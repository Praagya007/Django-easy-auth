# Day 3 — Architecture

Sprint 0, Day 3. System diagram, folder structure, service-layer / serializer / permissions conventions, caching strategy, session lifecycle, and the full API route list — before any application code exists.

---

## System diagram

```mermaid
flowchart TB
    Browser["React SPA"]
    Cloudflare["Cloudflare (Turnstile, Bot Mitigation, WAF)"]
    Caddy["Caddy (Reverse Proxy, TLS, Static Files)"]
    Django["Django + DRF (Gunicorn with Uvicorn workers)"]
    Celery["Celery worker"]
    Redis[("Redis (Sessions + Broker)")]
    Postgres[("PostgreSQL")]
    Google["Google OAuth"]
    GitHub["GitHub OAuth"]
    SMTP["SMTP (Brevo / SES)"]
    Inbox["User inbox"]

    Browser -->|HTTPS| Cloudflare
    Cloudflare -->|Filtered Traffic| Caddy
    Caddy -->|"/api/*"| Django
    Caddy -->|Static Build| Browser

    Django <-->|Session Read/Write| Redis
    Django <-->|Queries| Postgres
    Django -->|Enqueue Task| Redis
    Django -.->|Redirect + Callback| Google
    Django -.->|Redirect + Callback| GitHub

    Redis -->|Dequeue Task| Celery
    Celery -->|Queries| Postgres
    Celery -->|Send| SMTP
    SMTP -->|Deliver| Inbox

```

Browser traffic routes through Cloudflare first, which provides WAF, bot mitigation, and Turnstile challenges before hitting your infrastructure. Once cleared, traffic reaches Caddy, which serves the built React app directly for frontend routes and proxies all /api/* requests to Django. Django handles session states via Redis, queries PostgreSQL, and manages external authentication through Google and GitHub OAuth redirects. For asynchronous jobs, Django enqueues tasks into Redis, allowing Celery to dequeue them and trigger transactional emails via SMTP to the user's inbox.

---

## Folder structure

```
Django_Easy_Auth/
├── config/                     # project root — settings, URLs, WSGI/ASGI entry points
│   ├── __init__.py
│   ├── asgi.py
│   ├── wsgi.py
│   ├── urls.py
│   └── settings/
│       ├── __init__.py
│       ├── base.py
│       ├── dev.py
│       └── production.py
│
├── core/                        # cross-app shared code — the ONE global handler, not per-app logic
│   ├── __init__.py
│   └── exceptions.py            # global DRF exception handler: catches anything unhandled,
│                                 # formats a uniform JSON error payload, logs it — infra-level,
│                                 # not business-level (see each app's own exceptions.py for that)
│
├── auth/                        # unauthenticated flows: signup, login, verify, password reset
│   ├── __init__.py
│   ├── models.py
│   ├── exceptions.py            # app-specific exceptions services raise, e.g. TokenExpired
│   ├── serializers.py           # input/output shape only, no business logic
│   ├── services.py              # business logic — signup, login, reset
│   ├── tasks.py                 # celery tasks — verification/reset emails
│   ├── views.py                 # thin — routing + calling services
│   └── tests.py
│
├── accounts/                    # authenticated self-service: change password/email, profile
│   ├── __init__.py
│   ├── models.py
│   ├── exceptions.py
│   ├── serializers.py
│   ├── services.py
│   ├── tasks.py
│   ├── permissions.py           # object-level: users can only touch their own data
│   ├── views.py
│   └── tests.py
│
├── mfa/                          # TOTP setup, verify, disable, recovery codes
│   ├── __init__.py
│   ├── models.py                 # recovery codes at minimum — confirm what allauth's MFA module covers
│   ├── exceptions.py
│   ├── serializers.py
│   ├── services.py
│   ├── views.py
│   └── tests.py
│
└── sessions/                     # active-session listing, revoke-one, revoke-all
    ├── __init__.py
    ├── exceptions.py
    ├── serializers.py
    ├── services.py
    ├── views.py
    └── tests.py
```

`sessions` is a separate app from `accounts` despite the FK dependency — session management has its own roadmap days (35, 36, 41, 49: ghost-session fix, concurrent-session policy, session-behavior tests, revoke actions) and its own service surface, not just a couple of thin fields on the user.

---

## Service layer

- All business logic lives in `services.py`. Views are thin — routing and calling services only.
- Every app has its own `exceptions.py` for plain, app-specific exceptions that services raise (e.g. `TokenExpired`). This is separate from `core/exceptions.py`, which holds the one global DRF exception handler — it intercepts anything unhandled project-wide, formats a uniform JSON error payload, and logs it. Infra-level, not business-level.
- A service function is skipped only when the abstraction would add more complexity than it removes. Given this project's nature, that's the exception, not the default — service layer exists for almost every view.

## Serializer conventions

1. Serializers only serialize/deserialize. No business logic.
2. `SerializerMethodField` is avoided unless necessary, and only for read-only fields — never for write operations.
3. Validated data is passed to the service layer as keyword arguments:
   ```python
   your_service_function(**serializer.validated_data)
   ```
4. Serializers do strict input validation — password length/complexity, email format, and similar shape-level checks. This is genuinely their job.
5. Serializers only raise input/output-level exceptions. Everything else is raised elsewhere: `permissions.py` for permission exceptions, `services.py` for business-logic exceptions, the global exception handler for 500s (never leaking a full stack trace to the client).

## Permissions architecture

1. Permissions live in each app's `permissions.py`, unless the logic is a genuine one-off simple enough to wire directly onto the view.
2. Permissions raise 404, not 403, for resources that don't belong to the requesting user — this avoids leaking whether the resource exists at all.
3. `permissions.py` only raises permission-related exceptions — nothing else.
4. Mechanism depends on the case: `get_object_or_404` scoped to the requesting user is the default for private, per-user data (handles level-2 object ownership automatically, collapsing "doesn't exist" and "not yours" into the same 404). A permission class raising 403 is used instead for genuinely shared/role-based access cases.

**Level 0** — no auth required: login, signup, password reset (unauthenticated), email verification, CSRF cookie fetch.

**Level 1** — authenticated: session list, profile, password change, email change — anything that just requires being logged in.

**Level 2** — level 1 + object ownership: same actions as above, scoped to the specific resource being *this* user's. Anything the user has no business accessing returns 404, never 403.

## Caching strategy

**`/api/auth/me`**
- Client side: React Query, 5-minute TTL. The cache is actively busted on every mutating action below, so it's never meaningfully stale in normal use — the TTL exists purely as a fallback/data-sync safety net, not as the primary invalidation mechanism.
- Server side: Redis, ~7-day TTL, cache warmup via cron during off-peak hours. Justified by an overwhelmingly high read/write ratio — this endpoint gets hit on every protected route.
- Invalidation events (both client and server cache, unless noted): email change, password change, profile change (full name, etc.), nuclear logout (all devices), MFA enabled/disabled, login-method changes (linking/unlinking social accounts). A single-device logout does **not** invalidate this cache — other devices' sessions remain valid and `/me` for them is still correct.

**Session list**
- Client side: React Query, invalidated on logout, nuclear logout, or a specific device logout.
- Server side: Redis, scoped per user, high TTL justified by a high read/write ratio (users rarely log in/out relative to how often the list might be viewed). Write-through cache; invalidated on any session-purge event (not just explicit logout — this includes the Day 35 ghost-session purge). On cache failure, serve accurate data straight from the DB, stop relying on the cache, and log the failure to Sentry.

Client-side and server-side invalidation are independent — a fresh backend invalidation does not guarantee an open browser tab's client cache reflects it instantly; the 5-minute client fallback window covers that gap by design, not by bug.

## Session lifecycle

1. Without "remember me," the session ends as soon as the browser closes.
2. With "remember me," session TTL is 7 days with sliding expiration — activity extends it, tracked via `last_active_at`. 7 days of inactivity expires the session.
3. On password change:
   - Changed while **logged out** (via reset flow): purge all sessions, all devices.
   - Changed while **logged in**: purge all sessions except the current one, so the user isn't logged out of the session they're actively using. Same rule applies to email changes. Non-sensitive field changes (e.g. full name) don't purge anything.

Device identification for the session list is derived from the User-Agent header at session-creation time (browser/OS/device type) — not a persisted device fingerprint. Location (city/country) is deliberately deferred for v1; device + IP address is sufficient to distinguish sessions.

---

## API route list

Conventions: camelCase in all JSON. Cursor pagination where relevant. Every authenticated endpoint requires a valid session; CSRF required on all state-changing requests.

### `GET /api/auth/csrf` — L0

Sets the CSRF cookie.

| Status | Body |
|---|---|
| 200 | `{ "detail": "CSRF cookie set successfully." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `POST /api/auth/register` — L0

Body: `email`, `password`, `fullName`

| Status | Body |
|---|---|
| 200 | `{ "detail": "If this email exists, a verification email has been sent. Please check your inbox." }` *(enumeration-safe — identical regardless of whether the email exists)* |
| 400 | `{ "message": "Validation failed.", "errors": { "email": ["Email is required.", "Email must be a valid email address."], "password": ["Password is required.", "Password must be at least 12 characters long.", "Password must not exceed 64 characters.", "This password is too common. Please choose a different password.", "This password has been found in a data breach. Please choose a different password."], "fullName": ["Full name is required.", "Full name must be at least 2 characters long.", "Full name must not exceed 200 characters."] } }` |
| 401 | `{ "detail": "CSRF token missing." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `POST /api/auth/login` — L0

Body: `email`, `password`

| Status | Body |
|---|---|
| 200 | `{ "detail": "Login successful." }` |
| 400 | `{ "message": "Validation failed.", "errors": { "email": ["Email is required.", "Email must be a valid email address."], "password": ["Password is required.", "Password must be at least 12 characters long."], "nonFieldErrors": ["Invalid credentials."] } }` |
| 401 | `{ "detail": "CSRF token missing." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `POST /api/auth/reset-password` — L0

Body: `email`

| Status | Body |
|---|---|
| 200 | `{ "detail": "If this email exists, a password reset email has been sent. Please check your inbox." }` *(enumeration-safe)* |
| 400 | `{ "message": "Validation failed.", "errors": { "email": ["Email is required.", "Email must be a valid email address."] } }` |
| 401 | `{ "detail": "CSRF token missing." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `GET /api/auth/sessions` — L1

| Status | Body |
|---|---|
| 200 | `{ "sessions": [ { "id": "sess_938472910a3f8b1c", "isCurrent": true, "createdAt": "2026-07-15T08:30:00Z", "lastActiveAt": "2026-07-20T16:20:00Z", "expiresAt": "2026-08-15T08:30:00Z", "ipAddress": "192.0.2.1", "device": { "browser": "Chrome 124.0", "os": "macOS 14.4", "deviceType": "desktop" } } ], "previous": "https://api.example.com/api/auth/sessions?cursor=prev_cursor_value", "next": "https://api.example.com/api/auth/sessions?cursor=next_cursor_value" }` |
| 401 | `{ "detail": "Authentication credentials were not provided." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `DELETE /api/auth/sessions/{sessionId}` — L2

| Status | Body |
|---|---|
| 200 | `{ "detail": "Session terminated successfully." }` |
| 401 | `{ "detail": "CSRF token missing." }` or `{ "detail": "Authentication credentials were not provided." }` |
| 404 | `{ "detail": "Session not found." }` *(same message whether the session doesn't exist or belongs to another user)* |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `DELETE /api/auth/sessions/terminate-all` — L1

| Status | Body |
|---|---|
| 200 | `{ "detail": "All other sessions terminated successfully." }` |
| 401 | `{ "detail": "CSRF token missing." }` or `{ "detail": "Authentication credentials were not provided." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `PATCH /api/auth/change-email` — L2

Body: `newEmail`

| Status | Body |
|---|---|
| 200 | `{ "detail": "Email change request successful. A verification email has been sent to your new address." }` |
| 400 | `{ "message": "Validation failed.", "errors": { "newEmail": ["New email is required.", "New email must be a valid email address."] } }` |
| 401 | `{ "detail": "CSRF token missing." }` or `{ "detail": "Authentication credentials were not provided." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `POST /api/auth/change-password` — L2

Body: `oldPassword`, `newPassword`

| Status | Body |
|---|---|
| 200 | `{ "detail": "Password change successful." }` |
| 400 | `{ "message": "Validation failed.", "errors": { "oldPassword": ["Old password is required."], "newPassword": ["New password is required.", "New password must be at least 12 characters long.", "New password must not exceed 64 characters.", "This password is too common. Please choose a different password.", "This password has been found in a data breach. Please choose a different password."], "nonFieldErrors": ["Old password is incorrect."] } }` |
| 401 | `{ "detail": "CSRF token missing." }` or `{ "detail": "Authentication credentials were not provided." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `GET /api/auth/me` — L1

| Status | Body |
|---|---|
| 200 | `{ "id": "user_1234567890abcdef", "email": "youremail@email.com", "fullName": "Your Full Name", "isEmailVerified": true, "mfaEnabled": true, "createdAt": "2026-07-15T08:30:00Z", "loginMethod": "email_password" }` *(loginMethod: `email_password` \| `google_oauth` \| `github_oauth`)* |
| 401 | `{ "detail": "Authentication credentials were not provided." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `GET /api/auth/mfa` — L1

Initiates MFA setup.

| Status | Body |
|---|---|
| 200 | `{ "qrCodeUrl": "https://example.com/qrcode.png", "secret": "JBSWY3DPEHPK3PXP" }` |
| 401 | `{ "detail": "CSRF token missing." }` or `{ "detail": "Authentication credentials were not provided." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `POST /api/auth/mfa/verify` — L1

Body: `code`

| Status | Body |
|---|---|
| 200 | `{ "detail": "MFA verification successful." }` |
| 400 | `{ "message": "Validation failed.", "errors": { "code": ["MFA code is required.", "MFA code must be a 6-digit number."], "nonFieldErrors": ["Invalid MFA code."] } }` |
| 401 | `{ "detail": "CSRF token missing." }` or `{ "detail": "Authentication credentials were not provided." }` |
| 409 | `{ "detail": "MFA is not enabled for this user." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `POST /api/auth/mfa/disable` — L1

| Status | Body |
|---|---|
| 200 | `{ "detail": "MFA disabled successfully." }` |
| 401 | `{ "detail": "CSRF token missing." }` or `{ "detail": "Authentication credentials were not provided." }` |
| 409 | `{ "detail": "MFA is not enabled for this user." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `POST /api/auth/mfa/recovery-codes` — L1

| Status | Body |
|---|---|
| 200 | `{ "recoveryCodes": ["code1", "code2", "code3", "code4", "code5", "code6", "code7", "code8", "code9", "code10"] }` |
| 401 | `{ "detail": "CSRF token missing." }` or `{ "detail": "Authentication credentials were not provided." }` |
| 409 | `{ "detail": "MFA is not enabled for this user." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `POST /api/auth/logout` — L1

| Status | Body |
|---|---|
| 200 | `{ "detail": "Logout successful." }` |
| 401 | `{ "detail": "CSRF token missing." }` or `{ "detail": "Authentication credentials were not provided." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `POST /api/auth/verify-email` — L0

Body: `token`

Called by the React landing page on mount, after the user clicks the link in their email.

| Status | Body |
|---|---|
| 200 | `{ "detail": "Email verified successfully." }` |
| 400 | `{ "message": "Validation failed.", "errors": { "token": ["Token is required."] } }` |
| 409 | `{ "detail": "This verification link has already been used." }` |
| 410 | `{ "detail": "This verification link has expired. Please request a new one." }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### `POST /api/auth/resend-verification` — L0/L1 hybrid

Body: `email` *(optional — falls back to `request.user.email` if authenticated)*

| Status | Body |
|---|---|
| 200 | `{ "detail": "If an account with this email exists and is unverified, a new verification email has been sent." }` *(enumeration-safe — identical regardless of whether the account exists, is already verified, or doesn't exist)* |
| 400 | `{ "message": "Validation failed.", "errors": { "email": ["Email is required if not authenticated.", "Email must be a valid email address."] } }` |
| 429 | `{ "detail": "Please wait before requesting another verification email.", "retryAfter": 45 }` |
| 500 | `{ "detail": "An unexpected error occurred. Please try again later." }` |

### OAuth — deferred

**Google, GitHub init + callback** — handled via django-allauth headless's default URL scheme. Exact paths confirmed on Day 11 (allauth install) / Day 22–23 (provider config), documented then. One redirect + one callback per provider; new-vs-existing-user branching happens inside the callback per the Day 24 account-linking policy, not via separate signup/login routes.

---

## Invoicify conventions 

API conventions: this project reuses Invoicify's conventions — camelCase JSON, cursor pagination — rather than diverging. The sessions list is the one endpoint in this project where pagination is genuinely relevant.