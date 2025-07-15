#!/usr/bin/env python3
"""
Test the complete get_user_skills flow
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.user_profile import UserSkill, ProficiencyLevel
from supabase import create_client, Client
from dotenv import load_dotenv
from datetime import datetime

# Load environment variables
load_dotenv()

async def test_get_user_skills_flow():
    """Test the complete get_user_skills flow"""
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
    
    if not supabase_url or not supabase_key:
        print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set")
        return False
    
    # Create Supabase client
    supabase: Client = create_client(supabase_url, supabase_key)
    
    print("🔍 Testing complete get_user_skills flow...")
    
    user_id = 32
    
    try:
        # Step 1: Get raw data from Supabase
        print("\n1. Getting raw data from Supabase...")
        result = supabase.table("user_skills").select("*, skills(*)").eq("user_id", user_id).execute()
        print(f"   Got {len(result.data)} records")
        
        # Step 2: Transform the data
        print("\n2. Transforming data...")
        skills_data = []
        for i, skill_item in enumerate(result.data):
            print(f"   Processing item {i+1}: {skill_item.get('id', 'no id')}")
            
            # Transform 'skills' key to 'skill' key
            if 'skills' in skill_item:
                skill_item['skill'] = skill_item.pop('skills')
                print(f"      Transformed 'skills' to 'skill'")
            
            # Remove extra fields
            if 'updated_at' in skill_item:
                skill_item.pop('updated_at')
                print(f"      Removed 'updated_at'")
            
            skills_data.append(skill_item)
        
        print(f"   Transformed {len(skills_data)} items")
        
        # Step 3: Create UserSkill objects
        print("\n3. Creating UserSkill objects...")
        user_skills = []
        for i, skill_data in enumerate(skills_data):
            try:
                user_skill = UserSkill(**skill_data)
                user_skills.append(user_skill)
                print(f"   ✅ Created UserSkill {i+1}: {user_skill.skill.name if user_skill.skill else 'No skill'}")
            except Exception as e:
                print(f"   ❌ Failed to create UserSkill {i+1}: {e}")
                print(f"      Data: {skill_data}")
                return False
        
        print(f"\n✅ Successfully created {len(user_skills)} UserSkill objects!")
        
        # Step 4: Show some results
        print("\n4. Sample results:")
        for i, user_skill in enumerate(user_skills[:3]):
            print(f"   {i+1}. {user_skill.skill.name if user_skill.skill else 'No skill'} - {user_skill.proficiency_level}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error in get_user_skills flow: {e}")
        import traceback
        print(f"Traceback: {traceback.format_exc()}")
        return False

if __name__ == "__main__":
    print("🚀 Get User Skills Flow Test")
    print("=" * 50)
    
    import asyncio
    
    if asyncio.run(test_get_user_skills_flow()):
        print("\n✅ get_user_skills flow is working correctly!")
    else:
        print("\n❌ get_user_skills flow has issues!")
        sys.exit(1)