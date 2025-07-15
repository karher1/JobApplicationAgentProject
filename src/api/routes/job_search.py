from fastapi import APIRouter, HTTPException, Depends
from typing import List, Optional, Dict, Any
from pydantic import BaseModel
from src.models.schemas import JobPosition, JobSearchRequest, COMPANY_DOMAINS, COMPANY_DISPLAY_NAMES
from src.services.job_search_service import JobSearchService
from src.services.database_service import DatabaseService
from src.services.vector_service import VectorService
from src.services.llm_service import LLMService
from src.services.job_scrapers.company_scraper import CompanyScraper
import os
import logging

router = APIRouter(prefix="/jobs", tags=["job-search"])

# File logger for company_scraper.log
log_file = os.path.join(os.path.dirname(__file__), '../../../company_scraper.log')
file_handler = logging.FileHandler(log_file, mode='a')
file_handler.setLevel(logging.INFO)
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
file_handler.setFormatter(formatter)
logger = logging.getLogger("job_search_logger")
if not any(isinstance(h, logging.FileHandler) and h.baseFilename == file_handler.baseFilename for h in logger.handlers):
    logger.addHandler(file_handler)
logger.setLevel(logging.INFO)

class CompanyJobSearchRequest(BaseModel):
    """Request model for company-specific job search"""
    job_titles: List[str]
    companies: List[str]  # Max 5 companies
    locations: List[str] = ["Remote"]
    max_results: int = 10
    remote_only: bool = False

class CacheStatsResponse(BaseModel):
    """Response model for cache statistics"""
    total_files: int
    total_size_mb: float
    expired_files: int
    cache_duration_hours: float

# Dependency injection
def get_job_search_service() -> JobSearchService:
    from src.api.main import job_search_service
    return job_search_service

@router.post("/search", response_model=List[JobPosition])
async def search_jobs(
    request: JobSearchRequest,
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """Search for jobs across multiple job boards using plugin-based scrapers with caching"""
    try:
        jobs = await job_search_service.search_jobs(request)
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs: {str(e)}")

@router.post("/search/sample", response_model=List[JobPosition])
async def get_sample_jobs(
    request: JobSearchRequest,
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """Get sample jobs quickly without web scraping - for testing purposes"""
    try:
        # Get sample jobs directly without web scraping
        sample_jobs = job_search_service._get_sample_jobs(request)
        return sample_jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting sample jobs: {str(e)}")

@router.post("/search/companies", response_model=List[JobPosition])
async def search_jobs_by_companies(
    request: CompanyJobSearchRequest,
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """Search for jobs in specific companies - fast and targeted with caching"""
    try:
        # Limit to 5 companies for performance
        if len(request.companies) > 5:
            raise HTTPException(status_code=400, detail="Maximum 5 companies allowed")
        
        # Create company scraper
        company_scraper = CompanyScraper()
        
        # Convert to JobSearchRequest for compatibility
        job_request = JobSearchRequest(
            job_titles=request.job_titles,
            locations=request.locations,
            max_results=request.max_results,
            remote_only=request.remote_only
        )
        
        # Search for jobs in specific companies
        jobs = await company_scraper.scrape_jobs_from_companies(request.companies, job_request)
        
        # Close the scraper session
        await company_scraper.close()
        
        # Store results in database if jobs were found (optional)
        if jobs:
            try:
                await job_search_service.database_service.store_job_search_results(jobs, job_request)
            except Exception as e:
                # Database storage is optional, don't fail the request
                pass
            
            # Store job embeddings in vector database (optional)
            try:
                await job_search_service.vector_service.store_job_embeddings(jobs)
            except Exception as e:
                # Vector storage is optional, don't fail the request
                pass
        
        return jobs
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs by companies: {str(e)}")

@router.get("/companies", response_model=Dict[str, Any])
async def get_supported_companies():
    """Get list of supported companies with their domains"""
    try:
        return {
            "domains": COMPANY_DOMAINS,
            "display_names": COMPANY_DISPLAY_NAMES,
            "total_companies": len(COMPANY_DOMAINS)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting companies: {str(e)}")

@router.get("/company-domains", response_model=Dict[str, List[str]])
async def get_company_domains():
    """Get company domains organized by category"""
    try:
        return COMPANY_DOMAINS
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting company domains: {str(e)}")

@router.get("/cache/stats", response_model=CacheStatsResponse)
async def get_cache_stats(
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """Get cache statistics"""
    try:
        stats = await job_search_service.get_cache_stats()
        return CacheStatsResponse(**stats)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache stats: {str(e)}")

@router.delete("/cache/clear")
async def clear_cache(
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """Clear expired cache files"""
    try:
        await job_search_service.clear_cache()
        return {"message": "Cache cleared successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing cache: {str(e)}")

@router.get("/cache/info")
async def get_cache_info(
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """Get detailed cache information"""
    try:
        stats = await job_search_service.get_cache_stats()
        return {
            "cache_stats": stats,
            "cache_location": "data/cache",
            "cache_duration_hours": 6,
            "description": "Job search results are cached for 6 hours to improve performance"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting cache info: {str(e)}")

@router.post("/search/url", response_model=List[JobPosition])
async def search_jobs_from_url(
    url: str,
    request: JobSearchRequest,
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """Search for jobs from a specific URL using the appropriate scraper"""
    try:
        jobs = await job_search_service.search_jobs_from_url(url, request)
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs from URL: {str(e)}")

@router.post("/search/urls", response_model=List[JobPosition])
async def search_jobs_from_urls(
    urls: List[str],
    request: JobSearchRequest,
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """Search for jobs from multiple URLs"""
    try:
        jobs = await job_search_service.search_jobs_from_multiple_urls(urls, request)
        return jobs
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error searching jobs from URLs: {str(e)}")

@router.get("/scrapers")
async def get_available_scrapers(
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """Get list of available scrapers and supported domains"""
    try:
        scrapers = job_search_service.scraper_factory.get_all_scrapers()
        domains = job_search_service.scraper_factory.get_supported_domains()
        
        return {
            "scrapers": [{"name": scraper.name, "type": scraper.__class__.__name__} for scraper in scrapers],
            "supported_domains": domains
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting scrapers: {str(e)}")

@router.get("/test/scraper/{scraper_name}")
async def test_scraper(
    scraper_name: str,
    job_search_service: JobSearchService = Depends(get_job_search_service)
):
    """Test a specific scraper with sample data"""
    try:
        scraper = job_search_service.scraper_factory.get_scraper_by_name(scraper_name)
        if not scraper:
            raise HTTPException(status_code=404, detail=f"Scraper {scraper_name} not found")
        
        # Create a test request
        test_request = JobSearchRequest(
            job_titles=["Software Engineer", "QA Engineer"],
            locations=["Remote", "San Francisco"],
            max_results=5,
            remote_only=False
        )
        
        # Get sample URLs for this scraper
        sample_urls = job_search_service.sample_job_urls.get(scraper_name.lower(), [])
        if not sample_urls:
            return {"message": f"No sample URLs available for {scraper_name}"}
        
        # Test with first sample URL
        test_url = sample_urls[0]
        jobs = await scraper.scrape_jobs(test_url, test_request)
        
        return {
            "scraper": scraper_name,
            "test_url": test_url,
            "jobs_found": len(jobs),
            "jobs": [{"title": job.title, "company": job.company, "location": job.location} for job in jobs]
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error testing scraper: {str(e)}") 