#!/usr/bin/env python3
"""
Simple test script for the FastAPI backend
"""

import asyncio
import logging
from services.database_service import DatabaseService
from services.vector_service import VectorService
from services.llm_service import LLMService
from services.job_search_service import JobSearchService
from services.job_application_service import JobApplicationService

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_services():
    """Test all services initialization"""
    try:
        logger.info("Testing service initialization...")
        
        # Initialize services
        database_service = DatabaseService()
        vector_service = VectorService()
        llm_service = LLMService()
        job_search_service = JobSearchService(database_service, vector_service, llm_service)
        job_application_service = JobApplicationService(database_service, llm_service)
        
        # Test database service
        logger.info("Testing database service...")
        try:
            await database_service.initialize()
            health = await database_service.health_check()
            logger.info(f"Database health: {health.status}")
        except Exception as e:
            logger.warning(f"Database service test failed: {e}")
        
        # Test LLM service
        logger.info("Testing LLM service...")
        try:
            await llm_service.initialize()
            health = await llm_service.health_check()
            logger.info(f"LLM health: {health.status}")
        except Exception as e:
            logger.warning(f"LLM service test failed: {e}")
        
        # Test vector service (optional - requires Pinecone)
        logger.info("Testing vector service...")
        try:
            await vector_service.initialize()
            health = await vector_service.health_check()
            logger.info(f"Vector health: {health.status}")
        except Exception as e:
            logger.warning(f"Vector service test failed: {e}")
        
        # Test job search service
        logger.info("Testing job search service...")
        try:
            # Add sample jobs
            await job_search_service.add_sample_jobs()
            
            # Search for jobs
            jobs = await job_search_service.search_jobs(
                job_titles=["QA Engineer", "SDET"],
                locations=["Remote"],
                max_results=10
            )
            logger.info(f"Found {len(jobs)} jobs")
            
            for job in jobs:
                logger.info(f"- {job.title} at {job.company}")
                
        except Exception as e:
            logger.warning(f"Job search service test failed: {e}")
        
        logger.info("Service tests completed!")
        
    except Exception as e:
        logger.error(f"Test failed: {e}")

async def test_form_extraction():
    """Test form extraction (without actually visiting URLs)"""
    try:
        logger.info("Testing form extraction service...")
        
        database_service = DatabaseService()
        llm_service = LLMService()
        job_application_service = JobApplicationService(database_service, llm_service)
        
        # Test with a sample URL (won't actually visit it)
        sample_url = "https://example.com/job-application"
        logger.info(f"Would extract form fields from: {sample_url}")
        
        # Test LLM form data generation
        await llm_service.initialize()
        
        # Create sample form fields
        from models.schemas import FormField, FieldType
        
        sample_fields = [
            FormField(
                label="First Name",
                field_type=FieldType.TEXT,
                required=True
            ),
            FormField(
                label="Email",
                field_type=FieldType.EMAIL,
                required=True
            ),
            FormField(
                label="Cover Letter",
                field_type=FieldType.TEXTAREA,
                required=False
            )
        ]
        
        # Generate form data
        form_data = await llm_service.generate_form_data(sample_fields)
        logger.info(f"Generated form data: {form_data}")
        
    except Exception as e:
        logger.error(f"Form extraction test failed: {e}")

if __name__ == "__main__":
    logger.info("Starting FastAPI backend tests...")
    
    # Run tests
    asyncio.run(test_services())
    asyncio.run(test_form_extraction())
    
    logger.info("All tests completed!") 