import asyncio
import logging
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
import json
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Template
import os

from src.models.digest import (
    DigestContent, DigestRequest, DigestResponse, DigestType, DigestStatus,
    JobMatchSummary, ApplicationUpdate, ProfileInsight, SystemStats,
    EmailNotification, NotificationConfig, NotificationType,
    DigestPreferences, DigestTemplateData
)
from src.services.database_service import DatabaseService
from src.services.llm_service import LLMService
from src.services.vector_service import VectorService

logger = logging.getLogger(__name__)

class DigestService:
    """Service for generating and sending daily digests"""
    
    def __init__(self, db_service: DatabaseService, llm_service: LLMService, vector_service: VectorService):
        self.db = db_service
        self.llm = llm_service
        self.vector_service = vector_service
        
        # Email configuration
        self.smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(os.getenv("SMTP_PORT", "587"))
        self.smtp_username = os.getenv("SMTP_USERNAME")
        self.smtp_password = os.getenv("SMTP_PASSWORD")
        self.from_email = os.getenv("FROM_EMAIL", "noreply@jobapplicationagent.com")
        self.from_name = os.getenv("FROM_NAME", "Job Application Agent")
        
        # Base URLs
        self.base_url = os.getenv("BASE_URL", "http://localhost:8000")
        
    async def generate_digest(self, request: DigestRequest) -> DigestResponse:
        """Generate a digest for a user"""
        try:
            start_time = datetime.now()
            
            # Get user preferences
            preferences = await self._get_user_preferences(request.user_id)
            
            # Generate digest content
            content = await self._generate_digest_content(request, preferences)
            
            # Save digest to database
            digest_id = await self._save_digest(request.user_id, request.digest_type, content)
            
            # Send notification if requested
            email_sent = False
            email_id = None
            if request.include_job_matches or request.include_applications or request.include_insights:
                email_sent, email_id = await self._send_digest_notification(request.user_id, content, digest_id)
            
            generation_time = (datetime.now() - start_time).total_seconds()
            
            return DigestResponse(
                success=True,
                digest_id=str(digest_id),
                content=content,
                generated_at=datetime.now(),
                email_sent=email_sent,
                email_id=email_id
            )
            
        except Exception as e:
            logger.error(f"Error generating digest for user {request.user_id}: {str(e)}")
            return DigestResponse(
                success=False,
                generated_at=datetime.now(),
                error_message=str(e)
            )
    
    async def _generate_digest_content(self, request: DigestRequest, preferences: DigestPreferences) -> DigestContent:
        """Generate the content for a digest"""
        digest_date = request.date or date.today()
        
        # Get job matches
        job_matches = []
        if request.include_job_matches:
            job_matches = await self._get_job_matches(request.user_id, preferences, request.max_job_matches)
        
        # Get application updates
        application_updates = []
        if request.include_applications:
            application_updates = await self._get_application_updates(request.user_id, request.max_application_updates)
        
        # Get profile insights
        profile_insights = []
        if request.include_insights:
            profile_insights = await self._generate_profile_insights(request.user_id)
        
        # Get system stats
        system_stats = None
        if request.include_stats:
            system_stats = await self._get_system_stats(request.user_id, digest_date)
        
        # Get trending data
        top_skills = await self._get_top_skills_in_demand()
        trending_companies = await self._get_trending_companies()
        salary_insights = await self._get_salary_insights(request.user_id)
        
        return DigestContent(
            user_id=request.user_id,
            digest_date=digest_date,
            job_matches=job_matches,
            application_updates=application_updates,
            profile_insights=profile_insights,
            system_stats=system_stats,
            top_skills_in_demand=top_skills,
            trending_companies=trending_companies,
            salary_insights=salary_insights
        )
    
    async def _get_job_matches(self, user_id: int, preferences: DigestPreferences, max_matches: int) -> List[JobMatchSummary]:
        """Get job matches for a user"""
        try:
            # Get user profile for matching
            user_profile = await self.db.get_user_profile(user_id)
            if not user_profile:
                return []
            
            # Get recent jobs from database
            query = """
                SELECT j.*, jd.title, jd.company, jd.location, jd.salary_range, jd.job_type, jd.remote_type
                FROM jobs j
                JOIN job_descriptions jd ON j.job_description_id = jd.id
                WHERE j.created_at >= CURRENT_DATE - INTERVAL '7 days'
                ORDER BY j.created_at DESC
                LIMIT 100
            """
            
            jobs = await self.db.execute_query(query)
            
            # Calculate match scores using vector similarity
            job_matches = []
            for job in jobs:
                match_score, match_reasons = await self._calculate_job_match(
                    job, user_profile, preferences
                )
                
                if match_score >= 0.6:  # Only include good matches
                    job_matches.append(JobMatchSummary(
                        job_id=str(job['id']),
                        title=job['title'],
                        company=job['company'],
                        location=job['location'],
                        match_score=match_score,
                        match_reasons=match_reasons,
                        salary_range=job.get('salary_range'),
                        job_type=job.get('job_type'),
                        remote_type=job.get('remote_type'),
                        application_url=job['url'],
                        posted_date=job['created_at'].strftime('%Y-%m-%d') if job['created_at'] else None
                    ))
            
            # Sort by match score and limit
            job_matches.sort(key=lambda x: x.match_score, reverse=True)
            return job_matches[:max_matches]
            
        except Exception as e:
            logger.error(f"Error getting job matches: {str(e)}")
            return []
    
    async def _calculate_job_match(self, job: Dict, user_profile: Dict, preferences: DigestPreferences) -> tuple[float, List[str]]:
        """Calculate match score between job and user profile"""
        try:
            # Get job description for vector comparison
            job_desc_query = """
                SELECT description, requirements, skills
                FROM job_descriptions
                WHERE id = %s
            """
            job_desc = await self.db.execute_query(job_desc_query, (job['job_description_id'],))
            
            if not job_desc:
                return 0.0, []
            
            job_desc = job_desc[0]
            
            # Combine job text for vector comparison
            job_text = f"{job_desc['description']} {job_desc['requirements']} {job_desc['skills']}"
            
            # Get user skills and experience
            user_skills = user_profile.get('skills', [])
            user_experience = user_profile.get('experience', [])
            
            # Calculate vector similarity
            similarity_score = await self.vector_service.calculate_similarity(
                job_text, 
                " ".join(user_skills + [exp.get('description', '') for exp in user_experience])
            )
            
            # Calculate preference matches
            preference_score = 0.0
            match_reasons = []
            
            # Location preference
            if preferences.preferred_locations and job['location']:
                if any(loc.lower() in job['location'].lower() for loc in preferences.preferred_locations):
                    preference_score += 0.2
                    match_reasons.append("Location preference match")
            
            # Job type preference
            if preferences.preferred_job_types and job.get('job_type'):
                if job['job_type'] in preferences.preferred_job_types:
                    preference_score += 0.15
                    match_reasons.append("Job type preference match")
            
            # Salary range preference
            if preferences.salary_range_min and preferences.salary_range_max and job.get('salary_range'):
                # Simple salary parsing (in real implementation, use proper salary parsing)
                if "salary_range" in job['salary_range'].lower():
                    preference_score += 0.1
                    match_reasons.append("Salary range match")
            
            # Skills match
            if user_skills and job_desc.get('skills'):
                job_skills = [skill.strip().lower() for skill in job_desc['skills'].split(',')]
                user_skills_lower = [skill.lower() for skill in user_skills]
                matching_skills = [skill for skill in job_skills if skill in user_skills_lower]
                
                if matching_skills:
                    skill_match_ratio = len(matching_skills) / len(job_skills)
                    preference_score += skill_match_ratio * 0.3
                    match_reasons.append(f"Skills match: {', '.join(matching_skills[:3])}")
            
            # Combine scores
            final_score = (similarity_score * 0.6) + (preference_score * 0.4)
            
            if not match_reasons:
                match_reasons.append("Good overall match")
            
            return min(final_score, 1.0), match_reasons
            
        except Exception as e:
            logger.error(f"Error calculating job match: {str(e)}")
            return 0.0, []
    
    async def _get_application_updates(self, user_id: int, max_updates: int) -> List[ApplicationUpdate]:
        """Get recent application status updates"""
        try:
            # This would typically query an applications table
            # For now, return sample data
            return [
                ApplicationUpdate(
                    application_id="app_001",
                    job_title="Senior Software Engineer",
                    company="Tech Corp",
                    old_status="Applied",
                    new_status="Under Review",
                    update_date=datetime.now() - timedelta(days=1),
                    notes="Application is being reviewed by the hiring team",
                    follow_up_required=False
                ),
                ApplicationUpdate(
                    application_id="app_002",
                    job_title="Data Scientist",
                    company="AI Startup",
                    old_status="Under Review",
                    new_status="Interview Scheduled",
                    update_date=datetime.now() - timedelta(hours=6),
                    notes="First round interview scheduled for next week",
                    follow_up_required=True,
                    follow_up_date=date.today() + timedelta(days=7)
                )
            ][:max_updates]
            
        except Exception as e:
            logger.error(f"Error getting application updates: {str(e)}")
            return []
    
    async def _generate_profile_insights(self, user_id: int) -> List[ProfileInsight]:
        """Generate insights about user profile"""
        try:
            user_profile = await self.db.get_user_profile(user_id)
            if not user_profile:
                return []
            
            insights = []
            
            # Check profile completeness
            completeness_score = self._calculate_profile_completeness(user_profile)
            if completeness_score < 0.8:
                insights.append(ProfileInsight(
                    insight_type="profile_completeness",
                    title="Complete Your Profile",
                    description=f"Your profile is {completeness_score*100:.0f}% complete. Add more details to improve job matches.",
                    priority="high" if completeness_score < 0.6 else "medium",
                    action_required=True,
                    action_url=f"{self.base_url}/profile/edit"
                ))
            
            # Check for missing skills
            missing_skills = await self._identify_missing_skills(user_profile)
            if missing_skills:
                insights.append(ProfileInsight(
                    insight_type="missing_skills",
                    title="Skills in High Demand",
                    description=f"Consider adding these skills to your profile: {', '.join(missing_skills[:5])}",
                    priority="medium",
                    action_required=False,
                    action_url=f"{self.base_url}/profile/skills"
                ))
            
            # Resume optimization
            if user_profile.get('resume_url'):
                insights.append(ProfileInsight(
                    insight_type="resume_optimization",
                    title="Optimize Your Resume",
                    description="Your resume could be optimized with AI-powered suggestions for better ATS compatibility.",
                    priority="low",
                    action_required=False,
                    action_url=f"{self.base_url}/resume/optimize"
                ))
            
            return insights
            
        except Exception as e:
            logger.error(f"Error generating profile insights: {str(e)}")
            return []
    
    def _calculate_profile_completeness(self, user_profile: Dict) -> float:
        """Calculate profile completeness score"""
        required_fields = ['name', 'email', 'title', 'skills', 'experience']
        optional_fields = ['bio', 'education', 'certifications', 'resume_url', 'linkedin_url']
        
        required_score = sum(1 for field in required_fields if user_profile.get(field)) / len(required_fields)
        optional_score = sum(1 for field in optional_fields if user_profile.get(field)) / len(optional_fields)
        
        return (required_score * 0.7) + (optional_score * 0.3)
    
    async def _identify_missing_skills(self, user_profile: Dict) -> List[str]:
        """Identify skills that are in high demand but missing from profile"""
        try:
            # Get trending skills from recent job postings
            query = """
                SELECT skills FROM job_descriptions 
                WHERE created_at >= CURRENT_DATE - INTERVAL '30 days'
                LIMIT 100
            """
            job_descriptions = await self.db.execute_query(query)
            
            # Extract and count skills
            skill_counts = {}
            user_skills = set(skill.lower() for skill in user_profile.get('skills', []))
            
            for job in job_descriptions:
                if job['skills']:
                    skills = [skill.strip().lower() for skill in job['skills'].split(',')]
                    for skill in skills:
                        if skill not in user_skills:
                            skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            # Return top missing skills
            sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
            return [skill for skill, count in sorted_skills[:10]]
            
        except Exception as e:
            logger.error(f"Error identifying missing skills: {str(e)}")
            return []
    
    async def _get_system_stats(self, user_id: int, digest_date: date) -> SystemStats:
        """Get system statistics for the user"""
        try:
            # Get stats for the specified date
            query = """
                SELECT 
                    COUNT(*) as total_jobs_searched,
                    COUNT(CASE WHEN created_at >= %s THEN 1 END) as new_jobs_found
                FROM jobs
                WHERE created_at >= %s - INTERVAL '1 day'
            """
            
            stats = await self.db.execute_query(query, (digest_date, digest_date))
            job_stats = stats[0] if stats else {'total_jobs_searched': 0, 'new_jobs_found': 0}
            
            # For now, return sample stats (in real implementation, query actual data)
            return SystemStats(
                total_jobs_searched=job_stats['total_jobs_searched'],
                new_jobs_found=job_stats['new_jobs_found'],
                applications_submitted=5,  # Sample data
                interviews_scheduled=2,
                offers_received=0,
                profile_views=15,
                skills_matched=8
            )
            
        except Exception as e:
            logger.error(f"Error getting system stats: {str(e)}")
            return SystemStats(
                total_jobs_searched=0,
                new_jobs_found=0,
                applications_submitted=0,
                interviews_scheduled=0,
                offers_received=0,
                profile_views=0,
                skills_matched=0
            )
    
    async def _get_top_skills_in_demand(self) -> List[str]:
        """Get top skills currently in demand"""
        try:
            # Query recent job postings for trending skills
            query = """
                SELECT skills FROM job_descriptions 
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                LIMIT 50
            """
            job_descriptions = await self.db.execute_query(query)
            
            skill_counts = {}
            for job in job_descriptions:
                if job['skills']:
                    skills = [skill.strip() for skill in job['skills'].split(',')]
                    for skill in skills:
                        skill_counts[skill] = skill_counts.get(skill, 0) + 1
            
            sorted_skills = sorted(skill_counts.items(), key=lambda x: x[1], reverse=True)
            return [skill for skill, count in sorted_skills[:10]]
            
        except Exception as e:
            logger.error(f"Error getting top skills: {str(e)}")
            return ["Python", "JavaScript", "React", "AWS", "Docker"]
    
    async def _get_trending_companies(self) -> List[str]:
        """Get trending companies from recent job postings"""
        try:
            query = """
                SELECT company, COUNT(*) as job_count
                FROM job_descriptions 
                WHERE created_at >= CURRENT_DATE - INTERVAL '7 days'
                GROUP BY company
                ORDER BY job_count DESC
                LIMIT 10
            """
            companies = await self.db.execute_query(query)
            return [company['company'] for company in companies]
            
        except Exception as e:
            logger.error(f"Error getting trending companies: {str(e)}")
            return ["Google", "Microsoft", "Amazon", "Meta", "Apple"]
    
    async def _get_salary_insights(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get salary insights for the user's field"""
        try:
            # This would analyze salary data for similar roles
            return {
                "average_salary": "$120,000",
                "salary_range": "$80,000 - $160,000",
                "trend": "increasing",
                "recommendation": "Your target salary is competitive for your experience level"
            }
        except Exception as e:
            logger.error(f"Error getting salary insights: {str(e)}")
            return None
    
    async def _get_user_preferences(self, user_id: int) -> DigestPreferences:
        """Get user's digest preferences"""
        try:
            query = """
                SELECT * FROM digest_preferences WHERE user_id = %s
            """
            result = await self.db.execute_query(query, (user_id,))
            
            if result:
                pref = result[0]
                return DigestPreferences(
                    user_id=user_id,
                    include_job_matches=pref['include_job_matches'],
                    include_applications=pref['include_applications'],
                    include_insights=pref['include_insights'],
                    include_stats=pref['include_stats'],
                    max_job_matches=pref['max_job_matches'],
                    max_application_updates=pref['max_application_updates'],
                    preferred_job_types=pref['preferred_job_types'] or [],
                    preferred_locations=pref['preferred_locations'] or [],
                    salary_range_min=pref['salary_range_min'],
                    salary_range_max=pref['salary_range_max'],
                    notification_frequency=pref['notification_frequency'],
                    preferred_time=pref['preferred_time'].strftime('%H:%M') if pref['preferred_time'] else '09:00',
                    timezone=pref['timezone']
                )
            else:
                # Return default preferences
                return DigestPreferences(user_id=user_id)
                
        except Exception as e:
            logger.error(f"Error getting user preferences: {str(e)}")
            return DigestPreferences(user_id=user_id)
    
    async def _save_digest(self, user_id: int, digest_type: DigestType, content: DigestContent) -> str:
        """Save digest to database"""
        try:
            # Since execute_query is a placeholder, we'll generate a mock ID
            # In a real implementation, this would use proper database operations
            import uuid
            digest_id = str(uuid.uuid4())
            
            logger.info(f"Mock digest saved with ID: {digest_id}")
            return digest_id
            
        except Exception as e:
            logger.error(f"Error saving digest: {str(e)}")
            raise
    
    async def _send_digest_notification(self, user_id: int, content: DigestContent, digest_id: str) -> tuple[bool, Optional[str]]:
        """Send digest notification to user"""
        try:
            # Get user's notification preferences
            notification_config = await self._get_notification_config(user_id)
            if not notification_config or not notification_config.is_active:
                return False, None
            
            # Get user profile for personalization
            user_profile = await self.db.get_user_profile(user_id)
            user_name = user_profile.get('name', 'there') if user_profile else 'there'
            
            # Prepare template data
            template_data = DigestTemplateData(
                user_name=user_name,
                digest_date=content.digest_date.strftime('%B %d, %Y'),
                job_matches=content.job_matches,
                application_updates=content.application_updates,
                profile_insights=content.profile_insights,
                system_stats=content.system_stats,
                top_skills=content.top_skills_in_demand,
                trending_companies=content.trending_companies,
                salary_insights=content.salary_insights,
                unsubscribe_url=f"{self.base_url}/unsubscribe/{user_id}",
                settings_url=f"{self.base_url}/settings/digest",
                dashboard_url=f"{self.base_url}/dashboard"
            )
            
            # Generate email content
            email_content = await self._generate_email_content(template_data, content.digest_date)
            
            # Send email
            if notification_config.notification_type == NotificationType.EMAIL:
                success, email_id = await self._send_email(
                    notification_config.email_address,
                    email_content.subject,
                    email_content.html_content,
                    email_content.text_content
                )
                
                # Save notification history
                await self._save_notification_history(
                    user_id, NotificationType.EMAIL, digest_id, 
                    email_content.subject, email_content.html_content[:200], success
                )
                
                return success, email_id
            
            return False, None
            
        except Exception as e:
            logger.error(f"Error sending digest notification: {str(e)}")
            return False, None
    
    async def _get_notification_config(self, user_id: int) -> Optional[NotificationConfig]:
        """Get user's notification configuration"""
        try:
            query = """
                SELECT * FROM notification_configs 
                WHERE user_id = %s AND notification_type = 'email' AND is_active = true
            """
            result = await self.db.execute_query(query, (user_id,))
            
            if result:
                config = result[0]
                return NotificationConfig(
                    user_id=user_id,
                    notification_type=NotificationType.EMAIL,
                    email_address=config['email_address'],
                    is_active=config['is_active'],
                    preferences=config['preferences'] or {}
                )
            
            return None
            
        except Exception as e:
            logger.error(f"Error getting notification config: {str(e)}")
            return None
    
    async def _generate_email_content(self, template_data: DigestTemplateData, digest_date: date) -> EmailNotification:
        """Generate email content using templates"""
        try:
            # Get email template
            template_name = 'daily_digest' if digest_date == date.today() else 'weekly_digest'
            template = await self._get_email_template(template_name)
            
            # Render templates
            subject = Template(template['subject_template']).render(**template_data.model_dump())
            html_content = Template(template['html_template']).render(**template_data.model_dump())
            text_content = Template(template['text_template']).render(**template_data.model_dump())
            
            return EmailNotification(
                to_email=template_data.user_name,  # This should be the actual email
                subject=subject,
                html_content=html_content,
                text_content=text_content
            )
            
        except Exception as e:
            logger.error(f"Error generating email content: {str(e)}")
            raise
    
    async def _get_email_template(self, template_name: str) -> Dict[str, Any]:
        """Get email template from database"""
        try:
            query = """
                SELECT * FROM email_templates WHERE name = %s AND is_active = true
            """
            result = await self.db.execute_query(query, (template_name,))
            
            if result:
                return result[0]
            else:
                # Return default template
                return {
                    'subject_template': 'Your Job Digest - {{digest_date}}',
                    'html_template': '<h1>Your Job Digest</h1><p>{{user_name}}, here is your digest.</p>',
                    'text_template': 'Your Job Digest\n\n{{user_name}}, here is your digest.'
                }
                
        except Exception as e:
            logger.error(f"Error getting email template: {str(e)}")
            raise
    
    async def _send_email(self, to_email: str, subject: str, html_content: str, text_content: str) -> tuple[bool, Optional[str]]:
        """Send email using SMTP"""
        try:
            if not all([self.smtp_username, self.smtp_password]):
                logger.warning("SMTP credentials not configured, skipping email send")
                return False, None
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = f"{self.from_name} <{self.from_email}>"
            msg['To'] = to_email
            
            # Attach parts
            text_part = MIMEText(text_content, 'plain')
            html_part = MIMEText(html_content, 'html')
            msg.attach(text_part)
            msg.attach(html_part)
            
            # Send email
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(msg)
            
            return True, f"email_{datetime.now().timestamp()}"
            
        except Exception as e:
            logger.error(f"Error sending email: {str(e)}")
            return False, None
    
    async def _save_notification_history(self, user_id: int, notification_type: NotificationType, 
                                       digest_id: str, subject: str, content_preview: str, success: bool):
        """Save notification history"""
        try:
            query = """
                INSERT INTO notification_history 
                (user_id, notification_type, digest_id, subject, content_preview, status)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            
            status = 'sent' if success else 'failed'
            await self.db.execute_query(
                query, 
                (user_id, notification_type.value, digest_id, subject, content_preview, status)
            )
            
        except Exception as e:
            logger.error(f"Error saving notification history: {str(e)}")
    
    async def get_digest_schedules(self) -> List[Dict[str, Any]]:
        """Get all active digest schedules"""
        try:
            query = """
                SELECT ds.*, up.email, up.name
                FROM digest_schedules ds
                JOIN user_profiles up ON ds.user_id = up.id
                WHERE ds.is_active = true
                ORDER BY ds.next_scheduled
            """
            
            return await self.db.execute_query(query)
            
        except Exception as e:
            logger.error(f"Error getting digest schedules: {str(e)}")
            return []
    
    async def update_next_scheduled(self, schedule_id: int, next_scheduled: datetime):
        """Update next scheduled time for a digest"""
        try:
            query = """
                UPDATE digest_schedules 
                SET next_scheduled = %s, updated_at = NOW()
                WHERE id = %s
            """
            
            await self.db.execute_query(query, (next_scheduled, schedule_id))
            
        except Exception as e:
            logger.error(f"Error updating next scheduled: {str(e)}")
    
    async def get_digest_stats(self, start_date: date, end_date: date) -> Dict[str, Any]:
        """Get digest generation statistics"""
        try:
            query = """
                SELECT 
                    COUNT(*) as total_digests,
                    COUNT(CASE WHEN status = 'sent' THEN 1 END) as successful_digests,
                    COUNT(CASE WHEN status = 'failed' THEN 1 END) as failed_digests,
                    AVG(EXTRACT(EPOCH FROM (generated_at - created_at))) as avg_generation_time
                FROM generated_digests
                WHERE digest_date BETWEEN %s AND %s
            """
            
            result = await self.db.execute_query(query, (start_date, end_date))
            return result[0] if result else {}
            
        except Exception as e:
            logger.error(f"Error getting digest stats: {str(e)}")
            return {} 