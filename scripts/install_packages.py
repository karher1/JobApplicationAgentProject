#!/usr/bin/env python3
"""
Package Installation Script for Job Application Agent
Installs packages in logical batches with error handling
"""

import subprocess
import sys
import os
from pathlib import Path

def run_command(command, description):
    """Run a command and handle errors"""
    print(f"\n{'='*50}")
    print(f"Installing: {description}")
    print(f"Command: {command}")
    print(f"{'='*50}")
    
    try:
        result = subprocess.run(command, shell=True, check=True, 
                              capture_output=True, text=True)
        print(f"✅ Successfully installed: {description}")
        if result.stdout:
            print("Output:", result.stdout)
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ Error installing {description}:")
        print(f"Error code: {e.returncode}")
        if e.stdout:
            print("Stdout:", e.stdout)
        if e.stderr:
            print("Stderr:", e.stderr)
        return False

def check_venv():
    """Check if virtual environment is activated"""
    if not hasattr(sys, 'real_prefix') and not (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix):
        print("⚠️  Warning: Virtual environment doesn't appear to be activated.")
        print("   It's recommended to activate your virtual environment first.")
        response = input("   Continue anyway? (y/n): ")
        if response.lower() != 'y':
            print("Installation cancelled.")
            sys.exit(1)

def main():
    print("🚀 Job Application Agent - Package Installation")
    print("This script will install packages in logical batches")
    
    # Check if virtual environment is activated
    check_venv()
    
    # Define installation batches
    batches = [
        ("requirements_core.txt", "Core Dependencies"),
        ("requirements_langchain.txt", "LangChain & AI Dependencies"),
        ("requirements_selenium.txt", "Selenium & Web Automation"),
        ("requirements_database.txt", "Database & Supabase Dependencies")
    ]
    
    failed_batches = []
    
    for requirements_file, description in batches:
        if not Path(requirements_file).exists():
            print(f"⚠️  Warning: {requirements_file} not found, skipping...")
            continue
            
        success = run_command(f"pip install -r {requirements_file}", description)
        if not success:
            failed_batches.append(description)
    
    # Summary
    print(f"\n{'='*50}")
    print("📋 INSTALLATION SUMMARY")
    print(f"{'='*50}")
    
    if failed_batches:
        print(f"❌ Failed batches: {', '.join(failed_batches)}")
        print("\nTo retry failed installations:")
        for batch in failed_batches:
            print(f"   pip install -r requirements_{batch.lower().replace(' ', '_').replace('&', 'and')}.txt")
    else:
        print("✅ All packages installed successfully!")
    
    print(f"\n🎉 Installation complete!")
    print("You can now run your job application automation script.")

if __name__ == "__main__":
    main() 