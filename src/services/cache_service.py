import os
import json
import hashlib
import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio
from functools import wraps

from src.models.schemas import JobPosition, JobSearchRequest

logger = logging.getLogger(__name__)

class CacheService:
    """Service for caching job search results and company scrapes"""
    
    def __init__(self, cache_duration_hours: int = 6):
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache_dir = "data/cache"
        self._ensure_cache_dir()
        
    def _ensure_cache_dir(self):
        """Ensure cache directory exists"""
        os.makedirs(self.cache_dir, exist_ok=True)
    
    def _generate_cache_key(self, prefix: str, data: Dict[str, Any]) -> str:
        """Generate a cache key from data"""
        # Create a deterministic string representation
        data_str = json.dumps(data, sort_keys=True, default=str)
        hash_obj = hashlib.md5(data_str.encode())
        cache_key = f"{prefix}_{hash_obj.hexdigest()}"
        logger.info(f"Generated cache key: {cache_key} for data: {data}")
        return cache_key
    
    def _get_cache_file_path(self, cache_key: str) -> str:
        """Get the file path for a cache key"""
        return os.path.join(self.cache_dir, f"{cache_key}.json")
    
    def _is_cache_valid(self, cache_data: Dict[str, Any]) -> bool:
        """Check if cache data is still valid"""
        if 'timestamp' not in cache_data:
            return False
        
        cache_time = datetime.fromisoformat(cache_data['timestamp'])
        is_valid = datetime.now() - cache_time < self.cache_duration
        logger.info(f"Cache validity check: {is_valid}, cache_time: {cache_time}, now: {datetime.now()}")
        return is_valid
    
    async def get_cached_jobs(self, request: JobSearchRequest, companies: List[str] = None) -> Optional[List[JobPosition]]:
        """Get cached job search results"""
        try:
            # Create cache key from request
            cache_data = {
                'job_titles': request.job_titles,
                'locations': request.locations,
                'companies': companies or [],
                'max_results': request.max_results,
                'remote_only': request.remote_only,
                'job_boards': request.job_boards or []
            }
            
            cache_key = self._generate_cache_key("job_search", cache_data)
            cache_file = self._get_cache_file_path(cache_key)
            
            logger.info(f"Looking for cache file: {cache_file}")
            
            if not os.path.exists(cache_file):
                logger.info(f"Cache file not found: {cache_file}")
                return None
            
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            if not self._is_cache_valid(cache_data):
                # Cache expired, remove it
                logger.info(f"Cache expired, removing: {cache_file}")
                os.remove(cache_file)
                return None
            
            # Convert back to JobPosition objects
            jobs = []
            for job_data in cache_data.get('jobs', []):
                job = JobPosition(**job_data)
                jobs.append(job)
            
            logger.info(f"Cache hit: Found {len(jobs)} cached jobs")
            return jobs
            
        except Exception as e:
            logger.error(f"Error reading cache: {e}")
            return None
    
    async def cache_jobs(self, request: JobSearchRequest, jobs: List[JobPosition], companies: List[str] = None):
        """Cache job search results"""
        try:
            cache_data = {
                'job_titles': request.job_titles,
                'locations': request.locations,
                'companies': companies or [],
                'max_results': request.max_results,
                'remote_only': request.remote_only,
                'job_boards': request.job_boards or [],
                'timestamp': datetime.now().isoformat(),
                'jobs': [job.model_dump() if hasattr(job, 'model_dump') else job.dict() for job in jobs]
            }
            
            cache_key = self._generate_cache_key("job_search", cache_data)
            cache_file = self._get_cache_file_path(cache_key)
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Cached {len(jobs)} jobs with key: {cache_key}")
            
        except Exception as e:
            logger.error(f"Error caching jobs: {e}")
    
    async def get_cached_company_jobs(self, company: str, request: JobSearchRequest) -> Optional[List[JobPosition]]:
        """Get cached jobs for a specific company"""
        try:
            cache_data = {
                'company': company,
                'job_titles': request.job_titles,
                'locations': request.locations,
                'max_results': request.max_results,
                'remote_only': request.remote_only
            }
            
            cache_key = self._generate_cache_key("company_jobs", cache_data)
            cache_file = self._get_cache_file_path(cache_key)
            
            if not os.path.exists(cache_file):
                return None
            
            with open(cache_file, 'r') as f:
                cache_data = json.load(f)
            
            if not self._is_cache_valid(cache_data):
                os.remove(cache_file)
                return None
            
            jobs = []
            for job_data in cache_data.get('jobs', []):
                job = JobPosition(**job_data)
                jobs.append(job)
            
            logger.info(f"Cache hit: Found {len(jobs)} cached jobs for {company}")
            return jobs
            
        except Exception as e:
            logger.error(f"Error reading company cache: {e}")
            return None
    
    async def cache_company_jobs(self, company: str, request: JobSearchRequest, jobs: List[JobPosition]):
        """Cache jobs for a specific company"""
        try:
            cache_data = {
                'company': company,
                'job_titles': request.job_titles,
                'locations': request.locations,
                'max_results': request.max_results,
                'remote_only': request.remote_only,
                'timestamp': datetime.now().isoformat(),
                'jobs': [job.model_dump() if hasattr(job, 'model_dump') else job.dict() for job in jobs]
            }
            
            cache_key = self._generate_cache_key("company_jobs", cache_data)
            cache_file = self._get_cache_file_path(cache_key)
            
            with open(cache_file, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            logger.info(f"Cached {len(jobs)} jobs for {company}")
            
        except Exception as e:
            logger.error(f"Error caching company jobs: {e}")
    
    def clear_expired_cache(self):
        """Clear expired cache files"""
        try:
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        with open(file_path, 'r') as f:
                            cache_data = json.load(f)
                        
                        if not self._is_cache_valid(cache_data):
                            os.remove(file_path)
                            logger.info(f"Removed expired cache: {filename}")
                    except Exception as e:
                        logger.error(f"Error checking cache file {filename}: {e}")
                        
        except Exception as e:
            logger.error(f"Error clearing expired cache: {e}")
    
    def clear_all_cache(self):
        """Clear all cache files"""
        try:
            removed_count = 0
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    try:
                        os.remove(file_path)
                        removed_count += 1
                        logger.info(f"Removed cache file: {filename}")
                    except Exception as e:
                        logger.error(f"Error removing cache file {filename}: {e}")
            
            logger.info(f"Cleared all cache files: {removed_count} files removed")
            return removed_count
                        
        except Exception as e:
            logger.error(f"Error clearing all cache: {e}")
            return 0
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics"""
        try:
            total_files = 0
            total_size = 0
            expired_files = 0
            
            for filename in os.listdir(self.cache_dir):
                if filename.endswith('.json'):
                    file_path = os.path.join(self.cache_dir, filename)
                    total_files += 1
                    total_size += os.path.getsize(file_path)
                    
                    try:
                        with open(file_path, 'r') as f:
                            cache_data = json.load(f)
                        
                        if not self._is_cache_valid(cache_data):
                            expired_files += 1
                    except:
                        expired_files += 1
            
            return {
                'total_files': total_files,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'expired_files': expired_files,
                'cache_duration_hours': self.cache_duration.total_seconds() / 3600
            }
            
        except Exception as e:
            logger.error(f"Error getting cache stats: {e}")
            return {}

# Cache decorator for async functions
def cache_result(cache_service: CacheService, cache_type: str = "job_search"):
    """Decorator to cache function results"""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Try to get from cache first
            if cache_type == "job_search" and len(args) > 0:
                request = args[0]  # First argument should be JobSearchRequest
                companies = kwargs.get('companies', [])
                cached_result = await cache_service.get_cached_jobs(request, companies)
                if cached_result is not None:
                    return cached_result
            
            # If not in cache, execute function
            result = await func(*args, **kwargs)
            
            # Cache the result
            if cache_type == "job_search" and len(args) > 0:
                request = args[0]
                companies = kwargs.get('companies', [])
                await cache_service.cache_jobs(request, result, companies)
            
            return result
        return wrapper
    return decorator 