#!/usr/bin/env python3
"""
Environment Setup Helper for Mercor Airtable Automation

This script helps you configure your environment variables for the system.
"""

import os
import sys
from pathlib import Path

def update_env_file(base_id, openai_key=None):
    """Update the .env file with the provided credentials"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("ERROR: .env file not found. Creating from template...")
        env_template = """# Airtable Configuration
AIRTABLE_API_KEY="{airtable_key}"
AIRTABLE_BASE_ID={base_id}

# OpenAI Configuration  
OPENAI_API_KEY={openai_key}

# Optional Settings
MAX_TOKENS_PER_REQUEST=1500
LLM_MODEL=gpt-3.5-turbo
"""
        with open('.env', 'w') as f:
            f.write(env_template.format(
                airtable_key="YOUR_AIRTABLE_API_KEY_HERE",
                base_id=base_id,
                openai_key=openai_key or "YOUR_OPENAI_API_KEY_HERE"
            ))
        print("SUCCESS: Created .env file template")
        return

    # Read existing .env file
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    # Update the lines
    updated_lines = []
    for line in lines:
        if line.startswith('AIRTABLE_BASE_ID='):
            updated_lines.append(f'AIRTABLE_BASE_ID={base_id}\n')
            print(f"SUCCESS: Updated AIRTABLE_BASE_ID to: {base_id}")
        elif line.startswith('OPENAI_API_KEY=') and openai_key:
            updated_lines.append(f'OPENAI_API_KEY={openai_key}\n')
            print(f"SUCCESS: Updated OPENAI_API_KEY")
        else:
            updated_lines.append(line)
    
    # Write back to file
    with open('.env', 'w') as f:
        f.writelines(updated_lines)
    
    print("SUCCESS: Environment file updated successfully!")

def test_configuration():
    """Test the configuration to make sure it works"""
    print("\nTesting configuration...")
    
    try:
        import config
        config.validate_config()
        print("SUCCESS: Configuration validation passed!")
        
        # Test Airtable connection (without making actual API calls)
        print(f"SUCCESS: Airtable API Key: {config.AIRTABLE_API_KEY[:10]}...")
        print(f"SUCCESS: Airtable Base ID: {config.AIRTABLE_BASE_ID}")
        print(f"SUCCESS: OpenAI API Key: {config.OPENAI_API_KEY[:10] if config.OPENAI_API_KEY else 'Not set'}...")
        
        return True
    except Exception as e:
        print(f"ERROR: Configuration error: {e}")
        return False

def main():
    print("Mercor Airtable Automation - Environment Setup")
    print("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage: python setup_env.py <BASE_ID> [OPENAI_KEY]")
        print("\nExample:")
        print("  python setup_env.py appXXXXXXXXXXXXXX")
        print("  python setup_env.py appXXXXXXXXXXXXXX sk-XXXXXXXXXXXXXXXX")
        sys.exit(1)
    
    base_id = sys.argv[1]
    openai_key = sys.argv[2] if len(sys.argv) > 2 else None
    
    print(f"Setting up environment with:")
    print(f"   Base ID: {base_id}")
    print(f"   OpenAI Key: {'Provided' if openai_key else 'Not provided (will use existing or leave empty)'}")
    
    # Validate base ID format
    if not base_id.startswith('app') or len(base_id) != 17:
        print("WARNING: Base ID doesn't match expected format (should be 'app' + 14 characters)")
        confirm = input("Continue anyway? (y/N): ")
        if confirm.lower() != 'y':
            print("ERROR: Setup cancelled")
            sys.exit(1)
    
    # Update environment file
    update_env_file(base_id, openai_key)
    
    # Test configuration
    if test_configuration():
        print("\nSUCCESS: Setup completed successfully!")
        print("\nNext steps:")
        print("1. Verify your Airtable base has the required tables (see AIRTABLE_SCHEMA.md)")
        print("2. Test the system: python main.py status")
        print("3. Run the pipeline: python main.py pipeline")
    else:
        print("\nERROR: Setup completed but configuration test failed")
        print("Please check your API keys and try again")

if __name__ == "__main__":
    main()
