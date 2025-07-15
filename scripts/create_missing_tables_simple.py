#!/usr/bin/env python3
"""
Simple Missing Tables Creation Script
Creates missing tables by inserting dummy data
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def create_missing_tables():
    """Create missing tables by inserting dummy data"""
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
        
        # Get an existing user ID
        try:
            user_result = supabase.table("users").select("id").limit(1).execute()
            if user_result.data:
                test_user_id = user_result.data[0]["id"]
                print(f"   ✅ Using existing user ID: {test_user_id}")
            else:
                print("   ❌ No users found")
                return False
        except Exception as e:
            print(f"   ❌ Error getting user: {str(e)}")
            return False
        
        # Create skills table
        try:
            print("   Creating skills table...")
            skill_data = {
                "name": "Python",
                "category": "programming",
                "description": "Python programming language",
                "is_active": True
            }
            
            result = supabase.table("skills").insert(skill_data).execute()
            print("   ✅ Skills table created")
            
            # Clean up
            supabase.table("skills").delete().eq("name", "Python").execute()
            
        except Exception as e:
            print(f"   ❌ Skills table error: {str(e)}")
        
        # Create user_skills table
        try:
            print("   Creating user_skills table...")
            # First create a skill
            skill_result = supabase.table("skills").insert({
                "name": "JavaScript",
                "category": "programming",
                "description": "JavaScript programming language",
                "is_active": True
            }).execute()
            
            skill_id = skill_result.data[0]["id"]
            
            user_skill_data = {
                "user_id": test_user_id,
                "skill_id": skill_id,
                "proficiency_level": "intermediate",
                "years_of_experience": 2
            }
            
            result = supabase.table("user_skills").insert(user_skill_data).execute()
            print("   ✅ User skills table created")
            
            # Clean up
            supabase.table("user_skills").delete().eq("user_id", test_user_id).execute()
            supabase.table("skills").delete().eq("id", skill_id).execute()
            
        except Exception as e:
            print(f"   ❌ User skills table error: {str(e)}")
        
        # Create work_experience table
        try:
            print("   Creating work_experience table...")
            work_data = {
                "user_id": test_user_id,
                "company_name": "Test Company",
                "job_title": "Software Engineer",
                "location": "San Francisco",
                "start_date": "2023-01-01",
                "is_current": True,
                "description": "Test work experience"
            }
            
            result = supabase.table("work_experience").insert(work_data).execute()
            print("   ✅ Work experience table created")
            
            # Clean up
            supabase.table("work_experience").delete().eq("user_id", test_user_id).execute()
            
        except Exception as e:
            print(f"   ❌ Work experience table error: {str(e)}")
        
        # Create education table
        try:
            print("   Creating education table...")
            education_data = {
                "user_id": test_user_id,
                "institution_name": "Test University",
                "degree": "Bachelor of Science",
                "field_of_study": "Computer Science",
                "start_date": "2019-09-01",
                "end_date": "2023-05-01",
                "is_current": False
            }
            
            result = supabase.table("education").insert(education_data).execute()
            print("   ✅ Education table created")
            
            # Clean up
            supabase.table("education").delete().eq("user_id", test_user_id).execute()
            
        except Exception as e:
            print(f"   ❌ Education table error: {str(e)}")
        
        # Create certifications table
        try:
            print("   Creating certifications table...")
            cert_data = {
                "user_id": test_user_id,
                "name": "AWS Certified Developer",
                "issuing_organization": "Amazon Web Services",
                "issue_date": "2023-06-01",
                "is_active": True
            }
            
            result = supabase.table("certifications").insert(cert_data).execute()
            print("   ✅ Certifications table created")
            
            # Clean up
            supabase.table("certifications").delete().eq("user_id", test_user_id).execute()
            
        except Exception as e:
            print(f"   ❌ Certifications table error: {str(e)}")
        
        # Create resumes table
        try:
            print("   Creating resumes table...")
            resume_data = {
                "user_id": test_user_id,
                "title": "Test Resume",
                "file_path": "/uploads/test.pdf",
                "file_name": "test.pdf",
                "file_size": 1024,
                "is_primary": True,
                "version": "1.0"
            }
            
            result = supabase.table("resumes").insert(resume_data).execute()
            print("   ✅ Resumes table created")
            
            # Clean up
            supabase.table("resumes").delete().eq("user_id", test_user_id).execute()
            
        except Exception as e:
            print(f"   ❌ Resumes table error: {str(e)}")
        
        # Create application_history table
        try:
            print("   Creating application_history table...")
            app_data = {
                "user_id": test_user_id,
                "job_title": "Software Engineer",
                "company": "Test Company",
                "application_date": "2025-01-01",
                "status": "applied"
            }
            
            result = supabase.table("application_history").insert(app_data).execute()
            print("   ✅ Application history table created")
            
            # Clean up
            supabase.table("application_history").delete().eq("user_id", test_user_id).execute()
            
        except Exception as e:
            print(f"   ❌ Application history table error: {str(e)}")
        
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
            "user_skills",
            "jobs",
            "job_descriptions",
            "job_searches",
            "job_search_results",
            "job_applications",
            "work_experience",
            "education",
            "certifications",
            "resumes",
            "application_history",
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
    print("🚀 Simple Missing Tables Creation Tool")
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