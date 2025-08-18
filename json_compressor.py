"""
JSON Compression Script for Airtable Contractor Automation

This script gathers data from the three linked tables (Personal Details, Work Experience, 
Salary Preferences) and builds a single JSON object stored in the Applicants table.
"""

import json
import logging
from datetime import datetime, timedelta
from airtable import Airtable
import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JSONCompressor:
    def __init__(self):
        """Initialize the JSON Compressor with Airtable connections"""
        try:
            config.validate_config()
            self.applicants_table = Airtable(config.AIRTABLE_BASE_ID, config.TABLES['APPLICANTS'], api_key=config.AIRTABLE_API_KEY)
            self.personal_table = Airtable(config.AIRTABLE_BASE_ID, config.TABLES['PERSONAL_DETAILS'], api_key=config.AIRTABLE_API_KEY)
            self.experience_table = Airtable(config.AIRTABLE_BASE_ID, config.TABLES['WORK_EXPERIENCE'], api_key=config.AIRTABLE_API_KEY)
            self.salary_table = Airtable(config.AIRTABLE_BASE_ID, config.TABLES['SALARY_PREFERENCES'], api_key=config.AIRTABLE_API_KEY)
            logger.info("Successfully connected to all Airtable tables")
        except Exception as e:
            logger.error(f"Failed to initialize Airtable connections: {e}")
            raise

    def get_personal_details(self, applicant_id):
        """Fetch personal details for a specific applicant"""
        try:
            records = self.personal_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not records:
                logger.warning(f"No personal details found for applicant {applicant_id}")
                return {}
            
            record = records[0]['fields']
            return {
                'name': record.get('Full Name', ''),
                'email': record.get('Email', ''),
                'location': record.get('Location', ''),
                'linkedin': record.get('LinkedIn', ''),
                'phone': record.get('Phone', ''),
                'portfolio': record.get('Portfolio URL', '')
            }
        except Exception as e:
            logger.error(f"Error fetching personal details for {applicant_id}: {e}")
            return {}

    def get_work_experience(self, applicant_id):
        """Fetch all work experience records for a specific applicant"""
        try:
            records = self.experience_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not records:
                logger.warning(f"No work experience found for applicant {applicant_id}")
                return []
            
            experiences = []
            for record in records:
                fields = record['fields']
                
                # Calculate years of experience
                start_date = fields.get('Start Date')
                end_date = fields.get('End Date')
                years_experience = 0
                
                if start_date:
                    start = datetime.strptime(start_date, '%Y-%m-%d')
                    end = datetime.strptime(end_date, '%Y-%m-%d') if end_date else datetime.now()
                    years_experience = round((end - start).days / 365.25, 1)
                
                experience = {
                    'company': fields.get('Company', ''),
                    'title': fields.get('Title', ''),
                    'start_date': start_date,
                    'end_date': end_date,
                    'is_current': fields.get('Is Current', False),
                    'technologies': fields.get('Technologies', []),
                    'description': fields.get('Description', ''),
                    'years_experience': years_experience
                }
                experiences.append(experience)
            
            # Sort by start date (most recent first)
            experiences.sort(key=lambda x: x['start_date'] or '0000-00-00', reverse=True)
            return experiences
            
        except Exception as e:
            logger.error(f"Error fetching work experience for {applicant_id}: {e}")
            return []

    def get_salary_preferences(self, applicant_id):
        """Fetch salary preferences for a specific applicant"""
        try:
            records = self.salary_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not records:
                logger.warning(f"No salary preferences found for applicant {applicant_id}")
                return {}
            
            record = records[0]['fields']
            return {
                'preferred_rate': record.get('Preferred Rate', 0),
                'minimum_rate': record.get('Minimum Rate', 0),
                'currency': record.get('Currency', 'USD'),
                'availability': record.get('Availability', 0),
                'start_date': record.get('Start Date', ''),
                'contract_type': record.get('Contract Type', '')
            }
        except Exception as e:
            logger.error(f"Error fetching salary preferences for {applicant_id}: {e}")
            return {}

    def calculate_total_experience(self, experiences):
        """Calculate total years of experience across all positions"""
        if not experiences:
            return 0
        
        total_years = 0
        for exp in experiences:
            if exp.get('years_experience'):
                total_years += exp['years_experience']
        
        return round(total_years, 1)

    def has_tier1_company(self, experiences):
        """Check if applicant has worked at a tier-1 company"""
        for exp in experiences:
            company = exp.get('company', '').strip()
            if any(tier1.lower() in company.lower() for tier1 in config.TIER_1_COMPANIES):
                return True
        return False

    def compress_applicant_data(self, applicant_id):
        """Compress all data for a single applicant into JSON format"""
        try:
            logger.info(f"Compressing data for applicant {applicant_id}")
            
            # Gather data from all tables
            personal = self.get_personal_details(applicant_id)
            experiences = self.get_work_experience(applicant_id)
            salary = self.get_salary_preferences(applicant_id)
            
            # Calculate derived fields
            total_experience = self.calculate_total_experience(experiences)
            has_tier1 = self.has_tier1_company(experiences)
            
            # Build compressed JSON structure
            compressed_data = {
                'personal': personal,
                'experience': experiences,
                'salary': salary,
                'metadata': {
                    'total_experience_years': total_experience,
                    'has_tier1_company': has_tier1,
                    'compressed_at': datetime.now().isoformat(),
                    'record_count': {
                        'personal_details': 1 if personal else 0,
                        'work_experience': len(experiences),
                        'salary_preferences': 1 if salary else 0
                    }
                }
            }
            
            # Convert to JSON string
            json_string = json.dumps(compressed_data, indent=2)
            
            # Update the Applicants table with compressed JSON
            try:
                # Find the applicant record
                applicant_records = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
                
                if not applicant_records:
                    logger.error(f"No applicant record found for ID {applicant_id}")
                    return False
                
                record_id = applicant_records[0]['id']
                
                # Update with compressed JSON
                update_data = {
                    'Compressed JSON': json_string,
                    'Shortlist Status': 'Pending'  # Reset status for re-evaluation
                }
                
                self.applicants_table.update(record_id, update_data)
                logger.info(f"Successfully compressed and updated data for applicant {applicant_id}")
                return True
                
            except Exception as e:
                logger.error(f"Error updating applicant record {applicant_id}: {e}")
                return False
                
        except Exception as e:
            logger.error(f"Error compressing data for applicant {applicant_id}: {e}")
            return False

    def compress_all_applicants(self, force_update=False):
        """Compress data for all applicants"""
        try:
            logger.info("Starting compression for all applicants")
            
            # Get all applicants
            applicants = self.applicants_table.get_all()
            
            if not applicants:
                logger.warning("No applicants found in the database")
                return []
            
            results = []
            for applicant in applicants:
                applicant_id = applicant['fields'].get('Applicant ID')
                if not applicant_id:
                    logger.warning(f"Skipping record with missing Applicant ID: {applicant['id']}")
                    continue
                
                # Skip if already has compressed JSON (unless forcing update)
                if not force_update and applicant['fields'].get('Compressed JSON'):
                    logger.info(f"Skipping {applicant_id} - already has compressed JSON")
                    continue
                
                success = self.compress_applicant_data(applicant_id)
                results.append({
                    'applicant_id': applicant_id,
                    'success': success
                })
            
            successful = sum(1 for r in results if r['success'])
            logger.info(f"Compression completed: {successful}/{len(results)} applicants processed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in compress_all_applicants: {e}")
            return []

    def compress_single_applicant(self, applicant_id):
        """Compress data for a single applicant by ID"""
        logger.info(f"Compressing data for single applicant: {applicant_id}")
        return self.compress_applicant_data(applicant_id)

def main():
    """Main function for command line usage"""
    import sys
    
    compressor = JSONCompressor()
    
    if len(sys.argv) > 1:
        # Compress specific applicant
        applicant_id = sys.argv[1]
        success = compressor.compress_single_applicant(applicant_id)
        if success:
            print(f"Successfully compressed data for applicant {applicant_id}")
        else:
            print(f"Failed to compress data for applicant {applicant_id}")
    else:
        # Compress all applicants
        force_update = '--force' in sys.argv
        results = compressor.compress_all_applicants(force_update=force_update)
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"Compression completed:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        if failed > 0:
            failed_ids = [r['applicant_id'] for r in results if not r['success']]
            print(f"  Failed applicants: {', '.join(failed_ids)}")

if __name__ == "__main__":
    main()
