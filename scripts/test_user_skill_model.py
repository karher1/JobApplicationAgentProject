#!/usr/bin/env python3
"""
Test UserSkill model instantiation with real data
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models.user_profile import UserSkill, ProficiencyLevel
from datetime import datetime

def test_user_skill_model():
    """Test UserSkill model with real data from database"""
    
    # This is the real data structure from Supabase
    real_data = {
        'id': 11,
        'user_id': 32,
        'skill_id': 21,
        'proficiency_level': 'intermediate',
        'years_of_experience': None,
        'created_at': '2025-07-15T18:10:30.271603+00:00',
        'is_highlighted': False,
        'skill': {
            'id': 21,
            'name': 'Python',
            'category': 'programming',
            'is_active': True,
            'created_at': '2025-07-01T20:47:51.230205+00:00',
            'description': 'Python programming language'
        }
    }
    
    print("🔍 Testing UserSkill model instantiation...")
    
    # Test 1: Try with the real data
    try:
        print("\n1. Testing with real data from database:")
        user_skill = UserSkill(**real_data)
        print(f"   ✅ SUCCESS: Created UserSkill: {user_skill}")
        print(f"   Skill name: {user_skill.skill.name if user_skill.skill else 'None'}")
        return True
    except Exception as e:
        print(f"   ❌ FAILED: {e}")
        print(f"   Error type: {type(e)}")
        
        # Test 2: Try without the skill field
        try:
            print("\n2. Testing without skill field:")
            test_data = real_data.copy()
            test_data.pop('skill', None)
            user_skill = UserSkill(**test_data)
            print(f"   ✅ SUCCESS: Created UserSkill without skill: {user_skill}")
        except Exception as e2:
            print(f"   ❌ FAILED: {e2}")
        
        # Test 3: Try with string created_at
        try:
            print("\n3. Testing with string created_at:")
            test_data = real_data.copy()
            test_data['created_at'] = datetime.fromisoformat(test_data['created_at'].replace('Z', '+00:00'))
            user_skill = UserSkill(**test_data)
            print(f"   ✅ SUCCESS: Created UserSkill with datetime: {user_skill}")
        except Exception as e3:
            print(f"   ❌ FAILED: {e3}")
        
        return False

if __name__ == "__main__":
    print("🚀 UserSkill Model Test")
    print("=" * 50)
    
    if test_user_skill_model():
        print("\n✅ UserSkill model is working correctly!")
    else:
        print("\n❌ UserSkill model has issues!")
        sys.exit(1)