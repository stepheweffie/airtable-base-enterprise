#!/usr/bin/env python3
"""
Update OpenAI API Key Script

This script helps you update your OpenAI API key in the .env file.
"""

import os
import sys
from pathlib import Path

def update_openai_key(new_key):
    """Update the OpenAI API key in .env file"""
    env_file = Path('.env')
    
    if not env_file.exists():
        print("ERROR: .env file not found")
        return False
    
    # Read current content
    with open('.env', 'r') as f:
        lines = f.readlines()
    
    # Update the OpenAI key line
    updated_lines = []
    updated = False
    
    for line in lines:
        if line.startswith('OPENAI_API_KEY='):
            updated_lines.append(f'OPENAI_API_KEY={new_key}\n')
            updated = True
            print(f"SUCCESS: Updated OpenAI API key")
        else:
            updated_lines.append(line)
    
    if not updated:
        # Add the key if it doesn't exist
        updated_lines.append(f'OPENAI_API_KEY={new_key}\n')
        print("SUCCESS: Added OpenAI API key")
    
    # Write back to file
    with open('.env', 'w') as f:
        f.writelines(updated_lines)
    
    return True

def main():
    print("Update OpenAI API Key")
    print("=" * 30)
    
    if len(sys.argv) < 2:
        print("Usage: python update_openai_key.py <YOUR_OPENAI_API_KEY>")
        print("Example: python update_openai_key.py sk-your-actual-key-here")
        print()
        print("Or if you have it in environment variable:")
        print("python update_openai_key.py $OPENAI_API_KEY")
        return
    
    api_key = sys.argv[1]
    
    if not api_key.startswith('sk-'):
        print("WARNING: OpenAI API keys typically start with 'sk-'")
        confirm = input("Continue anyway? (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled")
            return
    
    if len(api_key) < 20:
        print("WARNING: OpenAI API keys are typically much longer")
        confirm = input("Continue anyway? (y/N): ")
        if confirm.lower() != 'y':
            print("Cancelled")
            return
    
    success = update_openai_key(api_key)
    
    if success:
        print("\nSUCCESS: OpenAI API key updated!")
        print("You can now run:")
        print("  python main.py pipeline")
        print("  python main.py evaluate")
    else:
        print("\nERROR: Failed to update API key")

if __name__ == "__main__":
    main()
