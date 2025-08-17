"""
Integration tests for Mercor Airtable Automation System

These tests verify that the modules work together correctly in realistic scenarios.
"""

import pytest
import os
import json
import time
from unittest.mock import Mock, patch, call
from datetime import datetime

from test_fixtures import (
    SAMPLE_COMPRESSED_JSON,
    MOCK_APPLICANT_RECORDS,
    MOCK_PERSONAL_RECORDS,
    MOCK_EXPERIENCE_RECORDS,
    MOCK_SALARY_RECORDS,
    generate_random_applicant_data,
    create_mock_airtable_record
)


class TestEndToEndWorkflow:
    """Test complete end-to-end workflow scenarios"""

    def setup_method(self):
        """Set up test environment for each test"""
        self.env_vars = {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }

    @patch('airtable.Airtable')
    @patch('openai.chat.completions.create')
    def test_full_pipeline_single_applicant(self, mock_openai_create, mock_airtable):
        """Test complete pipeline for a single applicant from data collection to evaluation"""
        with patch.dict(os.environ, self.env_vars):
            from main import MercorAutomation
            from json_compressor import JSONCompressor
            from shortlister import Shortlister
            from llm_evaluator import LLMEvaluator

            # Mock Airtable tables with realistic data flow
            mock_tables = self._setup_mock_airtable_tables(mock_airtable)
            
            # Mock OpenAI response
            mock_openai_response = Mock()
            mock_openai_response.choices = [Mock()]
            mock_openai_response.choices[0].message.content = """Summary: Experienced engineer with strong background at Google and Meta, specializing in full-stack development with modern technologies. Demonstrates leadership in backend systems and proven track record in high-scale applications. Well-positioned for senior contractor roles.
Score: 8
Issues: None
Follow-Ups: • What specific achievements at Google can you elaborate on? • Are you open to leading small development teams? • What's your experience with cloud architecture design?"""
            mock_openai_create.return_value = mock_openai_response

            # Initialize automation system
            automation = MercorAutomation()
            
            # Run full pipeline for single applicant
            results = automation.run_full_pipeline('APPLICANT_001')
            
            # Verify pipeline completed successfully
            assert results['compression']['success'] == 1
            assert results['compression']['failed'] == 0
            assert results['shortlisting']['success'] == 1  
            assert results['llm_evaluation']['success'] == 1
            
            # Verify data flow between modules
            self._verify_data_flow_integrity(mock_tables, mock_openai_create)

    @patch('airtable.Airtable')
    @patch('openai.chat.completions.create')
    def test_compression_to_shortlisting_integration(self, mock_openai_create, mock_airtable):
        """Test that compressed data flows correctly into shortlisting"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            from shortlister import Shortlister
            
            # Setup mock tables
            mock_tables = self._setup_mock_airtable_tables(mock_airtable)
            
            # Step 1: Compress applicant data
            compressor = JSONCompressor()
            success = compressor.compress_applicant_data('APPLICANT_001')
            assert success == True
            
            # Verify compressed JSON was written to applicants table
            mock_tables['applicants'].update.assert_called()
            update_call_args = mock_tables['applicants'].update.call_args
            update_data = update_call_args[0][1]  # Second argument is the update data
            assert 'Compressed JSON' in update_data
            
            # Parse the JSON that would be stored
            stored_json = json.loads(update_data['Compressed JSON'])
            assert stored_json['personal']['name'] == 'John Smith'
            assert stored_json['metadata']['has_tier1_company'] == True
            
            # Step 2: Run shortlisting on the compressed data
            # Mock the applicants table to return our compressed data
            mock_tables['applicants'].get_all.return_value = [{
                'id': 'rec123',
                'fields': {
                    'Applicant ID': 'APPLICANT_001',
                    'Compressed JSON': update_data['Compressed JSON']
                }
            }]
            
            shortlister = Shortlister()
            evaluation_result = shortlister.evaluate_applicant('APPLICANT_001', stored_json)
            
            # Verify shortlisting worked on compressed data
            assert evaluation_result['overall_pass'] == True
            assert 'Google' in evaluation_result['detailed_reason'] or 'tier-1' in evaluation_result['detailed_reason']

    @patch('airtable.Airtable')
    @patch('openai.chat.completions.create')
    def test_shortlisting_to_llm_integration(self, mock_openai_create, mock_airtable):
        """Test that shortlisted candidates flow correctly into LLM evaluation"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            from llm_evaluator import LLMEvaluator
            
            # Mock Airtable tables
            mock_tables = self._setup_mock_airtable_tables(mock_airtable)
            
            # Mock applicants table with compressed JSON
            mock_tables['applicants'].get_all.return_value = [{
                'id': 'rec123',
                'fields': {
                    'Applicant ID': 'APPLICANT_001',
                    'Compressed JSON': json.dumps(SAMPLE_COMPRESSED_JSON),
                    'Shortlist Status': 'Pending'
                }
            }]
            
            # Step 1: Run shortlisting
            shortlister = Shortlister()
            evaluation_result = shortlister.evaluate_applicant('APPLICANT_001', SAMPLE_COMPRESSED_JSON)
            assert evaluation_result['overall_pass'] == True
            
            # Step 2: Mock that shortlisting updated the status
            mock_tables['applicants'].get_all.return_value[0]['fields']['Shortlist Status'] = 'Shortlisted'
            
            # Step 3: Run LLM evaluation
            mock_openai_response = Mock()
            mock_openai_response.choices = [Mock()]
            mock_openai_response.choices[0].message.content = """Summary: Experienced engineer with strong background at Google and Meta.
Score: 8
Issues: None
Follow-Ups: • What specific achievements can you elaborate on?"""
            mock_openai_create.return_value = mock_openai_response
            
            evaluator = LLMEvaluator()
            llm_result = evaluator.evaluate_single_applicant('APPLICANT_001')
            
            # Verify LLM evaluation succeeded
            assert llm_result == True
            mock_openai_create.assert_called_once()
            
            # Verify LLM was called with the right data
            call_args = mock_openai_create.call_args
            prompt_content = call_args[1]['messages'][1]['content']  # User message content
            assert 'John Smith' in prompt_content
            assert 'Google' in prompt_content

    @patch('airtable.Airtable')
    def test_error_handling_across_modules(self, mock_airtable):
        """Test error handling when one module fails affects downstream modules"""
        with patch.dict(os.environ, self.env_vars):
            from main import MercorAutomation
            
            # Setup failing compression (e.g., no personal details found)
            mock_tables = {
                'applicants': Mock(),
                'personal': Mock(),
                'experience': Mock(),
                'salary': Mock(),
                'shortlisted': Mock()
            }
            
            mock_airtable.side_effect = lambda base_id, table_name, api_key: mock_tables.get(
                table_name.lower().replace(' ', ''), Mock()
            )
            
            # Make personal details return empty (causing compression failure)
            mock_tables['personal'].get_all.return_value = []
            mock_tables['experience'].get_all.return_value = []
            mock_tables['salary'].get_all.return_value = []
            mock_tables['applicants'].get_all.return_value = [{
                'id': 'rec123', 'fields': {'Applicant ID': 'APPLICANT_001'}
            }]
            
            automation = MercorAutomation()
            results = automation.run_full_pipeline('APPLICANT_001')
            
            # Verify graceful failure handling
            assert results['compression']['failed'] >= 1
            # Downstream modules should handle missing data gracefully
            assert 'shortlisting' in results
            assert 'llm_evaluation' in results

    @patch('airtable.Airtable')
    @patch('openai.chat.completions.create')
    def test_batch_processing_integration(self, mock_openai_create, mock_airtable):
        """Test processing multiple applicants through the pipeline"""
        with patch.dict(os.environ, self.env_vars):
            from main import MercorAutomation
            
            # Create multiple applicant records
            applicant_data = [
                create_mock_airtable_record('APPLICANT_001'),
                create_mock_airtable_record('APPLICANT_002'),
                create_mock_airtable_record('APPLICANT_003')
            ]
            
            mock_tables = self._setup_mock_airtable_tables(mock_airtable)
            mock_tables['applicants'].get_all.return_value = applicant_data
            
            # Mock OpenAI responses
            mock_openai_response = Mock()
            mock_openai_response.choices = [Mock()]
            mock_openai_response.choices[0].message.content = """Summary: Good candidate.
Score: 7
Issues: None
Follow-Ups: None"""
            mock_openai_create.return_value = mock_openai_response
            
            automation = MercorAutomation()
            results = automation.run_full_pipeline()  # No specific applicant = batch mode
            
            # Verify batch processing worked
            assert results['compression']['success'] >= 1
            assert results['shortlisting']['success'] >= 1
            assert results['llm_evaluation']['success'] >= 1

    def _setup_mock_airtable_tables(self, mock_airtable):
        """Helper method to setup consistent mock Airtable tables"""
        mock_tables = {
            'applicants': Mock(),
            'personal': Mock(),
            'experience': Mock(), 
            'salary': Mock(),
            'shortlisted': Mock()
        }
        
        # Configure the Airtable constructor to return appropriate mocks
        def airtable_constructor(base_id, table_name, api_key):
            table_key = table_name.lower().replace(' ', '')
            if 'applicant' in table_key:
                return mock_tables['applicants']
            elif 'personal' in table_key:
                return mock_tables['personal']
            elif 'experience' in table_key or 'work' in table_key:
                return mock_tables['experience']
            elif 'salary' in table_key:
                return mock_tables['salary']
            elif 'shortlist' in table_key:
                return mock_tables['shortlisted']
            else:
                return Mock()
        
        mock_airtable.side_effect = airtable_constructor
        
        # Setup default return values
        mock_tables['applicants'].get_all.return_value = MOCK_APPLICANT_RECORDS
        mock_tables['applicants'].update.return_value = True
        mock_tables['personal'].get_all.return_value = MOCK_PERSONAL_RECORDS
        mock_tables['experience'].get_all.return_value = MOCK_EXPERIENCE_RECORDS
        mock_tables['salary'].get_all.return_value = MOCK_SALARY_RECORDS
        mock_tables['shortlisted'].get_all.return_value = []
        mock_tables['shortlisted'].create.return_value = {'id': 'rec_shortlist_001'}
        
        return mock_tables

    def _verify_data_flow_integrity(self, mock_tables, mock_openai_create):
        """Helper method to verify data flows correctly between modules"""
        # Check that compression updated the applicants table
        mock_tables['applicants'].update.assert_called()
        
        # Check that OpenAI was called with reasonable data
        if mock_openai_create.called:
            call_args = mock_openai_create.call_args
            messages = call_args[1]['messages']
            user_message = next(msg for msg in messages if msg['role'] == 'user')
            assert len(user_message['content']) > 100  # Substantial prompt


class TestDataConsistency:
    """Test data consistency across module boundaries"""

    def setup_method(self):
        self.env_vars = {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }

    @patch('airtable.Airtable')
    def test_json_compression_decompression_roundtrip(self, mock_airtable):
        """Test that data survives compression->decompression roundtrip"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            from json_decompressor import JSONDecompressor
            
            # Mock the required tables
            mock_tables = {}
            for table_name in ['Applicants', 'Personal Details', 'Work Experience', 'Salary Preferences']:
                mock_table = Mock()
                mock_tables[table_name] = mock_table
                
            mock_airtable.side_effect = lambda base_id, table_name, api_key: mock_tables[table_name]
            
            # Setup data for compression
            mock_tables['Personal Details'].get_all.return_value = MOCK_PERSONAL_RECORDS
            mock_tables['Work Experience'].get_all.return_value = MOCK_EXPERIENCE_RECORDS
            mock_tables['Salary Preferences'].get_all.return_value = MOCK_SALARY_RECORDS
            mock_tables['Applicants'].get_all.return_value = [{'id': 'rec123', 'fields': {}}]
            mock_tables['Applicants'].update.return_value = True
            
            # Compress data
            compressor = JSONCompressor()
            compression_success = compressor.compress_applicant_data('APPLICANT_001')
            assert compression_success == True
            
            # Capture the compressed JSON
            update_call = mock_tables['Applicants'].update.call_args
            compressed_json_str = update_call[0][1]['Compressed JSON']
            compressed_data = json.loads(compressed_json_str)
            
            # Verify key data points are preserved
            assert compressed_data['personal']['name'] == 'John Smith'
            assert compressed_data['personal']['email'] == 'john.smith@example.com'
            assert len(compressed_data['experience']) == 2
            assert compressed_data['experience'][0]['company'] == 'Google'
            assert compressed_data['salary']['preferred_rate'] == 85
            assert compressed_data['metadata']['has_tier1_company'] == True

    @patch('airtable.Airtable')
    def test_shortlisting_criteria_consistency(self, mock_airtable):
        """Test that shortlisting criteria are consistently applied"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            mock_tables = {'applicants': Mock(), 'shortlisted': Mock()}
            mock_airtable.side_effect = lambda base_id, table_name, api_key: mock_tables.get(
                'shortlisted' if 'Shortlist' in table_name else 'applicants', Mock()
            )
            
            shortlister = Shortlister()
            
            # Test multiple candidates with different profiles
            test_candidates = [
                # Should pass: tier-1 company
                {
                    'id': 'TIER1_PASS',
                    'data': {
                        'personal': {'location': 'San Francisco, CA'},
                        'experience': [{'company': 'Google', 'years_experience': 2.0}],
                        'salary': {'preferred_rate': 90, 'currency': 'USD', 'availability': 25},
                        'metadata': {'total_experience_years': 2.0, 'has_tier1_company': True}
                    },
                    'should_pass': True
                },
                # Should pass: sufficient experience
                {
                    'id': 'EXPERIENCE_PASS',
                    'data': {
                        'personal': {'location': 'New York, NY'},
                        'experience': [{'company': 'StartupCorp', 'years_experience': 5.0}],
                        'salary': {'preferred_rate': 80, 'currency': 'USD', 'availability': 30},
                        'metadata': {'total_experience_years': 5.0, 'has_tier1_company': False}
                    },
                    'should_pass': True
                },
                # Should fail: high rate
                {
                    'id': 'RATE_FAIL',
                    'data': {
                        'personal': {'location': 'Toronto, Canada'},
                        'experience': [{'company': 'Meta', 'years_experience': 3.0}],
                        'salary': {'preferred_rate': 150, 'currency': 'USD', 'availability': 25},
                        'metadata': {'total_experience_years': 3.0, 'has_tier1_company': True}
                    },
                    'should_pass': False
                }
            ]
            
            for candidate in test_candidates:
                result = shortlister.evaluate_applicant(candidate['id'], candidate['data'])
                assert result['overall_pass'] == candidate['should_pass'], (
                    f"Candidate {candidate['id']} failed consistency check. "
                    f"Expected: {candidate['should_pass']}, Got: {result['overall_pass']}"
                )


class TestPerformanceAndReliability:
    """Test system performance and reliability under various conditions"""

    def setup_method(self):
        self.env_vars = {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }

    @patch('airtable.Airtable')
    @patch('openai.chat.completions.create')
    def test_api_retry_behavior(self, mock_openai_create, mock_airtable):
        """Test that API retries work correctly across modules"""
        with patch.dict(os.environ, self.env_vars):
            from llm_evaluator import LLMEvaluator
            import openai
            
            # Mock Airtable
            mock_table = Mock()
            mock_table.get_all.return_value = [{
                'id': 'rec123',
                'fields': {
                    'Applicant ID': 'APPLICANT_001',
                    'Compressed JSON': json.dumps(SAMPLE_COMPRESSED_JSON)
                }
            }]
            mock_airtable.return_value = mock_table
            
            # Mock OpenAI to fail once then succeed
            mock_success_response = Mock()
            mock_success_response.choices = [Mock()]
            mock_success_response.choices[0].message.content = """Summary: Test candidate.
Score: 7
Issues: None
Follow-Ups: None"""
            
            mock_openai_create.side_effect = [
                openai.RateLimitError(message="Rate limit", response=None, body=None),
                mock_success_response
            ]
            
            evaluator = LLMEvaluator()
            
            # Mock time.sleep to speed up test
            with patch('time.sleep'):
                content, error = evaluator.call_llm_with_retry("test prompt")
            
            # Verify retry worked
            assert content is not None
            assert error is None
            assert mock_openai_create.call_count == 2

    @patch('airtable.Airtable') 
    def test_large_dataset_handling(self, mock_airtable):
        """Test handling of larger datasets without memory issues"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            # Create a large number of mock records
            large_experience_list = []
            for i in range(50):  # Simulate applicant with many job experiences
                large_experience_list.append({
                    'id': f'rec_exp_{i}',
                    'fields': {
                        'Applicant ID': 'APPLICANT_MANY_JOBS',
                        'Company': f'Company_{i}',
                        'Title': f'Engineer_{i}',
                        'Start Date': '2020-01-01',
                        'End Date': '2021-01-01',
                        'Technologies': ['Python', 'JavaScript'],
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
            
            mock_tables['personal'].get_all.return_value = MOCK_PERSONAL_RECORDS
            mock_tables['experience'].get_all.return_value = large_experience_list
            mock_tables['salary'].get_all.return_value = MOCK_SALARY_RECORDS
            mock_tables['applicants'].get_all.return_value = [{'id': 'rec123', 'fields': {}}]
            mock_tables['applicants'].update.return_value = True
            
            compressor = JSONCompressor()
            result = compressor.compress_applicant_data('APPLICANT_MANY_JOBS')
            
            # Verify it handles large datasets without failure
            assert result == True
            
            # Verify the compressed data includes all experiences
            update_call = mock_tables['applicants'].update.call_args
            compressed_json_str = update_call[0][1]['Compressed JSON']
            compressed_data = json.loads(compressed_json_str)
            assert len(compressed_data['experience']) == 50
            assert compressed_data['metadata']['total_experience_years'] == 50.0  # 50 jobs × 1 year each

    @patch('airtable.Airtable')
    def test_concurrent_processing_safety(self, mock_airtable):
        """Test that the system handles concurrent-like scenarios safely"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            mock_tables = {'applicants': Mock(), 'shortlisted': Mock()}
            mock_airtable.side_effect = lambda base_id, table_name, api_key: mock_tables.get(
                'shortlisted' if 'Shortlist' in table_name else 'applicants', Mock()
            )
            
            # Simulate the same applicant being processed multiple times
            # (could happen with concurrent workers or retries)
            mock_tables['shortlisted'].get_all.return_value = []  # First time: no existing record
            mock_tables['shortlisted'].create.return_value = {'id': 'rec_new'}
            
            shortlister = Shortlister()
            
            # Process the same applicant twice
            result1 = shortlister.evaluate_applicant('APPLICANT_001', SAMPLE_COMPRESSED_JSON)
            result2 = shortlister.evaluate_applicant('APPLICANT_001', SAMPLE_COMPRESSED_JSON)
            
            # Both should succeed
            assert result1['overall_pass'] == True
            assert result2['overall_pass'] == True
            
            # Results should be consistent
            assert result1['detailed_reason'] == result2['detailed_reason']


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
