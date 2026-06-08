# LearnHub - Course Platform PRD

## Original Problem Statement
Build a Kajabi-like course/content platform with:
- Course Builder with video uploads (Vimeo/YouTube embed)
- Quiz System with scoring & pass/fail criteria
- Customizable Certificate generation on completion
- User Roles: Admin/Instructor, Client Manager, Students
- Stripe payment for paid courses
- Email notifications (enrollment, progress)
- AI Chatbot for student Q&A (Deepseek)
- Community Forums
- Private/free courses with group member registration
- Downloadable course materials
- **Multi-language support**: Course versions in English, Traditional Chinese, Simplified Chinese, Japanese, Korean
- **UI Internationalization**: English & Traditional Chinese interface (partial — nav/dashboard/auth; course admin pages still mixed)

## Architecture
- **Backend**: FastAPI + MongoDB + JWT Authentication
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Integrations**: Stripe (payments), Deepseek AI (chatbot)
- **Design**: Swiss & High-Contrast style (International Klein Blue #002FA7)
- **i18n**: Custom translation system with English/Traditional Chinese UI

## User Personas
1. **Admin/Instructor**: Creates courses in multiple languages, quizzes, manages users
2. **Client Manager**: Monitors group training progress; assigned by admin (not self-registration)
3. **Student**: Learns courses in preferred language, takes quizzes, earns certificates

## Core Requirements
- [x] User authentication with role-based access (admin, client_manager, student)
- [x] Course CRUD operations with video embedding (YouTube/Vimeo)
- [x] **Multi-language course support** (5 languages: EN, zh-TW, zh-CN, JA, KO)
- [x] **Course language filtering and search**
- [x] **UI language switching** (English ↔ Traditional Chinese)
- [x] **AI Auto-Translation** using Deepseek AI
- [x] Lesson management within courses
- [x] Quiz builder with multiple choice questions
- [x] Quiz scoring with configurable passing score
- [x] Certificate generation upon course completion
- [x] Stripe payment for paid courses
- [x] AI chatbot for student Q&A (Deepseek)
- [x] Community forums per course
- [x] Downloadable course materials
- [x] Private courses with group enrollment
- [x] Admin bulk enrollment (client managers view progress; admins enroll groups)

## What's Been Implemented (Jan 2026, updated Jun 2026)

### Backend layout
- `server.py` — Uvicorn entry
- `app.py` — App factory, CORS, lifespan
- `routes.py` — Aggregates domain routers under `/api`
- `routers/` — `auth`, `courses`, `lessons`, `quizzes`, `enrollments`, `groups`, `certificates`, `forums`, `chat`, `translate`, `payments`, `users`, `stats`, `root`
- `clients.py` — Shared Deepseek + Stripe clients
- `course_utils.py` — Cascade delete helpers

### Backend APIs
- `/api/auth/*` - Authentication (register, login, logout, refresh, me)
- `/api/languages` - Get supported languages
- `/api/courses/*` - Course CRUD with language field & filtering
- `/api/lessons/*` - Lesson CRUD
- `/api/quizzes/*` - Quiz CRUD and submission
- `/api/enrollments/*` - Course enrollment (Admin bulk enroll)
- `/api/groups/overview` - Course progress overview (Admin/Client Manager)
- `/api/groups/course/{id}/progress` - Detailed student progress per course
- `/api/groups/student/{id}/progress` - Individual student progress
- `/api/certificates/*` - Certificate management
- `/api/forums/*` - Forum posts
- `/api/chat` - AI chatbot (Deepseek)
- `/api/translate/*` - AI translation endpoints
- `/api/courses/{id}/create-translation` - Create translated course copy
- `/api/payments/*` - Stripe checkout
- `/api/users/*` - User management
- `/api/progress/*` - Lesson-level progress (complete, watch tracking, course summary)
- `/api/stats/*` - Dashboard statistics + admin analytics

### Frontend Pages
- Landing page with hero and features (bilingual)
- Language switcher component
- Login/Register pages
- Student dashboard with enrolled courses
- Admin dashboard with stats
- Course management with language field (admin)
- User management (admin)
- Course listing with language filter and search
- Course detail page with tabs
- Quiz taking interface
- Certificates page
- Payment success page
- Admin analytics dashboard (`/admin/analytics`)
- Lesson viewer with per-lesson progress tracking
- Certificate PDF download

### Supported Languages
| Code | Name | UI Support |
|------|------|------------|
| en | English | ✅ Primary UI |
| zh-TW | 繁體中文 | ✅ Partial UI (nav, auth, dashboards) |
| zh-CN | 简体中文 | Course only |
| ja | 日本語 | Course only |
| ko | 한국어 | Course only |

## Prioritized Backlog

### P0 (Critical) - COMPLETED
- [x] Core authentication
- [x] Course creation and viewing
- [x] Quiz system
- [x] Certificate generation
- [x] Multi-language course support
- [x] UI internationalization

### P1 (High Priority)
- [x] AI Chatbot integration
- [x] Stripe payments
- [x] Forum functionality
- [x] Email notifications (Brevo: enrollment, quiz progress, certificate)

### P2 (Medium Priority)
- [x] Course progress tracking per lesson
- [x] Video watch time tracking (watch_percent + last_position_sec)
- [x] Certificate PDF download
- [x] Course analytics dashboard
- [x] Student performance reports (lesson progress in group views)
- [ ] Full UI translation for zh-CN, ja, ko

### P3 (Low Priority)
- [ ] Course categories/tags
- [ ] Course reviews/ratings
- [ ] Instructor profiles
- [ ] Mobile app

## Next Tasks
1. Add full UI translations for Simplified Chinese, Japanese, Korean
2. Split `App.js` into page components under `src/pages/`
3. P3 features: categories/tags, reviews, instructor profiles
