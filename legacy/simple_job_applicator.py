#!/usr/bin/env python3
"""
Simple Job Application Script

This script provides a practical approach to automating job applications:
1. You provide job URLs manually (from your own searches)
2. The script automatically fills out all forms with realistic data
3. You review and submit manually

This avoids the complexity of web scraping while providing maximum value.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_application_automation import extract_job_application_form, fill_job_application_form, logger
import json
import time
from datetime import datetime

class SimpleJobApplicator:
    """Simple job application automation focusing on form filling"""
    
    def __init__(self):
        self.results = []
        
    def apply_to_single_job(self, url: str) -> dict:
        """Apply to a single job and return results"""
        logger.info(f"🎯 Applying to: {url}")
        
        try:
            # Extract form fields
            extraction_result = extract_job_application_form.invoke({"url": url})
            
            if extraction_result.success and extraction_result.suggested_data:
                # Fill the form
                form_data = extraction_result.suggested_data.additional_info
                fill_result = fill_job_application_form.invoke({"url": url, "form_data": form_data})
                
                result = {
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "success": fill_result.success,
                    "filled_fields": len(fill_result.filled_fields),
                    "total_fields": len(extraction_result.form_fields),
                    "failed_fields": fill_result.failed_fields,
                    "error_message": fill_result.error_message
                }
                
                if fill_result.success:
                    logger.info(f"✅ Successfully filled {len(fill_result.filled_fields)} fields")
                    print(f"✅ SUCCESS: {len(fill_result.filled_fields)}/{len(extraction_result.form_fields)} fields filled")
                else:
                    logger.warning(f"❌ Failed: {fill_result.error_message}")
                    print(f"❌ FAILED: {fill_result.error_message}")
                    
            else:
                result = {
                    "url": url,
                    "timestamp": datetime.now().isoformat(),
                    "success": False,
                    "filled_fields": 0,
                    "total_fields": 0,
                    "failed_fields": [],
                    "error_message": extraction_result.error_message or "Failed to extract form fields"
                }
                print(f"❌ EXTRACTION FAILED: {result['error_message']}")
                
            self.results.append(result)
            return result
            
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            result = {
                "url": url,
                "timestamp": datetime.now().isoformat(),
                "success": False,
                "filled_fields": 0,
                "total_fields": 0,
                "failed_fields": [],
                "error_message": str(e)
            }
            self.results.append(result)
            return result
    
    def apply_to_multiple_jobs(self, urls: list, delay_seconds: int = 30):
        """Apply to multiple jobs with delays between applications"""
        print(f"🚀 Starting batch application to {len(urls)} jobs")
        print(f"⏱️  Delay between applications: {delay_seconds} seconds")
        print("-" * 60)
        
        for i, url in enumerate(urls, 1):
            print(f"\n📝 Application {i}/{len(urls)}")
            print(f"🔗 URL: {url}")
            
            result = self.apply_to_single_job(url)
            
            # Add delay between applications (except for the last one)
            if i < len(urls):
                print(f"⏸️  Waiting {delay_seconds} seconds before next application...")
                time.sleep(delay_seconds)
        
        # Save results
        self.save_results()
        self.print_summary()
    
    def save_results(self):
        """Save results to JSON file"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"job_applications_{timestamp}.json"
        
        try:
            with open(filename, 'w') as f:
                json.dump({
                    "timestamp": datetime.now().isoformat(),
                    "total_applications": len(self.results),
                    "successful_applications": len([r for r in self.results if r["success"]]),
                    "results": self.results
                }, f, indent=2)
            
            print(f"\n💾 Results saved to: {filename}")
            
        except Exception as e:
            logger.error(f"Error saving results: {str(e)}")
    
    def print_summary(self):
        """Print a summary of all applications"""
        successful = len([r for r in self.results if r["success"]])
        total = len(self.results)
        
        print("\n" + "="*60)
        print("📊 BATCH APPLICATION SUMMARY")
        print("="*60)
        print(f"📝 Total Applications: {total}")
        print(f"✅ Successful: {successful}")
        print(f"❌ Failed: {total - successful}")
        print(f"📈 Success Rate: {(successful/total*100):.1f}%" if total > 0 else "0%")
        print("\n📋 Individual Results:")
        
        for i, result in enumerate(self.results, 1):
            status = "✅" if result["success"] else "❌"
            fields_info = f"{result['filled_fields']}/{result['total_fields']}" if result['total_fields'] > 0 else "0/0"
            print(f"  {i}. {status} {fields_info} fields - {result['url']}")
            if not result["success"] and result["error_message"]:
                print(f"     Error: {result['error_message']}")
        
        print("="*60)

def main():
    """Main function with examples"""
    print("🤖 Simple Job Application Automation")
    print("=====================================")
    
    # Example job URLs - replace with real ones
    example_urls = [
        "https://example-company.com/careers/qa-engineer",
        "https://another-company.ashbyhq.com/jobs/sdet-position"
    ]
    
    print("\n💡 USAGE EXAMPLES:")
    print("\n1. Apply to a single job:")
    print("   applicator = SimpleJobApplicator()")
    print("   applicator.apply_to_single_job('https://company.com/job-url')")
    
    print("\n2. Apply to multiple jobs:")
    print("   job_urls = [")
    print("       'https://company1.com/qa-engineer',")
    print("       'https://company2.ashbyhq.com/sdet-role',")
    print("       'https://company3.com/automation-engineer'")
    print("   ]")
    print("   applicator = SimpleJobApplicator()")
    print("   applicator.apply_to_multiple_jobs(job_urls, delay_seconds=30)")
    
    print("\n3. Apply from a text file:")
    print("   # Create a file 'job_urls.txt' with one URL per line")
    print("   with open('job_urls.txt', 'r') as f:")
    print("       urls = [line.strip() for line in f if line.strip()]")
    print("   applicator = SimpleJobApplicator()")
    print("   applicator.apply_to_multiple_jobs(urls)")
    
    print("\n🔍 HOW TO FIND JOB URLS:")
    print("1. Visit job boards manually (Indeed, LinkedIn, company career pages)")
    print("2. Search for QA Engineer, SDET, Software Engineer in Test roles")
    print("3. Copy the application URLs")
    print("4. Use this script to automatically fill out all the forms!")
    
    print("\n⚠️  IMPORTANT:")
    print("- The script fills forms but DOES NOT submit them")
    print("- You can review all filled data before submitting")
    print("- Resume upload fields are automatically skipped")
    print("- All data is realistic dummy data generated by AI")

if __name__ == "__main__":
    main() 