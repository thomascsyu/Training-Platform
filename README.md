# LearnHub — Kajabi-like Course Platform

Online learning platform built with **React**, **FastAPI**, and **MongoDB**. Supports multi-language courses, AI translation & chat (Deepseek), quizzes, certificates, Stripe payments, forums, and Brevo email notifications.

**Quick links:** [Quick Start](#-quick-start) · [Architecture](#-architecture) · [API](#-api-endpoints) · [Environment](#environment-variables) · [Test Accounts](memory/test_credentials.md) · [License](LICENSE)

---

## Quick Start

```bash
# Clone and enter the repo (folder name may differ)
git clone <repo-url> && cd learnhub

# Backend
cd backend
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # edit MONGO_URL, JWT_SECRET, etc.
uvicorn server:app --host 0.0.0.0 --port 8001 --reload

# Frontend (new terminal)
cd frontend
yarn install
cp .env.example .env   # set REACT_APP_BACKEND_URL=http://localhost:8001
yarn start
```

Open [http://localhost:3000](http://localhost:3000). Default admin is seeded from `ADMIN_EMAIL` / `ADMIN_PASSWORD` in backend `.env` — see [Test Accounts](memory/test_credentials.md).

**Docker (all services):** `cp .env.docker.example .env && docker compose up --build` — see [Docker](#docker).

---

## Overview

LearnHub is a full-featured LMS for creating, managing, and delivering courses. Organizations can run paid or free programs, track group progress, and issue certificates on quiz completion.

| Capability | Summary |
|------------|---------|
| Courses & lessons | YouTube/Vimeo embeds, materials, private courses |
| Assessments | Multiple-choice quizzes, configurable pass threshold |
| Credentials | Auto-generated certificates on pass |
| Commerce | Stripe checkout + webhooks |
| AI | Deepseek chatbot + course/quiz translation |
| Comms | Brevo emails (enrollment, quiz progress, certificate) |
| Roles | Admin, client manager (admin-assigned), student |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         CLIENT (React SPA)                        │
│  Landing · Auth · Dashboards · Course player · Quiz · Certs      │
│  i18n: EN + 繁中 (partial — see Internationalization)            │
└───────────────────────────────┬─────────────────────────────────┘
                                │ HTTPS + cookies (JWT)
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                      API (FastAPI + Motor)                        │
│  Auth · Courses · Quizzes · Enrollments · Payments · Groups      │
│  Forums · Chat · Translate · Certificates · Stats              │
└───────────────────────────────┬─────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
   MongoDB                 Deepseek AI              Stripe
   (primary DB)            (chat / translate)      (payments)
                                │
                                ▼
                           Brevo (transactional email)
```

### Backend layout

| File | Role |
|------|------|
| `server.py` | Uvicorn entry point |
| `app.py` | App factory, CORS, lifespan, indexes, admin seed |
| `routes.py` | Aggregates routers under `/api` |
| `routers/` | Domain route modules (`auth`, `courses`, `lessons`, `quizzes`, `enrollments`, `groups`, `certificates`, `forums`, `chat`, `translate`, `payments`, `users`, `stats`, `root`) |
| `clients.py` | Shared Deepseek + Stripe client init |
| `course_utils.py` | Course cascade-delete helpers |
| `config.py` | Environment configuration |
| `database.py` | MongoDB client |
| `models.py` | Pydantic request models |
| `auth_utils.py` | JWT, passwords, cookies, RBAC helpers |
| `email_service.py` | Brevo integration |

### Frontend layout

| Path | Role |
|------|------|
| `src/App.js` | Routes and page components (uses `lib/api.js` for auth + token refresh) |
| `src/lib/api.js` | Axios client (`withCredentials: true`) |
| `src/contexts/` | Auth and language providers |
| `src/components/` | Shared UI (guards, language switcher) |
| `src/i18n.js` | EN / 繁中 translation strings |
| `src/components/ui/` | Shadcn UI primitives |

See [frontend/README.md](frontend/README.md) for frontend-specific setup.

---

## Tech Stack

| Layer | Technology | Notes |
|-------|------------|-------|
| Frontend | React 19, React Router 7 | CRA + CRACO; optional `@emergentbase/visual-edits` (proprietary tarball in `package.json`) |
| Styling | Tailwind CSS 3, Shadcn UI | International Klein Blue `#002FA7` |
| HTTP | Axios | Cookie-based auth |
| Backend | Python 3.11+, FastAPI | Async via Motor |
| Database | MongoDB 6+ | Document store |
| Auth | PyJWT, bcrypt | HTTP-only cookies |
| Payments | Stripe | Checkout sessions + webhooks |
| AI | OpenAI SDK → Deepseek | Chat + translation |
| Email | Brevo (httpx) | Optional; skipped if no API key |

---

## User Roles

| Role | Capabilities |
|------|--------------|
| **Admin** | Courses, quizzes, users/roles, bulk enroll, analytics, AI translate, certificate styling |
| **Client manager** | Enrollments, group progress dashboards (assigned by admin only) |
| **Student** | Browse, enroll (free/paid), quiz, certificates, AI chat, forums |

> Public registration always creates **student** accounts. Bulk enrollment is **admin-only**. Promote users via `PUT /api/users/{id}/role?role=client_manager`.

---

## API Endpoints

Base path: `/api`

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/auth/register` | Register (always `student`) |
| POST | `/auth/login` | Login; sets access + refresh cookies |
| POST | `/auth/logout` | Clear cookies |
| POST | `/auth/refresh` | Renew access token from refresh cookie |
| GET | `/auth/me` | Current user |

### Courses & content

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/languages` | Public |
| GET/POST | `/courses` | List public; create = admin |
| GET/PUT/DELETE | `/courses/{id}` | Get public/private rules; mutate = admin |
| POST | `/courses/{id}/create-translation` | Admin |
| CRUD | `/lessons`, `/lessons/{id}` | Admin write |
| CRUD | `/quizzes`, `/quizzes/{id}` | Admin write; students get quiz without answers |
| POST | `/quizzes/{id}/submit` | Enrolled student |

### Enrollments & groups

| Method | Endpoint | Access |
|--------|----------|--------|
| POST | `/enrollments` | Self-enroll or admin bulk (`user_ids`) |
| GET | `/enrollments/my` | Authenticated |
| GET | `/enrollments/course/{id}` | Admin, client manager |
| GET | `/groups/overview` | Admin, client manager |
| GET | `/groups/course/{id}/progress` | Admin, client manager |
| GET | `/groups/student/{id}/progress` | Admin, client manager |

### Certificates

| Method | Endpoint | Access |
|--------|----------|--------|
| GET | `/certificates/my` | Owner |
| GET | `/certificates/{id}` | Owner, admin, or client manager |
| GET | `/certificates/{id}/pdf` | Owner, admin, or client manager — PDF download |
| PUT | `/certificates/{id}/customize` | Admin |

**Customize request body:**

```json
{
  "template": "default",
  "primary_color": "#002FA7",
  "secondary_color": "#0A0B10",
  "apply_to_course": false
}
```

Set `apply_to_course: true` to apply styling to all certificates for that certificate's course.

### AI, forums, payments, admin

| Area | Endpoints |
|------|-----------|
| Translation | `POST /translate/text`, `/translate/course/{id}`, `/translate/quiz/{id}` |
| Chat | `POST /chat`, `GET /chat/{course_id}/history` |
| Forums | `GET /forums/{course_id}`, `POST /forums/posts`, `DELETE /forums/posts/{id}` |
| Payments | `POST /payments/checkout`, `GET /payments/status/{session_id}`, `POST /webhook/stripe` |
| Users | `GET /users`, `PUT /users/{id}/role` |
| Stats | `GET /stats/admin`, `GET /stats/admin/analytics`, `GET /stats/student` |
| Progress | `GET /progress/course/{id}`, `PATCH /progress/lessons/{id}`, `POST /progress/lessons/{id}/complete` |

---

## Authentication

```
Login/Register
      │
      ▼
Access + refresh JWT → HTTP-only cookies (secure flag via COOKIE_SECURE)
      │
      ▼
API requests include cookies automatically (axios withCredentials)
      │
      ├── Valid access token → 200
      │
      └── Expired access token → 401
                │
                ▼
          POST /auth/refresh (refresh cookie)
                │
                ├── Success → new cookies → retry request
                └── Failure → redirect to login
```

| Token | Lifetime | Notes |
|-------|----------|-------|
| Access | 60 min | HS256 |
| Refresh | 7 days | Used only by `/auth/refresh` |

> **Note:** The SPA automatically calls `/auth/refresh` on 401 (via Axios interceptor) and clears session state if refresh fails.

---

## Email (Brevo)

Optional. If `BREVO_API_KEY` is unset, emails are skipped (logged only).

| Event | Trigger |
|-------|---------|
| Enrollment | Self-enroll, bulk enroll, or paid checkout |
| Progress | Failed quiz attempt (score sent as %) |
| Certificate | First successful quiz pass |

```env
BREVO_API_KEY=xkeysib-...
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=LearnHub
FRONTEND_URL=https://yourdomain.com
```

---

## Internationalization

| Scope | English | 繁體中文 | 简体中文 | 日本語 | 한국어 |
|-------|---------|----------|----------|--------|--------|
| Landing & auth | ✅ | ✅ | ✅ | ✅ | ✅ |
| Navigation & dashboards | ✅ | ✅ | ✅ | ✅ | ✅ |
| Course / quiz / admin UI | ✅ | ✅ | ✅ | ✅ | ✅ |

Course content supports **5 languages**: `en`, `zh-TW`, `zh-CN`, `ja`, `ko`. UI toggle persists in `localStorage`.

---

## Database Collections

`users` · `courses` · `lessons` · `quizzes` · `quiz_attempts` · `enrollments` · `certificates` · `forum_posts` · `chat_messages` · `payment_transactions`

<details>
<summary>Schema reference (expand)</summary>

#### `users`
```javascript
{ email, password_hash, name, role: "admin"|"client_manager"|"student", created_at }
```

#### `courses`
```javascript
{
  title, description, thumbnail_url, video_url, video_type: "youtube"|"vimeo",
  price, is_free, is_private, passing_score, materials: [{name, url}],
  language, category, translations, source_course_id, created_by, created_at, updated_at
}
```

#### `enrollments`
```javascript
{ course_id, user_id, enrolled_by?, completed, score, completed_at?, created_at }
```

#### `certificates`
```javascript
{
  certificate_id, course_id, user_id, user_name, course_title, score,
  template, primary_color, secondary_color, issued_at
}
```

</details>

---

## Environment Variables

Copy templates: `backend/.env.example`, `frontend/.env.example`, or for Docker Compose: `.env.docker.example` → `.env` at repo root.

### Backend

```bash
MONGO_URL=mongodb://localhost:27017
DB_NAME=learnhub
JWT_SECRET=                         # python -c "import secrets; print(secrets.token_hex(32))"

ENVIRONMENT=development             # production enables stricter defaults
COOKIE_SECURE=false                 # true in production (HTTPS)
CORS_ORIGINS=http://localhost:3000  # comma-separated; never * with credentials

ADMIN_EMAIL=admin@learnhub.com
ADMIN_PASSWORD=change-me

STRIPE_API_KEY=
STRIPE_WEBHOOK_SECRET=
REQUIRE_STRIPE_WEBHOOK_SECRET=false # true in production

DEEPSEEK_API_KEY=
BREVO_API_KEY=
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=LearnHub
FRONTEND_URL=http://localhost:3000
```

### Frontend

```bash
REACT_APP_BACKEND_URL=http://localhost:8001
```

---

## Deployment

### Prerequisites

Node.js 18+, Python 3.11+, MongoDB 6+, and accounts for Stripe, Deepseek, and (optionally) Brevo.

### Docker

**Full stack (MongoDB + API + web):**

```bash
cp .env.docker.example .env   # edit JWT_SECRET, ADMIN_PASSWORD
docker compose up --build
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8001 |
| MongoDB | localhost:27017 |

**Individual images:**

```bash
# API only (requires external MongoDB)
cd backend && docker build -t learnhub-api .
docker run -p 8001:8001 --env-file .env learnhub-api

# Web only
cd frontend
docker build -t learnhub-web --build-arg REACT_APP_BACKEND_URL=http://localhost:8001 .
docker run -p 3000:3000 learnhub-web
```

### Stripe webhook

1. Dashboard → Webhooks → `https://yourdomain.com/api/webhook/stripe`
2. Event: `checkout.session.completed`
3. Set `STRIPE_WEBHOOK_SECRET`; use `REQUIRE_STRIPE_WEBHOOK_SECRET=true` in production

### Production checklist

- [ ] Strong `JWT_SECRET` and `ADMIN_PASSWORD`
- [ ] `ENVIRONMENT=production`, `COOKIE_SECURE=true`
- [ ] `CORS_ORIGINS` set to frontend origin(s)
- [ ] Stripe live keys + webhook secret enforced
- [ ] Brevo configured; `FRONTEND_URL` correct
- [ ] HTTPS everywhere
- [ ] MongoDB authentication enabled (optional via `MONGO_ROOT_USER` / `MONGO_ROOT_PASSWORD` in Docker)

---

## Business Flows

### Enrollment

Browse → free enroll **or** Stripe checkout → webhook/status confirms payment → enrollment record → optional Brevo welcome email.

Students track **lesson progress** per course (mark complete, watch percent). Group dashboards show lesson completion alongside quiz status.

### Quiz & certificate

Take quiz → score computed vs `passing_score` → **pass:** mark enrollment complete, issue certificate (once), send cert email → **fail:** send progress email with score %. Certificates can be downloaded as PDF from `/certificates/{id}/pdf`.

### AI translation

Admin selects target language → Deepseek translates title, description, lessons → new course copy linked via `source_course_id`.

---

## Security

- Bcrypt password hashing
- JWT in HTTP-only cookies; `secure` flag from env
- RBAC on endpoints; roles assigned by admin only
- CORS restricted via `CORS_ORIGINS`
- Pydantic input validation
- MongoDB queries avoid passing raw user input into operators
- Stripe webhook signature verification (required in production)

---

## Testing

**Unit tests (no running server):**

```bash
pip install -r backend/requirements.txt pytest
python -m pytest tests/ -q
```

`tests/conftest.py` sets minimal env vars (`MONGO_URL`, `DB_NAME`, `JWT_SECRET`) before importing backend modules.

**Integration tests:** `backend_test.py`, `comprehensive_backend_test.py` (require running API + MongoDB).

Test accounts and role promotion steps: **[memory/test_credentials.md](memory/test_credentials.md)**

---

## Future Enhancements

- [x] Full UI translation (5 languages: EN, zh-TW, zh-CN, ja, ko)
- [x] Split `App.js` into `src/pages/` components
- [ ] Course categories/tags, ratings, instructor profiles
- [ ] Mobile app (React Native)

---

## License

MIT — see [LICENSE](LICENSE).

## Support

Open an issue in the repository for bugs and feature requests.
