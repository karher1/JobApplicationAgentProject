#!/usr/bin/env python3
"""
QA/SDET Job Search and Application Automation Script

This script automates the process of:
1. Searching for QA Engineer, SDET, Software Engineer in Test positions
2. Filtering jobs based on specific criteria
3. Batch applying to multiple positions
4. Tracking application results

Usage:
    python job_search_automation.py --search-only
    python job_search_automation.py --apply-batch
    python job_search_automation.py --full-automation
"""

import argparse
import sys
import os
import json
import time
from datetime import datetime
from typing import List, Dict, Any

# Add the current directory to Python path to import from main module
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from job_application_automation import (
    search_qa_jobs, batch_apply_to_jobs, filter_jobs_by_criteria,
    JobPosition, JobSearchResult, BatchApplicationResult,
    logger
)

class QAJobSearchAutomation:
    """Main class for QA job search automation"""
    
    def __init__(self):
        self.config = self.load_config()
        self.results_dir = "job_search_results"
        os.makedirs(self.results_dir, exist_ok=True)
    
    def load_config(self) -> Dict[str, Any]:
        """Load configuration from file or use defaults"""
        default_config = {
            "job_titles": [
                "QA Engineer",
                "SDET", 
                "Software Engineer in Test",
                "QA Automation Engineer",
                "Test Automation Engineer",
                "Quality Assurance Engineer"
            ],
            "locations": [
                "United States",
                "Remote",
                "San Francisco, CA",
                "New York, NY",
                "Austin, TX",
                "Seattle, WA"
            ],
            "required_keywords": [
                "automation",
                "selenium",
                "testing",
                "cypress",
                "pytest",
                "playwright"
            ],
            "excluded_keywords": [
                "manual testing only",
                "principal",
                "director",
                "vp",
                "vice president"
            ],
            "preferred_companies": [
                "Google",
                "Microsoft",
                "Amazon",
                "Apple",
                "Meta",
                "Netflix",
                "Uber",
                "Airbnb",
                "Stripe",
                "Shopify"
            ],
            "max_applications_per_run": 10,
            "max_search_results": 100,
            "remote_preferred": True,
            "delay_between_applications": 30
        }
        
        config_file = "job_search_config.json"
        if os.path.exists(config_file):
            try:
                with open(config_file, 'r') as f:
                    user_config = json.load(f)
                    default_config.update(user_config)
                    logger.info(f"Loaded configuration from {config_file}")
            except Exception as e:
                logger.warning(f"Error loading config file: {e}. Using defaults.")
        else:
            # Create default config file
            with open(config_file, 'w') as f:
                json.dump(default_config, f, indent=2)
            logger.info(f"Created default configuration file: {config_file}")
        
        return default_config
    
    def search_jobs(self) -> JobSearchResult:
        """Search for QA/SDET jobs across multiple platforms"""
        logger.info("🔍 Starting comprehensive job search...")
        
        # Perform the search using the tool's invoke method
        search_result = search_qa_jobs.invoke({
            "job_titles": self.config["job_titles"],
            "locations": self.config["locations"],
            "max_results_per_search": self.config["max_search_results"]
        })
        
        if search_result.success:
            logger.info(f"✅ Found {search_result.total_jobs_found} jobs")
            
            # Save search results
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            results_file = os.path.join(self.results_dir, f"search_results_{timestamp}.json")
            
            with open(results_file, 'w') as f:
                json.dump(search_result.model_dump(), f, indent=2, default=str)
            
            logger.info(f"Search results saved to {results_file}")
        else:
            logger.error(f"❌ Job search failed: {search_result.error_message}")
        
        return search_result
    
    def filter_jobs(self, jobs: List[JobPosition]) -> List[JobPosition]:
        """Filter jobs based on configuration criteria"""
        logger.info("🔧 Filtering jobs based on criteria...")
        
        filtered_jobs = filter_jobs_by_criteria.invoke({
            "jobs": jobs,
            "required_keywords": self.config["required_keywords"],
            "excluded_keywords": self.config["excluded_keywords"],
            "preferred_companies": self.config["preferred_companies"],
            "remote_only": self.config["remote_preferred"]
        })
        
        return filtered_jobs
    
    def apply_to_jobs(self, jobs: List[JobPosition]) -> BatchApplicationResult:
        """Apply to filtered jobs in batch"""
        logger.info("📝 Starting batch job applications...")
        
        # Extract URLs from job positions
        job_urls = [job.url for job in jobs if job.url]
        
        # Limit applications
        max_apps = min(len(job_urls), self.config["max_applications_per_run"])
        job_urls = job_urls[:max_apps]
        
        logger.info(f"Applying to {len(job_urls)} positions")
        
        # Perform batch applications using the tool's invoke method
        batch_result = batch_apply_to_jobs.invoke({
            "job_urls": job_urls,
            "max_applications": self.config["max_applications_per_run"]
        })
        
        # Save application results
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        results_file = os.path.join(self.results_dir, f"application_results_{timestamp}.json")
        
        with open(results_file, 'w') as f:
            json.dump(batch_result.model_dump(), f, indent=2, default=str)
        
        logger.info(f"Application results saved to {results_file}")
        
        return batch_result
    
    def run_full_automation(self):
        """Run the complete automation workflow"""
        logger.info("🚀 Starting full automation workflow...")
        
        start_time = time.time()
        
        try:
            # Step 1: Search for jobs
            search_result = self.search_jobs()
            
            if not search_result.success or not search_result.jobs:
                logger.error("No jobs found. Exiting automation.")
                return
            
            # Step 2: Filter jobs
            filtered_jobs = self.filter_jobs(search_result.jobs)
            
            if not filtered_jobs:
                logger.warning("No jobs match the filtering criteria.")
                return
            
            logger.info(f"Selected {len(filtered_jobs)} jobs for application")
            
            # Step 3: Apply to jobs
            application_result = self.apply_to_jobs(filtered_jobs)
            
            # Step 4: Generate summary report
            self.generate_summary_report(search_result, filtered_jobs, application_result)
            
        except Exception as e:
            logger.error(f"Error in full automation: {str(e)}")
        
        execution_time = time.time() - start_time
        logger.info(f"⏱️ Total execution time: {execution_time/60:.2f} minutes")
    
    def generate_summary_report(self, search_result: JobSearchResult, 
                               filtered_jobs: List[JobPosition], 
                               application_result: BatchApplicationResult):
        """Generate a comprehensive summary report"""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        report_file = os.path.join(self.results_dir, f"summary_report_{timestamp}.txt")
        
        with open(report_file, 'w') as f:
            f.write("🎯 QA/SDET Job Application Automation Summary\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Execution Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            
            f.write("📊 Search Results:\n")
            f.write(f"  • Total jobs found: {search_result.total_jobs_found}\n")
            f.write(f"  • Jobs after filtering: {len(filtered_jobs)}\n")
            f.write(f"  • Search query: {search_result.search_query}\n\n")
            
            f.write("📝 Application Results:\n")
            f.write(f"  • Applications attempted: {application_result.total_attempted}\n")
            f.write(f"  • Successful applications: {application_result.successful_applications}\n")
            f.write(f"  • Failed applications: {application_result.failed_applications}\n")
            f.write(f"  • Success rate: {(application_result.successful_applications/application_result.total_attempted*100):.1f}%\n\n")
            
            f.write("🎯 Top Applied Positions:\n")
            for i, job in enumerate(filtered_jobs[:application_result.total_attempted], 1):
                f.write(f"  {i}. {job.title} at {job.company} ({job.location})\n")
                f.write(f"     URL: {job.url}\n")
            
            f.write(f"\n⏱️ Total execution time: {application_result.execution_time/60:.2f} minutes\n")
        
        logger.info(f"📋 Summary report saved to {report_file}")
        
        # Also print summary to console
        print("\n" + "="*60)
        print("🎯 QA/SDET Job Application Automation Complete!")
        print("="*60)
        print(f"📊 Found {search_result.total_jobs_found} jobs, filtered to {len(filtered_jobs)}")
        print(f"📝 Applied to {application_result.successful_applications}/{application_result.total_attempted} positions successfully")
        print(f"⏱️ Completed in {application_result.execution_time/60:.2f} minutes")
        print(f"📋 Full report: {report_file}")
        print("="*60)

def main():
    """Main entry point for the script"""
    parser = argparse.ArgumentParser(
        description="QA/SDET Job Search and Application Automation",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --search-only                   # Only search for jobs
  %(prog)s --apply-batch job_urls.txt      # Apply to jobs from file
  %(prog)s --full-automation               # Complete workflow
  %(prog)s --config-setup                  # Setup configuration
        """
    )
    
    parser.add_argument(
        "--search-only", 
        action="store_true",
        help="Only search for jobs without applying"
    )
    
    parser.add_argument(
        "--apply-batch",
        type=str,
        help="Apply to jobs from a file containing URLs (one per line)"
    )
    
    parser.add_argument(
        "--full-automation",
        action="store_true", 
        help="Run complete workflow: search, filter, and apply"
    )
    
    parser.add_argument(
        "--config-setup",
        action="store_true",
        help="Setup configuration file interactively"
    )
    
    parser.add_argument(
        "--max-applications",
        type=int,
        default=10,
        help="Maximum number of applications to submit (default: 10)"
    )
    
    args = parser.parse_args()
    
    # Initialize automation
    automation = QAJobSearchAutomation()
    
    if args.config_setup:
        setup_configuration()
        return
    
    if args.search_only:
        automation.search_jobs()
        
    elif args.apply_batch:
        if not os.path.exists(args.apply_batch):
            logger.error(f"File not found: {args.apply_batch}")
            return
        
        with open(args.apply_batch, 'r') as f:
            job_urls = [line.strip() for line in f if line.strip()]
        
        logger.info(f"Applying to {len(job_urls)} jobs from {args.apply_batch}")
        batch_apply_to_jobs.invoke({
            "job_urls": job_urls,
            "max_applications": args.max_applications
        })
        
    elif args.full_automation:
        automation.run_full_automation()
        
    else:
        # Default: run full automation
        automation.run_full_automation()

def setup_configuration():
    """Interactive configuration setup"""
    print("🔧 QA Job Search Configuration Setup")
    print("=" * 40)
    
    config = {}
    
    # Job titles
    print("\n1. Job Titles to Search:")
    default_titles = ["QA Engineer", "SDET", "Software Engineer in Test", "QA Automation Engineer"]
    titles_input = input(f"Enter job titles (comma-separated) [{', '.join(default_titles)}]: ").strip()
    config["job_titles"] = [t.strip() for t in titles_input.split(",")] if titles_input else default_titles
    
    # Locations
    print("\n2. Locations to Search:")
    default_locations = ["United States", "Remote", "San Francisco, CA"]
    locations_input = input(f"Enter locations (comma-separated) [{', '.join(default_locations)}]: ").strip()
    config["locations"] = [l.strip() for l in locations_input.split(",")] if locations_input else default_locations
    
    # Max applications
    print("\n3. Application Settings:")
    max_apps = input("Maximum applications per run [10]: ").strip()
    config["max_applications_per_run"] = int(max_apps) if max_apps.isdigit() else 10
    
    # Remote preference
    remote_pref = input("Prefer remote positions? (y/n) [y]: ").strip().lower()
    config["remote_preferred"] = remote_pref != 'n'
    
    # Save configuration
    with open("job_search_config.json", 'w') as f:
        json.dump(config, f, indent=2)
    
    print("\n✅ Configuration saved to job_search_config.json")
    print("You can now run the automation with your custom settings!")

if __name__ == "__main__":
    main() 