import logging
from typing import List, Optional, Dict, Any
from datetime import datetime
from supabase import create_client, Client

from src.models.pending_applications import (
    PendingApplication, PendingApplicationCreate, PendingApplicationUpdate,
    PendingApplicationReviewRequest, PendingApplicationReviewResponse,
    PendingApplicationListResponse, PendingApplicationSubmissionResult,
    PendingApplicationStatus, PendingApplicationPriority,
    BatchSubmissionRequest, BatchSubmissionResponse
)
from src.models.schemas import ServiceHealth, JobPosition
from src.core.config import get_settings

logger = logging.getLogger(__name__)

class PendingApplicationService:
    """Service for managing pending applications with approval workflow"""
    
    def __init__(self):
        settings = get_settings()
        self.supabase_url = settings.supabase_url
        self.supabase_key = settings.supabase_anon_key
        self.supabase: Optional[Client] = None
        
    async def initialize(self):
        """Initialize Supabase client"""
        try:
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Supabase URL and key must be set")
            
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            logger.info("Pending application service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing pending application service: {e}")
            raise
    
    async def health_check(self) -> ServiceHealth:
        """Check pending application service health"""
        try:
            if not self.supabase:
                return ServiceHealth(status="unhealthy", message="Supabase client not initialized")
            
            # Test connection by querying pending applications table
            result = self.supabase.table("pending_applications").select("id").limit(1).execute()
            return ServiceHealth(status="healthy", message="Database connection successful")
        except Exception as e:
            return ServiceHealth(status="unhealthy", message=str(e))
    
    async def create_pending_application(
        self, 
        user_id: int, 
        job: JobPosition, 
        form_data: Dict[str, Any],
        cover_letter: Optional[str] = None,
        resume_id: Optional[int] = None,
        priority: PendingApplicationPriority = PendingApplicationPriority.MEDIUM,
        notes: Optional[str] = None
    ) -> PendingApplication:
        """Create a new pending application"""
        try:
            application_data = {
                "user_id": user_id,
                "job_id": job.id if job.id else f"job_{hash(job.url)}",
                "job_title": job.title,
                "company": job.company,
                "job_url": job.url,
                "resume_id": resume_id,
                "cover_letter": cover_letter,
                "form_data": form_data,
                "additional_info": {},
                "priority": priority.value,
                "notes": notes,
                "status": PendingApplicationStatus.PENDING.value
            }
            
            result = self.supabase.table("pending_applications").insert(application_data).execute()
            
            if result.data:
                logger.info(f"Created pending application for {job.title} at {job.company}")
                return PendingApplication(**result.data[0])
            else:
                raise ValueError("Failed to create pending application")
                
        except Exception as e:
            logger.error(f"Error creating pending application: {e}")
            raise
    
    async def get_pending_applications(
        self, 
        user_id: Optional[int] = None,
        status: Optional[PendingApplicationStatus] = None,
        limit: int = 50,
        offset: int = 0
    ) -> PendingApplicationListResponse:
        """Get pending applications with filtering"""
        try:
            query = self.supabase.table("pending_applications").select("*")
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            if status:
                query = query.eq("status", status.value)
            
            # Get total count
            count_query = self.supabase.table("pending_applications").select("id", count="exact")
            if user_id:
                count_query = count_query.eq("user_id", user_id)
            if status:
                count_query = count_query.eq("status", status.value)
            
            count_result = count_query.execute()
            total_count = count_result.count if count_result.count else 0
            
            # Get paginated results
            result = query.order("created_at", desc=True).range(offset, offset + limit - 1).execute()
            
            applications = [PendingApplication(**app) for app in result.data]
            
            # Get status counts
            status_counts = await self._get_status_counts(user_id)
            
            return PendingApplicationListResponse(
                applications=applications,
                total_count=total_count,
                pending_count=status_counts.get("pending", 0),
                approved_count=status_counts.get("approved", 0),
                rejected_count=status_counts.get("rejected", 0)
            )
            
        except Exception as e:
            logger.error(f"Error getting pending applications: {e}")
            raise
    
    async def get_pending_application(self, application_id: int) -> Optional[PendingApplication]:
        """Get a specific pending application by ID"""
        try:
            result = self.supabase.table("pending_applications").select("*").eq("id", application_id).execute()
            
            if result.data:
                return PendingApplication(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error getting pending application {application_id}: {e}")
            raise
    
    async def update_pending_application(
        self, 
        application_id: int, 
        update_data: PendingApplicationUpdate
    ) -> Optional[PendingApplication]:
        """Update a pending application"""
        try:
            # Only update fields that are provided
            update_dict = {k: v for k, v in update_data.model_dump().items() if v is not None}
            
            if not update_dict:
                # No updates provided, return current application
                return await self.get_pending_application(application_id)
            
            result = self.supabase.table("pending_applications").update(update_dict).eq("id", application_id).execute()
            
            if result.data:
                logger.info(f"Updated pending application {application_id}")
                return PendingApplication(**result.data[0])
            return None
            
        except Exception as e:
            logger.error(f"Error updating pending application {application_id}: {e}")
            raise
    
    async def review_pending_application(
        self, 
        application_id: int, 
        reviewer_id: int, 
        review_request: PendingApplicationReviewRequest
    ) -> PendingApplicationReviewResponse:
        """Review a pending application (approve/reject)"""
        try:
            # Get current application
            current_app = await self.get_pending_application(application_id)
            if not current_app:
                raise ValueError(f"Application {application_id} not found")
            
            old_status = current_app.status
            new_status = review_request.status
            
            # Update application
            update_data = {
                "status": new_status.value,
                "reviewer_id": reviewer_id,
                "reviewer_notes": review_request.reviewer_notes,
                "reviewed_at": datetime.now().isoformat()
            }
            
            if review_request.priority:
                update_data["priority"] = review_request.priority.value
            
            if review_request.modifications:
                # Apply modifications to form data or other fields
                if "form_data" in review_request.modifications:
                    update_data["form_data"] = review_request.modifications["form_data"]
                if "cover_letter" in review_request.modifications:
                    update_data["cover_letter"] = review_request.modifications["cover_letter"]
            
            result = self.supabase.table("pending_applications").update(update_data).eq("id", application_id).execute()
            
            if not result.data:
                raise ValueError("Failed to update application")
            
            # Log the review
            await self._log_application_review(
                application_id, reviewer_id, old_status, new_status, 
                review_request.reviewer_notes, review_request.modifications
            )
            
            logger.info(f"Reviewed application {application_id}: {old_status} -> {new_status}")
            
            return PendingApplicationReviewResponse(
                application_id=application_id,
                old_status=old_status,
                new_status=new_status,
                reviewer_id=reviewer_id,
                reviewed_at=datetime.now(),
                success=True,
                message=f"Application {new_status.value} successfully"
            )
            
        except Exception as e:
            logger.error(f"Error reviewing application {application_id}: {e}")
            return PendingApplicationReviewResponse(
                application_id=application_id,
                old_status=old_status if 'old_status' in locals() else PendingApplicationStatus.PENDING,
                new_status=review_request.status,
                reviewer_id=reviewer_id,
                reviewed_at=datetime.now(),
                success=False,
                message=f"Review failed: {str(e)}"
            )
    
    async def get_applications_for_review(
        self, 
        limit: int = 50,
        priority_filter: Optional[PendingApplicationPriority] = None
    ) -> List[PendingApplication]:
        """Get applications that need review (pending status)"""
        try:
            query = self.supabase.table("pending_applications").select("*").eq("status", "pending")
            
            if priority_filter:
                query = query.eq("priority", priority_filter.value)
            
            # Order by priority and creation date
            result = query.order("priority", desc=True).order("created_at", desc=False).limit(limit).execute()
            
            return [PendingApplication(**app) for app in result.data]
            
        except Exception as e:
            logger.error(f"Error getting applications for review: {e}")
            raise
    
    async def get_approved_applications(
        self, 
        user_id: Optional[int] = None,
        limit: int = 50
    ) -> List[PendingApplication]:
        """Get approved applications ready for submission"""
        try:
            query = self.supabase.table("pending_applications").select("*").eq("status", "approved")
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.order("reviewed_at", desc=False).limit(limit).execute()
            
            return [PendingApplication(**app) for app in result.data]
            
        except Exception as e:
            logger.error(f"Error getting approved applications: {e}")
            raise
    
    async def cancel_pending_application(
        self, 
        application_id: int, 
        user_id: int
    ) -> bool:
        """Cancel a pending application"""
        try:
            result = self.supabase.table("pending_applications").update({
                "status": PendingApplicationStatus.CANCELLED.value,
                "updated_at": datetime.now().isoformat()
            }).eq("id", application_id).eq("user_id", user_id).execute()
            
            if result.data:
                logger.info(f"Cancelled pending application {application_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error cancelling application {application_id}: {e}")
            raise
    
    async def _get_status_counts(self, user_id: Optional[int] = None) -> Dict[str, int]:
        """Get counts of applications by status"""
        try:
            query = self.supabase.table("pending_applications").select("status", count="exact")
            
            if user_id:
                query = query.eq("user_id", user_id)
            
            result = query.execute()
            
            # Count by status
            status_counts = {}
            for row in result.data:
                status = row["status"]
                status_counts[status] = status_counts.get(status, 0) + 1
            
            return status_counts
            
        except Exception as e:
            logger.error(f"Error getting status counts: {e}")
            return {}
    
    async def _log_application_review(
        self,
        application_id: int,
        reviewer_id: int,
        old_status: PendingApplicationStatus,
        new_status: PendingApplicationStatus,
        reviewer_notes: Optional[str],
        modifications: Optional[Dict[str, Any]]
    ):
        """Log application review for audit trail"""
        try:
            review_data = {
                "application_id": application_id,
                "reviewer_id": reviewer_id,
                "old_status": old_status.value,
                "new_status": new_status.value,
                "reviewer_notes": reviewer_notes,
                "modifications": modifications
            }
            
            self.supabase.table("pending_application_reviews").insert(review_data).execute()
            
        except Exception as e:
            logger.warning(f"Error logging application review: {e}")
            # Don't fail the main operation if logging fails
    
    async def delete_pending_application(self, application_id: int, user_id: int) -> bool:
        """Delete a pending application (only if not submitted)"""
        try:
            # Only allow deletion if not submitted
            result = self.supabase.table("pending_applications").delete().eq("id", application_id).eq("user_id", user_id).neq("status", "submitted").execute()
            
            if result.data:
                logger.info(f"Deleted pending application {application_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error deleting application {application_id}: {e}")
            raise 