from pydantic import BaseModel, Field, EmailStr, HttpUrl
from typing import List, Optional, Dict, Any
from datetime import datetime, date
from enum import Enum
from uuid import UUID

# Enums
class RemotePreference(str, Enum):
    REMOTE = "remote"
    HYBRID = "hybrid"
    ONSITE = "onsite"
    ANY = "any"

class JobTypePreference(str, Enum):
    FULLTIME = "fulltime"
    PARTTIME = "parttime"
    CONTRACT = "contract"
    ANY = "any"

class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    ANY = "any"

class ProficiencyLevel(str, Enum):
    BEGINNER = "beginner"
    INTERMEDIATE = "intermediate"
    ADVANCED = "advanced"
    EXPERT = "expert"

class SkillCategory(str, Enum):
    PROGRAMMING = "programming"
    FRAMEWORK = "framework"
    TOOL = "tool"
    LANGUAGE = "language"
    SOFT_SKILL = "soft_skill"

class ApplicationStatus(str, Enum):
    APPLIED = "applied"
    INTERVIEWING = "interviewing"
    OFFERED = "offered"
    REJECTED = "rejected"
    WITHDRAWN = "withdrawn"

# Base Models
class UserBase(BaseModel):
    email: EmailStr
    first_name: str = Field(..., min_length=1, max_length=100)
    last_name: str = Field(..., min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    location: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)

class UserCreate(UserBase):
    pass

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    first_name: Optional[str] = Field(None, min_length=1, max_length=100)
    last_name: Optional[str] = Field(None, min_length=1, max_length=100)
    phone: Optional[str] = Field(None, max_length=20)
    linkedin_url: Optional[HttpUrl] = None
    github_url: Optional[HttpUrl] = None
    portfolio_url: Optional[HttpUrl] = None
    location: Optional[str] = Field(None, max_length=255)
    timezone: Optional[str] = Field(None, max_length=50)

class User(UserBase):
    id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# User Preferences Models
class UserPreferencesBase(BaseModel):
    preferred_job_titles: List[str] = Field(default_factory=list)
    preferred_locations: List[str] = Field(default_factory=list)
    preferred_salary_min: Optional[int] = Field(None, ge=0)
    preferred_salary_max: Optional[int] = Field(None, ge=0)
    preferred_job_types: List[str] = Field(default_factory=list)
    remote_preference: bool = False
    notification_frequency: str = Field(default="daily")
    preferred_time: str = Field(default="09:00:00")
    timezone: str = Field(default="UTC")

class UserPreferencesCreate(UserPreferencesBase):
    user_id: int

class UserPreferencesUpdate(BaseModel):
    preferred_job_titles: Optional[List[str]] = None
    preferred_locations: Optional[List[str]] = None
    preferred_salary_min: Optional[int] = Field(None, ge=0)
    preferred_salary_max: Optional[int] = Field(None, ge=0)
    preferred_job_types: Optional[List[str]] = None
    remote_preference: Optional[bool] = None
    notification_frequency: Optional[str] = None
    preferred_time: Optional[str] = None
    timezone: Optional[str] = None

class UserPreferences(UserPreferencesBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Resume Models
class ResumeBase(BaseModel):
    title: str = Field(..., min_length=1, max_length=255)
    file_path: str = Field(..., max_length=500)

class ResumeCreate(ResumeBase):
    user_id: int

class ResumeUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)

class Resume(ResumeBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Resume Content Models
class ResumeContentBase(BaseModel):
    extracted_text: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None

class ResumeContentCreate(ResumeContentBase):
    resume_id: int

class ResumeContentUpdate(BaseModel):
    extracted_text: Optional[str] = None
    parsed_json: Optional[Dict[str, Any]] = None

class ResumeContent(ResumeContentBase):
    id: int
    resume_id: int
    embedding_vector: Optional[List[float]] = None
    last_parsed_at: datetime
    created_at: datetime

    class Config:
        from_attributes = True

# Skills Models
class SkillBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    category: Optional[SkillCategory] = None

class SkillCreate(SkillBase):
    pass

class Skill(SkillBase):
    id: int
    created_at: datetime

    class Config:
        from_attributes = True

# User Skills Models
class UserSkillBase(BaseModel):
    proficiency_level: ProficiencyLevel = ProficiencyLevel.INTERMEDIATE
    years_of_experience: Optional[int] = Field(None, ge=0)
    is_highlighted: bool = False

class UserSkillCreate(UserSkillBase):
    user_id: int
    skill_id: int

class UserSkillUpdate(BaseModel):
    proficiency_level: Optional[ProficiencyLevel] = None
    years_of_experience: Optional[int] = Field(None, ge=0)
    is_highlighted: Optional[bool] = None

class UserSkill(UserSkillBase):
    id: int
    user_id: int
    skill_id: int
    created_at: datetime
    skill: Optional[Skill] = None

    class Config:
        from_attributes = True

# Work Experience Models
class WorkExperienceBase(BaseModel):
    company_name: str = Field(..., min_length=1, max_length=255)
    job_title: str = Field(..., min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    start_date: date
    end_date: Optional[date] = None
    is_current: bool = False
    description: Optional[str] = None
    achievements: List[str] = Field(default_factory=list)
    technologies_used: List[str] = Field(default_factory=list)

class WorkExperienceCreate(WorkExperienceBase):
    user_id: int

class WorkExperienceUpdate(BaseModel):
    company_name: Optional[str] = Field(None, min_length=1, max_length=255)
    job_title: Optional[str] = Field(None, min_length=1, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    description: Optional[str] = None
    achievements: Optional[List[str]] = None
    technologies_used: Optional[List[str]] = None

class WorkExperience(WorkExperienceBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Education Models
class EducationBase(BaseModel):
    institution_name: str = Field(..., min_length=1, max_length=255)
    degree: str = Field(..., min_length=1, max_length=255)
    field_of_study: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: bool = False
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    description: Optional[str] = None

class EducationCreate(EducationBase):
    user_id: int

class EducationUpdate(BaseModel):
    institution_name: Optional[str] = Field(None, min_length=1, max_length=255)
    degree: Optional[str] = Field(None, min_length=1, max_length=255)
    field_of_study: Optional[str] = Field(None, max_length=255)
    location: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    is_current: Optional[bool] = None
    gpa: Optional[float] = Field(None, ge=0.0, le=4.0)
    description: Optional[str] = None

class Education(EducationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Certification Models
class CertificationBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    issuing_organization: str = Field(..., min_length=1, max_length=255)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = Field(None, max_length=255)
    credential_url: Optional[HttpUrl] = None

class CertificationCreate(CertificationBase):
    user_id: int

class CertificationUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=255)
    issuing_organization: Optional[str] = Field(None, min_length=1, max_length=255)
    issue_date: Optional[date] = None
    expiry_date: Optional[date] = None
    credential_id: Optional[str] = Field(None, max_length=255)
    credential_url: Optional[HttpUrl] = None

class Certification(CertificationBase):
    id: int
    user_id: int
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Application History Models
class ApplicationHistoryBase(BaseModel):
    job_id: Optional[str] = Field(None, max_length=255)
    resume_id: Optional[int] = None
    status: ApplicationStatus = ApplicationStatus.APPLIED
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None

class ApplicationHistoryCreate(ApplicationHistoryBase):
    user_id: int

class ApplicationHistoryUpdate(BaseModel):
    status: Optional[ApplicationStatus] = None
    notes: Optional[str] = None
    follow_up_date: Optional[date] = None

class ApplicationHistory(ApplicationHistoryBase):
    id: int
    user_id: int
    application_date: datetime
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

# Comprehensive User Profile Model
class UserProfile(BaseModel):
    user: User
    preferences: Optional[UserPreferences] = None
    resumes: List[Resume] = Field(default_factory=list)
    skills: List[UserSkill] = Field(default_factory=list)
    work_experience: List[WorkExperience] = Field(default_factory=list)
    education: List[Education] = Field(default_factory=list)
    certifications: List[Certification] = Field(default_factory=list)
    application_history: List[ApplicationHistory] = Field(default_factory=list)

    class Config:
        from_attributes = True

# Request/Response Models
class UserProfileCreateRequest(BaseModel):
    user: UserCreate
    preferences: Optional[UserPreferencesBase] = None

class UserProfileUpdateRequest(BaseModel):
    user: Optional[UserUpdate] = None
    preferences: Optional[UserPreferencesUpdate] = None

class ResumeUploadRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=255)
    file_content: str  # Base64 encoded content
    file_name: str

class SkillAddRequest(BaseModel):
    skill_name: str = Field(..., min_length=1, max_length=255)
    proficiency_level: ProficiencyLevel = ProficiencyLevel.INTERMEDIATE
    years_of_experience: Optional[int] = Field(None, ge=0)
    is_highlighted: bool = False

class JobMatchRequest(BaseModel):
    user_id: int
    job_description: str
    limit: int = Field(default=5, ge=1, le=20)

class JobMatchResponse(BaseModel):
    job_id: str
    title: str
    company: str
    match_score: float
    match_reasons: List[str]
    skills_match: List[str]
    experience_match: bool 