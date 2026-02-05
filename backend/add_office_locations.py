"""
Add AMD and BHV office locations to Gyanmanjari HRMS
"""
import asyncio
from motor.motor_asyncio import AsyncIOMotorClient
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import datetime

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

async def add_office_locations():
    # Connect to MongoDB
    mongo_url = os.environ['MONGO_URL']
    client = AsyncIOMotorClient(mongo_url)
    db = client[os.environ.get('DB_NAME', 'hrms_db')]
    
    print("🏢 Adding Gyanmanjari Office Locations...")
    
    # 1. AMD Office (Ahmedabad)
    amd_office = {
        "name": "AMD Office - Ahmedabad",
        "address": "Ahmedabad, Gujarat, India",
        "contact": "+91 79 1234 5678",
        "geofences": [
            {
                "id": "amd-main-gate",
                "name": "AMD Office - Main Entrance",
                "latitude": 23.113313,
                "longitude": 72.540281,
                "radius": 100.0,
                "description": "Main gate geofence with 100m radius"
            },
            {
                "id": "amd-parking",
                "name": "AMD Office - Parking Area",
                "latitude": 23.113413,
                "longitude": 72.540381,
                "radius": 50.0,
                "description": "Parking area geofence"
            }
        ],
        "holidays": [
            {
                "date": "2025-08-15",
                "type": "public",
                "description": "Independence Day"
            },
            {
                "date": "2025-10-02",
                "type": "public",
                "description": "Gandhi Jayanti"
            }
        ],
        "center_admin_ids": [],
        "created_at": datetime.utcnow(),
        "employee_count": 0,
        "city": "Ahmedabad",
        "state": "Gujarat",
        "timezone": "Asia/Kolkata"
    }
    
    # Check if AMD office already exists
    existing_amd = await db.centers.find_one({"name": "AMD Office - Ahmedabad"})
    if not existing_amd:
        result = await db.centers.insert_one(amd_office)
        print(f"✅ AMD Office created with ID: {result.inserted_id}")
        print(f"   📍 Location: 23.113313, 72.540281")
        print(f"   🎯 Geofences: {len(amd_office['geofences'])}")
    else:
        print("ℹ️  AMD Office already exists")
    
    # 2. BHV HO Office (Bhavnagar)
    bhv_office = {
        "name": "BHV HO Office - Bhavnagar",
        "address": "Head Office, Bhavnagar, Gujarat, India",
        "contact": "+91 278 1234 5678",
        "geofences": [
            {
                "id": "bhv-main-gate",
                "name": "BHV HO - Main Entrance",
                "latitude": 21.718829,
                "longitude": 72.121830,
                "radius": 150.0,
                "description": "Head office main entrance with 150m radius"
            },
            {
                "id": "bhv-reception",
                "name": "BHV HO - Reception Area",
                "latitude": 21.718729,
                "longitude": 72.121730,
                "radius": 75.0,
                "description": "Reception area geofence"
            }
        ],
        "holidays": [
            {
                "date": "2025-08-15",
                "type": "public",
                "description": "Independence Day"
            },
            {
                "date": "2025-10-02",
                "type": "public",
                "description": "Gandhi Jayanti"
            },
            {
                "date": "2025-03-14",
                "type": "public",
                "description": "Holi"
            }
        ],
        "center_admin_ids": [],
        "created_at": datetime.utcnow(),
        "employee_count": 0,
        "city": "Bhavnagar",
        "state": "Gujarat",
        "timezone": "Asia/Kolkata"
    }
    
    # Check if BHV office already exists
    existing_bhv = await db.centers.find_one({"name": "BHV HO Office - Bhavnagar"})
    if not existing_bhv:
        result = await db.centers.insert_one(bhv_office)
        print(f"✅ BHV HO Office created with ID: {result.inserted_id}")
        print(f"   📍 Location: 21.718829, 72.121830")
        print(f"   🎯 Geofences: {len(bhv_office['geofences'])}")
    else:
        print("ℹ️  BHV HO Office already exists")
    
    # Summary
    print("\n📊 Summary:")
    total_centers = await db.centers.count_documents({})
    print(f"   Total Centers: {total_centers}")
    
    all_centers = await db.centers.find().to_list(100)
    for center in all_centers:
        print(f"   - {center['name']}: {len(center.get('geofences', []))} geofences")
    
    print("\n🎉 Office locations setup complete!")
    print("\n📱 Test in app:")
    print("   1. Login as Super Admin")
    print("   2. Go to Centers tab")
    print("   3. You should see both offices listed")
    print("   4. Go to Attendance and check-in from these locations")
    
    client.close()

if __name__ == "__main__":
    asyncio.run(add_office_locations())
