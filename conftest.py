"""
Pytest configuration and shared fixtures
"""

import pytest
import os
from unittest.mock import Mock, patch


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment variables for all tests"""
    os.environ['AIRTABLE_API_KEY'] = 'test_key'
    os.environ['AIRTABLE_BASE_ID'] = 'test_base'  
    os.environ['OPENAI_API_KEY'] = 'test_openai'


@pytest.fixture
def mock_env_vars():
    """Fixture to provide test environment variables"""
    return {
        'AIRTABLE_API_KEY': 'test_key',
        'AIRTABLE_BASE_ID': 'test_base',
        'OPENAI_API_KEY': 'test_openai'
    }


@pytest.fixture
def mock_airtable():
    """Fixture to provide a mock Airtable instance"""
    with patch('airtable.Airtable') as mock:
        mock_instance = Mock()
        mock_instance.get_all.return_value = []
        mock_instance.update.return_value = True
        mock_instance.create.return_value = {'id': 'test_record_id'}
        mock.return_value = mock_instance
        yield mock


@pytest.fixture
def mock_openai():
    """Fixture to provide a mock OpenAI instance"""
    with patch('openai.chat.completions.create') as mock:
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = """Summary: Test candidate with good experience.
Score: 7
Issues: None
Follow-Ups: None"""
        mock.return_value = mock_response
        yield mock


@pytest.fixture
def sample_applicant_data():
    """Fixture providing sample applicant data for testing"""
    return {
        'personal': {
            'name': 'Test Applicant',
            'email': 'test@example.com',
            'location': 'San Francisco, CA',
            'linkedin': 'https://linkedin.com/in/test',
            'phone': '+1-555-0123'
        },
        'experience': [
            {
                'company': 'Google',
                'title': 'Software Engineer',
                'start_date': '2020-01-01',
                'end_date': '2023-01-01',
                'years_experience': 3.0,
                'technologies': ['Python', 'Go']
            }
        ],
        'salary': {
            'preferred_rate': 95,
            'currency': 'USD',
            'availability': 30
        },
        'metadata': {
            'total_experience_years': 3.0,
            'has_tier1_company': True,
            'compressed_at': '2024-01-01T00:00:00'
        }
    }
