"""
Initialize database tables and create test user.
Run this script once to set up the database.
"""

import asyncio
from app.core.database import init_db, AsyncSessionLocal
from app.models.database import User
from uuid import uuid4


async def main():
    print("🔧 Creating database tables...")
    await init_db()
    print("✅ Database tables created!")
    
    # Create a test user
    print("👤 Creating test user...")
    async with AsyncSessionLocal() as session:
        test_user = User(
            id=uuid4(),
            email="test@finsight.ai",
            api_key_hash="test_hash_123"
        )
        session.add(test_user)
        await session.commit()
        print(f"✅ Test user created: {test_user.email} (ID: {test_user.id})")
        print(f"\n💡 Use this user_id in your code: {test_user.id}")


if __name__ == "__main__":
    asyncio.run(main())
