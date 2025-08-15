"""
Configuration module for Mercor Airtable Automation System
"""
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Airtable Configuration
AIRTABLE_API_KEY = os.getenv('AIRTABLE_API_KEY')
AIRTABLE_BASE_ID = os.getenv('AIRTABLE_BASE_ID')

# OpenAI Configuration (using exported env var)
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')

# Table Names
TABLES = {
    'APPLICANTS': 'Applicants',
    'PERSONAL_DETAILS': 'Personal Details',
    'WORK_EXPERIENCE': 'Work Experience',
    'SALARY_PREFERENCES': 'Salary Preferences',
    'SHORTLISTED_LEADS': 'Shortlisted Leads'
}

# LLM Configuration
MAX_TOKENS_PER_REQUEST = int(os.getenv('MAX_TOKENS_PER_REQUEST', '1500'))
LLM_MODEL = os.getenv('LLM_MODEL', 'gpt-3.5-turbo')

# Shortlisting Criteria
TIER_1_COMPANIES = [
    'Google', 'Meta', 'OpenAI', 'Microsoft', 'Amazon', 'Apple', 'Netflix',
    'Tesla', 'SpaceX', 'Stripe', 'Airbnb', 'Uber', 'Palantir', 'Databricks'
]

ALLOWED_LOCATIONS = [
    'US', 'USA', 'United States', 'Canada', 'UK', 'United Kingdom', 
    'Germany', 'India', 'New York', 'NYC', 'San Francisco', 'SF',
    'London', 'Berlin', 'Bangalore', 'Mumbai', 'Delhi', 'Toronto',
    'Vancouver'
]

# Validation
def validate_config():
    """Validate that all required configuration is present"""
    missing = []
    if not AIRTABLE_API_KEY:
        missing.append('AIRTABLE_API_KEY')
    if not AIRTABLE_BASE_ID:
        missing.append('AIRTABLE_BASE_ID')
    if not OPENAI_API_KEY:
        missing.append('OPENAI_API_KEY')
    
    if missing:
        raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
    
    return True
