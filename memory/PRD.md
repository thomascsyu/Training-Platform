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

## Architecture
- **Backend**: FastAPI + MongoDB + JWT Authentication
- **Frontend**: React + Tailwind CSS + Shadcn UI
- **Integrations**: Stripe (payments), Deepseek AI (chatbot)
- **Design**: Swiss & High-Contrast style (International Klein Blue #002FA7)

## User Personas
1. **Admin/Instructor**: Creates courses, quizzes, manages users
2. **Client Manager**: Bulk enrolls groups of students to courses
3. **Student**: Learns courses, takes quizzes, earns certificates

## Core Requirements
- [x] User authentication with role-based access (admin, client_manager, student)
- [x] Course CRUD operations with video embedding (YouTube/Vimeo)
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
- `/api/courses/*` - Course CRUD
- `/api/lessons/*` - Lesson CRUD
- `/api/quizzes/*` - Quiz CRUD and submission
- `/api/enrollments/*` - Course enrollment
- `/api/certificates/*` - Certificate management
- `/api/forums/*` - Forum posts
- `/api/chat` - AI chatbot (Deepseek)
- `/api/payments/*` - Stripe checkout
- `/api/users/*` - User management
- `/api/stats/*` - Dashboard statistics

### Frontend Pages
- Landing page with hero and features
- Login/Register pages
- Student dashboard with enrolled courses
- Admin dashboard with stats
- Course management (admin)
- User management (admin)
- Course detail page with tabs (Overview, Lessons, Quizzes, Materials, AI Chat, Forum)
- Quiz taking interface
- Certificates page
- Payment success page
- Client manager group enrollment

## Prioritized Backlog

### P0 (Critical)
- [x] Core authentication
- [x] Course creation and viewing
- [x] Quiz system
- [x] Certificate generation

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

### P3 (Low Priority)
- [ ] Course categories/tags
- [ ] Search functionality
- [ ] Course reviews/ratings
- [ ] Instructor profiles
- [ ] Mobile app

## Next Tasks
1. Add email notifications for enrollment and course completion
2. Implement lesson-level progress tracking
3. Add PDF certificate download
4. Create course analytics dashboard
