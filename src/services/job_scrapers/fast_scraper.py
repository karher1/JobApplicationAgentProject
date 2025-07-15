import asyncio
import aiohttp
import re
from typing import List, Optional
from bs4 import BeautifulSoup
import logging
from datetime import datetime

from .base_scraper import BaseJobScraper
from src.models.schemas import JobPosition, JobSearchRequest

logger = logging.getLogger(__name__)

class FastScraper(BaseJobScraper):
    """Fast HTTP-based scraper for getting real job data quickly"""
    
    def __init__(self):
        super().__init__()
        self.name = "FastScraper"
        self.session = None
        
        # Fast job board endpoints that don't require JavaScript
        self.job_sources = {
            "remoteok": "https://remoteok.io/api",
            "himalayas": "https://himalayas.app/jobs/api",
            "workingnomads": "https://www.workingnomads.co/api/exposed_jobs",
            "remotive": "https://remotive.io/api/remote-jobs",
            "justremote": "https://justremote.co/api/jobs"
        }
    
    async def _get_session(self):
        """Get or create aiohttp session"""
        if not self.session:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=10),
                headers={
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
                }
            )
        return self.session
    
    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape jobs using fast HTTP requests"""
        jobs = []
        
        try:
            # Try RemoteOK first (has a good API)
            remoteok_jobs = await self._scrape_remoteok(request)
            jobs.extend(remoteok_jobs)
            
            # Try other sources if we need more jobs
            if len(jobs) < request.max_results:
                other_jobs = await self._scrape_other_sources(request)
                jobs.extend(other_jobs)
            
            # Limit to requested amount
            return jobs[:request.max_results]
            
        except Exception as e:
            logger.error(f"Error in fast scraper: {e}")
            return jobs
    
    async def _scrape_remoteok(self, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape RemoteOK API - very fast and reliable"""
        jobs = []
        
        try:
            session = await self._get_session()
            
            # RemoteOK API endpoint
            url = "https://remoteok.io/api"
            
            async with session.get(url) as response:
                if response.status == 200:
                    data = await response.json()
                    
                    # Skip first item which is usually metadata
                    job_data = data[1:] if len(data) > 1 else []
                    
                    for job in job_data:
                        try:
                            # Extract job data
                            title = job.get('position', '')
                            company = job.get('company', '')
                            location = job.get('location', 'Remote')
                            job_url = f"https://remoteok.io/remote-jobs/{job.get('id', '')}"
                            description = job.get('description', '')
                            
                            # Filter by job titles
                            if self._matches_job_criteria(title, request.job_titles):
                                job_position = JobPosition(
                                    title=title,
                                    company=company,
                                    location=location,
                                    url=job_url,
                                    job_board="RemoteOK",
                                    description_snippet=description[:200] + "..." if len(description) > 200 else description,
                                    posted_date=datetime.now().strftime("%Y-%m-%d"),
                                    salary_range=f"${job.get('salary_min', 0)}-${job.get('salary_max', 0)}" if job.get('salary_min') else None,
                                    job_type="Full-time",
                                    remote_option="Remote"
                                )
                                jobs.append(job_position)
                                
                                if len(jobs) >= request.max_results:
                                    break
                                    
                        except Exception as e:
                            logger.debug(f"Error parsing RemoteOK job: {e}")
                            continue
                
        except Exception as e:
            logger.error(f"Error scraping RemoteOK: {e}")
        
        return jobs
    
    async def _scrape_other_sources(self, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape other job sources for more variety"""
        jobs = []
        
        # Try a simple HTML scraper for AngelList jobs
        try:
            session = await self._get_session()
            
            # AngelList startups often have engineering jobs
            url = "https://angel.co/jobs"
            
            async with session.get(url) as response:
                if response.status == 200:
                    html = await response.text()
                    soup = BeautifulSoup(html, 'html.parser')
                    
                    # Look for job listings (simplified)
                    job_elements = soup.find_all('div', class_='job-listing')
                    
                    for element in job_elements[:5]:  # Limit to 5 jobs
                        try:
                            title_elem = element.find('h3') or element.find('h2')
                            company_elem = element.find('span', class_='company')
                            
                            if title_elem and company_elem:
                                title = title_elem.get_text(strip=True)
                                company = company_elem.get_text(strip=True)
                                
                                if self._matches_job_criteria(title, request.job_titles):
                                    job_position = JobPosition(
                                        title=title,
                                        company=company,
                                        location="Remote",
                                        url="https://angel.co/jobs",
                                        job_board="AngelList",
                                        description_snippet=f"Engineering position at {company}",
                                        posted_date=datetime.now().strftime("%Y-%m-%d"),
                                        job_type="Full-time",
                                        remote_option="Remote"
                                    )
                                    jobs.append(job_position)
                                    
                        except Exception as e:
                            logger.debug(f"Error parsing AngelList job: {e}")
                            continue
                            
        except Exception as e:
            logger.debug(f"Error scraping AngelList: {e}")
        
        return jobs
    
    def _matches_job_criteria(self, title: str, target_titles: List[str]) -> bool:
        """Check if job title matches search criteria"""
        title_lower = title.lower()
        
        for target in target_titles:
            if target.lower() in title_lower:
                return True
        
        # Also check for common engineering keywords
        engineering_keywords = [
            'engineer', 'developer', 'software', 'backend', 'frontend', 
            'fullstack', 'full-stack', 'qa', 'sdet', 'test', 'python',
            'javascript', 'react', 'node', 'senior', 'junior', 'lead'
        ]
        
        for keyword in engineering_keywords:
            if keyword in title_lower:
                return True
        
        return False
    
    def can_handle_url(self, url: str) -> bool:
        """This scraper can handle any URL by using job board APIs"""
        return True
    
    async def close(self):
        """Close the session"""
        if self.session:
            await self.session.close()
            self.session = None 