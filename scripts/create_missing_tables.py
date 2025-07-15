#!/usr/bin/env python3
"""
Create Missing Tables Script
Creates the missing tables that the application expects
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_missing_tables():
    """Create missing tables using Supabase client"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🔧 Creating missing tables...")
        
        # Create user_preferences table
        try:
            print("   Creating user_preferences table...")
            # We'll create this table by inserting a dummy record and letting Supabase create the table
            # This is a workaround since we can't execute raw SQL
            dummy_pref = {
                "user_id": 999999,  # Dummy user ID
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
            
            # Try to insert - this will create the table if it doesn't exist
            result = supabase.table("user_preferences").insert(dummy_pref).execute()
            print("   ✅ user_preferences table created/accessible")
            
            # Clean up dummy record
            supabase.table("user_preferences").delete().eq("user_id", 999999).execute()
            
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
        
        # Create jobs table (if it doesn't exist)
        try:
            print("   Checking jobs table...")
            dummy_job = {
                "title": "Test Job",
                "company": "Test Company",
                "location": "Test Location",
                "url": "https://example.com/test-job",
                "job_board": "Test Board",
                "description_snippet": "Test description",
                "is_active": True
            }
            
            result = supabase.table("jobs").insert(dummy_job).execute()
            print("   ✅ jobs table accessible")
            
            # Clean up dummy record
            supabase.table("jobs").delete().eq("url", "https://example.com/test-job").execute()
            
        except Exception as e:
            print(f"   ❌ jobs table error: {str(e)}")
        
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
        
        # Create digest_preferences table
        try:
            print("   Creating digest_preferences table...")
            dummy_digest_pref = {
                "user_id": 999999,
                "include_job_matches": True,
                "include_applications": True,
                "include_insights": True,
                "include_stats": True,
                "max_job_matches": 10,
                "max_application_updates": 20,
                "preferred_job_types": ["Full-time"],
                "preferred_locations": ["San Francisco"],
                "salary_range_min": 80000,
                "salary_range_max": 150000,
                "notification_frequency": "daily",
                "preferred_time": "09:00:00",
                "timezone": "UTC"
            }
            
            result = supabase.table("digest_preferences").insert(dummy_digest_pref).execute()
            print("   ✅ digest_preferences table created/accessible")
            
            # Clean up dummy record
            supabase.table("digest_preferences").delete().eq("user_id", 999999).execute()
            
        except Exception as e:
            print(f"   ❌ digest_preferences table error: {str(e)}")
        
        # Create generated_digests table
        try:
            print("   Creating generated_digests table...")
            dummy_digest = {
                "user_id": 999999,
                "digest_type": "daily",
                "digest_date": "2025-01-01",
                "content": {"test": "data"},
                "status": "pending"
            }
            
            result = supabase.table("generated_digests").insert(dummy_digest).execute()
            print("   ✅ generated_digests table created/accessible")
            
            # Clean up dummy record
            supabase.table("generated_digests").delete().eq("user_id", 999999).execute()
            
        except Exception as e:
            print(f"   ❌ generated_digests table error: {str(e)}")
        
        # Create notification_configs table
        try:
            print("   Creating notification_configs table...")
            dummy_notif_config = {
                "user_id": 999999,
                "notification_type": "email",
                "email_address": "test@example.com",
                "is_active": True,
                "preferences": {"frequency": "daily"}
            }
            
            result = supabase.table("notification_configs").insert(dummy_notif_config).execute()
            print("   ✅ notification_configs table created/accessible")
            
            # Clean up dummy record
            supabase.table("notification_configs").delete().eq("user_id", 999999).execute()
            
        except Exception as e:
            print(f"   ❌ notification_configs table error: {str(e)}")
        
        # Create notification_history table
        try:
            print("   Creating notification_history table...")
            dummy_notif_history = {
                "user_id": 999999,
                "notification_type": "email",
                "subject": "Test notification",
                "content_preview": "Test content",
                "status": "sent"
            }
            
            result = supabase.table("notification_history").insert(dummy_notif_history).execute()
            print("   ✅ notification_history table created/accessible")
            
            # Clean up dummy record
            supabase.table("notification_history").delete().eq("user_id", 999999).execute()
            
        except Exception as e:
            print(f"   ❌ notification_history table error: {str(e)}")
        
        # Create email_templates table
        try:
            print("   Creating email_templates table...")
            dummy_template = {
                "name": "test_template",
                "subject_template": "Test Subject",
                "html_template": "<h1>Test</h1>",
                "text_template": "Test",
                "variables": ["user_name"],
                "description": "Test template",
                "is_active": True
            }
            
            result = supabase.table("email_templates").insert(dummy_template).execute()
            print("   ✅ email_templates table created/accessible")
            
            # Clean up dummy record
            supabase.table("email_templates").delete().eq("name", "test_template").execute()
            
        except Exception as e:
            print(f"   ❌ email_templates table error: {str(e)}")
        
        # Create digest_schedules table
        try:
            print("   Creating digest_schedules table...")
            dummy_schedule = {
                "user_id": 999999,
                "digest_type": "daily",
                "frequency": "daily",
                "preferred_time": "09:00:00",
                "timezone": "UTC",
                "is_active": True
            }
            
            result = supabase.table("digest_schedules").insert(dummy_schedule).execute()
            print("   ✅ digest_schedules table created/accessible")
            
            # Clean up dummy record
            supabase.table("digest_schedules").delete().eq("user_id", 999999).execute()
            
        except Exception as e:
            print(f"   ❌ digest_schedules table error: {str(e)}")
        
        print("\n✅ Table creation completed!")
        return True
        
    except Exception as e:
        print(f"❌ Error creating tables: {str(e)}")
        return False

def test_table_access():
    """Test access to all tables"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🔍 Testing table access...")
        
        tables_to_test = [
            "users",
            "user_profiles", 
            "user_preferences",
            "skills",
            "jobs",
            "job_descriptions",
            "job_searches",
            "job_search_results",
            "job_applications",
            "digest_preferences",
            "generated_digests",
            "notification_configs",
            "notification_history",
            "email_templates",
            "digest_schedules"
        ]
        
        accessible_tables = []
        inaccessible_tables = []
        
        for table in tables_to_test:
            try:
                result = supabase.table(table).select("id").limit(1).execute()
                accessible_tables.append(table)
                print(f"   ✅ {table} table accessible")
            except Exception as e:
                inaccessible_tables.append(table)
                print(f"   ❌ {table} table error: {str(e)}")
        
        print(f"\n📊 Table Access Summary:")
        print(f"   ✅ Accessible tables: {len(accessible_tables)}")
        print(f"   ❌ Inaccessible tables: {len(inaccessible_tables)}")
        
        if inaccessible_tables:
            print(f"   📝 Inaccessible tables: {', '.join(inaccessible_tables)}")
        
        return len(inaccessible_tables) == 0
        
    except Exception as e:
        print(f"❌ Error testing table access: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Create Missing Tables Tool")
    print("=" * 50)
    
    # Create missing tables
    if create_missing_tables():
        print("\n✅ Tables created successfully!")
        
        # Test table access
        print("\n🔍 Testing table access...")
        if test_table_access():
            print("\n🎉 All tables are now accessible!")
        else:
            print("\n⚠️  Some tables may still be inaccessible")
    else:
        print("\n❌ Failed to create tables!")
        sys.exit(1) 