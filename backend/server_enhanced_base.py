from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, File, UploadFile
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from typing import List, Optional
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from bson import ObjectId
import base64
import math

# Import our custom modules
from models import *
from database import get_database, create_indexes, close_database
from leave_engine import LeaveRuleEngine
from payroll_engine import PayrollEngine

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('SECRET_KEY', 'gyanmanjari-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Initialize engines (will be set in startup)
leave_engine = None
payroll_engine = None

# Create the main app
app = FastAPI(title="Gyanmanjari HRMS API", version="2.0.0")
api_router = APIRouter(prefix="/api")

# Helper functions
def hash_password(password: str) -> str:
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def create_access_token(data: dict) -> str:
    to_encode = data.copy()
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

async def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)):
    try:
        token = credentials.credentials
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
        user_id = payload.get("sub")
        if user_id is None:
            raise HTTPException(status_code=401, detail="Invalid token")
        
        db = await get_database()
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        
        user["_id"] = str(user["_id"])
        user["id"] = str(user["_id"]) if "_id" in user else user.get("id")
        
        # Add assigned_centers if not present
        if "assigned_centers" not in user:
            user["assigned_centers"] = []
        if "profile_locked" not in user:
            user["profile_locked"] = False
            
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

def calculate_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance between two points in meters using Haversine formula"""
    R = 6371000  # Earth's radius in meters
    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    
    a = math.sin(delta_phi/2)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

# ============ STARTUP & SHUTDOWN ============

@app.on_event("startup")
async def startup_event():
    """Initialize database and engines"""
    global leave_engine, payroll_engine
    
    db = await get_database()
    leave_engine = LeaveRuleEngine(db)
    payroll_engine = PayrollEngine(db)
    
    logging.info("✅ Gyanmanjari HRMS started successfully")
    logging.info("✅ Database indexes created")
    logging.info("✅ Leave engine initialized")
    logging.info("✅ Payroll engine initialized")

@app.on_event("shutdown")
async def shutdown_event():
    await close_database()
    logging.info("Database connection closed")

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister):
    db = await get_database()
    
    # Check if user exists
    existing_user = await db.users.find_one({"email": user_data.email})
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered")
    
    existing_emp = await db.users.find_one({"employee_id": user_data.employee_id})
    if existing_emp:
        raise HTTPException(status_code=400, detail="Employee ID already exists")
    
    # Create user
    user_dict = user_data.dict()
    user_dict["password"] = hash_password(user_data.password)
    user_dict["is_active"] = True
    user_dict["created_at"] = datetime.utcnow()
    user_dict["assigned_centers"] = []
    user_dict["profile_locked"] = False
    user_dict["base_salary"] = 30000  # Default, to be set by admin
    
    result = await db.users.insert_one(user_dict)
    
    # Initialize leave balance
    leave_balance = {
        "user_id": str(result.inserted_id),
        "sick_balance": 12.0,
        "casual_balance": 12.0,
        "earned_balance": 18.0,
        "marriage_balance": 0.0,
        "bereavement_balance": 0.0,
        "year": datetime.utcnow().year
    }
    await db.leave_balances.insert_one(leave_balance)
    
    user_dict["id"] = str(result.inserted_id)
    del user_dict["password"]
    del user_dict["_id"]
    
    return UserResponse(**user_dict)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
    db = await get_database()
    user = await db.users.find_one({"email": credentials.email})
    
    if not user or not verify_password(credentials.password, user["password"]):
        raise HTTPException(status_code=401, detail="Invalid credentials")
    
    if not user.get("is_active", True):
        raise HTTPException(status_code=403, detail="Account is inactive")
    
    # Create token
    token = create_access_token({"sub": str(user["_id"]), "email": user["email"]})
    
    user_response = {
        "id": str(user["_id"]),
        "email": user["email"],
        "full_name": user["full_name"],
        "employee_id": user["employee_id"],
        "role": user["role"],
        "department": user.get("department"),
        "designation": user.get("designation"),
        "manager_id": user.get("manager_id"),
        "is_active": user["is_active"],
        "created_at": user["created_at"],
        "assigned_centers": user.get("assigned_centers", []),
        "primary_center": user.get("primary_center"),
        "profile_locked": user.get("profile_locked", False)
    }
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(**user_response)
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ============ CENTER MANAGEMENT ROUTES ============

@api_router.post("/centers", response_model=CenterResponse)
async def create_center(center: CenterCreate, current_user: dict = Depends(get_current_user)):
    """Create a new center - Super Admin only"""
    if current_user["role"] != UserRole.SUPER_ADMIN:
        raise HTTPException(status_code=403, detail="Only Super Admin can create centers")
    
    db = await get_database()
    
    center_dict = center.dict()
    center_dict["created_at"] = datetime.utcnow()
    center_dict["center_admin_ids"] = []
    center_dict["employee_count"] = 0
    
    result = await db.centers.insert_one(center_dict)
    center_dict["id"] = str(result.inserted_id)
    del center_dict["_id"]
    
    return CenterResponse(**center_dict)

@api_router.get("/centers", response_model=List[CenterResponse])
async def get_centers(current_user: dict = Depends(get_current_user)):
    """Get all centers or centers accessible to current user"""
    db = await get_database()
    
    if current_user["role"] == UserRole.SUPER_ADMIN:
        # Super admin sees all centers
        centers = await db.centers.find().to_list(1000)
    elif current_user["role"] == UserRole.CENTER_ADMIN:
        # Center admin sees only their assigned centers
        centers = await db.centers.find({
            "center_admin_ids": current_user["id"]
        }).to_list(1000)
    else:
        # Employees see their assigned centers
        centers = await db.centers.find({
            "_id": {"$in": [ObjectId(cid) for cid in current_user.get("assigned_centers", [])]}
        }).to_list(1000)
    
    result = []
    for center in centers:
        # Count employees
        emp_count = await db.users.count_documents({
            "assigned_centers": str(center["_id"])
        })
        
        center["id"] = str(center["_id"])
        center["employee_count"] = emp_count
        del center["_id"]
        result.append(CenterResponse(**center))
    
    return result

@api_router.post("/employees/assign-centers")
async def assign_centers_to_employee(
    assignment: AssignCentersRequest,
    current_user: dict = Depends(get_current_user)
):
    """Assign multiple centers to an employee"""
    if current_user["role"] not in [UserRole.SUPER_ADMIN, UserRole.HR_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    db = await get_database()
    
    # Validate centers exist
    for center_id in assignment.center_ids:
        center = await db.centers.find_one({"_id": ObjectId(center_id)})
        if not center:
            raise HTTPException(status_code=404, detail=f"Center {center_id} not found")
    
    # Update user
    await db.users.update_one(
        {"_id": ObjectId(assignment.employee_id)},
        {
            "$set": {
                "assigned_centers": assignment.center_ids,
                "primary_center": assignment.primary_center_id
            }
        }
    )
    
    return {"message": "Centers assigned successfully"}

@api_router.get("/centers/{center_id}/employees")
async def get_center_employees(center_id: str, current_user: dict = Depends(get_current_user)):
    """Get all employees assigned to a center"""
    db = await get_database()
    
    # Check authorization
    if current_user["role"] not in [UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.CENTER_ADMIN]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    employees = await db.users.find({
        "assigned_centers": center_id
    }).to_list(1000)
    
    result = []
    for emp in employees:
        emp["id"] = str(emp["_id"])
        del emp["_id"]
        del emp["password"]
        result.append(emp)
    
    return result

# ============ ENHANCED ATTENDANCE ROUTES ============

@api_router.post("/attendance/checkin")
async def check_in(checkin_data: CheckInRequest, current_user: dict = Depends(get_current_user)):
    """Enhanced check-in with multi-center support"""
    db = await get_database()
    
    # Check if already checked in today
    today = datetime.utcnow().date().isoformat()
    existing = await db.attendance.find_one({
        "user_id": current_user["id"],
        "date": today
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    # Validate user is assigned to this center
    if checkin_data.center_id not in current_user.get("assigned_centers", []):
        raise HTTPException(status_code=400, detail="You are not assigned to this center")
    
    # Validate geofence
    center = await db.centers.find_one({"_id": ObjectId(checkin_data.center_id)})
    if not center:
        raise HTTPException(status_code=404, detail="Center not found")
    
    # Find the specific geofence
    geofence = None
    for gf in center.get("geofences", []):
        if str(gf.get("_id", gf.get("id"))) == checkin_data.geofence_id:
            geofence = gf
            break
    
    if not geofence:
        raise HTTPException(status_code=404, detail="Geofence not found")
    
    # Check if within geofence radius
    distance = calculate_distance(
        checkin_data.latitude,
        checkin_data.longitude,
        geofence["latitude"],
        geofence["longitude"]
    )
    
    if distance > geofence["radius"]:
        raise HTTPException(
            status_code=400,
            detail=f"Outside geofence boundary. You are {int(distance)}m away, allowed radius is {int(geofence['radius'])}m"
        )
    
    # Save selfie to file system (or will be S3 later)
    selfie_path = f"/app/backend/uploads/selfies/{current_user['id']}_{today}.jpg"
    os.makedirs(os.path.dirname(selfie_path), exist_ok=True)
    
    try:
        selfie_data = base64.b64decode(checkin_data.selfie_base64.split(',')[-1])
        with open(selfie_path, 'wb') as f:
            f.write(selfie_data)
    except:
        # If save fails, use base64 directly
        selfie_path = checkin_data.selfie_base64[:100] + "..."
    
    # Create attendance record
    attendance = {
        "user_id": current_user["id"],
        "user_name": current_user["full_name"],
        "center_id": checkin_data.center_id,
        "center_name": center["name"],
        "check_in_time": datetime.utcnow(),
        "check_in_location": {
            "latitude": checkin_data.latitude,
            "longitude": checkin_data.longitude,
            "distance_from_center": distance
        },
        "selfie_url": selfie_path,
        "status": "present",
        "geofence_id": checkin_data.geofence_id,
        "date": today
    }
    
    result = await db.attendance.insert_one(attendance)
    attendance["id"] = str(result.inserted_id)
    
    return {"message": "Checked in successfully", "attendance_id": str(result.inserted_id)}

@api_router.post("/attendance/checkout")
async def check_out(checkout_data: CheckOutRequest, current_user: dict = Depends(get_current_user)):
    db = await get_database()
    today = datetime.utcnow().date().isoformat()
    attendance = await db.attendance.find_one({
        "user_id": current_user["id"],
        "date": today
    })
    
    if not attendance:
        raise HTTPException(status_code=404, detail="No check-in found for today")
    
    if attendance.get("check_out_time"):
        raise HTTPException(status_code=400, detail="Already checked out")
    
    # Update with checkout info
    await db.attendance.update_one(
        {"_id": attendance["_id"]},
        {
            "$set": {
                "check_out_time": datetime.utcnow(),
                "check_out_location": {
                    "latitude": checkout_data.latitude,
                    "longitude": checkout_data.longitude
                }
            }
        }
    )
    
    return {"message": "Checked out successfully"}

@api_router.get("/attendance/my-history")
async def get_my_attendance(current_user: dict = Depends(get_current_user), limit: int = 30):
    db = await get_database()
    attendance_records = await db.attendance.find(
        {"user_id": current_user["id"]}
    ).sort("check_in_time", -1).limit(limit).to_list(limit)
    
    result = []
    for record in attendance_records:
        record["id"] = str(record["_id"])
        del record["_id"]
        result.append(record)
    
    return result

@api_router.get("/attendance/today-status")
async def get_today_status(current_user: dict = Depends(get_current_user)):
    db = await get_database()
    today = datetime.utcnow().date().isoformat()
    attendance = await db.attendance.find_one({
        "user_id": current_user["id"],
        "date": today
    })
    
    if not attendance:
        return {"checked_in": False, "checked_out": False}
    
    return {
        "checked_in": True,
        "checked_out": attendance.get("check_out_time") is not None,
        "check_in_time": attendance.get("check_in_time").isoformat() if attendance.get("check_in_time") else None,
        "check_out_time": attendance.get("check_out_time").isoformat() if attendance.get("check_out_time") else None,
        "center_name": attendance.get("center_name")
    }

