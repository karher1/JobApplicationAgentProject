"""
Configuration management for the Job Application Automation system
"""

import os
from typing import Optional
from pydantic import Field
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings"""
    
    # API Configuration
    app_name: str = "Job Application Automation API"
    app_version: str = "1.0.0"
    debug: bool = Field(default=False, env="DEBUG")
    
    # Database Configuration
    supabase_url: Optional[str] = Field(default=None, env="SUPABASE_URL")
    supabase_key: Optional[str] = Field(default=None, env="SUPABASE_KEY")
    supabase_anon_key: Optional[str] = Field(default=None, env="SUPABASE_ANON_KEY")
    supabase_service_role_key: Optional[str] = Field(default=None, env="SUPABASE_SERVICE_ROLE_KEY")
    database_url: Optional[str] = Field(default=None, env="DATABASE_URL")
    
    # OpenAI Configuration
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4o-mini", env="OPENAI_MODEL")
    
    # Pinecone Configuration
    pinecone_api_key: Optional[str] = Field(default=None, env="PINECONE_API_KEY")
    pinecone_environment: Optional[str] = Field(default=None, env="PINECONE_ENVIRONMENT")
    pinecone_index_name: str = Field(default="job-embeddings", env="PINECONE_INDEX_NAME")
    
    # Email Configuration
    smtp_server: str = Field(default="smtp.gmail.com", env="SMTP_SERVER")
    smtp_port: int = Field(default=587, env="SMTP_PORT")
    smtp_username: Optional[str] = Field(default=None, env="SMTP_USERNAME")
    smtp_password: Optional[str] = Field(default=None, env="SMTP_PASSWORD")
    from_email: str = Field(default="noreply@jobapplicationagent.com", env="FROM_EMAIL")
    from_name: str = Field(default="Job Application Agent", env="FROM_NAME")
    
    # Base URLs
    base_url: str = Field(default="http://localhost:8000", env="BASE_URL")
    
    # Job Search Configuration
    max_jobs_per_search: int = Field(default=50, env="MAX_JOBS_PER_SEARCH")
    search_delay: float = Field(default=2.0, env="SEARCH_DELAY")
    
    # Selenium Configuration
    chrome_driver_path: Optional[str] = Field(default=None, env="CHROME_DRIVER_PATH")
    headless_mode: bool = Field(default=True, env="HEADLESS_MODE")
    
    # JWT Configuration
    secret_key: Optional[str] = Field(default=None, env="SECRET_KEY")
    
    class Config:
        env_file = ".env"
        case_sensitive = False
        extra = "ignore"  # Ignore extra fields in .env

# Global settings instance
settings = Settings()

def get_settings() -> Settings:
    """Get application settings"""
    return settings 