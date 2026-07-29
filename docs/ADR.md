# ADR-001: Sessions over JWT

**Status:** Accepted

**Context:**
Need to choose an authentication mechanism for a single-frontend-origin app with no third-party API consumers or mobile clients in scope.

**Decision:**
Use Django's built-in session authentication, not JWT.

**Reasoning:**
- Native to Django — supported at the framework level, no extra library required for the core mechanism.
- Sessions stored in Redis, not the DB — horizontal scaling of the session store is trivial.
- Server-side revocation is immediate and precise: kill one device's session, all of a user's sessions, or force a re-login on demand.
- JWT's "stateless" pitch breaks down in practice — production-ready JWT still needs state (refresh tokens, a revocation/blacklist store), which means building the same infrastructure sessions give you for free, plus more moving parts.
- JWT fits third-party APIs, mobile apps, and genuinely distributed systems. This project is none of those.

**Consequences:**
- If Redis goes down, users are logged out and must re-login. Acceptable at this scale; mitigated at larger scale via Redis clustering/HA (see ADR-002).
- Ties the app to Redis being available for any authenticated request — an explicit dependency, not a hidden one.

**Guiding principle:** Earn your complexity. Sessions + Redis is boring, well-understood, and sufficient. JWT would add complexity this project doesn't need and, if implemented incompletely, would be less secure than the boring option.

---

# ADR-002: Redis-backed sessions over DB-backed sessions

**Status:** Accepted

**Context:**
Given ADR-001 (sessions over JWT), need to decide where session data lives.

**Decision:**
- Pure Redis-backed sessions, not database-backed.
- Added a SESSION_COOKIE_AGE for 14 days and SESSION_EXPIRE_AT_BROWSER_CLOSE to True, 
if the user doesn't click remember me, they will be logged out.
- We're using django-redis as our cache backend — not just for session storage, but also for general application caching and as the Celery broker. Since Redis was already wired up for those other jobs, we pointed Django's built-in cache-based session engine at that same CACHES["default"] instead of adding a separate Redis connection just for sessions. One Redis connection, three jobs, rather than three separate ones.

**Reasoning:**
- Sub-millisecond read/write latency, faster than a DB round-trip.
- Horizontally scalable independent of the primary database.
- Native TTL support — session expiry doesn't need a cron job or scheduled cleanup task.
- HA available via Redis Cluster if needed later.
- Supports cross-device logout via pub/sub, which the project requires (session revocation, "log out everywhere").

**Consequences:**
- Session availability now depends on Redis uptime (see ADR-001's consequences — this is the same tradeoff, stated from the storage-layer side).

---

# ADR-003: Celery for async SMTP email sending

**Status:** Accepted

**Context:**
Several flows (signup, verification, password reset) require sending email. Synchronous SMTP calls block the request-response cycle and are unreliable.

**Decision:**
Send all SMTP email through Celery as background tasks, never synchronously in the request path.

**Reasoning:**
- Synchronous email sending can be slow, time out, or fail outright, leaving the user hanging on a blocked request.
- Users expect an immediate response; email delivery is not something they should wait on.
- Celery provides retry, scheduling, exponential backoff, and rate limiting out of the box — capability that would otherwise need to be hand-built.

**Consequences:**
- Adds Celery + Redis-as-broker as required infrastructure, not just for sessions.
- Introduces eventual-consistency between "action taken" and "email delivered" (e.g. brief delay before a verification email arrives) — acceptable given the UX and reliability tradeoff.

---

# ADR-004: Caddy over Nginx

**Status:** Accepted

**Context:**
Need a reverse proxy / static file server in front of Django and the React build.

**Decision:**
Use Caddy.

**Reasoning:**
- Automatic HTTPS with minimal configuration.
- Simple, readable config syntax — avoids spending disproportionate time on proxy configuration when the project's focus is the auth system, not the proxy layer.
- Built-in HTTP/2, HTTP/3, reverse proxying, load balancing, and edge-level rate limiting.
- Written in Go — fast, and its memory footprint, while higher than Nginx's C implementation, is a minor tradeoff given the features gained.
- Production-proven at scale (e.g. used by Stripe) — not a toy server.

**Consequences:**
- Nginx has a larger install base, more community troubleshooting material, and more battle-tested edge-case handling in extreme/high-scale scenarios. Acceptable tradeoff for this project's scale and priorities. 

---

# ADR-005: React Query for caching `/api/auth/me`

**Status:** Accepted

**Context:**
Every protected route needs to confirm the user is authenticated, which naively means an API call to `/me` on every navigation.

**Decision:**
Cache `/api/auth/me` client-side with React Query.

**Reasoning:**
- Avoids redundant API calls to `/me` on every protected-route visit when the session state hasn't changed.
- Reduces server load and improves perceived frontend performance.
- `staleTime` of 5 minutes acts as a TTL fallback, not the primary invalidation mechanism.

**Cache invalidation triggers:**
Cache is explicitly busted on: email change, name change, password change, logout (current device), logout of a specific device, logout of all devices.

**Consequences:**
- Correctness now depends on every mutating auth action remembering to bust the cache — a missed invalidation site is a stale-auth-state bug. Worth a checklist item in relevant later days (e.g. Day 30, Day 35, Day 49) to confirm each new session-mutating endpoint actually triggers invalidation.