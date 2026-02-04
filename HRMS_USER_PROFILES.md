# HRMS User Profiles & Role-Based Access Control

## Overview
The HRMS system has three distinct user profiles with different levels of access and capabilities.

## 1. 🔴 Super Admin Profile
**Role:** `super_admin`  
**Test Credentials:** `admin@hrms.com / admin123`

### Full System Control
- **User Management:** View all users, manage user roles and permissions
- **Geofence Management:** 
  - Create new office/site locations with GPS coordinates
  - Set geofence radius for attendance validation
  - Update and delete geofence locations
- **Attendance Oversight:**
  - View all employees' attendance in real-time
  - Access attendance history for any employee
  - Monitor location tracking for field employees
- **Leave Management:**
  - Approve/reject all leave applications
  - Configure leave types and balances
  - View leave history across organization
- **System Configuration:**
  - Customize attendance rules
  - Set up organizational hierarchy
  - Configure notifications and alerts
- **Reports & Analytics:**
  - Generate attendance reports
  - Leave utilization statistics
  - Employee productivity metrics

### UI Features
- **Admin Tab:** Dedicated admin panel in mobile app
- **Dashboard:** Real-time statistics and pending approvals
- **Quick Actions:** One-click geofence creation, bulk approvals

---

## 2. 🟡 HR Manager / Admin Profile
**Role:** `hr_manager`  
**Create via:** Register with role assignment or Super Admin promotion

### HR Operations & Management
- **Employee Management:**
  - View all employee profiles
  - Access employee attendance records
  - Monitor leave balances
- **Leave Approval:**
  - Approve/reject leave applications
  - View pending leave requests
  - Add remarks to leave decisions
- **Attendance Management:**
  - View today's attendance
  - Access attendance history
  - Generate attendance reports
- **User Oversight:**
  - View user list with status (active/inactive)
  - Track employee departments and designations

### Limitations
- **Cannot** create or modify geofences (Super Admin only)
- **Cannot** change system-wide settings
- **Cannot** modify user roles

### UI Features
- **Admin Tab:** HR-focused admin panel (limited access)
- **Approval Queue:** Streamlined leave approval interface
- **Reports:** Department-wise attendance and leave reports

---

## 3. 🟢 Employee / User Profile
**Role:** `employee`  
**Test Credentials:** `employee@hrms.com / employee123`

### Daily Operations
- **Attendance:**
  - Check-in with GPS validation (must be within geofence)
  - Take selfie for attendance verification
  - Check-out at end of day
  - View personal attendance history
- **Leave Management:**
  - View leave balance (Sick: 12, Casual: 12, Earned: 18 days)
  - Apply for leaves with date range and reason
  - Track leave application status (pending/approved/rejected)
  - View leave history
- **Profile:**
  - View personal information
  - Update profile details
  - View employee ID and department
- **Dashboard:**
  - Today's check-in status
  - Current leave balance
  - Quick action buttons

### Restrictions
- **No admin access** - Admin tab hidden
- **Cannot** view other employees' data
- **Cannot** approve leaves
- **Can only** manage personal attendance and leaves

### Check-in Requirements
1. Must be within 100m radius of assigned geofence
2. Must capture a selfie (face detection)
3. GPS location must be enabled
4. Can only check-in once per day

---

## Role Comparison Matrix

| Feature | Super Admin | HR Manager | Employee |
|---------|-------------|------------|----------|
| View Own Attendance | ✅ | ✅ | ✅ |
| View All Attendance | ✅ | ✅ | ❌ |
| Check-in/out | ✅ | ✅ | ✅ |
| Apply Leave | ✅ | ✅ | ✅ |
| Approve Leave | ✅ | ✅ | ❌ |
| View All Users | ✅ | ✅ | ❌ |
| Create Geofence | ✅ | ❌ | ❌ |
| Manage System Settings | ✅ | ❌ | ❌ |
| Admin Panel Access | Full | Limited | None |
| Location Tracking | ✅ | ✅ | ✅ |

---

## API Access Control

### Authentication Required
All endpoints require JWT token in Authorization header:
```
Authorization: Bearer <token>
```

### Role-Based Endpoint Access

**Public (Authenticated):**
- `POST /api/attendance/checkin`
- `POST /api/attendance/checkout`
- `GET /api/attendance/my-history`
- `GET /api/attendance/today-status`
- `POST /api/leaves/apply`
- `GET /api/leaves/my-leaves`
- `GET /api/leaves/balance`
- `GET /api/geofences`

**Admin Only (HR Manager + Super Admin):**
- `GET /api/admin/users`
- `GET /api/admin/attendance/all`
- `GET /api/leaves/pending`
- `POST /api/leaves/approve`

**Super Admin Only:**
- `POST /api/geofences` (Create geofence)
- `PUT /api/geofences/{id}` (Update geofence)
- `DELETE /api/geofences/{id}` (Delete geofence)
- System configuration endpoints

---

## How to Create Different User Profiles

### 1. Create Super Admin
Already created via seed script:
```
Email: admin@hrms.com
Password: admin123
Role: super_admin
```

### 2. Create HR Manager
```bash
POST /api/auth/register
{
  "email": "hr@company.com",
  "password": "secure_password",
  "full_name": "HR Manager",
  "employee_id": "HR001",
  "role": "hr_manager",
  "department": "Human Resources",
  "designation": "HR Manager"
}
```

### 3. Create Employee
```bash
POST /api/auth/register
{
  "email": "john@company.com",
  "password": "secure_password",
  "full_name": "John Doe",
  "employee_id": "EMP003",
  "role": "employee",
  "department": "Engineering",
  "designation": "Software Developer"
}
```

---

## Mobile App Experience by Role

### Super Admin View
- **5 Tabs:** Home | Attendance | Leaves | **Admin** | Profile
- Admin tab shows: Statistics, Geofence Management, Leave Approvals, All Users
- Full system customization options

### HR Manager View
- **5 Tabs:** Home | Attendance | Leaves | **Admin** | Profile
- Admin tab shows: Statistics, Leave Approvals, User List (no geofence management)
- Streamlined approval workflows

### Employee View
- **4 Tabs:** Home | Attendance | Leaves | Profile
- No admin tab visible
- Focus on personal attendance and leave management
- Simple, clean interface

---

## Security Features

1. **JWT Authentication:** Secure token-based auth with 7-day expiry
2. **Password Hashing:** Bcrypt with salt
3. **Role Validation:** Server-side role checking on every request
4. **Geofence Validation:** Attendance only within authorized locations
5. **Face Detection:** Selfie required for check-in (basic validation)
6. **GPS Verification:** Haversine formula for accurate distance calculation

---

## Default Leave Balance

All users start with:
- **Sick Leave:** 12 days
- **Casual Leave:** 12 days  
- **Earned Leave:** 18 days
- **Total:** 42 days per year

Leave balance updates automatically upon approval.
