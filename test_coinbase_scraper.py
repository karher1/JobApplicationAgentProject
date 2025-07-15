#!/usr/bin/env python3

import asyncio
import sys
import os

# Add the src directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.services.job_scrapers.coinbase_scraper import CoinbaseScraper
from src.models.schemas import JobSearchRequest

async def test_coinbase_scraper():
    """Test the Coinbase scraper"""
    scraper = CoinbaseScraper()
    
    # Create a test search request
    request = JobSearchRequest(
        job_titles=["Software Engineer", "Product Manager", "Data Scientist"],
        locations=["Remote", "USA", "UK"],
        remote_only=False
    )
    
    print("Testing Coinbase scraper...")
    print(f"Search criteria: {request.job_titles}")
    print(f"Locations: {request.locations}")
    print()
    
    # Test scraping
    jobs = await scraper.scrape_jobs("https://www.coinbase.com/careers", request)
    
    print(f"Found {len(jobs)} jobs")
    print()
    
    # Display first 10 jobs
    for i, job in enumerate(jobs[:10]):
        print(f"{i+1}. {job.title}")
        print(f"   Company: {job.company}")
        print(f"   Location: {job.location}")
        print(f"   URL: {job.url}")
        print(f"   Description: {job.description_snippet}")
        print()

if __name__ == "__main__":
    asyncio.run(test_coinbase_scraper()) 