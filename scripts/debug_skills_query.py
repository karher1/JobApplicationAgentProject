#!/usr/bin/env python3
"""
Debug skills query to understand what's happening
"""

import os
import sys
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def debug_skills_query():
    """Debug the skills query"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🔍 Debugging skills query...")
        
        user_id = 32
        
        # Test 1: Check user_skills table without join
        print("\n1. Checking user_skills table without join:")
        try:
            result = supabase.table("user_skills").select("*").eq("user_id", user_id).execute()
            print(f"   Found {len(result.data)} user_skills records")
            if result.data:
                print(f"   First record: {result.data[0]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 2: Check skills table
        print("\n2. Checking skills table:")
        try:
            result = supabase.table("skills").select("*").limit(5).execute()
            print(f"   Found {len(result.data)} skills records")
            if result.data:
                print(f"   First record: {result.data[0]}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 3: Try the join query
        print("\n3. Testing join query:")
        try:
            result = supabase.table("user_skills").select("*, skills(*)").eq("user_id", user_id).execute()
            print(f"   Join query returned {len(result.data)} records")
            if result.data:
                print(f"   First record: {result.data[0]}")
                print(f"   Skills field in first record: {result.data[0].get('skills', 'MISSING')}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        # Test 4: Check if there's a specific skill_id in the skills table
        print("\n4. Testing specific skill lookup:")
        try:
            # Get a skill_id from user_skills
            user_skills_result = supabase.table("user_skills").select("skill_id").eq("user_id", user_id).limit(1).execute()
            if user_skills_result.data:
                skill_id = user_skills_result.data[0]['skill_id']
                print(f"   Looking up skill_id: {skill_id}")
                
                # Look up the skill
                skill_result = supabase.table("skills").select("*").eq("id", skill_id).execute()
                if skill_result.data:
                    print(f"   Found skill: {skill_result.data[0]}")
                else:
                    print(f"   ❌ No skill found with id {skill_id}")
        except Exception as e:
            print(f"   ❌ Error: {e}")
        
        return True
            
    except Exception as e:
        print(f"❌ Error debugging skills query: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Skills Query Debug Tool")
    print("=" * 50)
    
    debug_skills_query()