"""
Shortlisting Automation Script for Airtable Contractor Automation

This script evaluates candidates against defined criteria and automatically 
populates the Shortlisted Leads table for qualifying applicants.

Criteria:
1. Experience: ≥ 4 years total OR worked at a Tier-1 company
2. Compensation: Preferred Rate ≤ $100 USD/hour AND Availability ≥ 20 hrs/week
3. Location: In US, Canada, UK, Germany, or India
"""

import json
import logging
from datetime import datetime
from airtable import Airtable
import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class Shortlister:
    def __init__(self):
        """Initialize the Shortlister with Airtable connections"""
        try:
            config.validate_config()
            self.applicants_table = Airtable(config.AIRTABLE_BASE_ID, config.TABLES['APPLICANTS'], api_key=config.AIRTABLE_API_KEY)
            self.shortlisted_table = Airtable(config.AIRTABLE_BASE_ID, config.TABLES['SHORTLISTED_LEADS'], api_key=config.AIRTABLE_API_KEY)
            logger.info("Successfully connected to Airtable tables")
        except Exception as e:
            logger.error(f"Failed to initialize Airtable connections: {e}")
            raise

    def convert_rate_to_usd(self, rate, currency):
        """Convert rate to USD for comparison (simplified conversion)"""
        conversion_rates = {
            'USD': 1.0,
            'EUR': 1.08,  # Approximate rates
            'GBP': 1.25,
            'CAD': 0.74,
            'INR': 0.012
        }
        
        if currency not in conversion_rates:
            logger.warning(f"Unknown currency {currency}, assuming USD")
            return rate
        
        return rate * conversion_rates[currency]

    def check_experience_criteria(self, applicant_data):
        """Check if applicant meets experience criteria"""
        try:
            metadata = applicant_data.get('metadata', {})
            total_experience = metadata.get('total_experience_years', 0)
            has_tier1 = metadata.get('has_tier1_company', False)
            
            # Criteria: ≥ 4 years total OR worked at a Tier-1 company
            meets_criteria = total_experience >= 4.0 or has_tier1
            
            reason = []
            if total_experience >= 4.0:
                reason.append(f"{total_experience} years total experience")
            if has_tier1:
                # Find which tier-1 companies
                tier1_companies = []
                for exp in applicant_data.get('experience', []):
                    company = exp.get('company', '').strip()
                    if any(tier1.lower() in company.lower() for tier1 in config.TIER_1_COMPANIES):
                        tier1_companies.append(company)
                
                if tier1_companies:
                    reason.append(f"worked at tier-1 company: {', '.join(set(tier1_companies))}")
            
            return meets_criteria, '; '.join(reason) if reason else "Does not meet experience criteria"
            
        except Exception as e:
            logger.error(f"Error checking experience criteria: {e}")
            return False, "Error evaluating experience"

    def check_compensation_criteria(self, applicant_data):
        """Check if applicant meets compensation criteria"""
        try:
            salary_data = applicant_data.get('salary', {})
            preferred_rate = salary_data.get('preferred_rate', 0)
            currency = salary_data.get('currency', 'USD')
            availability = salary_data.get('availability', 0)
            
            # Convert rate to USD
            usd_rate = self.convert_rate_to_usd(preferred_rate, currency)
            
            # Criteria: Preferred Rate ≤ $100 USD/hour AND Availability ≥ 20 hrs/week
            rate_ok = usd_rate <= 100
            availability_ok = availability >= 20
            meets_criteria = rate_ok and availability_ok
            
            reason = []
            if rate_ok:
                reason.append(f"rate ${usd_rate:.0f}/hr USD ≤ $100")
            else:
                reason.append(f"rate ${usd_rate:.0f}/hr USD > $100")
            
            if availability_ok:
                reason.append(f"{availability} hrs/week ≥ 20")
            else:
                reason.append(f"{availability} hrs/week < 20")
            
            return meets_criteria, '; '.join(reason)
            
        except Exception as e:
            logger.error(f"Error checking compensation criteria: {e}")
            return False, "Error evaluating compensation"

    def check_location_criteria(self, applicant_data):
        """Check if applicant meets location criteria"""
        try:
            personal_data = applicant_data.get('personal', {})
            location = personal_data.get('location', '').strip()
            
            if not location:
                return False, "No location specified"
            
            # Check against allowed locations (case-insensitive partial matching)
            location_lower = location.lower()
            allowed_matches = []
            
            for allowed in config.ALLOWED_LOCATIONS:
                if allowed.lower() in location_lower or location_lower in allowed.lower():
                    allowed_matches.append(allowed)
            
            meets_criteria = len(allowed_matches) > 0
            
            if meets_criteria:
                reason = f"location '{location}' matches allowed: {', '.join(allowed_matches)}"
            else:
                reason = f"location '{location}' not in allowed regions"
            
            return meets_criteria, reason
            
        except Exception as e:
            logger.error(f"Error checking location criteria: {e}")
            return False, "Error evaluating location"

    def evaluate_applicant(self, applicant_id, applicant_data):
        """Evaluate a single applicant against all criteria"""
        try:
            logger.info(f"Evaluating applicant {applicant_id}")
            
            # Check each criteria
            experience_pass, experience_reason = self.check_experience_criteria(applicant_data)
            compensation_pass, compensation_reason = self.check_compensation_criteria(applicant_data)
            location_pass, location_reason = self.check_location_criteria(applicant_data)
            
            # All criteria must pass
            overall_pass = experience_pass and compensation_pass and location_pass
            
            # Build detailed reason
            reasons = [
                f"Experience: {experience_reason}",
                f"Compensation: {compensation_reason}",
                f"Location: {location_reason}"
            ]
            
            detailed_reason = ' | '.join(reasons)
            
            result = {
                'applicant_id': applicant_id,
                'overall_pass': overall_pass,
                'experience_pass': experience_pass,
                'compensation_pass': compensation_pass,
                'location_pass': location_pass,
                'detailed_reason': detailed_reason,
                'summary': f"{'SHORTLISTED' if overall_pass else 'REJECTED'}: {detailed_reason}"
            }
            
            logger.info(f"Evaluation result for {applicant_id}: {'PASS' if overall_pass else 'FAIL'}")
            return result
            
        except Exception as e:
            logger.error(f"Error evaluating applicant {applicant_id}: {e}")
            return {
                'applicant_id': applicant_id,
                'overall_pass': False,
                'detailed_reason': f"Evaluation error: {e}",
                'summary': f"REJECTED: Evaluation error"
            }

    def create_shortlisted_lead(self, applicant_id, applicant_data, evaluation_result):
        """Create a record in the Shortlisted Leads table"""
        try:
            # Check if already shortlisted
            existing_records = self.shortlisted_table.get_all(formula=f"{{Applicant}} = '{applicant_id}'")
            if existing_records:
                logger.info(f"Applicant {applicant_id} already in Shortlisted Leads table")
                return True
            
            # Get applicant record ID
            applicant_records = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not applicant_records:
                logger.error(f"No applicant record found for ID {applicant_id}")
                return False
            
            applicant_record_id = applicant_records[0]['id']
            
            # Prepare shortlisted lead data
            shortlisted_data = {
                'Applicant': [applicant_record_id],
                'Compressed JSON': json.dumps(applicant_data, indent=2),
                'Score Reason': evaluation_result['summary']
            }
            
            # Create the record
            self.shortlisted_table.insert(shortlisted_data)
            logger.info(f"Created shortlisted lead record for applicant {applicant_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error creating shortlisted lead for {applicant_id}: {e}")
            return False

    def update_applicant_status(self, applicant_id, status):
        """Update the shortlist status in the Applicants table"""
        try:
            applicant_records = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not applicant_records:
                logger.error(f"No applicant record found for ID {applicant_id}")
                return False
            
            record_id = applicant_records[0]['id']
            update_data = {'Shortlist Status': status}
            
            self.applicants_table.update(record_id, update_data)
            logger.info(f"Updated applicant {applicant_id} status to {status}")
            return True
            
        except Exception as e:
            logger.error(f"Error updating applicant status for {applicant_id}: {e}")
            return False

    def shortlist_single_applicant(self, applicant_id):
        """Shortlist a single applicant by ID"""
        try:
            logger.info(f"Processing shortlist evaluation for applicant {applicant_id}")
            
            # Get applicant data
            applicant_records = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not applicant_records:
                logger.error(f"No applicant found with ID {applicant_id}")
                return False
            
            # Get compressed JSON
            compressed_json = applicant_records[0]['fields'].get('Compressed JSON')
            if not compressed_json:
                logger.error(f"No compressed JSON found for applicant {applicant_id}")
                return False
            
            try:
                applicant_data = json.loads(compressed_json)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format for applicant {applicant_id}: {e}")
                return False
            
            # Evaluate against criteria
            evaluation = self.evaluate_applicant(applicant_id, applicant_data)
            
            if evaluation['overall_pass']:
                # Create shortlisted lead
                success = self.create_shortlisted_lead(applicant_id, applicant_data, evaluation)
                if success:
                    self.update_applicant_status(applicant_id, 'Shortlisted')
                return success
            else:
                # Mark as rejected
                self.update_applicant_status(applicant_id, 'Rejected')
                logger.info(f"Applicant {applicant_id} did not meet criteria: {evaluation['detailed_reason']}")
                return True  # Successfully processed, just not shortlisted
            
        except Exception as e:
            logger.error(f"Error in shortlist_single_applicant for {applicant_id}: {e}")
            return False

    def shortlist_all_applicants(self, force_reevaluate=False):
        """Process shortlisting for all applicants with compressed JSON"""
        try:
            logger.info("Starting shortlist evaluation for all applicants")
            
            # Get all applicants with compressed JSON
            applicants = self.applicants_table.get_all()
            
            if not applicants:
                logger.warning("No applicants found in the database")
                return []
            
            results = []
            processed = 0
            shortlisted = 0
            rejected = 0
            
            for applicant in applicants:
                fields = applicant['fields']
                applicant_id = fields.get('Applicant ID')
                compressed_json = fields.get('Compressed JSON')
                current_status = fields.get('Shortlist Status')
                
                if not applicant_id:
                    logger.warning(f"Skipping record with missing Applicant ID: {applicant['id']}")
                    continue
                
                if not compressed_json:
                    logger.info(f"Skipping {applicant_id} - no compressed JSON")
                    continue
                
                # Skip if already processed (unless forcing re-evaluation)
                if not force_reevaluate and current_status in ['Shortlisted', 'Rejected']:
                    logger.info(f"Skipping {applicant_id} - already processed ({current_status})")
                    continue
                
                try:
                    applicant_data = json.loads(compressed_json)
                except json.JSONDecodeError:
                    logger.error(f"Invalid JSON for applicant {applicant_id}")
                    continue
                
                # Evaluate applicant
                evaluation = self.evaluate_applicant(applicant_id, applicant_data)
                success = False
                
                if evaluation['overall_pass']:
                    success = self.create_shortlisted_lead(applicant_id, applicant_data, evaluation)
                    if success:
                        self.update_applicant_status(applicant_id, 'Shortlisted')
                        shortlisted += 1
                else:
                    self.update_applicant_status(applicant_id, 'Rejected')
                    rejected += 1
                    success = True  # Successfully processed
                
                results.append({
                    'applicant_id': applicant_id,
                    'success': success,
                    'shortlisted': evaluation['overall_pass'],
                    'evaluation': evaluation
                })
                
                processed += 1
            
            logger.info(f"Shortlisting completed: {processed} processed, {shortlisted} shortlisted, {rejected} rejected")
            return results
            
        except Exception as e:
            logger.error(f"Error in shortlist_all_applicants: {e}")
            return []

    def get_shortlisting_summary(self):
        """Get a summary of current shortlisting status"""
        try:
            # Get counts from Applicants table
            all_applicants = self.applicants_table.get_all()
            
            total_applicants = len(all_applicants)
            with_json = sum(1 for a in all_applicants if a['fields'].get('Compressed JSON'))
            pending = sum(1 for a in all_applicants if a['fields'].get('Shortlist Status') == 'Pending')
            shortlisted = sum(1 for a in all_applicants if a['fields'].get('Shortlist Status') == 'Shortlisted')
            rejected = sum(1 for a in all_applicants if a['fields'].get('Shortlist Status') == 'Rejected')
            unprocessed = sum(1 for a in all_applicants if not a['fields'].get('Shortlist Status'))
            
            # Get counts from Shortlisted Leads table
            shortlisted_leads = self.shortlisted_table.get_all()
            leads_count = len(shortlisted_leads)
            
            summary = {
                'total_applicants': total_applicants,
                'with_compressed_json': with_json,
                'pending_review': pending,
                'shortlisted': shortlisted,
                'rejected': rejected,
                'unprocessed': unprocessed,
                'shortlisted_leads_count': leads_count
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting shortlisting summary: {e}")
            return {}

def main():
    """Main function for command line usage"""
    import sys
    
    shortlister = Shortlister()
    
    if '--summary' in sys.argv:
        # Show summary
        summary = shortlister.get_shortlisting_summary()
        print("Shortlisting Summary:")
        print(f"  Total Applicants: {summary.get('total_applicants', 0)}")
        print(f"  With Compressed JSON: {summary.get('with_compressed_json', 0)}")
        print(f"  Pending Review: {summary.get('pending_review', 0)}")
        print(f"  Shortlisted: {summary.get('shortlisted', 0)}")
        print(f"  Rejected: {summary.get('rejected', 0)}")
        print(f"  Unprocessed: {summary.get('unprocessed', 0)}")
        print(f"  Shortlisted Leads: {summary.get('shortlisted_leads_count', 0)}")
        return
    
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        # Shortlist specific applicant
        applicant_id = sys.argv[1]
        success = shortlister.shortlist_single_applicant(applicant_id)
        if success:
            print(f"Successfully processed applicant {applicant_id}")
        else:
            print(f"Failed to process applicant {applicant_id}")
    else:
        # Shortlist all applicants
        force_reevaluate = '--force' in sys.argv
        results = shortlister.shortlist_all_applicants(force_reevaluate=force_reevaluate)
        
        successful = sum(1 for r in results if r['success'])
        shortlisted = sum(1 for r in results if r.get('shortlisted', False))
        rejected = len(results) - shortlisted
        
        print(f"Shortlisting completed:")
        print(f"  Processed: {successful}")
        print(f"  Shortlisted: {shortlisted}")
        print(f"  Rejected: {rejected}")
        
        if shortlisted > 0:
            shortlisted_ids = [r['applicant_id'] for r in results if r.get('shortlisted', False)]
            print(f"  Shortlisted applicants: {', '.join(shortlisted_ids)}")

if __name__ == "__main__":
    main()
