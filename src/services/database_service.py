import os
import logging
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
import uuid
from supabase import create_client, Client
from src.models.schemas import JobPosition, JobSearchRequest, SearchStatistics, ApplicationStatistics, ServiceHealth
from src.core.config import get_settings

logger = logging.getLogger(__name__)

class DatabaseService:
    """Service for handling database operations with Supabase"""
    
    def __init__(self):
        settings = get_settings()
        self.supabase_url = settings.supabase_url
        self.supabase_key = settings.supabase_anon_key
        self.client: Optional[Client] = None
        
    async def initialize(self):
        """Initialize Supabase client"""
        try:
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Supabase URL and key must be set in environment variables")
            
            self.client = create_client(self.supabase_url, self.supabase_key)
            logger.info("Supabase client initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing Supabase client: {e}")
            raise
    
    async def health_check(self) -> ServiceHealth:
        """Check database health"""
        try:
            if not self.client:
                return ServiceHealth(status="unhealthy", message="Client not initialized")
            
            # Test connection with a simple query
            response = self.client.table("jobs").select("id").limit(1).execute()
            return ServiceHealth(status="healthy", message="Database connection successful")
        except Exception as e:
            return ServiceHealth(status="unhealthy", message=str(e))
    
    # Add missing methods that digest service expects
    async def execute_query(self, query: str, params: tuple = None) -> List[Dict[str, Any]]:
        """Execute a raw SQL query (simplified implementation for Supabase)"""
        try:
            if not self.client:
                raise ValueError("Database client not initialized")
            
            # This is a simplified implementation - in production, you'd want to use
            # Supabase's RPC functions or proper table operations
            logger.warning("execute_query called - this is a simplified implementation")
            
            # For now, return empty result
            return []
            
        except Exception as e:
            logger.error(f"Error executing query: {e}")
            raise
    
    async def get_user_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile by user ID"""
        try:
            if not self.client:
                raise ValueError("Database client not initialized")
            
            # Try to get user profile from user_profiles table
            response = self.client.table("user_profiles").select("*").eq("user_id", user_id).execute()
            
            if response.data:
                return response.data[0]
            
            # If no profile exists, try to get basic user info
            user_response = self.client.table("users").select("*").eq("id", user_id).execute()
            if user_response.data:
                user = user_response.data[0]
                return {
                    "id": user["id"],
                    "name": f"{user.get('first_name', '')} {user.get('last_name', '')}".strip(),
                    "email": user.get("email", ""),
                    "skills": [],
                    "experience": []
                }
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting user profile: {e}")
            raise
    
    async def get_job(self, job_id: str) -> Optional[Dict[str, Any]]:
        """Get job by ID"""
        try:
            if not self.client:
                raise ValueError("Database client not initialized")
            
            response = self.client.table("jobs").select("*").eq("id", job_id).execute()
            
            if response.data:
                return response.data[0]
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting job: {e}")
            raise

    async def store_job_search_results(self, jobs: List[JobPosition], search_request: JobSearchRequest):
        """Store job search results in database"""
        try:
            if not self.client:
                raise ValueError("Database client not initialized")
            
            # Store search metadata
            search_id = str(uuid.uuid4())
            search_data = {
                "id": search_id,
                "job_titles": search_request.job_titles,
                "locations": search_request.locations,
                "max_results": search_request.max_results,
                "job_boards": search_request.job_boards,
                "remote_only": search_request.remote_only,
                "total_jobs_found": len(jobs),
                "created_at": datetime.now().isoformat()
            }
            
            self.client.table("job_searches").insert(search_data).execute()
            
            # Store individual jobs
            for job in jobs:
                job_data = {
                    "id": str(uuid.uuid4()),
                    "search_id": search_id,
                    "title": job.title,
                    "company": job.company,
                    "location": job.location,
                    "url": job.url,
                    "job_board": job.job_board,
                    "posted_date": job.posted_date,
                    "salary_range": job.salary_range,
                    "job_type": job.job_type,
                    "remote_option": job.remote_option,
                    "description_snippet": job.description_snippet,
                    "created_at": datetime.now().isoformat(),
                    "updated_at": datetime.now().isoformat()
                }
                
                self.client.table("jobs").insert(job_data).execute()
            
            logger.info(f"Stored {len(jobs)} jobs in database")
            
        except Exception as e:
            logger.error(f"Error storing job search results: {e}")
            raise
    
    async def get_jobs(self, limit: int = 50, offset: int = 0, 
                      job_board: Optional[str] = None, location: Optional[str] = None) -> List[JobPosition]:
        """Get jobs from database with optional filtering"""
        try:
            if not self.client:
                raise ValueError("Database client not initialized")
            
            query = self.client.table("jobs").select("*")
            
            if job_board:
                query = query.eq("job_board", job_board)
            
            if location:
                query = query.eq("location", location)
            
            response = query.range(offset, offset + limit - 1).execute()
            
            jobs = []
            for row in response.data:
                job = JobPosition(
                    id=row["id"],
                    title=row["title"],
                    company=row["company"],
                    location=row["location"],
                    url=row["url"],
                    job_board=row["job_board"],
                    posted_date=row["posted_date"],
                    salary_range=row["salary_range"],
                    job_type=row["job_type"],
                    remote_option=row["remote_option"],
                    description_snippet=row["description_snippet"],
                    created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                    updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
                )
                jobs.append(job)
            
            return jobs
            
        except Exception as e:
            logger.error(f"Error retrieving jobs: {e}")
            raise
    
    async def get_job_by_id(self, job_id: str) -> Optional[JobPosition]:
        """Get a specific job by ID"""
        try:
            if not self.client:
                raise ValueError("Database client not initialized")
            
            response = self.client.table("jobs").select("*").eq("id", job_id).execute()
            
            if not response.data:
                return None
            
            row = response.data[0]
            job = JobPosition(
                id=row["id"],
                title=row["title"],
                company=row["company"],
                location=row["location"],
                url=row["url"],
                job_board=row["job_board"],
                posted_date=row["posted_date"],
                salary_range=row["salary_range"],
                job_type=row["job_type"],
                remote_option=row["remote_option"],
                description_snippet=row["description_snippet"],
                created_at=datetime.fromisoformat(row["created_at"]) if row["created_at"] else None,
                updated_at=datetime.fromisoformat(row["updated_at"]) if row["updated_at"] else None
            )
            
            return job
            
        except Exception as e:
            logger.error(f"Error retrieving job {job_id}: {e}")
            raise
    
    async def store_application_result(self, job_id: str, result: Dict[str, Any], form_data: Dict[str, Any]):
        """Store job application result"""
        try:
            if not self.client:
                raise ValueError("Database client not initialized")
            
            application_data = {
                "id": str(uuid.uuid4()),
                "job_id": job_id,
                "success": result.get("success", False),
                "filled_fields": result.get("filled_fields", []),
                "failed_fields": result.get("failed_fields", []),
                "error_message": result.get("error_message"),
                "form_data": form_data,
                "created_at": datetime.now().isoformat()
            }
            
            self.client.table("job_applications").insert(application_data).execute()
            logger.info(f"Stored application result for job {job_id}")
            
        except Exception as e:
            logger.error(f"Error storing application result: {e}")
            raise
    
    async def get_search_statistics(self) -> SearchStatistics:
        """Get job search statistics"""
        try:
            if not self.client:
                raise ValueError("Database client not initialized")
            
            # Get total searches
            searches_response = self.client.table("job_searches").select("id").execute()
            total_searches = len(searches_response.data)
            
            # Get total jobs found
            jobs_response = self.client.table("jobs").select("id").execute()
            total_jobs_found = len(jobs_response.data)
            
            # Calculate average jobs per search
            average_jobs_per_search = total_jobs_found / total_searches if total_searches > 0 else 0
            
            # Get most searched titles
            titles_response = self.client.table("job_searches").select("job_titles").execute()
            title_counts = {}
            for search in titles_response.data:
                for title in search["job_titles"]:
                    title_counts[title] = title_counts.get(title, 0) + 1
            
            most_searched_titles = [
                {"title": title, "count": count} 
                for title, count in sorted(title_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            # Get most searched locations
            locations_response = self.client.table("job_searches").select("locations").execute()
            location_counts = {}
            for search in locations_response.data:
                for location in search["locations"]:
                    location_counts[location] = location_counts.get(location, 0) + 1
            
            most_searched_locations = [
                {"location": location, "count": count} 
                for location, count in sorted(location_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            # Get search timeline (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            timeline_response = self.client.table("job_searches").select("created_at").gte("created_at", thirty_days_ago).execute()
            
            search_timeline = []
            for search in timeline_response.data:
                search_timeline.append({
                    "date": search["created_at"][:10],  # Just the date part
                    "count": 1
                })
            
            return SearchStatistics(
                total_searches=total_searches,
                total_jobs_found=total_jobs_found,
                average_jobs_per_search=average_jobs_per_search,
                most_searched_titles=most_searched_titles,
                most_searched_locations=most_searched_locations,
                search_timeline=search_timeline
            )
            
        except Exception as e:
            logger.error(f"Error getting search statistics: {e}")
            raise
    
    async def get_application_statistics(self) -> ApplicationStatistics:
        """Get job application statistics"""
        try:
            if not self.client:
                raise ValueError("Database client not initialized")
            
            # Get all applications
            applications_response = self.client.table("job_applications").select("*").execute()
            applications = applications_response.data
            
            total_applications = len(applications)
            successful_applications = len([app for app in applications if app["success"]])
            failed_applications = total_applications - successful_applications
            success_rate = successful_applications / total_applications if total_applications > 0 else 0
            
            # Calculate average application time (placeholder - would need timing data)
            average_application_time = 0.0
            
            # Get most applied companies
            company_counts = {}
            for app in applications:
                # Get job details to find company
                job_response = self.client.table("jobs").select("company").eq("id", app["job_id"]).execute()
                if job_response.data:
                    company = job_response.data[0]["company"]
                    company_counts[company] = company_counts.get(company, 0) + 1
            
            most_applied_companies = [
                {"company": company, "count": count} 
                for company, count in sorted(company_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ]
            
            # Get application timeline (last 30 days)
            thirty_days_ago = (datetime.now() - timedelta(days=30)).isoformat()
            timeline_response = self.client.table("job_applications").select("created_at").gte("created_at", thirty_days_ago).execute()
            
            application_timeline = []
            for app in timeline_response.data:
                application_timeline.append({
                    "date": app["created_at"][:10],  # Just the date part
                    "count": 1
                })
            
            return ApplicationStatistics(
                total_applications=total_applications,
                successful_applications=successful_applications,
                failed_applications=failed_applications,
                success_rate=success_rate,
                average_application_time=average_application_time,
                most_applied_companies=most_applied_companies,
                application_timeline=application_timeline
            )
            
        except Exception as e:
            logger.error(f"Error getting application statistics: {e}")
            raise 