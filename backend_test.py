#!/usr/bin/env python3
"""
HRMS Backend API Testing Suite
Tests all critical backend functionality including authentication, attendance, leaves, and admin features.
"""

import requests
import json
import sys
from datetime import datetime, date
import time

# Configuration
BASE_URL = "https://smarthr-hub-1.preview.emergentagent.com/api"

# Test credentials
ADMIN_CREDENTIALS = {
    "email": "admin@hrms.com",
    "password": "admin123"
}

EMPLOYEE_CREDENTIALS = {
    "email": "employee@hrms.com", 
    "password": "employee123"
}

# Test data
MAIN_OFFICE_GEOFENCE = {
    "latitude": 28.6139,
    "longitude": 77.2090,
    "radius": 100
}

# Location within geofence (28.6140, 77.2091 - about 15m from center)
VALID_LOCATION = {
    "latitude": 28.6140,
    "longitude": 77.2091
}

# Location outside geofence (28.6200, 77.2200 - about 1.5km away)
INVALID_LOCATION = {
    "latitude": 28.6200,
    "longitude": 77.2200
}

# Small base64 image (1x1 pixel PNG)
SAMPLE_SELFIE = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg=="

class HRMSTestSuite:
    def __init__(self):
        self.admin_token = None
        self.employee_token = None
        self.admin_user = None
        self.employee_user = None
        self.geofence_id = None
        self.test_results = []
        self.failed_tests = []

    def log_test(self, test_name, success, message="", response_data=None):
        """Log test results"""
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if message:
            print(f"   {message}")
        if not success and response_data:
            print(f"   Response: {response_data}")
        
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message,
            "response": response_data
        })
        
        if not success:
            self.failed_tests.append({
                "test": test_name,
                "message": message,
                "response": response_data
            })

    def make_request(self, method, endpoint, data=None, token=None, params=None):
        """Make HTTP request with proper headers"""
        url = f"{BASE_URL}{endpoint}"
        headers = {"Content-Type": "application/json"}
        
        if token:
            headers["Authorization"] = f"Bearer {token}"
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, params=params, timeout=30)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "PUT":
                response = requests.put(url, headers=headers, json=data, timeout=30)
            elif method.upper() == "DELETE":
                response = requests.delete(url, headers=headers, timeout=30)
            
            return response
        except requests.exceptions.RequestException as e:
            print(f"Request failed: {e}")
            return None

    def test_authentication(self):
        """Test authentication endpoints"""
        print("\n=== TESTING AUTHENTICATION ===")
        
        # Test admin login
        response = self.make_request("POST", "/auth/login", ADMIN_CREDENTIALS)
        if response and response.status_code == 200:
            data = response.json()
            self.admin_token = data.get("access_token")
            self.admin_user = data.get("user")
            self.log_test("Admin Login", True, f"Token received, Role: {self.admin_user.get('role')}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Admin Login", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")
            return False

        # Test employee login
        response = self.make_request("POST", "/auth/login", EMPLOYEE_CREDENTIALS)
        if response and response.status_code == 200:
            data = response.json()
            self.employee_token = data.get("access_token")
            self.employee_user = data.get("user")
            self.log_test("Employee Login", True, f"Token received, Role: {self.employee_user.get('role')}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Employee Login", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")
            return False

        # Test token validation with /auth/me
        response = self.make_request("GET", "/auth/me", token=self.admin_token)
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Admin Token Validation", True, f"User: {data.get('full_name')}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Admin Token Validation", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        response = self.make_request("GET", "/auth/me", token=self.employee_token)
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Employee Token Validation", True, f"User: {data.get('full_name')}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Employee Token Validation", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Test invalid credentials
        invalid_creds = {"email": "invalid@test.com", "password": "wrongpass"}
        response = self.make_request("POST", "/auth/login", invalid_creds)
        if response and response.status_code == 401:
            self.log_test("Invalid Credentials Rejection", True, "Correctly rejected invalid credentials")
        else:
            self.log_test("Invalid Credentials Rejection", False, f"Expected 401, got {response.status_code if response else 'No response'}")

        return True

    def test_geofence_management(self):
        """Test geofence management"""
        print("\n=== TESTING GEOFENCE MANAGEMENT ===")
        
        # Get existing geofences
        response = self.make_request("GET", "/geofences", token=self.employee_token)
        if response and response.status_code == 200:
            geofences = response.json()
            self.log_test("Get Geofences", True, f"Found {len(geofences)} geofences")
            
            # Find Main Office geofence
            main_office = None
            for gf in geofences:
                if gf.get("name") == "Main Office":
                    main_office = gf
                    self.geofence_id = gf.get("id")
                    break
            
            if main_office:
                self.log_test("Main Office Geofence Found", True, f"ID: {self.geofence_id}, Radius: {main_office.get('radius')}m")
            else:
                self.log_test("Main Office Geofence Found", False, "Main Office geofence not found in seed data")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get Geofences", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Test creating geofence (admin only)
        if self.admin_token:
            new_geofence = {
                "name": "Test Branch",
                "latitude": 28.7041,
                "longitude": 77.1025,
                "radius": 50.0,
                "address": "Test Address"
            }
            response = self.make_request("POST", "/geofences", new_geofence, token=self.admin_token)
            if response and response.status_code == 200:
                data = response.json()
                self.log_test("Create Geofence (Admin)", True, f"Created geofence: {data.get('name')}")
            else:
                error_msg = response.json().get("detail", "Unknown error") if response else "No response"
                self.log_test("Create Geofence (Admin)", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Test creating geofence as employee (should fail)
        if self.employee_token:
            response = self.make_request("POST", "/geofences", new_geofence, token=self.employee_token)
            if response and response.status_code == 403:
                self.log_test("Create Geofence (Employee - Should Fail)", True, "Correctly rejected employee geofence creation")
            else:
                self.log_test("Create Geofence (Employee - Should Fail)", False, f"Expected 403, got {response.status_code if response else 'No response'}")

    def test_attendance_management(self):
        """Test attendance management"""
        print("\n=== TESTING ATTENDANCE MANAGEMENT ===")
        
        if not self.employee_token or not self.geofence_id:
            self.log_test("Attendance Tests", False, "Missing employee token or geofence ID")
            return

        # Check initial attendance status
        response = self.make_request("GET", "/attendance/today-status", token=self.employee_token)
        if response and response.status_code == 200:
            status = response.json()
            self.log_test("Get Today Status (Initial)", True, f"Checked in: {status.get('checked_in')}, Checked out: {status.get('checked_out')}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get Today Status (Initial)", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Test check-in with valid location
        checkin_data = {
            "latitude": VALID_LOCATION["latitude"],
            "longitude": VALID_LOCATION["longitude"],
            "selfie_base64": SAMPLE_SELFIE,
            "geofence_id": self.geofence_id
        }
        
        response = self.make_request("POST", "/attendance/checkin", checkin_data, token=self.employee_token)
        if response and response.status_code == 200:
            data = response.json()
            self.log_test("Check-in (Valid Location)", True, f"Checked in at {data.get('check_in_time')}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Check-in (Valid Location)", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Verify checked in status
        response = self.make_request("GET", "/attendance/today-status", token=self.employee_token)
        if response and response.status_code == 200:
            status = response.json()
            if status.get("checked_in"):
                self.log_test("Verify Checked In Status", True, f"Check-in time: {status.get('check_in_time')}")
            else:
                self.log_test("Verify Checked In Status", False, "Status shows not checked in")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Verify Checked In Status", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Test duplicate check-in (should fail)
        response = self.make_request("POST", "/attendance/checkin", checkin_data, token=self.employee_token)
        if response and response.status_code == 400:
            self.log_test("Duplicate Check-in Prevention", True, "Correctly prevented duplicate check-in")
        else:
            self.log_test("Duplicate Check-in Prevention", False, f"Expected 400, got {response.status_code if response else 'No response'}")

        # Test check-out
        checkout_data = {
            "latitude": VALID_LOCATION["latitude"],
            "longitude": VALID_LOCATION["longitude"]
        }
        
        response = self.make_request("POST", "/attendance/checkout", checkout_data, token=self.employee_token)
        if response and response.status_code == 200:
            self.log_test("Check-out", True, "Successfully checked out")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Check-out", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Verify checked out status
        response = self.make_request("GET", "/attendance/today-status", token=self.employee_token)
        if response and response.status_code == 200:
            status = response.json()
            if status.get("checked_out"):
                self.log_test("Verify Checked Out Status", True, f"Check-out time: {status.get('check_out_time')}")
            else:
                self.log_test("Verify Checked Out Status", False, "Status shows not checked out")

        # Test attendance history
        response = self.make_request("GET", "/attendance/my-history", token=self.employee_token)
        if response and response.status_code == 200:
            history = response.json()
            self.log_test("Get Attendance History", True, f"Found {len(history)} attendance records")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get Attendance History", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

    def test_geofence_validation(self):
        """Test geofence validation with invalid location"""
        print("\n=== TESTING GEOFENCE VALIDATION ===")
        
        if not self.employee_token or not self.geofence_id:
            self.log_test("Geofence Validation Tests", False, "Missing employee token or geofence ID")
            return

        # Test check-in with invalid location (outside geofence)
        invalid_checkin = {
            "latitude": INVALID_LOCATION["latitude"],
            "longitude": INVALID_LOCATION["longitude"],
            "selfie_base64": SAMPLE_SELFIE,
            "geofence_id": self.geofence_id
        }
        
        response = self.make_request("POST", "/attendance/checkin", invalid_checkin, token=self.employee_token)
        if response and response.status_code == 400:
            error_detail = response.json().get("detail", "")
            if "Outside geofence boundary" in error_detail:
                self.log_test("Geofence Boundary Validation", True, f"Correctly rejected outside location: {error_detail}")
            else:
                self.log_test("Geofence Boundary Validation", False, f"Wrong error message: {error_detail}")
        else:
            self.log_test("Geofence Boundary Validation", False, f"Expected 400, got {response.status_code if response else 'No response'}")

    def test_leave_management(self):
        """Test leave management"""
        print("\n=== TESTING LEAVE MANAGEMENT ===")
        
        if not self.employee_token:
            self.log_test("Leave Management Tests", False, "Missing employee token")
            return

        # Check initial leave balance
        response = self.make_request("GET", "/leaves/balance", token=self.employee_token)
        if response and response.status_code == 200:
            balance = response.json()
            initial_casual = balance.get("casual_balance", 0)
            self.log_test("Get Leave Balance", True, f"Sick: {balance.get('sick_balance')}, Casual: {balance.get('casual_balance')}, Earned: {balance.get('earned_balance')}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get Leave Balance", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")
            return

        # Apply for casual leave
        leave_request = {
            "leave_type": "casual",
            "start_date": "2024-01-15",
            "end_date": "2024-01-15",
            "reason": "Personal work",
            "days_count": 1.0
        }
        
        response = self.make_request("POST", "/leaves/apply", leave_request, token=self.employee_token)
        leave_id = None
        if response and response.status_code == 200:
            data = response.json()
            leave_id = data.get("id")
            self.log_test("Apply Leave", True, f"Leave applied with ID: {leave_id}, Status: {data.get('status')}")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Apply Leave", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Get my leaves
        response = self.make_request("GET", "/leaves/my-leaves", token=self.employee_token)
        if response and response.status_code == 200:
            leaves = response.json()
            self.log_test("Get My Leaves", True, f"Found {len(leaves)} leave applications")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get My Leaves", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Test admin leave approval
        if self.admin_token and leave_id:
            # Get pending leaves (admin)
            response = self.make_request("GET", "/leaves/pending", token=self.admin_token)
            if response and response.status_code == 200:
                pending_leaves = response.json()
                self.log_test("Get Pending Leaves (Admin)", True, f"Found {len(pending_leaves)} pending leaves")
            else:
                error_msg = response.json().get("detail", "Unknown error") if response else "No response"
                self.log_test("Get Pending Leaves (Admin)", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

            # Approve the leave
            approval_data = {
                "leave_id": leave_id,
                "status": "approved",
                "remarks": "Approved by admin"
            }
            
            response = self.make_request("POST", "/leaves/approve", approval_data, token=self.admin_token)
            if response and response.status_code == 200:
                self.log_test("Approve Leave (Admin)", True, "Leave approved successfully")
                
                # Verify balance deduction
                response = self.make_request("GET", "/leaves/balance", token=self.employee_token)
                if response and response.status_code == 200:
                    new_balance = response.json()
                    new_casual = new_balance.get("casual_balance", 0)
                    if new_casual == initial_casual - 1:
                        self.log_test("Leave Balance Deduction", True, f"Balance correctly deducted: {initial_casual} -> {new_casual}")
                    else:
                        self.log_test("Leave Balance Deduction", False, f"Balance not deducted correctly: {initial_casual} -> {new_casual}")
            else:
                error_msg = response.json().get("detail", "Unknown error") if response else "No response"
                self.log_test("Approve Leave (Admin)", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Test employee trying to approve leave (should fail)
        if leave_id:
            approval_data = {
                "leave_id": leave_id,
                "status": "approved",
                "remarks": "Employee trying to approve"
            }
            
            response = self.make_request("POST", "/leaves/approve", approval_data, token=self.employee_token)
            if response and response.status_code == 403:
                self.log_test("Employee Leave Approval (Should Fail)", True, "Correctly rejected employee approval attempt")
            else:
                self.log_test("Employee Leave Approval (Should Fail)", False, f"Expected 403, got {response.status_code if response else 'No response'}")

    def test_location_tracking(self):
        """Test location tracking"""
        print("\n=== TESTING LOCATION TRACKING ===")
        
        if not self.employee_token:
            self.log_test("Location Tracking Tests", False, "Missing employee token")
            return

        # Update location (should fail if not checked in)
        location_data = {
            "latitude": VALID_LOCATION["latitude"],
            "longitude": VALID_LOCATION["longitude"],
            "timestamp": datetime.utcnow().isoformat()
        }
        
        response = self.make_request("POST", "/location/update", location_data, token=self.employee_token)
        if response and response.status_code == 400:
            self.log_test("Location Update (Not Checked In)", True, "Correctly rejected location update when not checked in")
        else:
            # If user is checked in, it should succeed
            if response and response.status_code == 200:
                self.log_test("Location Update", True, "Location updated successfully")
            else:
                error_msg = response.json().get("detail", "Unknown error") if response else "No response"
                self.log_test("Location Update", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Get location history
        today = date.today().isoformat()
        user_id = self.employee_user.get("id") if self.employee_user else "test"
        
        response = self.make_request("GET", f"/location/history/{user_id}/{today}", token=self.employee_token)
        if response and response.status_code == 200:
            history = response.json()
            locations = history.get("locations", [])
            self.log_test("Get Location History", True, f"Found {len(locations)} location records")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get Location History", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

    def test_admin_endpoints(self):
        """Test admin-only endpoints"""
        print("\n=== TESTING ADMIN ENDPOINTS ===")
        
        if not self.admin_token:
            self.log_test("Admin Endpoints Tests", False, "Missing admin token")
            return

        # Get all users
        response = self.make_request("GET", "/admin/users", token=self.admin_token)
        if response and response.status_code == 200:
            users = response.json()
            self.log_test("Get All Users (Admin)", True, f"Found {len(users)} users")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get All Users (Admin)", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Get all attendance
        response = self.make_request("GET", "/admin/attendance/all", token=self.admin_token)
        if response and response.status_code == 200:
            attendance = response.json()
            self.log_test("Get All Attendance (Admin)", True, f"Found {len(attendance)} attendance records")
        else:
            error_msg = response.json().get("detail", "Unknown error") if response else "No response"
            self.log_test("Get All Attendance (Admin)", False, f"Status: {response.status_code if response else 'No response'}, Error: {error_msg}")

        # Test employee access to admin endpoints (should fail)
        if self.employee_token:
            response = self.make_request("GET", "/admin/users", token=self.employee_token)
            if response and response.status_code == 403:
                self.log_test("Employee Admin Access (Should Fail)", True, "Correctly rejected employee admin access")
            else:
                self.log_test("Employee Admin Access (Should Fail)", False, f"Expected 403, got {response.status_code if response else 'No response'}")

    def run_all_tests(self):
        """Run all test suites"""
        print("🚀 Starting HRMS Backend API Tests")
        print(f"📍 Testing against: {BASE_URL}")
        
        start_time = time.time()
        
        # Run test suites in order
        if not self.test_authentication():
            print("❌ Authentication failed - stopping tests")
            return
            
        self.test_geofence_management()
        self.test_attendance_management()
        self.test_geofence_validation()
        self.test_leave_management()
        self.test_location_tracking()
        self.test_admin_endpoints()
        
        # Summary
        end_time = time.time()
        duration = end_time - start_time
        
        total_tests = len(self.test_results)
        passed_tests = len([t for t in self.test_results if t["success"]])
        failed_tests = len(self.failed_tests)
        
        print(f"\n{'='*60}")
        print(f"🏁 TEST SUMMARY")
        print(f"{'='*60}")
        print(f"⏱️  Duration: {duration:.2f} seconds")
        print(f"📊 Total Tests: {total_tests}")
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {(passed_tests/total_tests*100):.1f}%")
        
        if self.failed_tests:
            print(f"\n❌ FAILED TESTS:")
            for i, test in enumerate(self.failed_tests, 1):
                print(f"{i}. {test['test']}")
                if test['message']:
                    print(f"   Error: {test['message']}")
        
        return failed_tests == 0

if __name__ == "__main__":
    test_suite = HRMSTestSuite()
    success = test_suite.run_all_tests()
    
    if success:
        print("\n🎉 All tests passed!")
        sys.exit(0)
    else:
        print(f"\n💥 {len(test_suite.failed_tests)} tests failed!")
        sys.exit(1)