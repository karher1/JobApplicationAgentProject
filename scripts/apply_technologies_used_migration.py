#!/usr/bin/env python3
"""
Apply the technologies_used column migration
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
        migration_file = Path("database/migrations/add_technologies_used_column.sql")
        if not migration_file.exists():
            print(f"❌ Error: Migration file not found: {migration_file}")
            return False
        
        with open(migration_file, 'r') as f:
            migration_sql = f.read()
        
        print("🔧 Applying technologies_used column migration...")
        print(f"📁 Migration file: {migration_file}")
        
        # Execute the migration
        try:
            # For Supabase, we need to use the SQL editor or RPC function
            # This is a simple approach - just execute the SQL directly
            result = supabase.rpc('exec_sql', {'sql': migration_sql}).execute()
            print("✅ Migration applied successfully!")
            return True
        except Exception as e:
            # If RPC doesn't work, try direct SQL execution (this might not work in all cases)
            print(f"❌ Migration failed: {str(e)}")
            print("You may need to apply this migration manually in the Supabase SQL editor:")
            print(migration_sql)
            return False
            
    except Exception as e:
        print(f"❌ Error applying migration: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Technologies Used Column Migration")
    print("=" * 50)
    
    if apply_migration():
        print("\n✅ Migration completed successfully!")
    else:
        print("\n❌ Migration failed!")
        sys.exit(1)