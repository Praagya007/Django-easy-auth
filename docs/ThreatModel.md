# Threat Model v0.1

## 1. Anonymous Internet User — Public Endpoints

**Attacker:** Anonymous internet user

**Asset:** Server CPU/memory, private data of other users

**Entry point:** `api/auth/login`, `api/auth/register`, OAuth endpoints, `api/auth/reset-password`, `api/auth/csrf`

**Threat:**
- Brute force on login and signup
- SMTP abuse/burn via password reset and signup (repeated resend)
- DoS via Gunicorn worker exhaustion from oversized passwords requiring hashing
- Timing attacks on login, signup, and password reset
- User enumeration on login, signup, and password reset
- Repeated CSRF token fetching
- General bot-driven exploitation of the above

**Mitigation:**
1. **Login:** Run a dummy hash against a dummy DB value on every attempt. Always return "Invalid credentials" regardless of whether the account exists. After several failed attempts, don't lock the account — silently email the user: *"Something is trying to log in to your account. If this wasn't you, please reset your password immediately."*
2. **Signup:** Rate limit by IP/device ID. Validate fields, run a dummy hash, fire the verification email as a background task, and return a generic response — *"If this email is not registered, you will receive an email with instructions to verify your account"* — on every attempt, registered or not.
3. **Password hashing:** Argon2id. Max 64 characters (prevents password-DoS), min 12 characters (OWASP-recommended). Hashing is constant-time by construction.
4. **Password reset:** Rate limit by IP/device ID. Fire the reset email as a background task, return a generic response — *"If this email exists in our system, you will receive an email with instructions to reset your password"* — on every attempt, registered or not.
5. **CSRF endpoint:** Rate limit with a generous quota for legitimate users. Frontend should not re-fetch a token if one already exists.
6. **OAuth email collision:** Do not auto-link accounts. Send the same generic response: *"We will send a verification email to the email address associated with your OAuth provider account."* Note: allauth headless may already handle much of this — verify, don't assume.
7. **SMTP abuse prevention:** Pause resend if a token was already sent recently. Applies especially to signup/reset resend abuse. Should be rate limited, generously, for legit users.
8. **Perimeter:** WAF in front of API endpoints (SQLi, XSS, etc.); Cloudflare Turnstile to block bot traffic. *(Decided in-scope for v1 — see note below.)*
9. **2FA:** If enabled, never grant full access without the 6-digit code, even with a correct password.
10. **Password reset success:** Kill every session immediately.
11. **Admin/staff:** No internal/staff login via the public login endpoint — use Django admin or a separate auth path.

---

## 2. Authenticated Users / Attackers with a Session — Authenticated Endpoints

**Attacker:** Authenticated user (legitimate or attacker with a valid session)

**Asset:** Other users' private data

**Entry point:** `api/auth/me`, `api/auth/change-password`, `api/auth/change-email`, `api/auth/logout`, `api/auth/2fa-setup`, `api/auth/2fa-verify`, `api/auth/2fa-recovery-codes`, `api/auth/sessions`

**Threat:**
- IDOR — a user (legit or attacker) accessing another user's private data
- Acting on another user's behalf: logging out their sessions, disabling their 2FA, changing their email/password
- Brute-forcing 2FA codes or recovery codes
- Brute-forcing change-password / change-email endpoints
- Session hijacking leading to viewing/revoking another user's sessions

**Mitigation:**
- All endpoints require authentication.
- Querysets scoped to the current user (`request.user`) at all times.
- Return 404, not 403, for resources the user has no business accessing (403 confirms existence).
- Rate limit all of the above — legitimate clients can also misbehave (buggy client case).
- **2FA / recovery codes:** Limit attempts; lock and notify via email after repeated failures.
- **Email changes:** Notify both old and new email. If the old-email holder reports "this wasn't me," lock the account immediately, notify via email, and route to support for identity verification (standard account-takeover signal).
- **Password changes:** Disallow reuse of the last 10 passwords (credential-stuffing mitigation).
- **Password reset / email change success:** Bust all sessions except the current one.
- **Session security:** `HttpOnly`, `SameSite`, `Secure` cookies only. New session ID generated on every login (fixation prevention); session busted (not rotated) on logout.

---

## 3. Anonymous Internet User — OAuth Callback Endpoints

**Attacker:** Anonymous internet user

**Asset:** User accounts and authenticated sessions

**Entry point:** OAuth callback endpoints (e.g. Google/GitHub callback after provider redirect)

**Threat:** Forging or replaying an OAuth callback, or manipulating the redirect flow, to trick the application into establishing a session without legitimate provider authentication. The application must not treat an incoming callback alone as proof of authentication.

**Mitigation:** Validate the `state` parameter on every authorization flow (CSRF/forgery protection). Perform the authorization code exchange and ID/access token validation server-side — verify issuer, audience, nonce (where applicable), and token signatures. Only establish a local session after successful server-side verification. Never treat a callback, authorization code, or token alone as equivalent to an authenticated session.

**See More:** [OAuth Flow Explained](o-auth-flow-explained.md) for a detailed breakdown of the OAuth flow and security considerations.
---

## 4. Anonymous Internet User — Email Verification & Password Reset Confirmation

**Attacker:** Anonymous internet user

**Asset:** User accounts and the account-recovery process

**Entry point:** `api/auth/verify-email/<token>`, `api/auth/reset-confirm/<token>`

**Threat:** Guessing, brute-forcing, or replaying verification/reset tokens to verify another user's account or complete an unauthorized password reset.

**Mitigation:** Cryptographically secure, high-entropy, single-use tokens with short expiry. Invalidate immediately on use or replacement. Rate limit the *confirmation* endpoints themselves, not just the endpoints that generate the emails. Return generic responses so token validity can't be inferred from response differences.

**See More:** [Email Verification & Password Reset Explained](email-verification-and-password-reset-explained.md) for a detailed breakdown of the email verification and password reset flow and security considerations.

<!-- To maximize throughput on password hashing, alter the Argon2id parameters to be more efficient. To balance security and throughput, use these parameters: time_cost = 2 (2 iterations), memory cost= 16384 (16MiB) and parallelism 1. This is a good balance between security and throughput. Obviously more iterations and more memory cost would be more secure, but it also slows down throughput and Python's GIL is a bottleneck. 

This note is not exactly a mitigation of attack, but of throughput issue that CPU bound tasks tend to have Not included here. I have only attached this here as it goes along with the number 3.  -->