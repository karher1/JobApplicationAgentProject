#!/usr/bin/env python3
"""
Test script for Module 8: Daily Digest Generator
Tests digest generation, email notifications, and scheduling functionality
"""

import asyncio
import json
import sys
import os
from datetime import datetime, date, timedelta
from uuid import UUID, uuid4

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from services.database_service import DatabaseService
from services.llm_service import LLMService
from services.vector_service import VectorService
from services.digest_service import DigestService
from models.digest import (
    DigestRequest, DigestType, DigestPreferences,
    GenerateDigestRequest, BatchDigestRequest
)

async def test_digest_service():
    """Test the digest service functionality"""
    print("🧪 Testing Module 8: Daily Digest Generator")
    print("=" * 50)
    
    try:
        # Initialize services
        print("📡 Initializing services...")
        db_service = DatabaseService()
        llm_service = LLMService()
        vector_service = VectorService()
        digest_service = DigestService(db_service, llm_service, vector_service)
        
        await db_service.initialize()
        await llm_service.initialize()
        await vector_service.initialize()
        
        print("✅ Services initialized successfully")
        
        # Test 1: Generate digest for a user
        print("\n🔍 Test 1: Generate Daily Digest")
        print("-" * 30)
        
        # Create a test user ID
        test_user_id = uuid4()
        
        # Create digest request
        digest_request = DigestRequest(
            user_id=test_user_id,
            digest_type=DigestType.DAILY,
            date=date.today(),
            include_job_matches=True,
            include_applications=True,
            include_insights=True,
            include_stats=True,
            max_job_matches=5,
            max_application_updates=3
        )
        
        print(f"📧 Generating digest for user: {test_user_id}")
        result = await digest_service.generate_digest(digest_request)
        
        if result.success:
            print("✅ Digest generated successfully!")
            print(f"   - Digest ID: {result.digest_id}")
            print(f"   - Email sent: {result.email_sent}")
            print(f"   - Generated at: {result.generated_at}")
            
            if result.content:
                print(f"   - Job matches: {len(result.content.job_matches)}")
                print(f"   - Application updates: {len(result.content.application_updates)}")
                print(f"   - Profile insights: {len(result.content.profile_insights)}")
                print(f"   - Top skills: {len(result.content.top_skills_in_demand)}")
                print(f"   - Trending companies: {len(result.content.trending_companies)}")
        else:
            print(f"❌ Digest generation failed: {result.error_message}")
        
        # Test 2: Get digest schedules
        print("\n📅 Test 2: Get Digest Schedules")
        print("-" * 30)
        
        schedules = await digest_service.get_digest_schedules()
        print(f"📋 Found {len(schedules)} active digest schedules")
        
        for schedule in schedules[:3]:  # Show first 3
            print(f"   - User: {schedule.get('name', 'Unknown')}")
            print(f"     Type: {schedule.get('digest_type')}")
            print(f"     Frequency: {schedule.get('frequency')}")
            print(f"     Next scheduled: {schedule.get('next_scheduled')}")
        
        # Test 3: Get digest statistics
        print("\n📊 Test 3: Get Digest Statistics")
        print("-" * 30)
        
        start_date = date.today() - timedelta(days=7)
        end_date = date.today()
        
        stats = await digest_service.get_digest_stats(start_date, end_date)
        print(f"📈 Digest statistics for {start_date} to {end_date}:")
        print(f"   - Total digests: {stats.get('total_digests', 0)}")
        print(f"   - Successful: {stats.get('successful_digests', 0)}")
        print(f"   - Failed: {stats.get('failed_digests', 0)}")
        print(f"   - Avg generation time: {stats.get('avg_generation_time', 0):.2f}s")
        
        # Test 4: Get user preferences
        print("\n⚙️ Test 4: Get User Preferences")
        print("-" * 30)
        
        preferences = await digest_service._get_user_preferences(test_user_id)
        print(f"📋 Preferences for user {test_user_id}:")
        print(f"   - Include job matches: {preferences.include_job_matches}")
        print(f"   - Include applications: {preferences.include_applications}")
        print(f"   - Include insights: {preferences.include_insights}")
        print(f"   - Include stats: {preferences.include_stats}")
        print(f"   - Max job matches: {preferences.max_job_matches}")
        print(f"   - Max application updates: {preferences.max_application_updates}")
        print(f"   - Notification frequency: {preferences.notification_frequency}")
        print(f"   - Preferred time: {preferences.preferred_time}")
        print(f"   - Timezone: {preferences.timezone}")
        
        # Test 5: Test email template generation
        print("\n📧 Test 5: Email Template Generation")
        print("-" * 30)
        
        try:
            template = await digest_service._get_email_template('daily_digest')
            print("✅ Email template retrieved successfully")
            print(f"   - Subject template: {template['subject_template'][:50]}...")
            print(f"   - HTML template length: {len(template['html_template'])} chars")
            print(f"   - Text template length: {len(template['text_template'])} chars")
        except Exception as e:
            print(f"❌ Error getting email template: {e}")
        
        # Test 6: Test job matching functionality
        print("\n🎯 Test 6: Job Matching")
        print("-" * 30)
        
        # Create sample job data
        sample_job = {
            'id': 'test_job_001',
            'title': 'Senior Software Engineer',
            'company': 'Tech Corp',
            'location': 'San Francisco, CA',
            'url': 'https://example.com/job/001',
            'created_at': datetime.now(),
            'job_description_id': 'desc_001'
        }
        
        # Create sample user profile
        sample_user_profile = {
            'name': 'Test User',
            'email': 'test@example.com',
            'title': 'Software Engineer',
            'skills': ['Python', 'JavaScript', 'React', 'AWS'],
            'experience': [
                {'description': '5 years of software development experience'}
            ]
        }
        
        # Create sample preferences
        sample_preferences = DigestPreferences(
            user_id=test_user_id,
            preferred_locations=['San Francisco', 'Remote'],
            preferred_job_types=['Full-time'],
            salary_range_min=80000,
            salary_range_max=150000
        )
        
        try:
            match_score, match_reasons = await digest_service._calculate_job_match(
                sample_job, sample_user_profile, sample_preferences
            )
            print(f"✅ Job match calculated successfully")
            print(f"   - Match score: {match_score:.2f}")
            print(f"   - Match reasons: {match_reasons}")
        except Exception as e:
            print(f"❌ Error calculating job match: {e}")
        
        # Test 7: Test profile insights generation
        print("\n💡 Test 7: Profile Insights")
        print("-" * 30)
        
        try:
            insights = await digest_service._generate_profile_insights(test_user_id)
            print(f"✅ Generated {len(insights)} profile insights")
            
            for insight in insights:
                print(f"   - {insight.title}: {insight.description}")
                print(f"     Priority: {insight.priority}, Action required: {insight.action_required}")
        except Exception as e:
            print(f"❌ Error generating profile insights: {e}")
        
        # Test 8: Test trending data
        print("\n🔥 Test 8: Trending Data")
        print("-" * 30)
        
        try:
            top_skills = await digest_service._get_top_skills_in_demand()
            trending_companies = await digest_service._get_trending_companies()
            
            print(f"✅ Retrieved trending data")
            print(f"   - Top skills: {', '.join(top_skills[:5])}")
            print(f"   - Trending companies: {', '.join(trending_companies[:5])}")
        except Exception as e:
            print(f"❌ Error getting trending data: {e}")
        
        print("\n🎉 All tests completed!")
        print("=" * 50)
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()

async def test_api_endpoints():
    """Test the FastAPI endpoints for digest functionality"""
    print("\n🌐 Testing API Endpoints")
    print("=" * 50)
    
    try:
        import httpx
        
        # Test API endpoints
        base_url = "http://localhost:8000"
        
        # Test 1: Generate digest
        print("🔍 Test 1: POST /api/v1/digest/generate")
        print("-" * 30)
        
        test_user_id = str(uuid4())
        request_data = {
            "user_id": test_user_id,
            "digest_type": "daily",
            "send_notification": False,  # Don't send actual email during test
            "custom_date": date.today().isoformat()
        }
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    f"{base_url}/api/v1/digest/generate",
                    json=request_data,
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    result = response.json()
                    print("✅ Digest generation API call successful")
                    print(f"   - Success: {result.get('success')}")
                    print(f"   - Digest ID: {result.get('digest_id')}")
                else:
                    print(f"❌ API call failed with status {response.status_code}")
                    print(f"   Response: {response.text}")
            except Exception as e:
                print(f"❌ API call failed: {e}")
        
        # Test 2: Get digest schedules
        print("\n📅 Test 2: GET /api/v1/digest/schedules")
        print("-" * 30)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{base_url}/api/v1/digest/schedules")
                
                if response.status_code == 200:
                    schedules = response.json()
                    print(f"✅ Retrieved {len(schedules)} digest schedules")
                else:
                    print(f"❌ API call failed with status {response.status_code}")
            except Exception as e:
                print(f"❌ API call failed: {e}")
        
        # Test 3: Get digest stats
        print("\n📊 Test 3: GET /api/v1/digest/stats")
        print("-" * 30)
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.get(f"{base_url}/api/v1/digest/stats")
                
                if response.status_code == 200:
                    stats = response.json()
                    print("✅ Retrieved digest statistics")
                    print(f"   - Total digests: {stats.get('total_digests', 0)}")
                else:
                    print(f"❌ API call failed with status {response.status_code}")
            except Exception as e:
                print(f"❌ API call failed: {e}")
        
        print("\n🎉 API endpoint tests completed!")
        
    except ImportError:
        print("⚠️ httpx not available, skipping API endpoint tests")
    except Exception as e:
        print(f"❌ API tests failed: {e}")

async def main():
    """Main test function"""
    print("🚀 Starting Module 8: Daily Digest Generator Tests")
    print("=" * 60)
    
    # Test service functionality
    await test_digest_service()
    
    # Test API endpoints (if server is running)
    await test_api_endpoints()
    
    print("\n✨ All Module 8 tests completed!")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main()) 