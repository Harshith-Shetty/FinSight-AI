"""
Fix ChatMode enum in database to use lowercase values.
"""
import asyncio
import asyncpg
from app.core.config import settings

async def fix_chatmode_enum():
    """Fix the chatmode enum to use lowercase values."""
    
    # Connect to database
    db_url = settings.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    conn = await asyncpg.connect(db_url)
    
    try:
        print("Fixing chatmode enum...")
        
        # Step 1: Change column to VARCHAR temporarily
        print("1. Converting mode column to VARCHAR...")
        await conn.execute("ALTER TABLE chats ALTER COLUMN mode TYPE VARCHAR(20);")
        
        # Step 2: Drop old enum
        print("2. Dropping old chatmode enum...")
        await conn.execute("DROP TYPE IF EXISTS chatmode;")
        
        # Step 3: Create new enum with lowercase values
        print("3. Creating new chatmode enum with lowercase values...")
        await conn.execute("CREATE TYPE chatmode AS ENUM ('HYBRID', 'private');")
        
        # Step 4: Convert column back to enum
        print("4. Converting mode column back to chatmode enum...")
        await conn.execute("ALTER TABLE chats ALTER COLUMN mode TYPE chatmode USING mode::chatmode;")
        
        print("✅ ChatMode enum fixed successfully!")
        
    except Exception as e:
        print(f"❌ Error: {e}")
        raise
    finally:
        await conn.close()

if __name__ == "__main__":
    asyncio.run(fix_chatmode_enum())
