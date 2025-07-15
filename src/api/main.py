from fastapi import FastAPI, HTTPException, BackgroundTasks, Depends, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import os
import logging
from datetime import datetime, timedelta, date
import asyncio
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

# Import our modules
from src.services.job_search_service import JobSearchService
from src.services.job_application_service import JobApplicationService
from src.services.database_service import DatabaseService
from src.services.vector_service import VectorService
from src.services.llm_service import LLMService
from src.services.user_profile_service import UserProfileService
from src.services.job_extraction_service import JobExtractionService
from src.services.digest_service import DigestService
from src.services.pending_application_service import PendingApplicationService
from src.services.auth_service import AuthService
from src.services.chatbot_service import ChatbotService
from src.services.ai_content_service import AIContentService
from src.services.resume_parsing_service import ResumeParsingService
from src.api.routes.job_search import router as job_search_router
from src.api.routes.resume_review import router as resume_review_router
from src.api.routes.chatbot import router as chatbot_router
from src.api.middleware.auth_middleware import get_current_user_id
from src.models.schemas import (
    JobSearchRequest, JobSearchResponse, JobPosition,
    JobApplicationRequest, JobApplicationResponse,
    BatchApplicationRequest,
    FormExtractionRequest, FormExtractionResponse
)
from src.models.user_profile import (
    User, UserCreate, UserUpdate, UserProfile,
    UserPreferences, UserPreferencesCreate, UserPreferencesUpdate,
    Resume, ResumeCreate, ResumeUpdate,
    Skill, UserSkill, UserSkillCreate, UserSkillUpdate,
    WorkExperience, WorkExperienceCreate, WorkExperienceUpdate,
    Education, EducationCreate, EducationUpdate,
    Certification, CertificationCreate, CertificationUpdate,
    ApplicationHistory, ApplicationHistoryCreate, ApplicationHistoryUpdate,
    SkillAddRequest, ResumeUploadRequest, JobMatchRequest, JobMatchResponse
)
from src.models.job_extraction import (
    JobExtractionRequest, JobExtractionResponse,
    BatchExtractionRequest, BatchExtractionResponse,
    EnhancedJobPosition, ExtractionStats
)
from src.models.digest import (
    DigestRequest, DigestResponse, DigestType, DigestPreferences,
    GenerateDigestRequest, BatchDigestRequest, DigestStats
)
from src.models.pending_applications import (
    PendingApplication, PendingApplicationCreate, PendingApplicationUpdate,
    PendingApplicationReviewRequest, PendingApplicationReviewResponse,
    PendingApplicationListResponse, PendingApplicationStatus, PendingApplicationPriority
)
from src.models.auth import UserLogin, UserRegister, Token, AuthResponse
from src.models.ai_content import (
    CoverLetterRequest, EssayQuestionRequest, ShortResponseRequest,
    BatchContentRequest, ContentGenerationResult, BatchContentResponse,
    JobData, FieldContext
)

# Load environment variables
from dotenv import load_dotenv
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize rate limiter
limiter = Limiter(key_func=get_remote_address)

# Initialize FastAPI app
app = FastAPI(
    title="Job Application Automation API",
    description="AI-powered job search and application automation system",
    version="1.0.0"
)

# Add rate limiting middleware
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
app.add_middleware(SlowAPIMiddleware)

# Add CORS middleware
ALLOWED_ORIGINS = [
    "http://localhost:3000",  # Next.js development server
    "http://127.0.0.1:3000",  # Alternative localhost
    "https://your-production-domain.com",  # Add your production domain here
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "PATCH"],
    allow_headers=["*"],
)

# Include routers
app.include_router(job_search_router, prefix="/api/v2")
app.include_router(resume_review_router, prefix="/api")
app.include_router(chatbot_router, prefix="/api")

# Initialize services
database_service = DatabaseService()
vector_service = VectorService()
llm_service = LLMService()
user_profile_service = UserProfileService()
job_extraction_service = JobExtractionService(llm_service)
job_search_service = JobSearchService(database_service, vector_service, llm_service)
job_application_service = JobApplicationService(database_service, llm_service)
digest_service = DigestService(database_service, llm_service, vector_service)
pending_application_service = PendingApplicationService()
resume_parsing_service = ResumeParsingService()
auth_service = AuthService()
chatbot_service = ChatbotService(llm_service, database_service, user_profile_service, job_search_service)
ai_content_service = AIContentService(llm_service)

@app.on_event("startup")
async def startup_event():
    """Initialize services on startup"""
    try:
        # Initialize required services
        await database_service.initialize()
        await llm_service.initialize()
        await user_profile_service.initialize()
        await job_extraction_service.initialize()
        await pending_application_service.initialize()
        await auth_service.initialize()
        await chatbot_service.initialize()
        await ai_content_service.initialize()
        
        # Initialize optional services
        try:
            await vector_service.initialize()
            logger.info("Vector service initialized successfully")
        except Exception as e:
            logger.warning(f"Vector service initialization failed (optional): {e}")
        
        # Attach services to app state for route access
        app.state.database_service = database_service
        app.state.llm_service = llm_service
        app.state.vector_service = vector_service
        app.state.user_profile_service = user_profile_service
        app.state.job_extraction_service = job_extraction_service
        app.state.job_search_service = job_search_service
        app.state.job_application_service = job_application_service
        app.state.digest_service = digest_service
        app.state.pending_application_service = pending_application_service
        app.state.auth_service = auth_service
        app.state.chatbot_service = chatbot_service
        app.state.ai_content_service = ai_content_service
        
        logger.info("All services initialized successfully")
    except Exception as e:
        logger.error(f"Error initializing services: {e}")
        raise

@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "message": "Job Application Automation API",
        "status": "running",
        "timestamp": datetime.now().isoformat()
    }

@app.get("/health")
async def health_check():
    """Detailed health check"""
    try:
        health_status = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "services": {
                "database": await database_service.health_check(),
                "llm": await llm_service.health_check(),
                "user_profile": await user_profile_service.health_check(),
                "job_extraction": await job_extraction_service.health_check(),
                "pending_applications": await pending_application_service.health_check(),
                "chatbot": await chatbot_service.health_check(),
                "ai_content": await ai_content_service.health_check()
            }
        }
        
        # Add vector service health if available
        try:
            health_status["services"]["vector_db"] = await vector_service.health_check()
        except Exception as e:
            health_status["services"]["vector_db"] = {"status": "unavailable", "message": str(e)}
        
        return health_status
    except Exception as e:
        return {
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "error": str(e)
        }

# Helper function to check resume requirement
async def check_resume_requirement(user_id: int) -> bool:
    """Check if user has a primary resume uploaded"""
    try:
        primary_resume = await user_profile_service.get_primary_resume(user_id)
        return primary_resume is not None
    except Exception:
        return False

# Job Search Endpoints
@app.post("/api/jobs/search", response_model=JobSearchResponse)
@limiter.limit("10/minute")
async def search_jobs(request: Request, search_request: JobSearchRequest):
    """Search for jobs using multiple sources"""
    try:
        companies_info = f" in companies: {search_request.companies}" if search_request.companies else ""
        logger.info(f"Searching for jobs: {search_request.job_titles} in {search_request.locations}{companies_info}")
        
        # Search for jobs using enhanced job search service
        jobs = await job_search_service.search_jobs(search_request)
        
        # Store results in database
        await database_service.store_job_search_results(jobs, search_request)
        
        # Store job embeddings in vector database (optional)
        try:
            await vector_service.store_job_embeddings(jobs)
        except Exception as e:
            logger.warning(f"Failed to store job embeddings (optional): {e}")
        
        # Ensure jobs are properly serialized
        serialized_jobs = []
        for job in jobs:
            if hasattr(job, 'model_dump'):
                # Pydantic v2
                serialized_jobs.append(JobPosition(**job.model_dump()))
            elif hasattr(job, 'dict'):
                # Pydantic v1
                serialized_jobs.append(JobPosition(**job.dict()))
            else:
                # Already a dict or other format
                serialized_jobs.append(job)
        
        companies_query = f", Companies: {search_request.companies}" if search_request.companies else ""
        return JobSearchResponse(
            search_query=f"Titles: {search_request.job_titles}, Locations: {search_request.locations}{companies_query}",
            total_jobs_found=len(jobs),
            jobs=serialized_jobs,
            search_timestamp=datetime.now().isoformat(),
            success=True
        )
    except Exception as e:
        logger.error(f"Error searching jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/search-and-apply", response_model=Dict[str, Any])
@limiter.limit("5/minute")
async def search_and_apply_to_jobs(
    request: Request,
    user_id: str,
    search_request: JobSearchRequest,
    background_tasks: BackgroundTasks,
    current_user_id: int = Depends(get_current_user_id)
):
    """Search for jobs and automatically apply to matching ones"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        
        # Security check: ensure user can only access their own data
        if user_id_int != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only access your own data"
            )
        
        # Check if user has a primary resume uploaded
        if not await check_resume_requirement(user_id_int):
            raise HTTPException(
                status_code=400, 
                detail="A primary resume must be uploaded before applying to jobs. Please upload a resume first."
            )
        
        # Get user profile
        user_profile = await user_profile_service.get_complete_user_profile(user_id_int)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        logger.info(f"Searching and applying for user {user_id_int}: {search_request.job_titles} in {search_request.locations}")
        
        # Search for jobs
        jobs = await job_search_service.search_jobs(search_request)
        
        if not jobs:
            return {
                "user_id": user_id_int,
                "search_results": {
                    "total_jobs_found": 0,
                    "jobs": []
                },
                "application_results": {
                    "total_applications": 0,
                    "successful_applications": 0,
                    "failed_applications": 0
                }
            }
        
        # Filter jobs based on user preferences
        user_preferences = await user_profile_service.get_user_preferences(user_id_int)
        if user_preferences:
            # Apply user preferences filtering
            filtered_jobs = await job_search_service.filter_jobs_by_criteria(
                jobs,
                required_keywords=user_preferences.technology_preferences,
                preferred_companies=user_preferences.preferred_companies,
                remote_only=user_preferences.remote_preference == "remote"
            )
        else:
            filtered_jobs = jobs
        
        # Limit applications based on user preferences
        max_applications = user_preferences.application_limit_per_day if user_preferences else 10
        jobs_to_apply = filtered_jobs[:max_applications]
        
        # Get user's primary resume
        primary_resume = await user_profile_service.get_primary_resume(user_id_int)
        resume_id = primary_resume.id if primary_resume else None
        
        # Create pending applications instead of auto-submitting
        application_results = []
        for job in jobs_to_apply:
            try:
                pending_app = await pending_application_service.create_pending_application(
                    user_id=user_id_int,
                    job=job,
                    form_data={},
                    cover_letter=None,
                    resume_id=resume_id,
                    priority=PendingApplicationPriority.MEDIUM,
                    notes="Created via search-and-apply"
                )
                
                application_results.append({
                    "job_id": job.id,
                    "job_title": job.title,
                    "company": job.company,
                    "success": True,
                    "message": f"Application created and pending approval (ID: {pending_app.id})",
                    "error": None
                })
                
            except Exception as e:
                application_results.append({
                    "job_id": job.id,
                    "job_title": job.title,
                    "company": job.company,
                    "success": False,
                    "message": "Application creation failed",
                    "error": str(e)
                })
        
        successful_applications = sum(1 for r in application_results if r["success"])
        
        return {
            "user_id": user_id_int,
            "search_results": {
                "total_jobs_found": len(jobs),
                "filtered_jobs": len(filtered_jobs),
                "jobs_applied_to": len(jobs_to_apply)
            },
            "application_results": {
                "total_applications": len(application_results),
                "successful_applications": successful_applications,
                "failed_applications": len(application_results) - successful_applications,
                "results": application_results
            }
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error in search and apply: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs", response_model=List[JobPosition])
async def get_jobs(
    limit: int = 50,
    offset: int = 0,
    job_board: Optional[str] = None,
    location: Optional[str] = None
):
    """Get stored jobs with optional filtering"""
    try:
        jobs = await database_service.get_jobs(limit, offset, job_board, location)
        return jobs
    except Exception as e:
        logger.error(f"Error retrieving jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/extraction-stats", response_model=ExtractionStats)
async def get_extraction_statistics():
    """Get job extraction statistics"""
    try:
        stats = await job_extraction_service.get_extraction_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error retrieving extraction stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/{job_id}", response_model=JobPosition)
async def get_job(job_id: str):
    """Get a specific job by ID"""
    try:
        job = await database_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        return job
    except Exception as e:
        logger.error(f"Error retrieving job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Job Application Endpoints
@app.post("/api/jobs/{job_id}/apply", response_model=JobApplicationResponse)
async def apply_to_job(
    job_id: str,
    request: JobApplicationRequest,
    background_tasks: BackgroundTasks
):
    """Apply to a specific job"""
    try:
        # Convert user_id to int
        user_id = int(request.user_id)
        
        # Check if user has a primary resume uploaded
        if not await check_resume_requirement(user_id):
            raise HTTPException(
                status_code=400, 
                detail="A primary resume must be uploaded before applying to jobs. Please upload a resume first."
            )
        
        # Get job details
        job = await database_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get user profile
        user_profile = await user_profile_service.get_complete_user_profile(user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Create pending application instead of auto-submitting
        primary_resume = await user_profile_service.get_primary_resume(user_id)
        resume_id = primary_resume.id if primary_resume else None
        
        pending_app = await pending_application_service.create_pending_application(
            user_id=user_id,
            job=job,
            form_data=request.form_data,
            cover_letter=request.cover_letter,
            resume_id=resume_id,
            priority=PendingApplicationPriority.MEDIUM,
            notes="Created via job application endpoint"
        )
        
        return JobApplicationResponse(
            job_id=job_id,
            success=True,
            message=f"Application created and pending approval (ID: {pending_app.id})",
            filled_fields=[],
            failed_fields=[],
            error_message=None,
            application_timestamp=datetime.now().isoformat()
        )
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error applying to job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/batch-apply", response_model=Dict[str, Any])
async def batch_apply_to_jobs(
    request: BatchApplicationRequest,
    background_tasks: BackgroundTasks
):
    """Apply to multiple jobs in batch"""
    try:
        # Check if user has a primary resume uploaded
        if not await check_resume_requirement(request.user_id):
            raise HTTPException(
                status_code=400, 
                detail="A primary resume must be uploaded before applying to jobs. Please upload a resume first."
            )
        
        # Get user profile
        user_profile = await user_profile_service.get_complete_user_profile(request.user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Get user's primary resume
        primary_resume = await user_profile_service.get_primary_resume(request.user_id)
        resume_id = primary_resume.id if primary_resume else None
        
        results = []
        for job_id in request.job_ids:
            try:
                # Get job details
                job = await database_service.get_job(job_id)
                if not job:
                    results.append({
                        "job_id": job_id,
                        "success": False,
                        "error": "Job not found"
                    })
                    continue
                
                # Create pending application instead of auto-submitting
                pending_app = await pending_application_service.create_pending_application(
                    user_id=request.user_id,
                    job=job,
                    form_data=request.form_data,
                    cover_letter=None,
                    resume_id=resume_id,
                    priority=PendingApplicationPriority.MEDIUM,
                    notes="Created via batch application"
                )
                
                results.append({
                    "job_id": job_id,
                    "success": True,
                    "message": f"Application created and pending approval (ID: {pending_app.id})",
                    "error": None
                })
                
            except Exception as e:
                results.append({
                    "job_id": job_id,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "total_jobs": len(request.job_ids),
            "successful_applications": sum(1 for r in results if r["success"]),
            "failed_applications": sum(1 for r in results if not r["success"]),
            "results": results
        }
    except Exception as e:
        logger.error(f"Error in batch application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/batch-apply", response_model=Dict[str, Any])
async def batch_apply_to_jobs_for_user(
    user_id: str,
    request: List[str],  # List of job IDs
    background_tasks: BackgroundTasks
):
    """Apply to multiple jobs in batch for a specific user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        
        # Check if user has a primary resume uploaded
        if not await check_resume_requirement(user_id_int):
            raise HTTPException(
                status_code=400, 
                detail="A primary resume must be uploaded before applying to jobs. Please upload a resume first."
            )
        
        # Get user profile
        user_profile = await user_profile_service.get_complete_user_profile(user_id_int)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Get user's primary resume
        primary_resume = await user_profile_service.get_primary_resume(user_id_int)
        resume_id = primary_resume.id if primary_resume else None
        
        results = []
        for job_id in request:
            try:
                # Get job details
                job = await database_service.get_job(job_id)
                if not job:
                    results.append({
                        "job_id": job_id,
                        "success": False,
                        "error": "Job not found"
                    })
                    continue
                
                # Create pending application instead of auto-submitting
                pending_app = await pending_application_service.create_pending_application(
                    user_id=user_id_int,
                    job=job,
                    form_data={},
                    cover_letter=None,
                    resume_id=resume_id,
                    priority=PendingApplicationPriority.MEDIUM,
                    notes="Created via user batch application"
                )
                
                results.append({
                    "job_id": job_id,
                    "success": True,
                    "message": f"Application created and pending approval (ID: {pending_app.id})",
                    "error": None
                })
                
            except Exception as e:
                results.append({
                    "job_id": job_id,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "user_id": user_id_int,
            "total_jobs": len(request),
            "successful_applications": sum(1 for r in results if r["success"]),
            "failed_applications": sum(1 for r in results if not r["success"]),
            "results": results
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error in batch application for user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Form Extraction Endpoints
@app.post("/api/forms/extract", response_model=FormExtractionResponse)
async def extract_form_fields(request: FormExtractionRequest):
    """Extract form fields from a job application page"""
    try:
        fields = await job_application_service.extract_form_fields(request.url)
        return FormExtractionResponse(
            url=request.url,
            form_fields=fields,
            success=True
        )
    except Exception as e:
        logger.error(f"Error extracting form fields: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Similar Jobs Endpoints
@app.post("/api/jobs/similar")
async def find_similar_jobs(
    job_description: str,
    limit: int = 10
):
    """Find similar jobs using vector similarity"""
    try:
        similar_jobs = await vector_service.find_similar_jobs(job_description, limit)
        return {
            "query": job_description,
            "similar_jobs": similar_jobs,
            "total_found": len(similar_jobs)
        }
    except Exception as e:
        logger.error(f"Error finding similar jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Analytics Endpoints
@app.get("/api/analytics/search-stats")
async def get_search_statistics():
    """Get job search statistics"""
    try:
        stats = await database_service.get_search_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting search stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/analytics/application-stats")
async def get_application_statistics():
    """Get job application statistics"""
    try:
        stats = await database_service.get_application_statistics()
        return stats
    except Exception as e:
        logger.error(f"Error getting application stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Job Extraction Endpoints
@app.post("/api/jobs/extract", response_model=JobExtractionResponse)
async def extract_job_data(request: JobExtractionRequest):
    """Extract structured data from job description"""
    try:
        result = await job_extraction_service.extract_job_data(request)
        return result
    except Exception as e:
        logger.error(f"Error extracting job data: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/batch-extract", response_model=BatchExtractionResponse)
async def batch_extract_jobs(request: BatchExtractionRequest):
    """Extract data from multiple job descriptions"""
    try:
        result = await job_extraction_service.batch_extract_jobs(request)
        return result
    except Exception as e:
        logger.error(f"Error batch extracting jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/enhanced", response_model=List[EnhancedJobPosition])
async def get_enhanced_jobs(
    limit: int = 50,
    offset: int = 0,
    min_confidence: float = 0.0,
    job_type: Optional[str] = None,
    remote_type: Optional[str] = None,
    experience_level: Optional[str] = None
):
    """Get enhanced job data with extracted information"""
    try:
        jobs = await job_extraction_service.get_enhanced_jobs(
            limit=limit,
            offset=offset,
            min_confidence=min_confidence,
            job_type=job_type,
            remote_type=remote_type,
            experience_level=experience_level
        )
        return jobs
    except Exception as e:
        logger.error(f"Error getting enhanced jobs: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/jobs/enhanced/{job_id}", response_model=EnhancedJobPosition)
async def get_enhanced_job(job_id: str):
    """Get enhanced data for a specific job"""
    try:
        job = await job_extraction_service.get_enhanced_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Enhanced job not found")
        return job
    except Exception as e:
        logger.error(f"Error getting enhanced job: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/jobs/{job_id}/validate")
async def validate_job_extraction(job_id: str):
    """Validate and improve job extraction results"""
    try:
        result = await job_extraction_service.validate_extraction(job_id)
        return result
    except Exception as e:
        logger.error(f"Error validating job extraction: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# User Profile Endpoints
@app.post("/api/users", response_model=User)
async def create_user(user_data: UserCreate):
    """Create a new user"""
    try:
        user = await user_profile_service.create_user(user_data)
        return user
    except Exception as e:
        logger.error(f"Error creating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}", response_model=User)
async def get_user(user_id: str):
    """Get user by ID"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        user = await user_profile_service.get_user(user_id_int)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/users/{user_id}", response_model=User)
async def update_user(user_id: str, user_data: UserUpdate):
    """Update user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        user = await user_profile_service.update_user(user_id_int, user_data)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error updating user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Authentication Endpoints
@app.post("/api/auth/register", response_model=AuthResponse)
async def register_user(user_data: UserRegister):
    """Register a new user with password hashing"""
    try:
        response = await auth_service.register_user(user_data)
        return response
    except Exception as e:
        logger.error(f"Error registering user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/login", response_model=AuthResponse)
async def login_user(login_data: UserLogin):
    """Authenticate user and return JWT token"""
    try:
        response = await auth_service.login_user(login_data)
        return response
    except Exception as e:
        logger.error(f"Error logging in user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/change-password", response_model=AuthResponse)
async def change_password(
    current_password: str,
    new_password: str,
    current_user_id: int = Depends(get_current_user_id)
):
    """Change user password"""
    try:
        response = await auth_service.change_password(current_user_id, current_password, new_password)
        return response
    except Exception as e:
        logger.error(f"Error changing password: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/auth/verify")
async def verify_token(current_user_id: int = Depends(get_current_user_id)):
    """Verify JWT token and return user information"""
    try:
        # Get user profile data
        user = await user_profile_service.get_user_by_id(current_user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        
        return {
            "success": True,
            "user_id": current_user_id,
            "email": user.email,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "token_valid": True
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error verifying token: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/profile", response_model=UserProfile)
async def get_user_profile(user_id: str):
    """Get complete user profile with all related data"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        profile = await user_profile_service.get_complete_user_profile(user_id_int)
        if not profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        return profile
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting user profile: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/preferences", response_model=UserPreferences)
async def create_user_preferences(user_id: str, preferences_data: UserPreferencesCreate):
    """Create user preferences"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        preferences_data.user_id = user_id_int
        preferences = await user_profile_service.create_user_preferences(preferences_data)
        return preferences
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error creating user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/preferences", response_model=UserPreferences)
async def get_user_preferences(user_id: str):
    """Get user preferences"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        preferences = await user_profile_service.get_user_preferences(user_id_int)
        if not preferences:
            raise HTTPException(status_code=404, detail="User preferences not found")
        return preferences
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/users/{user_id}/preferences", response_model=UserPreferences)
async def update_user_preferences(user_id: str, preferences_data: UserPreferencesUpdate):
    """Update user preferences"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        preferences = await user_profile_service.update_user_preferences(user_id_int, preferences_data)
        if not preferences:
            raise HTTPException(status_code=404, detail="User preferences not found")
        return preferences
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error updating user preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/resumes", response_model=Resume)
async def upload_resume(user_id: str, upload_request: ResumeUploadRequest):
    """Upload a resume for a user"""
    try:
        logger.info(f"Uploading resume for user_id: {user_id} (type: {type(user_id)})")
        logger.info(f"Upload request: {upload_request}")
        
        # Convert user_id to int
        try:
            user_id_int = int(user_id)
            logger.info(f"Successfully converted user_id to int: {user_id_int}")
        except ValueError as ve:
            logger.error(f"ValueError converting user_id '{user_id}' to int: {ve}")
            raise HTTPException(status_code=400, detail=f"Invalid user_id format: {user_id}")
        
        # Check if user_profile_service is initialized
        if not user_profile_service:
            logger.error("User profile service not initialized")
            raise HTTPException(status_code=500, detail="User profile service not available")
        
        resume = await user_profile_service.upload_resume(user_id_int, upload_request)
        return resume
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Error uploading resume: {e}")
        logger.error(f"Exception type: {type(e)}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/api/users/{user_id}/resumes", response_model=List[Resume])
async def get_user_resumes(user_id: str):
    """Get all resumes for a user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        resumes = await user_profile_service.get_user_resumes(user_id_int)
        return resumes
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting user resumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/resumes/primary", response_model=Resume)
async def get_primary_resume(user_id: str):
    """Get user's primary resume"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        resume = await user_profile_service.get_primary_resume(user_id_int)
        if not resume:
            raise HTTPException(status_code=404, detail="Primary resume not found")
        return resume
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting primary resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/users/{user_id}/resumes/{resume_id}/primary")
async def set_primary_resume(user_id: str, resume_id: str):
    """Set a resume as primary"""
    try:
        # Convert IDs to int
        user_id_int = int(user_id)
        resume_id_int = int(resume_id)
        success = await user_profile_service.set_primary_resume(user_id_int, resume_id_int)
        if not success:
            raise HTTPException(status_code=404, detail="Resume not found")
        return {"message": "Primary resume updated successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error(f"Error setting primary resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/resumes/{resume_id}/parse")
async def parse_resume_and_populate_profile(user_id: str, resume_id: str):
    """Parse a resume and auto-populate user profile with extracted information"""
    try:
        # Convert IDs to int
        user_id_int = int(user_id)
        resume_id_int = int(resume_id)
        
        # Get the resume
        resumes = await user_profile_service.get_user_resumes(user_id_int)
        resume = next((r for r in resumes if r.id == resume_id_int), None)
        
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        # Parse the resume
        parsing_result = await resume_parsing_service.parse_resume(resume)
        
        if not parsing_result["success"]:
            raise HTTPException(status_code=400, detail=f"Failed to parse resume: {parsing_result.get('error', 'Unknown error')}")
        
        # Populate profile with parsed data
        population_result = await resume_parsing_service.populate_user_profile_from_resume(
            user_id_int, 
            parsing_result["extracted_data"], 
            user_profile_service
        )
        
        return {
            "success": True,
            "parsing_result": parsing_result,
            "population_result": population_result,
            "message": f"Resume parsed successfully. Added {population_result['skills_added']} skills, {population_result['work_experience_added']} work experiences, and {population_result['education_added']} education entries."
        }
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error(f"Error parsing resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/users/{user_id}/resumes/{resume_id}")
async def delete_resume(user_id: str, resume_id: str):
    """Delete a resume"""
    try:
        # Convert IDs to int
        user_id_int = int(user_id)
        resume_id_int = int(resume_id)
        
        # Delete the resume
        success = await user_profile_service.delete_resume(user_id_int, resume_id_int)
        
        if not success:
            raise HTTPException(status_code=404, detail="Resume not found")
        
        return {"success": True, "message": "Resume deleted successfully"}
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user ID or resume ID format")
    except Exception as e:
        logger.error(f"Error deleting resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/skills", response_model=UserSkill)
async def add_user_skill(user_id: str, skill_request: SkillAddRequest):
    """Add a skill to a user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        user_skill = await user_profile_service.add_skill_to_user(user_id_int, skill_request)
        return user_skill
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error adding user skill: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/skills", response_model=List[UserSkill])
async def get_user_skills(user_id: str):
    """Get all skills for a user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        skills = await user_profile_service.get_user_skills(user_id_int)
        return skills
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting user skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/skills", response_model=List[Skill])
async def get_available_skills():
    """Get all available skills in the system"""
    try:
        skills = await user_profile_service.get_available_skills()
        return skills
    except Exception as e:
        logger.error(f"Error getting available skills: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/work-experience", response_model=WorkExperience)
async def add_work_experience(user_id: str, work_data: WorkExperienceCreate):
    """Add work experience to a user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        work_data.user_id = user_id_int
        work_exp = await user_profile_service.add_work_experience(work_data)
        return work_exp
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error adding work experience: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/work-experience", response_model=List[WorkExperience])
async def get_user_work_experience(user_id: str):
    """Get all work experience for a user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        work_exp = await user_profile_service.get_user_work_experience(user_id_int)
        return work_exp
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting work experience: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/users/{user_id}/work-experience/{work_id}")
async def delete_work_experience(user_id: str, work_id: str):
    """Delete a work experience entry"""
    try:
        # Convert IDs to int
        user_id_int = int(user_id)
        work_id_int = int(work_id)
        
        # Delete the work experience
        success = await user_profile_service.delete_work_experience(work_id_int)
        
        if success:
            return {"success": True, "message": "Work experience deleted successfully"}
        else:
            raise HTTPException(status_code=404, detail="Work experience not found")
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid ID format")
    except Exception as e:
        logger.error(f"Error deleting work experience: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/education", response_model=Education)
async def add_education(user_id: str, education_data: EducationCreate):
    """Add education to a user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        education_data.user_id = user_id_int
        education = await user_profile_service.add_education(education_data)
        return education
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error adding education: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/education", response_model=List[Education])
async def get_user_education(user_id: str):
    """Get all education for a user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        education = await user_profile_service.get_user_education(user_id_int)
        return education
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting education: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/applications", response_model=ApplicationHistory)
async def add_application_history(user_id: str, app_data: ApplicationHistoryCreate):
    """Add application history for a user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        app_data.user_id = user_id_int
        app_history = await user_profile_service.add_application_history(app_data)
        return app_history
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error adding application history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/applications", response_model=List[ApplicationHistory])
async def get_user_application_history(user_id: str):
    """Get all application history for a user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        app_history = await user_profile_service.get_user_application_history(user_id_int)
        return app_history
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting application history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/users/{user_id}/match-jobs", response_model=List[JobMatchResponse])
async def match_jobs_for_user(user_id: str, request: JobMatchRequest):
    """Find job matches for a user based on their profile"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        request.user_id = user_id_int
        
        # Get user profile
        user_profile = await user_profile_service.get_complete_user_profile(user_id_int)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Get job matches using vector similarity
        # Convert UserProfile object to dictionary
        user_profile_dict = user_profile.model_dump() if hasattr(user_profile, 'model_dump') else user_profile.dict()
        
        matches = await vector_service.find_job_matches_for_user(
            user_profile=user_profile_dict,
            job_description=request.job_description,
            limit=request.limit
        )
        
        # Convert to response format
        job_matches = []
        for match in matches:
            job_matches.append(JobMatchResponse(
                job_id=match.get('id', ''),
                title=match.get('title', ''),
                company=match.get('company', ''),
                match_score=match.get('similarity', 0.0),
                match_reasons=[],  # Would be calculated based on match criteria
                skills_match=[],   # Would be extracted from match analysis
                experience_match=True  # Would be determined from profile comparison
            ))
        
        return job_matches
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error matching jobs for user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/job-recommendations", response_model=List[JobPosition])
async def get_job_recommendations_for_user(
    user_id: str,
    limit: int = 10,
    job_board: Optional[str] = None
):
    """Get personalized job recommendations for a user"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        
        # Get user profile
        user_profile = await user_profile_service.get_complete_user_profile(user_id_int)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Convert UserProfile object to dictionary
        user_profile_dict = user_profile.model_dump() if hasattr(user_profile, 'model_dump') else user_profile.dict()
        
        # Get job recommendations
        recommendations = await job_search_service.get_job_recommendations(user_profile_dict, limit)
        
        # Filter by job board if specified
        if job_board:
            recommendations = [job for job in recommendations if job.job_board.lower() == job_board.lower()]
        
        return recommendations
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting job recommendations for user: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Digest Endpoints
@app.post("/api/v1/digest/generate", response_model=DigestResponse)
async def generate_digest(request: GenerateDigestRequest):
    """Generate a digest for a user"""
    try:
        # Convert user_id to int
        user_id_int = int(request.user_id)
        
        digest_request = DigestRequest(
            user_id=user_id_int,
            digest_type=request.digest_type,
            date=request.custom_date,
            include_job_matches=True,
            include_applications=True,
            include_insights=True,
            include_stats=True
        )
        
        response = await digest_service.generate_digest(digest_request)
        return response
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error generating digest: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/v1/digest/generate/batch")
async def generate_digests_batch(request: BatchDigestRequest):
    """Generate digests for multiple users"""
    try:
        # Convert user_ids to int
        user_ids_int = [int(uid) for uid in request.user_ids]
        
        results = []
        for user_id in user_ids_int:
            try:
                digest_request = DigestRequest(
                    user_id=user_id,
                    digest_type=request.digest_type
                )
                response = await digest_service.generate_digest(digest_request)
                results.append({
                    "user_id": user_id,
                    "success": response.success,
                    "error": response.error_message
                })
            except Exception as e:
                results.append({
                    "user_id": user_id,
                    "success": False,
                    "error": str(e)
                })
        
        return {
            "total_users": len(user_ids_int),
            "successful_digests": sum(1 for r in results if r["success"]),
            "failed_digests": sum(1 for r in results if not r["success"]),
            "results": results
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error generating batch digests: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/digest/schedules")
async def get_digest_schedules():
    """Get all active digest schedules"""
    try:
        schedules = await digest_service.get_digest_schedules()
        return {"schedules": schedules}
    except Exception as e:
        logger.error(f"Error getting digest schedules: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/digest/stats")
async def get_digest_stats(start_date: str = None, end_date: str = None):
    """Get digest statistics"""
    try:
        # Parse dates
        start = datetime.strptime(start_date, "%Y-%m-%d").date() if start_date else date.today() - timedelta(days=30)
        end = datetime.strptime(end_date, "%Y-%m-%d").date() if end_date else date.today()
        
        stats = await digest_service.get_digest_stats(start, end)
        return stats
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    except Exception as e:
        logger.error(f"Error getting digest stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/v1/digest/preferences/{user_id}")
async def update_digest_preferences(user_id: str, preferences: DigestPreferences):
    """Update user's digest preferences"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        preferences.user_id = user_id_int
        
        # This would update the digest_preferences table
        # For now, return success
        return {"message": "Preferences updated successfully"}
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error updating digest preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/v1/digest/preferences/{user_id}")
async def get_digest_preferences(user_id: str):
    """Get user's digest preferences"""
    try:
        # Convert user_id to int
        user_id_int = int(user_id)
        preferences = await digest_service._get_user_preferences(user_id_int)
        return preferences
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting digest preferences: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Pending Application Endpoints
@app.post("/api/pending-applications", response_model=PendingApplication)
async def create_pending_application(
    user_id: int,
    job_id: str,
    form_data: Dict[str, Any],
    cover_letter: Optional[str] = None,
    priority: PendingApplicationPriority = PendingApplicationPriority.MEDIUM,
    notes: Optional[str] = None
):
    """Create a new pending application that requires approval"""
    try:
        # Check if user has a primary resume uploaded
        if not await check_resume_requirement(user_id):
            raise HTTPException(
                status_code=400, 
                detail="A primary resume must be uploaded before applying to jobs. Please upload a resume first."
            )
        
        # Get job details
        job = await database_service.get_job(job_id)
        if not job:
            raise HTTPException(status_code=404, detail="Job not found")
        
        # Get user's primary resume
        primary_resume = await user_profile_service.get_primary_resume(user_id)
        resume_id = primary_resume.id if primary_resume else None
        
        # Create pending application
        pending_app = await pending_application_service.create_pending_application(
            user_id=user_id,
            job=job,
            form_data=form_data,
            cover_letter=cover_letter,
            resume_id=resume_id,
            priority=priority,
            notes=notes
        )
        
        logger.info(f"Created pending application for {job.title} at {job.company}")
        return pending_app
        
    except Exception as e:
        logger.error(f"Error creating pending application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/pending-applications", response_model=PendingApplicationListResponse)
async def get_user_pending_applications(
    user_id: str,
    status: Optional[PendingApplicationStatus] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get pending applications for a specific user"""
    try:
        user_id_int = int(user_id)
        applications = await pending_application_service.get_pending_applications(
            user_id=user_id_int,
            status=status,
            limit=limit,
            offset=offset
        )
        return applications
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting user pending applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pending-applications", response_model=PendingApplicationListResponse)
async def get_all_pending_applications(
    status: Optional[PendingApplicationStatus] = None,
    limit: int = 50,
    offset: int = 0
):
    """Get all pending applications (for admin/reviewer use)"""
    try:
        applications = await pending_application_service.get_pending_applications(
            user_id=None,
            status=status,
            limit=limit,
            offset=offset
        )
        return applications
        
    except Exception as e:
        logger.error(f"Error getting pending applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pending-applications/for-review", response_model=List[PendingApplication])
async def get_applications_for_review(
    limit: int = 50,
    priority_filter: Optional[PendingApplicationPriority] = None
):
    """Get applications that need review (pending status)"""
    try:
        applications = await pending_application_service.get_applications_for_review(
            limit=limit,
            priority_filter=priority_filter
        )
        return applications
        
    except Exception as e:
        logger.error(f"Error getting applications for review: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/pending-applications/{application_id}", response_model=PendingApplication)
async def get_pending_application(application_id: int):
    """Get a specific pending application"""
    try:
        application = await pending_application_service.get_pending_application(application_id)
        if not application:
            raise HTTPException(status_code=404, detail="Pending application not found")
        return application
        
    except Exception as e:
        logger.error(f"Error getting pending application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pending-applications/{application_id}/review", response_model=PendingApplicationReviewResponse)
async def review_pending_application(
    application_id: int,
    reviewer_id: int,
    review_request: PendingApplicationReviewRequest
):
    """Review a pending application (approve/reject)"""
    try:
        review_response = await pending_application_service.review_pending_application(
            application_id=application_id,
            reviewer_id=reviewer_id,
            review_request=review_request
        )
        return review_response
        
    except Exception as e:
        logger.error(f"Error reviewing pending application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/pending-applications/{application_id}", response_model=PendingApplication)
async def update_pending_application(
    application_id: int,
    update_data: PendingApplicationUpdate
):
    """Update a pending application"""
    try:
        updated_app = await pending_application_service.update_pending_application(
            application_id=application_id,
            update_data=update_data
        )
        if not updated_app:
            raise HTTPException(status_code=404, detail="Pending application not found")
        return updated_app
        
    except Exception as e:
        logger.error(f"Error updating pending application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/pending-applications/{application_id}/cancel")
async def cancel_pending_application(
    application_id: int,
    user_id: int
):
    """Cancel a pending application"""
    try:
        success = await pending_application_service.cancel_pending_application(
            application_id=application_id,
            user_id=user_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Pending application not found or cannot be cancelled")
        
        return {"message": "Pending application cancelled successfully"}
        
    except Exception as e:
        logger.error(f"Error cancelling pending application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/pending-applications/{application_id}")
async def delete_pending_application(
    application_id: int,
    user_id: int
):
    """Delete a pending application (only if not submitted)"""
    try:
        success = await pending_application_service.delete_pending_application(
            application_id=application_id,
            user_id=user_id
        )
        if not success:
            raise HTTPException(status_code=404, detail="Pending application not found or cannot be deleted")
        
        return {"message": "Pending application deleted successfully"}
        
    except Exception as e:
        logger.error(f"Error deleting pending application: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/approved-applications", response_model=List[PendingApplication])
async def get_approved_applications(
    user_id: Optional[int] = None,
    limit: int = 50
):
    """Get approved applications ready for submission"""
    try:
        applications = await pending_application_service.get_approved_applications(
            user_id=user_id,
            limit=limit
        )
        return applications
        
    except Exception as e:
        logger.error(f"Error getting approved applications: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# Chatbot Endpoints
class ChatbotStartRequest(BaseModel):
    user_id: int
    conversation_type: str = "general"
    initial_message: Optional[str] = None

class ChatbotMessageRequest(BaseModel):
    user_id: int
    message: str

@app.post("/api/chatbot/start")
async def start_chatbot_conversation(request: ChatbotStartRequest):
    """Start a new chatbot conversation"""
    try:
        conversation_id = await chatbot_service.start_conversation(
            user_id=request.user_id,
            conversation_type=request.conversation_type,
            initial_message=request.initial_message
        )
        
        # Get the conversation to return initial messages
        conversation = await chatbot_service.get_conversation_history(conversation_id, request.user_id, limit=10)
        
        return {
            "conversation_id": conversation_id,
            "status": "started",
            "conversation": conversation
        }
    except Exception as e:
        logger.error(f"Error starting chatbot conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chatbot/{conversation_id}/message")
async def send_chatbot_message(
    conversation_id: str,
    request: ChatbotMessageRequest
):
    """Send a message to the chatbot"""
    try:
        response = await chatbot_service.send_message(
            conversation_id=conversation_id,
            user_id=request.user_id,
            message=request.message
        )
        
        return response
    except Exception as e:
        logger.error(f"Error sending chatbot message: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chatbot/{conversation_id}/history")
async def get_chatbot_conversation_history(
    conversation_id: str,
    user_id: int,
    limit: int = 50
):
    """Get conversation history"""
    try:
        history = await chatbot_service.get_conversation_history(
            conversation_id=conversation_id,
            user_id=user_id,
            limit=limit
        )
        
        return history
    except Exception as e:
        logger.error(f"Error getting conversation history: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/chatbot/conversations")
async def list_user_conversations(
    user_id: str,
    limit: int = 20
):
    """List user's chatbot conversations"""
    try:
        user_id_int = int(user_id)
        conversations = await chatbot_service.list_conversations(
            user_id=user_id_int,
            limit=limit
        )
        
        return {
            "conversations": conversations,
            "total": len(conversations)
        }
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error listing conversations: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chatbot/{conversation_id}/end")
async def end_chatbot_conversation(
    conversation_id: str,
    user_id: int
):
    """End a chatbot conversation"""
    try:
        success = await chatbot_service.end_conversation(
            conversation_id=conversation_id,
            user_id=user_id
        )
        
        return {
            "conversation_id": conversation_id,
            "status": "ended" if success else "error",
            "success": success
        }
    except Exception as e:
        logger.error(f"Error ending conversation: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/users/{user_id}/chatbot/stats")
async def get_chatbot_stats(user_id: str):
    """Get chatbot usage statistics for a user"""
    try:
        user_id_int = int(user_id)
        stats = await chatbot_service.get_conversation_stats(user_id_int)
        
        return stats
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid user_id format")
    except Exception as e:
        logger.error(f"Error getting chatbot stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))

# AI Content Generation Endpoints
@app.post("/api/ai/generate-cover-letter", response_model=ContentGenerationResult)
async def generate_cover_letter(
    request: CoverLetterRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    """Generate a personalized cover letter using AI"""
    try:
        # Security check: ensure user can only generate content for themselves
        if request.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only generate content for your own profile"
            )
        
        # Get user profile
        user_profile = await user_profile_service.get_complete_user_profile(current_user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Convert to dictionary for the service
        user_profile_dict = user_profile.model_dump() if hasattr(user_profile, 'model_dump') else user_profile.dict()
        job_data_dict = request.job_data.model_dump() if hasattr(request.job_data, 'model_dump') else request.job_data.dict()
        
        # Generate cover letter
        result = await ai_content_service.generate_cover_letter(
            user_profile=user_profile_dict,
            job_data=job_data_dict
        )
        
        # Convert result to response model
        return ContentGenerationResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating cover letter: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/answer-essay-question", response_model=ContentGenerationResult)
async def answer_essay_question(
    request: EssayQuestionRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    """Generate an answer to an essay question using AI"""
    try:
        # Security check
        if request.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only generate content for your own profile"
            )
        
        # Get user profile
        user_profile = await user_profile_service.get_complete_user_profile(current_user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Convert to dictionary for the service
        user_profile_dict = user_profile.model_dump() if hasattr(user_profile, 'model_dump') else user_profile.dict()
        job_data_dict = request.job_data.model_dump() if hasattr(request.job_data, 'model_dump') else request.job_data.dict()
        field_context_dict = None
        if request.field_context:
            field_context_dict = request.field_context.model_dump() if hasattr(request.field_context, 'model_dump') else request.field_context.dict()
        
        # Generate essay answer
        result = await ai_content_service.answer_essay_question(
            user_profile=user_profile_dict,
            job_data=job_data_dict,
            question=request.question,
            field_context=field_context_dict
        )
        
        # Convert result to response model
        return ContentGenerationResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating essay answer: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/generate-short-response", response_model=ContentGenerationResult)
async def generate_short_response(
    request: ShortResponseRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    """Generate a short response for a specific field using AI"""
    try:
        # Security check
        if request.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only generate content for your own profile"
            )
        
        # Get user profile
        user_profile = await user_profile_service.get_complete_user_profile(current_user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Convert to dictionary for the service
        user_profile_dict = user_profile.model_dump() if hasattr(user_profile, 'model_dump') else user_profile.dict()
        job_data_dict = request.job_data.model_dump() if hasattr(request.job_data, 'model_dump') else request.job_data.dict()
        
        # Generate short response
        result = await ai_content_service.generate_short_response(
            user_profile=user_profile_dict,
            job_data=job_data_dict,
            field_label=request.field_label,
            max_words=request.max_words or 50
        )
        
        # Convert result to response model
        return ContentGenerationResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating short response: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/generate-batch-content", response_model=BatchContentResponse)
async def generate_batch_content(
    request: BatchContentRequest,
    current_user_id: int = Depends(get_current_user_id)
):
    """Generate content for multiple fields in a single request"""
    try:
        # Security check
        if request.user_id != current_user_id:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access denied: You can only generate content for your own profile"
            )
        
        # Get user profile
        user_profile = await user_profile_service.get_complete_user_profile(current_user_id)
        if not user_profile:
            raise HTTPException(status_code=404, detail="User profile not found")
        
        # Convert to dictionary for the service
        user_profile_dict = user_profile.model_dump() if hasattr(user_profile, 'model_dump') else user_profile.dict()
        job_data_dict = request.job_data.model_dump() if hasattr(request.job_data, 'model_dump') else request.job_data.dict()
        
        results = []
        total_words = 0
        successful_generations = 0
        failed_generations = 0
        
        # Process each field
        for field in request.fields:
            try:
                # Determine the type of content to generate based on field
                if field.field_type == 'textarea' and field.label and len(field.label) > 20:
                    # Likely an essay question
                    result = await ai_content_service.answer_essay_question(
                        user_profile=user_profile_dict,
                        job_data=job_data_dict,
                        question=field.label,
                        field_context=field.model_dump() if hasattr(field, 'model_dump') else field.dict()
                    )
                elif field.field_type == 'textarea' and 'cover' in field.label.lower():
                    # Cover letter field
                    result = await ai_content_service.generate_cover_letter(
                        user_profile=user_profile_dict,
                        job_data=job_data_dict
                    )
                else:
                    # Short response
                    max_words = 50
                    if field.max_length:
                        # Estimate words from character limit (avg 5 chars per word)
                        max_words = min(max_words, field.max_length // 5)
                    
                    result = await ai_content_service.generate_short_response(
                        user_profile=user_profile_dict,
                        job_data=job_data_dict,
                        field_label=field.label,
                        max_words=max_words
                    )
                
                if result['success']:
                    successful_generations += 1
                    total_words += result.get('word_count', 0)
                else:
                    failed_generations += 1
                
                results.append(ContentGenerationResult(**result))
                
            except Exception as e:
                logger.error(f"Error generating content for field {field.label}: {e}")
                failed_generations += 1
                results.append(ContentGenerationResult(
                    success=False,
                    content_type="essay_answer",  # Default type
                    error=str(e),
                    field_label=field.label
                ))
        
        return BatchContentResponse(
            user_id=current_user_id,
            job_data=request.job_data,
            results=results,
            total_fields=len(request.fields),
            successful_generations=successful_generations,
            failed_generations=failed_generations,
            total_words=total_words
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating batch content: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/ai/extract-job-context")
async def extract_job_context(
    url: str,
    html_content: Optional[str] = None,
    current_user_id: int = Depends(get_current_user_id)
):
    """Extract job context from a webpage for AI content generation"""
    try:
        # This endpoint will help the extension extract job information
        # from the current page to provide context for AI generation
        
        if html_content:
            # Process provided HTML content
            job_data = await _extract_job_data_from_html(html_content, url)
        else:
            # For now, return basic job data structure
            # In a full implementation, you might scrape the URL
            job_data = JobData(
                title="Software Engineer",  # Would extract from page
                company="Unknown Company",  # Would extract from page
                description="",  # Would extract from page
                url=url,
                location="",  # Would extract from page
            )
        
        return {
            "success": True,
            "job_data": job_data,
            "extracted_at": datetime.now().isoformat()
        }
        
    except Exception as e:
        logger.error(f"Error extracting job context: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _extract_job_data_from_html(html_content: str, url: str) -> JobData:
    """Extract job data from HTML content"""
    # This is a simplified implementation
    # In a full version, you'd use BeautifulSoup and more sophisticated extraction
    
    import re
    
    # Simple regex-based extraction (would be more sophisticated in production)
    title_match = re.search(r'<title[^>]*>([^<]+)</title>', html_content, re.IGNORECASE)
    title = title_match.group(1) if title_match else "Unknown Position"
    
    # Extract company name from various possible locations
    company_patterns = [
        r'company["\']?\s*:\s*["\']([^"\']+)["\']',
        r'<meta[^>]*property=["\']og:site_name["\'][^>]*content=["\']([^"\']+)["\']',
        r'careers?\s+at\s+([^<\n]+)',
    ]
    
    company = "Unknown Company"
    for pattern in company_patterns:
        match = re.search(pattern, html_content, re.IGNORECASE)
        if match:
            company = match.group(1).strip()
            break
    
    return JobData(
        title=title,
        company=company,
        description="",  # Would extract job description
        url=url,
        location="",  # Would extract location
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    ) 