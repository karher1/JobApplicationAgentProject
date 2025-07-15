#!/usr/bin/env python3
"""
Database Migration Script
Applies the fix_missing_tables.sql migration to the Supabase database
"""

import os
import sys
from pathlib import Path
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def apply_migration():
    """Apply the database migration"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        # Read migration file
        migration_file = Path("database/migrations/fix_missing_tables.sql")
        if not migration_file.exists():
            print(f"❌ Error: Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("🔧 Applying database migration...")
        print(f"📁 Migration file: {migration_file}")
        
        # Split SQL into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        success_count = 0
        error_count = 0
        
        for i, statement in enumerate(statements, 1):
            if not statement or statement.startswith('--'):
                continue
                
            try:
                print(f"   Executing statement {i}/{len(statements)}...")
                # Execute the SQL statement
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                success_count += 1
                print(f"   ✅ Statement {i} executed successfully")
            except Exception as e:
                error_count += 1
                print(f"   ❌ Statement {i} failed: {str(e)}")
                # Continue with other statements
                continue
        
        print(f"\n📊 Migration Summary:")
        print(f"   ✅ Successful statements: {success_count}")
        print(f"   ❌ Failed statements: {error_count}")
        print(f"   📝 Total statements: {len(statements)}")
        
        if error_count == 0:
            print("🎉 Migration completed successfully!")
            return True
        else:
            print("⚠️  Migration completed with some errors. Check the output above.")
            return False
            
    except Exception as e:
        print(f"❌ Error applying migration: {str(e)}")
        return False

def test_database_connection():
    """Test database connection and basic operations"""
    try:
        # Get Supabase credentials
        supabase_url = os.getenv("SUPABASE_URL")
        supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY") or os.getenv("SUPABASE_ANON_KEY")
        
        if not supabase_url or not supabase_key:
            print("❌ Error: SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY or SUPABASE_ANON_KEY must be set")
            return False
        
        # Create Supabase client
        supabase: Client = create_client(supabase_url, supabase_key)
        
        print("🔍 Testing database connection...")
        
        # Test basic operations
        try:
            # Test users table
            result = supabase.table("users").select("id").limit(1).execute()
            print("   ✅ Users table accessible")
        except Exception as e:
            print(f"   ❌ Users table error: {str(e)}")
        
        try:
            # Test user_preferences table (should exist after migration)
            result = supabase.table("user_preferences").select("id").limit(1).execute()
            print("   ✅ User preferences table accessible")
        except Exception as e:
            print(f"   ❌ User preferences table error: {str(e)}")
        
        try:
            # Test skills table (should exist after migration)
            result = supabase.table("skills").select("id").limit(1).execute()
            print("   ✅ Skills table accessible")
        except Exception as e:
            print(f"   ❌ Skills table error: {str(e)}")
        
        try:
            # Test jobs table (should exist after migration)
            result = supabase.table("jobs").select("id").limit(1).execute()
            print("   ✅ Jobs table accessible")
        except Exception as e:
            print(f"   ❌ Jobs table error: {str(e)}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing database connection: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Database Migration Tool")
    print("=" * 50)
    
    # Test connection first
    if test_database_connection():
        print("\n✅ Database connection successful")
        
        # Apply migration
        if apply_migration():
            print("\n✅ Migration completed successfully!")
            
            # Test connection again
            print("\n🔍 Testing database after migration...")
            test_database_connection()
        else:
            print("\n❌ Migration failed!")
            sys.exit(1)
    else:
        print("\n❌ Database connection failed!")
        sys.exit(1) 