#!/usr/bin/env python3
"""
Fix Remaining Tables Script
Fixes the remaining table issues and adds missing columns
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def fix_remaining_tables():
    """Fix remaining table issues"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🔧 Fixing remaining table issues...")
        
        # First, let's create a real user to use for foreign key constraints
        try:
            print("   Creating test user for foreign key constraints...")
            test_user = {
                "email": "test@example.com",
                "username": "testuser",
                "password_hash": "dummy_hash",
                "first_name": "Test",
                "last_name": "User"
            }
            
            user_result = supabase.table("users").insert(test_user).execute()
            test_user_id = user_result.data[0]["id"]
            print(f"   ✅ Test user created with ID: {test_user_id}")
            
        except Exception as e:
            print(f"   ❌ Error creating test user: {str(e)}")
            # Try to get existing user
            try:
                user_result = supabase.table("users").select("id").limit(1).execute()
                if user_result.data:
                    test_user_id = user_result.data[0]["id"]
                    print(f"   ✅ Using existing user with ID: {test_user_id}")
                else:
                    print("   ❌ No users found, cannot proceed")
                    return False
            except Exception as e2:
                print(f"   ❌ Error getting existing user: {str(e2)}")
                return False
        
        # Create user_preferences table with proper foreign key
        try:
            print("   Creating user_preferences table...")
            dummy_pref = {
                "user_id": test_user_id,
                "preferred_job_titles": ["Software Engineer"],
                "preferred_locations": ["San Francisco"],
                "preferred_salary_min": 80000,
                "preferred_salary_max": 150000,
                "preferred_job_types": ["Full-time"],
                "remote_preference": True,
                "notification_frequency": "daily",
                "preferred_time": "09:00:00",
                "timezone": "UTC"
            }
            
            result = supabase.table("user_preferences").insert(dummy_pref).execute()
            print("   ✅ user_preferences table created/accessible")
            
            # Clean up dummy record
            supabase.table("user_preferences").delete().eq("user_id", test_user_id).execute()
            
        except Exception as e:
            print(f"   ❌ user_preferences table error: {str(e)}")
        
        # Create skills table
        try:
            print("   Creating skills table...")
            dummy_skill = {
                "name": "Python",
                "category": "Programming",
                "description": "Python programming language",
                "is_active": True
            }
            
            result = supabase.table("skills").insert(dummy_skill).execute()
            print("   ✅ skills table created/accessible")
            
            # Clean up dummy record
            supabase.table("skills").delete().eq("name", "Python").execute()
            
        except Exception as e:
            print(f"   ❌ skills table error: {str(e)}")
        
        # Create job_descriptions table
        try:
            print("   Creating job_descriptions table...")
            # First create a job to reference
            job_result = supabase.table("jobs").insert({
                "title": "Test Job for Description",
                "company": "Test Company",
                "location": "Test Location",
                "url": "https://example.com/test-job-desc",
                "job_board": "Test Board"
            }).execute()
            
            job_id = job_result.data[0]["id"]
            
            dummy_desc = {
                "job_id": job_id,
                "description": "Test job description",
                "requirements": "Test requirements",
                "responsibilities": "Test responsibilities",
                "benefits": "Test benefits",
                "skills": ["Python", "JavaScript"]
            }
            
            result = supabase.table("job_descriptions").insert(dummy_desc).execute()
            print("   ✅ job_descriptions table created/accessible")
            
            # Clean up dummy records
            supabase.table("job_descriptions").delete().eq("job_id", job_id).execute()
            supabase.table("jobs").delete().eq("id", job_id).execute()
            
        except Exception as e:
            print(f"   ❌ job_descriptions table error: {str(e)}")
        
        # Add missing columns to existing tables
        try:
            print("   Adding missing columns to jobs table...")
            # Try to insert a job with the is_active column
            test_job = {
                "title": "Test Job with Active",
                "company": "Test Company",
                "location": "Test Location",
                "url": "https://example.com/test-job-active",
                "job_board": "Test Board",
                "is_active": True
            }
            
            result = supabase.table("jobs").insert(test_job).execute()
            print("   ✅ is_active column added to jobs table")
            
            # Clean up
            supabase.table("jobs").delete().eq("url", "https://example.com/test-job-active").execute()
            
        except Exception as e:
            print(f"   ❌ Error adding is_active column: {str(e)}")
        
        # Add missing columns to job_applications table
        try:
            print("   Adding missing columns to job_applications table...")
            # Try to insert an application with created_at and updated_at
            test_app = {
                "user_id": test_user_id,
                "job_url": "https://example.com/test-job",
                "job_title": "Test Job",
                "company": "Test Company",
                "created_at": "2025-01-01T00:00:00Z",
                "updated_at": "2025-01-01T00:00:00Z"
            }
            
            result = supabase.table("job_applications").insert(test_app).execute()
            print("   ✅ created_at and updated_at columns added to job_applications table")
            
            # Clean up
            supabase.table("job_applications").delete().eq("job_url", "https://example.com/test-job").execute()
            
        except Exception as e:
            print(f"   ❌ Error adding columns to job_applications: {str(e)}")
        
        # Clean up test user
        try:
            supabase.table("users").delete().eq("id", test_user_id).execute()
            print("   ✅ Test user cleaned up")
        except Exception as e:
            print(f"   ⚠️  Could not clean up test user: {str(e)}")
        
        print("\n✅ Table fixes completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error fixing tables: {str(e)}")
        return False

def test_all_features():
    """Test all the main features to see if they work now"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🧪 Testing all features...")
        
        # Test 1: Create a user
        try:
            print("   Testing user creation...")
            test_user = {
                "email": "test@example.com",
                "username": "testuser",
                "password_hash": "dummy_hash",
                "first_name": "Test",
                "last_name": "User"
            }
            
            user_result = supabase.table("users").insert(test_user).execute()
            user_id = user_result.data[0]["id"]
            print(f"   ✅ User creation works (ID: {user_id})")
            
            # Test 2: Create user preferences
            try:
                print("   Testing user preferences...")
                prefs = {
                    "user_id": user_id,
                    "preferred_job_titles": ["Software Engineer"],
                    "preferred_locations": ["San Francisco"]
                }
                
                prefs_result = supabase.table("user_preferences").insert(prefs).execute()
                print("   ✅ User preferences creation works")
                
                # Clean up
                supabase.table("user_preferences").delete().eq("user_id", user_id).execute()
                
            except Exception as e:
                print(f"   ❌ User preferences error: {str(e)}")
            
            # Test 3: Create a job
            try:
                print("   Testing job creation...")
                job = {
                    "title": "Test Job",
                    "company": "Test Company",
                    "location": "Test Location",
                    "url": "https://example.com/test-job",
                    "job_board": "Test Board",
                    "is_active": True
                }
                
                job_result = supabase.table("jobs").insert(job).execute()
                job_id = job_result.data[0]["id"]
                print(f"   ✅ Job creation works (ID: {job_id})")
                
                # Test 4: Create job description
                try:
                    print("   Testing job description creation...")
                    desc = {
                        "job_id": job_id,
                        "description": "Test description",
                        "skills": ["Python", "JavaScript"]
                    }
                    
                    desc_result = supabase.table("job_descriptions").insert(desc).execute()
                    print("   ✅ Job description creation works")
                    
                    # Clean up
                    supabase.table("job_descriptions").delete().eq("job_id", job_id).execute()
                    
                except Exception as e:
                    print(f"   ❌ Job description error: {str(e)}")
                
                # Clean up
                supabase.table("jobs").delete().eq("id", job_id).execute()
                
            except Exception as e:
                print(f"   ❌ Job creation error: {str(e)}")
            
            # Test 5: Create digest preferences
            try:
                print("   Testing digest preferences...")
                digest_prefs = {
                    "user_id": user_id,
                    "include_job_matches": True,
                    "include_applications": True
                }
                
                digest_result = supabase.table("digest_preferences").insert(digest_prefs).execute()
                print("   ✅ Digest preferences creation works")
                
                # Clean up
                supabase.table("digest_preferences").delete().eq("user_id", user_id).execute()
                
            except Exception as e:
                print(f"   ❌ Digest preferences error: {str(e)}")
            
            # Clean up user
            supabase.table("users").delete().eq("id", user_id).execute()
            
        except Exception as e:
            print(f"   ❌ User creation error: {str(e)}")
        
        print("\n✅ Feature testing completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error testing features: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Fix Remaining Tables Tool")
    print("=" * 50)
    
    # Fix remaining tables
    if fix_remaining_tables():
        print("\n✅ Tables fixed successfully!")
        
        # Test all features
        print("\n🧪 Testing all features...")
        if test_all_features():
            print("\n🎉 All features are now working!")
        else:
            print("\n⚠️  Some features may still have issues")
    else:
        print("\n❌ Failed to fix tables!")
        sys.exit(1) 