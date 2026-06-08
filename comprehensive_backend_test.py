import requests
import sys
import json
import time
from datetime import datetime

class ComprehensiveLearnHubTester:
    def __init__(self, base_url="https://feature-builder-19.preview.emergentagent.com"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
        self.tests_run = 0
        self.tests_passed = 0
        self.admin_user = None
        self.student_user = None
        self.course_id = None
        self.quiz_id = None

    def run_test(self, name, method, endpoint, expected_status, data=None, cookies=None):
        """Run a single API test"""
        url = f"{self.base_url}/api/{endpoint}"
        
        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        
        try:
            kwargs = {}
            if data:
                kwargs['json'] = data
            if cookies:
                kwargs['cookies'] = cookies
                
            if method == 'GET':
                response = self.session.get(url, **kwargs)
            elif method == 'POST':
                response = self.session.post(url, **kwargs)
            elif method == 'PUT':
                response = self.session.put(url, **kwargs)
            elif method == 'DELETE':
                response = self.session.delete(url, **kwargs)

            success = response.status_code == expected_status
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    return success, response.json(), response.cookies
                except:
                    return success, {}, response.cookies
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_detail = response.json()
                    print(f"   Error: {error_detail}")
                except:
                    print(f"   Error: {response.text}")
                return False, {}, None

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}, None

    def test_admin_login(self):
        """Test admin login and store session"""
        success, response, cookies = self.run_test(
            "Admin Login",
            "POST",
            "auth/login",
            200,
            data={"email": "admin@learnhub.com", "password": "admin123"}
        )
        if success and 'id' in response:
            self.admin_user = response
            # Store cookies for session management
            if cookies:
                self.session.cookies.update(cookies)
            print(f"   Admin logged in: {response.get('name')} ({response.get('role')})")
            return True
        return False

    def test_student_registration_and_login(self):
        """Test student registration and login"""
        timestamp = datetime.now().strftime('%H%M%S')
        test_email = f"student{timestamp}@test.com"
        
        # Register student
        success, response, cookies = self.run_test(
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
            self.student_user = response
            if cookies:
                self.session.cookies.update(cookies)
            print(f"   Student registered and logged in: {response.get('name')}")
            return True, test_email
        return False, None

    def test_create_course_with_video(self):
        """Test creating a course with YouTube video (admin only)"""
        timestamp = datetime.now().strftime('%H%M%S')
        course_data = {
            "title": f"Complete Web Development Course {timestamp}",
            "description": "Learn full-stack web development from scratch. This comprehensive course covers HTML, CSS, JavaScript, React, Node.js, and MongoDB.",
            "video_url": "https://www.youtube.com/watch?v=UB1O30fR-EE",
            "video_type": "youtube",
            "price": 0.0,
            "is_free": True,
            "is_private": False,
            "passing_score": 70,
            "materials": [
                {"name": "Course Slides", "url": "https://example.com/slides.pdf"},
                {"name": "Code Examples", "url": "https://github.com/example/course-code"}
            ]
        }
        
        success, response, _ = self.run_test(
            "Create Course with YouTube Video",
            "POST",
            "courses",
            200,
            data=course_data
        )
        
        if success and 'id' in response:
            self.course_id = response.get('id')
            print(f"   Course created: {response.get('title')} (ID: {self.course_id})")
            return True
        return False

    def test_create_quiz(self):
        """Test creating a quiz for the course"""
        if not self.course_id:
            print("❌ No course ID available for quiz creation")
            return False
            
        quiz_data = {
            "course_id": self.course_id,
            "title": "Web Development Fundamentals Quiz",
            "questions": [
                {
                    "question": "What does HTML stand for?",
                    "options": [
                        "Hyper Text Markup Language",
                        "High Tech Modern Language", 
                        "Home Tool Markup Language",
                        "Hyperlink and Text Markup Language"
                    ],
                    "correct_answer": 0
                },
                {
                    "question": "Which CSS property is used to change the text color?",
                    "options": [
                        "font-color",
                        "text-color",
                        "color",
                        "foreground-color"
                    ],
                    "correct_answer": 2
                },
                {
                    "question": "What is the correct way to declare a JavaScript variable?",
                    "options": [
                        "var myVariable;",
                        "variable myVariable;",
                        "v myVariable;",
                        "declare myVariable;"
                    ],
                    "correct_answer": 0
                }
            ]
        }
        
        success, response, _ = self.run_test(
            "Create Quiz",
            "POST",
            "quizzes",
            200,
            data=quiz_data
        )
        
        if success and 'id' in response:
            self.quiz_id = response.get('id')
            print(f"   Quiz created: {response.get('title')} (ID: {self.quiz_id})")
            return True
        return False

    def test_student_enrollment(self):
        """Test student enrollment in the course"""
        if not self.course_id:
            print("❌ No course ID available for enrollment")
            return False
            
        # Switch to student session
        self.test_student_login()
        
        success, response, _ = self.run_test(
            "Student Course Enrollment",
            "POST",
            "enrollments",
            200,
            data={"course_id": self.course_id}
        )
        return success

    def test_student_login(self):
        """Login as student"""
        if not self.student_user:
            print("❌ No student user available")
            return False
            
        success, response, cookies = self.run_test(
            "Student Login",
            "POST", 
            "auth/login",
            200,
            data={"email": self.student_user['email'], "password": "test123"}
        )
        
        if success and cookies:
            self.session.cookies.update(cookies)
            return True
        return False

    def test_take_quiz(self):
        """Test taking the quiz and getting results"""
        if not self.quiz_id:
            print("❌ No quiz ID available")
            return False
            
        # First get the quiz
        success, quiz_data, _ = self.run_test(
            "Get Quiz",
            "GET",
            f"quizzes/{self.quiz_id}",
            200
        )
        
        if not success:
            return False
            
        # Submit quiz answers (all correct answers)
        answers = [0, 2, 0]  # Correct answers for the quiz
        
        success, response, _ = self.run_test(
            "Submit Quiz",
            "POST",
            f"quizzes/{self.quiz_id}/submit",
            200,
            data={"quiz_id": self.quiz_id, "answers": answers}
        )
        
        if success:
            score = response.get('score', 0)
            passed = response.get('passed', False)
            print(f"   Quiz result: Score {score}%, Passed: {passed}")
            return passed
        return False

    def test_get_certificates(self):
        """Test getting student certificates"""
        success, response, _ = self.run_test(
            "Get Student Certificates",
            "GET",
            "certificates/my",
            200
        )
        
        if success:
            cert_count = len(response) if isinstance(response, list) else 0
            print(f"   Found {cert_count} certificates")
            return cert_count > 0
        return False

    def test_ai_chatbot(self):
        """Test AI chatbot functionality"""
        if not self.course_id:
            print("❌ No course ID available for chat")
            return False
            
        chat_data = {
            "course_id": self.course_id,
            "message": "What are the key concepts I should focus on in web development?"
        }
        
        success, response, _ = self.run_test(
            "AI Chatbot",
            "POST",
            "chat",
            200,
            data=chat_data
        )
        
        if success and 'response' in response:
            ai_response = response.get('response', '')
            print(f"   AI Response length: {len(ai_response)} characters")
            return len(ai_response) > 0
        return False

    def test_forum_post(self):
        """Test forum posting functionality"""
        if not self.course_id:
            print("❌ No course ID available for forum")
            return False
            
        forum_data = {
            "course_id": self.course_id,
            "content": "This is a great course! I'm learning a lot about web development. Does anyone have tips for debugging JavaScript?"
        }
        
        success, response, _ = self.run_test(
            "Create Forum Post",
            "POST",
            "forums/posts",
            200,
            data=forum_data
        )
        
        if success and 'id' in response:
            print(f"   Forum post created: {response.get('id')}")
            
            # Test getting forum posts
            success2, posts, _ = self.run_test(
                "Get Forum Posts",
                "GET",
                f"forums/{self.course_id}",
                200
            )
            
            if success2:
                post_count = len(posts) if isinstance(posts, list) else 0
                print(f"   Found {post_count} forum posts")
                return post_count > 0
        return False

    def test_paid_course_creation(self):
        """Test creating a paid course"""
        # Switch back to admin
        self.test_admin_login()
        
        timestamp = datetime.now().strftime('%H%M%S')
        paid_course_data = {
            "title": f"Advanced React Masterclass {timestamp}",
            "description": "Master advanced React concepts including hooks, context, performance optimization, and testing.",
            "video_url": "https://www.youtube.com/watch?v=Ke90Tje7VS0",
            "video_type": "youtube",
            "price": 99.99,
            "is_free": False,
            "is_private": False,
            "passing_score": 80,
            "materials": [
                {"name": "Advanced React Guide", "url": "https://example.com/react-guide.pdf"}
            ]
        }
        
        success, response, _ = self.run_test(
            "Create Paid Course",
            "POST",
            "courses",
            200,
            data=paid_course_data
        )
        
        if success and 'id' in response:
            paid_course_id = response.get('id')
            print(f"   Paid course created: {response.get('title')} (ID: {paid_course_id})")
            return True, paid_course_id
        return False, None

    def test_payment_checkout(self, paid_course_id):
        """Test Stripe checkout creation"""
        if not paid_course_id:
            print("❌ No paid course ID available")
            return False
            
        # Switch to student
        self.test_student_login()
        
        checkout_data = {
            "course_id": paid_course_id,
            "origin_url": "https://feature-builder-19.preview.emergentagent.com"
        }
        
        success, response, _ = self.run_test(
            "Create Stripe Checkout",
            "POST",
            "payments/checkout",
            200,
            data=checkout_data
        )
        
        if success and 'url' in response:
            checkout_url = response.get('url')
            session_id = response.get('session_id')
            print(f"   Checkout URL created: {checkout_url[:50]}...")
            print(f"   Session ID: {session_id}")
            return True
        return False

    def test_client_manager_functionality(self):
        """Register a student, promote via admin, then verify client manager access"""
        timestamp = datetime.now().strftime('%H%M%S')
        manager_email = f"manager{timestamp}@test.com"

        self.run_test("Logout", "POST", "auth/logout", 200)

        success, response, _ = self.run_test(
            "Client Manager Registration (student)",
            "POST",
            "auth/register",
            200,
            data={
                "email": manager_email,
                "password": "manager123",
                "name": f"Test Manager {timestamp}",
                "role": "client_manager",
            },
        )

        if not success or "id" not in response:
            return False

        user_id = response.get("id")
        if not self.test_admin_login():
            return False

        promote_success, _, _ = self.run_test(
            "Promote to Client Manager",
            "PUT",
            f"users/{user_id}/role?role=client_manager",
            200,
        )
        if not promote_success:
            return False

        login_success, login_response, cookies = self.run_test(
            "Client Manager Login",
            "POST",
            "auth/login",
            200,
            data={"email": manager_email, "password": "manager123"},
        )
        if login_success and cookies:
            self.session.cookies.update(cookies)

        success2, users, _ = self.run_test(
            "Get Users (Client Manager)",
            "GET",
            "users",
            200,
        )
        if success2:
            user_count = len(users) if isinstance(users, list) else 0
            print(f"   Client manager can see {user_count} users")
            return True
        return False

def main():
    print("🚀 Starting Comprehensive LearnHub API Tests")
    print("=" * 60)
    
    tester = ComprehensiveLearnHubTester()
    
    # Test admin login
    if not tester.test_admin_login():
        print("❌ Admin login failed - stopping tests")
        return 1

    # Test course creation with video
    if not tester.test_create_course_with_video():
        print("❌ Course creation failed - stopping tests")
        return 1

    # Test quiz creation
    if not tester.test_create_quiz():
        print("❌ Quiz creation failed")

    # Test student registration and login
    reg_success, student_email = tester.test_student_registration_and_login()
    if not reg_success:
        print("❌ Student registration failed")
        return 1

    # Test student enrollment
    if not tester.test_student_enrollment():
        print("❌ Student enrollment failed")

    # Test taking quiz
    quiz_passed = tester.test_take_quiz()
    if quiz_passed:
        print("✅ Student passed the quiz!")
        
        # Test certificate generation
        tester.test_get_certificates()

    # Test AI chatbot
    tester.test_ai_chatbot()

    # Test forum functionality
    tester.test_forum_post()

    # Test paid course and payment
    paid_success, paid_course_id = tester.test_paid_course_creation()
    if paid_success:
        tester.test_payment_checkout(paid_course_id)

    # Test client manager functionality
    tester.test_client_manager_functionality()

    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {tester.tests_passed}/{tester.tests_run} passed")
    
    success_rate = (tester.tests_passed / tester.tests_run) * 100 if tester.tests_run > 0 else 0
    print(f"📈 Success Rate: {success_rate:.1f}%")
    
    if success_rate >= 80:
        print("🎉 Most tests passed! Backend is functioning well.")
        return 0
    else:
        print(f"⚠️  {tester.tests_run - tester.tests_passed} tests failed")
        return 1

if __name__ == "__main__":
    sys.exit(main())