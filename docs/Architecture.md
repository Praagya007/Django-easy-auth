# Day 3 — Architecture

Sprint 0, Day 3. System diagram, folder structure, service-layer / serializer / permissions conventions, caching strategy, session lifecycle, and the full API route list — before any application code exists.

---

## System diagram

```mermaid
flowchart TB
    Browser["React SPA"]
    Caddy["Caddy — reverse proxy, TLS, static files"]
    Django["Django + DRF (Gunicorn with Uvicorn workers)"]
    Celery["Celery worker"]
    Redis[("Redis — sessions + broker")]
    Postgres[("PostgreSQL")]
    Google["Google OAuth"]
    GitHub["GitHub OAuth"]
    SMTP["SMTP (Brevo / SES)"]
    Inbox["User inbox"]

    Browser -->|HTTPS| Caddy
    Caddy -->|"/api/*"| Django
    Caddy -->|static build| Browser

    Django <-->|session read/write| Redis
    Django <-->|queries| Postgres
    Django -->|enqueue task| Redis
    Django -.->|redirect + callback| Google
    Django -.->|redirect + callback| GitHub

    Redis -->|dequeue task| Celery
    Celery -->|queries| Postgres
    Celery -->|send| SMTP
    SMTP -->|deliver| Inbox
```

Browser talks only to Caddy. Caddy routes `/api/*` to Django and serves the built React app directly for everything else. Django reads/writes Redis for sessions, queries Postgres, and redirects to Google/GitHub for OAuth. Django enqueues jobs onto Redis; Celery dequeues them to send email via SMTP.
