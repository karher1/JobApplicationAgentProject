import os
import logging
from typing import List, Dict, Any, Optional
from openai import OpenAI
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser
from src.models.schemas import FormField, ServiceHealth

logger = logging.getLogger(__name__)

class LLMService:
    """Service for handling LLM operations with OpenAI GPT-4o-mini"""
    
    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.model_name = "gpt-4o-mini"
        self.temperature = 0.1
        
        self.openai_client = None
        self.langchain_llm = None
        
    async def initialize(self):
        """Initialize OpenAI and LangChain clients"""
        try:
            if not self.openai_api_key:
                raise ValueError("OpenAI API key must be set")
            
            # Initialize OpenAI client
            self.openai_client = OpenAI(api_key=self.openai_api_key)
            
            # Initialize LangChain LLM
            self.langchain_llm = ChatOpenAI(
                model=self.model_name,
                temperature=self.temperature,
                api_key=self.openai_api_key
            )
            
            logger.info("LLM service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing LLM service: {e}")
            raise
    
    async def health_check(self) -> ServiceHealth:
        """Check LLM service health"""
        try:
            if not self.openai_client:
                return ServiceHealth(status="unhealthy", message="Client not initialized")
            
            # Test with a simple completion
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=10
            )
            
            return ServiceHealth(status="healthy", message="LLM service responding")
        except Exception as e:
            return ServiceHealth(status="unhealthy", message=str(e))
    
    async def chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.1, 
                            max_tokens: int = 1000) -> str:
        """Generate chat completion using OpenAI GPT-4o-mini"""
        try:
            if not self.openai_client:
                raise ValueError("OpenAI client not initialized")
            
            response = self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens
            )
            
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"Error in chat completion: {e}")
            raise
    
    async def generate_form_data(self, form_fields: List[FormField]) -> Dict[str, Any]:
        """Generate appropriate form data based on detected fields"""
        try:
            if not self.langchain_llm:
                raise ValueError("LangChain LLM not initialized")
            
            # Create prompt for form data generation
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at analyzing job application forms and generating appropriate data.
                Given a list of form fields, generate realistic but fictional data for testing purposes.
                
                Rules:
                1. Generate realistic but fictional data
                2. For text fields, provide detailed, professional responses
                3. For required fields, always provide data
                4. For optional fields, provide data if it makes sense
                5. Use professional but not overly formal language
                6. Make responses specific to the field context
                7. For cover letters and essays, provide thoughtful, detailed responses"""),
                ("human", """Analyze these form fields and generate appropriate data:
                
                {form_fields}
                
                Generate the data in JSON format with the following structure:
                {{
                    "first_name": "string",
                    "last_name": "string", 
                    "email": "string",
                    "phone": "string",
                    "linkedin_url": "string",
                    "portfolio_url": "string",
                    "cover_letter": "string",
                    "additional_info": {{}}
                }}
                
                For any additional fields found, include them in additional_info with appropriate values.
                For cover letters and essay questions, provide detailed, thoughtful responses that demonstrate
                relevant experience and enthusiasm for the role.""")
            ])
            
            # Create chain
            chain = prompt | self.langchain_llm | JsonOutputParser()
            
            # Generate data
            result = await chain.ainvoke({"form_fields": [field.dict() for field in form_fields]})
            
            return result
            
        except Exception as e:
            logger.error(f"Error generating form data: {e}")
            # Return fallback data
            return self._create_fallback_data()
    
    async def analyze_job_description(self, job_description: str) -> Dict[str, Any]:
        """Analyze job description to extract key information"""
        try:
            if not self.langchain_llm:
                raise ValueError("LangChain LLM not initialized")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at analyzing job descriptions and extracting key information.
                Extract relevant details about the role, requirements, and company."""),
                ("human", """Analyze this job description and extract key information:
                
                {job_description}
                
                Return the analysis in JSON format:
                {{
                    "role_type": "string (e.g., QA Engineer, SDET, etc.)",
                    "required_skills": ["list", "of", "required", "skills"],
                    "preferred_skills": ["list", "of", "preferred", "skills"],
                    "experience_level": "string (e.g., Entry, Mid, Senior)",
                    "remote_option": "string (Remote, Hybrid, On-site)",
                    "key_responsibilities": ["list", "of", "responsibilities"],
                    "company_culture": "string (insights about company culture)",
                    "salary_indicator": "string (if mentioned)",
                    "application_focus": "string (what to emphasize in application)"
                }}""")
            ])
            
            chain = prompt | self.langchain_llm | JsonOutputParser()
            result = await chain.ainvoke({"job_description": job_description})
            
            return result
            
        except Exception as e:
            logger.error(f"Error analyzing job description: {e}")
            return {}
    
    async def generate_cover_letter(self, job_title: str, company: str, job_description: str) -> str:
        """Generate a personalized cover letter"""
        try:
            if not self.langchain_llm:
                raise ValueError("LangChain LLM not initialized")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at writing compelling cover letters for tech positions.
                Write professional, personalized cover letters that demonstrate relevant experience and enthusiasm."""),
                ("human", """Write a cover letter for this position:
                
                Job Title: {job_title}
                Company: {company}
                Job Description: {job_description}
                
                Write a professional cover letter that:
                1. Shows enthusiasm for the role and company
                2. Demonstrates relevant experience and skills
                3. Explains why you're a good fit
                4. Is specific to the job requirements
                5. Is 2-3 paragraphs long
                6. Uses professional but engaging language""")
            ])
            
            chain = prompt | self.langchain_llm
            result = await chain.ainvoke({
                "job_title": job_title,
                "company": company,
                "job_description": job_description
            })
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error generating cover letter: {e}")
            return self._create_fallback_cover_letter(job_title, company)
    
    async def answer_essay_question(self, question: str, job_context: str = "") -> str:
        """Generate a thoughtful answer to an essay question"""
        try:
            if not self.langchain_llm:
                raise ValueError("LangChain LLM not initialized")
            
            prompt = ChatPromptTemplate.from_messages([
                ("system", """You are an expert at answering job application essay questions.
                Provide thoughtful, detailed responses that demonstrate relevant experience and insights."""),
                ("human", """Answer this essay question for a job application:
                
                Question: {question}
                Job Context: {job_context}
                
                Provide a detailed, thoughtful response that:
                1. Directly addresses the question
                2. Demonstrates relevant experience and skills
                3. Shows critical thinking and insights
                4. Is specific and provides examples
                5. Is 2-4 paragraphs long
                6. Uses professional but engaging language""")
            ])
            
            chain = prompt | self.langchain_llm
            result = await chain.ainvoke({
                "question": question,
                "job_context": job_context
            })
            
            return result.content
            
        except Exception as e:
            logger.error(f"Error answering essay question: {e}")
            return self._create_fallback_essay_answer(question)
    
    def _create_fallback_data(self) -> Dict[str, Any]:
        """Create fallback form data"""
        return {
            "first_name": "John",
            "last_name": "Doe",
            "email": "john.doe@example.com",
            "phone": "+1-555-123-4567",
            "linkedin_url": "https://linkedin.com/in/johndoe",
            "portfolio_url": "https://johndoe.dev",
            "cover_letter": "I am excited to apply for this position and believe my experience in software testing and automation would be a great fit for your team.",
            "additional_info": {}
        }
    
    def _create_fallback_cover_letter(self, job_title: str, company: str) -> str:
        """Create fallback cover letter"""
        return f"""Dear Hiring Manager,

I am writing to express my interest in the {job_title} position at {company}. With my background in software testing and automation, I am excited about the opportunity to contribute to your team.

My experience includes developing automated test frameworks, implementing CI/CD pipelines, and working with various testing tools and methodologies. I am passionate about ensuring software quality and would welcome the chance to discuss how my skills align with your needs.

Thank you for considering my application. I look forward to the opportunity to speak with you about this position.

Best regards,
John Doe"""
    
    def _create_fallback_essay_answer(self, question: str) -> str:
        """Create fallback essay answer"""
        return f"""I would be happy to provide a thoughtful response to this question. Based on my experience in software testing and quality assurance, I believe I can offer valuable insights and demonstrate relevant skills that would benefit your team.

My approach to this topic involves considering both technical and strategic aspects, ensuring that any solution is both practical and aligned with business objectives. I would welcome the opportunity to discuss this further during an interview.

Thank you for considering my application.""" 