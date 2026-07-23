# Verified Shortlet App

Verified Shortlet is a production-style shortlet booking platform built with Flask, MySQL, and Docker. It supports property discovery, host onboarding, booking flows, payments, host verification, notifications, and an admin dashboard for moderation and operational oversight.

This repository contains a Flask web application with a server-rendered UI powered by Flask templates and Jinja2, backed by SQLAlchemy models and Alembic migrations.

## Why this project exists

The platform is designed to make shortlet management feel simple for three groups of users:

- Visitors can browse properties, view details, and reserve stays.
- Hosts can list properties, manage bookings, and submit verification documents.
- Admins can review properties, oversee bookings, and approve or reject host verification.

## Core features

- Property listing and detail pages
- User registration, login, and role-based access
- Host property submission and dashboard management
- Booking and reservation flow
- Payment initiation and confirmation experience
- Host verification workflow with NIN document upload
- Notifications for booking and verification events
- Admin dashboard for properties, bookings, and payments
- Dockerized deployment with Nginx and MySQL

## Tech stack

- Backend: Python, Flask, Flask-SQLAlchemy, Flask-Migrate, WTForms
- Templating: Jinja2
- Database: MySQL
- Deployment: Docker Compose, Gunicorn, Nginx
- Auth & security: session-based auth, CSRF protection, environment-based config

## Project structure

- [pkg/](pkg) — application package containing routes, models, services, templates, and forms
- [migrations/](migrations) — Alembic migrations
- [deployment/](deployment) — Docker and Nginx configuration
- [instance/](instance) — instance-specific config support
- [private_uploads/](private_uploads) — uploaded host documents and media assets
- [starter.py](starter.py) — application entry point
- [docker-compose.yml](docker-compose.yml) — local container orchestration

## Prerequisites

Before running the app locally, make sure you have:

- Python 3.10+
- MySQL running locally or Docker available
- pip and virtualenv

## Local development

### 1) Create and activate a virtual environment

On macOS/Linux:

```bash
python -m venv venv
source venv/bin/activate
```

On Windows PowerShell:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
```

### 2) Install dependencies

```bash
pip install -r requirements.txt
```

### 3) Configure environment variables

Create a `.env` file at the project root with values such as:

```env
SECRET_KEY=change-me-in-development
SQLALCHEMY_DATABASE_URI=mysql+mysqlconnector://root:rootpass@127.0.0.1:3307/shortletdb
MYSQL_DATABASE=shortletdb
MYSQL_USER=appuser
MYSQL_PASSWORD=appuserpass
MYSQL_ROOT_PASSWORD=rootpass
PAYSTACK_PUBLIC_KEY=your-public-key
PAYSTACK_SECRET_KEY=your-secret-key
PAYSTACK_CALLBACK_URL=http://127.0.0.1:8000/payment
PORT=8000
```

### 4) Run database migrations

```bash
set FLASK_APP=starter.py
flask db upgrade
```

### 5) Start the app

```bash
python starter.py
```

The app should be available at:

- http://127.0.0.1:8000
- production url: https://verified-shortlet-app-production.up.railway.app/
- Health endpoint: http://127.0.0.1:8000/healthz

## Docker deployment

The project is also ready for containerized deployment using Docker Compose.

```bash
docker compose up --build
```

This starts:

- the Flask application
- MySQL
- Nginx as a reverse proxy

The default entrypoint runs migrations and launches Gunicorn automatically.

## Typical user journeys

- A visitor browses available properties and checks booking availability.
- A host registers, adds property details, and uploads verification documents.
- A customer completes a booking and proceeds through the payment experience.
- An admin reviews property or host verification status from the dashboard.

## Development notes

- Database migrations are managed with Alembic.
- Static assets live under [pkg/static](pkg/static).
- Templates are organized under [pkg/templates](pkg/templates).
- Uploaded documents are stored under [private_uploads](private_uploads).

## Next steps

If you want to extend the platform, a strong next step would be to improve the current Flask experience with additional admin workflows, richer booking automation, and stronger deployment hardening.
