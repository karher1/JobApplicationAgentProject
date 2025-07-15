import asyncio
import aiohttp
from typing import List, Dict, Any, Optional
from .base_scraper import BaseJobScraper
from src.models.schemas import JobPosition, JobSearchRequest

class GitHubScraper(BaseJobScraper):
    """Scraper for GitHub careers page using their API."""
    
    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL."""
        return "github.com" in url.lower() or "github.careers" in url.lower()
    
    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        """
        Scrape job listings from GitHub via their careers API.
        GitHub has their own API at github.careers/api/jobs.
        """
        self.logger.info(f"Starting to scrape GitHub jobs via careers API")
        
        # GitHub careers API endpoint
        api_url = "https://www.github.careers/api/jobs"
        
        async with aiohttp.ClientSession() as session:
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
                    'Accept': 'application/json, text/plain, */*',
                    'Accept-Language': 'en-US,en;q=0.9',
                }
                
                self.logger.info(f"Fetching jobs from GitHub API: {api_url}")
                async with session.get(api_url, headers=headers) as response:
                    if response.status == 200:
                        data = await response.json()
                        jobs_data = data.get('jobs', [])
                        total_count = data.get('totalCount', len(jobs_data))
                        
                        self.logger.info(f"Successfully fetched {len(jobs_data)} jobs out of {total_count} total from GitHub API")
                        
                        # Parse jobs
                        jobs = []
                        for job_item in jobs_data:
                            job = self._parse_github_job(job_item)
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
                        self.logger.error(f"Failed to fetch jobs from GitHub API: HTTP {response.status}")
                        return []
                        
            except Exception as e:
                self.logger.error(f"Error scraping GitHub jobs: {str(e)}")
                return []
    
    def _parse_github_job(self, job_item: Dict[str, Any]) -> Optional[JobPosition]:
        """Parse individual job data from GitHub API."""
        try:
            # GitHub API nests job data under 'data' key
            job_data = job_item.get('data', {})
            if not job_data:
                return None
            
            # Extract basic job information
            title = job_data.get('title', '').strip()
            if not title:
                return None
            
            # Extract URL - construct from apply_url or use canonical_url
            apply_url = job_data.get('apply_url', '')
            canonical_url = job_data.get('meta_data', {}).get('canonical_url', '')
            job_url = canonical_url or apply_url
            
            # Extract location
            location_name = job_data.get('location_name', '')
            country = job_data.get('country', '')
            full_location = job_data.get('full_location', '')
            location = location_name or full_location or country
            
            # Extract department/category
            categories = job_data.get('categories', [])
            category = categories[0].get('name', '') if categories else ''
            
            # Extract other details
            req_id = job_data.get('req_id', '')
            posted_date = job_data.get('posted_date', '')
            employment_type = job_data.get('employment_type', 'FULL_TIME')
            
            # Extract description snippet
            description = job_data.get('description', '')
            description_snippet = description[:200] + '...' if len(description) > 200 else description
            
            # Determine remote option
            location_type = job_data.get('location_type', '')
            remote_option = "Remote" if "Remote" in location or location_type == "REMOTE" else "On-site"
            
            # Determine job type
            job_type = "Full-time" if employment_type == "FULL_TIME" else employment_type.replace('_', '-').title()
            
            self.logger.debug(f"Parsed job: {title} in {location} ({category})")
            
            # Create JobPosition using the base class helper method
            return self.create_job_position(
                title=title,
                company="GitHub",
                location=location,
                url=job_url,
                description=f"Category: {category}. {description_snippet}" if category else description_snippet,
                job_type=job_type,
                remote_option=remote_option
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing GitHub job data: {str(e)}")
            return None 