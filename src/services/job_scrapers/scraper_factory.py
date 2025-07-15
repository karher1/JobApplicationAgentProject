import logging
from typing import List, Optional
from urllib.parse import urlparse

from .base_scraper import BaseJobScraper
from .ashby_scraper import AshbyScraper
from .greenhouse_scraper import GreenhouseScraper
from .lever_scraper import LeverScraper
from .fast_scraper import FastScraper
from .stripe_scraper import StripeScraper
from .plaid_scraper import PlaidScraper
from .workable_scraper import WorkableScraper
from src.models.schemas import JobPosition, JobSearchRequest

logger = logging.getLogger(__name__)

class JobScraperFactory:
    """Factory for creating job scrapers based on URL"""
    
    def __init__(self):
        self.scrapers = [
            FastScraper(),  # Add FastScraper first for priority
            AshbyScraper(),
            GreenhouseScraper(),
            LeverScraper(),
            WorkableScraper(),
        ]
        self.logger = logging.getLogger("scraper.factory")
    
    def get_scraper_for_url(self, url: str) -> Optional[BaseJobScraper]:
        """Get the appropriate scraper for a given URL"""
        for scraper in self.scrapers:
            if scraper.can_handle_url(url):
                self.logger.info(f"Selected {scraper.name} scraper for URL: {url}")
                return scraper
        
        self.logger.warning(f"No scraper found for URL: {url}")
        return None
    
    def get_scraper_by_name(self, name: str) -> Optional[BaseJobScraper]:
        """Get a scraper by name"""
        for scraper in self.scrapers:
            if scraper.name.lower() == name.lower():
                return scraper
        return None
    
    def get_all_scrapers(self) -> List[BaseJobScraper]:
        """Get all available scrapers"""
        return self.scrapers
    
    async def scrape_jobs_from_url(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape jobs from a URL using the appropriate scraper"""
        scraper = self.get_scraper_for_url(url)
        if not scraper:
            self.logger.error(f"No scraper available for URL: {url}")
            return []
        
        try:
            jobs = await scraper.scrape_jobs(url, request)
            self.logger.info(f"Scraped {len(jobs)} jobs from {url} using {scraper.name}")
            return jobs
        except Exception as e:
            self.logger.error(f"Error scraping jobs from {url}: {e}")
            return []
    
    async def scrape_jobs_from_multiple_sources(self, urls: List[str], request: JobSearchRequest) -> List[JobPosition]:
        """Scrape jobs from multiple URLs"""
        all_jobs = []
        
        for url in urls:
            try:
                jobs = await self.scrape_jobs_from_url(url, request)
                all_jobs.extend(jobs)
                
                # Stop if we have enough jobs
                if len(all_jobs) >= request.max_results:
                    break
                    
            except Exception as e:
                self.logger.error(f"Error scraping from {url}: {e}")
                continue
        
        return all_jobs
    
    def get_supported_domains(self) -> List[str]:
        """Get list of supported domains"""
        domains = []
        for scraper in self.scrapers:
            if hasattr(scraper, 'supported_domains'):
                domains.extend(scraper.supported_domains)
            else:
                # Extract from can_handle_url logic
                if scraper.name == "Ashby":
                    domains.extend(["ashbyhq.com", "jobs.ashbyhq.com"])
                elif scraper.name == "Greenhouse":
                    domains.extend(["greenhouse.io", "boards.greenhouse.io"])
                elif scraper.name == "Lever":
                    domains.extend(["lever.co", "jobs.lever.co"])
                elif scraper.name == "Stripe":
                    domains.extend(["stripe.com", "jobs.stripe.com"])
                elif scraper.name == "Plaid":
                    domains.extend(["plaid.com", "jobs.plaid.com"])
        
        return domains 