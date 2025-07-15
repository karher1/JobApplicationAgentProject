#!/usr/bin/env python3
"""
User Interface for Job Application Agent with Supabase

This module provides a command-line interface for the job application agent
using Supabase as the database backend.
"""

import os
import sys
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
    from database_supabase import (
        user_manager, profile_manager, job_search_manager, 
        job_application_manager, supabase_manager
    )
    from ashby_job_search import AshbyJobSearch
except ImportError as e:
    logger.error(f"Failed to import required modules: {e}")
    sys.exit(1)

class UserInterface:
    """Command-line user interface for the job application agent"""
    
    def __init__(self):
        self.current_user = None
        self.ashby_searcher = AshbyJobSearch()
        
        # Check if Supabase is available
        if not supabase_manager:
            print("❌ Supabase connection not available!")
            print("Please check your .env file and run the setup script.")
            sys.exit(1)
    
    def display_welcome(self):
        """Display welcome message"""
        print("\n" + "=" * 60)
        print("🚀 Job Application Agent - Supabase Edition")
        print("=" * 60)
        print("Welcome to the AI-powered job application automation system!")
        print("This system helps you search for QA jobs and automate applications.")
        print("=" * 60)
    
    def display_main_menu(self):
        """Display main menu options"""
        print("\n📋 Main Menu:")
        print("1. Login")
        print("2. Sign Up")
        print("3. Exit")
        
        if self.current_user:
            print("\n👤 Logged in as:", self.current_user['username'])
            print("\n4. Manage Profile")
            print("5. Create Job Search")
            print("6. View Job Searches")
            print("7. Search Jobs on Ashby")
            print("8. View Job Applications")
            print("9. Logout")
    
    def get_user_choice(self, min_choice: int, max_choice: int) -> int:
        """Get user choice with validation"""
        while True:
            try:
                choice = int(input(f"\nEnter your choice ({min_choice}-{max_choice}): "))
                if min_choice <= choice <= max_choice:
                    return choice
                else:
                    print(f"Please enter a number between {min_choice} and {max_choice}")
            except ValueError:
                print("Please enter a valid number")
    
    def login(self):
        """Handle user login"""
        print("\n🔐 Login")
        print("-" * 30)
        
        email = input("Email: ").strip()
        password = input("Password: ").strip()
        
        if not email or not password:
            print("❌ Email and password are required")
            return
        
        user = user_manager.authenticate_user(email, password)
        if user:
            self.current_user = user
            print(f"✅ Welcome back, {user['username']}!")
        else:
            print("❌ Invalid email or password")
    
    def signup(self):
        """Handle user signup"""
        print("\n📝 Sign Up")
        print("-" * 30)
        
        email = input("Email: ").strip()
        username = input("Username: ").strip()
        password = input("Password: ").strip()
        confirm_password = input("Confirm Password: ").strip()
        first_name = input("First Name (optional): ").strip()
        last_name = input("Last Name (optional): ").strip()
        
        if not email or not username or not password:
            print("❌ Email, username, and password are required")
            return
        
        if password != confirm_password:
            print("❌ Passwords do not match")
            return
        
        user = user_manager.create_user(
            email=email,
            username=username,
            password=password,
            first_name=first_name if first_name else None,
            last_name=last_name if last_name else None
        )
        
        if user:
            self.current_user = user
            print(f"✅ Account created successfully! Welcome, {username}!")
        else:
            print("❌ Failed to create account. Email or username may already exist.")
    
    def manage_profile(self):
        """Manage user profile"""
        if not self.current_user:
            print("❌ Please login first")
            return
        
        print("\n👤 Profile Management")
        print("-" * 30)
        
        # Get current profile
        current_profile = profile_manager.get_profile(self.current_user['id'])
        
        print("1. View Current Profile")
        print("2. Update Profile")
        print("3. Update Resume")
        print("4. Back to Main Menu")
        
        choice = self.get_user_choice(1, 4)
        
        if choice == 1:
            self.view_profile()
        elif choice == 2:
            self.update_profile()
        elif choice == 3:
            self.update_resume()
    
    def view_profile(self):
        """View current profile"""
        profile = profile_manager.get_profile(self.current_user['id'])
        
        if profile:
            print("\n📋 Current Profile:")
            print(f"Phone: {profile.get('phone', 'Not set')}")
            print(f"Location: {profile.get('location', 'Not set')}")
            print(f"LinkedIn: {profile.get('linkedin_url', 'Not set')}")
            print(f"Portfolio: {profile.get('portfolio_url', 'Not set')}")
            print(f"Skills: {', '.join(profile.get('skills', []))}")
            print(f"Resume: {'Set' if profile.get('resume_text') else 'Not set'}")
        else:
            print("❌ No profile found. Please create one first.")
    
    def update_profile(self):
        """Update user profile"""
        print("\n📝 Update Profile")
        print("-" * 30)
        
        phone = input("Phone (press Enter to skip): ").strip()
        location = input("Location (press Enter to skip): ").strip()
        linkedin_url = input("LinkedIn URL (press Enter to skip): ").strip()
        portfolio_url = input("Portfolio URL (press Enter to skip): ").strip()
        
        # Get skills
        print("\nEnter skills (comma-separated, press Enter to skip):")
        skills_input = input("Skills: ").strip()
        skills = [skill.strip() for skill in skills_input.split(',')] if skills_input else []
        
        # Prepare profile data
        profile_data = {}
        if phone:
            profile_data['phone'] = phone
        if location:
            profile_data['location'] = location
        if linkedin_url:
            profile_data['linkedin_url'] = linkedin_url
        if portfolio_url:
            profile_data['portfolio_url'] = portfolio_url
        if skills:
            profile_data['skills'] = skills
        
        if profile_data:
            profile = profile_manager.create_profile(self.current_user['id'], **profile_data)
            if profile:
                print("✅ Profile updated successfully!")
            else:
                print("❌ Failed to update profile")
        else:
            print("ℹ️ No changes made")
    
    def update_resume(self):
        """Update user resume"""
        print("\n📄 Update Resume")
        print("-" * 30)
        
        print("Enter your resume text (press Enter twice to finish):")
        lines = []
        while True:
            line = input()
            if line == "" and lines and lines[-1] == "":
                break
            lines.append(line)
        
        resume_text = '\n'.join(lines[:-1])  # Remove the last empty line
        
        if resume_text.strip():
            success = profile_manager.update_resume(self.current_user['id'], resume_text)
            if success:
                print("✅ Resume updated successfully!")
            else:
                print("❌ Failed to update resume")
        else:
            print("ℹ️ No resume text provided")
    
    def create_job_search(self):
        """Create a new job search"""
        if not self.current_user:
            print("❌ Please login first")
            return
        
        print("\n🔍 Create Job Search")
        print("-" * 30)
        
        search_name = input("Search Name: ").strip()
        if not search_name:
            print("❌ Search name is required")
            return
        
        # Get job titles
        print("\nEnter job titles (comma-separated):")
        job_titles_input = input("Job Titles: ").strip()
        job_titles = [title.strip() for title in job_titles_input.split(',')] if job_titles_input else []
        
        if not job_titles:
            print("❌ At least one job title is required")
            return
        
        # Get locations
        print("\nEnter locations (comma-separated, press Enter to skip):")
        locations_input = input("Locations: ").strip()
        locations = [loc.strip() for loc in locations_input.split(',')] if locations_input else []
        
        # Get keywords
        print("\nEnter keywords (comma-separated, press Enter to skip):")
        keywords_input = input("Keywords: ").strip()
        keywords = [kw.strip() for kw in keywords_input.split(',')] if keywords_input else []
        
        # Get excluded keywords
        print("\nEnter excluded keywords (comma-separated, press Enter to skip):")
        excluded_input = input("Excluded Keywords: ").strip()
        excluded_keywords = [kw.strip() for kw in excluded_input.split(',')] if excluded_input else []
        
        # Remote only option
        remote_only = input("Remote only? (y/n, default: n): ").strip().lower() == 'y'
        
        job_search = job_search_manager.create_job_search(
            user_id=self.current_user['id'],
            search_name=search_name,
            job_titles=job_titles,
            locations=locations,
            keywords=keywords,
            excluded_keywords=excluded_keywords,
            remote_only=remote_only
        )
        
        if job_search:
            print(f"✅ Job search '{search_name}' created successfully!")
        else:
            print("❌ Failed to create job search")
    
    def view_job_searches(self):
        """View user's job searches"""
        if not self.current_user:
            print("❌ Please login first")
            return
        
        print("\n🔍 Your Job Searches")
        print("-" * 30)
        
        searches = job_search_manager.get_user_searches(self.current_user['id'])
        
        if not searches:
            print("No job searches found. Create one first!")
            return
        
        for i, search in enumerate(searches, 1):
            print(f"\n{i}. {search['search_name']}")
            print(f"   Job Titles: {', '.join(search['job_titles'])}")
            print(f"   Locations: {', '.join(search['locations']) if search['locations'] else 'Any'}")
            print(f"   Keywords: {', '.join(search['keywords']) if search['keywords'] else 'None'}")
            print(f"   Remote Only: {'Yes' if search['remote_only'] else 'No'}")
            print(f"   Created: {search['created_at']}")
            
            # Show results count
            results = job_search_manager.get_search_results(search['id'])
            print(f"   Results: {len(results)} jobs found")
    
    def search_jobs_ashby(self):
        """Search jobs on Ashby"""
        if not self.current_user:
            print("❌ Please login first")
            return
        
        print("\n🔍 Search Jobs on Ashby")
        print("-" * 30)
        
        # Get user's job searches
        searches = job_search_manager.get_user_searches(self.current_user['id'])
        
        if not searches:
            print("No job searches found. Please create one first!")
            return
        
        # Let user choose a search
        print("Choose a job search to run:")
        for i, search in enumerate(searches, 1):
            print(f"{i}. {search['search_name']}")
        
        choice = self.get_user_choice(1, len(searches))
        selected_search = searches[choice - 1]
        
        print(f"\n🔍 Running search: {selected_search['search_name']}")
        print("This may take a few minutes...")
        
        try:
            # Run the search
            results = self.ashby_searcher.search_jobs(
                job_titles=selected_search['job_titles'],
                locations=selected_search['locations'],
                keywords=selected_search['keywords'],
                excluded_keywords=selected_search['excluded_keywords'],
                remote_only=selected_search['remote_only']
            )
            
            if results:
                print(f"\n✅ Found {len(results)} jobs!")
                
                # Save results to database
                success = job_search_manager.save_search_results(selected_search['id'], results)
                if success:
                    print("✅ Results saved to database")
                else:
                    print("⚠️ Failed to save results to database")
                
                # Display results
                for i, job in enumerate(results[:10], 1):  # Show first 10
                    print(f"\n{i}. {job['title']}")
                    print(f"   Company: {job['company']}")
                    print(f"   Location: {job['location']}")
                    print(f"   URL: {job['url']}")
                
                if len(results) > 10:
                    print(f"\n... and {len(results) - 10} more jobs")
            else:
                print("❌ No jobs found matching your criteria")
                
        except Exception as e:
            print(f"❌ Error searching jobs: {e}")
    
    def view_job_applications(self):
        """View user's job applications"""
        if not self.current_user:
            print("❌ Please login first")
            return
        
        print("\n📝 Your Job Applications")
        print("-" * 30)
        
        applications = job_application_manager.get_user_applications(self.current_user['id'])
        
        if not applications:
            print("No job applications found.")
            return
        
        for i, app in enumerate(applications, 1):
            print(f"\n{i}. {app['job_title']}")
            print(f"   Company: {app['company']}")
            print(f"   Status: {app['status']}")
            print(f"   Success: {'Yes' if app['success'] else 'No'}")
            print(f"   Applied: {app['application_date']}")
            if app['notes']:
                print(f"   Notes: {app['notes']}")
    
    def logout(self):
        """Logout current user"""
        if self.current_user:
            print(f"👋 Goodbye, {self.current_user['username']}!")
            self.current_user = None
        else:
            print("❌ No user logged in")
    
    def run(self):
        """Main application loop"""
        self.display_welcome()
        
        while True:
            self.display_main_menu()
            
            if self.current_user:
                max_choice = 9
            else:
                max_choice = 3
            
            choice = self.get_user_choice(1, max_choice)
            
            if choice == 1:
                self.login()
            elif choice == 2:
                self.signup()
            elif choice == 3:
                print("👋 Thank you for using Job Application Agent!")
                break
            elif self.current_user:
                if choice == 4:
                    self.manage_profile()
                elif choice == 5:
                    self.create_job_search()
                elif choice == 6:
                    self.view_job_searches()
                elif choice == 7:
                    self.search_jobs_ashby()
                elif choice == 8:
                    self.view_job_applications()
                elif choice == 9:
                    self.logout()

def main():
    """Main function"""
    try:
        ui = UserInterface()
        ui.run()
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    except Exception as e:
        logger.error(f"Application error: {e}")
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main() 