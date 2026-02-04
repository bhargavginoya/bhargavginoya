"""
Advanced Leave Rule Engine for Gyanmanjari HRMS
Implements complex leave policies with validation
"""
from datetime import datetime, timedelta
from typing import Dict, Tuple, Optional
import logging

logger = logging.getLogger(__name__)

class LeaveRuleEngine:
    """
    Gyanmanjari Leave Policies:
    - CL (Casual Leave): 1 per month, must apply 7 days in advance
    - Sick Leave: Requires medical certificate attachment
    - LWP (Leave Without Pay): Max 3 leaves/month total (including CL)
    - Marriage: 7 days (allocated by admin)
    - Bereavement: 7 days (allocated by admin)
    """
    
    def __init__(self, db):
        self.db = db
    
    async def validate_leave_application(
        self,
        user_id: str,
        leave_type: str,
        start_date: str,
        end_date: str,
        days_count: float,
        medical_certificate: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Comprehensive leave validation
        Returns: (is_valid, error_message)
        """
        
        # 1. Check days in advance for CL
        if leave_type == "casual":
            days_in_advance = self._calculate_days_in_advance(start_date)
            if days_in_advance < 7:
                return False, f"Casual Leave must be applied 7 days in advance. You applied {days_in_advance} days in advance."
        
        # 2. Check medical certificate for sick leave
        if leave_type == "sick":
            if not medical_certificate:
                return False, "Medical certificate is mandatory for Sick Leave"
        
        # 3. Check monthly limit (CL + LWP max 3/month)
        month_key = datetime.strptime(start_date, "%Y-%m-%d").strftime("%Y-%m")
        if leave_type in ["casual", "lwp"]:
            monthly_count = await self._get_monthly_leave_count(user_id, month_key)
            if monthly_count + days_count > 3:
                return False, f"You can apply max 3 leaves/month (CL + LWP combined). Current month: {monthly_count}, Requesting: {days_count}"
        
        # 4. Check CL monthly limit (1 per month)
        if leave_type == "casual":
            cl_count = await self._get_monthly_cl_count(user_id, month_key)
            if cl_count + days_count > 1:
                return False, f"You can apply only 1 Casual Leave per month. Already applied: {cl_count}"
        
        # 5. Check leave balance
        balance_check = await self._check_leave_balance(user_id, leave_type, days_count)
        if not balance_check[0]:
            return False, balance_check[1]
        
        # 6. Check for overlapping leaves
        overlap = await self._check_overlapping_leaves(user_id, start_date, end_date)
        if overlap:
            return False, "You have overlapping leave applications for this period"
        
        # 7. Check for public holidays (should not deduct from leave)
        # This will be center-specific
        
        return True, "Leave application is valid"
    
    def _calculate_days_in_advance(self, start_date: str) -> int:
        """Calculate how many days in advance the leave is being applied"""
        start = datetime.strptime(start_date, "%Y-%m-%d")
        today = datetime.utcnow().date()
        delta = (start.date() - today).days
        return max(0, delta)
    
    async def _get_monthly_leave_count(self, user_id: str, month: str) -> float:
        """Get total CL + LWP count for the month"""
        leaves = await self.db.leaves.find({
            "user_id": user_id,
            "month_applied": month,
            "leave_type": {"$in": ["casual", "lwp"]},
            "status": {"$in": ["pending", "approved"]}
        }).to_list(None)
        
        return sum(leave.get("days_count", 0) for leave in leaves)
    
    async def _get_monthly_cl_count(self, user_id: str, month: str) -> float:
        """Get CL count for the month"""
        leaves = await self.db.leaves.find({
            "user_id": user_id,
            "month_applied": month,
            "leave_type": "casual",
            "status": {"$in": ["pending", "approved"]}
        }).to_list(None)
        
        return sum(leave.get("days_count", 0) for leave in leaves)
    
    async def _check_leave_balance(
        self,
        user_id: str,
        leave_type: str,
        days_requested: float
    ) -> Tuple[bool, str]:
        """Check if user has sufficient leave balance"""
        
        # LWP doesn't need balance check
        if leave_type == "lwp":
            return True, ""
        
        balance = await self.db.leave_balances.find_one({"user_id": user_id})
        if not balance:
            return False, "Leave balance not found"
        
        balance_key = f"{leave_type}_balance"
        available = balance.get(balance_key, 0)
        
        if available < days_requested:
            return False, f"Insufficient {leave_type} leave balance. Available: {available}, Requested: {days_requested}"
        
        return True, ""
    
    async def _check_overlapping_leaves(
        self,
        user_id: str,
        start_date: str,
        end_date: str
    ) -> bool:
        """Check if there are overlapping leave applications"""
        overlapping = await self.db.leaves.find_one({
            "user_id": user_id,
            "status": {"$in": ["pending", "approved"]},
            "$or": [
                {"start_date": {"$lte": end_date, "$gte": start_date}},
                {"end_date": {"$lte": end_date, "$gte": start_date}},
                {
                    "$and": [
                        {"start_date": {"$lte": start_date}},
                        {"end_date": {"$gte": end_date}}
                    ]
                }
            ]
        })
        
        return overlapping is not None
    
    async def calculate_leave_days(
        self,
        start_date: str,
        end_date: str,
        center_id: Optional[str] = None
    ) -> float:
        """
        Calculate actual leave days excluding weekends and public holidays
        For now, simplified calculation
        """
        start = datetime.strptime(start_date, "%Y-%m-%d")
        end = datetime.strptime(end_date, "%Y-%m-%d")
        
        # Simple calculation for now
        days = (end - start).days + 1
        
        # TODO: Exclude weekends and center-specific holidays
        # if center_id:
        #     holidays = await self._get_center_holidays(center_id, start_date, end_date)
        #     days -= len(holidays)
        
        return float(days)
    
    async def admin_override_leave_type(
        self,
        leave_id: str,
        admin_id: str,
        new_leave_type: str,
        reason: str
    ) -> bool:
        """
        Super Admin override - change leave type after approval
        """
        leave = await self.db.leaves.find_one({"_id": leave_id})
        if not leave:
            return False
        
        override_record = {
            "changed_by": admin_id,
            "original_type": leave["leave_type"],
            "new_type": new_leave_type,
            "reason": reason,
            "changed_at": datetime.utcnow()
        }
        
        # Update leave type and add to override history
        await self.db.leaves.update_one(
            {"_id": leave_id},
            {
                "$set": {"leave_type": new_leave_type},
                "$push": {"override_history": override_record}
            }
        )
        
        # Adjust leave balances
        await self._adjust_balance_for_override(
            leave["user_id"],
            leave["leave_type"],
            new_leave_type,
            leave["days_count"]
        )
        
        logger.info(f"Leave {leave_id} type changed from {leave['leave_type']} to {new_leave_type} by admin {admin_id}")
        return True
    
    async def _adjust_balance_for_override(
        self,
        user_id: str,
        old_type: str,
        new_type: str,
        days: float
    ):
        """Adjust leave balance when type is overridden"""
        
        # Restore old type balance
        if old_type != "lwp":
            old_balance_key = f"{old_type}_balance"
            await self.db.leave_balances.update_one(
                {"user_id": user_id},
                {"$inc": {old_balance_key: days}}
            )
        
        # Deduct new type balance
        if new_type != "lwp":
            new_balance_key = f"{new_type}_balance"
            await self.db.leave_balances.update_one(
                {"user_id": user_id},
                {"$inc": {new_balance_key: -days}}
            )
