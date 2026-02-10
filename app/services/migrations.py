"""
Database migration service for automatic schema updates.
"""

import asyncio
from sqlalchemy import text

from app.core.database import AsyncSessionLocal, engine
from app.models.database import Base


async def run_migrations():
    """
    Run database migrations automatically on startup.
    Creates tables and updates schema as needed.
    """
    print("🔧 Running database migrations...")
    
    try:
        async with engine.begin() as conn:
            # Create all tables (idempotent - won't recreate existing tables)
            await conn.run_sync(Base.metadata.create_all)
            
            # Update users table - add new columns if they don't exist
            try:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN IF NOT EXISTS password_hash VARCHAR(255),
                    ADD COLUMN IF NOT EXISTS last_login TIMESTAMP;
                """))
            except Exception:
                pass  # Columns already exist
            
            # Make api_key_hash nullable
            try:
                await conn.execute(text("""
                    ALTER TABLE users 
                    ALTER COLUMN api_key_hash DROP NOT NULL;
                """))
            except Exception:
                pass  # Already nullable
        
        print("✅ Database migrations completed successfully")
        
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        raise


async def verify_database():
    """
    Verify database schema after migration.
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name;
            """))
            
            tables = [row[0] for row in result.fetchall()]
            expected_tables = ['users', 'analysis_tasks', 'documents', 'chats', 'messages']
            missing_tables = [t for t in expected_tables if t not in tables]
            
            if missing_tables:
                print(f"⚠️  Missing tables: {', '.join(missing_tables)}")
            else:
                print(f"✅ Database verified: {len(tables)} tables found")
                
    except Exception as e:
        print(f"⚠️  Database verification failed: {e}")
