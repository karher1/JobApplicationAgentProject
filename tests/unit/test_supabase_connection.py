#!/usr/bin/env python3
"""
Test Supabase Connection

This script tests the Supabase connection and basic database operations.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_supabase_connection():
    """Test basic Supabase connection"""
    print("🔗 Testing Supabase Connection")
    print("=" * 40)
    
    try:
        from database_supabase import supabase_manager
        
        if supabase_manager and supabase_manager.test_connection():
            print("✅ Supabase connection successful!")
            return True
        else:
            print("❌ Supabase connection failed!")
            return False
            
    except Exception as e:
        print(f"❌ Error testing Supabase connection: {e}")
        return False

def test_user_operations():
    """Test user management operations"""
    print("\n👤 Testing User Operations")
    print("=" * 40)
    
    try:
        from database_supabase import user_manager
        
        if not user_manager:
            print("❌ User manager not available")
            return False
        
        # Test user creation
        print("1. Testing user creation...")
        test_user = user_manager.create_user(
            email="supabase_test@example.com",
            username="supabase_test",
            password="testpass123",
            first_name="Supabase",
            last_name="Test"
        )
        
        if test_user:
            print(f"✅ User created: {test_user['username']}")
            user_id = test_user['id']
            
            # Test user retrieval
            print("\n2. Testing user retrieval...")
            retrieved_user = user_manager.get_user_by_id(user_id)
            if retrieved_user:
                print(f"✅ User retrieved: {retrieved_user['email']}")
            else:
                print("❌ Failed to retrieve user")
            
            # Test user authentication
            print("\n3. Testing user authentication...")
            authenticated_user = user_manager.authenticate_user(
                "supabase_test@example.com", "testpass123"
            )
            if authenticated_user:
                print(f"✅ User authenticated: {authenticated_user['username']}")
            else:
                print("❌ User authentication failed")
            
            return True
        else:
            print("❌ Failed to create test user")
            return False
            
    except Exception as e:
        print(f"❌ Error testing user operations: {e}")
        return False

def test_profile_operations():
    """Test profile management operations"""
    print("\n📋 Testing Profile Operations")
    print("=" * 40)
    
    try:
        from database_supabase import profile_manager, user_manager
        
        if not profile_manager or not user_manager:
            print("❌ Profile or user manager not available")
            return False
        
        # Get or create a test user
        test_user = user_manager.get_user_by_email("supabase_test@example.com")
        if not test_user:
            test_user = user_manager.create_user(
                email="supabase_test@example.com",
                username="supabase_test",
                password="testpass123"
            )
        
        if not test_user:
            print("❌ No test user available")
            return False
        
        user_id = test_user['id']
        
        # Test profile creation
        print("1. Testing profile creation...")
        profile = profile_manager.create_profile(
            user_id=user_id,
            phone="(555) 123-4567",
            location="San Francisco, CA",
            linkedin_url="https://linkedin.com/in/supabase_test",
            skills=["Python", "Selenium", "Testing", "Supabase"]
        )
        
        if profile:
            print(f"✅ Profile created with {len(profile.get('skills', []))} skills")
            
            # Test profile retrieval
            print("\n2. Testing profile retrieval...")
            retrieved_profile = profile_manager.get_profile(user_id)
            if retrieved_profile:
                print(f"✅ Profile retrieved: {retrieved_profile.get('location', 'No location')}")
            else:
                print("❌ Failed to retrieve profile")
            
            # Test profile update
            print("\n3. Testing profile update...")
            updated_profile = profile_manager.create_profile(
                user_id=user_id,
                location="New York, NY",
                skills=["Python", "Selenium", "Testing", "Supabase", "PostgreSQL"]
            )
            if updated_profile:
                print(f"✅ Profile updated with {len(updated_profile.get('skills', []))} skills")
            else:
                print("❌ Failed to update profile")
            
            return True
        else:
            print("❌ Failed to create profile")
            return False
            
    except Exception as e:
        print(f"❌ Error testing profile operations: {e}")
        return False

def test_job_search_operations():
    """Test job search operations"""
    print("\n🔍 Testing Job Search Operations")
    print("=" * 40)
    
    try:
        from database_supabase import job_search_manager, user_manager
        
        if not job_search_manager or not user_manager:
            print("❌ Job search or user manager not available")
            return False
        
        # Get or create a test user
        test_user = user_manager.get_user_by_email("supabase_test@example.com")
        if not test_user:
            test_user = user_manager.create_user(
                email="supabase_test@example.com",
                username="supabase_test",
                password="testpass123"
            )
        
        if not test_user:
            print("❌ No test user available")
            return False
        
        user_id = test_user['id']
        
        # Test job search creation
        print("1. Testing job search creation...")
        job_search = job_search_manager.create_job_search(
            user_id=user_id,
            search_name="Supabase Test Search",
            job_titles=["QA Engineer", "Senior QA Engineer"],
            locations=["Remote", "San Francisco"],
            keywords=["automation", "selenium"],
            remote_only=True
        )
        
        if job_search:
            print(f"✅ Job search created: {job_search['search_name']}")
            search_id = job_search['id']
            
            # Test saving search results
            print("\n2. Testing search results saving...")
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
            
            success = job_search_manager.save_search_results(search_id, test_results)
            if success:
                print("✅ Search results saved successfully")
                
                # Test retrieving search results
                print("\n3. Testing search results retrieval...")
                results = job_search_manager.get_search_results(search_id)
                print(f"✅ Retrieved {len(results)} search results")
                
                for i, result in enumerate(results, 1):
                    print(f"   {i}. {result['job_title']} at {result['company']}")
            else:
                print("❌ Failed to save search results")
            
            # Test getting user searches
            print("\n4. Testing user searches retrieval...")
            user_searches = job_search_manager.get_user_searches(user_id)
            print(f"✅ Retrieved {len(user_searches)} user searches")
            
            return True
        else:
            print("❌ Failed to create job search")
            return False
            
    except Exception as e:
        print(f"❌ Error testing job search operations: {e}")
        return False

def test_job_application_operations():
    """Test job application operations"""
    print("\n📝 Testing Job Application Operations")
    print("=" * 40)
    
    try:
        from database_supabase import job_application_manager, user_manager
        
        if not job_application_manager or not user_manager:
            print("❌ Job application or user manager not available")
            return False
        
        # Get or create a test user
        test_user = user_manager.get_user_by_email("supabase_test@example.com")
        if not test_user:
            test_user = user_manager.create_user(
                email="supabase_test@example.com",
                username="supabase_test",
                password="testpass123"
            )
        
        if not test_user:
            print("❌ No test user available")
            return False
        
        user_id = test_user['id']
        
        # Test application creation
        print("1. Testing application creation...")
        application = job_application_manager.create_application(
            user_id=user_id,
            job_url="https://example.com/job1",
            job_title="QA Engineer",
            company="Test Company",
            status="applied"
        )
        
        if application:
            print(f"✅ Application created: {application['job_title']} at {application['company']}")
            app_id = application['id']
            
            # Test application status update
            print("\n2. Testing application status update...")
            success = job_application_manager.update_application_status(
                app_id,
                status="interviewed",
                success=True,
                filled_fields=["name", "email", "phone"],
                failed_fields=[]
            )
            if success:
                print("✅ Application status updated successfully")
            else:
                print("❌ Failed to update application status")
            
            # Test getting user applications
            print("\n3. Testing user applications retrieval...")
            applications = job_application_manager.get_user_applications(user_id)
            print(f"✅ Retrieved {len(applications)} user applications")
            
            return True
        else:
            print("❌ Failed to create application")
            return False
            
    except Exception as e:
        print(f"❌ Error testing job application operations: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 Supabase Database Test Suite")
    print("=" * 50)
    
    # Check environment variables
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Missing Supabase environment variables!")
        print("Please set SUPABASE_URL and SUPABASE_KEY in your .env file")
        return
    
    print(f"✅ Supabase URL: {supabase_url}")
    print(f"✅ Supabase Key: {'*' * 10}{supabase_key[-4:] if supabase_key else 'None'}")
    
    # Run tests
    tests = [
        ("Connection", test_supabase_connection),
        ("User Operations", test_user_operations),
        ("Profile Operations", test_profile_operations),
        ("Job Search Operations", test_job_search_operations),
        ("Job Application Operations", test_job_application_operations)
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 50)
    print("📊 Test Results Summary")
    print("=" * 50)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name}: {status}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Supabase integration is working correctly.")
    else:
        print("⚠️ Some tests failed. Please check your Supabase configuration.")

if __name__ == "__main__":
    main() 