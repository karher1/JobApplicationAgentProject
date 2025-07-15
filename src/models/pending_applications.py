from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

class PendingApplicationStatus(str, Enum):
    """Status of a pending application"""
    PENDING = "pending"  # Waiting for human approval
    APPROVED = "approved"  # Approved for submission
    REJECTED = "rejected"  # Rejected by human
    SUBMITTED = "submitted"  # Actually submitted to job board
    FAILED = "failed"  # Submission failed
    CANCELLED = "cancelled"  # Cancelled by user

class PendingApplicationPriority(str, Enum):
    """Priority levels for pending applications"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"

class PendingApplicationBase(BaseModel):
    """Base model for pending applications"""
    user_id: int = Field(..., description="User ID who wants to apply")
    job_id: str = Field(..., description="Job ID to apply for")
    job_title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    job_url: str = Field(..., description="Job application URL")
    resume_id: Optional[int] = Field(None, description="Resume ID to use")
    cover_letter: Optional[str] = Field(None, description="Cover letter text")
    form_data: Dict[str, Any] = Field(default_factory=dict, description="Form data to fill")
    additional_info: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Additional information")
    priority: PendingApplicationPriority = Field(default=PendingApplicationPriority.MEDIUM, description="Application priority")
    notes: Optional[str] = Field(None, description="User notes about the application")
    status: PendingApplicationStatus = Field(default=PendingApplicationStatus.PENDING, description="Current status")

class PendingApplicationCreate(PendingApplicationBase):
    """Model for creating a pending application"""
    pass

class PendingApplicationUpdate(BaseModel):
    """Model for updating a pending application"""
    status: Optional[PendingApplicationStatus] = None
    priority: Optional[PendingApplicationPriority] = None
    notes: Optional[str] = None
    reviewer_notes: Optional[str] = None
    cover_letter: Optional[str] = None
    form_data: Optional[Dict[str, Any]] = None
    additional_info: Optional[Dict[str, Any]] = None

class PendingApplication(PendingApplicationBase):
    """Full pending application model"""
    id: int = Field(..., description="Unique application ID")
    created_at: datetime = Field(..., description="When the application was created")
    updated_at: datetime = Field(..., description="When the application was last updated")
    reviewed_at: Optional[datetime] = Field(None, description="When the application was reviewed")
    reviewer_id: Optional[int] = Field(None, description="ID of user who reviewed")
    reviewer_notes: Optional[str] = Field(None, description="Notes from reviewer")
    submitted_at: Optional[datetime] = Field(None, description="When the application was submitted")
    submission_result: Optional[Dict[str, Any]] = Field(None, description="Results of submission attempt")

    class Config:
        from_attributes = True

class PendingApplicationReviewRequest(BaseModel):
    """Request model for reviewing a pending application"""
    status: PendingApplicationStatus = Field(..., description="New status (approved/rejected)")
    reviewer_notes: Optional[str] = Field(None, description="Notes from reviewer")
    priority: Optional[PendingApplicationPriority] = Field(None, description="Update priority if needed")
    modifications: Optional[Dict[str, Any]] = Field(None, description="Modifications to form data or other fields")

class PendingApplicationReviewResponse(BaseModel):
    """Response model for reviewing a pending application"""
    application_id: int = Field(..., description="ID of the reviewed application")
    old_status: PendingApplicationStatus = Field(..., description="Previous status")
    new_status: PendingApplicationStatus = Field(..., description="New status")
    reviewer_id: int = Field(..., description="ID of the reviewer")
    reviewed_at: datetime = Field(..., description="When the review was completed")
    success: bool = Field(..., description="Whether the review was successful")
    message: Optional[str] = Field(None, description="Status message")

class PendingApplicationListResponse(BaseModel):
    """Response model for listing pending applications"""
    applications: List[PendingApplication] = Field(..., description="List of pending applications")
    total_count: int = Field(..., description="Total number of pending applications")
    pending_count: int = Field(..., description="Number of applications awaiting review")
    approved_count: int = Field(..., description="Number of approved applications")
    rejected_count: int = Field(..., description="Number of rejected applications")

class PendingApplicationSubmissionResult(BaseModel):
    """Model for tracking submission results"""
    application_id: int = Field(..., description="ID of the pending application")
    success: bool = Field(..., description="Whether submission was successful")
    filled_fields: List[str] = Field(default_factory=list, description="Successfully filled fields")
    failed_fields: List[str] = Field(default_factory=list, description="Fields that failed to fill")
    error_message: Optional[str] = Field(None, description="Error message if submission failed")
    submitted_at: datetime = Field(..., description="When submission was attempted")
    submission_url: Optional[str] = Field(None, description="URL where submission was attempted")

class BatchSubmissionRequest(BaseModel):
    """Request model for submitting multiple approved applications"""
    application_ids: List[int] = Field(..., description="List of approved application IDs to submit")
    max_concurrent: int = Field(default=3, description="Maximum concurrent submissions")
    delay_between_submissions: int = Field(default=30, description="Delay between submissions in seconds")

class BatchSubmissionResponse(BaseModel):
    """Response model for batch submission"""
    total_submitted: int = Field(..., description="Total number of applications submitted")
    successful_submissions: int = Field(..., description="Number of successful submissions")
    failed_submissions: int = Field(..., description="Number of failed submissions")
    results: List[PendingApplicationSubmissionResult] = Field(..., description="Detailed results for each submission")
    execution_time: float = Field(..., description="Total execution time in seconds") 