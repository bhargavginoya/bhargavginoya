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

