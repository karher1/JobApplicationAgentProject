from fastapi import APIRouter, HTTPException, Depends, UploadFile, File, Form
from pydantic import BaseModel
from typing import Optional, Dict, Any
import logging

from src.services.resume_analysis_service import ResumeAnalysisService
from src.services.resume_parsing_service import ResumeParsingService
from src.api.middleware.auth_middleware import get_current_user
from src.models.user_profile import User

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/resume-analysis", tags=["resume-analysis"])

class ResumeAnalysisRequest(BaseModel):
    resume_text: str
    job_description: Optional[str] = None

class ResumeComparisonRequest(BaseModel):
    resume_text_1: str
    resume_text_2: str
    job_description: Optional[str] = None

@router.post("/analyze")
async def analyze_resume_strength(
    request: ResumeAnalysisRequest,
    current_user: User = Depends(get_current_user)
):
    """Analyze resume strength and provide optimization recommendations"""
    try:
        analysis_service = ResumeAnalysisService()
        
        result = await analysis_service.analyze_resume_strength(
            resume_text=request.resume_text,
            job_description=request.job_description
        )
        
        return {
            "success": True,
            "user_id": current_user.id,
            "analysis": result
        }
        
    except Exception as e:
        logger.error(f"Error analyzing resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/analyze-file")
async def analyze_resume_file(
    file: UploadFile = File(...),
    job_description: Optional[str] = Form(None),
    current_user: User = Depends(get_current_user)
):
    """Analyze uploaded resume file for strength and optimization"""
    try:
        # Save uploaded file temporarily
        import tempfile
        import os
        from pathlib import Path
        
        with tempfile.NamedTemporaryFile(delete=False, suffix=Path(file.filename).suffix) as temp_file:
            content = await file.read()
            temp_file.write(content)
            temp_file_path = temp_file.name
        
        try:
            # Extract text from file
            parsing_service = ResumeParsingService()
            file_extension = Path(file.filename).suffix.lower()
            text_content = await parsing_service._extract_text_from_file(
                Path(temp_file_path), 
                file_extension
            )
            
            if not text_content:
                raise HTTPException(status_code=400, detail="Could not extract text from file")
            
            # Analyze the extracted text
            analysis_service = ResumeAnalysisService()
            result = await analysis_service.analyze_resume_strength(
                resume_text=text_content,
                job_description=job_description
            )
            
            return {
                "success": True,
                "user_id": current_user.id,
                "filename": file.filename,
                "text_length": len(text_content),
                "analysis": result
            }
            
        finally:
            # Clean up temporary file
            os.unlink(temp_file_path)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error analyzing resume file: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/compare")
async def compare_resume_versions(
    request: ResumeComparisonRequest,
    current_user: User = Depends(get_current_user)
):
    """Compare two resume versions and recommend the better one"""
    try:
        analysis_service = ResumeAnalysisService()
        
        result = await analysis_service.compare_resume_versions(
            resume_text_1=request.resume_text_1,
            resume_text_2=request.resume_text_2,
            job_description=request.job_description
        )
        
        return {
            "success": True,
            "user_id": current_user.id,
            "comparison": result
        }
        
    except Exception as e:
        logger.error(f"Error comparing resumes: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/ats-keywords")
async def get_ats_keywords(
    job_description: str,
    current_user: User = Depends(get_current_user)
):
    """Extract important ATS keywords from a job description"""
    try:
        analysis_service = ResumeAnalysisService()
        
        # Use AI to extract keywords from job description
        from src.services.llm_service import LLMService
        llm_service = LLMService()
        
        prompt = f"""
Extract the most important keywords and phrases from this job description that would be crucial for ATS optimization. Return as JSON.

Return ONLY valid JSON with this structure:
{{
    "technical_skills": ["skill1", "skill2", ...],
    "soft_skills": ["skill1", "skill2", ...], 
    "tools_technologies": ["tool1", "tool2", ...],
    "industry_terms": ["term1", "term2", ...],
    "job_functions": ["function1", "function2", ...],
    "certifications": ["cert1", "cert2", ...],
    "experience_levels": ["level1", "level2", ...]
}}

Job Description:
{job_description}
"""
        
        response = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.1
        )
        
        import json
        import re
        try:
            keywords = json.loads(response)
        except json.JSONDecodeError:
            json_match = re.search(r'\{.*\}', response, re.DOTALL)
            if json_match:
                keywords = json.loads(json_match.group(0))
            else:
                raise ValueError("Invalid JSON response")
        
        return {
            "success": True,
            "user_id": current_user.id,
            "keywords": keywords
        }
        
    except Exception as e:
        logger.error(f"Error extracting ATS keywords: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/optimize-for-job")
async def optimize_resume_for_job(
    resume_text: str,
    job_description: str,
    current_user: User = Depends(get_current_user)
):
    """Generate optimized resume version tailored for a specific job"""
    try:
        from src.services.llm_service import LLMService
        llm_service = LLMService()
        
        prompt = f"""
Optimize this resume for the specific job description provided. Return the optimized resume text with improvements.

Guidelines for optimization:
1. Add relevant keywords from the job description
2. Emphasize relevant experience and skills
3. Reorder sections to highlight most relevant information first
4. Adjust achievement descriptions to match job requirements
5. Maintain truthfulness - only enhance existing content, don't fabricate
6. Keep the same overall structure and formatting
7. Ensure ATS compatibility

Job Description:
{job_description}

Original Resume:
{resume_text}

Return the optimized resume text:
"""
        
        optimized_resume = await llm_service.chat_completion(
            messages=[{"role": "user", "content": prompt}],
            temperature=0.3
        )
        
        # Also provide analysis of changes made
        analysis_service = ResumeAnalysisService()
        
        # Compare original vs optimized
        comparison = await analysis_service.compare_resume_versions(
            resume_text_1=resume_text,
            resume_text_2=optimized_resume,
            job_description=job_description
        )
        
        return {
            "success": True,
            "user_id": current_user.id,
            "original_resume": resume_text,
            "optimized_resume": optimized_resume,
            "improvement_analysis": comparison
        }
        
    except Exception as e:
        logger.error(f"Error optimizing resume: {e}")
        raise HTTPException(status_code=500, detail=str(e))