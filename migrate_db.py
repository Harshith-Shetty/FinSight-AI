"""
Database migration script to add new tables for multi-mode chat system.
Run this to update the database schema.
"""

import asyncio
from sqlalchemy import text

from app.core.database import AsyncSessionLocal, engine
from app.models.database import Base


async def migrate_and_verify():
    """
    Create new tables, update existing ones, and verify.
    """
    print("=" * 60)
    print("FinSight AI - Database Migration")
    print("=" * 60)
    print("\n🔧 Starting database migration...")
    
    async with engine.begin() as conn:
        # Create all new tables
        await conn.run_sync(Base.metadata.create_all)
        print("✅ Created new tables (documents, chats, messages)")
        
        # Update users table - add new columns if they don't exist
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
                ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
            """))
            print("✅ Updated users table with new columns")
        except Exception as e:
            print(f"⚠️  Users table update: {e}")
        
        # Make api_key_hash nullable
        try:
            await conn.execute(text("""
                ALTER TABLE users 
                ALTER COLUMN api_key_hash DROP NOT NULL;
            """))
            print("✅ Made api_key_hash nullable")
        except Exception as e:
            print(f"⚠️  api_key_hash update: {e}")
            
        # Update chats table - add soft delete column
        try:
            await conn.execute(text("""
                ALTER TABLE chats 
                ADD COLUMN IF NOT EXISTS is_deleted BOOLEAN DEFAULT FALSE;
            """))
            print("✅ Updated chats table with is_deleted column")
        except Exception as e:
            print(f"⚠️  Chats table update: {e}")
    
    print("\n✅ Database migration completed!")
    
    # Verify migration
    print("\n🔍 Verifying migration...")
    
    async with AsyncSessionLocal() as session:
        # Check if tables exist
        result = await session.execute(text("""
            SELECT table_name 
            FROM information_schema.tables 
            WHERE table_schema = 'public'
            ORDER BY table_name;
        """))
        
        tables = [row[0] for row in result.fetchall()]
        print(f"\n📊 Existing tables: {', '.join(tables)}")
        
        expected_tables = ['users', 'analysis_tasks', 'documents', 'chats', 'messages']
        missing_tables = [t for t in expected_tables if t not in tables]
        
        if missing_tables:
            print(f"❌ Missing tables: {', '.join(missing_tables)}")
        else:
            print("✅ All required tables exist!")
    
    print("\n" + "=" * 60)
    print("Migration complete! You can now start the API server.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(migrate_and_verify())
