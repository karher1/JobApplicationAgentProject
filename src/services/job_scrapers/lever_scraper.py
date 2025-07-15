import requests
import logging
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .base_scraper import BaseJobScraper
from src.models.schemas import JobPosition, JobSearchRequest

class LeverScraper(BaseJobScraper):
    """Scraper for Lever job boards (jobs.lever.co)"""
    
    def __init__(self):
        super().__init__()
        self.name = "Lever"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL"""
        return "lever.co" in url or "jobs.lever.co" in url
    
    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape jobs from Lever job boards"""
        jobs = []
        
        try:
            self.logger.info(f"Scraping Lever URL: {url}")
            
            # Get the page content
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Parse with BeautifulSoup
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Find job listings
            job_elements = self._find_job_elements(soup)
            
            if not job_elements:
                self.logger.warning(f"No job elements found for {url}")
                return jobs
            
            # Extract job data
            for element in job_elements:
                try:
                    job_data = self._extract_job_data(element, url)
                    if job_data and self.matches_search_criteria(job_data, request):
                        jobs.append(job_data)
                        self.logger.info(f"Found matching job: {job_data.title}")
                        
                except Exception as e:
                    self.logger.warning(f"Error extracting job data: {e}")
                    continue
            
        except Exception as e:
            self.logger.error(f"Error scraping Lever page {url}: {e}")
        
        return jobs
    
    def _find_job_elements(self, soup: BeautifulSoup) -> List:
        """Find job elements on the page"""
        job_selectors = [
            ".posting",  # Common Lever selector
            ".job-posting",
            ".job-listing",
            ".job-card",
            "[data-testid*='job']",
            "a[href*='/jobs/']",
            "div[role='listitem']",
            ".position"
        ]
        
        for selector in job_selectors:
            elements = soup.select(selector)
            if elements:
                self.logger.info(f"Found {len(elements)} job elements with selector: {selector}")
                return elements
        
        # Fallback: look for any links that might be jobs
        job_links = soup.find_all('a', href=True)
        job_links = [link for link in job_links if any(keyword in link['href'] for keyword in ['/jobs/', '/job/', 'lever.co'])]
        self.logger.info(f"Found {len(job_links)} potential job links")
        return job_links
    
    def _extract_job_data(self, element, base_url: str) -> Optional[JobPosition]:
        """Extract job data from an element"""
        try:
            # Extract job title - look for h5 with posting name first
            title_elem = element.select_one('h5[data-qa="posting-name"], h5, .posting-title h5')
            if not title_elem:
                # Fallback to other selectors
                title_elem = element.select_one('.posting-title, .job-title, h3, h4')
            
            if not title_elem:
                return None
            
            job_title = title_elem.get_text(strip=True)
            if not job_title:
                return None
            
            # Extract job URL - look for posting-title link
            link_elem = element.select_one('.posting-title, a[href*="/mistral/"], a[href*="/jobs/"]')
            job_url = None
            if link_elem and link_elem.get('href'):
                job_url = urljoin(base_url, link_elem.get('href'))
            
            # Extract location from posting categories
            location_elem = element.select_one('.posting-categories .location')
            if not location_elem:
                # Fallback to other location selectors
                location_elem = element.select_one('.posting-categories, .location, .job-location')
            
            location = "Remote"  # Default
            if location_elem:
                location_text = location_elem.get_text(strip=True)
                # Clean up location text
                if location_text:
                    location = location_text
            
            # Extract company from URL
            company = self._extract_company_from_url(base_url)
            
            # Extract department/team
            dept_elem = element.select_one('.posting-department, .department, .team')
            department = dept_elem.get_text(strip=True) if dept_elem else ""
            
            # Create description with more detail
            description_parts = []
            if department:
                description_parts.append(f"{department} position")
            description_parts.append(f"at {company}")
            
            # Add location info if available
            if location and location != "Remote":
                description_parts.append(f"in {location}")
                
            description = " ".join(description_parts)
            
            return self.create_job_position(
                title=job_title,
                company=company,
                location=location,
                url=job_url or base_url,
                description=description
            )
            
        except Exception as e:
            self.logger.warning(f"Error extracting job data: {e}")
            return None
    
    def _extract_company_from_url(self, url: str) -> str:
        """Extract company name from URL"""
        try:
            # Extract from jobs.lever.co/company-name
            parts = url.split('/')
            if len(parts) > 3 and 'lever.co' in url:
                company = parts[3].replace('-', ' ').title()
                return company
        except:
            pass
        return "Unknown Company" 