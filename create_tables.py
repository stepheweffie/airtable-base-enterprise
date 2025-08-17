#!/usr/bin/env python3
"""
Create Required Tables Script

This script creates all the required tables for the Mercor Airtable Automation system
using the Airtable API.
"""

import os
import sys
import requests
import json
from dotenv import load_dotenv

def create_table(base_id, api_key, table_config):
    """Create a table using Airtable API"""
    url = f"https://api.airtable.com/v0/meta/bases/{base_id}/tables"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    response = requests.post(url, headers=headers, json=table_config)
    
    if response.status_code == 200:
        table_data = response.json()
        return True, table_data
    else:
        return False, response.text

def get_table_configs():
    """Return all table configurations"""
    
    # 1. Applicants table (must be created first)
    applicants_config = {
        "name": "Applicants",
        "fields": [
            {
                "name": "Applicant ID",
                "type": "singleLineText"
            },
            {
                "name": "Compressed JSON",
                "type": "multilineText"
            },
            {
                "name": "Shortlist Status",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Pending"},
                        {"name": "Shortlisted"},
                        {"name": "Rejected"}
                    ]
                }
            },
            {
                "name": "LLM Summary",
                "type": "multilineText"
            },
            {
                "name": "LLM Score",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "LLM Follow-Ups",
                "type": "multilineText"
            },
            # Note: Created At and Modified At fields need to be added manually
        ]
    }
    
    return [
        ("Applicants", applicants_config),
    ]

def get_dependent_table_configs(applicants_table_id):
    """Return table configurations that depend on the Applicants table"""
    
    # 2. Personal Details table
    personal_details_config = {
        "name": "Personal Details",
        "fields": [
            {
                "name": "Record ID",
                "type": "singleLineText"
            },
            {
                "name": "Applicant ID",
                "type": "multipleRecordLinks",
                "options": {
                    "linkedTableId": applicants_table_id,
                    "isReversed": False
                }
            },
            {
                "name": "Full Name",
                "type": "singleLineText"
            },
            {
                "name": "Email",
                "type": "email"
            },
            {
                "name": "Location",
                "type": "singleLineText"
            },
            {
                "name": "LinkedIn",
                "type": "url"
            },
            {
                "name": "Phone",
                "type": "phoneNumber"
            },
            {
                "name": "Portfolio URL",
                "type": "url"
            }
        ]
    }
    
    # 3. Work Experience table
    work_experience_config = {
        "name": "Work Experience",
        "fields": [
            {
                "name": "Record ID",
                "type": "singleLineText"
            },
            {
                "name": "Applicant ID",
                "type": "multipleRecordLinks",
                "options": {
                    "linkedTableId": applicants_table_id,
                    "isReversed": False
                }
            },
            {
                "name": "Company",
                "type": "singleLineText"
            },
            {
                "name": "Title",
                "type": "singleLineText"
            },
            {
                "name": "Start Date",
                "type": "date",
                "options": {
                    "dateFormat": {
                        "name": "local",
                        "format": "l"
                    }
                }
            },
            {
                "name": "End Date",
                "type": "date",
                "options": {
                    "dateFormat": {
                        "name": "local",
                        "format": "l"
                    }
                }
            },
            {
                "name": "Technologies",
                "type": "multipleSelects",
                "options": {
                    "choices": [
                        {"name": "Python"},
                        {"name": "JavaScript"},
                        {"name": "TypeScript"},
                        {"name": "React"},
                        {"name": "Node.js"},
                        {"name": "Vue.js"},
                        {"name": "Angular"},
                        {"name": "Django"},
                        {"name": "Flask"},
                        {"name": "FastAPI"},
                        {"name": "PostgreSQL"},
                        {"name": "MySQL"},
                        {"name": "MongoDB"},
                        {"name": "Redis"},
                        {"name": "AWS"},
                        {"name": "Google Cloud"},
                        {"name": "Azure"},
                        {"name": "Docker"},
                        {"name": "Kubernetes"},
                        {"name": "Git"},
                        {"name": "Machine Learning"},
                        {"name": "Data Science"},
                        {"name": "DevOps"}
                    ]
                }
            },
            {
                "name": "Description",
                "type": "multilineText"
            },
            {
                "name": "Is Current",
                "type": "checkbox"
            }
        ]
    }
    
    # 4. Salary Preferences table
    salary_preferences_config = {
        "name": "Salary Preferences",
        "fields": [
            {
                "name": "Record ID",
                "type": "singleLineText"
            },
            {
                "name": "Applicant ID",
                "type": "multipleRecordLinks",
                "options": {
                    "linkedTableId": applicants_table_id,
                    "isReversed": False
                }
            },
            {
                "name": "Preferred Rate",
                "type": "number",
                "options": {
                    "precision": 2
                }
            },
            {
                "name": "Minimum Rate",
                "type": "number",
                "options": {
                    "precision": 2
                }
            },
            {
                "name": "Currency",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "USD"},
                        {"name": "EUR"},
                        {"name": "GBP"},
                        {"name": "CAD"},
                        {"name": "INR"}
                    ]
                }
            },
            {
                "name": "Availability",
                "type": "number",
                "options": {
                    "precision": 0
                }
            },
            {
                "name": "Start Date",
                "type": "date",
                "options": {
                    "dateFormat": {
                        "name": "local",
                        "format": "l"
                    }
                }
            },
            {
                "name": "Contract Type",
                "type": "singleSelect",
                "options": {
                    "choices": [
                        {"name": "Hourly"},
                        {"name": "Fixed-price"},
                        {"name": "Retainer"}
                    ]
                }
            }
        ]
    }
    
    # 5. Shortlisted Leads table
    shortlisted_leads_config = {
        "name": "Shortlisted Leads",
        "fields": [
            {
                "name": "Record ID",
                "type": "singleLineText"
            },
            {
                "name": "Applicant",
                "type": "multipleRecordLinks",
                "options": {
                    "linkedTableId": applicants_table_id,
                    "isReversed": False
                }
            },
            {
                "name": "Compressed JSON",
                "type": "multilineText"
            },
            {
                "name": "Score Reason",
                "type": "multilineText"
            },
            # Note: Created At field needs to be added manually
            # Note: Lookup fields (LLM Score, Applicant Name) will be added after table creation
        ]
    }
    
    return [
        ("Personal Details", personal_details_config),
        ("Work Experience", work_experience_config),
        ("Salary Preferences", salary_preferences_config),
        ("Shortlisted Leads", shortlisted_leads_config)
    ]

def main():
    print("Creating Required Tables for Mercor Airtable Automation")
    print("=" * 60)
    
    # Load environment variables
    load_dotenv()
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    if not api_key or not base_id:
        print("ERROR: Missing API key or base ID in .env file")
        sys.exit(1)
    
    print(f"Base ID: {base_id}")
    print(f"API Key: {api_key[:10]}...")
    print()
    
    created_tables = {}
    
    # Step 1: Create Applicants table first
    print("Step 1: Creating Applicants table...")
    table_configs = get_table_configs()
    
    for table_name, config in table_configs:
        print(f"Creating {table_name}...")
        success, result = create_table(base_id, api_key, config)
        
        if success:
            table_id = result['id']
            created_tables[table_name] = table_id
            print(f"SUCCESS: Created {table_name} (ID: {table_id})")
        else:
            print(f"ERROR: Failed to create {table_name}: {result}")
            sys.exit(1)
    
    # Step 2: Create dependent tables
    print("\nStep 2: Creating dependent tables...")
    applicants_table_id = created_tables["Applicants"]
    dependent_configs = get_dependent_table_configs(applicants_table_id)
    
    for table_name, config in dependent_configs:
        print(f"Creating {table_name}...")
        success, result = create_table(base_id, api_key, config)
        
        if success:
            table_id = result['id']
            created_tables[table_name] = table_id
            print(f"SUCCESS: Created {table_name} (ID: {table_id})")
        else:
            print(f"ERROR: Failed to create {table_name}: {result}")
            print(f"Continuing with remaining tables...")
    
    # Summary
    print(f"\nSUMMARY: Created {len(created_tables)} tables:")
    for name, table_id in created_tables.items():
        print(f"  - {name}: {table_id}")
    
    print("\nNEXT STEPS:")
    print("1. Test the system: python main.py status")
    print("2. Run the automation: python main.py pipeline")
    print("\nNote: Lookup fields in Shortlisted Leads table may need manual configuration")

if __name__ == "__main__":
    main()
