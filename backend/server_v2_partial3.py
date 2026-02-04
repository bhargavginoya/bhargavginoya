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

