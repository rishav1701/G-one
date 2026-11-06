# Architecture

G One is a single-process FastAPI application backed by PostgreSQL and a React single-page application. It is a simulated adult-ward deterioration demonstration, not for clinical use.

## Runtime components

- **Backend:** Python 3.11, FastAPI, Pydantic, SQLAlchemy, Alembic, and psycopg. The API owns authentication, role and ward authorization, audit events, observations, NEWS2 calculation, alert lifecycle, analytics, labs, and model integration.
- **Database:** PostgreSQL. Migrations are applied with Alembic; the application does not create its schema at runtime.
- **Frontend:** React, TypeScript, Vite, TanStack Query, and React Router. The packaged UI is built once and served by Nginx.
- **Simulator:** deterministic seeded synthetic observations sent through the same public ingestion service used by the application.
- **Model interface:** only a verified accepted artifact in `models/active` can load. There is no uploaded or requested model path. NEWS2 remains the only alert-driving score. The shipped state has no trained model.

## Request flow

The browser makes same-origin `/api` requests. In Docker, Nginx proxies those requests to the backend and serves the static React build with security headers. The API validates the session cookie and CSRF token, enforces role and ward scope, performs parameterized ORM operations, records audit events, and returns JSON with a request ID. The database stores only synthetic patient identifiers, age, sex, ward/admission, observations, scores, alerts, audit events, and demo results.

## Local development

Vite proxies `/api` to `http://localhost:8000`. PostgreSQL is the only supported application database. Tests that depend on constraints and timestamp behavior run against PostgreSQL. Pure domain tests may use no database.

## Deployment boundary

Compose is a local demonstration configuration. It uses one Uvicorn worker and does not provide production TLS termination, secrets management, backups, high availability, paging, device connectivity, clinical validation, or a hospital deployment profile.
