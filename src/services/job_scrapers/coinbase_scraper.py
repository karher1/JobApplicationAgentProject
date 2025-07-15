import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from .base_scraper import BaseJobScraper
from src.models.schemas import JobPosition, JobSearchRequest

class CoinbaseScraper(BaseJobScraper):
    """Scraper for Coinbase careers page using Greenhouse API."""
    
    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL."""
        return "coinbase.com" in url.lower()
    
    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        """
        Scrape job listings from Coinbase via Greenhouse API.
        Coinbase uses Greenhouse for their job board.
        """
        self.logger.info(f"Starting to scrape Coinbase jobs via Greenhouse API")
        
        # Coinbase uses Greenhouse - use their API directly
        api_url = "https://boards-api.greenhouse.io/v1/boards/coinbase/jobs"
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36'
                }
                
                self.logger.info(f"Fetching jobs from Greenhouse API: {api_url}")
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        jobs_data = data.get('jobs', [])
                        self.logger.info(f"Successfully fetched {len(jobs_data)} jobs from Greenhouse API")
                        
                        # Parse jobs
                        jobs = []
                        for job_data in jobs_data:
                            job = self._parse_greenhouse_job(job_data)
                            if job:
                                jobs.append(job)
                        
                        self.logger.info(f"Successfully parsed {len(jobs)} jobs")
                        
                        # Filter jobs based on search criteria
                        filtered_jobs = []
                        for job in jobs:
                            if self.matches_search_criteria(job, request):
                                filtered_jobs.append(job)
                        
                        self.logger.info(f"After filtering: {len(filtered_jobs)} jobs match criteria")
                        return filtered_jobs
                    else:
                        self.logger.error(f"Failed to fetch jobs from Greenhouse API: HTTP {response.status}")
                        return []
                        
            except Exception as e:
                self.logger.error(f"Error scraping Coinbase jobs: {str(e)}")
                return []
    
    def _parse_greenhouse_job(self, job_data: Dict[str, Any]) -> Optional[JobPosition]:
        """Parse individual job data from Greenhouse API."""
        try:
            # Extract basic job information
            title = job_data.get('title', '').strip()
            if not title:
                return None
            
            # Extract URL
            absolute_url = job_data.get('absolute_url', '')
            
            # Extract location
            location_data = job_data.get('location', {})
            location = location_data.get('name', '') if location_data else ''
            
            # Extract department
            departments = job_data.get('departments', [])
            department = departments[0].get('name', '') if departments else ''
            
            # Extract other details
            job_id = str(job_data.get('id', ''))
            updated_at = job_data.get('updated_at', '')
            
            # Extract metadata
            metadata = job_data.get('metadata', [])
            
            # Determine remote option
            remote_option = "Remote" if "Remote" in location else "On-site"
            
            self.logger.debug(f"Parsed job: {title} in {location} ({department})")
            
            # Create JobPosition using the base class helper method
            return self.create_job_position(
                title=title,
                company="Coinbase",
                location=location,
                url=absolute_url,
                description=f"Department: {department}",
                job_type="Full-time",  # Default for Coinbase
                remote_option=remote_option
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing job data: {str(e)}")
            return None 