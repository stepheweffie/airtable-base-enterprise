"""
Sample Data Generator for Mercor Airtable Automation System

This script generates realistic test data for validating the complete automation pipeline.
It creates sample applicants with varying profiles to test different scenarios.
"""

import json
import logging
import random
from datetime import datetime, timedelta
from airtable import Airtable
import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class SampleDataGenerator:
    def __init__(self):
        """Initialize the sample data generator"""
        try:
            config.validate_config()
            self.applicants_table = Airtable(config.AIRTABLE_BASE_ID, config.TABLES['APPLICANTS'], api_key=config.AIRTABLE_API_KEY)
            self.personal_table = Airtable(config.AIRTABLE_BASE_ID, config.TABLES['PERSONAL_DETAILS'], api_key=config.AIRTABLE_API_KEY)
            self.experience_table = Airtable(config.AIRTABLE_BASE_ID, config.TABLES['WORK_EXPERIENCE'], api_key=config.AIRTABLE_API_KEY)
            self.salary_table = Airtable(config.AIRTABLE_BASE_ID, config.TABLES['SALARY_PREFERENCES'], api_key=config.AIRTABLE_API_KEY)
            logger.info("Successfully connected to all Airtable tables")
        except Exception as e:
            logger.error(f"Failed to initialize sample data generator: {e}")
            raise

    def generate_sample_applicants(self, count=5):
        """Generate sample applicant profiles"""
        
        sample_profiles = [
            # Profile 1: Senior engineer from tier-1 company (should be shortlisted)
            {
                'applicant_id': 'SAMPLE_001',
                'personal': {
                    'name': 'Alice Johnson',
                    'email': 'alice.johnson@email.com',
                    'location': 'San Francisco, CA',
                    'linkedin': 'https://linkedin.com/in/alicejohnson',
                    'phone': '+1-555-0101'
                },
                'experience': [
                    {
                        'company': 'Google',
                        'title': 'Senior Software Engineer',
                        'start_date': '2021-03-01',
                        'end_date': '2024-01-15',
                        'technologies': ['Python', 'JavaScript', 'React', 'PostgreSQL'],
                        'description': 'Led frontend development for search infrastructure'
                    },
                    {
                        'company': 'Startup Inc',
                        'title': 'Full Stack Developer',
                        'start_date': '2019-06-01',
                        'end_date': '2021-02-28',
                        'technologies': ['Node.js', 'MongoDB', 'Vue.js'],
                        'description': 'Built core platform features from scratch'
                    }
                ],
                'salary': {
                    'preferred_rate': 95,
                    'currency': 'USD',
                    'availability': 30
                }
            },
            
            # Profile 2: Experienced developer, high rate (should be rejected)
            {
                'applicant_id': 'SAMPLE_002',
                'personal': {
                    'name': 'Bob Smith',
                    'email': 'bob.smith@email.com',
                    'location': 'New York, NY',
                    'linkedin': 'https://linkedin.com/in/bobsmith'
                },
                'experience': [
                    {
                        'company': 'TechCorp',
                        'title': 'Lead Developer',
                        'start_date': '2018-01-01',
                        'end_date': None,  # Current position
                        'technologies': ['Java', 'Spring', 'MySQL', 'AWS'],
                        'description': 'Leading a team of 8 developers'
                    }
                ],
                'salary': {
                    'preferred_rate': 150,  # Too high
                    'currency': 'USD',
                    'availability': 25
                }
            },
            
            # Profile 3: Junior developer, good rate and availability (should be rejected - not enough experience)
            {
                'applicant_id': 'SAMPLE_003',
                'personal': {
                    'name': 'Carol Williams',
                    'email': 'carol.williams@email.com',
                    'location': 'Toronto, Canada',
                    'linkedin': 'https://linkedin.com/in/carolwilliams'
                },
                'experience': [
                    {
                        'company': 'Local Agency',
                        'title': 'Junior Developer',
                        'start_date': '2022-09-01',
                        'end_date': None,
                        'technologies': ['JavaScript', 'React', 'Node.js'],
                        'description': 'Working on client websites and small applications'
                    }
                ],
                'salary': {
                    'preferred_rate': 45,
                    'currency': 'USD',
                    'availability': 40
                }
            },
            
            # Profile 4: Meta employee, good rate (should be shortlisted)
            {
                'applicant_id': 'SAMPLE_004',
                'personal': {
                    'name': 'David Chen',
                    'email': 'david.chen@email.com',
                    'location': 'London, UK',
                    'linkedin': 'https://linkedin.com/in/davidchen'
                },
                'experience': [
                    {
                        'company': 'Meta',
                        'title': 'Software Engineer',
                        'start_date': '2020-08-01',
                        'end_date': '2023-12-31',
                        'technologies': ['Python', 'React', 'GraphQL', 'Docker'],
                        'description': 'Worked on Instagram backend infrastructure'
                    },
                    {
                        'company': 'Freelance',
                        'title': 'Consultant',
                        'start_date': '2024-01-01',
                        'end_date': None,
                        'technologies': ['Python', 'FastAPI', 'PostgreSQL'],
                        'description': 'Providing technical consulting services'
                    }
                ],
                'salary': {
                    'preferred_rate': 80,
                    'currency': 'USD',
                    'availability': 25
                }
            },
            
            # Profile 5: Indian developer, low availability (should be rejected)
            {
                'applicant_id': 'SAMPLE_005',
                'personal': {
                    'name': 'Priya Patel',
                    'email': 'priya.patel@email.com',
                    'location': 'Mumbai, India',
                    'linkedin': 'https://linkedin.com/in/priyapatel'
                },
                'experience': [
                    {
                        'company': 'Indian Tech Solutions',
                        'title': 'Senior Developer',
                        'start_date': '2017-04-01',
                        'end_date': None,
                        'technologies': ['Java', 'Spring Boot', 'React', 'MongoDB'],
                        'description': 'Leading development of enterprise applications'
                    }
                ],
                'salary': {
                    'preferred_rate': 35,
                    'currency': 'USD',
                    'availability': 15  # Too low
                }
            }
        ]
        
        return sample_profiles[:count]

    def create_applicant_record(self, applicant_id):
        """Create an applicant record in Airtable"""
        try:
            # Check if applicant already exists
            existing = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if existing:
                logger.info(f"Applicant {applicant_id} already exists, skipping creation")
                return existing[0]['id']
            
            # Create new applicant record
            record_data = {'Applicant ID': applicant_id}
            record = self.applicants_table.insert(record_data)
            logger.info(f"Created applicant record for {applicant_id}")
            return record['id']
            
        except Exception as e:
            logger.error(f"Error creating applicant record for {applicant_id}: {e}")
            return None

    def create_personal_details(self, applicant_id, personal_data):
        """Create personal details record"""
        try:
            # Get applicant record ID
            applicant_records = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not applicant_records:
                logger.error(f"No applicant record found for {applicant_id}")
                return False
            
            applicant_record_id = applicant_records[0]['id']
            
            # Check if personal details already exist
            existing = self.personal_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if existing:
                logger.info(f"Personal details for {applicant_id} already exist, skipping")
                return True
            
            # Create personal details record
            record_data = {
                'Applicant ID': [applicant_record_id],
                'Full Name': personal_data.get('name', ''),
                'Email': personal_data.get('email', ''),
                'Location': personal_data.get('location', ''),
                'LinkedIn': personal_data.get('linkedin', ''),
                'Phone': personal_data.get('phone', ''),
                'Portfolio URL': personal_data.get('portfolio', '')
            }
            
            # Remove empty fields
            record_data = {k: v for k, v in record_data.items() if v}
            
            self.personal_table.insert(record_data)
            logger.info(f"Created personal details for {applicant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating personal details for {applicant_id}: {e}")
            return False

    def create_work_experience(self, applicant_id, experience_data):
        """Create work experience records"""
        try:
            # Get applicant record ID
            applicant_records = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not applicant_records:
                logger.error(f"No applicant record found for {applicant_id}")
                return False
            
            applicant_record_id = applicant_records[0]['id']
            
            # Clear existing experience records
            existing = self.experience_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            for record in existing:
                self.experience_table.delete(record['id'])
            
            # Create new experience records
            for exp in experience_data:
                record_data = {
                    'Applicant ID': [applicant_record_id],
                    'Company': exp.get('company', ''),
                    'Title': exp.get('title', ''),
                    'Start Date': exp.get('start_date', ''),
                    'End Date': exp.get('end_date', ''),
                    'Technologies': exp.get('technologies', []),
                    'Description': exp.get('description', ''),
                    'Is Current': not exp.get('end_date')  # Current if no end date
                }
                
                # Remove empty fields
                record_data = {k: v for k, v in record_data.items() if v or k == 'Is Current'}
                
                self.experience_table.insert(record_data)
                logger.info(f"Created experience record: {exp.get('company')} - {exp.get('title')}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating work experience for {applicant_id}: {e}")
            return False

    def create_salary_preferences(self, applicant_id, salary_data):
        """Create salary preferences record"""
        try:
            # Get applicant record ID
            applicant_records = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not applicant_records:
                logger.error(f"No applicant record found for {applicant_id}")
                return False
            
            applicant_record_id = applicant_records[0]['id']
            
            # Check if salary preferences already exist
            existing = self.salary_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if existing:
                logger.info(f"Salary preferences for {applicant_id} already exist, updating")
                record_id = existing[0]['id']
                update_data = {
                    'Preferred Rate': salary_data.get('preferred_rate', 0),
                    'Currency': salary_data.get('currency', 'USD'),
                    'Availability': salary_data.get('availability', 0)
                }
                self.salary_table.update(record_id, update_data)
            else:
                # Create salary preferences record
                record_data = {
                    'Applicant ID': [applicant_record_id],
                    'Preferred Rate': salary_data.get('preferred_rate', 0),
                    'Currency': salary_data.get('currency', 'USD'),
                    'Availability': salary_data.get('availability', 0)
                }
                
                self.salary_table.insert(record_data)
                logger.info(f"Created salary preferences for {applicant_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error creating salary preferences for {applicant_id}: {e}")
            return False

    def generate_and_insert_sample_data(self, count=5):
        """Generate and insert complete sample data"""
        logger.info(f"Generating {count} sample applicants...")
        
        sample_profiles = self.generate_sample_applicants(count)
        results = []
        
        for profile in sample_profiles:
            applicant_id = profile['applicant_id']
            logger.info(f"Creating sample data for {applicant_id}")
            
            success = True
            
            # Create applicant record
            if not self.create_applicant_record(applicant_id):
                success = False
                logger.error(f"Failed to create applicant record for {applicant_id}")
                continue
            
            # Create personal details
            if not self.create_personal_details(applicant_id, profile['personal']):
                success = False
                logger.error(f"Failed to create personal details for {applicant_id}")
            
            # Create work experience
            if not self.create_work_experience(applicant_id, profile['experience']):
                success = False
                logger.error(f"Failed to create work experience for {applicant_id}")
            
            # Create salary preferences
            if not self.create_salary_preferences(applicant_id, profile['salary']):
                success = False
                logger.error(f"Failed to create salary preferences for {applicant_id}")
            
            results.append({
                'applicant_id': applicant_id,
                'success': success
            })
            
            if success:
                logger.info(f"Successfully created complete profile for {applicant_id}")
        
        successful = sum(1 for r in results if r['success'])
        logger.info(f"Sample data generation completed: {successful}/{len(results)} successful")
        
        return results

    def cleanup_sample_data(self):
        """Remove all sample data (applicant IDs starting with SAMPLE_)"""
        logger.info("Cleaning up sample data...")
        
        try:
            # Get all sample applicants
            all_applicants = self.applicants_table.get_all()
            sample_applicants = [a for a in all_applicants if a['fields'].get('Applicant ID', '').startswith('SAMPLE_')]
            
            deleted_count = 0
            for applicant in sample_applicants:
                applicant_id = applicant['fields']['Applicant ID']
                
                # Delete from all child tables first
                for table in [self.personal_table, self.experience_table, self.salary_table]:
                    records = table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
                    for record in records:
                        table.delete(record['id'])
                
                # Delete from applicants table
                self.applicants_table.delete(applicant['id'])
                deleted_count += 1
                logger.info(f"Deleted sample applicant: {applicant_id}")
            
            logger.info(f"Cleanup completed: {deleted_count} sample applicants removed")
            return deleted_count
            
        except Exception as e:
            logger.error(f"Error during cleanup: {e}")
            return 0

def main():
    """Main function for command line usage"""
    import sys
    
    generator = SampleDataGenerator()
    
    if '--cleanup' in sys.argv:
        # Cleanup sample data
        deleted_count = generator.cleanup_sample_data()
        print(f"Cleaned up {deleted_count} sample applicants")
    else:
        # Generate sample data
        count = 5
        if len(sys.argv) > 1 and sys.argv[1].isdigit():
            count = int(sys.argv[1])
        
        results = generator.generate_and_insert_sample_data(count)
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"Sample data generation completed:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        if successful > 0:
            print("\nExpected shortlisting results:")
            print("  SAMPLE_001 (Alice): Should be SHORTLISTED (Google, good rate)")
            print("  SAMPLE_002 (Bob): Should be REJECTED (rate too high)")
            print("  SAMPLE_003 (Carol): Should be REJECTED (insufficient experience)")
            print("  SAMPLE_004 (David): Should be SHORTLISTED (Meta, good rate)")
            print("  SAMPLE_005 (Priya): Should be REJECTED (low availability)")
            print("\nRun 'python main.py pipeline' to test the complete automation!")

if __name__ == "__main__":
    main()
