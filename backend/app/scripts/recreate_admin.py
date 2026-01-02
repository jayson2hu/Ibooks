import asyncio
import sys
import os

# Add parent directory to path
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from sqlalchemy import select, delete
from app.database import AsyncSessionLocal
from app.models.user import User
from app.utils.security import get_password_hash

async def recreate_admin():
    async with AsyncSessionLocal() as db:
        # Delete existing admin user
        print("Deleting existing admin user...")
        result = await db.execute(
            delete(User).where(User.email == "admin@example.com")
        )
        await db.commit()
        print(f"✓ Deleted {result.rowcount} user(s)")
        
        # Create new admin user with correct fields
        print("\nCreating new admin user...")
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
        await db.refresh(admin)
        
        print(f"✓ Created admin user:")
        print(f"  - Email: {admin.email}")
        print(f"  - Username: {admin.username}")
        print(f"  - Role: {admin.role}")
        print(f"  - Status: {admin.status}")
        print(f"  - Password: Admin123")

if __name__ == "__main__":
    asyncio.run(recreate_admin())
