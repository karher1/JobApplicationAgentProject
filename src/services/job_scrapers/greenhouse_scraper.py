import requests
import logging
from typing import List, Optional
from bs4 import BeautifulSoup
from urllib.parse import urljoin

from .base_scraper import BaseJobScraper
from src.models.schemas import JobPosition, JobSearchRequest

class GreenhouseScraper(BaseJobScraper):
    """Scraper for Greenhouse job boards (boards.greenhouse.io)"""
    
    def __init__(self):
        super().__init__()
        self.name = "Greenhouse"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36'
        })
    
    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL"""
        return "greenhouse.io" in url or "boards.greenhouse.io" in url
    
    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape jobs from Greenhouse job boards"""
        jobs = []
        
        try:
            self.logger.info(f"Scraping Greenhouse URL: {url}")
            
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
            self.logger.error(f"Error scraping Greenhouse page {url}: {e}")
        
        return jobs
    
    def _find_job_elements(self, soup: BeautifulSoup) -> List:
        """Find job elements on the page"""
        job_selectors = [
            ".opening",  # Common Greenhouse selector
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
        job_links = [link for link in job_links if any(keyword in link['href'] for keyword in ['/jobs/', '/job/', 'greenhouse.io'])]
        self.logger.info(f"Found {len(job_links)} potential job links")
        return job_links
    
    def _extract_job_data(self, element, base_url: str) -> Optional[JobPosition]:
        """Extract job data from an element"""
        try:
            # Extract job title
            title_elem = element.select_one('a, .job-title, .position-title, h3, h4')
            if not title_elem:
                return None
            
            job_title = title_elem.get_text(strip=True)
            if not job_title:
                return None
            
            # Extract job URL
            if title_elem.name == 'a':
                job_url = title_elem.get('href')
            else:
                link_elem = element.select_one('a')
                job_url = link_elem.get('href') if link_elem else None
            
            if job_url:
                job_url = urljoin(base_url, job_url)
            
            # Extract location
            location_elem = element.select_one('.location, .job-location, .department')
            location = location_elem.get_text(strip=True) if location_elem else "Remote"
            
            # Extract company from URL
            company = self._extract_company_from_url(base_url)
            
            # Extract department/team
            dept_elem = element.select_one('.department, .team')
            department = dept_elem.get_text(strip=True) if dept_elem else ""
            
            # Create description
            description = f"{department} position at {company}" if department else f"Job opportunity at {company}"
            
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
            # Extract from boards.greenhouse.io/company-name
            parts = url.split('/')
            if len(parts) > 2:
                company = parts[2].replace('-', ' ').title()
                return company
        except:
            pass
        return "Unknown Company" 