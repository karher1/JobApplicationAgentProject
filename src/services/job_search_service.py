import os
import logging
import time
import requests
from typing import List, Dict, Any, Optional
from urllib.parse import urlparse, urljoin
from datetime import datetime
import json
import re

from src.models.schemas import JobPosition, JobSearchRequest
from src.services.database_service import DatabaseService
from src.services.vector_service import VectorService
from src.services.llm_service import LLMService
from src.services.job_scrapers.scraper_factory import JobScraperFactory
from src.services.cache_service import CacheService

logger = logging.getLogger(__name__)

class JobSearchService:
    def __init__(self, database_service, vector_service, llm_service):
        self.database_service = database_service
        self.vector_service = vector_service
        self.llm_service = llm_service
        self.scraper_factory = JobScraperFactory()
        self.cache_service = CacheService(cache_duration_hours=6)  # 6 hour cache

    async def search_jobs(self, request: JobSearchRequest) -> List[JobPosition]:
        """Search for jobs using plugin-based scrapers with caching"""
        jobs: List[JobPosition] = []
        start_time = time.time()
        
        try:
            # Check cache first for company-specific searches
            if request.companies and len(request.companies) > 0:
                companies = request.companies[:5]  # Limit to 5 companies
                
                # Try to get from cache first
                cached_jobs = await self.cache_service.get_cached_jobs(request, companies)
                if cached_jobs:
                    logger.info(f"Cache hit: Returning {len(cached_jobs)} cached jobs")
                    return cached_jobs[:request.max_results] if request.max_results else cached_jobs
                
                # If not in cache, scrape from companies
                from src.services.job_scrapers.company_scraper import CompanyScraper
                company_scraper = CompanyScraper()
                try:
                    jobs = await company_scraper.scrape_jobs_from_companies(companies, request)
                    await company_scraper.close()
                    
                    # Cache the results
                    if jobs:
                        await self.cache_service.cache_jobs(request, jobs, companies)
                        
                except Exception as e:
                    logger.error(f"Error in company-specific search: {e}")
                    # Fall back to general search if company search fails
                    jobs = await self.scraper_factory.scrape_jobs_from_multiple_sources([], request)
            else:
                # For general searches (no companies specified), use company scraper with defaults
                # Check cache first
                cached_jobs = await self.cache_service.get_cached_jobs(request)
                if cached_jobs:
                    logger.info(f"Cache hit: Returning {len(cached_jobs)} cached jobs")
                    return cached_jobs[:request.max_results] if request.max_results else cached_jobs
                
                # If not in cache, use company scraper which has diverse default companies
                from src.services.job_scrapers.company_scraper import CompanyScraper
                company_scraper = CompanyScraper()
                try:
                    jobs = await company_scraper.scrape_jobs_from_companies([], request)
                    await company_scraper.close()
                    
                    # Cache the results
                    if jobs:
                        await self.cache_service.cache_jobs(request, jobs)
                except Exception as e:
                    logger.error(f"Error in general company search: {e}")
                    # Fall back to scraper factory as last resort
                    jobs = await self.scraper_factory.scrape_jobs_from_multiple_sources([], request)
                    if jobs:
                        await self.cache_service.cache_jobs(request, jobs)
            
            # Store results in database
            if jobs:
                await self.database_service.store_job_search_results(jobs, request)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Job search completed in {elapsed_time:.2f} seconds, found {len(jobs)} jobs")
            
            return jobs[:request.max_results] if request.max_results else jobs
            
        except Exception as e:
            logger.error(f"Error in search_jobs: {e}")
            return []

    async def search_jobs_by_companies(self, request: JobSearchRequest, companies: List[str]) -> List[JobPosition]:
        """Search for jobs in specific companies with caching"""
        jobs: List[JobPosition] = []
        start_time = time.time()
        
        try:
            # Limit to 5 companies for performance
            limited_companies = companies[:5]
            
            # Check cache first
            cached_jobs = await self.cache_service.get_cached_jobs(request, limited_companies)
            if cached_jobs:
                logger.info(f"Cache hit: Returning {len(cached_jobs)} cached jobs for companies")
                return cached_jobs[:request.max_results] if request.max_results else cached_jobs
            
            # If not in cache, scrape from companies
            from src.services.job_scrapers.company_scraper import CompanyScraper
            company_scraper = CompanyScraper()
            
            try:
                jobs = await company_scraper.scrape_jobs_from_companies(limited_companies, request)
                await company_scraper.close()
                
                # Cache the results
                if jobs:
                    await self.cache_service.cache_jobs(request, jobs, limited_companies)
                    
            except Exception as e:
                logger.error(f"Error in company-specific search: {e}")
                return []
            
            # Store results in database
            if jobs:
                await self.database_service.store_job_search_results(jobs, request)
            
            elapsed_time = time.time() - start_time
            logger.info(f"Company job search completed in {elapsed_time:.2f} seconds, found {len(jobs)} jobs")
            
            return jobs[:request.max_results] if request.max_results else jobs
            
        except Exception as e:
            logger.error(f"Error in search_jobs_by_companies: {e}")
            return []

    async def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        return self.cache_service.get_cache_stats()
    
    async def clear_cache(self):
        """Clear all cache files"""
        removed_count = self.cache_service.clear_all_cache()
        logger.info(f"Cache cleared: {removed_count} files removed")

    async def get_job_recommendations(self, user_profile: Dict[str, Any], limit: int = 10) -> List[JobPosition]:
        """Get personalized job recommendations for a user based on their profile"""
        try:
            # Use vector service to find similar jobs based on user profile
            job_matches = await self.vector_service.find_job_matches_for_user(
                user_profile=user_profile,
                limit=limit
            )
            
            # Convert vector service results to JobPosition objects
            job_positions = []
            for match in job_matches:
                job_position = JobPosition(
                    id=match.get('id', ''),
                    title=match.get('title', ''),
                    company=match.get('company', ''),
                    location=match.get('location', ''),
                    url=match.get('url', ''),
                    job_board=match.get('job_board', 'Unknown'),
                    posted_date=None,
                    salary_range=None,
                    job_type=None,
                    remote_option=None,
                    description_snippet=match.get('description', ''),
                    is_applied=False,
                    is_favorite=False,
                    created_at=datetime.now()
                )
                job_positions.append(job_position)
            
            logger.info(f"Generated {len(job_positions)} job recommendations for user")
            return job_positions
            
        except Exception as e:
            logger.error(f"Error getting job recommendations: {e}")
            return []

    # Add methods as needed 