"""
LLM Evaluation System for Airtable Contractor Automation

This script uses OpenAI's API to evaluate, enrich, and sanity-check each application.
It provides summaries, quality scores, and follow-up questions based on compressed JSON data.
"""

import json
import logging
import time
import hashlib
from datetime import datetime
from airtable import Airtable
import openai
import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class LLMEvaluator:
    def __init__(self):
        """Initialize the LLM Evaluator with API connections"""
        try:
            config.validate_config()
            self.applicants_table = Airtable(config.AIRTABLE_BASE_ID, config.TABLES['APPLICANTS'], api_key=config.AIRTABLE_API_KEY)
            
            # Initialize OpenAI client
            openai.api_key = config.OPENAI_API_KEY
            self.model = config.LLM_MODEL
            self.max_tokens = config.MAX_TOKENS_PER_REQUEST
            
            logger.info("Successfully initialized LLM Evaluator")
        except Exception as e:
            logger.error(f"Failed to initialize LLM Evaluator: {e}")
            raise

    def generate_content_hash(self, compressed_json):
        """Generate a hash of the compressed JSON to detect changes"""
        if not compressed_json:
            return None
        return hashlib.md5(compressed_json.encode()).hexdigest()

    def build_evaluation_prompt(self, applicant_data):
        """Build the prompt for LLM evaluation"""
        
        # Extract key information for the prompt
        personal = applicant_data.get('personal', {})
        experiences = applicant_data.get('experience', [])
        salary = applicant_data.get('salary', {})
        metadata = applicant_data.get('metadata', {})
        
        # Build experience summary
        exp_summary = []
        for exp in experiences:
            company = exp.get('company', 'Unknown Company')
            title = exp.get('title', 'Unknown Title')
            years = exp.get('years_experience', 0)
            exp_summary.append(f"- {title} at {company} ({years} years)")
        
        experience_text = '\n'.join(exp_summary) if exp_summary else "No experience listed"
        
        prompt = f"""You are a recruiting analyst. Given this JSON applicant profile, do four things:

APPLICANT PROFILE:
Name: {personal.get('name', 'Not provided')}
Location: {personal.get('location', 'Not provided')}
Email: {personal.get('email', 'Not provided')}

WORK EXPERIENCE:
{experience_text}
Total Experience: {metadata.get('total_experience_years', 0)} years
Has Tier-1 Company: {metadata.get('has_tier1_company', False)}

COMPENSATION:
Preferred Rate: ${salary.get('preferred_rate', 0)}/hr {salary.get('currency', 'USD')}
Availability: {salary.get('availability', 0)} hours/week

TASKS:
1. Provide a concise 75-word summary highlighting key strengths and experience.
2. Rate overall candidate quality from 1-10 (higher is better) based on experience, skills, and market fit.
3. List any data gaps or inconsistencies you notice.
4. Suggest up to three follow-up questions to clarify gaps or assess fit.

Return exactly in this format:
Summary: [your 75-word summary]
Score: [integer 1-10]
Issues: [comma-separated list or 'None']
Follow-Ups: [bullet list with • prefix, or 'None']"""

        return prompt

    def call_llm_with_retry(self, prompt, max_retries=3):
        """Call LLM API with exponential backoff retry logic"""
        for attempt in range(max_retries):
            try:
                logger.info(f"Calling LLM API (attempt {attempt + 1}/{max_retries})")
                
                response = openai.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": "You are an expert recruiting analyst. Provide clear, concise, and actionable feedback on candidate profiles."},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=self.max_tokens,
                    temperature=0.3,  # Lower temperature for more consistent output
                    timeout=30  # 30 second timeout
                )
                
                content = response.choices[0].message.content.strip()
                
                # Basic validation that we got a structured response
                if "Summary:" in content and "Score:" in content:
                    logger.info("Successfully received LLM response")
                    return content, None
                else:
                    logger.warning("LLM response missing required sections")
                    return None, "Response format invalid"
                
            except openai.RateLimitError as e:
                wait_time = (2 ** attempt) * 1  # Exponential backoff: 1, 2, 4 seconds
                logger.warning(f"Rate limit hit, waiting {wait_time} seconds before retry")
                time.sleep(wait_time)
                continue
                
            except openai.APITimeoutError as e:
                wait_time = (2 ** attempt) * 2  # 2, 4, 8 seconds
                logger.warning(f"API timeout, waiting {wait_time} seconds before retry")
                time.sleep(wait_time)
                continue
                
            except openai.APIError as e:
                logger.error(f"OpenAI API error: {e}")
                if attempt == max_retries - 1:
                    return None, f"API error after {max_retries} attempts: {e}"
                time.sleep(2 ** attempt)
                continue
                
            except Exception as e:
                logger.error(f"Unexpected error calling LLM: {e}")
                if attempt == max_retries - 1:
                    return None, f"Unexpected error after {max_retries} attempts: {e}"
                time.sleep(2 ** attempt)
                continue
        
        return None, f"Failed after {max_retries} attempts"

    def parse_llm_response(self, response_text):
        """Parse the structured LLM response into components"""
        try:
            lines = response_text.strip().split('\n')
            
            summary = ""
            score = 0
            issues = "None"
            follow_ups = "None"
            
            current_section = None
            follow_up_lines = []
            
            for line in lines:
                line = line.strip()
                if not line:
                    continue
                
                if line.startswith("Summary:"):
                    summary = line.replace("Summary:", "").strip()
                    current_section = "summary"
                elif line.startswith("Score:"):
                    score_text = line.replace("Score:", "").strip()
                    try:
                        score = int(score_text)
                        if score < 1 or score > 10:
                            logger.warning(f"Score {score} out of range, clamping to 1-10")
                            score = max(1, min(10, score))
                    except ValueError:
                        logger.warning(f"Invalid score format: {score_text}, defaulting to 5")
                        score = 5
                    current_section = "score"
                elif line.startswith("Issues:"):
                    issues = line.replace("Issues:", "").strip()
                    current_section = "issues"
                elif line.startswith("Follow-Ups:"):
                    follow_ups_text = line.replace("Follow-Ups:", "").strip()
                    if follow_ups_text and follow_ups_text != "None":
                        follow_up_lines = [follow_ups_text]
                    current_section = "follow_ups"
                elif current_section == "follow_ups" and line.startswith("•"):
                    follow_up_lines.append(line)
                elif current_section == "summary" and not any(line.startswith(prefix) for prefix in ["Score:", "Issues:", "Follow-Ups:"]):
                    # Multi-line summary
                    summary += " " + line
            
            # Join follow-up lines
            if follow_up_lines:
                follow_ups = '\n'.join(follow_up_lines)
            
            # Validate summary length (approximately 75 words)
            word_count = len(summary.split())
            if word_count > 100:
                logger.warning(f"Summary is {word_count} words, may be too long")
            
            return {
                'summary': summary,
                'score': score,
                'issues': issues,
                'follow_ups': follow_ups
            }
            
        except Exception as e:
            logger.error(f"Error parsing LLM response: {e}")
            return {
                'summary': "Error parsing LLM response",
                'score': 5,
                'issues': "Response parsing failed",
                'follow_ups': "None"
            }

    def evaluate_single_applicant(self, applicant_id):
        """Evaluate a single applicant using LLM"""
        try:
            logger.info(f"Starting LLM evaluation for applicant {applicant_id}")
            
            # Get applicant data
            applicant_records = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not applicant_records:
                logger.error(f"No applicant found with ID {applicant_id}")
                return False
            
            record = applicant_records[0]
            fields = record['fields']
            compressed_json = fields.get('Compressed JSON')
            
            if not compressed_json:
                logger.error(f"No compressed JSON found for applicant {applicant_id}")
                return False
            
            # Check if content has changed (skip if unchanged)
            current_hash = self.generate_content_hash(compressed_json)
            stored_hash = fields.get('LLM Content Hash')
            
            if current_hash == stored_hash and fields.get('LLM Summary'):
                logger.info(f"Skipping {applicant_id} - content unchanged since last evaluation")
                return True
            
            try:
                applicant_data = json.loads(compressed_json)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid JSON format for applicant {applicant_id}: {e}")
                return False
            
            # Build prompt and call LLM
            prompt = self.build_evaluation_prompt(applicant_data)
            llm_response, error = self.call_llm_with_retry(prompt)
            
            if error:
                logger.error(f"LLM evaluation failed for {applicant_id}: {error}")
                # Update record with error info
                error_data = {
                    'LLM Summary': f"Evaluation failed: {error}",
                    'LLM Score': 0,
                    'LLM Follow-Ups': "LLM evaluation error - please review manually"
                }
                self.applicants_table.update(record['id'], error_data)
                return False
            
            # Parse LLM response
            parsed = self.parse_llm_response(llm_response)
            
            # Update Airtable record
            update_data = {
                'LLM Summary': parsed['summary'],
                'LLM Score': parsed['score'],
                'LLM Follow-Ups': parsed['follow_ups'],
                'LLM Content Hash': current_hash  # Store hash to detect future changes
            }
            
            # Add issues to summary if they exist
            if parsed['issues'] and parsed['issues'] != "None":
                update_data['LLM Summary'] += f" Issues noted: {parsed['issues']}"
            
            self.applicants_table.update(record['id'], update_data)
            
            logger.info(f"Successfully evaluated applicant {applicant_id} (Score: {parsed['score']})")
            return True
            
        except Exception as e:
            logger.error(f"Error evaluating applicant {applicant_id}: {e}")
            return False

    def evaluate_all_applicants(self, force_reevaluate=False):
        """Evaluate all applicants with compressed JSON"""
        try:
            logger.info("Starting LLM evaluation for all applicants")
            
            # Get all applicants with compressed JSON
            applicants = self.applicants_table.get_all()
            
            if not applicants:
                logger.warning("No applicants found in the database")
                return []
            
            results = []
            processed = 0
            successful = 0
            failed = 0
            skipped = 0
            
            for applicant in applicants:
                fields = applicant['fields']
                applicant_id = fields.get('Applicant ID')
                compressed_json = fields.get('Compressed JSON')
                
                if not applicant_id:
                    logger.warning(f"Skipping record with missing Applicant ID: {applicant['id']}")
                    continue
                
                if not compressed_json:
                    logger.info(f"Skipping {applicant_id} - no compressed JSON")
                    skipped += 1
                    continue
                
                # Check if already evaluated (unless forcing re-evaluation)
                if not force_reevaluate:
                    current_hash = self.generate_content_hash(compressed_json)
                    stored_hash = fields.get('LLM Content Hash')
                    has_summary = fields.get('LLM Summary')
                    
                    if current_hash == stored_hash and has_summary:
                        logger.info(f"Skipping {applicant_id} - already evaluated")
                        skipped += 1
                        continue
                
                # Evaluate applicant
                success = self.evaluate_single_applicant(applicant_id)
                
                results.append({
                    'applicant_id': applicant_id,
                    'success': success
                })
                
                if success:
                    successful += 1
                else:
                    failed += 1
                
                processed += 1
                
                # Add small delay to avoid hitting rate limits
                time.sleep(0.5)
            
            logger.info(f"LLM evaluation completed: {processed} processed, {successful} successful, {failed} failed, {skipped} skipped")
            return results
            
        except Exception as e:
            logger.error(f"Error in evaluate_all_applicants: {e}")
            return []

    def get_evaluation_summary(self):
        """Get a summary of LLM evaluation status"""
        try:
            all_applicants = self.applicants_table.get_all()
            
            total_applicants = len(all_applicants)
            with_json = sum(1 for a in all_applicants if a['fields'].get('Compressed JSON'))
            with_llm_summary = sum(1 for a in all_applicants if a['fields'].get('LLM Summary'))
            
            # Score distribution
            scores = [a['fields'].get('LLM Score', 0) for a in all_applicants if a['fields'].get('LLM Score')]
            score_dist = {}
            for score in scores:
                score_dist[score] = score_dist.get(score, 0) + 1
            
            avg_score = sum(scores) / len(scores) if scores else 0
            
            summary = {
                'total_applicants': total_applicants,
                'with_compressed_json': with_json,
                'with_llm_evaluation': with_llm_summary,
                'average_score': round(avg_score, 1),
                'score_distribution': score_dist
            }
            
            return summary
            
        except Exception as e:
            logger.error(f"Error getting evaluation summary: {e}")
            return {}

    def regenerate_evaluation(self, applicant_id):
        """Force regenerate LLM evaluation for a specific applicant"""
        try:
            # Clear existing LLM data
            applicant_records = self.applicants_table.get_all(formula=f"{{Applicant ID}} = '{applicant_id}'")
            if not applicant_records:
                logger.error(f"No applicant found with ID {applicant_id}")
                return False
            
            record_id = applicant_records[0]['id']
            
            # Clear LLM fields to force re-evaluation
            clear_data = {
                'LLM Content Hash': '',
                'LLM Summary': '',
                'LLM Score': 0,
                'LLM Follow-Ups': ''
            }
            
            self.applicants_table.update(record_id, clear_data)
            
            # Now evaluate
            return self.evaluate_single_applicant(applicant_id)
            
        except Exception as e:
            logger.error(f"Error regenerating evaluation for {applicant_id}: {e}")
            return False

def main():
    """Main function for command line usage"""
    import sys
    
    evaluator = LLMEvaluator()
    
    if '--summary' in sys.argv:
        # Show evaluation summary
        summary = evaluator.get_evaluation_summary()
        print("LLM Evaluation Summary:")
        print(f"  Total Applicants: {summary.get('total_applicants', 0)}")
        print(f"  With Compressed JSON: {summary.get('with_compressed_json', 0)}")
        print(f"  With LLM Evaluation: {summary.get('with_llm_evaluation', 0)}")
        print(f"  Average Score: {summary.get('average_score', 0)}")
        
        score_dist = summary.get('score_distribution', {})
        if score_dist:
            print("  Score Distribution:")
            for score in sorted(score_dist.keys()):
                print(f"    {score}/10: {score_dist[score]} applicants")
        return
    
    if len(sys.argv) > 1 and not sys.argv[1].startswith('--'):
        applicant_id = sys.argv[1]
        
        if '--regenerate' in sys.argv:
            # Force regenerate evaluation
            success = evaluator.regenerate_evaluation(applicant_id)
            if success:
                print(f"Successfully regenerated evaluation for applicant {applicant_id}")
            else:
                print(f"Failed to regenerate evaluation for applicant {applicant_id}")
        else:
            # Evaluate specific applicant
            success = evaluator.evaluate_single_applicant(applicant_id)
            if success:
                print(f"Successfully evaluated applicant {applicant_id}")
            else:
                print(f"Failed to evaluate applicant {applicant_id}")
    else:
        # Evaluate all applicants
        force_reevaluate = '--force' in sys.argv
        results = evaluator.evaluate_all_applicants(force_reevaluate=force_reevaluate)
        
        successful = sum(1 for r in results if r['success'])
        failed = len(results) - successful
        
        print(f"LLM evaluation completed:")
        print(f"  Successful: {successful}")
        print(f"  Failed: {failed}")
        
        if failed > 0:
            failed_ids = [r['applicant_id'] for r in results if not r['success']]
            print(f"  Failed applicants: {', '.join(failed_ids)}")

if __name__ == "__main__":
    main()
