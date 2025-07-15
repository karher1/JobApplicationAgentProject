#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.job_scrapers.github_scraper import GitHubScraper
from src.models.schemas import JobSearchRequest

async def test_github_scraper():
    """Test the GitHub scraper"""
    scraper = GitHubScraper()
    
    # Create a test search request
    request = JobSearchRequest(
        job_titles=["Software Engineer", "Product Manager", "Data Scientist", "Solutions Engineer"],
        locations=["Remote", "USA", "UK", "India"],
        remote_only=False
    )
    
    print("Testing GitHub scraper...")
    print(f"Search criteria: {request.job_titles}")
    print(f"Locations: {request.locations}")
    print()
    
    # Test scraping
    jobs = await scraper.scrape_jobs("https://www.github.careers/careers-home/jobs", request)
    
    print(f"Found {len(jobs)} jobs")
    print()
    
    # Display first 10 jobs
    for i, job in enumerate(jobs[:10]):
        print(f"{i+1}. {job.title}")
        print(f"   Company: {job.company}")
        print(f"   Location: {job.location}")
        print(f"   URL: {job.url}")
        print(f"   Description: {job.description_snippet}")
        print(f"   Job Type: {job.job_type}")
        print(f"   Remote Option: {job.remote_option}")
        print()

if __name__ == "__main__":
    asyncio.run(test_github_scraper()) 