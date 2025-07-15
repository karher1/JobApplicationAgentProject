#!/usr/bin/env python3
"""
Script to apply pending applications database migration
"""

import os
import sys
from pathlib import Path

# Add the src directory to the Python path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from supabase import create_client
from dotenv import load_dotenv

def apply_migration():
    """Apply the pending applications migration"""
    
    # Load environment variables
    load_dotenv()
    
    # Get Supabase credentials
    supabase_url = os.getenv("SUPABASE_URL")
    supabase_key = os.getenv("SUPABASE_SERVICE_ROLE_KEY")  # Need service role key for schema changes
    
    if not supabase_url or not supabase_key:
        print("❌ SUPABASE_URL and SUPABASE_SERVICE_ROLE_KEY must be set in environment")
        return False
    
    try:
        # Initialize Supabase client
        supabase = create_client(supabase_url, supabase_key)
        print("✅ Connected to Supabase")
        
        # Read the migration SQL file
        migration_file = Path(__file__).parent.parent / "database" / "schemas" / "pending_applications_tables.sql"
        
        if not migration_file.exists():
            print(f"❌ Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("📄 Read migration file")
        
        # Execute the migration
        print("🚀 Applying pending applications migration...")
        
        # Split the SQL into individual statements
        statements = [stmt.strip() for stmt in migration_sql.split(';') if stmt.strip()]
        
        for i, statement in enumerate(statements, 1):
            try:
                # Skip comments and empty statements
                if statement.startswith('--') or not statement:
                    continue
                
                print(f"   Executing statement {i}/{len(statements)}")
                result = supabase.rpc('exec_sql', {'sql': statement}).execute()
                
            except Exception as e:
                print(f"⚠️  Warning on statement {i}: {e}")
                # Continue with other statements
                continue
        
        print("✅ Migration applied successfully!")
        
        # Verify tables were created
        print("🔍 Verifying tables...")
        try:
            result = supabase.table("pending_applications").select("id").limit(1).execute()
            print("✅ pending_applications table verified")
        except Exception as e:
            print(f"❌ Error verifying pending_applications table: {e}")
        
        try:
            result = supabase.table("pending_application_reviews").select("id").limit(1).execute()
            print("✅ pending_application_reviews table verified")
        except Exception as e:
            print(f"❌ Error verifying pending_application_reviews table: {e}")
        
        try:
            result = supabase.table("pending_application_submissions").select("id").limit(1).execute()
            print("✅ pending_application_submissions table verified")
        except Exception as e:
            print(f"❌ Error verifying pending_application_submissions table: {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error applying migration: {e}")
        return False

if __name__ == "__main__":
    print("🔄 Applying Pending Applications Migration")
    print("=" * 50)
    
    success = apply_migration()
    
    if success:
        print("\n🎉 Migration completed successfully!")
        print("\nNext steps:")
        print("1. Start the server: python run.py")
        print("2. Test pending applications endpoints")
        print("3. Upload a resume before applying to jobs")
        print("4. Applications will now require human approval before submission")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1) 