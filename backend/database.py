"""
Database utilities with connection pooling, indexes, and optimization
"""
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, TEXT, IndexModel
import os
import logging

logger = logging.getLogger(__name__)

class Database:
    client: AsyncIOMotorClient = None
    db = None

async def get_database():
    """Get database instance with connection pooling"""
    mongo_url = os.environ.get('MONGO_URL')
    db_name = os.environ.get('DB_NAME', 'gyanmanjari_hrms')
    
    if Database.client is None:
        Database.client = AsyncIOMotorClient(
            mongo_url,
            maxPoolSize=50,  # Connection pool for high traffic
            minPoolSize=10,
            maxIdleTimeMS=45000,
            serverSelectionTimeoutMS=5000
        )
        Database.db = Database.client[db_name]
        logger.info(f"Connected to MongoDB: {db_name}")
        
        # Create indexes for performance
        await create_indexes()
    
    return Database.db

async def create_indexes():
    """Create database indexes for optimal query performance"""
    db = Database.db
    
    try:
        # Users collection indexes
        await db.users.create_indexes([
            IndexModel([("email", ASCENDING)], unique=True),
            IndexModel([("employee_id", ASCENDING)], unique=True),
            IndexModel([("role", ASCENDING)]),
            IndexModel([("assigned_centers", ASCENDING)]),
            IndexModel([("is_active", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)])
        ])
        
        # Centers collection indexes
        await db.centers.create_indexes([
            IndexModel([("name", TEXT)]),
            IndexModel([("center_admin_ids", ASCENDING)]),
            IndexModel([("created_at", DESCENDING)])
        ])
        
        # Attendance collection indexes
        await db.attendance.create_indexes([
            IndexModel([("user_id", ASCENDING), ("date", DESCENDING)]),
            IndexModel([("center_id", ASCENDING), ("date", DESCENDING)]),
            IndexModel([("date", DESCENDING)]),
            IndexModel([("check_in_time", DESCENDING)]),
            IndexModel([("user_id", ASCENDING), ("check_in_time", DESCENDING)])
        ])
        
        # Leaves collection indexes
        await db.leaves.create_indexes([
            IndexModel([("user_id", ASCENDING), ("applied_at", DESCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("center_id", ASCENDING), ("status", ASCENDING)]),
            IndexModel([("start_date", ASCENDING)]),
            IndexModel([("month_applied", ASCENDING), ("user_id", ASCENDING)])
        ])
        
        # Geofences collection indexes
        await db.geofences.create_indexes([
            IndexModel([("center_id", ASCENDING)]),
            IndexModel([("name", TEXT)])
        ])
        
        # Leave balances indexes
        await db.leave_balances.create_indexes([
            IndexModel([("user_id", ASCENDING), ("year", DESCENDING)], unique=True)
        ])
        
        # Payroll collection indexes
        await db.payroll_records.create_indexes([
            IndexModel([("employee_id", ASCENDING), ("month", DESCENDING)]),
            IndexModel([("status", ASCENDING)]),
            IndexModel([("generated_at", DESCENDING)])
        ])
        
        # Job postings indexes
        await db.job_postings.create_indexes([
            IndexModel([("status", ASCENDING)]),
            IndexModel([("department", ASCENDING)]),
            IndexModel([("title", TEXT)])
        ])
        
        # Candidates indexes
        await db.candidates.create_indexes([
            IndexModel([("email", ASCENDING)]),
            IndexModel([("job_id", ASCENDING)]),
            IndexModel([("current_status", ASCENDING)])
        ])
        
        logger.info("Database indexes created successfully")
        
    except Exception as e:
        logger.error(f"Error creating indexes: {e}")

async def close_database():
    """Close database connections"""
    if Database.client:
        Database.client.close()
        logger.info("Database connection closed")
