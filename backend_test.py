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