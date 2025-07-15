from pydantic import BaseModel, Field, validator, EmailStr
from typing import List, Optional, Dict, Any
from datetime import datetime
from enum import Enum
import re


# Enums
class FieldType(str, Enum):
    TEXT = "text"
    EMAIL = "email"
    PHONE = "tel"
    URL = "url"
    TEXTAREA = "textarea"
    SELECT = "select"
    FILE = "file"
    CHECKBOX = "checkbox"
    RADIO = "radio"


# Company domains and companies (using scraper-compatible keys)
COMPANY_DOMAINS = {
    "Generative AI": [
        "openai",
        "anthropic",
        "cohere",
        "mistral-ai",
        "inflection-ai",
        "xai",
        "adept",
        "perplexity-ai",
        "runway",
        "hugging-face",
        "stability-ai",
    ],
    "AI Infrastructure / Tooling": [
        "pinecone",
        "weaviate",
        "langchain",
        "weights-biases",
        "scale-ai",
        "labelbox",
        "truera",
    ],
    "Enterprise AI Platforms": [
        "databricks",
        "datarobot",
        "c3-ai",
        "abacus-ai",
        "sambanova",
    ],
    "Cloud / Infrastructure": [
        "amazon",
        "microsoft",
        "google",
        "cloudflare",
        "digitalocean",
        "fastly",
    ],
    "Developer Platforms": [
        "github",
        "gitlab",
        "hashicorp",
        "circleci",
        "netlify",
        "vercel",
        "render",
        "replit",
    ],
    "Dev Tools & SaaS": [
        "atlassian",
        "linear",
        "notion",
        "slack",
        "figma",
        "retool",
        "clickup",
    ],
    "Consumer & Social Tech": [
        "apple",
        "google",
        "meta",
        "snap",
        "bytedance",
        "spotify",
        "netflix",
        "pinterest",
    ],
    "Fintech": [
        "stripe",
        "square",
        "plaid",
        "brex",
        "ramp",
        "affirm",
        "robinhood",
        "chime",
        "coinbase",
    ],
    "Analytics & Data": [
        "snowflake",
        "confluent",
        "segment",
        "mixpanel",
        "amplitude",
        "looker",
        "tableau",
    ],
    "Security": ["okta", "cloudflare", "auth0", "crowdstrike", "sentinelone", "snyk"],
    "Enterprise SaaS": [
        "salesforce",
        "workday",
        "servicenow",
        "zendesk",
        "box",
        "dropbox",
        "zoom",
    ],
}

# Mapping from scraper keys to display names
COMPANY_DISPLAY_NAMES = {
    "openai": "OpenAI",
    "anthropic": "Anthropic",
    "cohere": "Cohere",
    "mistral-ai": "Mistral AI",
    "inflection-ai": "Inflection AI",
    "xai": "xAI",
    "adept": "Adept",
    "perplexity-ai": "Perplexity AI",
    "runway": "Runway",
    "hugging-face": "Hugging Face",
    "stability-ai": "Stability AI",
    "pinecone": "Pinecone",
    "weaviate": "Weaviate",
    "langchain": "LangChain",
    "weights-biases": "Weights & Biases",
    "scale-ai": "Scale AI",
    "labelbox": "Labelbox",
    "truera": "Truera",
    "databricks": "Databricks",
    "datarobot": "DataRobot",
    "c3-ai": "C3.ai",
    "abacus-ai": "Abacus.AI",
    "sambanova": "SambaNova",
    "amazon": "Amazon",
    "microsoft": "Microsoft",
    "google": "Google",
    "cloudflare": "Cloudflare",
    "digitalocean": "DigitalOcean",
    "fastly": "Fastly",
    "github": "GitHub",
    "gitlab": "GitLab",
    "hashicorp": "HashiCorp",
    "circleci": "CircleCI",
    "netlify": "Netlify",
    "vercel": "Vercel",
    "render": "Render",
    "replit": "Replit",
    "atlassian": "Atlassian",
    "linear": "Linear",
    "notion": "Notion",
    "slack": "Slack",
    "figma": "Figma",
    "retool": "Retool",
    "clickup": "ClickUp",
    "apple": "Apple",
    "meta": "Meta",
    "snap": "Snap",
    "bytedance": "ByteDance",
    "spotify": "Spotify",
    "netflix": "Netflix",
    "pinterest": "Pinterest",
    "stripe": "Stripe",
    "square": "Square",
    "plaid": "Plaid",
    "brex": "Brex",
    "ramp": "Ramp",
    "affirm": "Affirm",
    "robinhood": "Robinhood",
    "chime": "Chime",
    "snowflake": "Snowflake",
    "confluent": "Confluent",
    "segment": "Segment",
    "mixpanel": "Mixpanel",
    "amplitude": "Amplitude",
    "looker": "Looker",
    "tableau": "Tableau",
    "okta": "Okta",
    "auth0": "Auth0",
    "crowdstrike": "CrowdStrike",
    "sentinelone": "SentinelOne",
    "snyk": "Snyk",
    "salesforce": "Salesforce",
    "workday": "Workday",
    "servicenow": "ServiceNow",
    "zendesk": "Zendesk",
    "box": "Box",
    "dropbox": "Dropbox",
    "zoom": "Zoom",
}


# Base Models
class JobPosition(BaseModel):
    """Model for individual job positions"""

    id: Optional[str] = None
    title: str = Field(..., description="Job title")
    company: str = Field(..., description="Company name")
    location: str = Field(..., description="Job location")
    url: str = Field(..., description="Application URL")
    job_board: str = Field(..., description="Job board source")
    posted_date: Optional[str] = Field(None, description="When the job was posted")
    salary_range: Optional[str] = Field(None, description="Salary information")
    job_type: Optional[str] = Field(
        None, description="Full-time, Part-time, Contract, etc."
    )
    remote_option: Optional[str] = Field(None, description="Remote, Hybrid, On-site")
    description_snippet: Optional[str] = Field(
        None, description="Brief job description"
    )
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


class FormField(BaseModel):
    """Model for individual form fields"""

    label: str = Field(..., description="The label or name of the form field")
    field_type: FieldType = Field(..., description="The type of input field")
    required: bool = Field(default=False, description="Whether the field is required")
    placeholder: Optional[str] = Field(
        None, description="Placeholder text if available"
    )
    options: Optional[List[str]] = Field(
        None, description="Options for select/radio fields"
    )
    xpath: Optional[str] = Field(None, description="XPath selector for the field")


# Request Models
class JobSearchRequest(BaseModel):
    """Request model for job search"""

    job_titles: List[str] = Field(
        ..., min_items=1, max_items=10, description="List of job titles to search for"
    )
    locations: List[str] = Field(
        ..., min_items=1, max_items=10, description="List of locations to search in"
    )
    companies: Optional[List[str]] = Field(
        default=[],
        max_items=5,
        description="List of specific companies to search (max 5)",
    )
    max_results: int = Field(
        default=50, ge=1, le=100, description="Maximum number of results per search"
    )
    job_boards: Optional[List[str]] = Field(
        default=["Ashby"], max_items=3, description="Job boards to search"
    )
    remote_only: bool = Field(default=False, description="Search for remote jobs only")

    @validator("job_titles")
    def validate_job_titles(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one job title is required")
        for title in v:
            if not title.strip():
                raise ValueError("Job titles cannot be empty")
            if len(title.strip()) < 2:
                raise ValueError("Job titles must be at least 2 characters long")
            if len(title.strip()) > 100:
                raise ValueError("Job titles cannot exceed 100 characters")
        return [title.strip() for title in v]

    @validator("locations")
    def validate_locations(cls, v):
        if not v or len(v) == 0:
            raise ValueError("At least one location is required")
        for location in v:
            if not location.strip():
                raise ValueError("Locations cannot be empty")
            if len(location.strip()) < 2:
                raise ValueError("Locations must be at least 2 characters long")
            if len(location.strip()) > 100:
                raise ValueError("Locations cannot exceed 100 characters")
        return [location.strip() for location in v]

    @validator("companies")
    def validate_companies(cls, v):
        if v:
            for company in v:
                if not company.strip():
                    raise ValueError("Company names cannot be empty")
                if len(company.strip()) > 100:
                    raise ValueError("Company names cannot exceed 100 characters")
            return [company.strip() for company in v]
        return v


class JobApplicationRequest(BaseModel):
    """Request model for job application"""

    user_id: int = Field(..., description="User ID for the applicant")
    form_data: Dict[str, Any] = Field(..., description="Form data to fill")
    cover_letter: Optional[str] = Field(None, description="Cover letter text")
    resume_file: Optional[str] = Field(None, description="Path to resume file")
    additional_info: Optional[Dict[str, Any]] = Field(
        default_factory=dict, description="Additional information"
    )


class FormExtractionRequest(BaseModel):
    """Request model for form extraction"""

    url: str = Field(..., description="URL to extract form fields from")


class BatchApplicationRequest(BaseModel):
    """Request model for batch applications"""

    user_id: int = Field(..., description="User ID for the applicant")
    job_ids: List[str] = Field(..., description="List of job IDs to apply to")
    form_data: Dict[str, Any] = Field(
        ..., description="Form data to use for all applications"
    )
    max_applications: int = Field(
        default=10, description="Maximum number of applications to attempt"
    )


# Response Models
class JobSearchResponse(BaseModel):
    """Response model for job search"""

    search_query: str = Field(..., description="The search query used")
    total_jobs_found: int = Field(..., description="Total number of jobs found")
    jobs: List[JobPosition] = Field(..., description="List of job positions")
    search_timestamp: str = Field(..., description="When the search was performed")
    success: bool = Field(..., description="Whether the search was successful")
    error_message: Optional[str] = Field(
        None, description="Error message if search failed"
    )


class JobApplicationResponse(BaseModel):
    """Response model for job application"""

    job_id: str = Field(..., description="ID of the job applied to")
    success: bool = Field(..., description="Whether application was successful")
    filled_fields: List[str] = Field(
        default_factory=list, description="List of successfully filled fields"
    )
    failed_fields: List[str] = Field(
        default_factory=list, description="List of fields that failed to fill"
    )
    error_message: Optional[str] = Field(
        None, description="Error message if application failed"
    )
    application_timestamp: Optional[datetime] = None


class FormExtractionResponse(BaseModel):
    """Response model for form extraction"""

    url: str = Field(..., description="The URL that was processed")
    form_fields: List[FormField] = Field(
        ..., description="List of detected form fields"
    )
    success: bool = Field(..., description="Whether extraction was successful")
    error_message: Optional[str] = Field(
        None, description="Error message if extraction failed"
    )


class BatchApplicationResponse(BaseModel):
    """Response model for batch applications"""

    total_attempted: int = Field(..., description="Total applications attempted")
    successful_applications: int = Field(
        ..., description="Number of successful applications"
    )
    failed_applications: int = Field(..., description="Number of failed applications")
    application_results: List[Dict[str, Any]] = Field(
        ..., description="Detailed results for each application"
    )
    execution_time: float = Field(..., description="Total execution time in seconds")


# Analytics Models
class SearchStatistics(BaseModel):
    """Model for search statistics"""

    total_searches: int
    total_jobs_found: int
    average_jobs_per_search: float
    most_searched_titles: List[Dict[str, Any]]
    most_searched_locations: List[Dict[str, Any]]
    search_timeline: List[Dict[str, Any]]


class ApplicationStatistics(BaseModel):
    """Model for application statistics"""

    total_applications: int
    successful_applications: int
    failed_applications: int
    success_rate: float
    average_application_time: float
    most_applied_companies: List[Dict[str, Any]]
    application_timeline: List[Dict[str, Any]]


# Health Check Models
class ServiceHealth(BaseModel):
    """Model for service health status"""

    status: str = Field(..., description="Service status (healthy, unhealthy, unknown)")
    message: Optional[str] = Field(None, description="Additional status message")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Health check timestamp"
    )


class HealthResponse(BaseModel):
    """Response model for health check"""

    status: str = Field(..., description="Overall system status")
    timestamp: datetime = Field(
        default_factory=datetime.now, description="Health check timestamp"
    )
    services: Dict[str, ServiceHealth] = Field(
        ..., description="Health status of individual services"
    )
