"""
Seed script to populate initial data for HRMS
Run this to create:
- Default geofence location
- Sample admin user
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
from passlib.context import CryptContext
import os
from dotenv import load_dotenv
from pathlib import Path

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

async def seed_database():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'hrms_db')]
    
    print("🌱 Starting database seeding...")
    
    # Create default geofence
    existing_geofence = await db.geofences.find_one({"name": "Main Office"})
    if not existing_geofence:
        geofence = {
            "name": "Main Office",
            "latitude": 28.6139,  # Delhi coordinates (example)
            "longitude": 77.2090,
            "radius": 100.0,
            "address": "Main Office, Delhi",
            "created_at": None
        }
        await db.geofences.insert_one(geofence)
        print("✅ Created default geofence: Main Office")
    else:
        print("ℹ️  Geofence already exists")
    
    # Create admin user
    existing_admin = await db.users.find_one({"email": "admin@hrms.com"})
    if not existing_admin:
        admin_user = {
            "email": "admin@hrms.com",
            "password": pwd_context.hash("admin123"),
            "full_name": "Admin User",
            "employee_id": "EMP001",
            "role": "super_admin",
            "department": "IT",
            "designation": "System Administrator",
            "is_active": True,
            "created_at": None
        }
        result = await db.users.insert_one(admin_user)
        
        # Create leave balance for admin
        leave_balance = {
            "user_id": str(result.inserted_id),
            "sick_balance": 12.0,
            "casual_balance": 12.0,
            "earned_balance": 18.0,
            "year": 2025
        }
        await db.leave_balances.insert_one(leave_balance)
        print("✅ Created admin user: admin@hrms.com / admin123")
    else:
        print("ℹ️  Admin user already exists")
    
    # Create sample employee
    existing_emp = await db.users.find_one({"email": "employee@hrms.com"})
    if not existing_emp:
        employee = {
            "email": "employee@hrms.com",
            "password": pwd_context.hash("employee123"),
            "full_name": "John Doe",
            "employee_id": "EMP002",
            "role": "employee",
            "department": "Engineering",
            "designation": "Software Developer",
            "is_active": True,
            "created_at": None
        }
        result = await db.users.insert_one(employee)
        
        # Create leave balance
        leave_balance = {
            "user_id": str(result.inserted_id),
            "sick_balance": 12.0,
            "casual_balance": 12.0,
            "earned_balance": 18.0,
            "year": 2025
        }
        await db.leave_balances.insert_one(leave_balance)
        print("✅ Created sample employee: employee@hrms.com / employee123")
    else:
        print("ℹ️  Sample employee already exists")
    
    print("🎉 Database seeding completed!")
    client.close()

if __name__ == "__main__":
    asyncio.run(seed_database())
