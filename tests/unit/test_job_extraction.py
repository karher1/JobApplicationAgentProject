#!/usr/bin/env python3
"""
Test script to verify Enhanced Job Description Extractor (Module 3) functionality
"""

import os
import asyncio
import logging
from dotenv import load_dotenv

from services.job_extraction_service import JobExtractionService
from services.llm_service import LLMService
from models.job_extraction import JobExtractionRequest, BatchExtractionRequest

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_job_extraction():
    """Test enhanced job extraction functionality"""
    try:
        print("🔍 Testing Enhanced Job Description Extractor (Module 3)...")
        
        # Initialize services
        llm_service = LLMService()
        await llm_service.initialize()
        
        job_extraction_service = JobExtractionService(llm_service)
        await job_extraction_service.initialize()
        print("✅ Job extraction service initialized successfully!")
        
        # Test 1: Single job extraction
        print("\n📋 Testing single job extraction...")
        
        sample_job_description = """
        Senior Software Engineer - Python/React
        
        Company: TechCorp Inc.
        Location: San Francisco, CA (Hybrid)
        Salary: $120,000 - $180,000 USD annually
        
        About Us:
        TechCorp is a leading technology company with 500+ employees, founded in 2015. 
        We specialize in AI-powered solutions and are headquartered in San Francisco.
        
        Job Description:
        We are looking for a Senior Software Engineer to join our growing team. 
        You will be responsible for developing and maintaining our web applications.
        
        Requirements:
        - 5+ years of experience in software development
        - Strong proficiency in Python and React
        - Experience with AWS, Docker, and Kubernetes
        - Bachelor's degree in Computer Science or related field
        - Experience with machine learning frameworks (preferred)
        
        Responsibilities:
        - Design and implement scalable web applications
        - Collaborate with cross-functional teams
        - Mentor junior developers
        - Participate in code reviews and technical discussions
        
        Benefits:
        - Health, dental, and vision insurance
        - 401(k) retirement plan with company match
        - Flexible working hours and remote work options
        - Professional development budget
        - Unlimited paid time off
        - Stock options and equity
        
        This is a full-time position with hybrid work arrangement. 
        Visa sponsorship is available for qualified candidates.
        """
        
        extraction_request = JobExtractionRequest(
            job_url="https://example.com/job/senior-software-engineer",
            job_title="Senior Software Engineer",
            company_name="TechCorp Inc.",
            raw_description=sample_job_description
        )
        
        result = await job_extraction_service.extract_job_data(extraction_request)
        
        if result.success:
            print("✅ Job extraction successful!")
            job = result.job_position
            print(f"   - Title: {job.title}")
            print(f"   - Company: {job.company}")
            print(f"   - Confidence: {result.confidence_score:.2f}")
            print(f"   - Extraction time: {result.extraction_time:.2f}s")
            
            if job.salary_info:
                print(f"   - Salary: ${job.salary_info.min_amount:,.0f} - ${job.salary_info.max_amount:,.0f}")
            
            if job.requirements:
                print(f"   - Required skills: {', '.join(job.requirements.required_skills[:5])}")
                print(f"   - Experience level: {job.requirements.experience_level}")
            
            if job.benefits:
                benefits = []
                if job.benefits.health_insurance: benefits.append("Health")
                if job.benefits.remote_work: benefits.append("Remote")
                if job.benefits.professional_development: benefits.append("Professional Dev")
                print(f"   - Benefits: {', '.join(benefits)}")
        else:
            print(f"❌ Job extraction failed: {result.error_message}")
        
        # Test 2: Batch extraction
        print("\n📦 Testing batch job extraction...")
        
        sample_jobs = [
            """
            Junior Python Developer
            Company: StartupXYZ
            Location: Remote
            Salary: $80,000 - $100,000
            
            We're looking for a junior Python developer to join our team.
            Requirements: Python, Django, PostgreSQL, 1-2 years experience.
            Benefits: Health insurance, flexible hours, remote work.
            """,
            """
            DevOps Engineer
            Company: EnterpriseCorp
            Location: New York, NY
            Salary: $130,000 - $160,000
            
            Senior DevOps engineer needed for cloud infrastructure.
            Requirements: AWS, Docker, Kubernetes, 5+ years experience.
            Benefits: Full benefits package, 401(k), stock options.
            """
        ]
        
        batch_request = BatchExtractionRequest(
            job_urls=[
                "https://example.com/job/junior-python",
                "https://example.com/job/devops-engineer"
            ],
            max_concurrent=2
        )
        
        # Note: This would require actual job descriptions, so we'll skip for now
        print("   - Batch extraction test skipped (requires actual job URLs)")
        
        # Test 3: Extraction statistics
        print("\n📊 Testing extraction statistics...")
        stats = await job_extraction_service.get_extraction_statistics()
        print(f"   - Total extractions: {stats.total_extractions}")
        print(f"   - Successful: {stats.successful_extractions}")
        print(f"   - Failed: {stats.failed_extractions}")
        print(f"   - Average confidence: {stats.average_confidence:.2f}")
        
        # Test 4: Health check
        print("\n🏥 Testing service health...")
        health = await job_extraction_service.health_check()
        print(f"   - Status: {health.status}")
        print(f"   - Message: {health.message}")
        
        print("\n🎉 All Job Extraction Module tests completed!")
        print(f"📊 Summary:")
        print(f"   - Single extraction: {'✅ Success' if result.success else '❌ Failed'}")
        print(f"   - Confidence score: {result.confidence_score:.2f}")
        print(f"   - Extraction time: {result.extraction_time:.2f}s")
        print(f"   - Service health: {health.status}")
        
        return result.success
        
    except Exception as e:
        print(f"❌ Error testing job extraction: {e}")
        logger.error(f"Job extraction test failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(test_job_extraction()) 