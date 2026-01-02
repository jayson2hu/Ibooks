import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select
from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.security import get_password_hash

async def check_and_create_admin():
    async with AsyncSessionLocal() as db:
        # Check for ANY user
        result = await db.execute(select(User))
        users = result.scalars().all()
        
        print(f"Total users found: {len(users)}")
        for u in users:
            print(f"- {u.email} (Role: {u.role})")
            
        # Check for admin
        result = await db.execute(select(User).where(User.email == "admin@example.com"))
        admin = result.scalar_one_or_none()
        
        if not admin:
            print("\nCreating default admin user...")
            admin = User(
                email="admin@example.com",
                username="admin",
                password_hash=get_password_hash("Admin123"),
                role="admin",
                status="active",
                is_email_verified=True
            )
            db.add(admin)
            await db.commit()
            print("✓ Created admin user: admin@example.com / Admin123")
        else:
            print("\n✓ Admin user already exists.")

if __name__ == "__main__":
    asyncio.run(check_and_create_admin())
