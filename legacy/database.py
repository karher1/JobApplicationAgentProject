#!/usr/bin/env python3
"""
Database module for Job Application Agent

Handles user authentication, profile storage, and job search data.
"""

from sqlalchemy import create_engine, Column, Integer, String, Text, DateTime, Boolean, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.sql import func
from werkzeug.security import generate_password_hash, check_password_hash
import os
from datetime import datetime
from typing import Optional, List, Dict, Any
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Database configuration
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///job_agent.db")
engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

class User(Base):
    """User model for authentication and profile management"""
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100), nullable=True)
    last_name = Column(String(100), nullable=True)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    profile = relationship("UserProfile", back_populates="user", uselist=False)
    job_searches = relationship("JobSearch", back_populates="user")
    applications = relationship("JobApplication", back_populates="user")

class UserProfile(Base):
    """User profile with resume, skills, and preferences"""
    __tablename__ = "user_profiles"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    resume_text = Column(Text, nullable=True)
    resume_file_path = Column(String(500), nullable=True)
    skills = Column(JSON, default=list)  # List of skills
    work_history = Column(JSON, default=list)  # List of work experience
    education = Column(JSON, default=list)  # List of education
    preferences = Column(JSON, default=dict)  # Job preferences
    linkedin_url = Column(String(500), nullable=True)
    portfolio_url = Column(String(500), nullable=True)
    phone = Column(String(20), nullable=True)
    location = Column(String(200), nullable=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="profile")

class JobSearch(Base):
    """Job search history and preferences"""
    __tablename__ = "job_searches"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    search_name = Column(String(200), nullable=False)
    job_titles = Column(JSON, default=list)  # List of job titles to search for
    locations = Column(JSON, default=list)  # List of preferred locations
    keywords = Column(JSON, default=list)  # Required keywords
    excluded_keywords = Column(JSON, default=list)  # Keywords to exclude
    remote_only = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())
    
    # Relationships
    user = relationship("User", back_populates="job_searches")
    search_results = relationship("JobSearchResult", back_populates="job_search")

class JobSearchResult(Base):
    """Results from job searches"""
    __tablename__ = "job_search_results"
    
    id = Column(Integer, primary_key=True, index=True)
    job_search_id = Column(Integer, nullable=False)
    job_title = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False)
    location = Column(String(200), nullable=False)
    url = Column(String(500), nullable=False)
    job_board = Column(String(100), default="Ashby")
    posted_date = Column(String(100), nullable=True)
    salary_range = Column(String(200), nullable=True)
    job_type = Column(String(100), nullable=True)
    remote_option = Column(String(100), nullable=True)
    description_snippet = Column(Text, nullable=True)
    is_applied = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())
    
    # Relationships
    job_search = relationship("JobSearch", back_populates="search_results")
    applications = relationship("JobApplication", back_populates="job_result")

class JobApplication(Base):
    """Job application tracking"""
    __tablename__ = "job_applications"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, nullable=False)
    job_result_id = Column(Integer, nullable=True)
    job_url = Column(String(500), nullable=False)
    job_title = Column(String(200), nullable=False)
    company = Column(String(200), nullable=False)
    application_date = Column(DateTime, default=func.now())
    status = Column(String(50), default="applied")  # applied, interviewed, rejected, accepted
    notes = Column(Text, nullable=True)
    success = Column(Boolean, default=False)
    filled_fields = Column(JSON, default=list)
    failed_fields = Column(JSON, default=list)
    error_message = Column(Text, nullable=True)
    
    # Relationships
    user = relationship("User", back_populates="applications")
    job_result = relationship("JobSearchResult", back_populates="applications")

# Database operations
class DatabaseManager:
    """Database manager for handling all database operations"""
    
    def __init__(self):
        self.engine = engine
        self.SessionLocal = SessionLocal
    
    def create_tables(self):
        """Create all database tables"""
        Base.metadata.create_all(bind=self.engine)
        logger.info("Database tables created successfully")
    
    def get_session(self):
        """Get database session"""
        return self.SessionLocal()
    
    def close_session(self, session):
        """Close database session"""
        session.close()

class UserManager:
    """User management operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_user(self, email: str, username: str, password: str, 
                   first_name: str = None, last_name: str = None) -> Optional[User]:
        """Create a new user"""
        session = self.db_manager.get_session()
        try:
            # Check if user already exists
            existing_user = session.query(User).filter(
                (User.email == email) | (User.username == username)
            ).first()
            
            if existing_user:
                logger.warning(f"User with email {email} or username {username} already exists")
                return None
            
            # Create new user
            password_hash = generate_password_hash(password)
            user = User(
                email=email,
                username=username,
                password_hash=password_hash,
                first_name=first_name,
                last_name=last_name
            )
            
            session.add(user)
            session.commit()
            session.refresh(user)
            
            logger.info(f"User {username} created successfully")
            return user
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating user: {e}")
            return None
        finally:
            self.db_manager.close_session(session)
    
    def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate user with email and password"""
        session = self.db_manager.get_session()
        try:
            user = session.query(User).filter(User.email == email).first()
            
            if user and check_password_hash(user.password_hash, password):
                logger.info(f"User {user.username} authenticated successfully")
                return user
            
            logger.warning(f"Authentication failed for email: {email}")
            return None
            
        except Exception as e:
            logger.error(f"Error authenticating user: {e}")
            return None
        finally:
            self.db_manager.close_session(session)
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        session = self.db_manager.get_session()
        try:
            return session.query(User).filter(User.id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting user by ID: {e}")
            return None
        finally:
            self.db_manager.close_session(session)
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        session = self.db_manager.get_session()
        try:
            return session.query(User).filter(User.email == email).first()
        except Exception as e:
            logger.error(f"Error getting user by email: {e}")
            return None
        finally:
            self.db_manager.close_session(session)

class ProfileManager:
    """User profile management operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_profile(self, user_id: int, **profile_data) -> Optional[UserProfile]:
        """Create or update user profile"""
        session = self.db_manager.get_session()
        try:
            # Check if profile exists
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if profile:
                # Update existing profile
                for key, value in profile_data.items():
                    if hasattr(profile, key):
                        setattr(profile, key, value)
                profile.updated_at = datetime.now()
            else:
                # Create new profile
                profile = UserProfile(user_id=user_id, **profile_data)
                session.add(profile)
            
            session.commit()
            session.refresh(profile)
            
            logger.info(f"Profile updated for user {user_id}")
            return profile
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating/updating profile: {e}")
            return None
        finally:
            self.db_manager.close_session(session)
    
    def get_profile(self, user_id: int) -> Optional[UserProfile]:
        """Get user profile"""
        session = self.db_manager.get_session()
        try:
            return session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
        except Exception as e:
            logger.error(f"Error getting profile: {e}")
            return None
        finally:
            self.db_manager.close_session(session)
    
    def update_resume(self, user_id: int, resume_text: str, resume_file_path: str = None) -> bool:
        """Update user's resume"""
        session = self.db_manager.get_session()
        try:
            profile = session.query(UserProfile).filter(UserProfile.user_id == user_id).first()
            
            if not profile:
                profile = UserProfile(user_id=user_id)
                session.add(profile)
            
            profile.resume_text = resume_text
            if resume_file_path:
                profile.resume_file_path = resume_file_path
            profile.updated_at = datetime.now()
            
            session.commit()
            logger.info(f"Resume updated for user {user_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error updating resume: {e}")
            return False
        finally:
            self.db_manager.close_session(session)

class JobSearchManager:
    """Job search management operations"""
    
    def __init__(self, db_manager: DatabaseManager):
        self.db_manager = db_manager
    
    def create_job_search(self, user_id: int, search_name: str, job_titles: List[str],
                         locations: List[str] = None, keywords: List[str] = None,
                         excluded_keywords: List[str] = None, remote_only: bool = False) -> Optional[JobSearch]:
        """Create a new job search"""
        session = self.db_manager.get_session()
        try:
            job_search = JobSearch(
                user_id=user_id,
                search_name=search_name,
                job_titles=job_titles,
                locations=locations or [],
                keywords=keywords or [],
                excluded_keywords=excluded_keywords or [],
                remote_only=remote_only
            )
            
            session.add(job_search)
            session.commit()
            session.refresh(job_search)
            
            logger.info(f"Job search '{search_name}' created for user {user_id}")
            return job_search
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error creating job search: {e}")
            return None
        finally:
            self.db_manager.close_session(session)
    
    def get_user_searches(self, user_id: int) -> List[JobSearch]:
        """Get all job searches for a user"""
        session = self.db_manager.get_session()
        try:
            return session.query(JobSearch).filter(
                JobSearch.user_id == user_id,
                JobSearch.is_active == True
            ).all()
        except Exception as e:
            logger.error(f"Error getting user searches: {e}")
            return []
        finally:
            self.db_manager.close_session(session)
    
    def save_search_results(self, job_search_id: int, results: List[Dict[str, Any]]) -> bool:
        """Save job search results to database"""
        session = self.db_manager.get_session()
        try:
            for result_data in results:
                job_result = JobSearchResult(
                    job_search_id=job_search_id,
                    job_title=result_data.get('title', ''),
                    company=result_data.get('company', ''),
                    location=result_data.get('location', ''),
                    url=result_data.get('url', ''),
                    job_board=result_data.get('job_board', 'Ashby'),
                    posted_date=result_data.get('posted_date'),
                    salary_range=result_data.get('salary_range'),
                    job_type=result_data.get('job_type'),
                    remote_option=result_data.get('remote_option'),
                    description_snippet=result_data.get('description_snippet')
                )
                session.add(job_result)
            
            session.commit()
            logger.info(f"Saved {len(results)} search results for job search {job_search_id}")
            return True
            
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving search results: {e}")
            return False
        finally:
            self.db_manager.close_session(session)
    
    def get_search_results(self, job_search_id: int) -> List[JobSearchResult]:
        """Get search results for a job search"""
        session = self.db_manager.get_session()
        try:
            return session.query(JobSearchResult).filter(
                JobSearchResult.job_search_id == job_search_id
            ).all()
        except Exception as e:
            logger.error(f"Error getting search results: {e}")
            return []
        finally:
            self.db_manager.close_session(session)

# Initialize database
def init_database():
    """Initialize the database"""
    db_manager = DatabaseManager()
    db_manager.create_tables()
    return db_manager

# Global database manager instance
db_manager = init_database()
user_manager = UserManager(db_manager)
profile_manager = ProfileManager(db_manager)
job_search_manager = JobSearchManager(db_manager) 