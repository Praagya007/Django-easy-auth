## Reverse Threat Model — Understanding the OAuth Callback Flow

Instead of reading this as **attacker → threat → mitigation**, it can be understood in reverse by following how a legitimate OAuth login is supposed to work.

### 1. Goal

The objective is **not** to accept an OAuth callback.

The objective is to establish a legitimate authenticated session **only after** the application has independently verified that the identity provider (Google, GitHub, etc.) successfully authenticated the user.

---

### 2. Why the Callback Is Not Authentication

An OAuth callback endpoint is simply a public HTTP endpoint, for example:

```text
GET /auth/google/callback?code=abc123&state=xyz
```

Anyone on the Internet can send a request to this endpoint.

Receiving a callback request **does not prove** that:

* Google authenticated the user.
* The request belongs to an OAuth flow initiated by your application.
* The authorization code is valid.
* The authorization code belongs to your application.
* The callback has not been replayed or forged.

The callback is only the next step in the OAuth protocol—not proof of authentication.

---

### 3. What the Authorization Code Actually Means

The `code` parameter returned by the provider is **not** an authenticated session.

Instead, it is a temporary credential that tells your server:

> "Ask the identity provider whether this authorization request is legitimate."

The application must exchange this code with the OAuth provider over a secure server-to-server connection before trusting any identity information.

---

### 4. Why Each Validation Exists

#### Validate `state`

Before redirecting the user to the provider, the application generates a random `state` value and stores it locally.

When the provider redirects back, the returned `state` must exactly match the stored value.

This prevents attackers from:

* forging OAuth callbacks,
* performing CSRF attacks,
* injecting responses from unrelated authorization flows.

---

#### Exchange the Authorization Code Server-Side

The browser must never be trusted to validate authentication.

Instead, the backend exchanges the authorization code directly with the provider.

Only the provider can confirm that:

* the code is genuine,
* it has not expired,
* it belongs to your application,
* it has not already been redeemed.

---

#### Verify Token Claims

If an ID Token is returned, the server validates it before trusting any identity information.

Typical checks include:

* **Issuer (`iss`)** — confirms the token was issued by the expected identity provider.
* **Audience (`aud`)** — confirms the token was issued for your application's client ID.
* **Nonce (`nonce`)** (where applicable) — confirms the token belongs to the authentication request initiated by your application.
* **Expiration (`exp`)** — confirms the token is still valid.
* **Signature** — confirms the token has not been modified and was signed by the provider.

Without these checks, an attacker could attempt to present forged, altered, or misissued tokens.

---

### 5. Only Then Create a Session

Only after **all** validations succeed should the application establish its own authenticated session.

For example:

```text
User authenticated by Google
        ↓
Authorization code verified
        ↓
ID Token validated
        ↓
Local session created
```

The authenticated session is created because the server successfully verified the provider's response—not because the callback endpoint was visited.

---

### 6. The Security Principle

The OAuth callback endpoint is **not a login endpoint**.

It is a continuation of an authentication protocol whose responsibility is to receive the provider's response, validate every security property of that response, and **only then** establish a local authenticated session.

The application must never treat:

* an OAuth callback,
* an authorization code, or
* an ID/access token by itself

as equivalent to an authenticated user session.
