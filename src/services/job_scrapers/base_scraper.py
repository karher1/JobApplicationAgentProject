from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
from src.models.schemas import JobPosition, JobSearchRequest
import logging

logger = logging.getLogger(__name__)

class BaseJobScraper(ABC):
    """Base class for all job board scrapers"""
    
    def __init__(self):
        self.name = self.__class__.__name__
        self.logger = logging.getLogger(f"scraper.{self.name}")
    
    @abstractmethod
    async def scrape_jobs(self, url: str, request: JobSearchRequest) -> List[JobPosition]:
        """Scrape jobs from a specific URL"""
        raise NotImplementedError("Each scraper must implement this method")
    
    @abstractmethod
    def can_handle_url(self, url: str) -> bool:
        """Check if this scraper can handle the given URL"""
        raise NotImplementedError("Each scraper must implement this method")
    
    def matches_search_criteria(self, job: JobPosition, request: JobSearchRequest) -> bool:
        """Check if a job matches the search criteria with improved matching logic"""
        try:
            # Create combined text for searching (title + company + location + description)
            job_text = f"{job.title} {job.company} {job.location or ''} {job.description_snippet or ''}".lower()
            
            # Check job titles with fuzzy/partial matching
            if request.job_titles:
                title_match = False
                for title in request.job_titles:
                    title_lower = title.lower()
                    # Exact match in title
                    if title_lower in job.title.lower():
                        title_match = True
                        break
                    # Partial match in combined text
                    if title_lower in job_text:
                        title_match = True
                        break
                    # Keyword-based matching for common variations
                    if self._matches_job_keywords(title_lower, job_text):
                        title_match = True
                        break
                
                if not title_match:
                    self.logger.debug(f"Job title mismatch: '{job.title}' doesn't match {request.job_titles}")
                    return False
            
            # Check locations with more flexible matching
            if request.locations:
                location_match = False
                for location in request.locations:
                    location_lower = location.lower()
                    job_location_lower = (job.location or "").lower()
                    
                    # Exact match
                    if location_lower in job_location_lower:
                        location_match = True
                        break
                    # Remote matching
                    if location_lower == "remote" and any(remote_kw in job_location_lower for remote_kw in ["remote", "distributed", "anywhere"]):
                        location_match = True
                        break
                
                if not location_match:
                    self.logger.debug(f"Location mismatch: '{job.location}' doesn't match {request.locations}")
                    return False
            
            # Check remote preference
            if request.remote_only:
                job_location_lower = (job.location or "").lower()
                if not any(remote_kw in job_location_lower for remote_kw in ["remote", "distributed", "anywhere"]):
                    self.logger.debug(f"Remote filter: '{job.location}' is not remote")
                    return False
            
            self.logger.debug(f"Job matches criteria: {job.title} at {job.company}")
            return True
            
        except Exception as e:
            self.logger.warning(f"Error checking search criteria: {e}")
            return True  # Default to include if there's an error
    
    def _matches_job_keywords(self, search_title: str, job_text: str) -> bool:
        """Check if job matches based on keyword variations"""
        # Define keyword mappings for common job title variations
        keyword_mappings = {
            "qa engineer": ["quality assurance", "qa", "test engineer", "testing", "quality engineer"],
            "sdet": ["software development engineer in test", "software test engineer", "test automation", "automation engineer"],
            "software engineer in test": ["sdet", "test engineer", "qa engineer", "automation engineer"],
            "test engineer": ["qa engineer", "sdet", "testing", "quality assurance"],
            "automation engineer": ["test automation", "qa automation", "sdet"],
            "quality assurance": ["qa", "testing", "quality engineer"],
            "software engineer": ["developer", "engineer", "programming"],
            "data scientist": ["data analyst", "machine learning", "ml engineer"],
            "product manager": ["pm", "product owner", "product lead"]
        }
        
        # Check if any keywords match
        if search_title in keyword_mappings:
            for keyword in keyword_mappings[search_title]:
                if keyword in job_text:
                    return True
        
        # Check individual words for partial matching
        search_words = search_title.split()
        if len(search_words) > 1:
            # If searching for "QA Engineer", check if both "qa" and "engineer" appear
            word_matches = sum(1 for word in search_words if word in job_text)
            if word_matches >= len(search_words) * 0.7:  # 70% of words must match
                return True
        
        return False
    
    def create_job_position(self, title: str, company: str, location: str, 
                           url: str, description: str = "", **kwargs) -> JobPosition:
        """Create a JobPosition object with common fields"""
        return JobPosition(
            title=title,
            company=company,
            location=location,
            url=url,
            job_board=self.name,
            description_snippet=description,
            posted_date=datetime.now().strftime("%Y-%m-%d"),
            salary_range=kwargs.get('salary_range'),
            job_type=kwargs.get('job_type', 'Full-time'),
            remote_option=kwargs.get('remote_option', 'Remote' if 'remote' in location.lower() else 'On-site')
        ) 