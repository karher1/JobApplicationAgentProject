import logging
import asyncio
from typing import Dict, List, Any, Optional
import re
from datetime import datetime

from src.services.llm_service import LLMService

logger = logging.getLogger(__name__)

class ResumeAnalysisService:
    """Service for analyzing resume strength and providing ATS optimization recommendations"""
    
    def __init__(self):
        self.llm_service = LLMService()
    
    async def analyze_resume_strength(self, resume_text: str, job_description: Optional[str] = None) -> Dict[str, Any]:
        """Analyze resume strength and provide comprehensive feedback"""
        try:
            analysis_tasks = [
                self._analyze_ats_compatibility(resume_text),
                self._analyze_content_strength(resume_text),
                self._analyze_keyword_optimization(resume_text, job_description),
                self._analyze_formatting_structure(resume_text),
                self._generate_improvement_suggestions(resume_text, job_description)
            ]
            
            results = await asyncio.gather(*analysis_tasks, return_exceptions=True)
            
            # Process results and handle exceptions
            ats_score = results[0] if not isinstance(results[0], Exception) else {"score": 0, "issues": ["Analysis failed"]}
            content_score = results[1] if not isinstance(results[1], Exception) else {"score": 0, "feedback": []}
            keyword_analysis = results[2] if not isinstance(results[2], Exception) else {"missing_keywords": [], "keyword_density": {}}
            formatting_analysis = results[3] if not isinstance(results[3], Exception) else {"issues": [], "recommendations": []}
            improvement_suggestions = results[4] if not isinstance(results[4], Exception) else {"suggestions": []}
            
            # Calculate overall score
            overall_score = self._calculate_overall_score(ats_score, content_score)
            
            return {
                "overall_score": overall_score,
                "ats_compatibility": ats_score,
                "content_strength": content_score,
                "keyword_optimization": keyword_analysis,
                "formatting_analysis": formatting_analysis,
                "improvement_suggestions": improvement_suggestions["suggestions"],
                "analysis_timestamp": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error analyzing resume strength: {e}")
            return {
                "overall_score": 0,
                "error": str(e),
                "analysis_timestamp": datetime.now().isoformat()
            }
    
    async def _analyze_ats_compatibility(self, resume_text: str) -> Dict[str, Any]:
        """Analyze ATS compatibility and parsing issues"""
        try:
            prompt = f"""
Analyze this resume for ATS (Applicant Tracking System) compatibility. Return your analysis as JSON.

Return ONLY valid JSON with this structure:
{{
    "score": 85,
    "issues": [
        "Issue description 1",
        "Issue description 2"
    ],
    "recommendations": [
        "Recommendation 1",
        "Recommendation 2"
    ]
}}

ATS Analysis Criteria:
- Text extractability and readability
- Standard section headers
- Contact information placement
- Date formatting consistency
- Font and formatting simplicity
- File format compatibility
- Keyword placement and density
- Section organization

Score from 0-100 where:
- 90-100: Excellent ATS compatibility
- 80-89: Good compatibility with minor issues
- 70-79: Moderate compatibility, needs improvement
- 60-69: Poor compatibility, significant issues
- Below 60: Major ATS parsing problems

Resume text:
{resume_text}
"""
            
            response = await self.llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                # Extract JSON if wrapped in text
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                raise ValueError("Invalid JSON response")
                
        except Exception as e:
            logger.error(f"Error in ATS analysis: {e}")
            return {
                "score": 0,
                "issues": ["ATS analysis failed"],
                "recommendations": ["Please check resume formatting"]
            }
    
    async def _analyze_content_strength(self, resume_text: str) -> Dict[str, Any]:
        """Analyze content quality and impact"""
        try:
            prompt = f"""
Analyze the content strength of this resume. Return your analysis as JSON.

Return ONLY valid JSON with this structure:
{{
    "score": 78,
    "strengths": [
        "Strong achievement 1",
        "Strong achievement 2"
    ],
    "weaknesses": [
        "Weakness 1",
        "Weakness 2"
    ],
    "feedback": [
        "Specific feedback 1",
        "Specific feedback 2"
    ]
}}

Content Analysis Criteria:
- Achievement quantification (numbers, percentages, results)
- Action verb usage and impact
- Relevance to target roles
- Technical skills demonstration
- Leadership and collaboration examples
- Problem-solving examples
- Career progression clarity
- Professional summary effectiveness

Score from 0-100 based on content quality and impact.

Resume text:
{resume_text}
"""
            
            response = await self.llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                raise ValueError("Invalid JSON response")
                
        except Exception as e:
            logger.error(f"Error in content analysis: {e}")
            return {
                "score": 0,
                "strengths": [],
                "weaknesses": ["Content analysis failed"],
                "feedback": ["Please review resume content"]
            }
    
    async def _analyze_keyword_optimization(self, resume_text: str, job_description: Optional[str] = None) -> Dict[str, Any]:
        """Analyze keyword optimization for job matching"""
        try:
            if not job_description:
                # Generic keyword analysis
                return await self._generic_keyword_analysis(resume_text)
            
            prompt = f"""
Compare this resume against the job description and analyze keyword optimization. Return as JSON.

Return ONLY valid JSON with this structure:
{{
    "keyword_match_score": 65,
    "missing_keywords": [
        "important keyword 1",
        "important keyword 2"
    ],
    "present_keywords": [
        "keyword 1",
        "keyword 2"
    ],
    "keyword_density": {{
        "keyword1": 3,
        "keyword2": 1
    }},
    "recommendations": [
        "Add specific keyword recommendations",
        "Improve keyword placement"
    ]
}}

Job Description:
{job_description}

Resume:
{resume_text}
"""
            
            response = await self.llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.1
            )
            
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                raise ValueError("Invalid JSON response")
                
        except Exception as e:
            logger.error(f"Error in keyword analysis: {e}")
            return {
                "keyword_match_score": 0,
                "missing_keywords": [],
                "present_keywords": [],
                "keyword_density": {},
                "recommendations": ["Keyword analysis failed"]
            }
    
    async def _generic_keyword_analysis(self, resume_text: str) -> Dict[str, Any]:
        """Perform generic keyword analysis when no job description is provided"""
        # Extract common technical keywords
        tech_keywords = [
            "Python", "Java", "JavaScript", "React", "Node.js", "SQL", "AWS", "Docker",
            "Kubernetes", "Git", "Agile", "Scrum", "Machine Learning", "Data Analysis",
            "API", "REST", "GraphQL", "MongoDB", "PostgreSQL", "Redis", "Linux"
        ]
        
        found_keywords = []
        keyword_density = {}
        
        for keyword in tech_keywords:
            count = len(re.findall(r'\b' + re.escape(keyword) + r'\b', resume_text, re.IGNORECASE))
            if count > 0:
                found_keywords.append(keyword)
                keyword_density[keyword] = count
        
        return {
            "keyword_match_score": min(len(found_keywords) * 5, 100),
            "missing_keywords": [kw for kw in tech_keywords if kw not in found_keywords],
            "present_keywords": found_keywords,
            "keyword_density": keyword_density,
            "recommendations": [
                "Add more relevant technical keywords",
                "Consider industry-specific terminology",
                "Include both acronyms and full terms"
            ]
        }
    
    async def _analyze_formatting_structure(self, resume_text: str) -> Dict[str, Any]:
        """Analyze formatting and structure issues"""
        issues = []
        recommendations = []
        
        # Check for common formatting issues
        if len(resume_text.split('\n')) < 10:
            issues.append("Resume appears to have poor line breaks or structure")
            recommendations.append("Ensure proper section organization with clear headers")
        
        # Check for contact information
        if not re.search(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', resume_text):
            issues.append("No email address found")
            recommendations.append("Include a professional email address")
        
        # Check for phone number
        if not re.search(r'(\+?1[-.\s]?)?\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})', resume_text):
            issues.append("No phone number found")
            recommendations.append("Include a contact phone number")
        
        # Check for dates
        if not re.search(r'\d{4}', resume_text):
            issues.append("No dates found - include employment and education dates")
            recommendations.append("Add clear start and end dates for all positions")
        
        # Check for section headers
        section_headers = ['experience', 'education', 'skills', 'work', 'employment']
        found_sections = sum(1 for header in section_headers if header.lower() in resume_text.lower())
        
        if found_sections < 2:
            issues.append("Missing standard resume sections")
            recommendations.append("Include clear sections: Experience, Education, Skills")
        
        return {
            "issues": issues,
            "recommendations": recommendations,
            "formatting_score": max(0, 100 - len(issues) * 15)
        }
    
    async def _generate_improvement_suggestions(self, resume_text: str, job_description: Optional[str] = None) -> Dict[str, Any]:
        """Generate specific improvement suggestions"""
        try:
            context = f"Job Description: {job_description}\n\n" if job_description else ""
            
            prompt = f"""
Provide specific, actionable improvement suggestions for this resume. Return as JSON.

Return ONLY valid JSON with this structure:
{{
    "suggestions": [
        {{
            "category": "Content",
            "priority": "High",
            "suggestion": "Add quantified achievements with specific numbers and results",
            "example": "Instead of 'Improved system performance', write 'Improved system performance by 40%, reducing load times from 3s to 1.8s'"
        }},
        {{
            "category": "Keywords",
            "priority": "Medium", 
            "suggestion": "Include more relevant technical terms",
            "example": "Add specific technologies used in projects"
        }}
    ]
}}

Categories: Content, Keywords, Formatting, Structure, ATS
Priorities: High, Medium, Low

{context}Resume:
{resume_text}
"""
            
            response = await self.llm_service.chat_completion(
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2
            )
            
            import json
            try:
                return json.loads(response)
            except json.JSONDecodeError:
                json_match = re.search(r'\{.*\}', response, re.DOTALL)
                if json_match:
                    return json.loads(json_match.group(0))
                raise ValueError("Invalid JSON response")
                
        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")
            return {
                "suggestions": [
                    {
                        "category": "General",
                        "priority": "High",
                        "suggestion": "Review and optimize resume content for better impact",
                        "example": "Use action verbs and quantify achievements"
                    }
                ]
            }
    
    def _calculate_overall_score(self, ats_score: Dict, content_score: Dict) -> int:
        """Calculate overall resume score from component scores"""
        try:
            ats = ats_score.get("score", 0)
            content = content_score.get("score", 0)
            
            # Weighted average: ATS 40%, Content 60%
            overall = int(ats * 0.4 + content * 0.6)
            return min(max(overall, 0), 100)
            
        except Exception:
            return 0
    
    async def compare_resume_versions(self, resume_text_1: str, resume_text_2: str, job_description: Optional[str] = None) -> Dict[str, Any]:
        """Compare two resume versions and provide recommendations"""
        try:
            # Analyze both versions
            analysis_1 = await self.analyze_resume_strength(resume_text_1, job_description)
            analysis_2 = await self.analyze_resume_strength(resume_text_2, job_description)
            
            # Compare scores
            better_version = 1 if analysis_1["overall_score"] > analysis_2["overall_score"] else 2
            score_difference = abs(analysis_1["overall_score"] - analysis_2["overall_score"])
            
            return {
                "version_1_score": analysis_1["overall_score"],
                "version_2_score": analysis_2["overall_score"],
                "better_version": better_version,
                "score_difference": score_difference,
                "recommendation": f"Version {better_version} is stronger by {score_difference} points",
                "detailed_comparison": {
                    "version_1": analysis_1,
                    "version_2": analysis_2
                }
            }
            
        except Exception as e:
            logger.error(f"Error comparing resume versions: {e}")
            return {"error": str(e)}