#!/usr/bin/env python3
"""
Fix 404 Errors - Troubleshooting Script for Airtable Integration

This script helps identify and resolve the 404 errors in the Airtable integration.
The main issue is an incorrectly formatted base ID.

Run this script to:
1. Identify the current configuration issues
2. Test API connectivity 
3. Guide you through fixing the base ID
4. Verify the fix works
"""

import os
import sys
import requests
import json
from pathlib import Path

def check_env_file():
    """Check if .env file exists and has required variables"""
    env_file = Path('.env')
    if not env_file.exists():
        print("ERROR: .env file not found")
        return False, {}
    
    env_vars = {}
    with open('.env', 'r') as f:
        for line in f:
            line = line.strip()
            if line and not line.startswith('#') and '=' in line:
                key, value = line.split('=', 1)
                env_vars[key] = value.strip('"\'')
    
    return True, env_vars

def validate_base_id_format(base_id):
    """Validate Airtable base ID format"""
    if not base_id:
        return False, "Base ID is empty"
    
    if base_id == "REPLACE_WITH_CORRECT_BASE_ID":
        return False, "Base ID is still a placeholder"
    
    if not base_id.startswith('app'):
        return False, f"Base ID should start with 'app', but starts with '{base_id[:3]}'"
    
    if len(base_id) != 17:
        return False, f"Base ID should be 17 characters, but is {len(base_id)} characters"
    
    return True, "Base ID format is correct"

def test_airtable_api(api_key, base_id):
    """Test Airtable API connectivity"""
    if not api_key or api_key == "YOUR_AIRTABLE_API_KEY_HERE":
        return False, "API key is missing or placeholder"
    
    if not base_id or base_id == "REPLACE_WITH_CORRECT_BASE_ID":
        return False, "Base ID is missing or placeholder"
    
    # Test with a simple API call
    url = f"https://api.airtable.com/v0/{base_id}/Applicants?maxRecords=1"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            return True, "API connection successful!"
        elif response.status_code == 404:
            try:
                error_data = response.json()
                if error_data.get('error') == 'NOT_FOUND':
                    return False, f"Base or table not found. Check base ID: {base_id}"
            except:
                pass
            return False, f"404 Not Found - Base ID '{base_id}' doesn't exist or table 'Applicants' doesn't exist"
        elif response.status_code == 401:
            return False, "Authentication failed - check your API key"
        elif response.status_code == 403:
            return False, "Permission denied - API key may not have access to this base"
        else:
            return False, f"API error: {response.status_code} - {response.text}"
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {e}"

def get_base_info(api_key):
    """Try to get list of available bases"""
    url = "https://api.airtable.com/v0/meta/bases"
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    try:
        response = requests.get(url, headers=headers)
        if response.status_code == 200:
            bases = response.json().get('bases', [])
            return True, bases
        else:
            return False, f"Could not retrieve bases: {response.status_code}"
    except requests.exceptions.RequestException as e:
        return False, f"Network error: {e}"

def main():
    print("Airtable 404 Error Troubleshooting Tool")
    print("=" * 50)
    
    # Step 1: Check environment file
    print("\n1. Checking .env file...")
    env_exists, env_vars = check_env_file()
    
    if not env_exists:
        print("ERROR: .env file not found. Please create one based on .env.example")
        return
    
    api_key = env_vars.get('AIRTABLE_API_KEY')
    base_id = env_vars.get('AIRTABLE_BASE_ID')
    
    print(f"SUCCESS: Found .env file")
    print(f"   API Key: {api_key[:10] if api_key else 'None'}...")
    print(f"   Base ID: {base_id}")
    
    # Step 2: Validate base ID format
    print("\n2. Validating base ID format...")
    base_id_valid, base_id_message = validate_base_id_format(base_id)
    
    if base_id_valid:
        print(f"SUCCESS: {base_id_message}")
    else:
        print(f"ERROR: {base_id_message}")
        print("\nBase ID Issues Found:")
        print("   - Airtable base IDs must start with 'app' followed by 14 characters")
        print("   - Total length should be 17 characters")
        print("   - Example: app1234567890ABC")
        
        if base_id.startswith('pat'):
            print("\nCurrent Issue:")
            print("   Your base ID looks like a Personal Access Token (PAT) prefix.")
            print("   You need to get the actual base ID from your Airtable base.")
    
    # Step 3: Try to get available bases
    print("\n3. Checking available bases...")
    if api_key and api_key != "YOUR_AIRTABLE_API_KEY_HERE":
        success, bases = get_base_info(api_key)
        if success:
            print(f"SUCCESS: Found {len(bases)} available bases:")
            for base in bases:
                base_id = base.get('id')
                base_name = base.get('name')
                print(f"   - {base_name}: {base_id}")
            
            if bases:
                print(f"\nUse one of these base IDs in your .env file:")
                for base in bases:
                    print(f"   AIRTABLE_BASE_ID={base.get('id')}")
        else:
            print(f"ERROR: {bases}")
    else:
        print("WARNING: Skipping (API key missing or placeholder)")
    
    # Step 4: Test API connectivity
    print("\n4. Testing Airtable API connectivity...")
    if api_key and base_id and base_id_valid:
        success, message = test_airtable_api(api_key, base_id)
        if success:
            print(f"SUCCESS: {message}")
        else:
            print(f"ERROR: {message}")
    else:
        print("WARNING: Skipping (configuration issues found above)")
    
    # Step 5: Provide next steps
    print("\n5. Next Steps:")
    
    if not base_id_valid:
        print("   1. Create an Airtable base following the schema in AIRTABLE_SCHEMA.md")
        print("   2. Get the correct base ID from your Airtable base")
        print("      - Go to https://airtable.com/api")
        print("      - Select your base")
        print("      - Copy the base ID from the URL or documentation")
        print("   3. Update AIRTABLE_BASE_ID in .env file")
        print("   4. Run this script again to verify")
        print("   5. Test with: python main.py status")
    else:
        print("   SUCCESS: Configuration looks good!")
        print("   - Try running: python main.py status")
        print("   - If you still get errors, check that your Airtable base has the 'Applicants' table")
    
    print("\nDocumentation:")
    print("   - See AIRTABLE_SCHEMA.md for complete setup instructions")
    print("   - See README.md for usage guide")

if __name__ == "__main__":
    main()
