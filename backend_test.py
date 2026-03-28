import requests
import sys
import json
from datetime import datetime

class LearnHubAPITester:
    def __init__(self, base_url="https://feature-builder-19.preview.emergentagent.com"):
        self.base_url = base_url
        self.token = None
        self.admin_token = None
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def run_test(self, name, method, endpoint, expected_status, data=None, use_admin=False):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        headers = {'Content-Type': 'application/json'}
        
        # Use admin token if specified
        token_to_use = self.admin_token if use_admin else self.token
        if token_to_use:
            headers['Authorization'] = f'Bearer {token_to_use}'

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url, headers=headers)
            elif method == 'POST':
                response = self.session.post(url, json=data, headers=headers)
            elif method == 'PUT':
                response = self.session.put(url, json=data, headers=headers)
            elif method == 'DELETE':
                response = self.session.delete(url, headers=headers)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json()
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test API root endpoint"""
        return self.run_test("API Root", "GET", "", 200)

    def test_admin_login(self):
        """Test admin login"""
        success, response = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@learnhub.com", "password": "admin123"}
        )
        if success and 'id' in response:
            # Extract token from cookies if available
            print(f"   Admin logged in: {response.get('name')} ({response.get('role')})")
            return True
        return False

    def test_student_registration(self):
        """Test student registration"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_email = f"student{timestamp}@test.com"
        
        success, response = self.run_test(
            "Student Registration",
            "POST",
            "auth/register",
            200,
            data={
                "email": test_email,
                "password": "test123",
                "name": f"Test Student {timestamp}",
                "role": "student"
            }
        )
        if success and 'id' in response:
            print(f"   Student registered: {response.get('name')} ({response.get('email')})")
            return True, test_email
        return False, None

    def test_student_login(self, email):
        """Test student login"""
        success, response = self.run_test(
            "Student Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": "test123"}
        )
        if success and 'id' in response:
            print(f"   Student logged in: {response.get('name')}")
            return True
        return False

    def test_get_courses(self):
        """Test getting courses list"""
        return self.run_test("Get Courses", "GET", "courses", 200)

    def test_create_course(self):
        """Test creating a course (admin only)"""
        timestamp = datetime.now().strftime('%H%M%S')
        course_data = {
            "title": f"Test Course {timestamp}",
            "description": "This is a test course for API testing",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "video_type": "youtube",
            "price": 0.0,
            "is_free": True,
            "is_private": False,
            "passing_score": 70,
            "materials": [
                {"name": "Test Material", "url": "https://example.com/material.pdf"}
            ]
        }
        
        success, response = self.run_test(
            "Create Course",
            "POST",
            "courses",
            200,
            data=course_data,
            use_admin=True
        )
        if success and 'id' in response:
            print(f"   Course created: {response.get('title')} (ID: {response.get('id')})")
            return True, response.get('id')
        return False, None

    def test_get_course_detail(self, course_id):
        """Test getting course details"""
        return self.run_test("Get Course Detail", "GET", f"courses/{course_id}", 200)

    def test_enrollment(self, course_id):
        """Test course enrollment"""
        success, response = self.run_test(
            "Course Enrollment",
            "POST",
            "enrollments",
            200,
            data={"course_id": course_id}
        )
        return success

    def test_get_my_enrollments(self):
        """Test getting user's enrollments"""
        return self.run_test("Get My Enrollments", "GET", "enrollments/my", 200)

    def test_admin_stats(self):
        """Test admin dashboard stats"""
        return self.run_test("Admin Stats", "GET", "stats/admin", 200, use_admin=True)

    def test_student_stats(self):
        """Test student dashboard stats"""
        return self.run_test("Student Stats", "GET", "stats/student", 200)

    def test_auth_me(self):
        """Test getting current user info"""
        return self.run_test("Auth Me", "GET", "auth/me", 200)

def main():
    print("🚀 Starting LearnHub API Tests")
    print("=" * 50)
    
    tester = LearnHubAPITester()
    
    # Test API root
    success, _ = tester.test_root_endpoint()
    if not success:
        print("❌ API root endpoint failed - stopping tests")
        return 1

    # Test admin login
    if not tester.test_admin_login():
        print("❌ Admin login failed - stopping tests")
        return 1

    # Test admin stats
    tester.test_admin_stats()

    # Test student registration and login
    reg_success, student_email = tester.test_student_registration()
    if not reg_success:
        print("❌ Student registration failed")
        return 1

    if not tester.test_student_login(student_email):
        print("❌ Student login failed")
        return 1

    # Test student stats and auth
    tester.test_student_stats()
    tester.test_auth_me()

    # Test course operations
    tester.test_get_courses()
    
    # Create a course as admin (need to login as admin again)
    tester.test_admin_login()
    course_success, course_id = tester.test_create_course()
    
    if course_success and course_id:
        # Test course detail
        tester.test_get_course_detail(course_id)
        
        # Login as student again for enrollment
        tester.test_student_login(student_email)
        
        # Test enrollment
        tester.test_enrollment(course_id)
        tester.test_get_my_enrollments()

    # Print final results
    print("\n" + "=" * 50)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())