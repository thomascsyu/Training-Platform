# AGENTS.md

## Cursor Cloud specific instructions

LearnHub is a single product made of three services that must all run for end-to-end work:

| Service | Location | Dev run command | Port |
|---------|----------|-----------------|------|
| MongoDB | system package (mongodb-org 8) | `mongod --dbpath /data/db --bind_ip 127.0.0.1 --port 27017` | 27017 |
| Backend API (FastAPI) | `backend/` | `backend/venv/bin/uvicorn server:app --host 0.0.0.0 --port 8001 --reload` | 8001 |
| Frontend (React/CRACO) | `frontend/` | `yarn start` (from `frontend/`) | 3000 |

Standard setup/run/test commands live in `README.md` (Quick Start, Testing) and `frontend/README.md`; the update script already installs backend (`backend/requirements.txt`) and frontend (`yarn install`) deps. Below are only the non-obvious caveats.

### Startup caveats

- **MongoDB has no systemd** in this VM — start `mongod` manually (data dir `/data/db`). The API's `/ready` endpoint returns `503` until Mongo is connected; `/health` is always `200`.
- **Backend `.env` is required.** `cp backend/.env.example backend/.env` and set a real `JWT_SECRET` and `ADMIN_PASSWORD` (the admin account is only seeded when `ADMIN_PASSWORD` is set). It is gitignored, so it persists via the VM snapshot, not git.
- **Frontend local-dev must set `REACT_APP_BACKEND_URL`.** Create `frontend/.env` containing `REACT_APP_BACKEND_URL=http://localhost:8001` (this is the README Quick Start flow). This makes the browser call the backend directly instead of via the webpack-dev-server `/api` proxy. **Do not rely on the same-origin `/api` proxy in dev:** the `@emergentbase/visual-edits` dev middleware reads the body of every JSON `POST` and does not re-stream it, so proxied POSTs (e.g. `/api/auth/login`) hang forever. Direct `REACT_APP_BACKEND_URL` calls avoid this. Changing `frontend/.env` requires restarting `yarn start` (and a browser reload to pick up the new bundle).
- Cross-origin auth works because the API sets `CORS_ORIGINS=http://localhost:3000` with credentials and `localhost:3000`/`localhost:8001` are same-site (cookies are `SameSite=lax`).

### Testing caveats

- **Backend unit tests: run with `backend/.env` absent.** `python -m pytest tests/ -q` normally passes 51/51, but `backend/config.py` calls `load_dotenv()`, which auto-loads `backend/.env` (from `backend/`) and makes `tests/test_config.py::test_cors_origins_default_to_frontend_url` fail. Temporarily move `backend/.env` aside when running the suite, or run in an environment without it. Use the repo venv: `backend/venv/bin/python -m pytest tests/ -q`.
- Frontend tests: `CI=true yarn test` (from `frontend/`). There is no standalone ESLint config; lint runs through CRACO during `yarn start` / `yarn build`, so `CI=true yarn build` doubles as the lint check (ESLint warnings become errors).
- Integration tests `backend_test.py` / `comprehensive_backend_test.py` need a running API + MongoDB.
