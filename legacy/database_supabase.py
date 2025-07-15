#!/usr/bin/env python3
"""
Supabase Database Module for Job Application Agent

This module provides database operations using Supabase as the backend.
It replaces the SQLAlchemy implementation with Supabase client.
"""

import os
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from supabase import create_client, Client
except ImportError:
    logger.error("Supabase client not installed. Run: pip install supabase")
    raise

class SupabaseManager:
    """Supabase database manager"""
    
    def __init__(self):
        self.supabase_url = os.getenv("SUPABASE_URL")
        self.supabase_key = os.getenv("SUPABASE_KEY")
        
        if not self.supabase_url or not self.supabase_key:
            raise ValueError("SUPABASE_URL and SUPABASE_KEY must be set in environment variables")
        
        # Create client without proxy argument
        self.client: Client = create_client(self.supabase_url, self.supabase_key)
        logger.info("Supabase client initialized successfully")
    
    def test_connection(self) -> bool:
        """Test the Supabase connection"""
        try:
            # Try a simple query to test connection
            result = self.client.table('users').select('id').limit(1).execute()
            logger.info("Supabase connection test successful")
            return True
        except Exception as e:
            logger.error(f"Supabase connection test failed: {e}")
            return False

class UserManager:
    """User management operations with Supabase"""
    
    def __init__(self, supabase_manager: SupabaseManager):
        self.supabase = supabase_manager.client
    
    def create_user(self, email: str, username: str, password: str, 
                   first_name: str = None, last_name: str = None) -> Optional[Dict[str, Any]]:
        """Create a new user"""
        try:
            # Check if user already exists
            existing_user = self.supabase.table('users').select('*').eq('email', email).execute()
            if existing_user.data:
                logger.warning(f"User with email {email} already exists")
                return None
            
            existing_username = self.supabase.table('users').select('*').eq('username', username).execute()
            if existing_username.data:
                logger.warning(f"User with username {username} already exists")
                return None
            
            # Hash password (you might want to use a proper hashing library)
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Create user
            user_data = {
                'email': email,
                'username': username,
                'password_hash': password_hash,
                'first_name': first_name,
                'last_name': last_name,
                'is_active': True
            }
            
            result = self.supabase.table('users').insert(user_data).execute()
            
            if result.data:
                user = result.data[0]
                logger.info(f"User {username} created successfully")
                return user
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating user: {e}")
            return None
    
    def authenticate_user(self, email: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticate user with email and password"""
        try:
            # Hash password for comparison
            import hashlib
            password_hash = hashlib.sha256(password.encode()).hexdigest()
            
            # Find user
            result = self.supabase.table('users').select('*').eq('email', email).eq('password_hash', password_hash).execute()
            
            if result.data:
                user = result.data[0]
                logger.info(f"User {user['username']} authenticated successfully")
                return user
            
            logger.warning(f"Authentication failed for email: {email}")
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
    
    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        try:
            result = self.supabase.table('users').select('*').eq('id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
    
    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email"""
        try:
            result = self.supabase.table('users').select('*').eq('email', email).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None

class ProfileManager:
    """User profile management operations with Supabase"""
    
    def __init__(self, supabase_manager: SupabaseManager):
        self.supabase = supabase_manager.client
    
    def create_profile(self, user_id: int, **profile_data) -> Optional[Dict[str, Any]]:
        """Create or update user profile"""
        try:
            # Check if profile exists
            existing_profile = self.supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
            
            if existing_profile.data:
                # Update existing profile
                profile_id = existing_profile.data[0]['id']
                result = self.supabase.table('user_profiles').update(profile_data).eq('id', profile_id).execute()
            else:
                # Create new profile
                profile_data['user_id'] = user_id
                result = self.supabase.table('user_profiles').insert(profile_data).execute()
            
            if result.data:
                profile = result.data[0]
                logger.info(f"Profile updated for user {user_id}")
                return profile
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating/updating profile: {e}")
            return None
    
    def get_profile(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user profile"""
        try:
            result = self.supabase.table('user_profiles').select('*').eq('user_id', user_id).execute()
            return result.data[0] if result.data else None
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None
    
    def update_resume(self, user_id: int, resume_text: str, resume_file_path: str = None) -> bool:
        """Update user's resume"""
        try:
            update_data = {'resume_text': resume_text}
            if resume_file_path:
                update_data['resume_file_path'] = resume_file_path
            
            result = self.supabase.table('user_profiles').update(update_data).eq('user_id', user_id).execute()
            
            if result.data:
                logger.info(f"Resume updated for user {user_id}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating resume: {e}")
            return False

class JobSearchManager:
    """Job search management operations with Supabase"""
    
    def __init__(self, supabase_manager: SupabaseManager):
        self.supabase = supabase_manager.client
    
    def create_job_search(self, user_id: int, search_name: str, job_titles: List[str],
                         locations: List[str] = None, keywords: List[str] = None,
                         excluded_keywords: List[str] = None, remote_only: bool = False) -> Optional[Dict[str, Any]]:
        """Create a new job search"""
        try:
            job_search_data = {
                'user_id': user_id,
                'search_name': search_name,
                'job_titles': job_titles,
                'locations': locations or [],
                'keywords': keywords or [],
                'excluded_keywords': excluded_keywords or [],
                'remote_only': remote_only,
                'is_active': True
            }
            
            result = self.supabase.table('job_searches').insert(job_search_data).execute()
            
            if result.data:
                job_search = result.data[0]
                logger.info(f"Job search '{search_name}' created for user {user_id}")
                return job_search
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating job search: {e}")
            return None
    
    def get_user_searches(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all job searches for a user"""
        try:
            result = self.supabase.table('job_searches').select('*').eq('user_id', user_id).eq('is_active', True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting user searches: {e}")
            return []
    
    def save_search_results(self, job_search_id: int, results: List[Dict[str, Any]]) -> bool:
        """Save job search results to database"""
        try:
            # Prepare results data
            results_data = []
            for result_data in results:
                job_result = {
                    'job_search_id': job_search_id,
                    'job_title': result_data.get('title', ''),
                    'company': result_data.get('company', ''),
                    'location': result_data.get('location', ''),
                    'url': result_data.get('url', ''),
                    'job_board': result_data.get('job_board', 'Ashby'),
                    'posted_date': result_data.get('posted_date'),
                    'salary_range': result_data.get('salary_range'),
                    'job_type': result_data.get('job_type'),
                    'remote_option': result_data.get('remote_option'),
                    'description_snippet': result_data.get('description_snippet')
                }
                results_data.append(job_result)
            
            if results_data:
                result = self.supabase.table('job_search_results').insert(results_data).execute()
                if result.data:
                    logger.info(f"Saved {len(results_data)} search results for job search {job_search_id}")
                    return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error saving search results: {e}")
            return False
    
    def get_search_results(self, job_search_id: int) -> List[Dict[str, Any]]:
        """Get search results for a job search"""
        try:
            result = self.supabase.table('job_search_results').select('*').eq('job_search_id', job_search_id).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting search results: {e}")
            return []

class JobApplicationManager:
    """Job application tracking with Supabase"""
    
    def __init__(self, supabase_manager: SupabaseManager):
        self.supabase = supabase_manager.client
    
    def create_application(self, user_id: int, job_url: str, job_title: str, company: str,
                          job_result_id: int = None, status: str = 'applied') -> Optional[Dict[str, Any]]:
        """Create a new job application record"""
        try:
            application_data = {
                'user_id': user_id,
                'job_url': job_url,
                'job_title': job_title,
                'company': company,
                'job_result_id': job_result_id,
                'status': status,
                'success': False
            }
            
            result = self.supabase.table('job_applications').insert(application_data).execute()
            
            if result.data:
                application = result.data[0]
                logger.info(f"Job application created for {job_title} at {company}")
                return application
            
            return None
            
        except Exception as e:
            logger.error(f"Error creating job application: {e}")
            return None
    
    def update_application_status(self, application_id: int, status: str, success: bool = None,
                                 filled_fields: List[str] = None, failed_fields: List[str] = None,
                                 error_message: str = None) -> bool:
        """Update job application status"""
        try:
            update_data = {'status': status}
            if success is not None:
                update_data['success'] = success
            if filled_fields is not None:
                update_data['filled_fields'] = filled_fields
            if failed_fields is not None:
                update_data['failed_fields'] = failed_fields
            if error_message is not None:
                update_data['error_message'] = error_message
            
            result = self.supabase.table('job_applications').update(update_data).eq('id', application_id).execute()
            
            if result.data:
                logger.info(f"Application {application_id} status updated to {status}")
                return True
            
            return False
            
        except Exception as e:
            logger.error(f"Error updating application status: {e}")
            return False
    
    def get_user_applications(self, user_id: int) -> List[Dict[str, Any]]:
        """Get all job applications for a user"""
        try:
            result = self.supabase.table('job_applications').select('*').eq('user_id', user_id).order('application_date', desc=True).execute()
            return result.data or []
        except Exception as e:
            logger.error(f"Error getting user applications: {e}")
            return []

# Initialize Supabase
def init_supabase():
    """Initialize Supabase connection"""
    try:
        supabase_manager = SupabaseManager()
        if supabase_manager.test_connection():
            return supabase_manager
        else:
            raise Exception("Failed to connect to Supabase")
    except Exception as e:
        logger.error(f"Failed to initialize Supabase: {e}")
        raise

# Global Supabase manager instance
try:
    supabase_manager = init_supabase()
    user_manager = UserManager(supabase_manager)
    profile_manager = ProfileManager(supabase_manager)
    job_search_manager = JobSearchManager(supabase_manager)
    job_application_manager = JobApplicationManager(supabase_manager)
except Exception as e:
    logger.error(f"Failed to initialize Supabase managers: {e}")
    # Fallback to None for graceful degradation
    supabase_manager = None
    user_manager = None
    profile_manager = None
    job_search_manager = None
    job_application_manager = None 