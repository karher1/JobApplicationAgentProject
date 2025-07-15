#!/usr/bin/env python3
"""
Example Usage Script for Job Application Automation with LangChain Framework

This script demonstrates how to use the LangChain-based job application automation system.
"""

import sys
import os
from typing import List

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def demonstrate_basic_automation():
    """Demonstrate basic job application automation"""
    print("🔧 Basic Job Application Automation")
    print("=" * 40)
    
    try:
        from job_application_automation import extract_job_application_form, fill_job_application_form
        
        # Example URL (replace with actual job application URL)
        url = input("Enter job application URL: ").strip()
        
        if not url:
            print("No URL provided. Using example URL...")
            url = "https://example.com/job-application"
        
        print(f"\n📋 Step 1: Extracting form fields from {url}")
        extraction_result = extract_job_application_form.invoke({"url": url})
        
        if extraction_result.success:
            print(f"✅ Found {len(extraction_result.form_fields)} form fields")
            
            print(f"\n✍️ Step 2: Filling form with generated data")
            fill_result = fill_job_application_form.invoke({
                "url": url,
                "form_data": extraction_result.suggested_data.model_dump()
            })
            
            if fill_result.success:
                print(f"✅ Successfully filled {len(fill_result.filled_fields)} fields")
                print(f"❌ Failed to fill {len(fill_result.failed_fields)} fields")
            else:
                print(f"❌ Form filling failed: {fill_result.error_message}")
        else:
            print(f"❌ Form extraction failed: {extraction_result.error_message}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def demonstrate_langchain_integration():
    """Demonstrate LangChain framework integration"""
    print("\n🤖 LangChain Framework Integration")
    print("=" * 40)
    
    try:
        from langchain_example import agent_executor
        
        # Example job application request
        url = input("Enter job application URL for LangChain analysis: ").strip()
        job_title = input("Enter job title: ").strip()
        company = input("Enter company name: ").strip()
        
        if not url or not job_title or not company:
            print("Missing information. Using example data...")
            url = "https://example.com/job-application"
            job_title = "QA Engineer"
            company = "Example Corp"
        
        print(f"\n🔍 Analyzing job application for {job_title} at {company}")
        
        # Use LangChain agent to analyze and potentially apply
        result = agent_executor.invoke({
            "input": f"Analyze the job application at {url} for a {job_title} position at {company}. Provide recommendations for filling it out."
        })
        
        print("\n📊 LangChain Analysis Result:")
        print(result["output"])
        
    except Exception as e:
        print(f"❌ Error: {e}")

def demonstrate_job_search():
    """Demonstrate job search functionality"""
    print("\n🔍 Job Search and Filtering")
    print("=" * 40)
    
    try:
        from job_search_automation import QAJobSearchAutomation
        
        # Initialize the automation system
        automation = QAJobSearchAutomation()
        
        print("📋 Step 1: Searching for QA jobs...")
        search_result = automation.search_jobs()
        
        if search_result.success and search_result.jobs:
            print(f"✅ Found {search_result.total_jobs_found} jobs")
            
            print("\n🔧 Step 2: Filtering jobs...")
            filtered_jobs = automation.filter_jobs(search_result.jobs)
            print(f"✅ Filtered down to {len(filtered_jobs)} relevant jobs")
            
            # Show some example jobs
            print("\n📋 Sample Job Listings:")
            for i, job in enumerate(filtered_jobs[:3]):
                print(f"{i+1}. {job.title} at {job.company}")
                print(f"   Location: {job.location}")
                print(f"   URL: {job.url}")
                print()
            
            # Ask if user wants to apply
            apply_choice = input("Would you like to apply to these jobs? (y/n): ").strip().lower()
            
            if apply_choice == 'y':
                print("\n📝 Step 3: Applying to jobs...")
                application_result = automation.apply_to_jobs(filtered_jobs)
                
                print(f"\n📊 Application Results:")
                print(f"Total attempted: {application_result.total_attempted}")
                print(f"Successful: {application_result.successful_applications}")
                print(f"Failed: {application_result.failed_applications}")
                print(f"Success rate: {(application_result.successful_applications/application_result.total_attempted)*100:.1f}%")
        else:
            print(f"❌ Job search failed: {search_result.error_message}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

def demonstrate_batch_processing():
    """Demonstrate batch job processing"""
    print("\n📦 Batch Job Processing")
    print("=" * 40)
    
    try:
        from job_application_automation import batch_apply_to_jobs
        
        # Example job URLs
        print("Enter job URLs (one per line, press Enter twice when done):")
        job_urls = []
        while True:
            url = input("URL: ").strip()
            if not url:
                break
            job_urls.append(url)
        
        if not job_urls:
            print("No URLs provided. Using example URLs...")
            job_urls = [
                "https://example1.com/job-application",
                "https://example2.com/job-application",
                "https://example3.com/job-application"
            ]
        
        print(f"\n🚀 Applying to {len(job_urls)} jobs...")
        
        batch_result = batch_apply_to_jobs.invoke({
            "job_urls": job_urls,
            "max_applications": len(job_urls)
        })
        
        print(f"\n📊 Batch Application Results:")
        print(f"Total attempted: {batch_result.total_attempted}")
        print(f"Successful: {batch_result.successful_applications}")
        print(f"Failed: {batch_result.failed_applications}")
        print(f"Execution time: {batch_result.execution_time:.2f} seconds")
        
        # Show detailed results
        print(f"\n📋 Detailed Results:")
        for i, result in enumerate(batch_result.application_results):
            status = "✅ SUCCESS" if result.get("success") else "❌ FAILED"
            print(f"{i+1}. {status} - {result.get('url', 'Unknown URL')}")
            if not result.get("success"):
                print(f"   Error: {result.get('error_message', 'Unknown error')}")
        
    except Exception as e:
        print(f"❌ Error: {e}")

def main():
    """Main function with interactive menu"""
    print("🤖 Job Application Automation with LangChain Framework")
    print("=" * 60)
    print()
    
    while True:
        print("Choose an option:")
        print("1. Basic Job Application Automation")
        print("2. LangChain Framework Integration")
        print("3. Job Search and Filtering")
        print("4. Batch Job Processing")
        print("5. Exit")
        print()
        
        choice = input("Enter your choice (1-5): ").strip()
        
        if choice == '1':
            demonstrate_basic_automation()
        elif choice == '2':
            demonstrate_langchain_integration()
        elif choice == '3':
            demonstrate_job_search()
        elif choice == '4':
            demonstrate_batch_processing()
        elif choice == '5':
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid choice. Please enter 1-5.")
        
        print("\n" + "="*60 + "\n")

if __name__ == "__main__":
    main() 