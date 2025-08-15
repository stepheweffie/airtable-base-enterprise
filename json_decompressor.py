"""
JSON Decompression Script for Mercor Airtable Automation

This script reads the compressed JSON from the Applicants table and upserts
the data back to the child tables (Personal Details, Work Experience, Salary Preferences).
"""

import json
import logging
from datetime import datetime
from airtable import Airtable
import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class JSONDecompressor:
    def __init__(self):
        """Initialize the JSON Decompressor with Airtable connections"""
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

    def get_compressed_data(self, applicant_id):
        """Fetch compressed JSON data for a specific applicant"""
        try:
            records = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not records:
                logger.error(f"No applicant found with ID {applicant_id}")
                return None
            
            compressed_json = records[0]['fields'].get('Compressed JSON')
            if not compressed_json:
                logger.error(f"No compressed JSON found for applicant {applicant_id}")
                return None
            
            try:
                return json.loads(compressed_json)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format for applicant {applicant_id}: {e}")
                return None
                
        except Exception as e:
            logger.error(f"Error fetching compressed data for {applicant_id}: {e}")
            return None

    def upsert_personal_details(self, applicant_id, personal_data):
        """Upsert personal details record"""
        try:
            if not personal_data:
                logger.warning(f"No personal data to upsert for applicant {applicant_id}")
                return True
            
            # Check if record already exists
            existing_records = self.personal_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            
            # Prepare data for upsert
            upsert_data = {
                'Applicant ID': [self._get_applicant_record_id(applicant_id)],
                'Full Name': personal_data.get('name', ''),
                'Email': personal_data.get('email', ''),
                'Location': personal_data.get('location', ''),
                'LinkedIn': personal_data.get('linkedin', ''),
                'Phone': personal_data.get('phone', ''),
                'Portfolio URL': personal_data.get('portfolio', '')
            }
            
            # Remove empty fields to avoid overwriting with blanks
            upsert_data = {k: v for k, v in upsert_data.items() if v}
            
            if existing_records:
                # Update existing record
                record_id = existing_records[0]['id']
                self.personal_table.update(record_id, upsert_data)
                logger.info(f"Updated personal details for applicant {applicant_id}")
            else:
                # Create new record
                self.personal_table.insert(upsert_data)
                logger.info(f"Created new personal details for applicant {applicant_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting personal details for {applicant_id}: {e}")
            return False

    def upsert_work_experience(self, applicant_id, experience_data):
        """Upsert work experience records"""
        try:
            if not experience_data:
                logger.warning(f"No experience data to upsert for applicant {applicant_id}")
                return True
            
            # Get existing experience records
            existing_records = self.experience_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            existing_by_company_title = {}
            
            for record in existing_records:
                fields = record['fields']
                key = f"{fields.get('Company', '')}-{fields.get('Title', '')}-{fields.get('Start Date', '')}"
                existing_by_company_title[key] = record
            
            applicant_record_id = self._get_applicant_record_id(applicant_id)
            processed_keys = set()
            
            # Process each experience from JSON
            for exp in experience_data:
                if not isinstance(exp, dict):
                    continue
                
                key = f"{exp.get('company', '')}-{exp.get('title', '')}-{exp.get('start_date', '')}"
                processed_keys.add(key)
                
                # Prepare data
                upsert_data = {
                    'Applicant ID': [applicant_record_id],
                    'Company': exp.get('company', ''),
                    'Title': exp.get('title', ''),
                    'Start Date': exp.get('start_date', ''),
                    'End Date': exp.get('end_date', ''),
                    'Technologies': exp.get('technologies', []),
                    'Description': exp.get('description', ''),
                    'Is Current': exp.get('is_current', False)
                }
                
                # Remove empty fields
                upsert_data = {k: v for k, v in upsert_data.items() if v or k == 'Is Current'}
                
                if key in existing_by_company_title:
                    # Update existing record
                    record_id = existing_by_company_title[key]['id']
                    update_data = {k: v for k, v in upsert_data.items() if k != 'Applicant ID'}
                    self.experience_table.update(record_id, update_data)
                    logger.info(f"Updated experience record: {exp.get('company')} - {exp.get('title')}")
                else:
                    # Create new record
                    self.experience_table.insert(upsert_data)
                    logger.info(f"Created new experience record: {exp.get('company')} - {exp.get('title')}")
            
            # Delete records that are no longer in the JSON
            for key, record in existing_by_company_title.items():
                if key not in processed_keys:
                    self.experience_table.delete(record['id'])
                    logger.info(f"Deleted obsolete experience record: {key}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting work experience for {applicant_id}: {e}")
            return False

    def upsert_salary_preferences(self, applicant_id, salary_data):
        """Upsert salary preferences record"""
        try:
            if not salary_data:
                logger.warning(f"No salary data to upsert for applicant {applicant_id}")
                return True
            
            # Check if record already exists
            existing_records = self.salary_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            
            # Prepare data for upsert
            upsert_data = {
                'Applicant ID': [self._get_applicant_record_id(applicant_id)],
                'Preferred Rate': salary_data.get('preferred_rate', 0),
                'Minimum Rate': salary_data.get('minimum_rate', 0),
                'Currency': salary_data.get('currency', 'USD'),
                'Availability': salary_data.get('availability', 0),
                'Start Date': salary_data.get('start_date', ''),
                'Contract Type': salary_data.get('contract_type', '')
            }
            
            # Remove empty fields
            upsert_data = {k: v for k, v in upsert_data.items() if v or isinstance(v, (int, float))}
            
            if existing_records:
                # Update existing record
                record_id = existing_records[0]['id']
                update_data = {k: v for k, v in upsert_data.items() if k != 'Applicant ID'}
                self.salary_table.update(record_id, update_data)
                logger.info(f"Updated salary preferences for applicant {applicant_id}")
            else:
                # Create new record
                self.salary_table.insert(upsert_data)
                logger.info(f"Created new salary preferences for applicant {applicant_id}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error upserting salary preferences for {applicant_id}: {e}")
            return False

    def _get_applicant_record_id(self, applicant_id):
        """Get the Airtable record ID for an applicant ID"""
        try:
            records = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if records:
                return records[0]['id']
            else:
                logger.error(f"No applicant record found for ID {applicant_id}")
                return None
        except Exception as e:
            logger.error(f"Error getting applicant record ID for {applicant_id}: {e}")
            return None

    def decompress_applicant_data(self, applicant_id):
        """Decompress data for a single applicant"""
        try:
            logger.info(f"Decompressing data for applicant {applicant_id}")
            
            # Get compressed data
            compressed_data = self.get_compressed_data(applicant_id)
            if not compressed_data:
                return False
            
            # Extract data sections
            personal_data = compressed_data.get('personal', {})
            experience_data = compressed_data.get('experience', [])
            salary_data = compressed_data.get('salary', {})
            
            # Upsert to each table
            success = True
            success &= self.upsert_personal_details(applicant_id, personal_data)
            success &= self.upsert_work_experience(applicant_id, experience_data)
            success &= self.upsert_salary_preferences(applicant_id, salary_data)
            
            if success:
                logger.info(f"Successfully decompressed all data for applicant {applicant_id}")
            else:
                logger.error(f"Some errors occurred while decompressing data for applicant {applicant_id}")
            
            return success
            
        except Exception as e:
            logger.error(f"Error decompressing data for applicant {applicant_id}: {e}")
            return False

    def decompress_all_applicants(self):
        """Decompress data for all applicants that have compressed JSON"""
        try:
            logger.info("Starting decompression for all applicants with compressed JSON")
            
            # Get all applicants with compressed JSON
            applicants = self.applicants_table.get_all()
            
            if not applicants:
                logger.warning("No applicants found in the database")
                return []
            
            results = []
            for applicant in applicants:
                applicant_id = applicant['fields'].get('Applicant ID')
                compressed_json = applicant['fields'].get('Compressed JSON')
                
                if not applicant_id:
                    logger.warning(f"Skipping record with missing Applicant ID: {applicant['id']}")
                    continue
                
                if not compressed_json:
                    logger.info(f"Skipping {applicant_id} - no compressed JSON")
                    continue
                
                success = self.decompress_applicant_data(applicant_id)
                results.append({
                    'applicant_id': applicant_id,
                    'success': success
                })
            
            successful = sum(1 for r in results if r['success'])
            logger.info(f"Decompression completed: {successful}/{len(results)} applicants processed successfully")
            return results
            
        except Exception as e:
            logger.error(f"Error in decompress_all_applicants: {e}")
            return []

    def decompress_single_applicant(self, applicant_id):
        """Decompress data for a single applicant by ID"""
        logger.info(f"Decompressing data for single applicant: {applicant_id}")
        return self.decompress_applicant_data(applicant_id)

    def validate_decompression(self, applicant_id):
        """Validate that decompressed data matches compressed JSON"""
        try:
            logger.info(f"Validating decompression for applicant {applicant_id}")
            
            # Get original compressed data
            compressed_data = self.get_compressed_data(applicant_id)
            if not compressed_data:
                return False
            
            # Re-compress the data and compare
            from json_compressor import JSONCompressor
            compressor = JSONCompressor()
            
            # Get current state of data
            personal = compressor.get_personal_details(applicant_id)
            experiences = compressor.get_work_experience(applicant_id)
            salary = compressor.get_salary_preferences(applicant_id)
            
            # Compare with original compressed data
            original_personal = compressed_data.get('personal', {})
            original_experiences = compressed_data.get('experience', [])
            original_salary = compressed_data.get('salary', {})
            
            # Basic validation (could be more thorough)
            personal_match = personal.get('name') == original_personal.get('name')
            experience_match = len(experiences) == len(original_experiences)
            salary_match = salary.get('preferred_rate') == original_salary.get('preferred_rate')
            
            validation_passed = personal_match and experience_match and salary_match
            
            if validation_passed:
                logger.info(f"Validation passed for applicant {applicant_id}")
            else:
                logger.warning(f"Validation failed for applicant {applicant_id}")
                logger.debug(f"Personal match: {personal_match}, Experience match: {experience_match}, Salary match: {salary_match}")
            
            return validation_passed
            
        except Exception as e:
            logger.error(f"Error validating decompression for {applicant_id}: {e}")
            return False

def main():
    """Main function for command line usage"""
    import sys
    
    decompressor = JSONDecompressor()
    
    if len(sys.argv) > 1:
        applicant_id = sys.argv[1]
        
        if '--validate' in sys.argv:
            # Validate decompression
            success = decompressor.validate_decompression(applicant_id)
            if success:
                print(f"Validation passed for applicant {applicant_id}")
            else:
                print(f"Validation failed for applicant {applicant_id}")
        else:
            # Decompress specific applicant
            success = decompressor.decompress_single_applicant(applicant_id)
            if success:
                print(f"Successfully decompressed data for applicant {applicant_id}")
            else:
                print(f"Failed to decompress data for applicant {applicant_id}")
    else:
        # Decompress all applicants
        results = decompressor.decompress_all_applicants()
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"Decompression completed:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        if failed > 0:
            failed_ids = [r['applicant_id'] for r in results if not r['success']]
            print(f"  Failed applicants: {', '.join(failed_ids)}")

if __name__ == "__main__":
    main()
