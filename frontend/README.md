# LearnHub Frontend

React single-page application for the LearnHub LMS.

## Stack

- React 19 + React Router
- Tailwind CSS + Shadcn UI
- Axios (cookie-based auth)
- Custom i18n (English / Traditional Chinese)

## Project Structure

```
src/
├── App.js              # Route definitions and page components
├── lib/api.js          # Axios client and error formatting
├── contexts/           # AuthProvider, LanguageProvider
├── components/         # Shared layout, guards, language switcher
├── components/ui/      # Shadcn UI primitives
└── i18n.js             # UI translation strings
```

## Setup

```bash
cd frontend
cp .env.example .env
# Set REACT_APP_BACKEND_URL to your API origin (e.g. http://localhost:8001)

yarn install
yarn start
```

The dev server runs at [http://localhost:3000](http://localhost:3000).

## Scripts

| Command | Description |
|---------|-------------|
| `yarn start` | Development server (CRACO) |
| `yarn build` | Production build |
| `yarn test` | Run tests |

## Environment

| Variable | Description |
|----------|-------------|
| `REACT_APP_BACKEND_URL` | Backend API origin (no trailing slash) |

## Docker

From the **repo root** (full stack with MongoDB):

```bash
cp .env.docker.example .env
docker compose up --build
```

Or build this service only:

```bash
docker build -t learnhub-web --build-arg REACT_APP_BACKEND_URL=http://localhost:8001 .
docker run -p 3000:8080 learnhub-web
```

> `REACT_APP_BACKEND_URL` must be reachable from the **browser** (usually `http://localhost:8001`), not an internal Docker hostname.
