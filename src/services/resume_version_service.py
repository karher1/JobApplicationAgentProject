import logging
import asyncio
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from src.services.llm_service import LLMService
from src.services.user_profile_service import UserProfileService
from src.services.resume_analysis_service import ResumeAnalysisService
from src.models.user_profile import Resume, ResumeCreate

logger = logging.getLogger(__name__)

class ResumeVersionService:
    """Service for managing multiple resume versions tailored for different job types"""
    
    def __init__(self, user_profile_service: UserProfileService):
        self.llm_service = LLMService()
        self.user_profile_service = user_profile_service
        self.analysis_service = ResumeAnalysisService()
    
    async def create_targeted_resume_version(
        self, 
        user_id: int, 
        original_resume_text: str, 
        target_job_type: str,
        target_industry: str,
        job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Create a new resume version optimized for a specific job type/industry"""
        try:
            # Generate optimized resume content
            optimized_content = await self._generate_optimized_resume(
                original_resume_text, 
                target_job_type, 
                target_industry, 
                job_description
            )
            
            # Analyze the new version
            analysis = await self.analysis_service.analyze_resume_strength(
                optimized_content, 
                job_description
            )
            
            # Save as new resume version
            version_name = f"{target_job_type}_{target_industry}_{datetime.now().strftime('%Y%m%d')}"
            
            resume_data = ResumeCreate(
                user_id=user_id,
                filename=f"{version_name}.txt",
                file_content=optimized_content.encode(),
                file_size=len(optimized_content),
                content_type="text/plain",
                is_primary=False,
                version_notes=f"Optimized for {target_job_type} roles in {target_industry}"
            )
            
            new_resume = await self.user_profile_service.create_resume_version(resume_data)
            
            return {
                "success": True,
                "resume_id": new_resume.id,
                "version_name": version_name,
                "target_job_type": target_job_type,
                "target_industry": target_industry,
                "optimized_content": optimized_content,
                "analysis": analysis,
                "improvements_made": await self._describe_improvements(
                    original_resume_text, 
                    optimized_content
                )
            }
            
        except Exception as e:
            logger.error(f"Error creating targeted resume version: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_optimized_resume(
        self, 
        original_text: str, 
        job_type: str, 
        industry: str, 
        job_description: Optional[str] = None
    ) -> str:
        """Generate optimized resume content using AI"""
        try:
            job_context = f"\n\nSpecific Job Description:\n{job_description}" if job_description else ""
            
            prompt = f"""
Optimize this resume for {job_type} positions in the {industry} industry. 

Guidelines:
1. Maintain all factual information - do not fabricate experience or skills
2. Reorder sections to highlight most relevant experience first
3. Adjust language and keywords to match industry terminology
4. Emphasize achievements and skills most relevant to {job_type} roles
5. Ensure ATS compatibility with proper formatting
6. Add relevant keywords naturally throughout the content
7. Strengthen action verbs and quantify achievements where possible
8. Customize professional summary for the target role

Target: {job_type} in {industry}{job_context}

Original Resume:
{original_text}

Return the optimized resume with the same overall structure but enhanced for the target role:
"""
            
            response = await self.llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating optimized resume: {e}")
            return original_text
    
    async def _describe_improvements(self, original: str, optimized: str) -> List[str]:
        """Describe what improvements were made to the resume"""
        try:
            prompt = f"""
Compare these two resume versions and list the key improvements made in the optimized version.
Focus on specific changes like:
- Keywords added
- Sections reordered
- Language improvements
- Achievements enhanced
- Skills emphasized

Original Resume (first 500 chars):
{original[:500]}...

Optimized Resume (first 500 chars):
{optimized[:500]}...

Return a JSON array of improvement descriptions:
["improvement 1", "improvement 2", ...]
"""
            
            response = await self.llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            try:
                import json
                improvements = json.loads(response)
                return improvements if isinstance(improvements, list) else []
            except json.JSONDecodeError:
                return ["Resume optimized for target role and industry"]
                
        except Exception as e:
            logger.error(f"Error describing improvements: {e}")
            return ["Resume optimized for target role and industry"]
    
    async def compare_resume_versions(
        self, 
        user_id: int, 
        version_ids: List[int], 
        job_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """Compare multiple resume versions and recommend the best one"""
        try:
            if len(version_ids) < 2:
                raise ValueError("Need at least 2 resume versions to compare")
            
            # Get resume versions
            resumes = []
            for version_id in version_ids:
                resume = await self.user_profile_service.get_resume(user_id, version_id)
                if resume:
                    resumes.append(resume)
            
            if len(resumes) < 2:
                raise ValueError("Could not retrieve enough resume versions")
            
            # Analyze each version
            analyses = []
            for resume in resumes:
                resume_text = resume.file_content.decode() if isinstance(resume.file_content, bytes) else resume.file_content
                analysis = await self.analysis_service.analyze_resume_strength(
                    resume_text, 
                    job_description
                )
                analyses.append({
                    "resume_id": resume.id,
                    "filename": resume.filename,
                    "analysis": analysis
                })
            
            # Find best version
            best_version = max(analyses, key=lambda x: x["analysis"]["overall_score"])
            
            return {
                "success": True,
                "comparison_results": analyses,
                "recommended_version": best_version,
                "comparison_summary": await self._generate_comparison_summary(analyses),
                "job_description_provided": job_description is not None
            }
            
        except Exception as e:
            logger.error(f"Error comparing resume versions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _generate_comparison_summary(self, analyses: List[Dict]) -> str:
        """Generate a summary of the comparison results"""
        try:
            best = max(analyses, key=lambda x: x["analysis"]["overall_score"])
            worst = min(analyses, key=lambda x: x["analysis"]["overall_score"])
            
            summary = f"""
Resume Comparison Summary:

Best Version: {best['filename']} (Score: {best['analysis']['overall_score']}/100)
- Strengths: {', '.join(best['analysis'].get('content_strength', {}).get('strengths', [])[:3])}

Lowest Version: {worst['filename']} (Score: {worst['analysis']['overall_score']}/100)

Score Difference: {best['analysis']['overall_score'] - worst['analysis']['overall_score']} points

We recommend using {best['filename']} for your applications.
"""
            return summary.strip()
            
        except Exception as e:
            logger.error(f"Error generating comparison summary: {e}")
            return "Comparison completed. Check individual analysis results for details."
    
    async def get_user_resume_versions(self, user_id: int) -> Dict[str, Any]:
        """Get all resume versions for a user with their metadata"""
        try:
            resumes = await self.user_profile_service.get_user_resumes(user_id)
            
            versions = []
            for resume in resumes:
                versions.append({
                    "id": resume.id,
                    "filename": resume.filename,
                    "created_at": resume.created_at,
                    "is_primary": resume.is_primary,
                    "version_notes": getattr(resume, 'version_notes', ''),
                    "file_size": resume.file_size,
                    "last_analyzed": None  # Could add analysis timestamp if stored
                })
            
            return {
                "success": True,
                "user_id": user_id,
                "total_versions": len(versions),
                "primary_version": next((v for v in versions if v["is_primary"]), None),
                "versions": versions
            }
            
        except Exception as e:
            logger.error(f"Error getting user resume versions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def generate_industry_specific_versions(
        self, 
        user_id: int, 
        original_resume_id: int, 
        target_industries: List[str]
    ) -> Dict[str, Any]:
        """Generate multiple resume versions for different industries"""
        try:
            # Get original resume
            original_resume = await self.user_profile_service.get_resume(user_id, original_resume_id)
            if not original_resume:
                raise ValueError("Original resume not found")
            
            original_text = original_resume.file_content.decode() if isinstance(original_resume.file_content, bytes) else original_resume.file_content
            
            results = []
            successful_versions = 0
            failed_versions = 0
            
            for industry in target_industries:
                try:
                    # Determine common job type for the industry
                    job_type = await self._suggest_job_type_for_industry(industry, original_text)
                    
                    # Create optimized version
                    version_result = await self.create_targeted_resume_version(
                        user_id=user_id,
                        original_resume_text=original_text,
                        target_job_type=job_type,
                        target_industry=industry
                    )
                    
                    if version_result["success"]:
                        successful_versions += 1
                    else:
                        failed_versions += 1
                    
                    results.append({
                        "industry": industry,
                        "job_type": job_type,
                        "result": version_result
                    })
                    
                except Exception as e:
                    failed_versions += 1
                    results.append({
                        "industry": industry,
                        "job_type": "Unknown",
                        "result": {
                            "success": False,
                            "error": str(e)
                        }
                    })
            
            return {
                "success": True,
                "original_resume_id": original_resume_id,
                "target_industries": target_industries,
                "successful_versions": successful_versions,
                "failed_versions": failed_versions,
                "results": results
            }
            
        except Exception as e:
            logger.error(f"Error generating industry-specific versions: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    async def _suggest_job_type_for_industry(self, industry: str, resume_text: str) -> str:
        """Suggest appropriate job type based on industry and resume content"""
        try:
            prompt = f"""
Based on this resume and target industry, suggest the most appropriate job type/role.

Industry: {industry}
Resume (first 300 chars): {resume_text[:300]}...

Return just the job type (e.g., "Software Engineer", "Data Analyst", "Product Manager", "Marketing Specialist"):
"""
            
            response = await self.llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            return response.strip()
            
        except Exception as e:
            logger.error(f"Error suggesting job type: {e}")
            return "Professional"