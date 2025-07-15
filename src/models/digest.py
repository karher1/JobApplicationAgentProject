from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
from uuid import UUID

# Enums
class DigestType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    CUSTOM = "custom"

class NotificationType(str, Enum):
    EMAIL = "email"
    SLACK = "slack"
    WEBHOOK = "webhook"
    SMS = "sms"

class DigestStatus(str, Enum):
    PENDING = "pending"
    GENERATING = "generating"
    SENT = "sent"
    FAILED = "failed"

# Digest Content Models
class JobMatchSummary(BaseModel):
    """Summary of job matches for a user"""
    job_id: str
    title: str
    company: str
    location: str
    match_score: float
    match_reasons: List[str]
    salary_range: Optional[str] = None
    job_type: Optional[str] = None
    remote_type: Optional[str] = None
    application_url: str
    posted_date: Optional[str] = None

class ApplicationUpdate(BaseModel):
    """Summary of application status updates"""
    application_id: str
    job_title: str
    company: str
    old_status: str
    new_status: str
    update_date: datetime
    notes: Optional[str] = None
    follow_up_required: bool = False
    follow_up_date: Optional[date] = None

class ProfileInsight(BaseModel):
    """Insights about user profile"""
    insight_type: str  # 'missing_skills', 'profile_completeness', 'resume_optimization'
    title: str
    description: str
    priority: str  # 'high', 'medium', 'low'
    action_required: bool = False
    action_url: Optional[str] = None

class SystemStats(BaseModel):
    """System statistics for the digest"""
    total_jobs_searched: int
    new_jobs_found: int
    applications_submitted: int
    interviews_scheduled: int
    offers_received: int
    profile_views: int
    skills_matched: int

# Digest Models
class DigestContent(BaseModel):
    """Content for a daily digest"""
    user_id: int
    digest_date: date
    job_matches: List[JobMatchSummary] = Field(default_factory=list)
    application_updates: List[ApplicationUpdate] = Field(default_factory=list)
    profile_insights: List[ProfileInsight] = Field(default_factory=list)
    system_stats: Optional[SystemStats] = None
    top_skills_in_demand: List[str] = Field(default_factory=list)
    trending_companies: List[str] = Field(default_factory=list)
    salary_insights: Optional[Dict[str, Any]] = None

class DigestTemplate(BaseModel):
    """Template for digest generation"""
    id: int
    name: str
    description: str
    template_type: DigestType
    subject_template: str
    html_template: str
    text_template: str
    is_active: bool = True
    created_at: datetime
    updated_at: datetime

class DigestSchedule(BaseModel):
    """Schedule for digest generation"""
    user_id: int
    digest_type: DigestType
    frequency: str  # 'daily', 'weekly', 'monthly'
    preferred_time: str  # '09:00', '18:00', etc.
    timezone: str
    is_active: bool = True
    last_sent: Optional[datetime] = None
    next_scheduled: Optional[datetime] = None

class DigestRequest(BaseModel):
    """Request to generate a digest"""
    user_id: int
    digest_type: DigestType = DigestType.DAILY
    date: Optional[date] = None  # If None, use today
    include_job_matches: bool = True
    include_applications: bool = True
    include_insights: bool = True
    include_stats: bool = True
    max_job_matches: int = 10
    max_application_updates: int = 20

class DigestResponse(BaseModel):
    """Response from digest generation"""
    success: bool
    digest_id: Optional[str] = None
    content: Optional[DigestContent] = None
    generated_at: datetime
    error_message: Optional[str] = None
    email_sent: bool = False
    email_id: Optional[str] = None

# Notification Models
class NotificationConfig(BaseModel):
    """Configuration for notifications"""
    user_id: int
    notification_type: NotificationType
    email_address: Optional[EmailStr] = None
    slack_webhook: Optional[str] = None
    webhook_url: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: bool = True
    preferences: Dict[str, Any] = Field(default_factory=dict)

class EmailNotification(BaseModel):
    """Email notification details"""
    to_email: EmailStr
    subject: str
    html_content: str
    text_content: str
    from_name: str = "Job Application Agent"
    from_email: str = "noreply@jobapplicationagent.com"
    reply_to: Optional[EmailStr] = None
    attachments: List[Dict[str, Any]] = Field(default_factory=list)

class NotificationHistory(BaseModel):
    """History of sent notifications"""
    id: int
    user_id: int
    notification_type: NotificationType
    digest_id: Optional[str] = None
    subject: str
    content_preview: str
    sent_at: datetime
    status: str  # 'sent', 'delivered', 'failed', 'bounced'
    error_message: Optional[str] = None
    delivery_time: Optional[float] = None  # seconds

# Request/Response Models
class GenerateDigestRequest(BaseModel):
    """Request to generate digest for a user"""
    user_id: int
    digest_type: DigestType = DigestType.DAILY
    send_notification: bool = True
    custom_date: Optional[date] = None

class BatchDigestRequest(BaseModel):
    """Request to generate digests for multiple users"""
    user_ids: List[int]
    digest_type: DigestType = DigestType.DAILY
    send_notifications: bool = True
    max_concurrent: int = 5

class DigestStats(BaseModel):
    """Statistics about digest generation"""
    total_digests_generated: int
    successful_digests: int
    failed_digests: int
    total_notifications_sent: int
    average_generation_time: float
    most_active_users: List[Dict[str, Any]]
    digest_timeline: List[Dict[str, Any]]

class DigestPreferences(BaseModel):
    """User preferences for digest content"""
    user_id: int
    include_job_matches: bool = True
    include_applications: bool = True
    include_insights: bool = True
    include_stats: bool = True
    max_job_matches: int = 10
    max_application_updates: int = 20
    preferred_job_types: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    salary_range_min: Optional[int] = None
    salary_range_max: Optional[int] = None
    notification_frequency: str = "daily"
    preferred_time: str = "09:00"
    timezone: str = "UTC"

# Template Models
class EmailTemplate(BaseModel):
    """Email template for notifications"""
    name: str
    subject_template: str
    html_template: str
    text_template: str
    variables: List[str] = Field(default_factory=list)
    description: str = ""

class DigestTemplateData(BaseModel):
    """Data structure for digest templates"""
    user_name: str
    digest_date: str
    job_matches: List[JobMatchSummary]
    application_updates: List[ApplicationUpdate]
    profile_insights: List[ProfileInsight]
    system_stats: Optional[SystemStats]
    top_skills: List[str]
    trending_companies: List[str]
    salary_insights: Optional[Dict[str, Any]]
    unsubscribe_url: str
    settings_url: str
    dashboard_url: str 