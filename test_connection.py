#!/usr/bin/env python3
"""
Connection Test Script for Mercor Airtable Automation

This script tests your Airtable and OpenAI connections without making any changes to your data.
"""

import os
import sys
from datetime import datetime

def test_config():
    """Test basic configuration"""
    print("Testing Configuration...")
    try:
        import config
        config.validate_config()
        print("SUCCESS: Configuration validation passed")
        return True
    except Exception as e:
        print(f"ERROR: Configuration error: {e}")
        return False

def test_airtable_connection():
    """Test Airtable connection"""
    print("\nTesting Airtable Connection...")
    try:
        from airtable import Airtable
        import config
        
        # Test connection to Applicants table
        applicants_table = Airtable(config.AIRTABLE_BASE_ID, 'Applicants', api_key=config.AIRTABLE_API_KEY)
        
        # Try to get records (limit to 1 to minimize API usage)
        records = applicants_table.get_all(maxRecords=1)
        print(f"SUCCESS: Successfully connected to Airtable")
        print(f"SUCCESS: Base ID: {config.AIRTABLE_BASE_ID}")
        print(f"SUCCESS: Found {len(records)} records in Applicants table")
        
        # Test other tables
        tables_to_check = ['Personal Details', 'Work Experience', 'Salary Preferences', 'Shortlisted Leads']
        for table_name in tables_to_check:
            try:
                table = Airtable(config.AIRTABLE_BASE_ID, table_name, api_key=config.AIRTABLE_API_KEY)
                records = table.get_all(maxRecords=1)
                print(f"SUCCESS: {table_name}: {len(records)} records")
            except Exception as e:
                print(f"ERROR: {table_name}: {str(e)}")
        
        return True
    except Exception as e:
        print(f"ERROR: Airtable connection failed: {e}")
        print("\nPossible issues:")
        print("   - Check your AIRTABLE_API_KEY is correct")
        print("   - Check your AIRTABLE_BASE_ID is correct")
        print("   - Ensure your Airtable base has the required tables")
        print("   - Verify API permissions")
        return False

def test_openai_connection():
    """Test OpenAI connection"""
    print("\nTesting OpenAI Connection...")
    try:
        import config
        if not config.OPENAI_API_KEY or config.OPENAI_API_KEY.startswith('sk-EXAMPLE'):
            print("WARNING: OpenAI API key not configured (this is optional)")
            print("   Set OPENAI_API_KEY in .env file to enable LLM evaluation")
            return True
        
        import openai
        openai.api_key = config.OPENAI_API_KEY
        
        # Test with a simple API call
        response = openai.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[{"role": "user", "content": "Hello, this is a connection test. Please respond with just 'OK'."}],
            max_tokens=5
        )
        
        print("SUCCESS: OpenAI connection successful")
        print(f"SUCCESS: Model: {config.LLM_MODEL}")
        print(f"SUCCESS: Max tokens: {config.MAX_TOKENS_PER_REQUEST}")
        return True
    except Exception as e:
        print(f"ERROR: OpenAI connection failed: {e}")
        print("\nPossible issues:")
        print("   - Check your OPENAI_API_KEY is correct")
        print("   - Ensure you have OpenAI API credits")
        print("   - Verify internet connection")
        return False

def test_system_integration():
    """Test basic system integration"""
    print("\nTesting System Integration...")
    try:
        # Test JSON Compressor initialization
        from json_compressor import JSONCompressor
        compressor = JSONCompressor()
        print("SUCCESS: JSON Compressor initialized")
        
        # Test Shortlister initialization
        from shortlister import Shortlister
        shortlister = Shortlister()
        print("SUCCESS: Shortlister initialized")
        
        # Test LLM Evaluator initialization  
        from llm_evaluator import LLMEvaluator
        evaluator = LLMEvaluator()
        print("SUCCESS: LLM Evaluator initialized")
        
        # Test Main Automation initialization
        from main import MercorAutomation
        automation = MercorAutomation()
        print("SUCCESS: Main Automation initialized")
        
        return True
    except Exception as e:
        print(f"ERROR: System integration failed: {e}")
        return False

def main():
    print("Mercor Airtable Automation - Connection Test")
    print("=" * 50)
    print(f"Test started: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests_passed = 0
    total_tests = 4
    
    # Run all tests
    if test_config():
        tests_passed += 1
    
    if test_airtable_connection():
        tests_passed += 1
    
    if test_openai_connection():
        tests_passed += 1
    
    if test_system_integration():
        tests_passed += 1
    
    # Summary
    print(f"\nTest Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("SUCCESS: All tests passed! Your system is ready to use.")
        print("\nNext steps:")
        print("1. Run system status: python main.py status")
        print("2. Run the pipeline: python main.py pipeline")
    elif tests_passed >= 2:  # Config and Airtable are essential
        print("WARNING: Basic functionality available, but some features may be limited")
        print("Fix the failed tests for full functionality")
    else:
        print("ERROR: Critical issues found. Please fix configuration before proceeding")
    
    print(f"\nTest completed: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

if __name__ == "__main__":
    main()
