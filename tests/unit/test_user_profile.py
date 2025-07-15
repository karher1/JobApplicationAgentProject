#!/usr/bin/env python3
"""
Test script to verify User Profile Module (Module 1) functionality
"""

import os
import asyncio
import logging
from uuid import UUID
from datetime import date
from dotenv import load_dotenv

from services.user_profile_service import UserProfileService
from models.user_profile import (
    UserCreate, UserPreferencesCreate, SkillAddRequest,
    WorkExperienceCreate, EducationCreate, ResumeUploadRequest
)

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_user_profile():
    """Test user profile functionality"""
    try:
        print("🔍 Testing User Profile Module (Module 1)...")
        
        # Initialize user profile service
        user_profile_service = UserProfileService()
        await user_profile_service.initialize()
        print("✅ User profile service initialized successfully!")
        
        # Test 1: Create a user
        print("\n👤 Testing user creation...")
        user_data = UserCreate(
            email="test@example.com",
            first_name="John",
            last_name="Doe",
            phone="+1234567890",
            location="San Francisco, CA",
            timezone="America/Los_Angeles"
        )
        
        user = await user_profile_service.create_user(user_data)
        print(f"✅ Created user: {user.first_name} {user.last_name} ({user.id})")
        
        # Test 2: Create user preferences
        print("\n⚙️ Testing user preferences...")
        preferences_data = UserPreferencesCreate(
            user_id=user.id,
            preferred_job_titles=["Software Engineer", "Full Stack Developer"],
            preferred_locations=["San Francisco", "Remote"],
            salary_min=80000,
            salary_max=150000,
            remote_preference="remote",
            job_type_preference="fulltime",
            experience_level="mid"
        )
        
        preferences = await user_profile_service.create_user_preferences(preferences_data)
        print(f"✅ Created preferences for user {user.id}")
        
        # Test 3: Add skills
        print("\n🛠️ Testing skills management...")
        skills_to_add = [
            SkillAddRequest(skill_name="Python", proficiency_level="advanced", years_of_experience=5, is_highlighted=True),
            SkillAddRequest(skill_name="JavaScript", proficiency_level="intermediate", years_of_experience=3),
            SkillAddRequest(skill_name="React", proficiency_level="intermediate", years_of_experience=2),
            SkillAddRequest(skill_name="Docker", proficiency_level="beginner", years_of_experience=1)
        ]
        
        for skill_request in skills_to_add:
            skill = await user_profile_service.add_skill_to_user(user.id, skill_request)
            print(f"✅ Added skill: {skill_request.skill_name}")
        
        # Test 4: Add work experience
        print("\n💼 Testing work experience...")
        work_exp_data = WorkExperienceCreate(
            user_id=user.id,
            company_name="Tech Corp",
            job_title="Senior Software Engineer",
            location="San Francisco, CA",
            start_date=date(2020, 1, 1),
            end_date=date(2023, 12, 31),
            is_current=False,
            description="Led development of web applications using Python and React",
            achievements=["Improved performance by 50%", "Mentored 3 junior developers"],
            technologies_used=["Python", "React", "Docker", "AWS"]
        )
        
        work_exp = await user_profile_service.add_work_experience(work_exp_data)
        print(f"✅ Added work experience: {work_exp.job_title} at {work_exp.company_name}")
        
        # Test 5: Add education
        print("\n🎓 Testing education...")
        education_data = EducationCreate(
            user_id=user.id,
            institution_name="University of California",
            degree="Bachelor of Science",
            field_of_study="Computer Science",
            location="Berkeley, CA",
            start_date=date(2016, 9, 1),
            end_date=date(2020, 5, 1),
            is_current=False,
            gpa=3.8
        )
        
        education = await user_profile_service.add_education(education_data)
        print(f"✅ Added education: {education.degree} in {education.field_of_study}")
        
        # Test 6: Get complete user profile
        print("\n📋 Testing complete profile retrieval...")
        profile = await user_profile_service.get_complete_user_profile(user.id)
        print(f"✅ Retrieved complete profile for {profile.user.first_name} {profile.user.last_name}")
        print(f"   - Skills: {len(profile.skills)} skills")
        print(f"   - Work Experience: {len(profile.work_experience)} positions")
        print(f"   - Education: {len(profile.education)} degrees")
        print(f"   - Preferences: {'Set' if profile.preferences else 'Not set'}")
        
        # Test 7: Get available skills
        print("\n🔍 Testing available skills...")
        available_skills = await user_profile_service.get_available_skills()
        print(f"✅ Found {len(available_skills)} available skills in database")
        
        # Test 8: Test user preferences retrieval
        print("\n⚙️ Testing preferences retrieval...")
        user_prefs = await user_profile_service.get_user_preferences(user.id)
        print(f"✅ Retrieved preferences: {user_prefs.preferred_job_titles}")
        
        # Test 9: Test user skills retrieval
        print("\n🛠️ Testing skills retrieval...")
        user_skills = await user_profile_service.get_user_skills(user.id)
        print(f"✅ Retrieved {len(user_skills)} user skills")
        for skill in user_skills:
            print(f"   - {skill.skill.name if skill.skill else 'Unknown'}: {skill.proficiency_level}")
        
        # Test 10: Test work experience retrieval
        print("\n💼 Testing work experience retrieval...")
        work_experience = await user_profile_service.get_user_work_experience(user.id)
        print(f"✅ Retrieved {len(work_experience)} work experience entries")
        
        # Test 11: Test education retrieval
        print("\n🎓 Testing education retrieval...")
        education_list = await user_profile_service.get_user_education(user.id)
        print(f"✅ Retrieved {len(education_list)} education entries")
        
        print("\n🎉 All User Profile Module tests passed successfully!")
        print(f"📊 Summary:")
        print(f"   - User created: {user.id}")
        print(f"   - Skills added: {len(user_skills)}")
        print(f"   - Work experience: {len(work_experience)}")
        print(f"   - Education: {len(education_list)}")
        print(f"   - Preferences: {'Set' if user_prefs else 'Not set'}")
        
        return user.id
        
    except Exception as e:
        print(f"❌ Error testing user profile: {e}")
        logger.error(f"User profile test failed: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    asyncio.run(test_user_profile()) 