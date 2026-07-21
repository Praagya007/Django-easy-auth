# Understanding Email Verification & Password Reset Confirmation (Reverse Walkthrough)

Instead of reading this as **attacker → threat → mitigation**, it can be understood in reverse by following how a legitimate email verification or password reset is supposed to work.

### 1. Goal

The objective is **not** to accept a verification or password reset token.

The objective is to perform a sensitive account action **only after** the application has verified that the requester possesses a valid, unexpired, single-use token that was issued specifically for that account and purpose.

---

### 2. Why the Confirmation Endpoint Is Not Authorization

Email verification and password reset confirmation endpoints are simply public HTTP endpoints, for example:

```text
GET /api/auth/verify-email/<token>

GET /api/auth/reset-confirm/<token>
```

Anyone on the Internet can send requests to these endpoints.

Receiving a request **does not prove** that:

* The requester owns the email address.
* The token was legitimately issued by your application.
* The token belongs to the account being modified.
* The token has not expired.
* The token has not already been used.
* The token has not been guessed or replayed.

The confirmation endpoint is only the next step in the account verification or recovery process—not proof that the requested action should be performed.

---

### 3. What the Token Actually Means

A verification or password reset token is **not** an authenticated session.

Instead, it is a temporary, cryptographically secure secret that tells your server:

> "Verify that this token is genuine, still valid, unused, and belongs to the intended account before performing any sensitive action."

Possession of the token demonstrates possession of the email that received it—but only after the server has successfully validated every property of that token.

---

### 4. Why Each Validation Exists

#### High-Entropy Tokens

Verification and reset tokens should be generated using a cryptographically secure random number generator.

This makes them computationally infeasible to guess through brute force.

---

#### Short Expiration

Tokens should expire after a short period of time.

This limits the window during which an intercepted or leaked token can be abused.

---

#### Single Use

Once a token has been successfully used, it should immediately become invalid.

This prevents replay attacks where an attacker attempts to reuse an old verification or reset link.

---

#### Immediate Invalidation on Replacement

If a user requests another verification or reset email, any previously issued token should immediately become invalid.

Only the most recently generated token should remain usable.

---

#### Generic Responses

The application should return the same response regardless of whether:

* the token is valid,
* the token is invalid,
* the token has expired, or
* the token has already been used.

This prevents attackers from learning anything useful by comparing application responses.

---

#### Rate Limiting

The confirmation endpoints themselves should be rate limited.

This helps prevent attackers from repeatedly attempting to guess valid tokens or abusing the endpoint with automated requests.

---

### 5. Only Then Perform the Sensitive Action

Only after **all** validations succeed should the application perform the requested operation.

For example:

```text
Verification/reset request
        ↓
Token located
        ↓
Token validated
        ↓
Token unused
        ↓
Token unexpired
        ↓
Sensitive action performed
```

For email verification:

* Mark the email address as verified.

For password reset:

* Allow the password to be changed.
* Invalidate the reset token.
* Invalidate existing user sessions.

The sensitive action is performed because the server successfully validated the token—not because the confirmation endpoint was visited.

---

### 6. The Security Principle

Email verification and password reset confirmation endpoints are **not authorization endpoints**.

They are continuations of an account verification or recovery protocol whose responsibility is to validate a temporary secret before allowing any sensitive account state change.

The application must never treat:

* a confirmation endpoint request,
* a verification token, or
* a password reset token by itself

as sufficient authorization to modify an account.

Only after the server verifies that the token is genuine, unexpired, single-use, and issued for the intended account should the requested action be performed.
