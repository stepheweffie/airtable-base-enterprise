"""
Test fixtures and sample data for Mercor Airtable Automation tests
"""

import json
from datetime import datetime, timedelta
from faker import Faker

fake = Faker()

# Sample applicant data
SAMPLE_PERSONAL_DETAILS = {
    'Full Name': 'John Smith',
    'Email': 'john.smith@example.com',
    'Location': 'San Francisco, CA',
    'LinkedIn': 'https://linkedin.com/in/johnsmith',
    'Phone': '+1-555-123-4567',
    'Portfolio URL': 'https://johnsmith.dev'
}

SAMPLE_WORK_EXPERIENCE = [
    {
        'Company': 'Google',
        'Title': 'Senior Software Engineer',
        'Start Date': '2020-01-01',
        'End Date': '2023-06-01',
        'Is Current': False,
        'Technologies': ['Python', 'Go', 'Kubernetes', 'GCP'],
        'Description': 'Led backend development for Google Search improvements',
        'years_experience': 3.5
    },
    {
        'Company': 'Meta',
        'Title': 'Software Engineer',
        'Start Date': '2018-06-01',
        'End Date': '2019-12-31',
        'Is Current': False,
        'Technologies': ['React', 'JavaScript', 'GraphQL'],
        'Description': 'Worked on Instagram web frontend',
        'years_experience': 1.5
    }
]

SAMPLE_SALARY_PREFERENCES = {
    'Preferred Rate': 85,
    'Minimum Rate': 70,
    'Currency': 'USD',
    'Availability': 30,
    'Start Date': '2024-02-01',
    'Contract Type': 'Contract'
}

SAMPLE_COMPRESSED_JSON = {
    'personal': {
        'name': 'John Smith',
        'email': 'john.smith@example.com',
        'location': 'San Francisco, CA',
        'linkedin': 'https://linkedin.com/in/johnsmith',
        'phone': '+1-555-123-4567',
        'portfolio': 'https://johnsmith.dev'
    },
    'experience': [
        {
            'company': 'Google',
            'title': 'Senior Software Engineer',
            'start_date': '2020-01-01',
            'end_date': '2023-06-01',
            'is_current': False,
            'technologies': ['Python', 'Go', 'Kubernetes', 'GCP'],
            'description': 'Led backend development for Google Search improvements',
            'years_experience': 3.5
        },
        {
            'company': 'Meta',
            'title': 'Software Engineer',
            'start_date': '2018-06-01',
            'end_date': '2019-12-31',
            'is_current': False,
            'technologies': ['React', 'JavaScript', 'GraphQL'],
            'description': 'Worked on Instagram web frontend',
            'years_experience': 1.5
        }
    ],
    'salary': {
        'preferred_rate': 85,
        'minimum_rate': 70,
        'currency': 'USD',
        'availability': 30,
        'start_date': '2024-02-01',
        'contract_type': 'Contract'
    },
    'metadata': {
        'total_experience_years': 5.0,
        'has_tier1_company': True,
        'compressed_at': '2024-01-15T10:30:00',
        'record_count': {
            'personal_details': 1,
            'work_experience': 2,
            'salary_preferences': 1
        }
    }
}

# Test cases for shortlisting criteria
SHORTLISTING_TEST_CASES = [
    {
        'name': 'qualified_tier1_company',
        'description': 'Should pass: Has tier-1 company experience',
        'data': {
            'personal': {'location': 'San Francisco, CA'},
            'experience': [{'company': 'Google', 'years_experience': 2.0}],
            'salary': {'preferred_rate': 90, 'currency': 'USD', 'availability': 25},
            'metadata': {'total_experience_years': 2.0, 'has_tier1_company': True}
        },
        'expected_pass': True
    },
    {
        'name': 'qualified_experience_years',
        'description': 'Should pass: Has 4+ years experience',
        'data': {
            'personal': {'location': 'Toronto, Canada'},
            'experience': [{'company': 'Startup Inc', 'years_experience': 4.5}],
            'salary': {'preferred_rate': 75, 'currency': 'USD', 'availability': 30},
            'metadata': {'total_experience_years': 4.5, 'has_tier1_company': False}
        },
        'expected_pass': True
    },
    {
        'name': 'rejected_low_experience',
        'description': 'Should fail: Low experience, no tier-1 company',
        'data': {
            'personal': {'location': 'New York, NY'},
            'experience': [{'company': 'Small Corp', 'years_experience': 2.0}],
            'salary': {'preferred_rate': 80, 'currency': 'USD', 'availability': 25},
            'metadata': {'total_experience_years': 2.0, 'has_tier1_company': False}
        },
        'expected_pass': False
    },
    {
        'name': 'rejected_high_rate',
        'description': 'Should fail: Rate too high',
        'data': {
            'personal': {'location': 'London, UK'},
            'experience': [{'company': 'Google', 'years_experience': 3.0}],
            'salary': {'preferred_rate': 150, 'currency': 'USD', 'availability': 25},
            'metadata': {'total_experience_years': 3.0, 'has_tier1_company': True}
        },
        'expected_pass': False
    },
    {
        'name': 'rejected_low_availability',
        'description': 'Should fail: Low availability',
        'data': {
            'personal': {'location': 'Berlin, Germany'},
            'experience': [{'company': 'Meta', 'years_experience': 4.0}],
            'salary': {'preferred_rate': 85, 'currency': 'USD', 'availability': 15},
            'metadata': {'total_experience_years': 4.0, 'has_tier1_company': True}
        },
        'expected_pass': False
    },
    {
        'name': 'rejected_location',
        'description': 'Should fail: Location not allowed',
        'data': {
            'personal': {'location': 'Tokyo, Japan'},
            'experience': [{'company': 'Apple', 'years_experience': 5.0}],
            'salary': {'preferred_rate': 90, 'currency': 'USD', 'availability': 30},
            'metadata': {'total_experience_years': 5.0, 'has_tier1_company': True}
        },
        'expected_pass': False
    }
]

# LLM evaluation test cases
LLM_EVALUATION_TEST_CASES = [
    {
        'name': 'strong_candidate',
        'mock_response': """Summary: Experienced engineer with strong background at Google and Meta, specializing in full-stack development with modern technologies. Demonstrates leadership in backend systems and proven track record in high-scale applications. Well-positioned for senior contractor roles.
Score: 8
Issues: None
Follow-Ups: • What specific achievements at Google can you elaborate on? • Are you open to leading small development teams? • What's your experience with cloud architecture design?""",
        'expected_score': 8,
        'expected_issues': 'None',
        'expected_follow_ups_count': 3
    },
    {
        'name': 'average_candidate',
        'mock_response': """Summary: Mid-level developer with decent experience but limited senior-level responsibilities. Technologies are current but depth unclear. Compensation expectations reasonable and availability good for project needs.
Score: 5
Issues: Limited leadership experience mentioned, unclear technical depth
Follow-Ups: • Can you provide examples of complex problems you've solved? • Have you mentored junior developers?""",
        'expected_score': 5,
        'expected_issues': 'Limited leadership experience mentioned, unclear technical depth',
        'expected_follow_ups_count': 2
    }
]

# Mock Airtable records
MOCK_APPLICANT_RECORDS = [
    {
        'id': 'rec123456789',
        'fields': {
            'Applicant ID': 'APPLICANT_001',
            'Status': 'Active',
            'Compressed JSON': json.dumps(SAMPLE_COMPRESSED_JSON),
            'Shortlist Status': 'Pending',
            'LLM Evaluation': '',
            'LLM Score': 0,
            'Created': '2024-01-15T10:00:00.000Z'
        }
    }
]

MOCK_PERSONAL_RECORDS = [
    {
        'id': 'rec_personal_001',
        'fields': {
            'Applicant ID': 'APPLICANT_001',
            **SAMPLE_PERSONAL_DETAILS
        }
    }
]

MOCK_EXPERIENCE_RECORDS = [
    {
        'id': 'rec_exp_001',
        'fields': {
            'Applicant ID': 'APPLICANT_001',
            **SAMPLE_WORK_EXPERIENCE[0]
        }
    },
    {
        'id': 'rec_exp_002',
        'fields': {
            'Applicant ID': 'APPLICANT_001',
            **SAMPLE_WORK_EXPERIENCE[1]
        }
    }
]

MOCK_SALARY_RECORDS = [
    {
        'id': 'rec_salary_001',
        'fields': {
            'Applicant ID': 'APPLICANT_001',
            **SAMPLE_SALARY_PREFERENCES
        }
    }
]

def generate_random_applicant_data():
    """Generate random but realistic applicant data for testing"""
    companies = ['Google', 'Meta', 'Amazon', 'Microsoft', 'Netflix', 'Stripe', 'Airbnb', 'StartupCorp', 'TechCo']
    titles = ['Software Engineer', 'Senior Software Engineer', 'Staff Engineer', 'Engineering Manager', 'Full Stack Developer']
    technologies = ['Python', 'JavaScript', 'React', 'Node.js', 'Go', 'Java', 'TypeScript', 'AWS', 'Docker', 'Kubernetes']
    locations = ['San Francisco, CA', 'New York, NY', 'Seattle, WA', 'Austin, TX', 'Toronto, Canada', 'London, UK', 'Berlin, Germany']
    
    # Generate experiences
    num_experiences = fake.random_int(min=1, max=4)
    experiences = []
    
    for i in range(num_experiences):
        years_exp = fake.random.uniform(0.5, 5.0)
        start_date = fake.date_between(start_date='-6y', end_date='-1y')
        end_date = None if i == 0 and fake.boolean(chance_of_getting_true=30) else fake.date_between(start_date=start_date, end_date='today')
        
        experiences.append({
            'company': fake.random_element(companies),
            'title': fake.random_element(titles),
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat() if end_date else None,
            'is_current': end_date is None,
            'technologies': fake.random_elements(technologies, unique=True, length=fake.random_int(2, 5)),
            'description': fake.sentence(nb_words=10),
            'years_experience': round(years_exp, 1)
        })
    
    total_years = sum(exp['years_experience'] for exp in experiences)
    has_tier1 = any(company in ['Google', 'Meta', 'Amazon', 'Microsoft', 'Netflix', 'Stripe', 'Airbnb'] for company in [exp['company'] for exp in experiences])
    
    return {
        'personal': {
            'name': fake.name(),
            'email': fake.email(),
            'location': fake.random_element(locations),
            'linkedin': f"https://linkedin.com/in/{fake.user_name()}",
            'phone': fake.phone_number(),
            'portfolio': f"https://{fake.user_name()}.dev"
        },
        'experience': experiences,
        'salary': {
            'preferred_rate': fake.random_int(min=50, max=200),
            'minimum_rate': fake.random_int(min=40, max=150),
            'currency': fake.random_element(['USD', 'EUR', 'GBP', 'CAD']),
            'availability': fake.random_int(min=10, max=40),
            'start_date': fake.future_date(end_date='+30d').isoformat(),
            'contract_type': fake.random_element(['Contract', 'Part-time', 'Full-time'])
        },
        'metadata': {
            'total_experience_years': round(total_years, 1),
            'has_tier1_company': has_tier1,
            'compressed_at': datetime.now().isoformat(),
            'record_count': {
                'personal_details': 1,
                'work_experience': len(experiences),
                'salary_preferences': 1
            }
        }
    }

def create_mock_airtable_record(applicant_id, data=None):
    """Create a mock Airtable record structure"""
    if data is None:
        data = generate_random_applicant_data()
    
    return {
        'id': f'rec_{fake.lexify("??????????", letters="abcdefghijklmnopqrstuvwxyz0123456789")}',
        'fields': {
            'Applicant ID': applicant_id,
            'Status': 'Active',
            'Compressed JSON': json.dumps(data),
            'Shortlist Status': 'Pending',
            'LLM Evaluation': '',
            'LLM Score': 0,
            'Created': fake.past_datetime(start_date='-30d').isoformat() + 'Z'
        }
    }

# Currency conversion test data
CURRENCY_CONVERSION_TEST_CASES = [
    {'rate': 100, 'currency': 'USD', 'expected': 100},
    {'rate': 100, 'currency': 'EUR', 'expected': 108},
    {'rate': 100, 'currency': 'GBP', 'expected': 125},
    {'rate': 100, 'currency': 'CAD', 'expected': 74},
    {'rate': 100, 'currency': 'INR', 'expected': 1.2},
    {'rate': 100, 'currency': 'XYZ', 'expected': 100}  # Unknown currency
]
