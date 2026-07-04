import requests
import sys
import json
import os
from datetime import datetime

ADMIN_EMAIL = os.environ.get("ADMIN_EMAIL", "admin@learnhub.com")
ADMIN_PASSWORD = os.environ.get("ADMIN_PASSWORD", "admin123")

class LearnHubAPITester:
    def __init__(self, base_url="https://feature-builder-19.preview.emergentagent.com"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

    def run_test(self, name, method, endpoint, expected_status, data=None, use_admin=False):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            if method == 'GET':
                response = self.session.get(url)
            elif method == 'POST':
                response = self.session.post(url, json=data)
            elif method == 'PUT':
                response = self.session.put(url, json=data)
            elif method == 'DELETE':
                response = self.session.delete(url)

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
            data={"email": ADMIN_EMAIL, "password": ADMIN_PASSWORD}
        )
        if success and 'id' in response:
            # Extract token from cookies if available
            print(f"   Admin logged in: {response.get('name')} ({response.get('role')})")
            # Verify admin authentication by checking /auth/me
            auth_success, auth_response = self.run_test(
                "Verify Admin Auth",
                "GET",
                "auth/me",
                200
            )
            if auth_success:
                print(f"   Admin auth verified: {auth_response.get('role')}")
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

    def test_get_languages(self):
        """Test getting supported languages"""
        success, response = self.run_test("Get Languages", "GET", "languages", 200)
        if success:
            languages = response.get('languages', [])
            names = response.get('names', {})
            print(f"   Supported languages: {languages}")
            print(f"   Language names: {names}")
            # Verify expected languages are present
            expected_langs = ["en", "zh-TW", "zh-CN", "ja", "ko"]
            missing_langs = [lang for lang in expected_langs if lang not in languages]
            if missing_langs:
                print(f"   ⚠️  Missing languages: {missing_langs}")
                return False
            return True
        return False

    def test_create_course_with_language(self, language="zh-TW"):
        """Test creating a course with specific language"""
        timestamp = datetime.now().strftime('%H%M%S')
        course_data = {
            "title": f"多語言測試課程 {timestamp}",
            "description": "這是一個多語言測試課程",
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
            "video_type": "youtube",
            "price": 0.0,
            "is_free": True,
            "is_private": False,
            "passing_score": 70,
            "language": language,
            "materials": []
        }
        
        success, response = self.run_test(
            f"Create Course with Language ({language})",
            "POST",
            "courses",
            200,
            data=course_data,
            use_admin=True
        )
        if success and 'id' in response:
            print(f"   Course created with language {language}: {response.get('title')} (ID: {response.get('id')})")
            return True, response.get('id')
        return False, None

    def test_get_courses_with_language_filter(self, language="zh-TW"):
        """Test getting courses filtered by language"""
        success, response = self.run_test(
            f"Get Courses with Language Filter ({language})",
            "GET",
            f"courses?language={language}",
            200
        )
        if success:
            courses = response if isinstance(response, list) else []
            print(f"   Found {len(courses)} courses for language {language}")
            # Verify all returned courses have the correct language
            for course in courses:
                if course.get('language') != language:
                    print(f"   ⚠️  Course {course.get('id')} has wrong language: {course.get('language')}")
                    return False
            return True
        return False

    def test_get_courses_with_search(self, search_term="測試"):
        """Test course search functionality"""
        success, response = self.run_test(
            f"Search Courses ({search_term})",
            "GET",
            f"courses?search={search_term}",
            200
        )
        if success:
            courses = response if isinstance(response, list) else []
            print(f"   Found {len(courses)} courses matching '{search_term}'")
            return True
        return False

    def test_create_course_invalid_language(self):
        """Test creating course with invalid language"""
        timestamp = datetime.now().strftime('%H%M%S')
        course_data = {
            "title": f"Invalid Language Course {timestamp}",
            "description": "Course with invalid language",
            "language": "invalid-lang",
            "price": 0.0,
            "is_free": True
        }
        
        success, response = self.run_test(
            "Create Course with Invalid Language",
            "POST",
            "courses",
            400,  # Should fail with 400
            data=course_data,
            use_admin=True
        )
        return success  # Success means it correctly rejected invalid language

    def test_translate_text(self):
        """Test text translation endpoint"""
        translate_data = {
            "text": "Hello, this is a test course",
            "source_language": "en",
            "target_language": "zh-TW"
        }
        
        success, response = self.run_test(
            "Translate Text",
            "POST",
            "translate/text",
            200,
            data=translate_data,
            use_admin=True
        )
        if success and 'translated_text' in response:
            print(f"   Translated text: {response.get('translated_text')}")
            return True
        return False

    def test_translate_course(self, course_id):
        """Test course translation endpoint"""
        translate_data = {
            "course_id": course_id,
            "target_languages": ["zh-TW", "ja", "ko"]
        }
        
        success, response = self.run_test(
            "Translate Course",
            "POST",
            f"translate/course/{course_id}",
            200,
            data=translate_data,
            use_admin=True
        )
        if success and 'translations' in response:
            translations = response.get('translations', {})
            print(f"   Translations created for languages: {list(translations.keys())}")
            for lang, trans in translations.items():
                if 'title' in trans:
                    print(f"   {lang}: {trans['title']}")
            return True
        return False

    def test_create_translated_course(self, source_course_id, target_language="zh-TW"):
        """Test creating a translated course"""
        success, response = self.run_test(
            f"Create Translated Course ({target_language})",
            "POST",
            f"courses/{source_course_id}/create-translation?target_language={target_language}",
            200,
            use_admin=True
        )
        if success and 'new_course_id' in response:
            new_course_id = response.get('new_course_id')
            translated_title = response.get('title')
            print(f"   New translated course created: {translated_title} (ID: {new_course_id})")
            return True, new_course_id
        return False, None

    def test_bulk_enrollment(self, course_id, user_ids):
        """Test bulk enrollment (admin only)"""
        success, response = self.run_test(
            "Bulk Enrollment",
            "POST",
            "enrollments",
            200,
            data={"course_id": course_id, "user_ids": user_ids},
            use_admin=True
        )
        if success:
            enrolled_count = len(response.get('enrolled', []))
            print(f"   Bulk enrolled {enrolled_count} users")
            return True
        return False

    def test_groups_overview(self):
        """Test groups overview endpoint (admin/client_manager)"""
        success, response = self.run_test(
            "Groups Overview",
            "GET",
            "groups/overview",
            200,
            use_admin=True
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} courses in overview")
            for course in response[:3]:  # Show first 3 courses
                print(f"   Course: {course.get('course_title')} - Enrolled: {course.get('total_enrolled')}, Completed: {course.get('completed')}")
            return True
        return False

    def test_course_group_progress(self, course_id):
        """Test course group progress endpoint"""
        success, response = self.run_test(
            "Course Group Progress",
            "GET",
            f"groups/course/{course_id}/progress",
            200,
            use_admin=True
        )
        if success and 'summary' in response:
            summary = response.get('summary', {})
            students = response.get('students', [])
            print(f"   Course progress - Total: {summary.get('total_enrolled')}, Completed: {summary.get('completed')}")
            print(f"   Students tracked: {len(students)}")
            return True
        return False

    def test_student_progress(self, user_id):
        """Test individual student progress endpoint"""
        success, response = self.run_test(
            "Student Progress",
            "GET",
            f"groups/student/{user_id}/progress",
            200,
            use_admin=True
        )
        if success and 'summary' in response:
            summary = response.get('summary', {})
            courses = response.get('courses', [])
            print(f"   Student progress - Enrolled: {summary.get('total_enrolled')}, Completed: {summary.get('completed')}")
            print(f"   Courses: {len(courses)}")
            return True
        return False

    def test_course_enrollments(self, course_id):
        """Test getting course enrollments (admin/client_manager)"""
        success, response = self.run_test(
            "Course Enrollments",
            "GET",
            f"enrollments/course/{course_id}",
            200,
            use_admin=True
        )
        if success and isinstance(response, list):
            print(f"   Found {len(response)} enrollments for course")
            return True
        return False

    def test_client_manager_registration(self):
        """Register a student and promote to client_manager via admin API"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_email = f"manager{timestamp}@test.com"

        self.run_test("Logout before manager signup", "POST", "auth/logout", 200)

        success, response = self.run_test(
            "Client Manager Registration (student)",
            "POST",
            "auth/register",
            200,
            data={
                "email": test_email,
                "password": "test123",
                "name": f"Test Manager {timestamp}",
                "role": "client_manager",
            },
        )
        if not success or "id" not in response:
            return False, None, None

        user_id = response.get("id")
        if response.get("role") != "student":
            print(f"   Warning: registration returned role {response.get('role')}, expected student")

        if not self.test_admin_login():
            return False, None, None

        promote_success, _ = self.run_test(
            "Promote to Client Manager",
            "PUT",
            f"users/{user_id}/role?role=client_manager",
            200,
        )
        if promote_success:
            print(f"   Client Manager created: {response.get('name')} ({test_email})")
            return True, test_email, user_id
        return False, None, None

    def test_client_manager_login(self, email):
        """Test client manager login"""
        success, response = self.run_test(
            "Client Manager Login",
            "POST",
            "auth/login",
            200,
            data={"email": email, "password": "test123"}
        )
        if success and 'id' in response:
            print(f"   Client Manager logged in: {response.get('name')}")
            return True
        return False

def main():
    print("🚀 Starting LearnHub API Tests - Role Management & Email Notifications")
    print("=" * 70)
    
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

    # Test client manager registration and login
    print("\n👥 Testing Client Manager Role")
    manager_success, manager_email, manager_id = tester.test_client_manager_registration()
    if manager_success:
        tester.test_client_manager_login(manager_email)

    # Test student stats and auth
    tester.test_student_stats()
    tester.test_auth_me()

    # Test language features
    print("\n🌐 Testing Multi-Language Features")
    tester.test_get_languages()

    # Test course operations
    tester.test_get_courses()
    
    # Create a course as admin (need to login as admin again)
    tester.test_admin_login()
    course_success, course_id = tester.test_create_course()
    
    # Test multi-language course creation
    zh_course_success, zh_course_id = tester.test_create_course_with_language("zh-TW")
    ja_course_success, ja_course_id = tester.test_create_course_with_language("ja")
    
    # Test invalid language
    tester.test_create_course_invalid_language()
    
    # Test language filtering
    if zh_course_success:
        tester.test_get_courses_with_language_filter("zh-TW")
    if ja_course_success:
        tester.test_get_courses_with_language_filter("ja")
    
    # Test search functionality
    tester.test_get_courses_with_search("測試")
    tester.test_get_courses_with_search("Test")
    
    if course_success and course_id:
        # Test course detail
        tester.test_get_course_detail(course_id)
        
        # Test translation features
        print("\n🌐 Testing Auto-Translation Features")
        tester.test_translate_text()
        tester.test_translate_course(course_id)
        
        # Test creating translated course
        translated_success, translated_course_id = tester.test_create_translated_course(course_id, "zh-TW")
        if translated_success:
            # Verify the translated course exists
            tester.test_get_course_detail(translated_course_id)
        
        # Login as student again for enrollment
        tester.test_student_login(student_email)
        
        # Test enrollment
        tester.test_enrollment(course_id)
        tester.test_get_my_enrollments()

        # Test NEW FEATURES - Admin Bulk Enrollment & Group Progress
        print("\n📊 Testing New Admin Features - Bulk Enrollment & Group Progress")
        
        # Login as admin for bulk enrollment
        tester.test_admin_login()
        
        # Create additional students for bulk enrollment
        student_ids = []
        for i in range(2):
            timestamp = datetime.now().strftime('%H%M%S') + str(i)
            test_email = f"bulkstudent{timestamp}@test.com"
            reg_success, response = tester.run_test(
                f"Create Bulk Student {i+1}",
                "POST",
                "auth/register",
                200,
                data={
                    "email": test_email,
                    "password": "test123",
                    "name": f"Bulk Student {i+1}",
                    "role": "student"
                }
            )
            if reg_success and 'id' in response:
                student_ids.append(response['id'])
        
        # Login as admin again after creating students
        tester.test_admin_login()
        
        # Test bulk enrollment
        if student_ids:
            tester.test_bulk_enrollment(course_id, student_ids)
        
        # Test group progress endpoints
        print("\n🔍 Checking admin authentication before group tests...")
        auth_success, auth_response = tester.run_test(
            "Check Current User",
            "GET",
            "auth/me",
            200
        )
        if auth_success:
            print(f"   Current user: {auth_response.get('name')} ({auth_response.get('role')})")
        
        tester.test_groups_overview()
        tester.test_course_group_progress(course_id)
        tester.test_course_enrollments(course_id)
        
        # Test individual student progress
        if student_ids:
            tester.test_student_progress(student_ids[0])
        
        # Test Client Manager access to group progress
        if manager_success:
            print("\n👥 Testing Client Manager Group Progress Access")
            tester.test_client_manager_login(manager_email)
            tester.test_groups_overview()
            tester.test_course_group_progress(course_id)

    # Print final results
    print("\n" + "=" * 70)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed!")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())