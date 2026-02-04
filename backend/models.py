"""
Pydantic Models for Gyanmanjari HRMS
Enhanced with multi-center, advanced leave policies, and payroll
"""
from pydantic import BaseModel, Field, EmailStr
from typing import List, Optional, Dict
from datetime import datetime

# ============ USER & ROLE MODELS ============

class UserRole:
    SUPER_ADMIN = "super_admin"
    CENTER_ADMIN = "center_admin"
    HR_MANAGER = "hr_manager"
    REPORTING_MANAGER = "reporting_manager"
    EMPLOYEE = "employee"

class UserBase(BaseModel):
    email: EmailStr
    full_name: str
    employee_id: str
    role: str = UserRole.EMPLOYEE
    department: Optional[str] = None
    designation: Optional[str] = None
    manager_id: Optional[str] = None
    phone: Optional[str] = None

class UserRegister(UserBase):
    password: str

class UserResponse(UserBase):
    id: str
    is_active: bool
    created_at: datetime
    assigned_centers: List[str] = []
    primary_center: Optional[str] = None
    profile_locked: bool = False

# ============ CENTER MODELS ============

class GeoFenceData(BaseModel):
    name: str
    latitude: float
    longitude: float
    radius: float = 100.0

class HolidayData(BaseModel):
    date: str  # YYYY-MM-DD
    type: str  # "public" or "vacation"
    description: str

class CenterCreate(BaseModel):
    name: str
    address: str
    contact: str
    geofences: List[GeoFenceData] = []
    holidays: List[HolidayData] = []

class CenterResponse(BaseModel):
    id: str
    name: str
    address: str
    contact: str
    center_admin_ids: List[str] = []
    geofences: List[Dict]
    holidays: List[Dict]
    created_at: datetime
    employee_count: int = 0

class AssignCentersRequest(BaseModel):
    employee_id: str
    center_ids: List[str]
    primary_center_id: str

# ============ LEAVE MODELS (Enhanced) ============

class LeaveType:
    CASUAL = "casual"  # CL
    SICK = "sick"
    EARNED = "earned"
    LWP = "lwp"  # Leave Without Pay
    MARRIAGE = "marriage"
    BEREAVEMENT = "bereavement"

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
    medical_certificate_base64: Optional[str] = None  # For sick leave
    center_id: Optional[str] = None

class LeaveApproval(BaseModel):
    leave_id: str
    status: str  # approved or rejected
    remarks: Optional[str] = None

class LeaveOverride(BaseModel):
    leave_id: str
    new_leave_type: str
    reason: str

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
    medical_certificate_url: Optional[str] = None
    days_in_advance: Optional[int] = None
    month_applied: Optional[str] = None
    override_history: List[Dict] = []

# ============ ATTENDANCE MODELS (Enhanced) ============

class CheckInRequest(BaseModel):
    latitude: float
    longitude: float
    selfie_base64: str
    geofence_id: str
    center_id: str

class AttendanceResponse(BaseModel):
    id: str
    user_id: str
    user_name: str
    center_id: str
    center_name: str
    check_in_time: datetime
    check_out_time: Optional[datetime] = None
    check_in_location: Dict
    check_out_location: Optional[Dict] = None
    selfie_url: str
    status: str
    geofence_id: str
    date: str

# ============ PAYROLL MODELS ============

class PayrollConfig(BaseModel):
    month: str  # YYYY-MM
    working_days: int = 26
    per_day_salary_factor: float = 1.0

class CompensatoryCredit(BaseModel):
    employee_id: str
    days_credited: float
    reason: str
    year_valid_for: int
    date_credited: datetime = Field(default_factory=datetime.utcnow)

class PayrollRecord(BaseModel):
    employee_id: str
    employee_name: str
    month: str  # YYYY-MM
    year: int
    base_salary: float
    present_days: int
    lwp_days: int
    unused_cl_encashment: float
    compensatory_days: float
    gross_salary: float
    deductions: Dict[str, float] = {}
    allowances: Dict[str, float] = {}
    net_salary: float
    status: str = "draft"  # draft, finalized, paid
    generated_at: datetime = Field(default_factory=datetime.utcnow)

class PayrollGenerate(BaseModel):
    month: str  # YYYY-MM
    employee_ids: Optional[List[str]] = None  # None = all employees

class SalarySlipTemplate(BaseModel):
    company_name: str = "Gyanmanjari"
    company_address: str = ""
    company_contact: str = ""
    show_allowances: bool = True
    show_deductions: bool = True
    logo_url: Optional[str] = None

# ============ RECRUITMENT/ATS MODELS ============

class JobPosting(BaseModel):
    title: str
    description: str
    department: str
    location: str
    requirements: List[str] = []
    status: str = "open"  # open, closed

class CandidateApplication(BaseModel):
    job_id: str
    name: str
    email: EmailStr
    phone: str
    resume_base64: str
    cover_letter: Optional[str] = None

class InterviewRound(BaseModel):
    candidate_id: str
    round_number: int
    panelist_ids: List[str]
    scheduled_date: str
    scheduled_time: str
    status: str = "scheduled"  # scheduled, completed, cancelled

class InterviewFeedback(BaseModel):
    interview_id: str
    rating: int  # 1-5
    comments: str
    recommendation: str  # hire, maybe, reject

class OfferLetter(BaseModel):
    candidate_id: str
    template_html: str
    salary_offered: float
    joining_date: str

class OnboardingDocument(BaseModel):
    candidate_id: str
    doc_type: str  # aadhaar, pan, bank, education
    file_base64: str
    file_name: str

# ============ EXIT MANAGEMENT MODELS ============

class ResignationRequest(BaseModel):
    reason: str
    last_working_day: str  # YYYY-MM-DD

class ResignationResponse(BaseModel):
    id: str
    employee_id: str
    employee_name: str
    resignation_date: datetime
    last_working_day: str
    notice_period_days: int
    reason: str
    status: str  # pending, approved, completed
    approved_by: Optional[str] = None

class FullAndFinal(BaseModel):
    employee_id: str
    pending_salary: float
    unused_leaves_encashment: float
    asset_recovery_deduction: float
    lwp_deduction: float
    other_deductions: Dict[str, float] = {}
    final_settlement: float
    clearance_checklist: Dict[str, bool] = {
        "it_assets": False,
        "hr_documents": False,
        "no_dues": False
    }
    payment_status: str = "pending"  # pending, processed

# ============ UTILITY MODELS ============

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse

class MessageResponse(BaseModel):
    message: str
    data: Optional[Dict] = None
