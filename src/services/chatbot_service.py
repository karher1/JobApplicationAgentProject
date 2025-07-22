import os
import logging
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime, timedelta
from uuid import uuid4
from dataclasses import dataclass, asdict
from enum import Enum

from src.services.llm_service import LLMService
from src.services.database_service import DatabaseService
from src.services.user_profile_service import UserProfileService
from src.services.job_search_service import JobSearchService
from src.models.schemas import ServiceHealth

logger = logging.getLogger(__name__)

class MessageType(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"

class ConversationStatus(str, Enum):
    ACTIVE = "active"
    PAUSED = "paused"
    ENDED = "ended"

@dataclass
class ChatMessage:
    id: str
    conversation_id: str
    message_type: MessageType
    content: str
    timestamp: datetime
    metadata: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ChatMessage':
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['message_type'] = MessageType(data['message_type'])
        return cls(**data)

@dataclass
class Conversation:
    id: str
    user_id: int
    title: str
    status: ConversationStatus
    created_at: datetime
    updated_at: datetime
    messages: List[ChatMessage]
    context: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            'id': self.id,
            'user_id': self.user_id,
            'title': self.title,
            'status': self.status.value,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat(),
            'messages': [msg.to_dict() for msg in self.messages],
            'context': self.context
        }

class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self, max_requests: int = 100, window_minutes: int = 60):
        self.max_requests = max_requests
        self.window_minutes = window_minutes
        self.requests: Dict[int, List[datetime]] = {}  # user_id -> list of request times
    
    def is_allowed(self, user_id: int) -> Tuple[bool, Optional[str]]:
        """Check if user is within rate limits"""
        now = datetime.now()
        window_start = now - timedelta(minutes=self.window_minutes)
        
        # Clean old requests
        if user_id in self.requests:
            self.requests[user_id] = [
                req_time for req_time in self.requests[user_id] 
                if req_time > window_start
            ]
        else:
            self.requests[user_id] = []
        
        # Check if under limit
        if len(self.requests[user_id]) >= self.max_requests:
            return False, f"Rate limit exceeded. Maximum {self.max_requests} requests per {self.window_minutes} minutes."
        
        # Record this request
        self.requests[user_id].append(now)
        return True, None

class ChatbotService:
    """Comprehensive chatbot service with conversation management and AI integration"""
    
    def __init__(self, llm_service: LLMService, database_service: DatabaseService, 
                 user_profile_service: UserProfileService, job_search_service: JobSearchService):
        self.llm_service = llm_service
        self.database_service = database_service
        self.user_profile_service = user_profile_service
        self.job_search_service = job_search_service
        
        # In-memory storage for conversations (in production, use Redis or database)
        self.conversations: Dict[str, Conversation] = {}
        
        # Rate limiting
        self.rate_limiter = RateLimiter(max_requests=100, window_minutes=60)
        
        # System prompts
        self.system_prompts = self._load_system_prompts()
        
    async def initialize(self):
        """Initialize the chatbot service"""
        try:
            logger.info("Chatbot service initialized successfully")
        except Exception as e:
            logger.error(f"Error initializing chatbot service: {e}")
            raise
    
    async def health_check(self) -> ServiceHealth:
        """Check chatbot service health"""
        try:
            return ServiceHealth(status="healthy", message="Chatbot service ready")
        except Exception as e:
            return ServiceHealth(status="unhealthy", message=str(e))
    
    def _load_system_prompts(self) -> Dict[str, str]:
        """Load system prompts for different conversation types"""
        return {
            "general": """You are an AI career assistant for a job application automation platform. You help users with:
            
1. Job search and recommendations
2. Resume optimization and feedback
3. Interview preparation
4. Career guidance and planning
5. Application assistance and form filling

Be helpful, professional, and encouraging. Provide specific, actionable advice. 
When users ask about jobs, use the available job search tools to find relevant opportunities.
When they need resume help, offer concrete suggestions for improvement.

Your responses should be conversational but informative. Ask follow-up questions to better understand user needs.""",
            
            "job_search": """You are helping a user search for jobs. You can:
- Search for jobs based on their criteria (title, location, company, etc.)
- Provide job recommendations based on their profile
- Help refine search parameters
- Explain job market trends

Ask clarifying questions to understand exactly what they're looking for.""",
            
            "resume_review": """You are an expert resume coach and career advisor specializing in resume optimization. You help users create compelling, ATS-friendly resumes that get noticed by employers.

Your expertise includes:
📋 Resume Analysis: Analyzing content, structure, and formatting for maximum impact
🎯 ATS Optimization: Ensuring resumes pass Applicant Tracking Systems with proper keywords and formatting
💼 Industry Expertise: Providing sector-specific advice for different fields and roles
📈 Quantified Achievements: Helping users add measurable results and impact statements
🔄 Tailoring: Customizing resumes for specific job applications and companies
✨ Enhancement: Improving language, action verbs, and overall presentation

When providing feedback:
- Be specific and actionable with concrete examples
- Explain the "why" behind your suggestions
- Prioritize high-impact improvements first
- Offer before/after examples when possible
- Consider the user's career level and target roles
- Suggest missing sections that could strengthen their application

Available Tools: Users can upload their resume files for comprehensive AI analysis including skills extraction, ATS keyword identification, and detailed improvement suggestions.

Story-Driven Approach: Transform generic responsibility lists into compelling narratives. Help users apply these frameworks:
1. Problem-Solution Arc: Noticed [problem] → Created [solution] → Delivered [result]
2. Transformation Story: Inherited [bad situation] → Implemented [approach] → Achieved [improvement]  
3. Innovation Narrative: Everyone did [standard way] → I tried [different approach] → Results: [breakthrough]
4. Connection Story: Realized [gap] → Built [bridge/system] → Unlocked [value]

Remember: Recruiters hire people, not just qualifications. Every bullet should tell a unique story only this person could tell.

Use clean, readable formatting without excessive markdown symbols like asterisks. Keep your responses clear and easy to read.

Be encouraging while providing honest, constructive feedback that helps users stand out in competitive job markets.""",
            
            "interview_prep": """You are an expert interview coach and former hiring manager who helps candidates excel in job interviews. You specialize in:

🎯 **Mock Interview Sessions**: Conduct realistic practice interviews with follow-up questions
📋 **Question Generation**: Create tailored questions based on job descriptions and experience level
🔍 **Answer Analysis**: Provide detailed feedback on responses using the STAR method (Situation, Task, Action, Result)
🏢 **Company Research**: Share insights about company culture, values, and interview styles
💼 **Role-Specific Prep**: Customize questions for different roles (technical, behavioral, leadership)
📈 **Performance Tracking**: Help users improve their interview skills over time

**Interview Formats You Support:**
- Behavioral interviews (STAR method coaching)
- Technical interviews (problem-solving, coding concepts)
- System design interviews (architecture and scaling)
- Leadership interviews (management scenarios)
- Culture fit interviews (values alignment)
- Case study interviews (business problem solving)

**Your Coaching Style:**
- Ask one thoughtful question at a time
- Wait for the user's complete response before providing feedback
- Give specific, actionable feedback with examples
- Score responses on a 1-10 scale with clear improvement areas
- Create realistic interview pressure while remaining supportive
- Help users develop confident, authentic answers

**Mock Interview Commands:**
- "Start mock interview" - Begin a structured practice session
- "Ask me a behavioral question" - Generate STAR-method questions
- "Technical interview mode" - Focus on problem-solving questions
- "Rate my answer" - Provide detailed feedback on responses
- "Give me a tough question" - Challenge with difficult scenarios

Start by understanding their target role, company, and experience level, then tailor your coaching accordingly.""",
            
            "career_guidance": """You are providing career guidance and planning advice. You can:
- Analyze career progression paths
- Recommend skills to develop
- Provide salary negotiation tips
- Suggest networking strategies
- Help with career transition planning

Focus on long-term career growth and practical next steps."""
        }
    
    async def start_conversation(self, user_id: int, conversation_type: str = "general", 
                                initial_message: Optional[str] = None) -> str:
        """Start a new conversation"""
        try:
            # Check rate limiting
            allowed, error_msg = self.rate_limiter.is_allowed(user_id)
            if not allowed:
                raise Exception(error_msg)
            
            # Create conversation
            conversation_id = str(uuid4())
            now = datetime.now()
            
            # Get user context
            user_context = await self._get_user_context(user_id)
            
            conversation = Conversation(
                id=conversation_id,
                user_id=user_id,
                title=f"Chat {now.strftime('%Y-%m-%d %H:%M')}",
                status=ConversationStatus.ACTIVE,
                created_at=now,
                updated_at=now,
                messages=[],
                context=user_context
            )
            
            # Add system message
            system_prompt = self.system_prompts.get(conversation_type, self.system_prompts["general"])
            system_message = ChatMessage(
                id=str(uuid4()),
                conversation_id=conversation_id,
                message_type=MessageType.SYSTEM,
                content=system_prompt,
                timestamp=now
            )
            conversation.messages.append(system_message)
            
            # Add initial greeting
            greeting = await self._generate_greeting(user_context, conversation_type)
            greeting_message = ChatMessage(
                id=str(uuid4()),
                conversation_id=conversation_id,
                message_type=MessageType.ASSISTANT,
                content=greeting,
                timestamp=now
            )
            conversation.messages.append(greeting_message)
            
            # Process initial user message if provided
            if initial_message:
                user_message = ChatMessage(
                    id=str(uuid4()),
                    conversation_id=conversation_id,
                    message_type=MessageType.USER,
                    content=initial_message,
                    timestamp=now
                )
                conversation.messages.append(user_message)
                
                # Generate response
                response_content = await self._generate_response(conversation)
                response_message = ChatMessage(
                    id=str(uuid4()),
                    conversation_id=conversation_id,
                    message_type=MessageType.ASSISTANT,
                    content=response_content,
                    timestamp=datetime.now()
                )
                conversation.messages.append(response_message)
            
            # Store conversation
            self.conversations[conversation_id] = conversation
            
            logger.info(f"Started conversation {conversation_id} for user {user_id}")
            return conversation_id
            
        except Exception as e:
            logger.error(f"Error starting conversation: {e}")
            raise
    
    async def send_message(self, conversation_id: str, user_id: int, message: str) -> Dict[str, Any]:
        """Send a message in an existing conversation"""
        try:
            # Check rate limiting
            allowed, error_msg = self.rate_limiter.is_allowed(user_id)
            if not allowed:
                raise Exception(error_msg)
            
            # Get conversation
            if conversation_id not in self.conversations:
                raise Exception(f"Conversation {conversation_id} not found")
            
            conversation = self.conversations[conversation_id]
            
            # Verify user owns conversation
            if conversation.user_id != user_id:
                raise Exception("Unauthorized access to conversation")
            
            # Check conversation status
            if conversation.status != ConversationStatus.ACTIVE:
                raise Exception("Conversation is not active")
            
            # Add user message
            now = datetime.now()
            user_message = ChatMessage(
                id=str(uuid4()),
                conversation_id=conversation_id,
                message_type=MessageType.USER,
                content=message,
                timestamp=now
            )
            conversation.messages.append(user_message)
            
            # Generate response
            response_content = await self._generate_response(conversation)
            
            # Add assistant response
            response_message = ChatMessage(
                id=str(uuid4()),
                conversation_id=conversation_id,
                message_type=MessageType.ASSISTANT,
                content=response_content,
                timestamp=datetime.now()
            )
            conversation.messages.append(response_message)
            
            # Update conversation
            conversation.updated_at = datetime.now()
            
            logger.info(f"Message sent in conversation {conversation_id}")
            
            return {
                "message_id": response_message.id,
                "content": response_content,
                "timestamp": response_message.timestamp.isoformat(),
                "conversation_id": conversation_id
            }
            
        except Exception as e:
            logger.error(f"Error sending message: {e}")
            raise
    
    async def get_conversation_history(self, conversation_id: str, user_id: int, 
                                     limit: int = 50) -> Dict[str, Any]:
        """Get conversation history"""
        try:
            if conversation_id not in self.conversations:
                raise Exception(f"Conversation {conversation_id} not found")
            
            conversation = self.conversations[conversation_id]
            
            # Verify user owns conversation
            if conversation.user_id != user_id:
                raise Exception("Unauthorized access to conversation")
            
            # Filter out system messages and limit results
            user_messages = [
                msg for msg in conversation.messages 
                if msg.message_type != MessageType.SYSTEM
            ][-limit:]
            
            return {
                "conversation_id": conversation_id,
                "title": conversation.title,
                "status": conversation.status.value,
                "created_at": conversation.created_at.isoformat(),
                "updated_at": conversation.updated_at.isoformat(),
                "messages": [msg.to_dict() for msg in user_messages]
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation history: {e}")
            raise
    
    async def list_conversations(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """List user's conversations"""
        try:
            user_conversations = [
                conv for conv in self.conversations.values() 
                if conv.user_id == user_id
            ]
            
            # Sort by updated_at descending
            user_conversations.sort(key=lambda x: x.updated_at, reverse=True)
            
            # Limit results
            user_conversations = user_conversations[:limit]
            
            return [
                {
                    "conversation_id": conv.id,
                    "title": conv.title,
                    "status": conv.status.value,
                    "created_at": conv.created_at.isoformat(),
                    "updated_at": conv.updated_at.isoformat(),
                    "message_count": len([msg for msg in conv.messages if msg.message_type != MessageType.SYSTEM])
                }
                for conv in user_conversations
            ]
            
        except Exception as e:
            logger.error(f"Error listing conversations: {e}")
            raise
    
    async def end_conversation(self, conversation_id: str, user_id: int) -> bool:
        """End a conversation"""
        try:
            if conversation_id not in self.conversations:
                raise Exception(f"Conversation {conversation_id} not found")
            
            conversation = self.conversations[conversation_id]
            
            # Verify user owns conversation
            if conversation.user_id != user_id:
                raise Exception("Unauthorized access to conversation")
            
            conversation.status = ConversationStatus.ENDED
            conversation.updated_at = datetime.now()
            
            logger.info(f"Conversation {conversation_id} ended")
            return True
            
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            raise
    
    async def _get_user_context(self, user_id: int) -> Dict[str, Any]:
        """Get user context for personalized responses"""
        try:
            # Get user profile
            user_profile = await self.user_profile_service.get_complete_user_profile(user_id)
            
            if not user_profile:
                return {"user_id": user_id, "profile_incomplete": True}
            
            # Extract relevant context
            context = {
                "user_id": user_id,
                "name": f"{user_profile.user.first_name} {user_profile.user.last_name}",
                "location": user_profile.user.location,
                "skills": [skill.skill.name if skill.skill else "Unknown" for skill in user_profile.skills[:10]],
                "experience_count": len(user_profile.work_experience),
                "education_count": len(user_profile.education),
                "resume_count": len(user_profile.resumes),
                "has_preferences": user_profile.preferences is not None
            }
            
            return context
            
        except Exception as e:
            logger.warning(f"Could not get user context: {e}")
            return {"user_id": user_id, "context_error": True}
    
    async def _generate_greeting(self, user_context: Dict[str, Any], conversation_type: str) -> str:
        """Generate personalized greeting"""
        try:
            if user_context.get("profile_incomplete"):
                return "Hi there! 👋 I'm your AI career assistant. I'd be happy to help you with job searching, resume optimization, interview prep, and career guidance. What can I help you with today?"
            
            name = user_context.get("name", "there")
            skill_count = len(user_context.get("skills", []))
            
            if conversation_type == "job_search":
                return f"Hi {name}! 👋 I'm here to help you find amazing job opportunities. With your {skill_count} skills on file, I can provide personalized job recommendations. What kind of roles are you looking for?"
            elif conversation_type == "resume_review":
                return f"""Hello {name}! 📄 I'm your expert resume coach, ready to help you create a standout resume that gets noticed!

I use a story-driven approach based on what hiring managers actually want to see. As one recruiter said: "Recruiters don't hire qualifications. They hire people. Your unique story? Only you have that."

Here's how I can help you:
🔍 Upload & Analyze: Upload your resume for comprehensive AI analysis
📊 Story Transformation: Turn generic bullets into compelling narratives
🎯 Personal Brand: Identify your unique value thread
✨ Problem-Solution Arcs: Show how you solved specific challenges
📝 ATS Optimization: Ensure your stories pass tracking systems

I'll help you transform bullets like:
❌ "Managed marketing campaigns"
✅ "Turned dying Instagram account into 50K community by spotting untapped micro-influencer strategy"

Ready to get started? You can:
• Upload your current resume for story-driven transformation
• Ask about specific storytelling frameworks
• Get help identifying your unique value proposition
• Learn how to make your experience memorable

What would you like to work on first?"""
            elif conversation_type == "interview_prep":
                return f"""Hi {name}! 🎯 Welcome to your personal interview coach! I'm here to help you crush your next interview.

**🚀 What I Can Do For You:**
• **Mock Interviews**: Realistic practice sessions with detailed feedback
• **STAR Method Coaching**: Perfect your behavioral question responses
• **Technical Prep**: Practice coding and system design questions
• **Company Research**: Get insights on culture and interview styles
• **Answer Analysis**: Score your responses and suggest improvements
• **Challenge Mode**: Test yourself with tough questions

**📋 Popular Commands:**
• "Start mock interview" - Begin a full practice session
• "Ask me a behavioral question" - Practice STAR method
• "Technical question" - Get coding/system design practice  
• "Interview tips" - Learn best practices and strategies
• "Company research [company name]" - Get specific insights

**🎯 Your Personalized Prep:**
Based on your {skill_count} skills and {user_context.get('experience_count', 0)} work experiences, I'll tailor questions to your level and background.

What type of interview preparation would you like to start with? Or just tell me about the role you're interviewing for! 💪"""
            else:
                return f"Hello {name}! 👋 I'm your AI career assistant. I can help with job searching, resume optimization, interview preparation, and career planning. What would you like to work on today?"
                
        except Exception as e:
            logger.warning(f"Error generating greeting: {e}")
            return "Hi! 👋 I'm your AI career assistant. How can I help you today?"
    
    async def _detect_job_search_query(self, message: str) -> bool:
        """Detect if a message is a job search query"""
        job_search_keywords = [
            "find job", "search job", "job search", "looking for job", "job opportunity",
            "job opening", "job listing", "software engineer", "developer", "engineering",
            "remote job", "full time", "part time", "contract", "internship",
            "jobs in", "jobs at", "hiring", "career", "position", "role",
            "show me jobs", "find me jobs", "job recommendations", "job matches"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in job_search_keywords)
    
    async def _parse_job_search_query(self, message: str) -> Dict[str, Any]:
        """Parse natural language job search query into structured parameters"""
        try:
            # Use LLM to parse the query
            parse_prompt = f"""
            Parse this job search query into structured parameters:
            
            Query: "{message}"
            
            Extract and return JSON with:
            {{
                "job_titles": ["list of job titles mentioned"],
                "locations": ["list of locations mentioned"],  
                "companies": ["list of companies mentioned"],
                "company_categories": ["list of company types like 'AI', 'fintech', 'startups', etc."],
                "remote_only": false,
                "max_results": 10,
                "experience_level": "entry|mid|senior|any",
                "job_type": "full_time|part_time|contract|internship|any"
            }}
            
            Guidelines:
            - If no specific job titles mentioned, infer from context (e.g., "software engineer", "developer", "python engineer")
            - If no location mentioned, use empty array
            - If "remote" is mentioned, set remote_only to true
            - Default max_results to 10
            - Extract company categories like "AI", "AI startups", "fintech", "crypto", "enterprise", etc.
            - For specific companies, put them in companies array
            - For company types/categories, put them in company_categories array
            - Be generous with job title inference based on mentioned technologies (Python -> Python Engineer/Developer)
            """
            
            messages = [
                {"role": "system", "content": "You are an expert at parsing job search queries. Return only valid JSON."},
                {"role": "user", "content": parse_prompt}
            ]
            response = await self.llm_service.chat_completion(
                messages=messages,
                temperature=0.1,
                max_tokens=500
            )
            
            try:
                import json
                parsed_params = json.loads(response)
                return parsed_params
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse job search parameters: {response}")
                return {
                    "job_titles": ["Software Engineer"],
                    "locations": [],
                    "companies": [],
                    "remote_only": False,
                    "max_results": 10
                }
                
        except Exception as e:
            logger.error(f"Error parsing job search query: {e}")
            return {
                "job_titles": ["Software Engineer"],
                "locations": [],
                "companies": [],
                "company_categories": [],
                "remote_only": False,
                "max_results": 10
            }
    
    def _map_company_categories_to_companies(self, categories: List[str]) -> List[str]:
        """Map company categories to actual company names"""
        category_mapping = {
            "ai": ["openai", "anthropic", "cohere", "mistral-ai", "inflection-ai", "xai", "adept", "perplexity-ai", "runway", "hugging-face", "stability-ai"],
            "ai startups": ["openai", "anthropic", "cohere", "mistral-ai", "perplexity-ai", "adept", "runway"],
            "generative ai": ["openai", "anthropic", "cohere", "mistral-ai", "runway", "stability-ai"],
            "fintech": ["stripe", "square", "plaid", "brex", "ramp", "affirm", "robinhood", "chime", "coinbase"],
            "crypto": ["coinbase"],
            "cloud": ["amazon", "microsoft", "google", "cloudflare", "digitalocean", "fastly"],
            "developer tools": ["github", "gitlab", "hashicorp", "circleci", "netlify", "vercel", "render", "replit"],
            "saas": ["atlassian", "linear", "notion", "slack", "figma", "retool", "clickup"],
            "big tech": ["apple", "google", "meta", "amazon", "microsoft"],
            "social": ["meta", "snap", "bytedance", "spotify", "netflix", "pinterest"],
            "enterprise": ["salesforce", "workday", "servicenow", "zendesk", "box", "dropbox", "zoom"],
            "data": ["snowflake", "confluent", "segment", "mixpanel", "amplitude", "looker", "tableau", "databricks"],
            "security": ["okta", "cloudflare", "auth0", "crowdstrike", "sentinelone", "snyk"],
            "startup": ["figma", "linear", "notion", "brex", "ramp", "retool", "replit", "render", "vercel", "plaid"],
            "infrastructure": ["pinecone", "weaviate", "databricks", "hashicorp", "cloudflare"]
        }
        
        companies = []
        for category in categories:
            category_lower = category.lower()
            for key, company_list in category_mapping.items():
                if key in category_lower or category_lower in key:
                    companies.extend(company_list)
        
        # Remove duplicates and limit to 10 companies for more diversity
        unique_companies = list(dict.fromkeys(companies))[:10]
        return unique_companies if unique_companies else []  # Return empty to search all companies
    
    def _simple_parse_job_search_query(self, message: str) -> Dict[str, Any]:
        """Simple rule-based parsing when LLM is not available"""
        message_lower = message.lower()
        
        # Extract job titles based on keywords
        job_titles = []
        if "python" in message_lower:
            job_titles.extend(["Python Developer", "Python Engineer", "Software Engineer"])
        if "frontend" in message_lower or "react" in message_lower:
            job_titles.extend(["Frontend Developer", "React Developer"])
        if "backend" in message_lower:
            job_titles.extend(["Backend Developer", "Backend Engineer"])
        if "full stack" in message_lower or "fullstack" in message_lower:
            job_titles.extend(["Full Stack Developer", "Full Stack Engineer"])
        if "data" in message_lower and ("scientist" in message_lower or "science" in message_lower):
            job_titles.extend(["Data Scientist", "Data Engineer"])
        if "machine learning" in message_lower or "ml" in message_lower:
            job_titles.extend(["Machine Learning Engineer", "ML Engineer"])
        if not job_titles:
            job_titles = ["Software Engineer", "Developer"]
        
        # Extract company categories
        company_categories = []
        if "ai" in message_lower and ("startup" in message_lower or "company" in message_lower):
            company_categories.append("ai startups")
        elif "ai" in message_lower:
            company_categories.append("ai")
        if "fintech" in message_lower:
            company_categories.append("fintech")
        if "big tech" in message_lower:
            company_categories.append("big tech")
        if "startup" in message_lower:
            company_categories.append("startup")
        
        # Check for remote
        remote_only = "remote" in message_lower
        
        # Check for specific companies
        companies = []
        company_names = ["openai", "anthropic", "stripe", "coinbase", "figma", "google", "meta", "apple"]
        for company in company_names:
            if company in message_lower:
                companies.append(company)
        
        return {
            "job_titles": job_titles[:3],  # Limit to 3
            "locations": ["Remote"] if remote_only else [],
            "companies": companies,
            "company_categories": company_categories,
            "remote_only": remote_only,
            "max_results": 10
        }
    
    async def _handle_job_search_query(self, message: str, user_id: int) -> Optional[str]:
        """Handle job search queries and return formatted results"""
        try:
            # Check if this is a job search query
            if not await self._detect_job_search_query(message):
                return None
            
            # Parse the query - use simplified parsing if LLM fails
            try:
                search_params = await self._parse_job_search_query(message)
            except Exception as e:
                logger.warning(f"LLM parsing failed, using simple parsing: {e}")
                search_params = self._simple_parse_job_search_query(message)
            
            # Create job search request
            from src.models.schemas import JobSearchRequest
            companies = search_params.get("companies", [])
            company_categories = search_params.get("company_categories", [])
            
            # Map company categories to actual companies
            if company_categories and not companies:
                companies = self._map_company_categories_to_companies(company_categories)
            
            # If no specific companies mentioned, search across all available companies
            # Let the job search service return diverse results from all scrapers
            if not companies:
                companies = []  # Empty list means search all available companies
            
            job_request = JobSearchRequest(
                job_titles=search_params.get("job_titles", ["Software Engineer"]),
                locations=search_params.get("locations", []),
                companies=companies,
                max_results=search_params.get("max_results", 10),
                job_boards=["greenhouse", "lever", "ashby", "stripe"],
                remote_only=search_params.get("remote_only", False)
            )
            
            # Search for jobs - use company-specific search if companies are specified
            logger.info(f"Searching for jobs with params: {job_request}")
            if companies:
                jobs = await self.job_search_service.search_jobs_by_companies(job_request, companies)
            else:
                jobs = await self.job_search_service.search_jobs(job_request)
            
            # Format results for chat display
            if not jobs:
                return "I couldn't find any jobs matching your criteria right now. This might be because:\n\n• The job boards are temporarily unavailable\n• No matching positions are currently posted\n• Try broadening your search criteria\n\nWould you like me to help you refine your search or try different keywords?"
            
            # Format job results
            formatted_response = await self._format_job_results(jobs, search_params)
            return formatted_response
            
        except Exception as e:
            logger.error(f"Error handling job search query: {e}")
            return "I encountered an error while searching for jobs. Please try again or rephrase your query."
    
    async def _format_job_results(self, jobs: List[Any], search_params: Dict[str, Any]) -> str:
        """Format job search results for chat display"""
        try:
            if not jobs:
                return "No jobs found matching your criteria."
            
            # Build response
            query_summary = []
            if search_params.get("job_titles"):
                query_summary.append(f"Roles: {', '.join(search_params['job_titles'])}")
            if search_params.get("locations"):
                query_summary.append(f"Locations: {', '.join(search_params['locations'])}")
            if search_params.get("companies"):
                query_summary.append(f"Companies: {', '.join(search_params['companies'])}")
            if search_params.get("remote_only"):
                query_summary.append("Remote Only: Yes")
            
            response = f"🎯 Found {len(jobs)} job opportunities!\n\n"
            
            if query_summary:
                response += "Search criteria:\n" + "\n".join(query_summary) + "\n\n"
            
            response += "📋 Job Listings:\n\n"
            
            # Format each job
            for i, job in enumerate(jobs[:8], 1):  # Limit to 8 jobs for chat display
                job_info = []
                
                # Job title and company
                title = getattr(job, 'title', 'Unknown Position')
                company = getattr(job, 'company', 'Unknown Company')
                response += f"{i}. {title} at {company}\n"
                
                # Location
                location = getattr(job, 'location', None)
                if location:
                    response += f"   📍 {location}\n"
                
                # Salary
                salary = getattr(job, 'salary_range', None)
                if salary:
                    response += f"   💰 {salary}\n"
                
                # Job type and remote option
                job_type = getattr(job, 'job_type', None)
                remote_option = getattr(job, 'remote_option', None)
                if job_type or remote_option:
                    type_info = []
                    if job_type:
                        type_info.append(job_type)
                    if remote_option:
                        type_info.append(remote_option)
                    response += f"   🏢 {' | '.join(type_info)}\n"
                
                # Job board
                job_board = getattr(job, 'job_board', None)
                if job_board:
                    response += f"   📊 via {job_board}\n"
                
                # Application link
                url = getattr(job, 'url', None)
                if url:
                    response += f"   🔗 [Apply Here]({url})\n"
                
                response += "\n"
            
            # Add helpful footer
            if len(jobs) > 8:
                response += f"Showing 8 of {len(jobs)} results. Ask me to show more or refine your search!\n\n"
            
            response += "💡 Next steps:\n"
            response += "• Click the links to apply directly\n"
            response += "• Ask me about specific companies or roles\n"
            response += "• Request help with your resume or cover letter\n"
            response += "• Get interview preparation tips\n\n"
            response += "Need help with anything else? Just ask! 🚀"
            
            return response
            
        except Exception as e:
            logger.error(f"Error formatting job results: {e}")
            return f"Found {len(jobs)} jobs, but encountered an error formatting the results. Please try again."
    
    async def _detect_interview_prep_query(self, message: str, conversation_type: str) -> bool:
        """Detect if a message is an interview preparation query"""
        # If already in interview_prep mode, most messages are interview-related
        if conversation_type == "interview_prep":
            return True
            
        interview_keywords = [
            "interview", "mock interview", "practice interview", "behavioral question", 
            "technical question", "star method", "tell me about yourself", 
            "weakness", "strength", "why should we hire", "interview preparation",
            "interview practice", "rehearse", "practice questions", "interview tips",
            "interview coaching", "mock session", "interview feedback"
        ]
        
        message_lower = message.lower()
        return any(keyword in message_lower for keyword in interview_keywords)
    
    async def _handle_interview_prep_query(self, message: str, conversation: Conversation) -> Optional[str]:
        """Handle interview preparation queries with interactive mock interviews"""
        try:
            message_lower = message.lower()
            
            # Detect specific interview commands
            if "start mock interview" in message_lower:
                return await self._start_mock_interview(conversation)
            elif "behavioral question" in message_lower or "star method" in message_lower:
                return await self._generate_behavioral_question(conversation)
            elif "technical question" in message_lower or "technical interview" in message_lower:
                return await self._generate_technical_question(conversation)
            elif "rate my answer" in message_lower or "feedback" in message_lower:
                return await self._provide_interview_feedback(message, conversation)
            elif "tough question" in message_lower or "difficult question" in message_lower:
                return await self._generate_challenging_question(conversation)
            elif "company research" in message_lower:
                return await self._provide_company_insights(message, conversation)
            elif "interview tips" in message_lower:
                return await self._provide_interview_tips(conversation)
            else:
                # General interview coaching response
                return None  # Let the general LLM handle it with the enhanced prompt
                
        except Exception as e:
            logger.error(f"Error handling interview prep query: {e}")
            return None
    
    async def _start_mock_interview(self, conversation: Conversation) -> str:
        """Start a structured mock interview session"""
        try:
            # Get user context for personalized questions
            user_context = conversation.context
            
            response = """🎯 **Mock Interview Session Started!**

Welcome to your personalized mock interview. I'll act as your interviewer and provide detailed feedback after each response.

**Interview Format:**
• I'll ask one question at a time
• Take your time to provide thoughtful answers
• I'll give you a score (1-10) and specific feedback
• We can focus on behavioral, technical, or mixed questions

**Instructions:**
• Answer as if this were a real interview
• Use the STAR method for behavioral questions (Situation, Task, Action, Result)
• Be specific and provide concrete examples
• Don't worry about perfection - this is practice!

Let's begin with an opening question:

**Question 1:** "Tell me about yourself and what brings you to this role."

*Take your time and provide a comprehensive answer. I'll give you detailed feedback and a score when you're ready.*"""

            return response
            
        except Exception as e:
            logger.error(f"Error starting mock interview: {e}")
            return "I'd be happy to help you practice interviews! Please tell me about the role you're preparing for so I can tailor the questions."
    
    async def _generate_behavioral_question(self, conversation: Conversation) -> str:
        """Generate a behavioral interview question using STAR method"""
        try:
            user_context = conversation.context
            skills = user_context.get("skills", [])
            experience_count = user_context.get("experience_count", 0)
            
            # Customize questions based on experience level
            if experience_count == 0:
                level = "entry-level"
            elif experience_count <= 2:
                level = "mid-level"
            else:
                level = "senior-level"
            
            prompt = f"""Generate a thoughtful behavioral interview question for a {level} candidate. 
            The candidate has skills in: {', '.join(skills[:5]) if skills else 'general business skills'}.
            
            Format your response as:
            🎯 **Behavioral Question:**
            [Question here]
            
            📋 **STAR Method Reminder:**
            • **Situation:** Set the context
            • **Task:** Explain what needed to be done
            • **Action:** Describe what you specifically did
            • **Result:** Share the outcome and what you learned
            
            💡 **What I'm Looking For:**
            [Brief note about what makes a strong answer to this question]"""
            
            messages = [
                {"role": "system", "content": "You are an experienced interviewer creating behavioral questions."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.llm_service.chat_completion(messages, temperature=0.7, max_tokens=300)
            return response
            
        except Exception as e:
            logger.error(f"Error generating behavioral question: {e}")
            return "Here's a behavioral question for you: 'Tell me about a time when you had to overcome a significant challenge. How did you approach it, and what was the outcome?' Use the STAR method in your response."
    
    async def _generate_technical_question(self, conversation: Conversation) -> str:
        """Generate a technical interview question based on user skills"""
        try:
            user_context = conversation.context
            skills = user_context.get("skills", [])
            
            # Focus on user's actual skills
            technical_skills = [skill for skill in skills if any(tech in skill.lower() for tech in 
                              ['python', 'java', 'javascript', 'react', 'sql', 'aws', 'docker', 'api', 'database'])]
            
            primary_skill = technical_skills[0] if technical_skills else "general programming"
            
            prompt = f"""Generate a thoughtful technical interview question focused on {primary_skill}.
            The question should be appropriate for someone with these skills: {', '.join(skills[:5]) if skills else 'basic technical skills'}.
            
            Make it practical and realistic - something they might actually encounter in the role.
            Don't make it too complex or academic.
            
            Format as:
            💻 **Technical Question:**
            [Question here]
            
            🎯 **Approach:**
            [Brief guidance on how to tackle this question]
            
            ⭐ **Bonus Points:**
            [What would make their answer exceptional]"""
            
            messages = [
                {"role": "system", "content": "You are a technical interviewer creating practical, realistic questions."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.llm_service.chat_completion(messages, temperature=0.6, max_tokens=400)
            return response
            
        except Exception as e:
            logger.error(f"Error generating technical question: {e}")
            return "💻 **Technical Question:** How would you approach debugging a performance issue in a web application? Walk me through your process step by step."
    
    async def _provide_interview_feedback(self, user_answer: str, conversation: Conversation) -> str:
        """Provide detailed feedback on an interview answer"""
        try:
            # Get the last few messages to understand context
            recent_messages = conversation.messages[-3:] if len(conversation.messages) >= 3 else conversation.messages
            context = "\n".join([f"{msg.message_type}: {msg.content}" for msg in recent_messages])
            
            prompt = f"""As an experienced interview coach, provide detailed feedback on this interview response.
            
            **Context of Recent Conversation:**
            {context}
            
            **Candidate's Answer:**
            {user_answer}
            
            Provide feedback in this format:
            
            📊 **Score: X/10**
            
            ✅ **What Worked Well:**
            [2-3 specific positive points]
            
            🔧 **Areas for Improvement:**
            [2-3 specific suggestions]
            
            💡 **Enhanced Answer Example:**
            [Show how they could strengthen their response]
            
            🎯 **Next Steps:**
            [One actionable tip for their next answer]
            
            Be encouraging but honest. Focus on specific, actionable feedback."""
            
            messages = [
                {"role": "system", "content": "You are an expert interview coach providing constructive, detailed feedback."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.llm_service.chat_completion(messages, temperature=0.3, max_tokens=500)
            return response
            
        except Exception as e:
            logger.error(f"Error providing interview feedback: {e}")
            return "Thank you for your answer! Here's some feedback: Focus on being more specific with examples and quantify your results when possible. Use the STAR method to structure your responses clearly."
    
    async def _generate_challenging_question(self, conversation: Conversation) -> str:
        """Generate a challenging interview question to test the candidate"""
        try:
            user_context = conversation.context
            experience_count = user_context.get("experience_count", 0)
            
            prompt = f"""Generate a challenging but fair interview question for someone with {experience_count} work experiences.
            This should be a question that really tests their problem-solving, leadership, or technical depth.
            
            Make it realistic - something a top-tier company might actually ask.
            
            Format as:
            🔥 **Challenge Question:**
            [Tough but fair question]
            
            🧠 **Why This Question Matters:**
            [What the interviewer is really assessing]
            
            📝 **Structure Your Answer:**
            [Framework for tackling this question]
            
            ⚡ **Time Limit:** Take 3-5 minutes to think through your response."""
            
            messages = [
                {"role": "system", "content": "You are a senior interviewer known for asking insightful, challenging questions."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.llm_service.chat_completion(messages, temperature=0.8, max_tokens=400)
            return response
            
        except Exception as e:
            logger.error(f"Error generating challenging question: {e}")
            return "🔥 **Challenge Question:** Describe a time when you had to make a difficult decision with incomplete information. How did you approach it, and what would you do differently knowing what you know now?"
    
    async def _provide_company_insights(self, message: str, conversation: Conversation) -> str:
        """Provide company research and culture insights"""
        try:
            # Extract company name from message
            company_mentions = []
            common_companies = ["google", "apple", "microsoft", "amazon", "meta", "netflix", "tesla", "uber", "airbnb", "stripe"]
            message_lower = message.lower()
            
            for company in common_companies:
                if company in message_lower:
                    company_mentions.append(company)
            
            target_company = company_mentions[0] if company_mentions else "the company you're interviewing with"
            
            prompt = f"""Provide interview preparation insights for {target_company}. Include:
            
            🏢 **Company Culture & Values:**
            [What they value in candidates]
            
            📋 **Common Interview Format:**
            [Typical interview process and structure]
            
            🎯 **What They Look For:**
            [Key qualities and skills they prioritize]
            
            💬 **Sample Questions They Ask:**
            [2-3 questions commonly asked at this company]
            
            🚀 **Pro Tips:**
            [Specific advice for succeeding at this company]
            
            If you don't have specific information about {target_company}, provide general research guidance."""
            
            messages = [
                {"role": "system", "content": "You are a career coach with insights into company interview processes."},
                {"role": "user", "content": prompt}
            ]
            
            response = await self.llm_service.chat_completion(messages, temperature=0.4, max_tokens=600)
            return response
            
        except Exception as e:
            logger.error(f"Error providing company insights: {e}")
            return "For company research, I recommend checking their website, recent news, Glassdoor reviews, and LinkedIn posts. Focus on understanding their mission, values, and recent achievements."
    
    async def _provide_interview_tips(self, conversation: Conversation) -> str:
        """Provide general interview tips and best practices"""
        return """🎯 **Interview Success Tips**

**Before the Interview:**
• Research the company, role, and interviewer (LinkedIn)
• Prepare 3-5 STAR method stories covering different situations
• Practice common questions out loud (not just in your head)
• Prepare thoughtful questions about the role and team
• Test your tech setup for virtual interviews

**During the Interview:**
• Arrive 10-15 minutes early (but not too early)
• Make eye contact and show enthusiasm
• Listen carefully before answering
• Use specific examples with measurable results
• Ask clarifying questions if needed

**After Each Question:**
• Check if they want more detail: "Would you like me to elaborate on any part?"
• Connect your answer to the role: "This experience prepared me for..."

**Red Flags to Avoid:**
• Speaking negatively about previous employers
• Being vague or generic in answers
• Not asking any questions about the role
• Focusing only on what you'll gain, not what you'll contribute

**Your Questions to Ask:**
• "What does success look like in this role after 90 days?"
• "What are the biggest challenges facing the team right now?"
• "How does this role contribute to the company's goals?"

**Follow-up:**
• Send a thank-you email within 24 hours
• Reference specific conversation points
• Reiterate your interest and key qualifications

Ready to practice? Ask me to start a mock interview or generate specific questions! 🚀"""
    
    async def _generate_response(self, conversation: Conversation) -> str:
        """Generate AI response using LLM service with job search and interview prep integration"""
        try:
            # Get the latest user message
            latest_message = conversation.messages[-1]
            user_message = latest_message.content if latest_message.message_type == MessageType.USER else ""
            
            # Check if this is a job search query
            job_search_result = await self._handle_job_search_query(user_message, conversation.user_id)
            if job_search_result:
                return job_search_result
            
            # Check if this is an interview preparation query
            # Note: conversation type is not stored in context, so we'll detect based on content
            if await self._detect_interview_prep_query(user_message, ""):
                interview_result = await self._handle_interview_prep_query(user_message, conversation)
                if interview_result:
                    return interview_result
            
            # Prepare messages for LLM (last 10 messages for context)
            recent_messages = conversation.messages[-10:]
            
            # Convert to LLM format
            llm_messages = []
            for msg in recent_messages:
                if msg.message_type == MessageType.SYSTEM:
                    llm_messages.append({"role": "system", "content": msg.content})
                elif msg.message_type == MessageType.USER:
                    llm_messages.append({"role": "user", "content": msg.content})
                elif msg.message_type == MessageType.ASSISTANT:
                    llm_messages.append({"role": "assistant", "content": msg.content})
            
            # Add user context to system message if available
            if conversation.context:
                context_info = f"\nUser Context: {json.dumps(conversation.context, indent=2)}"
                if llm_messages and llm_messages[0]["role"] == "system":
                    llm_messages[0]["content"] += context_info
            
            # Generate response
            response = await self.llm_service.chat_completion(
                messages=llm_messages,
                temperature=0.7,
                max_tokens=1000
            )
            
            return response
            
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble processing your request right now. Please try again in a moment."
    
    async def get_conversation_stats(self, user_id: int) -> Dict[str, Any]:
        """Get conversation statistics for a user"""
        try:
            user_conversations = [
                conv for conv in self.conversations.values() 
                if conv.user_id == user_id
            ]
            
            total_conversations = len(user_conversations)
            active_conversations = len([conv for conv in user_conversations if conv.status == ConversationStatus.ACTIVE])
            total_messages = sum(len([msg for msg in conv.messages if msg.message_type != MessageType.SYSTEM]) for conv in user_conversations)
            
            return {
                "total_conversations": total_conversations,
                "active_conversations": active_conversations,
                "total_messages": total_messages,
                "rate_limit_remaining": max(0, self.rate_limiter.max_requests - len(self.rate_limiter.requests.get(user_id, [])))
            }
            
        except Exception as e:
            logger.error(f"Error getting conversation stats: {e}")
            return {"error": str(e)} 