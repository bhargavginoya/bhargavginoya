# Gyanmanjari HRMS - Complete Implementation Plan

## 🎯 Project Overview
Transform existing HRMS into enterprise-grade system for Gyanmanjari with 30+ centers, advanced leave policies, payroll automation, and complete ATS.

---

## 📋 Phase 1: Immediate Fixes & Branding (Day 1)
### ✅ Completed
- [x] Downloaded Gyanmanjari branding assets
- [x] Verified backend authentication working
- [x] Confirmed services running

### 🔄 In Progress
- [ ] Apply Gyanmanjari branding globally
- [ ] Test all existing buttons and fix broken functionality
- [ ] Update app name to "Gyanmanjari HRMS"

### Tasks:
1. Replace all "HRMS" references with "Gyanmanjari HRMS"
2. Integrate logos in login, headers, and navigation
3. Test and fix any broken buttons/API calls
4. Update app.json with new branding

---

## 📋 Phase 2: Multi-Geofencing & Center Hierarchy (Day 1-2)

### Backend Changes:
1. **New Collections:**
   - `centers` - Store 30+ center locations
   - `employee_center_assignments` - Many-to-many mapping
   - Update `geofences` to link with centers

2. **User Roles Enhancement:**
   - Add `center_admin` role
   - Link users to specific centers
   - Center-based data access control

3. **New API Endpoints:**
   ```
   POST   /api/centers - Create center
   GET    /api/centers - List all centers
   GET    /api/centers/{id}/employees - Get center employees
   POST   /api/centers/{id}/geofences - Add geofence to center
   POST   /api/employees/{id}/assign-centers - Assign multiple centers
   ```

### Frontend Changes:
1. Super Admin: Center management UI
2. Center Admin: Limited dashboard for their center only
3. Multi-geofence selection during check-in

---

## 📋 Phase 3: Advanced Leave Rule Engine (Day 2-3)

### Backend Implementation:
1. **New Leave Types:**
   - CL (Casual Leave) - 1/month, 7 days advance
   - Sick Leave - Requires medical certificate
   - LWP (Leave Without Pay) - Max 3/month total
   - Marriage Leave - 7 days (admin allocatable)
   - Bereavement Leave - 7 days (admin allocatable)

2. **Leave Rules Engine:**
   ```python
   class LeaveRuleEngine:
       - validate_cl_advance_notice()
       - validate_monthly_limit()
       - validate_medical_certificate()
       - calculate_lwp_limit()
       - check_public_holidays()
   ```

3. **New Fields:**
   - `attachment_url` for medical certificates
   - `applied_days_in_advance`
   - `center_id` for center-specific holidays

4. **Admin Override:**
   - PUT /api/leaves/{id}/change-type - Change leave type
   - PUT /api/leaves/{id}/override - Admin override rules

### Frontend:
1. File upload for medical certificates
2. Advance notice validation
3. Monthly limit display
4. Admin override interface

---

## 📋 Phase 4: Web Dashboard with Webcam & Geolocation (Day 3-4)

### New Web App (Next.js):
1. **Directory Structure:**
   ```
   /app/web-dashboard/
   ├── pages/
   │   ├── index.tsx (Login)
   │   ├── dashboard/
   │   ├── attendance/
   │   ├── leaves/
   │   └── admin/
   ├── components/
   │   ├── WebcamCapture.tsx
   │   ├── GeolocationCheck.tsx
   │   └── AttendanceButton.tsx
   └── public/
   ```

2. **Features:**
   - Browser geolocation API
   - Webcam access via getUserMedia()
   - Exact parity with mobile app
   - Real-time sync with MongoDB

---

## 📋 Phase 5: Payroll Automation (Day 4-5)

### New Collections:
```javascript
payroll_config: {
  month, year,
  working_days,
  per_day_salary_factor
}

payroll_records: {
  employee_id,
  month, year,
  present_days,
  lwp_days,
  unused_cl_encashment,
  compensatory_days,
  gross_salary,
  deductions,
  net_salary,
  pdf_url
}

compensatory_credits: {
  employee_id,
  days_credited,
  reason,
  year_valid_for
}
```

### Calculation Logic:
```python
def calculate_payroll(employee_id, month, year):
    attendance = get_attendance_data()
    leaves = get_leave_data()
    
    present_days = attendance.count()
    lwp_days = leaves.filter(type='LWP').count()
    unused_cl = 1 - leaves.filter(type='CL').count()
    
    payable_days = present_days - lwp_days
    encashment = unused_cl * per_day_salary
    
    net_salary = (base_salary/30 * payable_days) + encashment
    
    generate_pdf(salary_slip)
```

### Admin Features:
- Bulk payroll generation
- Custom salary slip templates
- Edit deductions/allowances
- Compensatory off management

---

## 📋 Phase 6: Recruitment & ATS (Day 5-6)

### New Collections:
```javascript
job_postings: {
  title, description,
  department, location,
  status: 'open'|'closed'
}

candidates: {
  name, email, phone,
  resume_url,
  current_status,
  temp_login_credentials
}

interview_rounds: {
  candidate_id,
  round_number,
  panelist_ids[],
  scheduled_date,
  feedback: [{panelist_id, rating, comments}]
}

offer_letters: {
  candidate_id,
  template_html,
  generated_pdf_url,
  status: 'sent'|'accepted'|'rejected'
}

onboarding_docs: {
  candidate_id,
  doc_type: 'aadhaar'|'pan'|'bank'|'education',
  file_url,
  verification_status
}
```

### Features:
1. **Public Job Portal:**
   - Candidate application form
   - Resume upload
   - Auto temp login creation

2. **Interview Management:**
   - Configurable rounds (1-5)
   - Panelist assignments
   - Feedback collection
   - Status tracking

3. **Offer Letter:**
   - Rich text editor (Quill/TinyMCE)
   - Template customization
   - PDF generation
   - Digital signature

4. **Onboarding:**
   - Document upload portal
   - Verification workflow
   - Auto convert to employee

---

## 📋 Phase 7: Exit Management & FnF (Day 6-7)

### New Collections:
```javascript
resignations: {
  employee_id,
  resignation_date,
  last_working_day,
  notice_period_days,
  reason,
  status: 'pending'|'approved'|'completed'
}

full_and_final: {
  employee_id,
  pending_salary,
  unused_leaves_encashment,
  asset_recovery_deduction,
  lwp_deduction,
  final_settlement,
  payment_status,
  clearance_checklist: {
    it_assets: boolean,
    hr_documents: boolean,
    no_dues: boolean
  }
}
```

### Calculation:
```python
def calculate_fnf(employee_id):
    pending_salary = get_current_month_salary()
    unused_leaves = get_unused_leaves() * per_day_salary
    assets = get_pending_asset_returns()
    
    total = pending_salary + unused_leaves - assets
    return fnf_record
```

### Features:
- Resignation workflow
- Notice period tracking
- Asset clearance checklist
- Automated FnF calculation
- Profile locking post-exit

---

## 📋 Phase 8: Advanced Features

### Real-Time Sync:
- WebSocket integration for live updates
- MongoDB Change Streams
- Push notifications

### Profile Locking:
- Employee fills profile → Lock fields
- Only admin can edit
- Audit trail for changes

### Center-Specific Holidays:
- Per-center holiday calendar
- Public holidays vs vacation days
- Auto-block leave applications on holidays

### Offline-First Mobile:
- IndexedDB for local storage
- Background sync when online
- Queue management for failed requests

---

## 🗄️ Enhanced Database Schema

```javascript
// Centers Collection
{
  _id: ObjectId,
  name: "Gyanmanjari Main Center",
  address: "...",
  contact: "...",
  center_admin_ids: [ObjectId],
  geofences: [{
    name: "Main Building",
    latitude: 28.6139,
    longitude: 77.2090,
    radius: 100
  }],
  holidays: [{
    date: "2025-08-15",
    type: "public"|"vacation",
    description: "Independence Day"
  }]
}

// Enhanced User Schema
{
  ...existing_fields,
  assigned_centers: [ObjectId], // Can check-in from any
  primary_center: ObjectId,
  sub_admin_centers: [ObjectId], // For center admins
  profile_locked: boolean,
  profile_locked_at: DateTime
}

// Enhanced Leave Schema
{
  ...existing_fields,
  attachment_url: String, // Medical certificate
  days_in_advance: Number,
  month_applied: String, // Track monthly limits
  center_id: ObjectId,
  admin_override: {
    changed_by: ObjectId,
    original_type: String,
    new_type: String,
    reason: String
  }
}
```

---

## 🔐 Role Permissions Matrix

| Feature | Super Admin | Center Admin | Employee |
|---------|-------------|--------------|----------|
| Create Centers | ✅ | ❌ | ❌ |
| Assign Geofences | ✅ | ❌ | ❌ |
| View All Centers | ✅ | Own Only | Assigned Only |
| Approve Leaves | ✅ | Own Center | ❌ |
| Generate Payroll | ✅ | Own Center | View Own |
| Manage ATS | ✅ | Limited | ❌ |
| Edit Leave Type | ✅ | ❌ | ❌ |
| Lock Profiles | ✅ | ❌ | ❌ |

---

## 🚀 Deployment Checklist

- [ ] Environment variables configured
- [ ] MongoDB indexes created
- [ ] File upload service configured (S3/CloudFlare)
- [ ] Email service integrated (SendGrid)
- [ ] SMS service for notifications (Twilio)
- [ ] Backup strategy implemented
- [ ] Monitoring & logging setup
- [ ] Load testing completed
- [ ] Security audit passed
- [ ] User acceptance testing done

---

## 📊 Success Metrics

1. **Stability:** 99.9% uptime
2. **Performance:** API response < 200ms
3. **User Adoption:** 350+ active users
4. **Data Accuracy:** Payroll calculations 100% accurate
5. **Sync Speed:** Real-time updates < 2s latency

---

**Implementation Start Date:** Feb 4, 2025
**Target Completion:** Feb 11, 2025 (7 days)
**Version:** 2.0.0 - Gyanmanjari Enterprise Edition
