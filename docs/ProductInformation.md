# Day 1 — Product Definition & Scope

## What is this and who is it for?

A production-hardened, session-based authentication system for Django REST Framework + React applications. It exists so developers building real Django + React apps don't rebuild auth from scratch — and don't rebuild it insecurely, which is the more common failure mode.

Primary audience: developers shipping a single-tenant SaaS-shaped web app who want session-based auth (not JWT) with OAuth, done to a standard that survives an actual security audit — not a tutorial-grade auth flow. Secondary purpose: this is a portfolio piece intended to read as senior-level engineering, not a toy project.

## Goals

- Email + full name + password signup, on a custom user model (overriding Django's default).
- Email + password login.
- Email-based password reset via Brevo (SMTP). Note for future production use: SendGrid is likely better value at scale ($20 = 50k emails/mo, no hard caps vs. Brevo's 300/day free tier) — noted here as a future swap, not a Day 1 decision.
- OAuth2 login/signup via Google and GitHub only.
- Password change for logged-in users: old password + new password required. Reuse of the last 10 passwords is blocked.
- Email change for logged-in users, with a notification sent to the *old* address on change (account-takeover signal).
- MFA via TOTP (e.g. Google Authenticator), with recovery codes. Built at Tier 3 (Day 48), not Sprint 0 — flagged here as in-scope so it doesn't drift.
- Unified session-management settings: view all active sessions, terminate any single one, and "log out from all other devices" (keeps the current session alive, kills the rest).
- Eliminate the standard authentication failure modes: CSRF, CORS misconfiguration, weak password hashing, predictable reset tokens, timing attacks, brute force, user enumeration.
- Sessions + Redis for auth state, not JWT — avoids blacklisting, refresh-token rotation, and logout-that-doesn't-actually-log-out, all of which are self-inflicted JWT problems.
- Security-first as a design constraint, not a bullet point retrofitted later.
- Sentry (error tracking) and Loki (log aggregation) and Cloudflare Turnstile/turning it on: in scope for this project, added at Tier 4 (Day 53/58 — structured logging and the ASVS pass), not Sprint 0 or Tier 1. Not deferred past v1.0; just not early. Never return a 500 full stack trace to the client. Always return a generic error message, and log the full stack trace server-side. Global error handler for Django + DRF, not just a per-view decorator. (See Day 53 for the full reasoning.) 


## Non-goals

- No user roles, permissions, or admin dashboard beyond Django's built-in admin. This is an auth system, not a user-management platform.
- No social login beyond Google and GitHub — no Facebook, Twitter/X, LinkedIn, Apple (it requires a developer account, and 99$ p/y just for a sign in/up with Apple button) etc. Fewer providers, fewer OAuth-quirk categories to defend.
- No i18n/l10n. English-only, single frontend origin, by design.
- No JWT. Sessions + Redis only — see Goals for reasoning.
- No mobile-app-specific auth surface (push-token handling, native deep-linking, etc.). This is built for a single web frontend. (DRF token auth exists as a documented Django/DRF pattern for anyone who later wants to extend this toward mobile — that's a note for future readers, not a Day 1 commitment or a hint of planned work.)
- No SAML, OIDC-as-a-provider, or enterprise SSO. Not building an enterprise identity platform.
- No multi-tenancy. Single-tenant assumption runs through the whole system (session model, rate-limit keys, everything).
- No `/me`-via-SSE or websocket push for account-data changes. A 5-minute React Query `staleTime` is an acceptable tradeoff against the complexity of a push channel for data that changes rarely. (Full reasoning revisited and finalized Day 64.)

## Tech stack

**Backend:** Django + DRF as the core. PostgreSQL for persistence. Redis for session storage, `/api/auth/me` caching, and rate-limiting. Celery for background work (primarily email sends) so nothing user-facing blocks on SMTP. Custom user model (email as `USERNAME_FIELD`, full name, email-verification status) rather than Django's default. Argon2id for password hashing via Django's built-in hasher framework. Cloudflare Turnstile for bot mitigation and WAF. Sentry + Loki for error tracking and logging (Tier 4, not Sprint 0).

**Frontend:** React + Vite. React Query for server-state/caching (this is what makes the `/me` caching strategy work). Tailwind CSS for styling.

## Folder structure (rough — finalized Day 3)

```
Backend:
config/                  (settings: base, dev, prod)
apps/
  auth/                  (authentication)
    models.py            (custom user model)
    serializers.py
    views.py
    urls.py
    tasks.py             (Celery: email sends)
    signals.py
    tests.py
  accounts/              (user profile / account management)
    models.py
    serializers.py
    views.py
    urls.py
    signals.py
    tests.py

```

Frontend:
src/
components/
pages/
services/
utils/
App.jsx
main.jsx

*Flag for Day 3: no explicit home yet for MFA (TOTP setup, recovery codes) or session-management endpoints (list/revoke) — both are core deliverables per the roadmap and need a folder decision, not an assumption they fit inside `auth/`.*

## Milestone list (maps to the five tiers)

- **90%** — Works end to end for a real user: email signup/login, Google OAuth, GitHub OAuth, password reset, change password, change email, logout, `/me`, CORS all functioning together.
- **95%** — Prod-frequent edge cases handled and tested: rate limiting, OAuth provider quirks (GitHub private email, collision handling), verification/reset edge cases, session fixation/ghost-session fixes.
- **96%** — Low-probability, high-severity, fixed regardless of rarity: timing-attack mitigation (measured, not assumed), breach-password checking, MFA (TOTP + recovery codes), re-auth for sensitive actions.
- **97%** — Rare but cheap enough that skipping has no real argument: operational resilience (Redis failure behavior, structured logging), self-run OWASP ASVS audit and fixes, health checks.
- **98%** — Last few things worth the small remaining cost: race conditions (signup, reset-token reuse), load testing and the first real bottleneck fixed, finalized threat model.
- **The remaining 2%** — deliberately out of scope: novel/future attack vectors, enterprise auth (SAML/OIDC-as-provider), multi-tenancy, JWT (not needed for this project). Not unfinished — an honest ceiling.

## Production-readiness definition

**Login:** email+password, Google OAuth, GitHub OAuth. No timing attacks, brute force, or user enumeration.

**Signup:** same three paths. Email verification never leaks whether an account already exists — a signup attempt against an existing email gets the identical response and screen as a new one.

**Password reset:** email-based, generic response regardless of whether the email exists, dispatched async via Celery so response timing doesn't leak existence either. Strict rate limiting against brute force.

**Change password:** requires old password. Blocks reuse of the last 10 passwords. Kills all other active sessions on change (prevents a stolen session from surviving a password rotation meant to kill it).

**Change email:** requires current password (re-auth). Notifies the *old* address of the change. Kills all other sessions. If the person will old email clicks: This wasn't me,
you immediately on the backend, freeze the account. Next, the user reaches out to the support team to verify identity and regain access. This is a standard account-takeover signal. 


**`/api/auth/me`:** returns current user (email, full name, verification status) or a generic unauthenticated response — never leaks user existence via response shape. Cached in Redis server-side and React Query client-side, write-through invalidation on any mutating action, explicit cache-bust on logout.

**Logout:** single-session and all-sessions variants. CSRF protection via tokens + `SameSite` cookies. Session ID regenerated on login (fixation prevention). Redis session key deleted immediately, not just cookie-cleared client-side.

**Settings / session management:** view all active sessions, terminate any one, log out everywhere. Same CSRF/fixation protections as logout.

**Out of scope (the 2%):** forever-open attack surface (novel/future vectors), enterprise-grade auth, multi-tenancy, JWT (not needed for this project). Explicitly not chased.

## Success criteria (beyond "it runs")

- A complete, secure, drop-in-able auth system for Django + React apps — saves the standard weeks of auth boilerplate and gets the security-sensitive parts right by default, not by luck.
- A reference implementation of authentication best practices — documented well enough to double as a learning resource, not just a working system.
- Used, or at minimum usable, by developers who'd actually run it in production — not a demo that only survives a happy-path walkthrough.
- Functions as a serious portfolio piece supporting a remote backend/full-stack job search — should read as something a senior engineer would forward internally, per the project's own stated bar.

## What exactly am I building?

A session-based (Redis-backed, not JWT) authentication system for Django + DRF + React, supporting email/password and Google/GitHub OAuth signup and login, password reset, password and email change with reuse/notification protections, TOTP-based MFA, full session visibility and management, and the standard authentication attack surface (CSRF, timing, enumeration, brute force, fixation) closed by default — built to a security-audited, load-tested, production-hardened standard, not a tutorial-grade implementation.