from fastapi import FastAPI, APIRouter, HTTPException, Depends, status, WebSocket, WebSocketDisconnect
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from dotenv import load_dotenv
from starlette.middleware.cors import CORSMiddleware
from motor.motor_asyncio import AsyncIOMotorClient
import os
import logging
from pathlib import Path
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
import uuid
from datetime import datetime, timedelta
from passlib.context import CryptContext
import jwt
from bson import ObjectId
import json
import base64

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

# MongoDB connection
mongo_url = os.environ['MONGO_URL']
client = AsyncIOMotorClient(mongo_url)
db = client[os.environ.get('DB_NAME', 'hrms_db')]

# Security
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer()
SECRET_KEY = os.environ.get('SECRET_KEY', 'your-secret-key-change-in-production')
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

# Create the main app
app = FastAPI(title="HRMS API")
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
        user = await db.users.find_one({"_id": ObjectId(user_id)})
        if user is None:
            raise HTTPException(status_code=401, detail="User not found")
        user["id"] = str(user["_id"])
        del user["_id"]
        return user
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

# ============ MODELS ============

# User Models
class UserRole:
    SUPER_ADMIN = "super_admin"
    HR_MANAGER = "hr_manager"
    REPORTING_MANAGER = "reporting_manager"
    EMPLOYEE = "employee"

class UserRegister(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    employee_id: str
    role: str = UserRole.EMPLOYEE
    department: Optional[str] = None
    designation: Optional[str] = None
    manager_id: Optional[str] = None

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserResponse(BaseModel):
    id: str
    email: str
    full_name: str
    employee_id: str
    role: str
    department: Optional[str] = None
    designation: Optional[str] = None
    manager_id: Optional[str] = None
    is_active: bool
    created_at: datetime

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

# GeoFence Models
class GeoFence(BaseModel):
    name: str
    latitude: float
    longitude: float
    radius: float = 100.0  # meters
    address: Optional[str] = None

class GeoFenceResponse(BaseModel):
    id: str
    name: str
    latitude: float
    longitude: float
    radius: float
    address: Optional[str] = None
    created_at: datetime

# Attendance Models
class CheckInRequest(BaseModel):
    latitude: float
    longitude: float
    selfie_base64: str
    geofence_id: str

class CheckOutRequest(BaseModel):
    latitude: float
    longitude: float

class AttendanceResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    check_in_location: Dict
    check_out_location: Optional[Dict] = None
    selfie_base64: str
    status: str  # present, half_day, absent
    geofence_id: str
    date: str

# Location Tracking Models
class LocationUpdate(BaseModel):
    latitude: float
    longitude: float
    timestamp: datetime = Field(default_factory=datetime.utcnow)

class LocationHistoryResponse(BaseModel):
    id: str
    user_id: str
    locations: List[Dict]
    date: str

# Leave Models
class LeaveType:
    SICK = "sick"
    CASUAL = "casual"
    EARNED = "earned"

class LeaveStatus:
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"

class LeaveRequest(BaseModel):
    leave_type: str
    start_date: str
    end_date: str
    reason: str
    days_count: float

class LeaveApproval(BaseModel):
    leave_id: str
    status: str  # approved or rejected
    remarks: Optional[str] = None

class LeaveResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    leave_type: str
    start_date: str
    end_date: str
    reason: str
    days_count: float
    status: str
    remarks: Optional[str] = None
    applied_at: datetime
    approved_by: Optional[str] = None
    approved_at: Optional[datetime] = None

class LeaveBalance(BaseModel):
    user_id: str
    sick_balance: float = 12.0
    casual_balance: float = 12.0
    earned_balance: float = 18.0

# ============ AUTH ROUTES ============

@api_router.post("/auth/register", response_model=UserResponse)
async def register(user_data: UserRegister):
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
    
    result = await db.users.insert_one(user_dict)
    
    # Initialize leave balance
    leave_balance = {
        "user_id": str(result.inserted_id),
        "sick_balance": 12.0,
        "casual_balance": 12.0,
        "earned_balance": 18.0,
        "year": datetime.utcnow().year
    }
    await db.leave_balances.insert_one(leave_balance)
    
    user_dict["id"] = str(result.inserted_id)
    del user_dict["password"]
    del user_dict["_id"]
    
    return UserResponse(**user_dict)

@api_router.post("/auth/login", response_model=TokenResponse)
async def login(credentials: UserLogin):
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
        "created_at": user["created_at"]
    }
    
    return TokenResponse(
        access_token=token,
        user=UserResponse(**user_response)
    )

@api_router.get("/auth/me", response_model=UserResponse)
async def get_me(current_user: dict = Depends(get_current_user)):
    return UserResponse(**current_user)

# ============ GEOFENCE ROUTES ============

@api_router.post("/geofences", response_model=GeoFenceResponse)
async def create_geofence(geofence: GeoFence, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in [UserRole.SUPER_ADMIN, UserRole.HR_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    geofence_dict = geofence.dict()
    geofence_dict["created_at"] = datetime.utcnow()
    
    result = await db.geofences.insert_one(geofence_dict)
    geofence_dict["id"] = str(result.inserted_id)
    
    return GeoFenceResponse(**geofence_dict)

@api_router.get("/geofences", response_model=List[GeoFenceResponse])
async def get_geofences(current_user: dict = Depends(get_current_user)):
    geofences = await db.geofences.find().to_list(1000)
    result = []
    for gf in geofences:
        gf["id"] = str(gf["_id"])
        del gf["_id"]
        result.append(GeoFenceResponse(**gf))
    return result

# ============ ATTENDANCE ROUTES ============

import math

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

@api_router.post("/attendance/checkin", response_model=AttendanceResponse)
async def check_in(checkin_data: CheckInRequest, current_user: dict = Depends(get_current_user)):
    # Check if already checked in today
    today = datetime.utcnow().date().isoformat()
    existing = await db.attendance.find_one({
        "user_id": current_user["id"],
        "date": today
    })
    
    if existing:
        raise HTTPException(status_code=400, detail="Already checked in today")
    
    # Validate geofence
    geofence = await db.geofences.find_one({"_id": ObjectId(checkin_data.geofence_id)})
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
    
    # Create attendance record
    attendance = {
        "user_id": current_user["id"],
        "user_name": current_user["full_name"],
        "check_in_time": datetime.utcnow(),
        "check_in_location": {
            "latitude": checkin_data.latitude,
            "longitude": checkin_data.longitude,
            "distance_from_center": distance
        },
        "selfie_base64": checkin_data.selfie_base64,
        "status": "present",
        "geofence_id": checkin_data.geofence_id,
        "date": today
    }
    
    result = await db.attendance.insert_one(attendance)
    attendance["id"] = str(result.inserted_id)
    
    return AttendanceResponse(**attendance)

@api_router.post("/attendance/checkout")
async def check_out(checkout_data: CheckOutRequest, current_user: dict = Depends(get_current_user)):
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

@api_router.get("/attendance/my-history", response_model=List[AttendanceResponse])
async def get_my_attendance(current_user: dict = Depends(get_current_user), limit: int = 30):
    attendance_records = await db.attendance.find(
        {"user_id": current_user["id"]}
    ).sort("check_in_time", -1).limit(limit).to_list(limit)
    
    result = []
    for record in attendance_records:
        record["id"] = str(record["_id"])
        del record["_id"]
        result.append(AttendanceResponse(**record))
    
    return result

@api_router.get("/attendance/today-status")
async def get_today_status(current_user: dict = Depends(get_current_user)):
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
        "check_out_time": attendance.get("check_out_time").isoformat() if attendance.get("check_out_time") else None
    }

# ============ LOCATION TRACKING ROUTES ============

@api_router.post("/location/update")
async def update_location(location: LocationUpdate, current_user: dict = Depends(get_current_user)):
    today = datetime.utcnow().date().isoformat()
    
    # Check if checked in
    attendance = await db.attendance.find_one({
        "user_id": current_user["id"],
        "date": today
    })
    
    if not attendance:
        raise HTTPException(status_code=400, detail="Not checked in today")
    
    # Add location to tracking
    location_dict = location.dict()
    location_dict["user_id"] = current_user["id"]
    location_dict["date"] = today
    
    await db.location_tracking.insert_one(location_dict)
    
    return {"message": "Location updated"}

@api_router.get("/location/history/{user_id}/{date}")
async def get_location_history(user_id: str, date: str, current_user: dict = Depends(get_current_user)):
    # Only managers and admins can see others' locations
    if current_user["id"] != user_id and current_user["role"] not in [
        UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.REPORTING_MANAGER
    ]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    locations = await db.location_tracking.find({
        "user_id": user_id,
        "date": date
    }).sort("timestamp", 1).to_list(1000)
    
    result = []
    for loc in locations:
        result.append({
            "latitude": loc["latitude"],
            "longitude": loc["longitude"],
            "timestamp": loc["timestamp"].isoformat()
        })
    
    return {"user_id": user_id, "date": date, "locations": result}

# ============ LEAVE MANAGEMENT ROUTES ============

@api_router.post("/leaves/apply", response_model=LeaveResponse)
async def apply_leave(leave_req: LeaveRequest, current_user: dict = Depends(get_current_user)):
    # Check leave balance
    balance = await db.leave_balances.find_one({"user_id": current_user["id"]})
    if not balance:
        raise HTTPException(status_code=404, detail="Leave balance not found")
    
    balance_key = f"{leave_req.leave_type}_balance"
    if balance.get(balance_key, 0) < leave_req.days_count:
        raise HTTPException(
            status_code=400,
            detail=f"Insufficient {leave_req.leave_type} leave balance. Available: {balance.get(balance_key, 0)}"
        )
    
    # Create leave request
    leave_dict = leave_req.dict()
    leave_dict["user_id"] = current_user["id"]
    leave_dict["user_name"] = current_user["full_name"]
    leave_dict["status"] = LeaveStatus.PENDING
    leave_dict["applied_at"] = datetime.utcnow()
    
    result = await db.leaves.insert_one(leave_dict)
    leave_dict["id"] = str(result.inserted_id)
    
    return LeaveResponse(**leave_dict)

@api_router.get("/leaves/my-leaves", response_model=List[LeaveResponse])
async def get_my_leaves(current_user: dict = Depends(get_current_user)):
    leaves = await db.leaves.find(
        {"user_id": current_user["id"]}
    ).sort("applied_at", -1).to_list(100)
    
    result = []
    for leave in leaves:
        leave["id"] = str(leave["_id"])
        del leave["_id"]
        result.append(LeaveResponse(**leave))
    
    return result

@api_router.get("/leaves/balance")
async def get_leave_balance(current_user: dict = Depends(get_current_user)):
    balance = await db.leave_balances.find_one({"user_id": current_user["id"]})
    if not balance:
        return {"sick_balance": 0, "casual_balance": 0, "earned_balance": 0}
    
    return {
        "sick_balance": balance.get("sick_balance", 0),
        "casual_balance": balance.get("casual_balance", 0),
        "earned_balance": balance.get("earned_balance", 0)
    }

@api_router.get("/leaves/pending", response_model=List[LeaveResponse])
async def get_pending_leaves(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in [UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.REPORTING_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    leaves = await db.leaves.find(
        {"status": LeaveStatus.PENDING}
    ).sort("applied_at", 1).to_list(100)
    
    result = []
    for leave in leaves:
        leave["id"] = str(leave["_id"])
        del leave["_id"]
        result.append(LeaveResponse(**leave))
    
    return result

@api_router.post("/leaves/approve")
async def approve_leave(approval: LeaveApproval, current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in [UserRole.SUPER_ADMIN, UserRole.HR_MANAGER, UserRole.REPORTING_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    leave = await db.leaves.find_one({"_id": ObjectId(approval.leave_id)})
    if not leave:
        raise HTTPException(status_code=404, detail="Leave not found")
    
    if leave["status"] != LeaveStatus.PENDING:
        raise HTTPException(status_code=400, detail="Leave already processed")
    
    # Update leave status
    await db.leaves.update_one(
        {"_id": ObjectId(approval.leave_id)},
        {
            "$set": {
                "status": approval.status,
                "remarks": approval.remarks,
                "approved_by": current_user["id"],
                "approved_at": datetime.utcnow()
            }
        }
    )
    
    # Update leave balance if approved
    if approval.status == LeaveStatus.APPROVED:
        balance_key = f"{leave['leave_type']}_balance"
        await db.leave_balances.update_one(
            {"user_id": leave["user_id"]},
            {"$inc": {balance_key: -leave["days_count"]}}
        )
    
    return {"message": f"Leave {approval.status}"}

# ============ ADMIN ROUTES ============

@api_router.get("/admin/users", response_model=List[UserResponse])
async def get_all_users(current_user: dict = Depends(get_current_user)):
    if current_user["role"] not in [UserRole.SUPER_ADMIN, UserRole.HR_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    users = await db.users.find().to_list(1000)
    result = []
    for user in users:
        user["id"] = str(user["_id"])
        del user["_id"]
        del user["password"]
        result.append(UserResponse(**user))
    
    return result

@api_router.get("/admin/attendance/all")
async def get_all_attendance(current_user: dict = Depends(get_current_user), date: Optional[str] = None):
    if current_user["role"] not in [UserRole.SUPER_ADMIN, UserRole.HR_MANAGER]:
        raise HTTPException(status_code=403, detail="Not authorized")
    
    query = {}
    if date:
        query["date"] = date
    else:
        query["date"] = datetime.utcnow().date().isoformat()
    
    attendance_records = await db.attendance.find(query).to_list(1000)
    
    result = []
    for record in attendance_records:
        record["id"] = str(record["_id"])
        del record["_id"]
        result.append(record)
    
    return result

# Include router
app.include_router(api_router)

app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

@app.on_event("shutdown")
async def shutdown_db_client():
    client.close()
