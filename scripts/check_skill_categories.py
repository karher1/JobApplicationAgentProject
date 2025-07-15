#!/usr/bin/env python3
"""
Check what skill categories exist in the database
"""

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def check_skill_categories():
    """Check what skill categories exist in the database"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🔍 Checking skill categories in database...")
        
        # Get all skills
        result = supabase.table("skills").select("category").execute()
        
        # Get unique categories
        categories = set()
        for skill in result.data:
            if skill.get('category'):
                categories.add(skill['category'])
        
        print(f"\n📊 Found {len(categories)} unique skill categories:")
        for category in sorted(categories):
            print(f"   - {category}")
        
        return True
            
    except Exception as e:
        print(f"❌ Error checking skill categories: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Skill Categories Check")
    print("=" * 50)
    
    check_skill_categories()