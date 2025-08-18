#!/usr/bin/env python3
"""
Add Test Data Script

This script adds sample applicant data to test the Mercor Airtable Automation system.
"""

import os
import sys
from dotenv import load_dotenv
from airtable import Airtable

def add_test_applicant():
    """Add a sample applicant with complete data across all tables"""
    
    load_dotenv()
    api_key = os.getenv('AIRTABLE_API_KEY')
    base_id = os.getenv('AIRTABLE_BASE_ID')
    
    if not api_key or not base_id:
        print("ERROR: Missing API key or base ID in .env file")
        return False
    
    # Initialize table connections
    applicants_table = Airtable(base_id, 'Applicants', api_key=api_key)
    personal_details_table = Airtable(base_id, 'Personal Details', api_key=api_key)
    work_experience_table = Airtable(base_id, 'Work Experience', api_key=api_key)
    salary_preferences_table = Airtable(base_id, 'Salary Preferences', api_key=api_key)
    
    try:
        # 1. Create main applicant record
        applicant_data = {
            'Applicant ID': 'APP-001-TEST',
            'Shortlist Status': 'Pending'
        }
        
        print("Creating test applicant...")
        applicant_record = applicants_table.insert(applicant_data)
        applicant_id = applicant_record['id']
        print(f"SUCCESS: Created applicant with ID: {applicant_id}")
        
        # 2. Add personal details
        personal_data = {
            'Record ID': 'PD-001',
            'Applicant ID': 'APP-001-TEST',
            'Full Name': 'John Smith',
            'Email': 'john.smith@example.com',
            'Location': 'San Francisco, CA',
            'LinkedIn': 'https://linkedin.com/in/johnsmith',
            'Phone': '+1-555-123-4567',
            'Portfolio URL': 'https://johnsmith.dev'
        }
        
        print("Adding personal details...")
        personal_record = personal_details_table.insert(personal_data)
        print(f"SUCCESS: Created personal details with ID: {personal_record['id']}")
        
        # 3. Add work experience
        work_data = [
            {
                'Record ID': 'WE-001',
                'Applicant ID': 'APP-001-TEST',
                'Company': 'Tech Corp',
                'Title': 'Senior Software Engineer',
                'Start Date': '2022-01-15',
                'End Date': '2024-08-01',
                'Description': 'Led development of microservices architecture using Python and React',
                'Is Current': False
            },
            {
                'Record ID': 'WE-002',
                'Applicant ID': 'APP-001-TEST',
                'Company': 'Startup Inc',
                'Title': 'Full Stack Developer',
                'Start Date': '2024-08-15',
                'Description': 'Building scalable web applications with modern tech stack',
                'Is Current': True
            }
        ]
        
        print("Adding work experience...")
        for work in work_data:
            work_record = work_experience_table.insert(work)
            print(f"SUCCESS: Created work experience at {work['Company']}")
        
        # 4. Add salary preferences
        salary_data = {
            'Record ID': 'SP-001',
            'Applicant ID': 'APP-001-TEST',
            'Preferred Rate': 85.00,
            'Minimum Rate': 70.00,
            'Currency': 'USD',
            'Availability': 40,
            'Start Date': '2024-09-01',
            'Contract Type': 'Hourly'
        }
        
        print("Adding salary preferences...")
        salary_record = salary_preferences_table.insert(salary_data)
        print(f"SUCCESS: Created salary preferences with ID: {salary_record['id']}")
        
        print("\\nTest data added successfully!")
        print(f"Test applicant ID: APP-001-TEST")
        print("\\nYou can now run:")
        print("  python main.py status")
        print("  python main.py pipeline")
        print("  python main.py compress APP-001-TEST")
        
        return True
        
    except Exception as e:
        print(f"ERROR: Failed to add test data: {e}")
        return False

def main():
    print("Adding Test Data to Mercor Airtable Automation")
    print("=" * 50)
    
    success = add_test_applicant()
    
    if success:
        print("\\nSUCCESS: Test data added successfully!")
    else:
        print("\\nERROR: Failed to add test data")

if __name__ == "__main__":
    main()
