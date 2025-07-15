#!/usr/bin/env python3
"""
Test Script for Enhanced Job Application Agent

This script demonstrates the new features:
- User authentication and registration
- Profile management
- Ashby job search
- Database storage
"""

import sys
import os

# Add the current directory to Python path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_database_operations():
    """Test database operations"""
    print("🧪 Testing Database Operations")
    print("=" * 40)
    
    try:
        from database import user_manager, profile_manager, job_search_manager
        
        # Test user creation
        print("1. Testing user creation...")
        user = user_manager.create_user(
            email="test@example.com",
            username="testuser",
            password="testpass123",
            first_name="Test",
            last_name="User"
        )
        
        if user:
            print(f"✅ User created: {user.username}")
            
            # Test profile creation
            print("\n2. Testing profile creation...")
            profile = profile_manager.create_profile(
                user_id=user.id,
                phone="(555) 123-4567",
                location="San Francisco, CA",
                linkedin_url="https://linkedin.com/in/testuser",
                skills=["Python", "Selenium", "Testing", "Automation"]
            )
            
            if profile:
                print("✅ Profile created successfully")
                
                # Test job search creation
                print("\n3. Testing job search creation...")
                job_search = job_search_manager.create_job_search(
                    user_id=user.id,
                    search_name="QA Engineer Search",
                    job_titles=["QA Engineer", "Senior QA Engineer"],
                    locations=["Remote", "San Francisco"],
                    keywords=["automation", "selenium"],
                    remote_only=True
                )
                
                if job_search:
                    print("✅ Job search created successfully")
                    
                    # Test job search results
                    print("\n4. Testing job search results...")
                    test_results = [
                        {
                            'title': 'QA Engineer',
                            'company': 'Test Company',
                            'location': 'Remote',
                            'url': 'https://example.com/job1',
                            'job_board': 'Ashby'
                        },
                        {
                            'title': 'Senior QA Engineer',
                            'company': 'Another Company',
                            'location': 'San Francisco',
                            'url': 'https://example.com/job2',
                            'job_board': 'Ashby'
                        }
                    ]
                    
                    success = job_search_manager.save_search_results(job_search.id, test_results)
                    if success:
                        print("✅ Job search results saved successfully")
                        
                        # Retrieve results
                        results = job_search_manager.get_search_results(job_search.id)
                        print(f"✅ Retrieved {len(results)} job results")
                    else:
                        print("❌ Failed to save job search results")
                else:
                    print("❌ Failed to create job search")
            else:
                print("❌ Failed to create profile")
        else:
            print("❌ Failed to create user")
            
    except Exception as e:
        print(f"❌ Error testing database operations: {e}")

def test_ashby_job_search():
    """Test Ashby job search"""
    print("\n🔍 Testing Ashby Job Search")
    print("=" * 40)
    
    try:
        from ashby_job_search import AshbyJobSearchAgent
        
        agent = AshbyJobSearchAgent()
        
        # Test job search with limited results
        print("Searching for QA Engineer positions...")
        jobs = agent.search_qa_jobs(
            job_titles=["QA Engineer", "Senior QA Engineer"],
            max_results=5
        )
        
        if jobs:
            print(f"✅ Found {len(jobs)} QA jobs")
            print("\nSample jobs:")
            for i, job in enumerate(jobs[:3], 1):
                print(f"{i}. {job['title']} at {job['company']}")
                print(f"   Location: {job['location']}")
                print(f"   URL: {job['url']}")
                print()
        else:
            print("❌ No jobs found")
            
    except Exception as e:
        print(f"❌ Error testing Ashby job search: {e}")

def test_user_interface():
    """Test user interface components"""
    print("\n🖥️ Testing User Interface Components")
    print("=" * 40)
    
    try:
        from user_interface import JobAgentUI
        
        ui = JobAgentUI()
        
        # Test without user (should show login/signup options)
        print("1. Testing main menu without user...")
        print("   (This would normally show login/signup options)")
        
        # Test with a mock user
        print("\n2. Testing with mock user...")
        from database import user_manager
        
        # Create a test user if it doesn't exist
        test_user = user_manager.get_user_by_email("demo@example.com")
        if not test_user:
            test_user = user_manager.create_user(
                email="demo@example.com",
                username="demo",
                password="demopass123",
                first_name="Demo",
                last_name="User"
            )
        
        if test_user:
            ui.current_user = test_user
            print(f"   ✅ Mock user created: {test_user.username}")
            
            # Test profile viewing
            print("\n3. Testing profile viewing...")
            from database import profile_manager
            
            profile = profile_manager.get_profile(test_user.id)
            if profile:
                print(f"   ✅ Profile found with {len(profile.skills) if profile.skills else 0} skills")
            else:
                print("   ℹ️ No profile found (this is normal for new users)")
        else:
            print("   ❌ Failed to create mock user")
            
    except Exception as e:
        print(f"❌ Error testing user interface: {e}")

def test_integration():
    """Test the complete integration"""
    print("\n🔗 Testing Complete Integration")
    print("=" * 40)
    
    try:
        from database import user_manager, profile_manager, job_search_manager
        from ashby_job_search import AshbyJobSearchAgent
        
        # Create a test user
        print("1. Creating test user...")
        user = user_manager.create_user(
            email="integration@example.com",
            username="integration_test",
            password="testpass123",
            first_name="Integration",
            last_name="Test"
        )
        
        if not user:
            print("❌ Failed to create test user")
            return
        
        print(f"✅ Test user created: {user.username}")
        
        # Create profile
        print("\n2. Creating user profile...")
        profile = profile_manager.create_profile(
            user_id=user.id,
            phone="(555) 999-8888",
            location="Remote",
            linkedin_url="https://linkedin.com/in/integrationtest",
            skills=["Python", "Selenium", "Cypress", "Pytest", "Jenkins"]
        )
        
        if profile:
            print("✅ Profile created successfully")
        
        # Create job search
        print("\n3. Creating job search...")
        job_search = job_search_manager.create_job_search(
            user_id=user.id,
            search_name="Integration Test Search",
            job_titles=["QA Engineer", "QA Automation Engineer"],
            locations=["Remote"],
            keywords=["automation", "selenium"],
            remote_only=True
        )
        
        if job_search:
            print("✅ Job search created successfully")
            
            # Perform actual job search
            print("\n4. Performing job search...")
            agent = AshbyJobSearchAgent()
            jobs = agent.search_qa_jobs(
                job_titles=["QA Engineer", "QA Automation Engineer"],
                max_results=3
            )
            
            if jobs:
                print(f"✅ Found {len(jobs)} jobs")
                
                # Save results
                success = job_search_manager.save_search_results(job_search.id, jobs)
                if success:
                    print("✅ Job results saved to database")
                    
                    # Retrieve and display results
                    results = job_search_manager.get_search_results(job_search.id)
                    print(f"\n📊 Retrieved {len(results)} jobs from database:")
                    for i, result in enumerate(results, 1):
                        print(f"{i}. {result.job_title} at {result.company}")
                        print(f"   Location: {result.location}")
                        print(f"   URL: {result.url}")
                else:
                    print("❌ Failed to save job results")
            else:
                print("ℹ️ No jobs found (this is normal if no QA jobs are currently available)")
        else:
            print("❌ Failed to create job search")
            
    except Exception as e:
        print(f"❌ Error in integration test: {e}")

def main():
    """Main test function"""
    print("🧪 Enhanced Job Application Agent - Test Suite")
    print("=" * 60)
    
    # Run tests
    test_database_operations()
    test_ashby_job_search()
    test_user_interface()
    test_integration()
    
    print("\n" + "=" * 60)
    print("✅ Test suite completed!")
    print("\nTo use the full system, run:")
    print("python user_interface.py")

if __name__ == "__main__":
    main() 