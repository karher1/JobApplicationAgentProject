import os
import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime, date
import aiofiles
from pathlib import Path

from supabase import create_client, Client
from src.models.user_profile import (
    User, UserCreate, UserUpdate, UserProfile,
    UserPreferences, UserPreferencesCreate, UserPreferencesUpdate,
    Resume, ResumeCreate, ResumeUpdate, ResumeContent, ResumeContentCreate,
    Skill, SkillCreate, UserSkill, UserSkillCreate, UserSkillUpdate,
    WorkExperience, WorkExperienceCreate, WorkExperienceUpdate,
    Education, EducationCreate, EducationUpdate,
    Certification, CertificationCreate, CertificationUpdate,
    ApplicationHistory, ApplicationHistoryCreate, ApplicationHistoryUpdate,
    SkillAddRequest, ResumeUploadRequest
)
from src.models.schemas import ServiceHealth
from src.core.config import get_settings

logger = logging.getLogger(__name__)

class UserProfileService:
    """Service for managing user profiles, resumes, skills, and preferences"""
    
    def __init__(self):
        settings = get_settings()
        self.supabase_url = settings.supabase_url
        self.supabase_key = settings.supabase_anon_key
        self.supabase: Optional[Client] = None
        self.uploads_dir = Path("uploads/resumes")
        self.uploads_dir.mkdir(parents=True, exist_ok=True)
        
    async def initialize(self):
        """Initialize Supabase client"""
        try:
            if not self.supabase_url or not self.supabase_key:
                raise ValueError("Supabase URL and key must be set")
            
            self.supabase = create_client(self.supabase_url, self.supabase_key)
            logger.info("User profile service initialized successfully")
            
        except Exception as e:
            logger.error(f"Error initializing user profile service: {e}")
            raise
    
    async def health_check(self) -> ServiceHealth:
        """Check user profile service health"""
        try:
            if not self.supabase:
                return ServiceHealth(status="unhealthy", message="Supabase client not initialized")
            
            # Test connection by querying users table
            result = self.supabase.table("users").select("id").limit(1).execute()
            return ServiceHealth(status="healthy", message="Database connection successful")
        except Exception as e:
            return ServiceHealth(status="unhealthy", message=str(e))
    
    # User Management
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user"""
        try:
            result = self.supabase.table("users").insert(user_data.model_dump()).execute()
            return User(**result.data[0])
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            raise
    
    async def get_user(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        try:
            result = self.supabase.table("users").select("*").eq("id", user_id).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting user: {e}")
            raise
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        try:
            result = self.supabase.table("users").select("*").eq("email", email).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            raise
    
    async def update_user(self, user_id: int, user_data: UserUpdate) -> Optional[User]:
        """Update user"""
        try:
            update_data = {k: v for k, v in user_data.model_dump().items() if v is not None}
            result = self.supabase.table("users").update(update_data).eq("id", user_id).execute()
            if result.data:
                return User(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error updating user: {e}")
            raise
    
    async def delete_user(self, user_id: int) -> bool:
        """Delete user and all associated data"""
        try:
            result = self.supabase.table("users").delete().eq("id", user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting user: {e}")
            raise
    
    # User Preferences Management
    async def create_user_preferences(self, preferences_data: UserPreferencesCreate) -> UserPreferences:
        """Create user preferences"""
        try:
            result = self.supabase.table("user_preferences").insert(preferences_data.model_dump()).execute()
            return UserPreferences(**result.data[0])
        except Exception as e:
            logger.error(f"Error creating user preferences: {e}")
            raise
    
    async def get_user_preferences(self, user_id: int) -> Optional[UserPreferences]:
        """Get user preferences"""
        try:
            result = self.supabase.table("user_preferences").select("*").eq("user_id", user_id).execute()
            if result.data:
                return UserPreferences(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting user preferences: {e}")
            raise
    
    async def update_user_preferences(self, user_id: int, preferences_data: UserPreferencesUpdate) -> Optional[UserPreferences]:
        """Update user preferences"""
        try:
            update_data = {k: v for k, v in preferences_data.model_dump().items() if v is not None}
            result = self.supabase.table("user_preferences").update(update_data).eq("user_id", user_id).execute()
            if result.data:
                return UserPreferences(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            raise
    
    # Resume Management
    async def upload_resume(self, user_id: int, upload_request: ResumeUploadRequest) -> Resume:
        """Upload and store a resume"""
        try:
            import base64
            
            # Decode base64 content
            file_content = base64.b64decode(upload_request.file_content)
            
            # Save file to disk
            file_path = self.uploads_dir / f"{user_id}_{upload_request.file_name}"
            async with aiofiles.open(file_path, 'wb') as f:
                await f.write(file_content)
            
            # Create resume record
            resume_data = ResumeCreate(
                user_id=user_id,
                title=upload_request.name,
                file_path=str(file_path)
            )
            
            result = self.supabase.table("resumes").insert(resume_data.model_dump()).execute()
            return Resume(**result.data[0])
        except Exception as e:
            logger.error(f"Error uploading resume: {e}")
            raise
    
    async def get_user_resumes(self, user_id: int) -> List[Resume]:
        """Get all resumes for a user"""
        try:
            result = self.supabase.table("resumes").select("*").eq("user_id", user_id).execute()
            return [Resume(**resume) for resume in result.data]
        except Exception as e:
            logger.error(f"Error getting user resumes: {e}")
            raise
    
    async def get_primary_resume(self, user_id: int) -> Optional[Resume]:
        """Get user's primary resume"""
        try:
            result = self.supabase.table("resumes").select("*").eq("user_id", user_id).eq("is_primary", True).execute()
            if result.data:
                return Resume(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error getting primary resume: {e}")
            raise
    
    async def set_primary_resume(self, user_id: int, resume_id: int) -> bool:
        """Set a resume as primary"""
        try:
            # First, unset all primary resumes for this user
            self.supabase.table("resumes").update({"is_primary": False}).eq("user_id", user_id).execute()
            
            # Then set the specified resume as primary
            result = self.supabase.table("resumes").update({"is_primary": True}).eq("id", resume_id).eq("user_id", user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error setting primary resume: {e}")
            raise
    
    async def delete_resume(self, user_id: int, resume_id: int) -> bool:
        """Delete a resume"""
        try:
            result = self.supabase.table("resumes").delete().eq("id", resume_id).eq("user_id", user_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting resume: {e}")
            raise
    
    # Skills Management
    async def add_skill_to_user(self, user_id: int, skill_request: SkillAddRequest) -> UserSkill:
        """Add a skill to a user"""
        try:
            # First, get or create the skill
            skill_result = self.supabase.table("skills").select("*").eq("name", skill_request.skill_name).execute()
            if skill_result.data:
                skill_id = skill_result.data[0]["id"]
            else:
                skill_data = SkillCreate(name=skill_request.skill_name)
                skill_result = self.supabase.table("skills").insert(skill_data.model_dump()).execute()
                skill_id = skill_result.data[0]["id"]
            
            # Check if user already has this skill
            existing_skill = self.supabase.table("user_skills").select("*").eq("user_id", user_id).eq("skill_id", skill_id).execute()
            if existing_skill.data:
                # Update existing skill instead of creating duplicate
                update_data = {
                    "proficiency_level": skill_request.proficiency_level,
                    "years_of_experience": skill_request.years_of_experience,
                    "is_highlighted": skill_request.is_highlighted
                }
                result = self.supabase.table("user_skills").update(update_data).eq("user_id", user_id).eq("skill_id", skill_id).execute()
                return UserSkill(**result.data[0])
            
            # Add new skill to user
            user_skill_data = UserSkillCreate(
                user_id=user_id,
                skill_id=skill_id,
                proficiency_level=skill_request.proficiency_level,
                years_of_experience=skill_request.years_of_experience,
                is_highlighted=skill_request.is_highlighted
            )
            
            result = self.supabase.table("user_skills").insert(user_skill_data.model_dump()).execute()
            return UserSkill(**result.data[0])
        except Exception as e:
            logger.error(f"Error adding skill to user: {e}")
            raise
    
    async def get_user_skills(self, user_id: int) -> List[UserSkill]:
        """Get all skills for a user"""
        try:
            result = self.supabase.table("user_skills").select("*, skills(*)").eq("user_id", user_id).execute()
            # Transform the data to match the UserSkill model structure
            skills_data = []
            for skill_item in result.data:
                # Transform 'skills' key to 'skill' key to match UserSkill model
                if 'skills' in skill_item:
                    skill_item['skill'] = skill_item.pop('skills')
                
                # Remove extra fields that might cause model validation issues
                if 'updated_at' in skill_item:
                    skill_item.pop('updated_at')
                
                skills_data.append(skill_item)
            
            return [UserSkill(**skill) for skill in skills_data]
        except Exception as e:
            logger.error(f"Error getting user skills: {e}")
            raise
    
    async def update_user_skill(self, user_id: int, skill_id: int, skill_data: UserSkillUpdate) -> Optional[UserSkill]:
        """Update a user's skill"""
        try:
            update_data = {k: v for k, v in skill_data.model_dump().items() if v is not None}
            result = self.supabase.table("user_skills").update(update_data).eq("user_id", user_id).eq("skill_id", skill_id).execute()
            if result.data:
                return UserSkill(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error updating user skill: {e}")
            raise
    
    async def remove_user_skill(self, user_id: int, skill_id: int) -> bool:
        """Remove a skill from a user"""
        try:
            result = self.supabase.table("user_skills").delete().eq("user_id", user_id).eq("skill_id", skill_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error removing user skill: {e}")
            raise
    
    # Work Experience Management
    async def add_work_experience(self, work_data: WorkExperienceCreate) -> WorkExperience:
        """Add work experience to a user"""
        try:
            # Convert date objects to strings for JSON serialization
            data_dict = work_data.model_dump()
            if data_dict.get("start_date"):
                data_dict["start_date"] = data_dict["start_date"].isoformat()
            if data_dict.get("end_date"):
                data_dict["end_date"] = data_dict["end_date"].isoformat()
            
            result = self.supabase.table("work_experience").insert(data_dict).execute()
            return WorkExperience(**result.data[0])
        except Exception as e:
            logger.error(f"Error adding work experience: {e}")
            raise
    
    async def get_user_work_experience(self, user_id: int) -> List[WorkExperience]:
        """Get all work experience for a user"""
        try:
            result = self.supabase.table("work_experience").select("*").eq("user_id", user_id).execute()
            return [WorkExperience(**exp) for exp in result.data]
        except Exception as e:
            logger.error(f"Error getting user work experience: {e}")
            raise
    
    async def update_work_experience(self, work_id: int, work_data: WorkExperienceUpdate) -> Optional[WorkExperience]:
        """Update work experience"""
        try:
            update_data = {k: v for k, v in work_data.model_dump().items() if v is not None}
            result = self.supabase.table("work_experience").update(update_data).eq("id", work_id).execute()
            if result.data:
                return WorkExperience(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error updating work experience: {e}")
            raise
    
    async def delete_work_experience(self, work_id: int) -> bool:
        """Delete work experience"""
        try:
            result = self.supabase.table("work_experience").delete().eq("id", work_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting work experience: {e}")
            raise
    
    # Education Management
    async def add_education(self, education_data: EducationCreate) -> Education:
        """Add education to a user"""
        try:
            # Convert date objects to strings for JSON serialization
            data_dict = education_data.model_dump()
            if data_dict.get("start_date"):
                data_dict["start_date"] = data_dict["start_date"].isoformat()
            if data_dict.get("end_date"):
                data_dict["end_date"] = data_dict["end_date"].isoformat()
            
            result = self.supabase.table("education").insert(data_dict).execute()
            return Education(**result.data[0])
        except Exception as e:
            logger.error(f"Error adding education: {e}")
            raise
    
    async def get_user_education(self, user_id: int) -> List[Education]:
        """Get all education for a user"""
        try:
            result = self.supabase.table("education").select("*").eq("user_id", user_id).execute()
            return [Education(**edu) for edu in result.data]
        except Exception as e:
            logger.error(f"Error getting user education: {e}")
            raise
    
    async def update_education(self, education_id: int, education_data: EducationUpdate) -> Optional[Education]:
        """Update education"""
        try:
            update_data = {k: v for k, v in education_data.model_dump().items() if v is not None}
            result = self.supabase.table("education").update(update_data).eq("id", education_id).execute()
            if result.data:
                return Education(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error updating education: {e}")
            raise
    
    async def delete_education(self, education_id: int) -> bool:
        """Delete education"""
        try:
            result = self.supabase.table("education").delete().eq("id", education_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting education: {e}")
            raise
    
    # Certification Management
    async def add_certification(self, cert_data: CertificationCreate) -> Certification:
        """Add certification to a user"""
        try:
            result = self.supabase.table("certifications").insert(cert_data.model_dump()).execute()
            return Certification(**result.data[0])
        except Exception as e:
            logger.error(f"Error adding certification: {e}")
            raise
    
    async def get_user_certifications(self, user_id: int) -> List[Certification]:
        """Get all certifications for a user"""
        try:
            result = self.supabase.table("certifications").select("*").eq("user_id", user_id).execute()
            return [Certification(**cert) for cert in result.data]
        except Exception as e:
            logger.error(f"Error getting user certifications: {e}")
            raise
    
    async def update_certification(self, cert_id: int, cert_data: CertificationUpdate) -> Optional[Certification]:
        """Update certification"""
        try:
            update_data = {k: v for k, v in cert_data.model_dump().items() if v is not None}
            result = self.supabase.table("certifications").update(update_data).eq("id", cert_id).execute()
            if result.data:
                return Certification(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error updating certification: {e}")
            raise
    
    async def delete_certification(self, cert_id: int) -> bool:
        """Delete certification"""
        try:
            result = self.supabase.table("certifications").delete().eq("id", cert_id).execute()
            return len(result.data) > 0
        except Exception as e:
            logger.error(f"Error deleting certification: {e}")
            raise
    
    # Application History Management
    async def add_application_history(self, app_data: ApplicationHistoryCreate) -> ApplicationHistory:
        """Add application history for a user"""
        try:
            result = self.supabase.table("application_history").insert(app_data.model_dump()).execute()
            return ApplicationHistory(**result.data[0])
        except Exception as e:
            logger.error(f"Error adding application history: {e}")
            raise
    
    async def get_user_application_history(self, user_id: int) -> List[ApplicationHistory]:
        """Get all application history for a user"""
        try:
            result = self.supabase.table("application_history").select("*").eq("user_id", user_id).execute()
            return [ApplicationHistory(**app) for app in result.data]
        except Exception as e:
            logger.error(f"Error getting user application history: {e}")
            raise
    
    async def update_application_status(self, app_id: int, status_data: ApplicationHistoryUpdate) -> Optional[ApplicationHistory]:
        """Update application status"""
        try:
            update_data = {k: v for k, v in status_data.model_dump().items() if v is not None}
            result = self.supabase.table("application_history").update(update_data).eq("id", app_id).execute()
            if result.data:
                return ApplicationHistory(**result.data[0])
            return None
        except Exception as e:
            logger.error(f"Error updating application status: {e}")
            raise
    
    # Composite Profile Management
    async def get_complete_user_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get complete user profile with all related data"""
        try:
            # Get user
            user = await self.get_user(user_id)
            if not user:
                return None
            
            # Initialize empty lists for missing tables
            preferences = None
            resumes = []
            skills = []
            work_experience = []
            education = []
            certifications = []
            application_history = []
            
            # Try to get preferences (table might not exist)
            try:
                preferences = await self.get_user_preferences(user_id)
            except Exception as e:
                logger.warning(f"Could not get user preferences: {e}")
            
            # Try to get resumes (table might not exist)
            try:
                resumes = await self.get_user_resumes(user_id)
            except Exception as e:
                logger.warning(f"Could not get user resumes: {e}")
            
            # Try to get skills (table might not exist)
            try:
                skills = await self.get_user_skills(user_id)
            except Exception as e:
                logger.warning(f"Could not get user skills: {e}")
            
            # Try to get work experience (table might not exist)
            try:
                work_experience = await self.get_user_work_experience(user_id)
            except Exception as e:
                logger.warning(f"Could not get user work experience: {e}")
            
            # Try to get education (table might not exist)
            try:
                education = await self.get_user_education(user_id)
            except Exception as e:
                logger.warning(f"Could not get user education: {e}")
            
            # Try to get certifications (table might not exist)
            try:
                certifications = await self.get_user_certifications(user_id)
            except Exception as e:
                logger.warning(f"Could not get user certifications: {e}")
            
            # Try to get application history (table might not exist)
            try:
                application_history = await self.get_user_application_history(user_id)
            except Exception as e:
                logger.warning(f"Could not get user application history: {e}")
            
            return UserProfile(
                user=user,
                preferences=preferences,
                resumes=resumes,
                skills=skills,
                work_experience=work_experience,
                education=education,
                certifications=certifications,
                application_history=application_history
            )
        except Exception as e:
            logger.error(f"Error getting complete user profile: {e}")
            raise
    
    # Utility Methods
    async def get_available_skills(self) -> List[Skill]:
        """Get all available skills in the system"""
        try:
            result = self.supabase.table("skills").select("*").execute()
            return [Skill(**skill) for skill in result.data]
        except Exception as e:
            logger.error(f"Error getting available skills: {e}")
            raise 