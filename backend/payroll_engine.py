"""
Payroll Calculation Engine for Gyanmanjari HRMS
Auto-calculates salaries based on attendance and leaves
"""
from datetime import datetime, timedelta
from typing import Dict, List, Optional
import calendar
import logging
from bson import ObjectId

logger = logging.getLogger(__name__)

class PayrollEngine:
    """
    Gyanmanjari Payroll Logic:
    - Auto-calculate based on attendance + leaves
    - Formula: Total Days - (Unapproved Absences + LWP)
    - Unused CL encashment
    - Compensatory off tracking for center admins
    """
    
    def __init__(self, db):
        self.db = db
    
    async def calculate_monthly_payroll(
        self,
        employee_id: str,
        month: str,  # YYYY-MM format
        base_salary: float
    ) -> Dict:
        """
        Calculate complete payroll for an employee for a given month
        """
        year, month_num = map(int, month.split('-'))
        working_days = calendar.monthrange(year, month_num)[1]
        
        # Get attendance data
        attendance_count = await self._get_attendance_count(employee_id, month)
        
        # Get leave data
        leave_data = await self._get_leave_data(employee_id, month)
        
        # Calculate present days
        present_days = attendance_count + leave_data['paid_leave_days']
        
        # Calculate LWP deduction
        lwp_days = leave_data['lwp_days']
        
        # Calculate unused CL encashment
        unused_cl = await self._calculate_unused_cl_encashment(employee_id, month)
        
        # Get compensatory days
        comp_days = await self._get_compensatory_days(employee_id, month)
        
        # Per day salary
        per_day_salary = base_salary / working_days
        
        # Gross salary calculation
        regular_salary = per_day_salary * (present_days - lwp_days)
        cl_encashment = unused_cl * per_day_salary
        comp_payment = comp_days * per_day_salary
        
        gross_salary = regular_salary + cl_encashment + comp_payment
        
        # Deductions (to be configured by admin)
        deductions = await self._calculate_deductions(gross_salary, employee_id)
        
        # Allowances (to be configured by admin)
        allowances = await self._get_allowances(employee_id)
        
        # Net salary
        net_salary = gross_salary + sum(allowances.values()) - sum(deductions.values())
        
        payroll_record = {
            "employee_id": employee_id,
            "month": month,
            "year": year,
            "working_days": working_days,
            "present_days": present_days,
            "lwp_days": lwp_days,
            "base_salary": base_salary,
            "unused_cl_encashment": cl_encashment,
            "compensatory_payment": comp_payment,
            "gross_salary": gross_salary,
            "deductions": deductions,
            "allowances": allowances,
            "net_salary": net_salary,
            "status": "draft",
            "generated_at": datetime.utcnow(),
            "calculation_details": {
                "per_day_salary": per_day_salary,
                "regular_salary": regular_salary,
                "attendance_days": attendance_count,
                "paid_leave_days": leave_data['paid_leave_days'],
                "unused_cl": unused_cl,
                "comp_days": comp_days
            }
        }
        
        return payroll_record
    
    async def _get_attendance_count(self, employee_id: str, month: str) -> int:
        """Get number of days employee checked in"""
        year, month_num = month.split('-')
        
        # Count unique dates with attendance
        attendance_records = await self.db.attendance.find({
            "user_id": employee_id,
            "date": {"$regex": f"^{month}"}
        }).to_list(None)
        
        return len(attendance_records)
    
    async def _get_leave_data(self, employee_id: str, month: str) -> Dict:
        """Get leave information for the month"""
        leaves = await self.db.leaves.find({
            "user_id": employee_id,
            "status": "approved",
            "start_date": {"$regex": f"^{month}"}
        }).to_list(None)
        
        paid_leave_days = 0
        lwp_days = 0
        
        for leave in leaves:
            if leave['leave_type'] == 'lwp':
                lwp_days += leave['days_count']
            else:
                paid_leave_days += leave['days_count']
        
        return {
            "paid_leave_days": paid_leave_days,
            "lwp_days": lwp_days
        }
    
    async def _calculate_unused_cl_encashment(
        self,
        employee_id: str,
        month: str
    ) -> float:
        """
        Calculate unused CL for encashment
        Policy: 1 CL per month. Unused = encashed
        """
        # Check if user applied CL this month
        cl_used = await self.db.leaves.find({
            "user_id": employee_id,
            "month_applied": month,
            "leave_type": "casual",
            "status": "approved"
        }).to_list(None)
        
        cl_days_used = sum(leave.get('days_count', 0) for leave in cl_used)
        
        # Unused CL = 1 - used (max 1 per month)
        unused = max(0, 1 - cl_days_used)
        
        return unused
    
    async def _get_compensatory_days(
        self,
        employee_id: str,
        month: str
    ) -> float:
        """
        Get compensatory days used this month
        Center admins working during summer vacation get comp-off
        """
        comp_records = await self.db.compensatory_credits.find({
            "employee_id": employee_id,
            "date_credited": {
                "$gte": datetime.strptime(f"{month}-01", "%Y-%m-%d"),
                "$lt": datetime.strptime(f"{month}-01", "%Y-%m-%d") + timedelta(days=32)
            }
        }).to_list(None)
        
        return sum(record.get('days_credited', 0) for record in comp_records)
    
    async def _calculate_deductions(
        self,
        gross_salary: float,
        employee_id: str
    ) -> Dict[str, float]:
        """
        Calculate deductions (PF, TDS, etc.)
        Configurable by admin
        """
        deductions = {}
        
        # Basic deductions (to be made configurable)
        if gross_salary > 15000:
            deductions['pf'] = gross_salary * 0.12  # 12% PF
        
        if gross_salary > 50000:
            deductions['tds'] = gross_salary * 0.05  # 5% TDS (simplified)
        
        return deductions
    
    async def _get_allowances(self, employee_id: str) -> Dict[str, float]:
        """
        Get employee-specific allowances
        Configurable by admin
        """
        # To be fetched from employee config
        # For now, empty
        return {}
    
    async def bulk_generate_payroll(
        self,
        month: str,
        employee_ids: Optional[List[str]] = None
    ) -> List[Dict]:
        """
        Generate payroll for multiple employees
        """
        if not employee_ids:
            # Get all active employees
            employees = await self.db.users.find({"is_active": True}).to_list(None)
            employee_ids = [str(emp['_id']) for emp in employees]
        
        payroll_records = []
        
        for emp_id in employee_ids:
            try:
                # Get employee base salary (to be stored in user profile)
                employee = await self.db.users.find_one({"_id": ObjectId(emp_id)})
                base_salary = employee.get('base_salary', 30000)  # Default
                
                record = await self.calculate_monthly_payroll(
                    emp_id,
                    month,
                    base_salary
                )
                
                # Store in database
                await self.db.payroll_records.insert_one(record)
                payroll_records.append(record)
                
                logger.info(f"Payroll generated for employee {emp_id} for {month}")
                
            except Exception as e:
                logger.error(f"Error generating payroll for {emp_id}: {e}")
                continue
        
        return payroll_records
    
    async def finalize_payroll(self, payroll_id: str) -> bool:
        """
        Finalize payroll (lock it from editing)
        """
        result = await self.db.payroll_records.update_one(
            {"_id": ObjectId(payroll_id)},
            {"$set": {"status": "finalized", "finalized_at": datetime.utcnow()}}
        )
        
        return result.modified_count > 0
    
    async def credit_compensatory_off(
        self,
        employee_id: str,
        days: float,
        reason: str,
        valid_for_year: int
    ):
        """
        Credit compensatory days to center admin for working during vacation
        """
        comp_record = {
            "employee_id": employee_id,
            "days_credited": days,
            "reason": reason,
            "year_valid_for": valid_for_year,
            "date_credited": datetime.utcnow()
        }
        
        await self.db.compensatory_credits.insert_one(comp_record)
        logger.info(f"Credited {days} comp days to employee {employee_id}")
