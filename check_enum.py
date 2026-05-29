import asyncio
from sqlalchemy import text
from app.core.database import engine

async def check():
    async with engine.begin() as conn:
        r = await conn.execute(text(
            "SELECT enumlabel FROM pg_enum WHERE enumtypid = 'userrole'::regtype ORDER BY enumsortorder;"
        ))
        values = [row[0] for row in r.fetchall()]
        print("DB userrole enum values:", values)

asyncio.run(check())
