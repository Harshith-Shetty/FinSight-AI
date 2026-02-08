"""
Create test user in database.
"""

import asyncio
from sqlalchemy import text
from app.core.database import AsyncSessionLocal


async def create_test_user():
    async with AsyncSessionLocal() as session:
        # Create test user with fixed ID
        await session.execute(text("""
            INSERT INTO users (id, email, api_key_hash, created_at)
            VALUES ('00000000-0000-0000-0000-000000000001', 'test@finsight.ai', 'test_hash', NOW())
            ON CONFLICT (id) DO NOTHING
        """))
        await session.commit()
        print("✅ Test user created!")


if __name__ == "__main__":
    asyncio.run(create_test_user())
