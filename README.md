# Verified Shortlet App

Verified Shortlet is an API-first property booking platform with a Flask backend and a React frontend.

## Stack

- Backend: Flask, SQLAlchemy, Alembic, JWT auth
- Frontend: React, React Router, Axios, Vite
- Database: MySQL (configured through SQLAlchemy URI)

## Architecture

- Flask serves JSON APIs under `/api/*` only.
- React SPA handles all user-facing routes and rendering.
- Authentication and authorization are role-based (customer, host, admin) using JWT bearer tokens.
- API security includes request validation, upload checks, CORS controls, and security headers.

## Project Structure

- `pkg/`
  - `api/`: API blueprints and API-only helpers
  - `models.py`: SQLAlchemy entities
  - `config.py`: runtime and security config
  - `__init__.py`: app factory, blueprint registration, middleware
- `migrations/`: Alembic migration history
- `frontend/`: React SPA codebase
- `starter.py`: backend development entrypoint
- `requirements.txt`: backend Python dependencies

## Quick Start

### 1) Backend

1. Create and activate a virtual environment.
2. Install dependencies:
   - `pip install -r requirements.txt`
3. Copy `.env.example` to `.env` and update values.
4. Configure environment variables (see `docs/ENVIRONMENT.md`).
5. Run migrations:
   - `flask db upgrade`
6. Start API server:
   - `python starter.py`

Backend default URL: `http://127.0.0.1:8000`
API base path: `http://127.0.0.1:8000/api`

### 2) Frontend

1. Open `frontend/`.
2. Copy `.env.example` to `.env`.
3. Install dependencies:
   - `npm install`
4. Run dev server:
   - `npm run dev`

Set `VITE_API_BASE_URL` to your API base URL (default `http://127.0.0.1:8000/api`).

## Documentation

- API overview: `docs/API.md`
- Environment reference: `docs/ENVIRONMENT.md`
- Development workflow: `docs/DEVELOPMENT.md`
- Deployment checklist: `docs/DEPLOYMENT.md`
- Frontend details: `frontend/README.md`

## Operational Notes

- The backend is intentionally API-only in this phase.
- Legacy server-rendered pages and static site scaffolding were removed as part of cleanup.
- Query loading and selected React shared components were optimized to reduce runtime overhead.
