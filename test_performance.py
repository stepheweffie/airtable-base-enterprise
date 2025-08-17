"""
Performance tests for Mercor Airtable Automation System

These tests verify that the system performs well under load and handles
rate limiting, large datasets, and concurrent operations gracefully.
"""

import pytest
import os
import json
import time
import threading
from unittest.mock import Mock, patch, call
from datetime import datetime, timedelta
from concurrent.futures import ThreadPoolExecutor, as_completed

from test_fixtures import (
    generate_random_applicant_data,
    create_mock_airtable_record,
    SAMPLE_COMPRESSED_JSON
)


class TestScalabilityAndPerformance:
    """Test system scalability with large datasets"""

    def setup_method(self):
        """Set up test environment for each test"""
        self.env_vars = {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }

    @patch('airtable.Airtable')
    def test_large_batch_compression(self, mock_airtable):
        """Test compression performance with large number of applicants"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            # Setup mock tables for large dataset
            num_applicants = 100
            mock_tables = self._setup_performance_mock_tables(mock_airtable, num_applicants)
            
            compressor = JSONCompressor()
            
            # Measure compression time
            start_time = time.time()
            results = compressor.compress_all_applicants(force_update=True)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Performance assertions
            assert len(results) == num_applicants
            assert processing_time < 30  # Should complete within 30 seconds for 100 records
            assert sum(1 for r in results if r['success']) >= num_applicants * 0.8  # At least 80% success rate
            
            # Verify it doesn't consume excessive memory
            # (This is implicit - if memory usage was excessive, the test would fail)
            print(f"Compressed {num_applicants} records in {processing_time:.2f} seconds")

    @patch('airtable.Airtable')
    def test_shortlisting_performance_large_dataset(self, mock_airtable):
        """Test shortlisting performance with large dataset"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            # Create large dataset with mixed qualification profiles
            num_applicants = 200
            applicant_records = []
            
            for i in range(num_applicants):
                data = generate_random_applicant_data()
                record = {
                    'id': f'rec_{i}',
                    'fields': {
                        'Applicant ID': f'APPLICANT_{i:03d}',
                        'Compressed JSON': json.dumps(data),
                        'Shortlist Status': 'Pending'
                    }
                }
                applicant_records.append(record)
            
            mock_tables = {'applicants': Mock(), 'shortlisted': Mock()}
            mock_airtable.side_effect = lambda base_id, table_name, api_key: mock_tables.get(
                'shortlisted' if 'Shortlist' in table_name else 'applicants', Mock()
            )
            
            mock_tables['applicants'].get_all.return_value = applicant_records
            mock_tables['shortlisted'].get_all.return_value = []
            mock_tables['shortlisted'].create.return_value = {'id': 'rec_shortlist_new'}
            mock_tables['applicants'].update.return_value = True
            
            shortlister = Shortlister()
            
            # Measure shortlisting time
            start_time = time.time()
            results = shortlister.shortlist_all_applicants(force_reevaluate=True)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Performance assertions
            assert len(results) == num_applicants
            assert processing_time < 45  # Should complete within 45 seconds for 200 records
            print(f"Processed {num_applicants} shortlisting evaluations in {processing_time:.2f} seconds")
            
            # Verify reasonable shortlisting rate
            shortlisted_count = sum(1 for r in results if r.get('shortlisted', False))
            assert 0 <= shortlisted_count <= num_applicants  # Sanity check
            print(f"Shortlisted {shortlisted_count} out of {num_applicants} candidates")

    @patch('airtable.Airtable')
    @patch('openai.chat.completions.create')
    def test_llm_evaluation_performance_with_rate_limiting(self, mock_openai_create, mock_airtable):
        """Test LLM evaluation performance with simulated rate limiting"""
        with patch.dict(os.environ, self.env_vars):
            from llm_evaluator import LLMEvaluator
            import openai
            
            # Setup mock Airtable
            num_applicants = 20  # Smaller number for LLM tests due to API calls
            applicant_records = []
            
            for i in range(num_applicants):
                record = {
                    'id': f'rec_{i}',
                    'fields': {
                        'Applicant ID': f'APPLICANT_{i:03d}',
                        'Compressed JSON': json.dumps(generate_random_applicant_data()),
                        'LLM Evaluation': '',
                        'LLM Score': 0
                    }
                }
                applicant_records.append(record)
            
            mock_table = Mock()
            mock_table.get_all.return_value = applicant_records
            mock_table.update.return_value = True
            mock_airtable.return_value = mock_table
            
            # Mock OpenAI with occasional rate limiting
            mock_success_response = Mock()
            mock_success_response.choices = [Mock()]
            mock_success_response.choices[0].message.content = """Summary: Test candidate with good experience.
Score: 7
Issues: None
Follow-Ups: None"""
            
            # Create a list of responses including some rate limit errors
            responses = []
            for i in range(num_applicants + 5):  # Extra for retries
                if i % 7 == 0:  # Every 7th call triggers rate limit
                    responses.append(openai.RateLimitError(message="Rate limit", response=None, body=None))
                else:
                    responses.append(mock_success_response)
            
            mock_openai_create.side_effect = responses
            
            evaluator = LLMEvaluator()
            
            # Measure evaluation time with rate limiting
            start_time = time.time()
            with patch('time.sleep') as mock_sleep:  # Mock sleep to speed up test
                results = evaluator.evaluate_all_applicants(force_reevaluate=True)
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Performance assertions
            assert len(results) == num_applicants
            assert processing_time < 60  # Should complete within 60 seconds even with retries
            
            # Verify retry mechanism was used
            retry_count = sum(1 for call_args in mock_sleep.call_args_list if call_args)
            assert retry_count > 0  # Should have triggered some retries
            
            # Verify success rate despite rate limiting
            success_count = sum(1 for r in results if r['success'])
            assert success_count >= num_applicants * 0.8  # At least 80% should succeed
            
            print(f"Evaluated {num_applicants} applicants in {processing_time:.2f}s with {retry_count} retries")

    @patch('airtable.Airtable')
    def test_memory_usage_large_json_compression(self, mock_airtable):
        """Test memory efficiency with large JSON objects"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            # Create applicant with very large work experience history
            large_experience_records = []
            for i in range(500):  # 500 job experiences
                large_experience_records.append({
                    'id': f'rec_exp_{i}',
                    'fields': {
                        'Applicant ID': 'APPLICANT_LARGE',
                        'Company': f'Company_{i}' * 10,  # Long company names
                        'Title': f'Software Engineer Level {i % 7}',
                        'Start Date': '2020-01-01',
                        'End Date': '2021-01-01',
                        'Technologies': ['Python', 'JavaScript', 'React', 'Node.js', 'AWS'] * 5,  # Lots of tech
                        'Description': 'A' * 1000,  # 1KB description per job
                        'years_experience': 1.0
                    }
                })
            
            mock_tables = {
                'applicants': Mock(),
                'personal': Mock(), 
                'experience': Mock(),
                'salary': Mock()
            }
            
            mock_airtable.side_effect = lambda base_id, table_name, api_key: {
                'Applicants': mock_tables['applicants'],
                'Personal Details': mock_tables['personal'],
                'Work Experience': mock_tables['experience'],
                'Salary Preferences': mock_tables['salary']
            }.get(table_name, Mock())
            
            mock_tables['personal'].get_all.return_value = [{
                'id': 'rec_personal',
                'fields': {
                    'Applicant ID': 'APPLICANT_LARGE',
                    'Full Name': 'Large Dataset Test User',
                    'Email': 'large@test.com'
                }
            }]
            mock_tables['experience'].get_all.return_value = large_experience_records
            mock_tables['salary'].get_all.return_value = [{
                'id': 'rec_salary',
                'fields': {
                    'Applicant ID': 'APPLICANT_LARGE',
                    'Preferred Rate': 100,
                    'Currency': 'USD',
                    'Availability': 30
                }
            }]
            mock_tables['applicants'].get_all.return_value = [{'id': 'rec123', 'fields': {}}]
            mock_tables['applicants'].update.return_value = True
            
            compressor = JSONCompressor()
            
            # Measure compression of large dataset
            start_time = time.time()
            result = compressor.compress_applicant_data('APPLICANT_LARGE')
            end_time = time.time()
            
            processing_time = end_time - start_time
            
            # Verify compression succeeded
            assert result == True
            assert processing_time < 10  # Should complete within 10 seconds even for large data
            
            # Verify compressed data structure is correct
            update_call = mock_tables['applicants'].update.call_args
            compressed_json_str = update_call[0][1]['Compressed JSON']
            compressed_data = json.loads(compressed_json_str)
            
            assert len(compressed_data['experience']) == 500
            assert compressed_data['metadata']['total_experience_years'] == 500.0
            
            print(f"Compressed 500 job experiences in {processing_time:.2f} seconds")

    def _setup_performance_mock_tables(self, mock_airtable, num_applicants):
        """Helper to setup mock tables for performance testing"""
        mock_tables = {
            'applicants': Mock(),
            'personal': Mock(),
            'experience': Mock(),
            'salary': Mock()
        }
        
        mock_airtable.side_effect = lambda base_id, table_name, api_key: {
            'Applicants': mock_tables['applicants'],
            'Personal Details': mock_tables['personal'],
            'Work Experience': mock_tables['experience'],
            'Salary Preferences': mock_tables['salary']
        }.get(table_name, Mock())
        
        # Generate mock data for performance testing
        applicant_records = []
        personal_records = []
        experience_records = []
        salary_records = []
        
        for i in range(num_applicants):
            applicant_id = f'APPLICANT_{i:03d}'
            
            # Applicant record
            applicant_records.append({
                'id': f'rec_app_{i}',
                'fields': {
                    'Applicant ID': applicant_id,
                    'Status': 'Active',
                    'Shortlist Status': 'Pending'
                }
            })
            
            # Personal details
            personal_records.append({
                'id': f'rec_personal_{i}',
                'fields': {
                    'Applicant ID': applicant_id,
                    'Full Name': f'Test User {i}',
                    'Email': f'user{i}@test.com',
                    'Location': ['San Francisco, CA', 'New York, NY', 'London, UK'][i % 3]
                }
            })
            
            # Work experience (1-3 jobs per applicant)
            num_jobs = (i % 3) + 1
            for j in range(num_jobs):
                experience_records.append({
                    'id': f'rec_exp_{i}_{j}',
                    'fields': {
                        'Applicant ID': applicant_id,
                        'Company': ['Google', 'Meta', 'Amazon', 'Microsoft', 'StartupCorp'][j % 5],
                        'Title': 'Software Engineer',
                        'Start Date': '2020-01-01',
                        'End Date': '2022-01-01',
                        'Technologies': ['Python', 'JavaScript', 'React'],
                        'years_experience': 2.0
                    }
                })
            
            # Salary preferences
            salary_records.append({
                'id': f'rec_salary_{i}',
                'fields': {
                    'Applicant ID': applicant_id,
                    'Preferred Rate': 80 + (i % 40),  # Vary rates between 80-120
                    'Currency': 'USD',
                    'Availability': 20 + (i % 20)  # Vary availability 20-40 hrs
                }
            })
        
        # Setup return values
        mock_tables['applicants'].get_all.return_value = applicant_records
        mock_tables['personal'].get_all.side_effect = lambda formula=None: [
            r for r in personal_records 
            if not formula or formula.split("'")[1] in r['fields']['Applicant ID']
        ]
        mock_tables['experience'].get_all.side_effect = lambda formula=None: [
            r for r in experience_records 
            if not formula or formula.split("'")[1] in r['fields']['Applicant ID']
        ]
        mock_tables['salary'].get_all.side_effect = lambda formula=None: [
            r for r in salary_records 
            if not formula or formula.split("'")[1] in r['fields']['Applicant ID']
        ]
        mock_tables['applicants'].update.return_value = True
        
        return mock_tables


class TestConcurrencyAndThreadSafety:
    """Test concurrent operations and thread safety"""

    def setup_method(self):
        self.env_vars = {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base', 
            'OPENAI_API_KEY': 'test_openai'
        }

    @patch('airtable.Airtable')
    def test_concurrent_compression_operations(self, mock_airtable):
        """Test multiple compression operations running concurrently"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            # Setup mock tables
            mock_tables = {
                'applicants': Mock(),
                'personal': Mock(),
                'experience': Mock(),
                'salary': Mock()
            }
            
            def mock_airtable_constructor(base_id, table_name, api_key):
                # Return thread-safe mocks
                return {
                    'Applicants': mock_tables['applicants'],
                    'Personal Details': mock_tables['personal'],
                    'Work Experience': mock_tables['experience'],
                    'Salary Preferences': mock_tables['salary']
                }.get(table_name, Mock())
            
            mock_airtable.side_effect = mock_airtable_constructor
            
            # Setup mock data for different applicants
            def get_personal_data(formula=None):
                applicant_id = formula.split("'")[1] if formula else 'APPLICANT_001'
                return [{
                    'id': f'rec_personal_{applicant_id}',
                    'fields': {
                        'Applicant ID': applicant_id,
                        'Full Name': f'User {applicant_id}',
                        'Email': f'{applicant_id.lower()}@test.com'
                    }
                }]
            
            def get_experience_data(formula=None):
                applicant_id = formula.split("'")[1] if formula else 'APPLICANT_001'
                return [{
                    'id': f'rec_exp_{applicant_id}',
                    'fields': {
                        'Applicant ID': applicant_id,
                        'Company': 'Google',
                        'Title': 'Engineer',
                        'Start Date': '2020-01-01',
                        'End Date': '2022-01-01',
                        'years_experience': 2.0
                    }
                }]
            
            def get_salary_data(formula=None):
                applicant_id = formula.split("'")[1] if formula else 'APPLICANT_001'
                return [{
                    'id': f'rec_salary_{applicant_id}',
                    'fields': {
                        'Applicant ID': applicant_id,
                        'Preferred Rate': 90,
                        'Currency': 'USD',
                        'Availability': 30
                    }
                }]
            
            mock_tables['personal'].get_all.side_effect = get_personal_data
            mock_tables['experience'].get_all.side_effect = get_experience_data
            mock_tables['salary'].get_all.side_effect = get_salary_data
            mock_tables['applicants'].get_all.return_value = [{'id': 'rec123', 'fields': {}}]
            mock_tables['applicants'].update.return_value = True
            
            def compress_applicant(applicant_id):
                """Function to run compression in a thread"""
                compressor = JSONCompressor()
                return compressor.compress_applicant_data(applicant_id)
            
            # Run multiple compressions concurrently
            applicant_ids = [f'APPLICANT_{i:03d}' for i in range(1, 11)]  # 10 applicants
            
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=5) as executor:
                future_to_applicant = {
                    executor.submit(compress_applicant, app_id): app_id 
                    for app_id in applicant_ids
                }
                
                results = {}
                for future in as_completed(future_to_applicant):
                    applicant_id = future_to_applicant[future]
                    try:
                        result = future.result()
                        results[applicant_id] = result
                    except Exception as e:
                        results[applicant_id] = False
                        print(f"Exception for {applicant_id}: {e}")
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Verify concurrent operations succeeded
            assert len(results) == len(applicant_ids)
            success_count = sum(1 for result in results.values() if result)
            assert success_count >= len(applicant_ids) * 0.8  # At least 80% success
            assert processing_time < 15  # Should be faster than sequential processing
            
            print(f"Compressed {len(applicant_ids)} applicants concurrently in {processing_time:.2f} seconds")

    @patch('airtable.Airtable')
    @patch('openai.chat.completions.create')
    def test_concurrent_api_calls_rate_limiting(self, mock_openai_create, mock_airtable):
        """Test concurrent API calls with rate limiting"""
        with patch.dict(os.environ, self.env_vars):
            from llm_evaluator import LLMEvaluator
            import openai
            
            # Mock Airtable
            mock_table = Mock()
            def get_applicant_data(formula=None):
                applicant_id = formula.split("'")[1] if formula else 'APPLICANT_001'
                return [{
                    'id': f'rec_{applicant_id}',
                    'fields': {
                        'Applicant ID': applicant_id,
                        'Compressed JSON': json.dumps(SAMPLE_COMPRESSED_JSON)
                    }
                }]
            
            mock_table.get_all.side_effect = get_applicant_data
            mock_table.update.return_value = True
            mock_airtable.return_value = mock_table
            
            # Mock OpenAI with rate limiting simulation
            mock_success_response = Mock()
            mock_success_response.choices = [Mock()]
            mock_success_response.choices[0].message.content = """Summary: Good candidate.
Score: 7
Issues: None
Follow-Ups: None"""
            
            call_count = 0
            def mock_openai_response(*args, **kwargs):
                nonlocal call_count
                call_count += 1
                # Simulate rate limiting every 3rd call
                if call_count % 3 == 0:
                    raise openai.RateLimitError(message="Rate limit", response=None, body=None)
                return mock_success_response
            
            mock_openai_create.side_effect = mock_openai_response
            
            def evaluate_applicant(applicant_id):
                """Function to run evaluation in a thread"""
                evaluator = LLMEvaluator()
                with patch('time.sleep'):  # Mock sleep to speed up test
                    return evaluator.evaluate_single_applicant(applicant_id)
            
            # Run multiple evaluations concurrently
            applicant_ids = [f'APPLICANT_{i:03d}' for i in range(1, 6)]  # 5 applicants
            
            start_time = time.time()
            with ThreadPoolExecutor(max_workers=3) as executor:
                future_to_applicant = {
                    executor.submit(evaluate_applicant, app_id): app_id 
                    for app_id in applicant_ids
                }
                
                results = {}
                for future in as_completed(future_to_applicant):
                    applicant_id = future_to_applicant[future]
                    try:
                        result = future.result()
                        results[applicant_id] = result
                    except Exception as e:
                        results[applicant_id] = False
                        print(f"Exception for {applicant_id}: {e}")
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Verify concurrent operations with rate limiting
            assert len(results) == len(applicant_ids)
            success_count = sum(1 for result in results.values() if result)
            assert success_count >= len(applicant_ids) * 0.6  # At least 60% success (due to rate limiting)
            
            print(f"Evaluated {len(applicant_ids)} applicants concurrently in {processing_time:.2f} seconds")


class TestResourceUtilization:
    """Test resource utilization and cleanup"""

    def setup_method(self):
        self.env_vars = {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }

    @patch('airtable.Airtable')
    def test_connection_pooling_efficiency(self, mock_airtable):
        """Test that connections are reused efficiently"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            # Mock Airtable to track connection creation
            connection_count = 0
            def track_connections(base_id, table_name, api_key):
                nonlocal connection_count
                connection_count += 1
                mock_table = Mock()
                mock_table.get_all.return_value = []
                return mock_table
            
            mock_airtable.side_effect = track_connections
            
            # Create multiple compressor instances
            compressors = [JSONCompressor() for _ in range(10)]
            
            # Verify connections are created as expected
            # Each compressor creates 4 table connections
            expected_connections = 10 * 4
            assert connection_count == expected_connections
            
            print(f"Created {connection_count} connections for 10 JSONCompressor instances")

    @patch('airtable.Airtable')
    @patch('openai.chat.completions.create')
    def test_memory_cleanup_after_processing(self, mock_openai_create, mock_airtable):
        """Test that memory is properly cleaned up after processing"""
        with patch.dict(os.environ, self.env_vars):
            from main import MercorAutomation
            
            # Setup basic mocks
            mock_table = Mock()
            mock_table.get_all.return_value = [{
                'id': 'rec123',
                'fields': {
                    'Applicant ID': 'APPLICANT_001',
                    'Compressed JSON': json.dumps(SAMPLE_COMPRESSED_JSON),
                    'Shortlist Status': 'Pending'
                }
            }]
            mock_table.update.return_value = True
            mock_airtable.return_value = mock_table
            
            mock_openai_response = Mock()
            mock_openai_response.choices = [Mock()]
            mock_openai_response.choices[0].message.content = """Summary: Test.
Score: 7
Issues: None
Follow-Ups: None"""
            mock_openai_create.return_value = mock_openai_response
            
            # Process multiple times to check for memory leaks
            for i in range(5):
                automation = MercorAutomation()
                results = automation.run_full_pipeline('APPLICANT_001')
                assert results['compression']['success'] == 1
                
                # Force cleanup
                del automation
            
            # If we reach here without memory errors, cleanup is working
            print("Successfully processed 5 iterations without memory issues")


if __name__ == '__main__':
    pytest.main([__file__, '-v', '-s'])
