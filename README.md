# LearnHub — Kajabi-like Course Platform

Online learning platform built with **React**, **FastAPI**, and **MongoDB**. Supports multi-language courses, AI translation & chat (Deepseek), quizzes, certificates, Stripe payments, forums, and Brevo email notifications.

**Quick links:** [Quick Start](#-quick-start) · [Zeabur deployment](#zeabur-deployment) · [Architecture](#-architecture) · [API](#-api-endpoints) · [Environment](#environment-variables) · [Test Accounts](memory/test_credentials.md) · [License](LICENSE)

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

Open [http://localhost:3000](http://localhost:3000). The admin account is seeded from `ADMIN_EMAIL` / `ADMIN_PASSWORD` in backend `.env` only when `ADMIN_PASSWORD` is set — see [Test Accounts](memory/test_credentials.md).

**Docker (all services):** `cp .env.docker.example .env && docker compose up --build` — see [Docker](#docker).

---


## Zeabur deployment

This repository is a monorepo with separate Dockerfiles for the API and web app. Zeabur does not deploy from `docker-compose.yml`, so create **three** Zeabur services from the same Git repository:

| Service | Role | Example domain |
|---------|------|----------------|
| `mongodb` | Database (Zeabur prebuilt MongoDB) | internal only |
| **one API service** (see below) | FastAPI backend | `https://<api>.zeabur.app` |
| `frontend` | React SPA | `https://<web>.zeabur.app` |

`frontend` and the API service are **not duplicates** — the browser loads the SPA from `frontend`, and the SPA calls the API over HTTPS with cookies. You need both.

### Pick one API service name

Several Dockerfile names exist for the same Python API. **Create only one API service** — do not deploy both `backend` and `training-platform` in the same project.

| Zeabur service name | Dockerfile used | When to use |
|---------------------|-----------------|-------------|
| `training-platform` | `Dockerfile.training-platform` | **Recommended** when the Zeabur project/repo is named after this repo (`Training-Platform`). |
| `backend` | `Dockerfile.backend` | Alternative API name; same app as `training-platform` with a slightly different start command. |
| `training-platform-beling` | `Dockerfile.training-platform-beling` | Same API image; use when the Zeabur service name includes a suffix (e.g. domain/project slug). Without this match, Zeabur auto-detects the monorepo as Node.js and the container exits immediately with no Python logs. |
| `frontend` | `Dockerfile.frontend` | Always required for the web UI. |
| `learnhub-frontend` / `learnhub-frontend-*` | `Dockerfile.learnhub-frontend` (symlink) | Same image as `frontend`; use when your Zeabur service name is not exactly `frontend`. |

**How Zeabur picks a Dockerfile:** the deciding factor is the exact **service name** you set in the Zeabur dashboard, not the `zbpack.<service>.json` files. Zeabur automatically builds `Dockerfile.<service-name>` (or `<service-name>.Dockerfile`) for whatever the service is named. The `zbpack.*.json` files in this repo are kept as a defensive fallback but are not required for this to work — get the service name right and the matching Dockerfile is picked up with zero extra config.

If your service name doesn't match any of the names above, either rename the service to one of them, set the service's **Root Directory** to `frontend` so it builds `frontend/Dockerfile`, or set **`ZBPACK_DOCKERFILE_PATH=Dockerfile.frontend`** on the Zeabur service. All containers listen on `${PORT:-8080}`, which matches Zeabur's routed port convention.

### Environment variables (production)

**MongoDB:** no manual connection string is usually needed. Link the prebuilt MongoDB service; Zeabur exposes `MONGO_CONNECTION_STRING` to other services automatically. The API reads the first of `MONGO_URL`, `MONGODB_URI`, `MONGO_CONNECTION_STRING`, or `MONGO_URI`. Do **not** set `MONGO_CONNECTION_STRING=${MONGO_CONNECTION_STRING}` on the API service — that self-reference blocks the injected value.

**API service** (`training-platform`, `backend`, or `training-platform-beling`):

```bash
ENVIRONMENT=production
COOKIE_SECURE=true
# Cookie SameSite. Leave unset: in secure production it defaults to 'none' so a
# cross-domain SPA can keep its auth cookie. Set 'lax' explicitly only when the
# SPA and API share a site (e.g. same-origin /api proxy). A cross-site SPA with
# SameSite=lax drops the auth cookie and the user loops back to the login page.
# COOKIE_SAMESITE=none
JWT_SECRET=<64-char hex>
DB_NAME=learnhub
ADMIN_EMAIL=<your admin email>
ADMIN_PASSWORD=<strong password>
# optional second admin (both required if used):
# ADMIN2_EMAIL=<second admin email>
# ADMIN2_PASSWORD=<strong password>
FRONTEND_URL=https://<your-frontend-domain>
CORS_ORIGINS=https://<your-frontend-domain>
LOG_LEVEL=info
# optional: STRIPE_*, BREVO_*, DEEPSEEK_*
# Stripe can also be configured later in Admin → Stripe Payments
# (database keys override these env vars).
UPLOADS_DIR=/app/uploads
```

Attach a **persistent volume** to the API service mounted at `/app/uploads`. Without it, uploaded course thumbnails are lost on redeploy/restart while MongoDB still keeps the old URLs (broken previews).

**Frontend service:**

```bash
# Use the API service's Zeabur private hostname (Networking → Private), port 8080.
BACKEND_PROXY_URL=http://training-platform.zeabur.internal:8080
# Do not set REACT_APP_BACKEND_URL unless you intentionally want cross-origin API calls.
```

Find the exact private hostname under the **API** service → Networking → Private (e.g. `training-platform.zeabur.internal` or `backend.zeabur.internal`). Do **not** paste a ClusterIP like `10.x.x.x` — those go stale when services are recreated.

If the frontend domain returns **HTTP 404**, Zeabur is not running the React container — the service name likely doesn't match any `Dockerfile.*` in the repo. Rename the service to `frontend` or `learnhub-frontend`, or set `ZBPACK_DOCKERFILE_PATH=Dockerfile.frontend`, then redeploy.

Use **`REACT_APP_BACKEND_URL`** only for legacy direct cross-origin API access (not recommended). Zeabur forwards service variables into the Docker build as `ARG`s; `Dockerfile.frontend` declares `ARG REACT_APP_BACKEND_URL` **without a default** so the dashboard value is baked into the CRA bundle at build time when set. Changing it later requires a **redeploy**, not just a restart.

### URL alignment checklist

These three values must use the same public origins:

| Variable | Service | Must match |
|----------|---------|------------|
| `BACKEND_PROXY_URL` | `frontend` | API private hostname (e.g. `http://training-platform.zeabur.internal:8080`) |
| `FRONTEND_URL` | API | Public frontend URL |
| `CORS_ORIGINS` | API | Same origin as `FRONTEND_URL` (not `*`) |

Bind the **frontend** domain to the `frontend` service. Bind the **API** domain to your single API service.

### Health checks and troubleshooting

- **Liveness:** use `/health` on the API (always `200`). Do not use `/ready` as the liveness probe — it returns `503` until MongoDB is connected.
- **Readiness:** `curl https://<api-domain>/ready` should return `200` once Mongo is wired.
- **Invalid Mongo connection string:** malformed values (`tcp://`, missing `mongodb://`, unescaped `@` in passwords) still allow `/health` to respond; `/ready` stays `503` until fixed. Percent-encode special characters in credentials (`urllib.parse.quote_plus`).
- **Frontend HTTP 404:** service name doesn't match a `Dockerfile.*` — set `ZBPACK_DOCKERFILE_PATH=Dockerfile.frontend` or rename to `frontend` / `learnhub-frontend`, then redeploy.
- **Frontend calls `localhost:8001`:** `REACT_APP_BACKEND_URL` was set at build time — unset it and redeploy so the app uses same-origin `/api`.
- **502 on API domain:** API service suspended or not deployed — resume/redeploy the API service, not a second copy.
- **"Invalid credentials" logging in with the example admin password:** the values in `backend/.env.example` (`admin@learnhub.com` / `change-me-in-production`) are placeholders, not live credentials. If `ADMIN_PASSWORD` isn't set as a real Variable on the API service, no admin account is created at all — the API only logs a warning, the UI just shows "Invalid credentials". Set `ADMIN_EMAIL`/`ADMIN_PASSWORD` to real values on the API service and **redeploy/restart it** — the admin account is only (re)seeded at container startup, so saving the variable alone isn't enough.
- **`API proxy error: connect ECONNREFUSED …:8080` on login:** the frontend container reached a private hostname but nothing accepted `:8080`. Usually the **API service is crash-looping** (check API runtime logs) or `BACKEND_PROXY_URL` points at the wrong private hostname. Fix/redeploy the API until `https://<api-domain>/health` returns `200`. On the **frontend** set `BACKEND_PROXY_URL=http://<api-private-hostname>:8080` (API → Networking → Private). Optional last resort: set `REACT_APP_BACKEND_URL` or `TRAINING_PLATFORM_URL` to the API’s public HTTPS URL so the frontend proxy can fall back when private networking fails; redeploy the frontend after changing variables.
- **Broken course thumbnails after redeploy:** attach persistent storage to the API service at `/app/uploads` and set `UPLOADS_DIR=/app/uploads`.
- **"Payment service not configured" at checkout:** the API has no Stripe secret key. Either set `STRIPE_API_KEY` (and ideally `STRIPE_WEBHOOK_SECRET`) on the **API** Zeabur service and redeploy/restart, or sign in as admin → **Stripe Payments** (`/admin/stripe-settings`) and paste a Secret (`sk_test_…` / `sk_live_…`) or Restricted (`rk_test_…` / `rk_live_…`) key from [Stripe API keys](https://dashboard.stripe.com/apikeys). Do **not** use a publishable `pk_…` key. Admin-saved keys override environment variables. Also configure a webhook to `https://<your-frontend-or-api-origin>/api/webhook/stripe` for `checkout.session.completed` (the admin page shows a copyable webhook URL).

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
| `src/i18n.js` | UI strings (EN, 繁中, 简中, 日本語, 한국어) |
| `src/pages/` | Extracted pages (`DashboardLayout`, `AdminCourseEditPage`) |

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
| POST | `/auth/forgot-password` | Send password reset email (always generic response) |
| POST | `/auth/reset-password` | Reset password with one-time token |
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
| POST | `/certificates` | Admin, client manager |
| GET | `/certificates/my` | Owner |
| GET | `/certificates/{id}` | Owner, admin, or client manager |
| GET | `/certificates/{id}/pdf` | Owner, admin, or client manager — PDF download |
| PUT | `/certificates/{id}/customize` | Admin |
| GET | `/certificate-settings` | Admin |
| PUT | `/certificate-settings` | Admin |

**Customize request body:**

```json
{
  "template": "default",
  "primary_color": "#002FA7",
  "secondary_color": "#0A0B10",
  "background": "geometric",
  "apply_to_course": false
}
```

Set `apply_to_course: true` to apply styling to all certificates for that certificate's course. `background` selects one of five artworks: `plain`, `geometric`, `waves`, `guilloche`, `corners`.

**Certificate settings** (managed from the certificate module itself, not course settings) control the certificate ID naming structure and default styling:

```json
{
  "id_format": "CERT-{year}-{seq:6}",
  "default_background": "plain",
  "default_primary_color": "#002fa7",
  "default_secondary_color": "#0a0b10"
}
```

`id_format` tokens: `{seq}`/`{seq:N}` (running sequence, zero-padded to `N`), `{year}`, `{month}`, `{day}`, `{random}`/`{random:N}`, `{course}` (short course code). Text outside braces is literal, so `CERT-{year}-{seq:6}` yields `CERT-2026-000042`.

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
| Password reset | User submits forgot-password request |

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
  template, primary_color, secondary_color, background, issued_at, valid_until
}
```

#### `platform_settings` (`_id: "certificate"`)
```javascript
{
  id_format, sequence, default_background,
  default_primary_color, default_secondary_color
}
```

</details>

---

## Environment Variables

Copy templates: `backend/.env.example`, `frontend/.env.example`, or for Docker Compose: `.env.docker.example` → `.env` at repo root.

### Backend

```bash
MONGO_URL=mongodb://localhost:27017 # also accepts MONGODB_URI / MONGO_CONNECTION_STRING / MONGO_URI
DB_NAME=learnhub
JWT_SECRET=                         # python -c "import secrets; print(secrets.token_hex(32))"

ENVIRONMENT=development             # production enables stricter defaults
COOKIE_SECURE=false                 # true in production (HTTPS)
CORS_ORIGINS=http://localhost:3000  # comma-separated; never * with credentials

ADMIN_EMAIL=admin@learnhub.com
ADMIN_PASSWORD=change-me-in-production
ADMIN2_EMAIL=admin2@learnhub.com
ADMIN2_PASSWORD=change-me-admin2

STRIPE_API_KEY=
STRIPE_CURRENCY=hkd # default HKD — also configurable in Admin → Stripe Payments
STRIPE_WEBHOOK_SECRET=
REQUIRE_STRIPE_WEBHOOK_SECRET=false # true in production

DEEPSEEK_API_KEY=
BREVO_API_KEY=
EMAIL_FROM=noreply@yourdomain.com
EMAIL_FROM_NAME=LearnHub
FRONTEND_URL=http://localhost:3000
RESET_PASSWORD_TOKEN_TTL_MINUTES=30
LOG_LEVEL=info                     # critical | error | warning | debug | trace; invalid values fall back to info
UPLOADS_DIR=                        # optional; defaults to backend/uploads (use /app/uploads in Docker/cloud)
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

Course thumbnails are stored in the `uploads_data` Docker volume (mounted at `/app/uploads` on the API container). They survive `docker compose down` unless you remove volumes with `-v`.

**Rebuild MongoDB + API only:**

```bash
# Rebuild/recreate the API container and restart MongoDB without deleting data
scripts/rebuild-mongo-api.sh

# Rebuild from a clean local MongoDB volume (destructive)
scripts/rebuild-mongo-api.sh --reset-db --yes

# Also pull the configured MongoDB image and start the web service afterward
scripts/rebuild-mongo-api.sh --pull-mongo --web
```

| Service | URL |
|---------|-----|
| Frontend | http://localhost:3000 |
| API | http://localhost:8001 |
| MongoDB | localhost:27017 |

**Individual images:**

```bash
# API only (requires external MongoDB)
docker build -t learnhub-api -f backend/Dockerfile .
docker run -p 8001:8080 --env-file .env learnhub-api

# Web only
docker build -t learnhub-web -f frontend/Dockerfile --build-arg REACT_APP_BACKEND_URL=http://localhost:8001 .
docker run -p 3000:8080 learnhub-web
```

### Zeabur (container deploy)

See **[Zeabur deployment](#zeabur-deployment)** above for the full service layout, environment variables, URL alignment, and troubleshooting.

Quick summary: one project needs **mongodb + one API service + frontend**. Do not create both `backend` and `training-platform`. Attach the public web domain to `frontend` and the API domain to your single API service.

**Production checklist (Zeabur):**

- [ ] Strong `JWT_SECRET` and `ADMIN_PASSWORD`
- [ ] `ENVIRONMENT=production`, `COOKIE_SECURE=true`
- [ ] `CORS_ORIGINS` and `FRONTEND_URL` set to the frontend origin (not `*`)
- [ ] `BACKEND_PROXY_URL` set on `frontend` to the API private hostname; **leave `REACT_APP_BACKEND_URL` unset** so the SPA uses the same-origin `/api` proxy (first-party cookies). If you must call the API cross-origin, set `COOKIE_SAMESITE=none` (with `COOKIE_SECURE=true`) or logins will loop
- [ ] API `/ready` returns `200` after Mongo is linked
- [ ] Stripe live keys + webhook secret enforced (if using payments)
- [ ] Brevo configured; `FRONTEND_URL` correct (if using email)

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
