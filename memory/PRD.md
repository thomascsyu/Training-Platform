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
- **UI Internationalization**: English & Traditional Chinese interface

## Architecture
- **Backend**: FastAPI + MongoDB + JWT Authentication
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Integrations**: Stripe (payments), Deepseek AI (chatbot)
- **Design**: Swiss & High-Contrast style (International Klein Blue #002FA7)
- **i18n**: Custom translation system with English/Traditional Chinese UI

## User Personas
1. **Admin/Instructor**: Creates courses in multiple languages, quizzes, manages users
2. **Client Manager**: Bulk enrolls groups of students to courses
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
- [x] Client manager bulk enrollment

## What's Been Implemented (Jan 2026)

### Backend APIs
- `/api/auth/*` - Authentication (register, login, logout, me)
- `/api/languages` - Get supported languages
- `/api/courses/*` - Course CRUD with language field & filtering
- `/api/lessons/*` - Lesson CRUD
- `/api/quizzes/*` - Quiz CRUD and submission
- `/api/enrollments/*` - Course enrollment
- `/api/certificates/*` - Certificate management
- `/api/forums/*` - Forum posts
- `/api/chat` - AI chatbot (Deepseek)
- `/api/translate/text` - Translate single text with AI
- `/api/translate/course/{id}` - Translate course to multiple languages
- `/api/translate/quiz/{id}` - Translate quiz questions
- `/api/courses/{id}/create-translation` - Create translated course copy
- `/api/payments/*` - Stripe checkout
- `/api/users/*` - User management
- `/api/stats/*` - Dashboard statistics

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
- Client manager group enrollment

### Supported Languages
| Code | Name | UI Support |
|------|------|------------|
| en | English | ✅ Full |
| zh-TW | 繁體中文 | ✅ Full |
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
- [ ] Email notifications (SendGrid/Resend integration)

### P2 (Medium Priority)
- [ ] Course progress tracking per lesson
- [ ] Video watch time tracking
- [ ] Certificate PDF download
- [ ] Course analytics dashboard
- [ ] Student performance reports
- [ ] Full UI translation for zh-CN, ja, ko

### P3 (Low Priority)
- [ ] Course categories/tags
- [ ] Course reviews/ratings
- [ ] Instructor profiles
- [ ] Mobile app

## Next Tasks
1. Add email notifications for enrollment and course completion
2. Implement lesson-level progress tracking
3. Add PDF certificate download
4. Create course analytics dashboard
5. Add full UI translations for Simplified Chinese, Japanese, Korean
