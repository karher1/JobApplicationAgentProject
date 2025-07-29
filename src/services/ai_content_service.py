"""
AI Content Generation Service for Job Applications
Handles cover letters, essay questions, and personalized responses
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
import json
import re

from src.services.llm_service import LLMService
from src.models.user_profile import User, UserProfile

logger = logging.getLogger(__name__)


class AIContentService:
    """Service for generating AI-powered content for job applications"""
    
    def __init__(self, llm_service: LLMService):
        self.llm_service = llm_service
        self.max_cover_letter_length = 400  # words
        self.max_essay_length = 300  # words
        
    async def initialize(self):
        """Initialize the AI content service"""
        logger.info("AI Content service initialized successfully")
        
    async def health_check(self) -> Dict[str, Any]:
        """Check the health of the AI content service"""
        try:
            # Test a simple generation to ensure service is working
            test_result = await self.llm_service.chat_completion(
                messages=[{"role": "user", "content": "Say 'AI service is healthy' in exactly those words."}],
                max_tokens=20
            )
            
            is_healthy = "ai service is healthy" in test_result.lower()
            
            return {
                "status": "healthy" if is_healthy else "degraded",
                "message": "AI content generation service is operational",
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "status": "unhealthy",
                "message": f"AI content service error: {str(e)}",
                "timestamp": datetime.now().isoformat()
            }
    
    async def generate_cover_letter(
        self, 
        user_profile: Dict[str, Any], 
        job_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Generate a personalized cover letter"""
        try:
            logger.info(f"Generating cover letter for {job_data.get('title', 'Unknown')} at {job_data.get('company', 'Unknown')}")
            
            prompt = self._build_cover_letter_prompt(user_profile, job_data)
            
            cover_letter = await self.llm_service.generate_response(prompt)
            
            # Clean and format the response
            formatted_letter = self._format_cover_letter(cover_letter)
            
            return {
                "success": True,
                "content": formatted_letter,
                "word_count": len(formatted_letter.split()),
                "type": "cover_letter",
                "job_title": job_data.get('title'),
                "company": job_data.get('company'),
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return {
                "success": False,
                "error": str(e),
                "type": "cover_letter"
            }
    
    async def answer_essay_question(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        question: str,
        field_context: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """Generate an answer to an essay question"""
        try:
            logger.info(f"Generating essay answer for question: {question[:50]}...")
            
            # Classify the question type for better prompting
            question_type = self._classify_essay_question(question)
            
            prompt = self._build_essay_prompt(
                user_profile, job_data, question, question_type, field_context
            )
            
            answer = await self.llm_service.generate_response(prompt)
            
            # Clean and format the response
            formatted_answer = self._format_essay_answer(answer, question_type)
            
            return {
                "success": True,
                "content": formatted_answer,
                "word_count": len(formatted_answer.split()),
                "question": question,
                "question_type": question_type,
                "type": "essay_answer",
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating essay answer: {e}")
            return {
                "success": False,
                "error": str(e),
                "question": question,
                "type": "essay_answer"
            }
    
    async def generate_short_response(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        field_label: str,
        max_words: int = 50
    ) -> Dict[str, Any]:
        """Generate short responses for specific fields"""
        try:
            logger.info(f"Generating short response for field: {field_label}")
            
            prompt = self._build_short_response_prompt(
                user_profile, job_data, field_label, max_words
            )
            
            response = await self.llm_service.generate_response(prompt)
            
            # Ensure response fits constraints
            formatted_response = self._format_short_response(response, max_words)
            
            return {
                "success": True,
                "content": formatted_response,
                "word_count": len(formatted_response.split()),
                "field_label": field_label,
                "type": "short_response",
                "generated_at": datetime.now().isoformat()
            }
            
        except Exception as e:
            logger.error(f"Error generating short response: {e}")
            return {
                "success": False,
                "error": str(e),
                "field_label": field_label,
                "type": "short_response"
            }
    
    def _build_cover_letter_prompt(
        self, 
        user_profile: Dict[str, Any], 
        job_data: Dict[str, Any]
    ) -> str:
        """Build a prompt for cover letter generation"""
        
        # Extract key information
        name = f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip()
        job_title = job_data.get('title', 'this position')
        company = job_data.get('company', 'your company')
        job_description = job_data.get('description', '')
        
        # Build experience summary
        experience_summary = self._build_experience_summary(user_profile)
        skills_summary = self._build_skills_summary(user_profile)
        
        prompt = f"""Write a professional cover letter for {name} applying for the {job_title} position at {company}.

USER PROFILE:
- Name: {name}
- Email: {user_profile.get('email', '')}
- Location: {user_profile.get('location', '')}
- Experience: {experience_summary}
- Key Skills: {skills_summary}
- LinkedIn: {user_profile.get('linkedin_url', '')}
- Portfolio: {user_profile.get('portfolio_url', '')}

JOB DETAILS:
- Position: {job_title}
- Company: {company}
- Description: {job_description[:500]}...

REQUIREMENTS:
1. Write in first person as {name}
2. Keep it professional but personable
3. Highlight relevant experience and skills
4. Show genuine interest in the company
5. Maximum {self.max_cover_letter_length} words
6. Include specific examples when possible
7. End with a call to action

Format as a complete cover letter ready to copy-paste into an application form. Do not include address headers or date - just the letter content."""

        return prompt
    
    def _build_essay_prompt(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        question: str,
        question_type: str,
        field_context: Optional[Dict[str, Any]] = None
    ) -> str:
        """Build a prompt for essay question answering"""
        
        name = f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip()
        job_title = job_data.get('title', 'this position')
        company = job_data.get('company', 'the company')
        
        # Get relevant context based on question type
        context = self._get_relevant_context(user_profile, question_type)
        
        prompt = f"""Answer this job application essay question for {name}:

QUESTION: {question}

CONTEXT:
- Applicant: {name}
- Position: {job_title}
- Company: {company}
- Question Type: {question_type}

APPLICANT BACKGROUND:
{context}

REQUIREMENTS:
1. Write in first person as {name}
2. Answer the question directly and completely
3. Use specific examples from the applicant's background
4. Keep it authentic and professional
5. Maximum {self.max_essay_length} words
6. Make it compelling and memorable
7. Show enthusiasm for the role and company

Provide a complete answer that directly addresses the question asked."""

        return prompt
    
    def _build_short_response_prompt(
        self,
        user_profile: Dict[str, Any],
        job_data: Dict[str, Any],
        field_label: str,
        max_words: int
    ) -> str:
        """Build a prompt for short field responses"""
        
        name = f"{user_profile.get('first_name', '')} {user_profile.get('last_name', '')}".strip()
        
        prompt = f"""Provide a short, professional response for this job application field:

FIELD: {field_label}
APPLICANT: {name}
POSITION: {job_data.get('title', 'the position')}
COMPANY: {job_data.get('company', 'the company')}

APPLICANT INFO:
- Experience: {self._build_experience_summary(user_profile)}
- Skills: {self._build_skills_summary(user_profile)}
- Education: {user_profile.get('education', 'Not specified')}

REQUIREMENTS:
1. Maximum {max_words} words
2. Direct and concise
3. Professional tone
4. Relevant to the field label
5. First person perspective

Provide only the response content, no additional formatting or explanation."""

        return prompt
    
    def _classify_essay_question(self, question: str) -> str:
        """Classify the type of essay question for better prompting"""
        question_lower = question.lower()
        
        classifications = {
            'motivation': [
                'why do you want', 'why are you interested', 'what motivates you',
                'why this position', 'why our company', 'what attracts you'
            ],
            'experience': [
                'tell us about your experience', 'describe your background',
                'what experience do you have', 'relevant experience'
            ],
            'strengths': [
                'what are your strengths', 'describe your skills',
                'what makes you qualified', 'why should we hire you'
            ],
            'challenges': [
                'describe a challenge', 'difficult situation', 'overcome obstacles',
                'problem you solved', 'conflict resolution'
            ],
            'goals': [
                'career goals', 'where do you see yourself', 'future plans',
                'professional development', 'aspirations'
            ],
            'teamwork': [
                'team experience', 'collaboration', 'working with others',
                'team project', 'leadership experience'
            ],
            'about_you': [
                'tell us about yourself', 'describe yourself',
                'who are you', 'personal statement'
            ]
        }
        
        for question_type, keywords in classifications.items():
            if any(keyword in question_lower for keyword in keywords):
                return question_type
        
        return 'general'
    
    def _get_relevant_context(self, user_profile: Dict[str, Any], question_type: str) -> str:
        """Get relevant context based on question type"""
        context_parts = []
        
        # Always include basic info
        context_parts.append(f"Experience: {self._build_experience_summary(user_profile)}")
        context_parts.append(f"Skills: {self._build_skills_summary(user_profile)}")
        
        # Add specific context based on question type
        if question_type in ['experience', 'strengths', 'about_you']:
            if user_profile.get('work_experience'):
                context_parts.append("Recent Work Experience:")
                for exp in user_profile.get('work_experience', [])[:2]:  # Last 2 jobs
                    context_parts.append(f"- {exp.get('title', '')} at {exp.get('company', '')} ({exp.get('duration', '')})")
        
        if question_type in ['goals', 'motivation']:
            if user_profile.get('career_objective'):
                context_parts.append(f"Career Objective: {user_profile.get('career_objective')}")
        
        if question_type == 'teamwork':
            context_parts.append("Communication and collaboration skills from professional experience")
        
        return "\n".join(context_parts)
    
    def _build_experience_summary(self, user_profile: Dict[str, Any]) -> str:
        """Build a concise experience summary"""
        work_exp = user_profile.get('work_experience', [])
        if not work_exp:
            return "Professional experience in software development and technology"
        
        # Take most recent 2-3 positions
        recent_exp = work_exp[:3]
        exp_summary = []
        
        for exp in recent_exp:
            title = exp.get('title', '')
            company = exp.get('company', '')
            if title and company:
                exp_summary.append(f"{title} at {company}")
        
        if exp_summary:
            return "; ".join(exp_summary)
        else:
            return "Relevant professional experience"
    
    def _build_skills_summary(self, user_profile: Dict[str, Any]) -> str:
        """Build a concise skills summary"""
        skills = user_profile.get('skills', [])
        if not skills:
            return "Technical and professional skills"
        
        # Take top skills (assume they're ordered by relevance)
        top_skills = [skill.get('name', '') for skill in skills[:8] if skill.get('name')]
        
        if top_skills:
            return ", ".join(top_skills)
        else:
            return "Technical and professional skills"
    
    def _format_cover_letter(self, content: str) -> str:
        """Format and clean the cover letter content"""
        # Remove any unwanted formatting
        content = content.strip()
        
        # Remove common unwanted elements
        unwanted_patterns = [
            r'^Dear Hiring Manager,?\s*',
            r'^To Whom It May Concern,?\s*',
            r'Sincerely,?\s*$',
            r'Best regards,?\s*$',
            r'Thank you,?\s*$'
        ]
        
        for pattern in unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE | re.MULTILINE)
        
        # Ensure proper paragraph structure
        paragraphs = [p.strip() for p in content.split('\n\n') if p.strip()]
        content = '\n\n'.join(paragraphs)
        
        # Limit word count
        words = content.split()
        if len(words) > self.max_cover_letter_length:
            content = ' '.join(words[:self.max_cover_letter_length])
            # Try to end at a sentence
            if not content.endswith('.'):
                last_period = content.rfind('.')
                if last_period > len(content) * 0.8:  # If period is in last 20%
                    content = content[:last_period + 1]
        
        return content.strip()
    
    def _format_essay_answer(self, content: str, question_type: str) -> str:
        """Format and clean essay answer content"""
        content = content.strip()
        
        # Remove any unwanted prefixes/suffixes
        unwanted_patterns = [
            r'^Answer:\s*',
            r'^Response:\s*',
            r'^Here is my answer:\s*',
            r'^My answer is:\s*'
        ]
        
        for pattern in unwanted_patterns:
            content = re.sub(pattern, '', content, flags=re.IGNORECASE)
        
        # Ensure proper structure
        if question_type in ['about_you', 'experience'] and not content.startswith('I'):
            # Make sure it starts appropriately for first-person responses
            pass
        
        # Limit word count
        words = content.split()
        if len(words) > self.max_essay_length:
            content = ' '.join(words[:self.max_essay_length])
            # Try to end at a sentence
            if not content.endswith('.'):
                last_period = content.rfind('.')
                if last_period > len(content) * 0.8:
                    content = content[:last_period + 1]
        
        return content.strip()
    
    def _format_short_response(self, content: str, max_words: int) -> str:
        """Format and clean short response content"""
        content = content.strip()
        
        # Remove quotes if the whole response is quoted
        if content.startswith('"') and content.endswith('"'):
            content = content[1:-1].strip()
        
        # Limit word count strictly
        words = content.split()
        if len(words) > max_words:
            content = ' '.join(words[:max_words])
        
        return content.strip()