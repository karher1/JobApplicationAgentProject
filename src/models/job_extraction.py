from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum

# Enums for structured data
class ExperienceLevel(str, Enum):
    ENTRY = "entry"
    JUNIOR = "junior"
    MID = "mid"
    SENIOR = "senior"
    LEAD = "lead"
    PRINCIPAL = "principal"
    EXECUTIVE = "executive"

class JobType(str, Enum):
    FULL_TIME = "full_time"
    PART_TIME = "part_time"
    CONTRACT = "contract"
    INTERNSHIP = "internship"
    FREELANCE = "freelance"

class RemoteType(str, Enum):
    ONSITE = "onsite"
    REMOTE = "remote"
    HYBRID = "hybrid"
    FLEXIBLE = "flexible"

class SalaryType(str, Enum):
    HOURLY = "hourly"
    ANNUAL = "annual"
    MONTHLY = "monthly"
    PROJECT_BASED = "project_based"

# Enhanced Job Extraction Models
class SalaryInfo(BaseModel):
    """Extracted salary information"""
    min_amount: Optional[float] = Field(None, ge=0, description="Minimum salary amount")
    max_amount: Optional[float] = Field(None, ge=0, description="Maximum salary amount")
    currency: str = Field(default="USD", description="Currency code")
    salary_type: SalaryType = Field(default=SalaryType.ANNUAL, description="Type of salary")
    is_negotiable: bool = Field(default=False, description="Whether salary is negotiable")
    includes_equity: bool = Field(default=False, description="Whether compensation includes equity")
    includes_benefits: bool = Field(default=False, description="Whether compensation includes benefits")

class CompanyInfo(BaseModel):
    """Extracted company information"""
    name: str = Field(..., description="Company name")
    industry: Optional[str] = Field(None, description="Company industry")
    size: Optional[str] = Field(None, description="Company size (e.g., '10-50 employees')")
    founded_year: Optional[int] = Field(None, description="Company founding year")
    location: Optional[str] = Field(None, description="Company headquarters location")
    website: Optional[str] = Field(None, description="Company website")
    description: Optional[str] = Field(None, description="Company description")

class JobRequirements(BaseModel):
    """Extracted job requirements"""
    required_skills: List[str] = Field(default_factory=list, description="Required technical skills")
    preferred_skills: List[str] = Field(default_factory=list, description="Preferred skills")
    required_experience_years: Optional[int] = Field(None, ge=0, description="Required years of experience")
    experience_level: Optional[ExperienceLevel] = Field(None, description="Required experience level")
    required_education: Optional[str] = Field(None, description="Required education level")
    certifications: List[str] = Field(default_factory=list, description="Required certifications")
    languages: List[str] = Field(default_factory=list, description="Required languages")

class JobBenefits(BaseModel):
    """Extracted job benefits"""
    health_insurance: bool = Field(default=False, description="Health insurance provided")
    dental_insurance: bool = Field(default=False, description="Dental insurance provided")
    vision_insurance: bool = Field(default=False, description="Vision insurance provided")
    retirement_plan: bool = Field(default=False, description="Retirement plan provided")
    paid_time_off: bool = Field(default=False, description="Paid time off provided")
    flexible_hours: bool = Field(default=False, description="Flexible working hours")
    remote_work: bool = Field(default=False, description="Remote work options")
    professional_development: bool = Field(default=False, description="Professional development support")
    other_benefits: List[str] = Field(default_factory=list, description="Other benefits mentioned")

class EnhancedJobPosition(BaseModel):
    """Enhanced job position with extracted structured data"""
    # Basic job info (from original JobPosition)
    id: Optional[str] = None
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    url: str = Field(..., description="Application URL")
    job_board: str = Field(..., description="Job board source")
    posted_date: Optional[str] = Field(None, description="When the job was posted")
    job_type: Optional[JobType] = Field(None, description="Type of employment")
    remote_type: Optional[RemoteType] = Field(None, description="Remote work arrangement")
    description_snippet: Optional[str] = Field(None, description="Brief job description")
    
    # Enhanced extracted data
    full_description: Optional[str] = Field(None, description="Full job description text")
    salary_info: Optional[SalaryInfo] = Field(None, description="Extracted salary information")
    company_info: Optional[CompanyInfo] = Field(None, description="Extracted company information")
    requirements: Optional[JobRequirements] = Field(None, description="Extracted job requirements")
    benefits: Optional[JobBenefits] = Field(None, description="Extracted job benefits")
    
    # Additional extracted fields
    responsibilities: List[str] = Field(default_factory=list, description="Job responsibilities")
    qualifications: List[str] = Field(default_factory=list, description="Job qualifications")
    application_deadline: Optional[datetime] = Field(None, description="Application deadline")
    start_date: Optional[datetime] = Field(None, description="Expected start date")
    contract_duration: Optional[str] = Field(None, description="Contract duration for contract roles")
    travel_requirements: Optional[str] = Field(None, description="Travel requirements")
    visa_sponsorship: bool = Field(default=False, description="Whether visa sponsorship is provided")
    
    # Metadata
    extraction_confidence: float = Field(default=0.0, ge=0.0, le=1.0, description="Confidence score of extraction")
    extraction_timestamp: Optional[datetime] = Field(None, description="When extraction was performed")
    raw_extraction_data: Optional[Dict[str, Any]] = Field(None, description="Raw LLM extraction output")
    
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

# Request/Response Models
class JobExtractionRequest(BaseModel):
    """Request model for job extraction"""
    job_url: str = Field(..., description="URL of the job posting")
    job_title: Optional[str] = Field(None, description="Job title if known")
    company_name: Optional[str] = Field(None, description="Company name if known")
    raw_description: Optional[str] = Field(None, description="Raw job description text")
    force_re_extraction: bool = Field(default=False, description="Force re-extraction even if cached")

class JobExtractionResponse(BaseModel):
    """Response model for job extraction"""
    success: bool = Field(..., description="Whether extraction was successful")
    job_position: Optional[EnhancedJobPosition] = Field(None, description="Extracted job position")
    extraction_time: float = Field(..., description="Time taken for extraction in seconds")
    error_message: Optional[str] = Field(None, description="Error message if extraction failed")
    confidence_score: float = Field(default=0.0, description="Overall confidence score")

class BatchExtractionRequest(BaseModel):
    """Request model for batch job extraction"""
    job_urls: List[str] = Field(..., description="List of job URLs to extract")
    max_concurrent: int = Field(default=5, ge=1, le=10, description="Maximum concurrent extractions")

class BatchExtractionResponse(BaseModel):
    """Response model for batch job extraction"""
    total_jobs: int = Field(..., description="Total number of jobs processed")
    successful_extractions: int = Field(..., description="Number of successful extractions")
    failed_extractions: int = Field(..., description="Number of failed extractions")
    results: List[JobExtractionResponse] = Field(..., description="Individual extraction results")
    total_time: float = Field(..., description="Total time taken for batch extraction")

# Extraction Templates
class ExtractionTemplate(BaseModel):
    """Template for LLM-based extraction"""
    name: str = Field(..., description="Template name")
    description: str = Field(..., description="Template description")
    prompt_template: str = Field(..., description="LLM prompt template")
    output_schema: Dict[str, Any] = Field(..., description="Expected output schema")
    version: str = Field(default="1.0", description="Template version")

# Extraction Statistics
class ExtractionStats(BaseModel):
    """Statistics for job extraction"""
    total_extractions: int = Field(..., description="Total number of extractions performed")
    successful_extractions: int = Field(..., description="Number of successful extractions")
    failed_extractions: int = Field(..., description="Number of failed extractions")
    average_confidence: float = Field(..., description="Average confidence score")
    average_extraction_time: float = Field(..., description="Average extraction time in seconds")
    most_extracted_companies: List[Dict[str, Any]] = Field(default_factory=list, description="Most extracted companies")
    extraction_timeline: List[Dict[str, Any]] = Field(default_factory=list, description="Extraction timeline data")

# Validation Models
class ExtractionValidation(BaseModel):
    """Validation results for extracted data"""
    field_name: str = Field(..., description="Name of the field being validated")
    is_valid: bool = Field(..., description="Whether the field is valid")
    confidence: float = Field(..., ge=0.0, le=1.0, description="Confidence in the validation")
    suggestions: List[str] = Field(default_factory=list, description="Suggestions for improvement")
    error_message: Optional[str] = Field(None, description="Error message if validation failed")

class JobExtractionValidation(BaseModel):
    """Complete validation for a job extraction"""
    job_id: str = Field(..., description="Job ID being validated")
    overall_valid: bool = Field(..., description="Whether the overall extraction is valid")
    overall_confidence: float = Field(..., ge=0.0, le=1.0, description="Overall confidence score")
    field_validations: List[ExtractionValidation] = Field(..., description="Individual field validations")
    recommendations: List[str] = Field(default_factory=list, description="Overall recommendations") 