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
    print("Running database migrations...")
    
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
            
            # Fix chatmode enum to use UPPERCASE values (matching Python code)
            try:
                print("  - Checking chatmode enum values...")
                result = await conn.execute(text("""
                    SELECT enumlabel FROM pg_enum 
                    WHERE enumtypid = 'chatmode'::regtype 
                    ORDER BY enumsortorder;
                """))
                enum_values = [row[0] for row in result.fetchall()]
                
                if 'hybrid' in enum_values or 'private' in enum_values:
                    print("  - Fixing chatmode to UPPERCASE...")
                    await conn.execute(text("ALTER TABLE chats ALTER COLUMN mode TYPE VARCHAR(20);"))
                    await conn.execute(text("DROP TYPE chatmode;"))
                    await conn.execute(text("CREATE TYPE chatmode AS ENUM ('HYBRID', 'PRIVATE');"))
                    await conn.execute(text("ALTER TABLE chats ALTER COLUMN mode TYPE chatmode USING UPPER(mode)::chatmode;"))
                    print("  Chatmode enum fixed to UPPERCASE")
            except Exception:
                pass

        print("Database migrations completed successfully")
        
    except Exception as e:
        print(f"Migration failed: {e}")
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
                print(f"WARNING: Missing tables: {', '.join(missing_tables)}")
            else:
                print(f"Database verified: {len(tables)} tables found")
                
    except Exception as e:
        print(f"WARNING: Database verification failed: {e}")
