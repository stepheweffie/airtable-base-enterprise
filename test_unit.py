"""
Comprehensive unit tests for Mercor Airtable Automation System
"""

import pytest
import os
import json
import hashlib
from unittest.mock import Mock, patch, MagicMock, call
from datetime import datetime, timedelta

# Import test fixtures
from test_fixtures import (
    SAMPLE_COMPRESSED_JSON, 
    SHORTLISTING_TEST_CASES, 
    LLM_EVALUATION_TEST_CASES,
    CURRENCY_CONVERSION_TEST_CASES,
    MOCK_APPLICANT_RECORDS,
    MOCK_PERSONAL_RECORDS,
    MOCK_EXPERIENCE_RECORDS,
    MOCK_SALARY_RECORDS,
    generate_random_applicant_data
)


class TestConfig:
    """Test configuration module"""

    def test_config_import(self):
        """Test that config module can be imported"""
        import config
        assert config is not None

    def test_config_validation_success(self):
        """Test successful configuration validation"""
        with patch.dict(os.environ, {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }):
            import config
            assert config.validate_config() == True

    def test_config_validation_failure_missing_airtable_key(self):
        """Test config validation failure when AIRTABLE_API_KEY is missing"""
        # Test the validation function directly with None values
        import config
        original_key = config.AIRTABLE_API_KEY
        original_base = config.AIRTABLE_BASE_ID
        original_openai = config.OPENAI_API_KEY
        
        try:
            # Temporarily set missing key
            config.AIRTABLE_API_KEY = None
            config.AIRTABLE_BASE_ID = 'test_base'
            config.OPENAI_API_KEY = 'test_openai'
            
            with pytest.raises(ValueError, match="Missing required environment variables.*AIRTABLE_API_KEY"):
                config.validate_config()
        finally:
            # Restore original values
            config.AIRTABLE_API_KEY = original_key
            config.AIRTABLE_BASE_ID = original_base
            config.OPENAI_API_KEY = original_openai

    def test_config_validation_failure_missing_base_id(self):
        """Test config validation failure when AIRTABLE_BASE_ID is missing"""
        import config
        original_key = config.AIRTABLE_API_KEY
        original_base = config.AIRTABLE_BASE_ID
        original_openai = config.OPENAI_API_KEY
        
        try:
            config.AIRTABLE_API_KEY = 'test_key'
            config.AIRTABLE_BASE_ID = None
            config.OPENAI_API_KEY = 'test_openai'
            
            with pytest.raises(ValueError, match="Missing required environment variables.*AIRTABLE_BASE_ID"):
                config.validate_config()
        finally:
            config.AIRTABLE_API_KEY = original_key
            config.AIRTABLE_BASE_ID = original_base
            config.OPENAI_API_KEY = original_openai

    def test_config_validation_failure_missing_openai_key(self):
        """Test config validation failure when OPENAI_API_KEY is missing"""
        import config
        original_key = config.AIRTABLE_API_KEY
        original_base = config.AIRTABLE_BASE_ID
        original_openai = config.OPENAI_API_KEY
        
        try:
            config.AIRTABLE_API_KEY = 'test_key'
            config.AIRTABLE_BASE_ID = 'test_base'
            config.OPENAI_API_KEY = None
            
            with pytest.raises(ValueError, match="Missing required environment variables.*OPENAI_API_KEY"):
                config.validate_config()
        finally:
            config.AIRTABLE_API_KEY = original_key
            config.AIRTABLE_BASE_ID = original_base
            config.OPENAI_API_KEY = original_openai

    def test_config_constants(self):
        """Test that configuration constants are properly defined"""
        import config
        
        # Test TIER_1_COMPANIES
        assert isinstance(config.TIER_1_COMPANIES, list)
        assert len(config.TIER_1_COMPANIES) > 0
        assert 'Google' in config.TIER_1_COMPANIES
        assert 'Meta' in config.TIER_1_COMPANIES
        assert 'Amazon' in config.TIER_1_COMPANIES

        # Test ALLOWED_LOCATIONS
        assert isinstance(config.ALLOWED_LOCATIONS, list)
        assert len(config.ALLOWED_LOCATIONS) > 0
        assert 'US' in config.ALLOWED_LOCATIONS or 'USA' in config.ALLOWED_LOCATIONS
        assert 'Canada' in config.ALLOWED_LOCATIONS
        assert 'UK' in config.ALLOWED_LOCATIONS

    def test_config_table_names(self):
        """Test table name configuration"""
        import config
        
        assert 'APPLICANTS' in config.TABLES
        assert 'PERSONAL_DETAILS' in config.TABLES
        assert 'WORK_EXPERIENCE' in config.TABLES
        assert 'SALARY_PREFERENCES' in config.TABLES
        assert 'SHORTLISTED_LEADS' in config.TABLES

    def test_llm_config_defaults(self):
        """Test LLM configuration defaults"""
        with patch.dict(os.environ, {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }, clear=True):
            import config
            
            assert config.MAX_TOKENS_PER_REQUEST == 1500
            assert config.LLM_MODEL == 'gpt-3.5-turbo'


class TestJSONCompressor:
    """Test JSON compression functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.env_vars = {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }

    @patch('airtable.Airtable')
    def test_json_compressor_initialization(self, mock_airtable):
        """Test JSONCompressor initialization"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            compressor = JSONCompressor()
            assert compressor is not None
            assert mock_airtable.call_count == 4  # 4 tables

    @patch('airtable.Airtable')
    def test_get_personal_details_success(self, mock_airtable):
        """Test successful personal details retrieval"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            # Mock the personal table
            mock_personal_table = Mock()
            mock_personal_table.get_all.return_value = MOCK_PERSONAL_RECORDS
            
            compressor = JSONCompressor()
            compressor.personal_table = mock_personal_table
            
            result = compressor.get_personal_details('APPLICANT_001')
            
            assert result['name'] == 'John Smith'
            assert result['email'] == 'john.smith@example.com'
            assert result['location'] == 'San Francisco, CA'

    @patch('airtable.Airtable')
    def test_get_personal_details_not_found(self, mock_airtable):
        """Test personal details retrieval when no records found"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            mock_personal_table = Mock()
            mock_personal_table.get_all.return_value = []
            
            compressor = JSONCompressor()
            compressor.personal_table = mock_personal_table
            
            result = compressor.get_personal_details('NONEXISTENT')
            
            assert result == {}

    @patch('airtable.Airtable')
    def test_get_work_experience_success(self, mock_airtable):
        """Test successful work experience retrieval"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            mock_experience_table = Mock()
            mock_experience_table.get_all.return_value = MOCK_EXPERIENCE_RECORDS
            
            compressor = JSONCompressor()
            compressor.experience_table = mock_experience_table
            
            result = compressor.get_work_experience('APPLICANT_001')
            
            assert len(result) == 2
            assert result[0]['company'] == 'Google'
            assert result[0]['years_experience'] == 3.5

    @patch('airtable.Airtable')
    def test_calculate_total_experience(self, mock_airtable):
        """Test total experience calculation"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            compressor = JSONCompressor()
            
            experiences = [
                {'years_experience': 2.5},
                {'years_experience': 1.8},
                {'years_experience': 0.7}
            ]
            
            result = compressor.calculate_total_experience(experiences)
            assert result == 5.0

    @patch('airtable.Airtable')
    def test_has_tier1_company_true(self, mock_airtable):
        """Test tier-1 company detection - positive case"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            compressor = JSONCompressor()
            
            experiences = [
                {'company': 'Google Inc.'},
                {'company': 'StartupCorp'}
            ]
            
            result = compressor.has_tier1_company(experiences)
            assert result == True

    @patch('airtable.Airtable')
    def test_has_tier1_company_false(self, mock_airtable):
        """Test tier-1 company detection - negative case"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            compressor = JSONCompressor()
            
            experiences = [
                {'company': 'StartupCorp'},
                {'company': 'LocalBiz'}
            ]
            
            result = compressor.has_tier1_company(experiences)
            assert result == False

    @patch('airtable.Airtable')
    def test_compress_applicant_data_success(self, mock_airtable):
        """Test successful applicant data compression"""
        with patch.dict(os.environ, self.env_vars):
            from json_compressor import JSONCompressor
            
            compressor = JSONCompressor()
            
            # Mock all data retrieval methods
            compressor.get_personal_details = Mock(return_value=SAMPLE_COMPRESSED_JSON['personal'])
            compressor.get_work_experience = Mock(return_value=SAMPLE_COMPRESSED_JSON['experience'])
            compressor.get_salary_preferences = Mock(return_value=SAMPLE_COMPRESSED_JSON['salary'])
            
            # Mock the applicants table update
            mock_applicants_table = Mock()
            mock_applicants_table.get_all.return_value = [{'id': 'rec123', 'fields': {}}]
            mock_applicants_table.update.return_value = True
            compressor.applicants_table = mock_applicants_table
            
            result = compressor.compress_applicant_data('APPLICANT_001')
            
            assert result == True
            mock_applicants_table.update.assert_called_once()


class TestShortlister:
    """Test shortlisting functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.env_vars = {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }

    @patch('airtable.Airtable')
    def test_shortlister_initialization(self, mock_airtable):
        """Test Shortlister initialization"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            shortlister = Shortlister()
            assert shortlister is not None
            assert mock_airtable.call_count == 2  # 2 tables

    @patch('airtable.Airtable')
    def test_currency_conversion(self, mock_airtable):
        """Test currency conversion logic"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            shortlister = Shortlister()
            
            for test_case in CURRENCY_CONVERSION_TEST_CASES:
                result = shortlister.convert_rate_to_usd(test_case['rate'], test_case['currency'])
                assert result == test_case['expected']

    @patch('airtable.Airtable')
    def test_shortlisting_criteria(self, mock_airtable):
        """Test shortlisting criteria evaluation"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            shortlister = Shortlister()
            
            for test_case in SHORTLISTING_TEST_CASES:
                # Test experience criteria
                exp_pass, exp_reason = shortlister.check_experience_criteria(test_case['data'])
                
                # Test compensation criteria
                comp_pass, comp_reason = shortlister.check_compensation_criteria(test_case['data'])
                
                # Test location criteria
                loc_pass, loc_reason = shortlister.check_location_criteria(test_case['data'])
                
                # Overall evaluation
                result = shortlister.evaluate_applicant(f"TEST_{test_case['name']}", test_case['data'])
                
                assert result['overall_pass'] == test_case['expected_pass'], f"Failed for test case: {test_case['name']}"

    @patch('airtable.Airtable')
    def test_check_experience_criteria_tier1(self, mock_airtable):
        """Test experience criteria with tier-1 company"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            shortlister = Shortlister()
            
            data = {
                'metadata': {'total_experience_years': 2.0, 'has_tier1_company': True},
                'experience': [{'company': 'Google', 'years_experience': 2.0}]
            }
            
            meets_criteria, reason = shortlister.check_experience_criteria(data)
            
            assert meets_criteria == True
            assert 'Google' in reason or 'tier-1' in reason.lower()

    @patch('airtable.Airtable')
    def test_check_experience_criteria_years(self, mock_airtable):
        """Test experience criteria with sufficient years"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            shortlister = Shortlister()
            
            data = {
                'metadata': {'total_experience_years': 5.0, 'has_tier1_company': False},
                'experience': []
            }
            
            meets_criteria, reason = shortlister.check_experience_criteria(data)
            
            assert meets_criteria == True
            assert '5.0 years' in reason

    @patch('airtable.Airtable')
    def test_check_compensation_criteria_pass(self, mock_airtable):
        """Test compensation criteria - passing case"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            shortlister = Shortlister()
            
            data = {
                'salary': {'preferred_rate': 90, 'currency': 'USD', 'availability': 25}
            }
            
            meets_criteria, reason = shortlister.check_compensation_criteria(data)
            
            assert meets_criteria == True
            assert '90' in reason and '25' in reason

    @patch('airtable.Airtable')
    def test_check_compensation_criteria_fail_rate(self, mock_airtable):
        """Test compensation criteria - failing due to high rate"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            shortlister = Shortlister()
            
            data = {
                'salary': {'preferred_rate': 150, 'currency': 'USD', 'availability': 30}
            }
            
            meets_criteria, reason = shortlister.check_compensation_criteria(data)
            
            assert meets_criteria == False
            assert '150' in reason and '> $100' in reason

    @patch('airtable.Airtable')
    def test_check_location_criteria_pass(self, mock_airtable):
        """Test location criteria - passing case"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            shortlister = Shortlister()
            
            data = {
                'personal': {'location': 'San Francisco, CA'}
            }
            
            meets_criteria, reason = shortlister.check_location_criteria(data)
            
            assert meets_criteria == True
            assert 'San Francisco' in reason

    @patch('airtable.Airtable')
    def test_check_location_criteria_fail(self, mock_airtable):
        """Test location criteria - failing case"""
        with patch.dict(os.environ, self.env_vars):
            from shortlister import Shortlister
            
            shortlister = Shortlister()
            
            data = {
                'personal': {'location': 'Tokyo, Japan'}
            }
            
            meets_criteria, reason = shortlister.check_location_criteria(data)
            
            assert meets_criteria == False
            assert 'Tokyo' in reason and 'not in allowed' in reason


class TestLLMEvaluator:
    """Test LLM evaluation functionality"""

    def setup_method(self):
        """Set up test environment"""
        self.env_vars = {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }

    @patch('airtable.Airtable')
    @patch('openai.api_key')
    def test_llm_evaluator_initialization(self, mock_openai_key, mock_airtable):
        """Test LLMEvaluator initialization"""
        with patch.dict(os.environ, self.env_vars):
            from llm_evaluator import LLMEvaluator
            
            evaluator = LLMEvaluator()
            assert evaluator is not None
            assert evaluator.model == 'gpt-3.5-turbo'
            assert evaluator.max_tokens == 1500

    @patch('airtable.Airtable')
    @patch('openai.api_key')
    def test_generate_content_hash(self, mock_openai_key, mock_airtable):
        """Test content hash generation"""
        with patch.dict(os.environ, self.env_vars):
            from llm_evaluator import LLMEvaluator
            
            evaluator = LLMEvaluator()
            
            test_content = "test content"
            expected_hash = hashlib.md5(test_content.encode()).hexdigest()
            
            result = evaluator.generate_content_hash(test_content)
            assert result == expected_hash

    @patch('airtable.Airtable')
    @patch('openai.api_key')
    def test_build_evaluation_prompt(self, mock_openai_key, mock_airtable):
        """Test LLM prompt generation"""
        with patch.dict(os.environ, self.env_vars):
            from llm_evaluator import LLMEvaluator
            
            evaluator = LLMEvaluator()
            
            prompt = evaluator.build_evaluation_prompt(SAMPLE_COMPRESSED_JSON)
            
            assert isinstance(prompt, str)
            assert len(prompt) > 100
            assert 'John Smith' in prompt
            assert 'Google' in prompt
            assert 'recruiting analyst' in prompt.lower()
            assert 'Summary:' in prompt
            assert 'Score:' in prompt

    @patch('airtable.Airtable')
    @patch('openai.api_key')
    def test_parse_llm_response(self, mock_openai_key, mock_airtable):
        """Test LLM response parsing"""
        with patch.dict(os.environ, self.env_vars):
            from llm_evaluator import LLMEvaluator
            
            evaluator = LLMEvaluator()
            
            for test_case in LLM_EVALUATION_TEST_CASES:
                result = evaluator.parse_llm_response(test_case['mock_response'])
                
                assert 'summary' in result
                assert 'score' in result
                assert 'issues' in result
                assert 'follow_ups' in result
                
                assert result['score'] == test_case['expected_score']
                assert result['issues'] == test_case['expected_issues']
                
                if test_case['expected_follow_ups_count'] > 0:
                    assert len(result['follow_ups'].split('•')) >= test_case['expected_follow_ups_count']

    @patch('airtable.Airtable')
    @patch('openai.chat.completions.create')
    def test_call_llm_with_retry_success(self, mock_openai_create, mock_airtable):
        """Test successful LLM API call"""
        with patch.dict(os.environ, self.env_vars):
            from llm_evaluator import LLMEvaluator
            
            # Mock successful API response
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = LLM_EVALUATION_TEST_CASES[0]['mock_response']
            mock_openai_create.return_value = mock_response
            
            evaluator = LLMEvaluator()
            
            content, error = evaluator.call_llm_with_retry("test prompt")
            
            assert content is not None
            assert error is None
            assert "Summary:" in content

    @patch('airtable.Airtable')
    @patch('openai.chat.completions.create')
    def test_call_llm_with_retry_rate_limit(self, mock_openai_create, mock_airtable):
        """Test LLM API call with rate limiting"""
        with patch.dict(os.environ, self.env_vars):
            from llm_evaluator import LLMEvaluator
            import openai
            
            # Mock rate limit error then success
            mock_response = Mock()
            mock_response.choices = [Mock()]
            mock_response.choices[0].message.content = LLM_EVALUATION_TEST_CASES[0]['mock_response']
            
            mock_openai_create.side_effect = [
                openai.RateLimitError(message="Rate limit", response=None, body=None),
                mock_response
            ]
            
            evaluator = LLMEvaluator()
            
            with patch('time.sleep'):  # Mock sleep to speed up test
                content, error = evaluator.call_llm_with_retry("test prompt")
            
            assert content is not None
            assert error is None
            assert mock_openai_create.call_count == 2


class TestMercorAutomation:
    """Test main automation orchestrator"""

    def setup_method(self):
        """Set up test environment"""
        self.env_vars = {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }

    @patch('json_compressor.JSONCompressor')
    @patch('shortlister.Shortlister')
    @patch('llm_evaluator.LLMEvaluator')
    @patch('json_decompressor.JSONDecompressor')
    def test_automation_initialization(self, mock_decompressor, mock_llm, mock_shortlister, mock_compressor):
        """Test MercorAutomation initialization"""
        with patch.dict(os.environ, self.env_vars):
            from main import MercorAutomation
            
            automation = MercorAutomation()
            assert automation is not None
            assert automation.compressor is not None
            assert automation.shortlister is not None
            assert automation.evaluator is not None

    @patch('json_compressor.JSONCompressor')
    @patch('shortlister.Shortlister')
    @patch('llm_evaluator.LLMEvaluator')
    @patch('json_decompressor.JSONDecompressor')
    def test_run_full_pipeline_single_applicant(self, mock_decompressor, mock_llm, mock_shortlister, mock_compressor):
        """Test running full pipeline for single applicant"""
        with patch.dict(os.environ, self.env_vars):
            from main import MercorAutomation
            
            # Mock successful operations
            mock_compressor_instance = Mock()
            mock_compressor_instance.compress_single_applicant.return_value = True
            mock_compressor.return_value = mock_compressor_instance
            
            mock_shortlister_instance = Mock()
            mock_shortlister_instance.shortlist_single_applicant.return_value = True
            mock_shortlister_instance.get_shortlisting_summary.return_value = {'shortlisted': 1}
            mock_shortlister.return_value = mock_shortlister_instance
            
            mock_llm_instance = Mock()
            mock_llm_instance.evaluate_single_applicant.return_value = True
            mock_llm.return_value = mock_llm_instance
            
            automation = MercorAutomation()
            results = automation.run_full_pipeline('APPLICANT_001')
            
            assert results['compression']['success'] == 1
            assert results['compression']['failed'] == 0
            assert results['shortlisting']['success'] == 1
            assert results['llm_evaluation']['success'] == 1

    @patch('json_compressor.JSONCompressor')
    @patch('shortlister.Shortlister')  
    @patch('llm_evaluator.LLMEvaluator')
    @patch('json_decompressor.JSONDecompressor')
    def test_get_system_status(self, mock_decompressor, mock_llm, mock_shortlister, mock_compressor):
        """Test getting system status"""
        with patch.dict(os.environ, self.env_vars):
            from main import MercorAutomation
            
            # Mock summary data
            mock_shortlister_instance = Mock()
            mock_shortlister_instance.get_shortlisting_summary.return_value = {
                'total_applicants': 10,
                'with_compressed_json': 8,
                'shortlisted': 3,
                'rejected': 5,
                'unprocessed': 2
            }
            mock_shortlister.return_value = mock_shortlister_instance
            
            mock_llm_instance = Mock()
            mock_llm_instance.get_evaluation_summary.return_value = {
                'with_llm_evaluation': 6,
                'average_score': 7.2
            }
            mock_llm.return_value = mock_llm_instance
            
            automation = MercorAutomation()
            status = automation.get_system_status()
            
            assert status['applicants']['total'] == 10
            assert status['applicants']['shortlisted'] == 3
            assert status['llm_evaluation']['evaluated'] == 6
            assert status['llm_evaluation']['average_score'] == 7.2

    def test_main_cli_help(self):
        """Test main CLI help functionality"""
        with patch.dict(os.environ, self.env_vars):
            import subprocess
            import sys
            
            result = subprocess.run(
                [sys.executable, 'main.py', '--help'], 
                capture_output=True, 
                text=True,
                cwd='/Users/savantlab/mercor-airtable-automation'
            )
            
            assert result.returncode == 0
            assert 'Mercor Airtable Automation System' in result.stdout
            assert 'pipeline' in result.stdout
            assert 'status' in result.stdout


# Additional utility tests
class TestUtilities:
    """Test utility functions and edge cases"""

    def test_json_structure_validation(self):
        """Test JSON structure used in compression"""
        json_string = json.dumps(SAMPLE_COMPRESSED_JSON)
        parsed_back = json.loads(json_string)
        
        assert parsed_back['personal']['name'] == 'John Smith'
        assert parsed_back['experience'][0]['company'] == 'Google'
        assert parsed_back['salary']['preferred_rate'] == 85
        assert parsed_back['metadata']['has_tier1_company'] == True

    def test_random_data_generation(self):
        """Test random data generation for testing"""
        data = generate_random_applicant_data()
        
        assert 'personal' in data
        assert 'experience' in data
        assert 'salary' in data
        assert 'metadata' in data
        
        assert isinstance(data['experience'], list)
        assert len(data['experience']) > 0
        assert data['metadata']['total_experience_years'] >= 0

    def test_edge_case_empty_data(self):
        """Test handling of empty or None data"""
        with patch.dict(os.environ, {
            'AIRTABLE_API_KEY': 'test_key',
            'AIRTABLE_BASE_ID': 'test_base',
            'OPENAI_API_KEY': 'test_openai'
        }):
            from json_compressor import JSONCompressor
            
            with patch('airtable.Airtable'):
                compressor = JSONCompressor()
                
                # Test empty experience list
                result = compressor.calculate_total_experience([])
                assert result == 0
                
                # Test None experience
                result = compressor.calculate_total_experience(None)
                assert result == 0
                
                # Test empty experience for tier-1 check
                result = compressor.has_tier1_company([])
                assert result == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
