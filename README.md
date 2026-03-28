# LearnHub - Kajabi-like Course Platform

A comprehensive online learning platform built with React, FastAPI, and MongoDB. Features multi-language support, AI-powered translation, quizzes, certificates, and Stripe payments.

---

## 🎯 Overview

LearnHub is a full-featured Learning Management System (LMS) that enables organizations to create, manage, and deliver online courses to students worldwide. The platform supports multiple languages, AI-powered content translation, and comprehensive course management.

---

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT LAYER                            │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   React Frontend                         │   │
│  │  • Landing Page    • Course Player    • Admin Dashboard  │   │
│  │  • Auth Pages      • Quiz System      • Certificate View │   │
│  │  • i18n (EN/繁中)  • AI Chat          • Forum            │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                         API LAYER                               │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                   FastAPI Backend                        │   │
│  │  • REST API        • JWT Auth         • Role-based ACL   │   │
│  │  • Course CRUD     • Quiz Engine      • Payment Handler  │   │
│  │  • AI Translation  • Chatbot          • Webhook Handler  │   │
│  └─────────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                       DATA LAYER                                │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │   MongoDB    │  │  Deepseek AI │  │    Stripe    │          │
│  │  (Database)  │  │  (Chat/Trans)│  │  (Payments)  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
└─────────────────────────────────────────────────────────────────┘
```

---

## 📁 File Structure

```
/app
├── backend/
│   ├── server.py              # Main FastAPI application (all routes & logic)
│   ├── requirements.txt       # Python dependencies
│   └── .env                   # Environment variables (DB, API keys)
│
├── frontend/
│   ├── public/
│   │   └── index.html         # HTML entry point
│   ├── src/
│   │   ├── App.js             # Main React application (all components)
│   │   ├── App.css            # Custom styles
│   │   ├── index.js           # React entry point
│   │   ├── index.css          # Tailwind imports
│   │   ├── i18n.js            # Internationalization (EN/繁中 translations)
│   │   ├── hooks/
│   │   │   └── use-toast.js   # Toast notification hook
│   │   └── components/
│   │       └── ui/            # Shadcn UI components
│   │           ├── button.jsx
│   │           ├── card.jsx
│   │           ├── dialog.jsx
│   │           ├── input.jsx
│   │           ├── select.jsx
│   │           ├── tabs.jsx
│   │           └── ...
│   ├── package.json           # Node.js dependencies
│   ├── tailwind.config.js     # Tailwind CSS configuration
│   └── .env                   # Frontend environment variables
│
├── memory/
│   ├── PRD.md                 # Product Requirements Document
│   └── test_credentials.md    # Test account credentials
│
├── test_reports/              # Automated test results
│   └── iteration_*.json
│
└── README.md                  # This file
```

---

## 💻 Tech Stack

### Frontend
| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.x | UI Framework |
| React Router | 6.x | Client-side routing |
| Tailwind CSS | 3.x | Utility-first styling |
| Shadcn UI | Latest | Component library |
| Axios | Latest | HTTP client |
| Lucide React | Latest | Icon library |
| Sonner | Latest | Toast notifications |

### Backend
| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.100+ | Web framework |
| Motor | Latest | Async MongoDB driver |
| PyJWT | Latest | JWT authentication |
| Bcrypt | Latest | Password hashing |
| OpenAI SDK | Latest | Deepseek AI integration |

### Database
| Technology | Purpose |
|------------|---------|
| MongoDB | Primary database |
| Collections | users, courses, lessons, quizzes, quiz_attempts, enrollments, certificates, forum_posts, chat_messages, payment_transactions |

### External Services
| Service | Purpose |
|---------|---------|
| Deepseek AI | Chatbot & Auto-translation |
| Stripe | Payment processing |

---

## 🗄️ Database Schema

### Collections

#### `users`
```javascript
{
  _id: ObjectId,
  email: String (unique),
  password_hash: String,
  name: String,
  role: String ["admin", "client_manager", "student"],
  created_at: ISODate
}
```

#### `courses`
```javascript
{
  _id: ObjectId,
  title: String,
  description: String,
  thumbnail_url: String,
  video_url: String,
  video_type: String ["youtube", "vimeo"],
  price: Number,
  is_free: Boolean,
  is_private: Boolean,
  passing_score: Number (0-100),
  materials: Array [{name, url}],
  language: String ["en", "zh-TW", "zh-CN", "ja", "ko"],
  category: String,
  translations: Object {lang_code: {title, description}},
  source_course_id: String (for translated courses),
  created_by: String (user_id),
  created_at: ISODate,
  updated_at: ISODate
}
```

#### `lessons`
```javascript
{
  _id: ObjectId,
  course_id: String,
  title: String,
  description: String,
  video_url: String,
  video_type: String,
  order: Number,
  materials: Array [{name, url}],
  created_at: ISODate
}
```

#### `quizzes`
```javascript
{
  _id: ObjectId,
  course_id: String,
  title: String,
  questions: Array [{
    question: String,
    options: Array[String],
    correct_answer: Number (index)
  }],
  translations: Object {lang_code: {title, questions}},
  created_at: ISODate
}
```

#### `quiz_attempts`
```javascript
{
  _id: ObjectId,
  quiz_id: String,
  course_id: String,
  user_id: String,
  answers: Array[Number],
  score: Number,
  passed: Boolean,
  created_at: ISODate
}
```

#### `enrollments`
```javascript
{
  _id: ObjectId,
  course_id: String,
  user_id: String,
  enrolled_by: String (for bulk enrollment),
  completed: Boolean,
  score: Number,
  completed_at: ISODate,
  created_at: ISODate
}
```

#### `certificates`
```javascript
{
  _id: ObjectId,
  certificate_id: String (8-char unique),
  course_id: String,
  user_id: String,
  user_name: String,
  course_title: String,
  score: Number,
  template: String,
  primary_color: String,
  secondary_color: String,
  issued_at: ISODate
}
```

#### `forum_posts`
```javascript
{
  _id: ObjectId,
  course_id: String,
  content: String,
  parent_id: String (for replies),
  user_id: String,
  user_name: String,
  created_at: ISODate
}
```

#### `chat_messages`
```javascript
{
  _id: ObjectId,
  course_id: String,
  user_id: String,
  role: String ["user", "assistant"],
  content: String,
  created_at: ISODate
}
```

#### `payment_transactions`
```javascript
{
  _id: ObjectId,
  session_id: String (Stripe),
  course_id: String,
  user_id: String,
  amount: Number,
  currency: String,
  payment_status: String ["pending", "paid"],
  created_at: ISODate,
  updated_at: ISODate
}
```

---

## 🔧 API Endpoints

### Authentication
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth/register` | Register new user |
| POST | `/api/auth/login` | Login and get JWT |
| POST | `/api/auth/logout` | Clear auth cookies |
| GET | `/api/auth/me` | Get current user |

### Courses
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/courses` | List courses (with ?language=, ?search=) |
| POST | `/api/courses` | Create course (admin) |
| GET | `/api/courses/{id}` | Get course details |
| PUT | `/api/courses/{id}` | Update course (admin) |
| DELETE | `/api/courses/{id}` | Delete course (admin) |
| GET | `/api/languages` | Get supported languages |

### Lessons
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/lessons` | Create lesson (admin) |
| GET | `/api/lessons/{id}` | Get lesson details |
| PUT | `/api/lessons/{id}` | Update lesson (admin) |
| DELETE | `/api/lessons/{id}` | Delete lesson (admin) |

### Quizzes
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/quizzes` | Create quiz (admin) |
| GET | `/api/quizzes/{id}` | Get quiz (hides answers for students) |
| POST | `/api/quizzes/{id}/submit` | Submit quiz answers |

### Enrollments
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/enrollments` | Enroll in course (self or bulk by admin) |
| GET | `/api/enrollments/my` | Get my enrollments |
| GET | `/api/enrollments/course/{id}` | Get course enrollments (admin/manager) |

### Group Progress Tracking (Client Manager)
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/groups/overview` | Overview of all courses with progress stats |
| GET | `/api/groups/course/{id}/progress` | Detailed student progress for a course |
| GET | `/api/groups/student/{id}/progress` | Individual student progress across courses |

### Certificates
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/certificates/my` | Get my certificates |
| GET | `/api/certificates/{id}` | Get certificate details |
| PUT | `/api/certificates/{id}/customize` | Customize certificate (admin) |

### AI Translation (Deepseek)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/translate/text` | Translate single text |
| POST | `/api/translate/course/{id}` | Translate course to languages |
| POST | `/api/translate/quiz/{id}` | Translate quiz questions |
| POST | `/api/courses/{id}/create-translation` | Create translated course copy |

### AI Chatbot (Deepseek)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/chat` | Send message to AI |
| GET | `/api/chat/{course_id}/history` | Get chat history |

### Forums
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/forums/{course_id}` | Get forum posts |
| POST | `/api/forums/posts` | Create post/reply |
| DELETE | `/api/forums/posts/{id}` | Delete post |

### Payments (Stripe)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/payments/checkout` | Create checkout session |
| GET | `/api/payments/status/{session_id}` | Check payment status |
| POST | `/api/webhook/stripe` | Stripe webhook handler |

### Users & Stats
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/users` | List users (admin/manager) |
| PUT | `/api/users/{id}/role` | Change user role (admin) |
| GET | `/api/stats/admin` | Admin dashboard stats |
| GET | `/api/stats/student` | Student dashboard stats |

---

## ✨ Features

### 1. Course Management
- Create courses with YouTube/Vimeo video embedding
- Organize content into lessons with ordering
- Upload downloadable materials (PDFs, resources)
- Set pricing (free or paid via Stripe)
- Mark courses as private (invitation only)

### 2. Multi-Language Support
- **5 Course Languages**: English, Traditional Chinese (繁體中文), Simplified Chinese (简体中文), Japanese (日本語), Korean (한국어)
- **UI Languages**: English ↔ Traditional Chinese toggle
- **Language Filter**: Filter courses by language on browse page
- **Language Badges**: Visual indicators on course cards

### 3. AI Auto-Translation (Deepseek)
- One-click course translation to any supported language
- Translates: course title, description, all lessons
- Creates new course copy with translated content
- Separate quiz translation endpoint
- Real-time text translation API

### 4. Quiz System
- Multiple choice questions
- Configurable passing score (default 70%)
- Automatic scoring and feedback
- Progress tracking
- Certificate eligibility on pass

### 5. Certificate Generation
- Auto-generated on course completion
- Customizable colors and templates
- Unique certificate ID
- Student name and score
- Issue date tracking

### 6. AI Chatbot (Deepseek)
- Course-specific AI assistant
- Context-aware responses
- Chat history persistence
- Available on course detail page

### 7. Community Forums
- Course-specific discussions
- Threaded replies
- User attribution
- Admin moderation

### 8. Payment Processing (Stripe)
- Secure checkout sessions
- Automatic enrollment on payment
- Webhook-based confirmation
- Test mode support

### 9. User Roles & Permissions

| Role | Capabilities |
|------|--------------|
| **Admin** | Full access: Create/edit/delete courses & quizzes, Bulk enroll students, Manage users, View analytics, AI translate content, Configure certificates |
| **Client Manager** | View course enrollments, Monitor group training progress, View student completion rates & scores, Track individual student progress across courses |
| **Student** | Browse courses, Enroll (free or via payment), Take quizzes, Earn certificates, Use AI chat, Participate in forums |

---

## 📧 Email Notifications (Brevo)

### Configuration
```env
BREVO_API_KEY=your-brevo-api-key
EMAIL_FROM=noreply@learnhub.com
EMAIL_FROM_NAME=LearnHub
```

### Email Types
| Event | Recipient | Content |
|-------|-----------|---------|
| **Enrollment** | Student | Welcome email with course link |
| **Progress** | Student | Progress update with percentage |
| **Certificate** | Student | Congratulations with certificate details |

### Getting Brevo API Key
1. Sign up at [brevo.com](https://brevo.com)
2. Go to SMTP & API → API Keys
3. Create new API key
4. Add to backend .env file

---

## 🔐 Authentication Flow

```
1. User submits login credentials
         │
         ▼
2. Backend validates against MongoDB
         │
         ▼
3. JWT tokens generated (access + refresh)
         │
         ▼
4. Tokens set as HTTP-only cookies
         │
         ▼
5. Frontend includes cookies in API requests
         │
         ▼
6. Backend validates JWT on protected routes
```

**Token Configuration:**
- Access Token: 60 minutes expiry
- Refresh Token: 7 days expiry
- Algorithm: HS256
- Storage: HTTP-only cookies

---

## 🌐 Internationalization (i18n)

### Supported UI Languages
- **English (en)**: Full support
- **Traditional Chinese (zh-TW)**: Full support

### Translation Keys Structure
```javascript
translations = {
  en: {
    nav: { home, courses, dashboard, login, ... },
    landing: { headline, subheadline, features, ... },
    auth: { email, password, signIn, ... },
    dashboard: { welcomeBack, enrolledCourses, ... },
    courses: { allCourses, createCourse, ... },
    quiz: { submit, congratulations, ... },
    certificate: { myCertificates, download, ... },
    ...
  },
  "zh-TW": {
    nav: { home: "首頁", courses: "課程", ... },
    ...
  }
}
```

### Language Switching
- Toggle in header navigation
- Persisted to localStorage
- Applies immediately without reload

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+
- Python 3.11+
- MongoDB 6+
- Deepseek API key
- Stripe API key (test mode)

### Environment Variables

**Backend (.env)**
```
MONGO_URL=mongodb://localhost:27017
DB_NAME=learnhub
JWT_SECRET=your-secret-key
ADMIN_EMAIL=admin@learnhub.com
ADMIN_PASSWORD=admin123
DEEPSEEK_API_KEY=sk-xxx
STRIPE_API_KEY=sk_test_xxx
FRONTEND_URL=http://localhost:3000
```

**Frontend (.env)**
```
REACT_APP_BACKEND_URL=http://localhost:8001
```

### Installation

```bash
# Backend
cd backend
pip install -r requirements.txt
python server.py

# Frontend
cd frontend
yarn install
yarn start
```

---

## 🧪 Test Credentials

| Role | Email | Password |
|------|-------|----------|
| Admin | admin@learnhub.com | admin123 |
| Student | student@test.com | test123 |

---

## 📊 Business Logic

### Course Enrollment Flow
```
1. Student browses courses
         │
         ▼
2. Selects course → Check if free or paid
         │
    ┌────┴────┐
    ▼         ▼
  FREE      PAID
    │         │
    │         ▼
    │    Stripe Checkout
    │         │
    │         ▼
    │    Payment Success
    │         │
    └────┬────┘
         ▼
3. Create enrollment record
         │
         ▼
4. Student accesses course content
```

### Quiz & Certificate Flow
```
1. Student completes watching lessons
         │
         ▼
2. Takes quiz → Submits answers
         │
         ▼
3. Backend calculates score
         │
    ┌────┴────┐
    ▼         ▼
  PASS      FAIL
  (≥70%)   (<70%)
    │         │
    ▼         │
4. Mark      │
enrollment   │
completed    │
    │         │
    ▼         │
5. Generate  │
certificate  │
    │         │
    └────┬────┘
         ▼
6. Show result to student
```

### AI Translation Flow
```
1. Admin clicks translate on course
         │
         ▼
2. Selects target language
         │
         ▼
3. Backend calls Deepseek API
         │
    ┌────┴────┐
    ▼         ▼
  Title    Description
    │         │
    ▼         ▼
4. Translate lessons (loop)
         │
         ▼
5. Create new course with translations
         │
         ▼
6. Return new course to admin
```

---

## 🔒 Security Features

- **Password Hashing**: Bcrypt with salt
- **JWT Authentication**: HTTP-only cookies
- **Role-based Access Control**: Endpoint-level protection
- **CORS Configuration**: Restricted origins
- **Input Validation**: Pydantic models
- **SQL Injection Prevention**: MongoDB parameterized queries

---

## 📈 Future Enhancements

- [ ] Email notifications (SendGrid)
- [ ] Certificate PDF download
- [ ] Lesson progress tracking
- [ ] Video watch time analytics
- [ ] Course ratings & reviews
- [ ] Instructor profiles
- [ ] Mobile app (React Native)
- [ ] Full UI translation (zh-CN, ja, ko)

---

## 📄 License

MIT License - See LICENSE file for details.

---

## 🤝 Support

For issues and feature requests, please create an issue in the repository.
