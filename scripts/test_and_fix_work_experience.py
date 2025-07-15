#!/usr/bin/env python3
"""
Test work experience table structure and add missing columns
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_work_experience_table():
    """Test the work_experience table structure"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🔍 Testing work_experience table structure...")
        
        # Try to insert a test record with technologies_used
        try:
            test_data = {
                "user_id": 32,
                "company_name": "Test Company",
                "job_title": "Test Job",
                "start_date": "2024-01-01",
                "description": "Test description",
                "technologies_used": ["Python", "FastAPI"]
            }
            
            # This will fail if the column doesn't exist
            result = supabase.table("work_experience").insert(test_data).execute()
            print("✅ technologies_used column exists and is working")
            
            # Clean up the test record
            if result.data:
                supabase.table("work_experience").delete().eq("id", result.data[0]["id"]).execute()
                print("✅ Test record cleaned up")
            
            return True
            
        except Exception as e:
            print(f"❌ technologies_used column test failed: {str(e)}")
            if "technologies_used" in str(e):
                print("🔧 The technologies_used column is missing from the work_experience table")
                print("📝 You need to add this column manually in the Supabase SQL editor:")
                print("   ALTER TABLE work_experience ADD COLUMN IF NOT EXISTS technologies_used TEXT[] DEFAULT '{}';")
            return False
            
    except Exception as e:
        print(f"❌ Error testing work_experience table: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Work Experience Table Test")
    print("=" * 50)
    
    if test_work_experience_table():
        print("\n✅ Work experience table is properly configured!")
    else:
        print("\n❌ Work experience table needs to be fixed!")
        sys.exit(1)