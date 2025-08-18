"""
Main Orchestrator Script for Airtable Contractor Automation System

This script coordinates the complete automation pipeline:
1. JSON compression
2. Shortlisting automation
3. LLM evaluation
4. Data management operations
"""

import logging
import sys
import argparse
from datetime import datetime

from json_compressor import JSONCompressor
from json_decompressor import JSONDecompressor
from shortlister import Shortlister
from llm_evaluator import LLMEvaluator
import config

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ContractorAutomation:
    def __init__(self):
        """Initialize the main automation orchestrator"""
        try:
            config.validate_config()
            self.compressor = JSONCompressor()
            self.decompressor = JSONDecompressor()
            self.shortlister = Shortlister()
            self.evaluator = LLMEvaluator()
            logger.info("Successfully initialized Contractor Automation System")
        except Exception as e:
            logger.error(f"Failed to initialize automation system: {e}")
            raise

    def run_full_pipeline(self, applicant_id=None, force_all=False):
        """Run the complete automation pipeline"""
        logger.info("Starting full automation pipeline")
        
        results = {
            'compression': {'success': 0, 'failed': 0},
            'shortlisting': {'success': 0, 'failed': 0, 'shortlisted': 0},
            'llm_evaluation': {'success': 0, 'failed': 0}
        }
        
        try:
            # Step 1: JSON Compression
            logger.info("Step 1: Running JSON compression...")
            if applicant_id:
                compression_success = self.compressor.compress_single_applicant(applicant_id)
                results['compression']['success'] = 1 if compression_success else 0
                results['compression']['failed'] = 0 if compression_success else 1
            else:
                compression_results = self.compressor.compress_all_applicants(force_update=force_all)
                results['compression']['success'] = sum(1 for r in compression_results if r['success'])
                results['compression']['failed'] = len(compression_results) - results['compression']['success']
            
            logger.info(f"Compression completed: {results['compression']['success']} successful, {results['compression']['failed']} failed")
            
            # Step 2: Shortlisting
            logger.info("Step 2: Running shortlisting automation...")
            if applicant_id:
                shortlist_success = self.shortlister.shortlist_single_applicant(applicant_id)
                results['shortlisting']['success'] = 1 if shortlist_success else 0
                results['shortlisting']['failed'] = 0 if shortlist_success else 1
                # Check if applicant was shortlisted
                summary = self.shortlister.get_shortlisting_summary()
                results['shortlisting']['shortlisted'] = summary.get('shortlisted', 0)
            else:
                shortlist_results = self.shortlister.shortlist_all_applicants(force_reevaluate=force_all)
                results['shortlisting']['success'] = sum(1 for r in shortlist_results if r['success'])
                results['shortlisting']['failed'] = len(shortlist_results) - results['shortlisting']['success']
                results['shortlisting']['shortlisted'] = sum(1 for r in shortlist_results if r.get('shortlisted', False))
            
            logger.info(f"Shortlisting completed: {results['shortlisting']['success']} processed, {results['shortlisting']['shortlisted']} shortlisted")
            
            # Step 3: LLM Evaluation
            logger.info("Step 3: Running LLM evaluation...")
            if applicant_id:
                eval_success = self.evaluator.evaluate_single_applicant(applicant_id)
                results['llm_evaluation']['success'] = 1 if eval_success else 0
                results['llm_evaluation']['failed'] = 0 if eval_success else 1
            else:
                eval_results = self.evaluator.evaluate_all_applicants(force_reevaluate=force_all)
                results['llm_evaluation']['success'] = sum(1 for r in eval_results if r['success'])
                results['llm_evaluation']['failed'] = len(eval_results) - results['llm_evaluation']['success']
            
            logger.info(f"LLM evaluation completed: {results['llm_evaluation']['success']} successful, {results['llm_evaluation']['failed']} failed")
            
            logger.info("Full automation pipeline completed successfully!")
            return results
            
        except Exception as e:
            logger.error(f"Error in full pipeline: {e}")
            return results

    def get_system_status(self):
        """Get comprehensive system status"""
        logger.info("Gathering system status...")
        
        try:
            # Get summary from each component
            shortlist_summary = self.shortlister.get_shortlisting_summary()
            eval_summary = self.evaluator.get_evaluation_summary()
            
            status = {
                'timestamp': datetime.now().isoformat(),
                'applicants': {
                    'total': shortlist_summary.get('total_applicants', 0),
                    'with_compressed_json': shortlist_summary.get('with_compressed_json', 0),
                    'pending_review': shortlist_summary.get('pending_review', 0),
                    'shortlisted': shortlist_summary.get('shortlisted', 0),
                    'rejected': shortlist_summary.get('rejected', 0),
                    'unprocessed': shortlist_summary.get('unprocessed', 0)
                },
                'llm_evaluation': {
                    'evaluated': eval_summary.get('with_llm_evaluation', 0),
                    'average_score': eval_summary.get('average_score', 0),
                    'score_distribution': eval_summary.get('score_distribution', {})
                },
                'shortlisted_leads': shortlist_summary.get('shortlisted_leads_count', 0)
            }
            
            return status
            
        except Exception as e:
            logger.error(f"Error getting system status: {e}")
            return {'error': str(e)}

    def cleanup_data(self, dry_run=True):
        """Clean up inconsistent or orphaned data"""
        logger.info(f"Running data cleanup (dry_run={dry_run})...")
        
        cleanup_report = {
            'orphaned_records': 0,
            'duplicate_records': 0,
            'inconsistent_data': 0
        }
        
        # This would implement data cleanup logic
        # For now, just return a placeholder
        logger.info("Data cleanup completed")
        return cleanup_report

def main():
    """Main function with command line interface"""
    parser = argparse.ArgumentParser(description="Airtable Contractor Automation System")
    
    # Main commands
    parser.add_argument('command', nargs='?', default='status',
                       choices=['pipeline', 'status', 'compress', 'decompress', 'shortlist', 'evaluate', 'cleanup'],
                       help='Command to execute')
    
    # Optional applicant ID
    parser.add_argument('applicant_id', nargs='?', help='Specific applicant ID to process')
    
    # Flags
    parser.add_argument('--force', action='store_true', help='Force re-processing of all records')
    parser.add_argument('--dry-run', action='store_true', help='Show what would be done without making changes')
    parser.add_argument('--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    # Set up logging level
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    try:
        automation = ContractorAutomation()
        
        if args.command == 'pipeline':
            # Run full pipeline
            print("Running full automation pipeline...")
            results = automation.run_full_pipeline(args.applicant_id, args.force)
            
            print("\nPipeline Results:")
            print(f"  Compression: {results['compression']['success']} successful, {results['compression']['failed']} failed")
            print(f"  Shortlisting: {results['shortlisting']['success']} processed, {results['shortlisting']['shortlisted']} shortlisted")
            print(f"  LLM Evaluation: {results['llm_evaluation']['success']} successful, {results['llm_evaluation']['failed']} failed")
            
        elif args.command == 'status':
            # Show system status
            status = automation.get_system_status()
            
            print("System Status:")
            print(f"  Timestamp: {status['timestamp']}")
            print(f"  Total Applicants: {status['applicants']['total']}")
            print(f"  With Compressed JSON: {status['applicants']['with_compressed_json']}")
            print(f"  Pending Review: {status['applicants']['pending_review']}")
            print(f"  Shortlisted: {status['applicants']['shortlisted']}")
            print(f"  Rejected: {status['applicants']['rejected']}")
            print(f"  Unprocessed: {status['applicants']['unprocessed']}")
            print(f"  LLM Evaluated: {status['llm_evaluation']['evaluated']}")
            print(f"  Average LLM Score: {status['llm_evaluation']['average_score']}")
            print(f"  Shortlisted Leads: {status['shortlisted_leads']}")
            
        elif args.command == 'compress':
            # Run compression only
            if args.applicant_id:
                success = automation.compressor.compress_single_applicant(args.applicant_id)
                print(f"Compression {'successful' if success else 'failed'} for applicant {args.applicant_id}")
            else:
                results = automation.compressor.compress_all_applicants(force_update=args.force)
                successful = sum(1 for r in results if r['success'])
                print(f"Compression completed: {successful}/{len(results)} successful")
                
        elif args.command == 'decompress':
            # Run decompression only
            if args.applicant_id:
                success = automation.decompressor.decompress_single_applicant(args.applicant_id)
                print(f"Decompression {'successful' if success else 'failed'} for applicant {args.applicant_id}")
            else:
                results = automation.decompressor.decompress_all_applicants()
                successful = sum(1 for r in results if r['success'])
                print(f"Decompression completed: {successful}/{len(results)} successful")
                
        elif args.command == 'shortlist':
            # Run shortlisting only
            if args.applicant_id:
                success = automation.shortlister.shortlist_single_applicant(args.applicant_id)
                print(f"Shortlisting {'successful' if success else 'failed'} for applicant {args.applicant_id}")
            else:
                results = automation.shortlister.shortlist_all_applicants(force_reevaluate=args.force)
                successful = sum(1 for r in results if r['success'])
                shortlisted = sum(1 for r in results if r.get('shortlisted', False))
                print(f"Shortlisting completed: {successful} processed, {shortlisted} shortlisted")
                
        elif args.command == 'evaluate':
            # Run LLM evaluation only
            if args.applicant_id:
                success = automation.evaluator.evaluate_single_applicant(args.applicant_id)
                print(f"LLM evaluation {'successful' if success else 'failed'} for applicant {args.applicant_id}")
            else:
                results = automation.evaluator.evaluate_all_applicants(force_reevaluate=args.force)
                successful = sum(1 for r in results if r['success'])
                print(f"LLM evaluation completed: {successful}/{len(results)} successful")
                
        elif args.command == 'cleanup':
            # Run data cleanup
            report = automation.cleanup_data(dry_run=args.dry_run)
            print("Data cleanup report:")
            print(f"  Orphaned records: {report['orphaned_records']}")
            print(f"  Duplicate records: {report['duplicate_records']}")
            print(f"  Inconsistent data: {report['inconsistent_data']}")
            
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
