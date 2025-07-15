#!/usr/bin/env python3
"""
User Interface for Job Application Agent

Provides a command-line interface for user authentication, profile management,
and job searching with the Ashby job search agent.
"""

import os
import sys
import getpass
from typing import List, Dict, Any, Optional
import logging

# Import our modules
from database import user_manager, profile_manager, job_search_manager
from ashby_job_search import AshbyJobSearchAgent

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class JobAgentUI:
    """User interface for the job application agent"""
    
    def __init__(self):
        self.current_user = None
        self.ashby_agent = AshbyJobSearchAgent()
        
    def main_menu(self):
        """Main application menu"""
        while True:
            print("\n" + "="*60)
            print("🤖 Job Application Agent")
            print("="*60)
            
            if self.current_user:
                print(f"👤 Welcome, {self.current_user.username}!")
                print("\nChoose an option:")
                print("1. View Profile")
                print("2. Update Profile")
                print("3. Search Jobs")
                print("4. View Job Searches")
                print("5. View Job Results")
                print("6. Logout")
                print("7. Exit")
                
                choice = input("\nEnter your choice (1-7): ").strip()
                
                if choice == '1':
                    self.view_profile()
                elif choice == '2':
                    self.update_profile()
                elif choice == '3':
                    self.search_jobs()
                elif choice == '4':
                    self.view_job_searches()
                elif choice == '5':
                    self.view_job_results()
                elif choice == '6':
                    self.logout()
                elif choice == '7':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please try again.")
            else:
                print("\nChoose an option:")
                print("1. Login")
                print("2. Sign Up")
                print("3. Exit")
                
                choice = input("\nEnter your choice (1-3): ").strip()
                
                if choice == '1':
                    self.login()
                elif choice == '2':
                    self.signup()
                elif choice == '3':
                    print("👋 Goodbye!")
                    break
                else:
                    print("❌ Invalid choice. Please try again.")
    
    def signup(self):
        """User registration"""
        print("\n" + "="*40)
        print("📝 User Registration")
        print("="*40)
        
        try:
            email = input("Email: ").strip()
            if not email or '@' not in email:
                print("❌ Please enter a valid email address.")
                return
            
            username = input("Username: ").strip()
            if not username:
                print("❌ Username is required.")
                return
            
            password = getpass.getpass("Password: ")
            if len(password) < 6:
                print("❌ Password must be at least 6 characters long.")
                return
            
            confirm_password = getpass.getpass("Confirm Password: ")
            if password != confirm_password:
                print("❌ Passwords do not match.")
                return
            
            first_name = input("First Name (optional): ").strip()
            last_name = input("Last Name (optional): ").strip()
            
            # Create user
            user = user_manager.create_user(
                email=email,
                username=username,
                password=password,
                first_name=first_name or None,
                last_name=last_name or None
            )
            
            if user:
                print("✅ User created successfully!")
                self.current_user = user
                
                # Create initial profile
                self.create_initial_profile()
            else:
                print("❌ Failed to create user. Email or username may already exist.")
                
        except KeyboardInterrupt:
            print("\n❌ Registration cancelled.")
        except Exception as e:
            print(f"❌ Error during registration: {e}")
    
    def login(self):
        """User login"""
        print("\n" + "="*40)
        print("🔐 User Login")
        print("="*40)
        
        try:
            email = input("Email: ").strip()
            password = getpass.getpass("Password: ")
            
            user = user_manager.authenticate_user(email, password)
            
            if user:
                print("✅ Login successful!")
                self.current_user = user
            else:
                print("❌ Invalid email or password.")
                
        except KeyboardInterrupt:
            print("\n❌ Login cancelled.")
        except Exception as e:
            print(f"❌ Error during login: {e}")
    
    def logout(self):
        """User logout"""
        self.current_user = None
        print("✅ Logged out successfully!")
    
    def create_initial_profile(self):
        """Create initial user profile"""
        print("\n" + "="*40)
        print("📋 Create Your Profile")
        print("="*40)
        
        try:
            # Get basic profile information
            phone = input("Phone (optional): ").strip()
            location = input("Location (optional): ").strip()
            linkedin_url = input("LinkedIn URL (optional): ").strip()
            portfolio_url = input("Portfolio URL (optional): ").strip()
            
            # Get skills
            print("\nEnter your skills (comma-separated):")
            skills_input = input("Skills: ").strip()
            skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
            
            # Create profile
            profile_data = {
                'phone': phone or None,
                'location': location or None,
                'linkedin_url': linkedin_url or None,
                'portfolio_url': portfolio_url or None,
                'skills': skills
            }
            
            profile = profile_manager.create_profile(self.current_user.id, **profile_data)
            
            if profile:
                print("✅ Profile created successfully!")
            else:
                print("❌ Failed to create profile.")
                
        except KeyboardInterrupt:
            print("\n❌ Profile creation cancelled.")
        except Exception as e:
            print(f"❌ Error creating profile: {e}")
    
    def view_profile(self):
        """View user profile"""
        print("\n" + "="*40)
        print("👤 User Profile")
        print("="*40)
        
        try:
            profile = profile_manager.get_profile(self.current_user.id)
            
            if profile:
                print(f"Name: {self.current_user.first_name or ''} {self.current_user.last_name or ''}")
                print(f"Email: {self.current_user.email}")
                print(f"Username: {self.current_user.username}")
                print(f"Phone: {profile.phone or 'Not set'}")
                print(f"Location: {profile.location or 'Not set'}")
                print(f"LinkedIn: {profile.linkedin_url or 'Not set'}")
                print(f"Portfolio: {profile.portfolio_url or 'Not set'}")
                print(f"Skills: {', '.join(profile.skills) if profile.skills else 'Not set'}")
                print(f"Resume: {'Uploaded' if profile.resume_text else 'Not uploaded'}")
            else:
                print("❌ Profile not found.")
                
        except Exception as e:
            print(f"❌ Error viewing profile: {e}")
    
    def update_profile(self):
        """Update user profile"""
        print("\n" + "="*40)
        print("✏️ Update Profile")
        print("="*40)
        
        try:
            profile = profile_manager.get_profile(self.current_user.id)
            
            # Get updated information
            phone = input(f"Phone ({profile.phone if profile and profile.phone else 'Not set'}): ").strip()
            location = input(f"Location ({profile.location if profile and profile.location else 'Not set'}): ").strip()
            linkedin_url = input(f"LinkedIn URL ({profile.linkedin_url if profile and profile.linkedin_url else 'Not set'}): ").strip()
            portfolio_url = input(f"Portfolio URL ({profile.portfolio_url if profile and profile.portfolio_url else 'Not set'}): ").strip()
            
            # Get skills
            current_skills = ', '.join(profile.skills) if profile and profile.skills else ''
            print(f"Current skills: {current_skills}")
            skills_input = input("New skills (comma-separated, press Enter to keep current): ").strip()
            
            if skills_input:
                skills = [skill.strip() for skill in skills_input.split(',') if skill.strip()]
            else:
                skills = profile.skills if profile else []
            
            # Update profile
            profile_data = {
                'phone': phone if phone else (profile.phone if profile else None),
                'location': location if location else (profile.location if profile else None),
                'linkedin_url': linkedin_url if linkedin_url else (profile.linkedin_url if profile else None),
                'portfolio_url': portfolio_url if portfolio_url else (profile.portfolio_url if profile else None),
                'skills': skills
            }
            
            updated_profile = profile_manager.create_profile(self.current_user.id, **profile_data)
            
            if updated_profile:
                print("✅ Profile updated successfully!")
            else:
                print("❌ Failed to update profile.")
                
        except KeyboardInterrupt:
            print("\n❌ Profile update cancelled.")
        except Exception as e:
            print(f"❌ Error updating profile: {e}")
    
    def search_jobs(self):
        """Search for jobs"""
        print("\n" + "="*40)
        print("🔍 Job Search")
        print("="*40)
        
        try:
            # Get search parameters
            search_name = input("Search name: ").strip()
            if not search_name:
                print("❌ Search name is required.")
                return
            
            # Job titles
            print("\nAvailable job titles:")
            default_titles = ["QA Engineer", "Senior QA Engineer", "QA Automation Engineer"]
            for i, title in enumerate(default_titles, 1):
                print(f"{i}. {title}")
            print("4. Custom titles")
            
            title_choice = input("\nChoose job titles (1-4, comma-separated): ").strip()
            
            if title_choice == '4':
                custom_titles = input("Enter custom job titles (comma-separated): ").strip()
                job_titles = [title.strip() for title in custom_titles.split(',') if title.strip()]
            else:
                choices = [int(c.strip()) for c in title_choice.split(',') if c.strip().isdigit()]
                job_titles = [default_titles[i-1] for i in choices if 1 <= i <= 3]
            
            if not job_titles:
                print("❌ No job titles selected.")
                return
            
            # Locations
            locations_input = input("Preferred locations (comma-separated, optional): ").strip()
            locations = [loc.strip() for loc in locations_input.split(',') if loc.strip()]
            
            # Keywords
            keywords_input = input("Required keywords (comma-separated, optional): ").strip()
            keywords = [kw.strip() for kw in keywords_input.split(',') if kw.strip()]
            
            # Excluded keywords
            excluded_input = input("Excluded keywords (comma-separated, optional): ").strip()
            excluded_keywords = [kw.strip() for kw in excluded_input.split(',') if kw.strip()]
            
            # Remote only
            remote_only = input("Remote only? (y/n): ").strip().lower() == 'y'
            
            # Max results
            max_results_input = input("Maximum results (default 50): ").strip()
            max_results = int(max_results_input) if max_results_input.isdigit() else 50
            
            print(f"\n🔍 Searching for {', '.join(job_titles)} positions...")
            
            # Create job search in database
            job_search = job_search_manager.create_job_search(
                user_id=self.current_user.id,
                search_name=search_name,
                job_titles=job_titles,
                locations=locations,
                keywords=keywords,
                excluded_keywords=excluded_keywords,
                remote_only=remote_only
            )
            
            if not job_search:
                print("❌ Failed to create job search.")
                return
            
            # Perform the search
            jobs = self.ashby_agent.search_qa_jobs(job_titles=job_titles, max_results=max_results)
            
            if jobs:
                # Save results to database
                job_search_manager.save_search_results(job_search.id, jobs)
                
                print(f"\n✅ Found {len(jobs)} jobs!")
                print("\nJob Results:")
                for i, job in enumerate(jobs[:10], 1):  # Show first 10
                    print(f"{i}. {job['title']} at {job['company']}")
                    print(f"   Location: {job['location']}")
                    print(f"   URL: {job['url']}")
                    print()
                
                if len(jobs) > 10:
                    print(f"... and {len(jobs) - 10} more jobs")
            else:
                print("❌ No jobs found matching your criteria.")
                
        except KeyboardInterrupt:
            print("\n❌ Job search cancelled.")
        except Exception as e:
            print(f"❌ Error during job search: {e}")
    
    def view_job_searches(self):
        """View user's job searches"""
        print("\n" + "="*40)
        print("📋 Job Searches")
        print("="*40)
        
        try:
            searches = job_search_manager.get_user_searches(self.current_user.id)
            
            if searches:
                for i, search in enumerate(searches, 1):
                    print(f"{i}. {search.search_name}")
                    print(f"   Job titles: {', '.join(search.job_titles)}")
                    print(f"   Locations: {', '.join(search.locations) if search.locations else 'Any'}")
                    print(f"   Remote only: {'Yes' if search.remote_only else 'No'}")
                    print(f"   Created: {search.created_at.strftime('%Y-%m-%d %H:%M')}")
                    print()
            else:
                print("No job searches found.")
                
        except Exception as e:
            print(f"❌ Error viewing job searches: {e}")
    
    def view_job_results(self):
        """View job search results"""
        print("\n" + "="*40)
        print("📊 Job Results")
        print("="*40)
        
        try:
            searches = job_search_manager.get_user_searches(self.current_user.id)
            
            if not searches:
                print("No job searches found.")
                return
            
            print("Select a job search:")
            for i, search in enumerate(searches, 1):
                print(f"{i}. {search.search_name}")
            
            choice = input("\nEnter search number: ").strip()
            
            if not choice.isdigit() or int(choice) < 1 or int(choice) > len(searches):
                print("❌ Invalid choice.")
                return
            
            selected_search = searches[int(choice) - 1]
            results = job_search_manager.get_search_results(selected_search.id)
            
            if results:
                print(f"\nResults for '{selected_search.search_name}':")
                print(f"Total jobs: {len(results)}")
                print()
                
                for i, result in enumerate(results[:20], 1):  # Show first 20
                    print(f"{i}. {result.job_title} at {result.company}")
                    print(f"   Location: {result.location}")
                    print(f"   URL: {result.url}")
                    print(f"   Applied: {'Yes' if result.is_applied else 'No'}")
                    print(f"   Favorite: {'Yes' if result.is_favorite else 'No'}")
                    print()
                
                if len(results) > 20:
                    print(f"... and {len(results) - 20} more jobs")
            else:
                print("No results found for this search.")
                
        except Exception as e:
            print(f"❌ Error viewing job results: {e}")

def main():
    """Main function"""
    ui = JobAgentUI()
    ui.main_menu()

if __name__ == "__main__":
    main() 