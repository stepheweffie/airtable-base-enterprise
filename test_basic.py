"""
Basic unit tests for the Mercor Airtable Automation System

These tests validate core functionality and are run in the CI/CD pipeline.
"""

import pytest
import os
import json
from unittest.mock import Mock, patch, MagicMock

def test_config_module_import():
    """Test that config module can be imported"""
    import config
    assert config is not None

def test_config_validation_with_env_vars():
    """Test configuration validation with environment variables"""
    import config
    
    # Set mock environment variables
    os.environ['AIRTABLE_API_KEY'] = 'test_key'
    os.environ['AIRTABLE_BASE_ID'] = 'test_base'
    os.environ['OPENAI_API_KEY'] = 'test_openai'
    
    # Should not raise an exception
    assert config.validate_config() == True
    
    # Clean up
    del os.environ['AIRTABLE_API_KEY']
    del os.environ['AIRTABLE_BASE_ID'] 
    del os.environ['OPENAI_API_KEY']

def test_config_constants():
    """Test that configuration constants are properly defined"""
    import config
    
    assert isinstance(config.TIER_1_COMPANIES, list)
    assert len(config.TIER_1_COMPANIES) > 0
    assert 'Google' in config.TIER_1_COMPANIES
    
    assert isinstance(config.ALLOWED_LOCATIONS, list)
    assert len(config.ALLOWED_LOCATIONS) > 0
    assert 'US' in config.ALLOWED_LOCATIONS

@patch('airtable.Airtable')
def test_json_compressor_initialization(mock_airtable):
    """Test that JSONCompressor can be initialized"""
    # Mock environment variables
    os.environ['AIRTABLE_API_KEY'] = 'test_key'
    os.environ['AIRTABLE_BASE_ID'] = 'test_base'
    os.environ['OPENAI_API_KEY'] = 'test_openai'
    
    from json_compressor import JSONCompressor
    
    # Mock the Airtable connection
    mock_airtable.return_value = Mock()
    
    compressor = JSONCompressor()
    assert compressor is not None
    
    # Clean up
    del os.environ['AIRTABLE_API_KEY']
    del os.environ['AIRTABLE_BASE_ID']
    del os.environ['OPENAI_API_KEY']

def test_shortlisting_criteria_logic():
    """Test shortlisting criteria without Airtable connection"""
    # Mock environment variables
    os.environ['AIRTABLE_API_KEY'] = 'test_key'
    os.environ['AIRTABLE_BASE_ID'] = 'test_base'
    os.environ['OPENAI_API_KEY'] = 'test_openai'
    
    with patch('airtable.Airtable'):
        from shortlister import Shortlister
        
        shortlister = Shortlister()
        
        # Test experience criteria
        applicant_data = {
            'metadata': {
                'total_experience_years': 5.0,
                'has_tier1_company': True
            },
            'experience': [
                {'company': 'Google', 'title': 'Engineer', 'years_experience': 3.0}
            ]
        }
        
        meets_criteria, reason = shortlister.check_experience_criteria(applicant_data)
        assert meets_criteria == True
        assert 'years total experience' in reason or 'tier-1 company' in reason
        
        # Test compensation criteria
        applicant_data = {
            'salary': {
                'preferred_rate': 95,
                'currency': 'USD',
                'availability': 30
            }
        }
        
        meets_criteria, reason = shortlister.check_compensation_criteria(applicant_data)
        assert meets_criteria == True
        
        # Test location criteria
        applicant_data = {
            'personal': {
                'location': 'San Francisco, CA'
            }
        }
        
        meets_criteria, reason = shortlister.check_location_criteria(applicant_data)
        assert meets_criteria == True
    
    # Clean up
    del os.environ['AIRTABLE_API_KEY']
    del os.environ['AIRTABLE_BASE_ID']
    del os.environ['OPENAI_API_KEY']

def test_llm_prompt_generation():
    """Test LLM prompt generation without API calls"""
    # Mock environment variables
    os.environ['AIRTABLE_API_KEY'] = 'test_key'
    os.environ['AIRTABLE_BASE_ID'] = 'test_base'
    os.environ['OPENAI_API_KEY'] = 'test_openai'
    
    with patch('airtable.Airtable'), patch('openai.api_key'):
        from llm_evaluator import LLMEvaluator
        
        evaluator = LLMEvaluator()
        
        test_data = {
            'personal': {'name': 'Test User', 'email': 'test@test.com', 'location': 'NYC'},
            'experience': [{'company': 'Google', 'title': 'Engineer', 'years_experience': 3.0}],
            'salary': {'preferred_rate': 95, 'currency': 'USD', 'availability': 30},
            'metadata': {'total_experience_years': 3.0, 'has_tier1_company': True}
        }
        
        prompt = evaluator.build_evaluation_prompt(test_data)
        
        assert isinstance(prompt, str)
        assert len(prompt) > 100  # Should be a substantial prompt
        assert 'Test User' in prompt
        assert 'Google' in prompt
        assert 'recruiting analyst' in prompt.lower()
    
    # Clean up
    del os.environ['AIRTABLE_API_KEY']
    del os.environ['AIRTABLE_BASE_ID']
    del os.environ['OPENAI_API_KEY']

def test_main_cli_help():
    """Test that main CLI shows help without errors"""
    import subprocess
    import sys
    
    # Mock environment variables
    os.environ['AIRTABLE_API_KEY'] = 'test_key'
    os.environ['AIRTABLE_BASE_ID'] = 'test_base'
    os.environ['OPENAI_API_KEY'] = 'test_openai'
    
    result = subprocess.run([sys.executable, 'main.py', '--help'], 
                          capture_output=True, text=True)
    
    assert result.returncode == 0
    assert 'Mercor Airtable Automation System' in result.stdout
    assert 'pipeline' in result.stdout
    assert 'status' in result.stdout
    
    # Clean up
    del os.environ['AIRTABLE_API_KEY']
    del os.environ['AIRTABLE_BASE_ID']
    del os.environ['OPENAI_API_KEY']

def test_json_structure_validation():
    """Test JSON structure used in compression"""
    sample_json = {
        'personal': {'name': 'Test', 'email': 'test@test.com'},
        'experience': [{'company': 'Google', 'title': 'Engineer'}],
        'salary': {'preferred_rate': 95, 'currency': 'USD'},
        'metadata': {'total_experience_years': 3.0, 'has_tier1_company': True}
    }
    
    # Should be valid JSON
    json_string = json.dumps(sample_json)
    parsed_back = json.loads(json_string)
    
    assert parsed_back['personal']['name'] == 'Test'
    assert parsed_back['experience'][0]['company'] == 'Google'
    assert parsed_back['salary']['preferred_rate'] == 95
    assert parsed_back['metadata']['has_tier1_company'] == True

def test_currency_conversion():
    """Test currency conversion logic"""
    # Mock environment variables for imports
    os.environ['AIRTABLE_API_KEY'] = 'test_key'
    os.environ['AIRTABLE_BASE_ID'] = 'test_base'
    os.environ['OPENAI_API_KEY'] = 'test_openai'
    
    with patch('airtable.Airtable'):
        from shortlister import Shortlister
        
        shortlister = Shortlister()
        
        # Test USD conversion (should be 1:1)
        usd_rate = shortlister.convert_rate_to_usd(100, 'USD')
        assert usd_rate == 100
        
        # Test EUR conversion
        eur_rate = shortlister.convert_rate_to_usd(100, 'EUR')
        assert eur_rate > 100  # EUR should be worth more than USD
        
        # Test unknown currency (should default to input rate)
        unknown_rate = shortlister.convert_rate_to_usd(100, 'XYZ')
        assert unknown_rate == 100
    
    # Clean up
    del os.environ['AIRTABLE_API_KEY']
    del os.environ['AIRTABLE_BASE_ID']
    del os.environ['OPENAI_API_KEY']

if __name__ == '__main__':
    pytest.main([__file__])
