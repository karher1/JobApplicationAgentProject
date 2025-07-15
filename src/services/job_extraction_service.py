import os
import logging
import asyncio
import json
import time
from typing import List, Optional, Dict, Any
from datetime import datetime
from urllib.parse import urlparse
import re

from openai import OpenAI
from supabase import create_client, Client
from src.models.job_extraction import (
    EnhancedJobPosition, JobExtractionRequest, JobExtractionResponse,
    BatchExtractionRequest, BatchExtractionResponse, ExtractionStats,
    SalaryInfo, CompanyInfo, JobRequirements, JobBenefits,
    ExperienceLevel, JobType, RemoteType, SalaryType
)
from src.models.schemas import ServiceHealth, JobPosition
from src.services.llm_service import LLMService
from src.core.config import get_settings

logger = logging.getLogger(__name__)

class JobExtractionService:
    """Enhanced service for extracting structured data from job descriptions using LLM"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.openai_client = None
        settings = get_settings()
        self.supabase_url = settings.supabase_url
        self.supabase_key = settings.supabase_anon_key
        self.supabase: Optional[Client] = None
        
        # Extraction templates
        self.extraction_templates = self._load_extraction_templates()
        
    async def initialize(self):
        """Initialize the extraction service"""
        try:
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Supabase URL and key must be set")
            
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            self.openai_client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
            
            logger.info("Job extraction service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing job extraction service: {e}")
            raise
    
    async def health_check(self) -> ServiceHealth:
        """Check extraction service health"""
        try:
            if not self.supabase or not self.openai_client:
                return ServiceHealth(status="unhealthy", message="Service not initialized")
            
            # Test OpenAI connection
            response = self.openai_client.models.list()
            
            return ServiceHealth(status="healthy", message="Extraction service ready")
        except Exception as e:
            return ServiceHealth(status="unhealthy", message=str(e))
    
    def _load_extraction_templates(self) -> Dict[str, str]:
        """Load extraction prompt templates"""
        return {
            "job_extraction": """
You are an expert job description analyzer. Extract structured information from the following job posting.

Job Title: {job_title}
Company: {company_name}
URL: {job_url}

Job Description:
{job_description}

Please extract the following information in JSON format:

{{
    "salary_info": {{
        "min_amount": <number or null>,
        "max_amount": <number or null>,
        "currency": "USD",
        "salary_type": "annual|hourly|monthly|project_based",
        "is_negotiable": <boolean>,
        "includes_equity": <boolean>,
        "includes_benefits": <boolean>
    }},
    "company_info": {{
        "name": "<company name>",
        "industry": "<industry or null>",
        "size": "<company size or null>",
        "founded_year": <year or null>,
        "location": "<headquarters location or null>",
        "website": "<website or null>",
        "description": "<company description or null>"
    }},
    "requirements": {{
        "required_skills": ["<skill1>", "<skill2>"],
        "preferred_skills": ["<skill1>", "<skill2>"],
        "required_experience_years": <number or null>,
        "experience_level": "entry|junior|mid|senior|lead|principal|executive",
        "required_education": "<education level or null>",
        "certifications": ["<cert1>", "<cert2>"],
        "languages": ["<lang1>", "<lang2>"]
    }},
    "benefits": {{
        "health_insurance": <boolean>,
        "dental_insurance": <boolean>,
        "vision_insurance": <boolean>,
        "retirement_plan": <boolean>,
        "paid_time_off": <boolean>,
        "flexible_hours": <boolean>,
        "remote_work": <boolean>,
        "professional_development": <boolean>,
        "other_benefits": ["<benefit1>", "<benefit2>"]
    }},
    "additional_info": {{
        "responsibilities": ["<responsibility1>", "<responsibility2>"],
        "qualifications": ["<qualification1>", "<qualification2>"],
        "application_deadline": "<date or null>",
        "start_date": "<date or null>",
        "contract_duration": "<duration or null>",
        "travel_requirements": "<requirements or null>",
        "visa_sponsorship": <boolean>,
        "job_type": "full_time|part_time|contract|internship|freelance",
        "remote_type": "onsite|remote|hybrid|flexible"
    }},
    "confidence_score": <float between 0 and 1>
}}

Only include information that is explicitly mentioned in the job description. Use null for missing information. Be accurate and conservative in your extraction.
""",
            
            "salary_extraction": """
Extract salary information from the following text. Look for salary ranges, hourly rates, or compensation details.

Text: {text}

Return JSON:
{{
    "min_amount": <number or null>,
    "max_amount": <number or null>,
    "currency": "USD",
    "salary_type": "annual|hourly|monthly|project_based",
    "is_negotiable": <boolean>,
    "includes_equity": <boolean>,
    "includes_benefits": <boolean>
}}
""",
            
            "skills_extraction": """
Extract technical skills and requirements from the following job description.

Job Description: {job_description}

Return JSON:
{{
    "required_skills": ["<skill1>", "<skill2>"],
    "preferred_skills": ["<skill1>", "<skill2>"],
    "required_experience_years": <number or null>,
    "experience_level": "entry|junior|mid|senior|lead|principal|executive",
    "required_education": "<education level or null>",
    "certifications": ["<cert1>", "<cert2>"],
    "languages": ["<lang1>", "<lang2>"]
}}
"""
        }
    
    async def extract_job_data(self, request: JobExtractionRequest) -> JobExtractionResponse:
        """Extract structured data from a job posting"""
        start_time = time.time()
        
        try:
            logger.info(f"Starting job extraction for URL: {request.job_url}")
            
            # Check if we already have extracted data (unless force re-extraction)
            if not request.force_re_extraction:
                existing_job = await self._get_existing_extraction(request.job_url)
                if existing_job:
                    return JobExtractionResponse(
                        success=True,
                        job_position=existing_job,
                        extraction_time=time.time() - start_time,
                        confidence_score=existing_job.extraction_confidence or 0.0
                    )
            
            # Get job description text
            job_description = request.raw_description
            if not job_description:
                job_description = await self._scrape_job_description(request.job_url)
            
            if not job_description:
                raise ValueError("Could not retrieve job description")
            
            # Extract structured data using LLM
            extraction_data = await self._extract_with_llm(
                job_title=request.job_title or "Unknown",
                company_name=request.company_name or "Unknown",
                job_url=request.job_url,
                job_description=job_description
            )
            
            # Create enhanced job position
            enhanced_job = await self._create_enhanced_job_position(
                request=request,
                job_description=job_description,
                extraction_data=extraction_data
            )
            
            # Store in database
            await self._store_enhanced_job(enhanced_job)
            
            extraction_time = time.time() - start_time
            
            return JobExtractionResponse(
                success=True,
                job_position=enhanced_job,
                extraction_time=extraction_time,
                confidence_score=extraction_data.get("confidence_score", 0.0)
            )
            
        except Exception as e:
            logger.error(f"Error extracting job data: {e}")
            return JobExtractionResponse(
                success=False,
                job_position=None,
                extraction_time=time.time() - start_time,
                error_message=str(e),
                confidence_score=0.0
            )
    
    async def _extract_with_llm(self, job_title: str, company_name: str, job_url: str, job_description: str) -> Dict[str, Any]:
        """Extract structured data using OpenAI GPT"""
        try:
            prompt = self.extraction_templates["job_extraction"].format(
                job_title=job_title,
                company_name=company_name,
                job_url=job_url,
                job_description=job_description
            )
            
            response = await self.llm_service.generate_structured_response(
                prompt=prompt,
                system_message="You are an expert job description analyzer. Extract structured information accurately and return only valid JSON."
            )
            
            # Parse JSON response
            try:
                extraction_data = json.loads(response)
                return extraction_data
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse LLM response as JSON: {e}")
                # Try to extract JSON from the response
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    try:
                        return json.loads(json_match.group())
                    except json.JSONDecodeError:
                        pass
                
                # Return basic extraction as fallback
                return self._fallback_extraction(job_description)
                
        except Exception as e:
            logger.error(f"Error in LLM extraction: {e}")
            return self._fallback_extraction(job_description)
    
    def _fallback_extraction(self, job_description: str) -> Dict[str, Any]:
        """Fallback extraction using basic text analysis"""
        try:
            # Basic salary extraction
            salary_patterns = [
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*-\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:to|-)\s*\$(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)',
                r'(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*-\s*(\d{1,3}(?:,\d{3})*(?:\.\d{2})?)\s*(?:USD|dollars?)'
            ]
            
            salary_info = {"min_amount": None, "max_amount": None, "currency": "USD", "salary_type": "annual"}
            for pattern in salary_patterns:
                match = re.search(pattern, job_description, re.IGNORECASE)
                if match:
                    try:
                        min_sal = float(match.group(1).replace(',', ''))
                        max_sal = float(match.group(2).replace(',', ''))
                        salary_info = {
                            "min_amount": min_sal,
                            "max_amount": max_sal,
                            "currency": "USD",
                            "salary_type": "annual",
                            "is_negotiable": False,
                            "includes_equity": False,
                            "includes_benefits": False
                        }
                        break
                    except ValueError:
                        continue
            
            # Basic skills extraction
            common_skills = [
                "Python", "JavaScript", "Java", "C++", "C#", "Go", "Rust", "PHP", "Ruby",
                "React", "Vue", "Angular", "Node.js", "Django", "Flask", "FastAPI",
                "Docker", "Kubernetes", "AWS", "Azure", "Google Cloud", "Git",
                "MongoDB", "PostgreSQL", "MySQL", "Redis", "Elasticsearch"
            ]
            
            found_skills = []
            for skill in common_skills:
                if re.search(rf'\b{re.escape(skill)}\b', job_description, re.IGNORECASE):
                    found_skills.append(skill)
            
            return {
                "salary_info": salary_info,
                "company_info": {
                    "name": "Unknown",
                    "industry": None,
                    "size": None,
                    "founded_year": None,
                    "location": None,
                    "website": None,
                    "description": None
                },
                "requirements": {
                    "required_skills": found_skills,
                    "preferred_skills": [],
                    "required_experience_years": None,
                    "experience_level": None,
                    "required_education": None,
                    "certifications": [],
                    "languages": []
                },
                "benefits": {
                    "health_insurance": False,
                    "dental_insurance": False,
                    "vision_insurance": False,
                    "retirement_plan": False,
                    "paid_time_off": False,
                    "flexible_hours": False,
                    "remote_work": False,
                    "professional_development": False,
                    "other_benefits": []
                },
                "additional_info": {
                    "responsibilities": [],
                    "qualifications": [],
                    "application_deadline": None,
                    "start_date": None,
                    "contract_duration": None,
                    "travel_requirements": None,
                    "visa_sponsorship": False,
                    "job_type": None,
                    "remote_type": None
                },
                "confidence_score": 0.3
            }
            
        except Exception as e:
            logger.error(f"Error in fallback extraction: {e}")
            return {"confidence_score": 0.0}
    
    async def _scrape_job_description(self, job_url: str) -> Optional[str]:
        """Scrape job description from URL"""
        try:
            # This is a simplified version - in production you'd use proper web scraping
            # For now, we'll return None and expect the description to be provided
            logger.warning(f"Job description scraping not implemented for URL: {job_url}")
            return None
        except Exception as e:
            logger.error(f"Error scraping job description: {e}")
            return None
    
    async def _create_enhanced_job_position(
        self, 
        request: JobExtractionRequest, 
        job_description: str, 
        extraction_data: Dict[str, Any]
    ) -> EnhancedJobPosition:
        """Create enhanced job position from extraction data"""
        try:
            # Parse extraction data
            salary_info = SalaryInfo(**extraction_data.get("salary_info", {}))
            company_info = CompanyInfo(**extraction_data.get("company_info", {}))
            requirements = JobRequirements(**extraction_data.get("requirements", {}))
            benefits = JobBenefits(**extraction_data.get("benefits", {}))
            additional_info = extraction_data.get("additional_info", {})
            
            # Determine job type and remote type
            job_type_str = additional_info.get("job_type")
            job_type = JobType(job_type_str) if job_type_str else None
            
            remote_type_str = additional_info.get("remote_type")
            remote_type = RemoteType(remote_type_str) if remote_type_str else None
            
            return EnhancedJobPosition(
                title=request.job_title or "Unknown",
                company=request.company_name or company_info.name,
                location="Unknown",  # Would need to extract from URL or description
                url=request.job_url,
                job_board=self._extract_job_board(request.job_url),
                job_type=job_type,
                remote_type=remote_type,
                description_snippet=job_description[:200] + "..." if len(job_description) > 200 else job_description,
                full_description=job_description,
                salary_info=salary_info,
                company_info=company_info,
                requirements=requirements,
                benefits=benefits,
                responsibilities=additional_info.get("responsibilities", []),
                qualifications=additional_info.get("qualifications", []),
                application_deadline=self._parse_date(additional_info.get("application_deadline")),
                start_date=self._parse_date(additional_info.get("start_date")),
                contract_duration=additional_info.get("contract_duration"),
                travel_requirements=additional_info.get("travel_requirements"),
                visa_sponsorship=additional_info.get("visa_sponsorship", False),
                extraction_confidence=extraction_data.get("confidence_score", 0.0),
                extraction_timestamp=datetime.now(),
                raw_extraction_data=extraction_data
            )
            
        except Exception as e:
            logger.error(f"Error creating enhanced job position: {e}")
            raise
    
    def _extract_job_board(self, url: str) -> str:
        """Extract job board from URL"""
        try:
            domain = urlparse(url).netloc.lower()
            if "ashby" in domain:
                return "Ashby"
            elif "linkedin" in domain:
                return "LinkedIn"
            elif "indeed" in domain:
                return "Indeed"
            elif "glassdoor" in domain:
                return "Glassdoor"
            else:
                return "Other"
        except:
            return "Unknown"
    
    def _parse_date(self, date_str: Optional[str]) -> Optional[datetime]:
        """Parse date string to datetime"""
        if not date_str:
            return None
        
        try:
            # Add common date parsing patterns here
            # For now, return None
            return None
        except:
            return None
    
    async def _store_enhanced_job(self, job: EnhancedJobPosition) -> None:
        """Store enhanced job in database"""
        try:
            # Store in enhanced_jobs table (you'll need to create this)
            job_data = job.model_dump()
            job_data["created_at"] = datetime.now()
            job_data["updated_at"] = datetime.now()
            
            # For now, just log the storage
            logger.info(f"Would store enhanced job: {job.title} at {job.company}")
            
        except Exception as e:
            logger.error(f"Error storing enhanced job: {e}")
    
    async def _get_existing_extraction(self, job_url: str) -> Optional[EnhancedJobPosition]:
        """Get existing extraction from database"""
        try:
            # Query enhanced_jobs table
            # For now, return None
            return None
        except Exception as e:
            logger.error(f"Error getting existing extraction: {e}")
            return None
    
    async def batch_extract_jobs(self, request: BatchExtractionRequest) -> BatchExtractionResponse:
        """Extract data from multiple job URLs in batch"""
        start_time = time.time()
        results = []
        successful = 0
        failed = 0
        
        # Process jobs with concurrency limit
        semaphore = asyncio.Semaphore(request.max_concurrent)
        
        async def extract_single_job(job_url: str):
            async with semaphore:
                extraction_request = JobExtractionRequest(job_url=job_url)
                result = await self.extract_job_data(extraction_request)
                return result
        
        # Create tasks for all jobs
        tasks = [extract_single_job(url) for url in request.job_urls]
        
        # Execute all tasks
        batch_results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Process results
        for i, result in enumerate(batch_results):
            if isinstance(result, Exception):
                failed += 1
                results.append(JobExtractionResponse(
                    success=False,
                    job_position=None,
                    extraction_time=0.0,
                    error_message=str(result),
                    confidence_score=0.0
                ))
            else:
                if result.success:
                    successful += 1
                else:
                    failed += 1
                results.append(result)
        
        total_time = time.time() - start_time
        
        return BatchExtractionResponse(
            total_jobs=len(request.job_urls),
            successful_extractions=successful,
            failed_extractions=failed,
            results=results,
            total_time=total_time
        )
    
    async def get_extraction_statistics(self) -> ExtractionStats:
        """Get extraction statistics"""
        try:
            # Query database for statistics
            # For now, return mock data
            return ExtractionStats(
                total_extractions=0,
                successful_extractions=0,
                failed_extractions=0,
                average_confidence=0.0,
                average_extraction_time=0.0,
                most_extracted_companies=[],
                extraction_timeline=[]
            )
        except Exception as e:
            logger.error(f"Error getting extraction statistics: {e}")
            raise
    
    async def validate_extraction(self, job_id: str) -> Dict[str, Any]:
        """Validate extracted job data"""
        try:
            # Get job from database
            # For now, return basic validation
            return {
                "job_id": job_id,
                "overall_valid": True,
                "overall_confidence": 0.8,
                "field_validations": [],
                "recommendations": []
            }
        except Exception as e:
            logger.error(f"Error validating extraction: {e}")
            raise 