# A list of edge cases:-
1) Session Middleware: 
- User sends a session id but the server does not recognize it.
- User does not send a session id at all but the server expects one.
- User sends a session id that has expired or is invalid.

2) Authentication Middleware:
- User sends invalid credentials (wrong username/password).
- User sends valid credentials but the account is locked or disabled.
- Timing attack vector (a user's credentials that exists returns in 200ms but a non-existent user returns in 100ms, allowing an attacker to guess valid usernames).
- A hacker attempts to brute-force login by sending multiple requests in a short period of time.

3) request.user:
- request.user not validated by the backend, trusting the client. 
- request.user is manipulated by the client to gain unauthorized access to resources.  
- request.user having a role that is not authorized to perform certain actions, but the backend does not check for this.
- request.user should not be fully deleted (always first make soft delete, then perform a hard delete after a certain period of time) to avoid data loss or accidental deletion.

4) From Authentication Cheat Sheet (OWASP):
- User IDs should be unique and non guessable (avoid sequential id like users/123 instead prefer uuids like this: users/2f4d8a1c-b26a-4c12-b94f-56de07b34e12)
- Django's user model uses a username by default, override that to use email and instead of username, prefer a full name field, looks better and is more user friendly.
- Suppose, you have internal admins, staffs, etc. of your web app. Do not let this be logged in via your frontend. Frontend is purely for users that use your web app.
- Suppose you internal admins, staffs, use the same credentials as they use in other websites, do not let them use the same credentials for your web app. Always enforce a different password for your web app. 
- Avoid shorter length of passwords, enforce 12-16 (minimum, recommended).
- Long passwords can cause a Passworrd DDoS, so avoid allowing users to set a password longer than 64 characters.
- Length matters more for password security btw. 
- Never truncate passwords, enforce this on your UI: max cap of 64 chars, show an error message, then, on your backend recheck this again. 
- Passwords should not have any sort of restrictions on special characters, allow all special characters, however, prevent common security pitfalls like XSS, SQL injection, etc. by preventing it being ran on your system.
- Encourage users to pick strong passwords and enable 2FA (Two Factor Authentication) for better security.
- Avoid users using their old passwords or passwords that are too similar to their previous ones. Implement a password history policy to prevent reuse of recent passwords. Have I been PWned API can be used to check if a password has been compromised in a data breach.
- When a user forgets their password, implement a secure password reset process like email confirmation, if a user enters the password that has been used before or from the have I been pwned API, show an error message and ask them to choose a different password. As soon as a password change occurs, destroy all existing sessions for that user to prevent unauthorized access with old sessions.
- Passwords should be stored using strong hashing algorithm (bcrypt, Argon2, or PBKDF2) with a unique salt for each password. Django does this automatically btw, argon2 is the best option as per OWASP, but bcrypt and PBKDF2 are also good options. 
- Compare passwords securely, they should run in same time, preventing timing attacks, they should have minimum and maximum characters, all enforced pre comparison, on the UI and on the backend both. Django's authenticate() method does this automatically btw.
- Use HTTPS always to protect sensitive data during transmission, including passwords and session tokens.
- Always return generic error messages for authentication failures to avoid giving attackers clues about valid usernames or passwords. For example, instead of saying "Invalid username" or "Invalid password," return a message like "Invalid credentials." For sign ups, if a user tries to sign up with an existing email, immediately fire a background job and return exactly this, "If this email is not registered, you will receive a confirmation email to complete the registration process." This prevents attackers from enumerating valid email addresses. Plus, to mitigate timing attacks: you can do this: either hash that password instantly, fire a background job and return that same response or detach that hashing process purely on a background job and return that same response. This way, the response time will be consistent regardless of whether the email is registered or not.
- MFA (Multi factor authentication) is a must for sensitive actions like changing passwords, updating email addresses, or performing financial transactions. Implement MFA using methods like SMS, email, or authenticator apps.
- Always throttle login attempts to prevent brute-force attacks. Implement rate limiting and account lockouts after a certain number of failed attempts.
- Silently lock an account out after a certain number of failed login attempts, and require the user to go through a secure account recovery process to regain access. This prevents attackers from knowing if an account is locked or not.
- Importantly: log every authentication attempt, including successful and failed logins, password changes, and account lockouts. This helps in detecting suspicious activity and potential security breaches.
- Use CAPTCHAs to prevent bots from attempting to brute-force login or registration forms. However, ensure that CAPTCHAs are accessible and do not hinder legitimate users. 
- When a user changes their email address, send a confirmation to the new email address and to the old email address both. This helps prevent unauthorized changes and alerts the user to any suspicious activity. When a user clicks, "This was not me" on the old email, immediately lock that account and require the user to go through a secure account recovery process to regain access. This prevents attackers from knowing if an account is locked or not.
- Whenever using authentication mechanisms like Google, Github, etc. it is important to know that them having access token does not mean they are authenticated. The difference here is that them having access token means the user is allowed to call the API of like Google, Github, etc. but actually being authenticated means the user is exactly who they say they are. So, always verify the access token with the provider's API to ensure its validity and authenticity. This prevents attackers from using stolen or forged tokens to gain unauthorized access. Do not trust a provider blindly, don't just directly merge credentials. 
Always, reverify, revalidate, and reauthenticate the user with the provider's API to ensure that the access token is still valid and has not been revoked. This adds an extra layer of security and helps prevent unauthorized access to your application.
- From a internal error POV, never ever leak full stack traces or sensitive information of errors from your backend to the frontend. Log a full stack trace for tracking errors on sites like Sentry, logging handled by Grafana Loki and return a generic response to the users like "Something went wrong, please try again later." This prevents attackers from gaining insights into your application's inner workings and potential vulnerabilities. Always sanitize error messages to avoid exposing sensitive information.

5) From session management cheat sheet (OWASP):
- Session IDs should be unique, random, and non-guessable. Avoid using predictable session IDs or sequential numbers.
- Session IDs should be invalidated after logout or after a certain period of inactivity. Implement session expiration and automatic logout to enhance security. 
- Use secure cookies (with the Secure and HttpOnly flags) to store session IDs. This prevents session hijacking and protects against cross-site scripting (XSS) attacks. However, CSRF cookies should not be HTTPOnly otherwise, JS couldn't read it and send it in the request header for CSRF protection.
- Implement session fixation protection by regenerating session IDs after successful login. This prevents attackers from using a fixed session ID to gain unauthorized access.
- Implement session timeout and automatic logout after a certain period of inactivity. This reduces the risk of unauthorized access if a user leaves their session unattended.
- Suppose a user is logged in on multiple devices, if they log out from one device, other devices should stay logged in. However, if a user does a nuclear (logout, which means bar the current device, log out from all devices) logout, all devices should be logged out. This prevents unauthorized access if a user forgets to log out from a shared or public device. 
- As soon as a password is changed (via forget password), you should immediately delete all the session IDs that are currently active for that user. This prevents unauthorized access with old sessions after a password change. But, when a user is logged in and he changes his password from a specific device, that device should not be logged out. This is because the user is already authenticated on that device and changing the password does not invalidate the current session. However, all other devices should be logged out to prevent unauthorized access with old sessions. This applies for email changes too.
- Session IDs should not be exposed in URLs or query parameters. Use secure methods like cookies or headers to transmit session IDs. This prevents session hijacking through URL sharing or logging.
- Session IDs should be stored securely on the server, like database or most popular one like Redis. 
- If a user clicks (remember me), that session should be validated for a longer period of time, but if the user does not click (remember me), that session should be validated for a shorter period of time. This prevents unauthorized access if a user forgets to log out from a shared or public device. Sessions should be based on a sliding expiration model, where the session expiration time is extended with each user activity. This ensures that active users are not logged out prematurely while still enforcing session expiration for inactive users.
- Sessions should be scoped in the cache per user. Avoid anyone being able to access another user's session data. This prevents unauthorized access to sensitive information and ensures that each user's session is isolated. 
- When a user deletes their account, all session IDs associated with that user should be invalidated and removed from the server. This prevents unauthorized access to the deleted user's account and ensures that their session data is no longer accessible.
- When a user deletes their browser history, the server does not recognize the session ID. Thus, now you re-login the user and generate a new session ID. 
- Sessions should be all 3: HttpOnly, Secure, and SameSite. This prevents session hijacking and protects against cross-site scripting (XSS) and cross-site request forgery (CSRF) attacks both at the same time. 

6) CSRF protection:
- CSRF tokens protects against CSRF attacks. The requests are made sure to be only made from that specific user and not from any other user. CSRF tokens should be unique, random, and non-guessable. Avoid using predictable tokens or sequential numbers. 
- CSRF tokens should be included in all state-changing requests (POST, PUT, DELETE) to ensure that the request is coming from the authenticated user. This prevents attackers from making unauthorized requests on behalf of the user.
- CSRF tokens should always be provided by your backend first to your frontend. Then, axios can read that toekn and send it to the backend. Using a decorator like @ensure_csrf_cookie in Django, you can ensure that the CSRF cookie is set for the user. Call this on the landing page.

OAuth edge cases:
- A user tries to login with an OAuth provider (like Google, GitHub, etc.) but the provider's API is down or unreachable. The application should handle this gracefully and inform the user of the issue.
- A user tries to login with an OAuth provider but he/she has already an account with the same email address in your application. The application should handle this case by either linking the accounts or prompting the user to log in with their existing credentials. Never link accounts automatically without the user's consent, as this can lead to unauthorized access and account takeover.
- A user tries to login with an OAuth provider but the provider's API returns an error or unexpected response. The application should handle this case gracefully and inform the user of the issue. Never show a blank page or crash the application, as this can lead to a poor user experience and potential security vulnerabilities.
- Suppose a user has done fully their operations via OAuth. Do you let them set a password for their account so that they can login with their email or do what ? 
- How do you handle OAuth rate limits per provider? 
- What if the user revokes access to your application from the OAuth provider's settings? The application should handle this case by logging the user out and informing them of the revocation, plus logging the entire event. 
- What if the user changes their email address on the OAuth provider's platform? The application should handle this edge case too.

C0RS preflight edge cases:
- A user tries to make a cross-origin request to your application but the server does not allow the origin.
- Any origin can make a preflight request to your server. Handle this via a whitelist of allowed origins. If the origin is not in the whitelist, return a 403 Forbidden response.
- Preflight handling for non simple requests (PUT, PATCH, DELETE) or with any non convential content type like not json or text/plain, etc. should be handled properly. Return the appropriate CORS headers in the response to allow the request to proceed.

Headless API (Django All Auth):
I have read it. Pretty useful information, it supports mobile and web apps now. The previous versions didn't do.

The answering of the questions for today are as follows:-
1) Session Fixation:
- Attacker creates a valid session ID.
- He/she sends that session ID to the victim via a link or email.
- The victim clicks the link and logs in, unknowingly using the attacker's session ID.
- The attacker can now hijack the victim's session and gain unauthorized access to their account.

The fix:
Always make sure to regenerate the session ID after a successful login. This ensures that any previously issued session IDs are invalidated and cannot be used by an attacker. In Django, this can be done using the `django.contrib.sessions.middleware.SessionMiddleware` and calling `request.session.cycle_key()` after a successful login.

Plus, sessions can never be stored on URLs or query params. Always store sessions like this: HTTPONly, samesite secure all true. 

2) Session Hijacking: 
- A victim is already logged in to a web application.
- An attacker intercepts the victim's session ID through various means (e.g., network sniffing, XSS attacks, etc.).
- The attacker uses the stolen session ID to impersonate the victim and gain unauthorized access to their account.

The fix:
Always encrypt the session ID via HTTPs to prevent network sniffing and MITM.
Always store session IDs purely on HTTPOnly cookies, preventing JS to read them. 
From a user POV, avoid using a public WiFi where the network is portrayed like: connected/not secure, etc. This is a common way for attackers to intercept session IDs.

# The user has access token does not mean he is authenticated:

A user having a Google access token means he is authorized to call Google APIs, but it does not mean he is authenticated in your application. The access token only proves that the user has granted permission to your application to access their Google account data. This is where OIDC comes into picture, which is an identity layer on top of OAuth 2.0. OIDC provides a standardized way to authenticate users and obtain their identity information, such as their name and email address.

7) Headless API (Django All Auth), edge cases:
1) Can the headless API allow you to override the default fields and add custom fields to the user model? As per allauth/headless/adapter. 
2) The headless API needs new CORS headers too, point to be noted. Not exactly in an edge case sense but something to keep in mind.
3) From the headless API section, routing: This is more a CORS based edge case. Since, the backend and the frontend are hosted on one root domain but different subdomains, you need to set these flags: 
- SESSION_COOKIE_DOMAIN = "example.com" (for all subdomains)
- CSRF_COOKIE_DOMAIN = "example.com" (for all subdomains)
- CORS_ALLOWED_ORIGINS = ["https://subdomain1.example.com", "https://subdomain2.example.com"] 
and lastly
CSRF_TRUSTED_ORIGINS = ["https://subdomain1.example.com", "https://subdomain2.example.com"] (for all subdomains) (for all subdomains, for PUT/PATCH/POST and DELETE requests)

4) The headless API returns data in this exact format:-
status to match the HTTP code, data if anything is part of data key, metadata if anything is part of metadata key, and errors if anything is part of errors key. This does follow consistency on API responses. But, do we even need all of this ? Why and why not ? 
5) allauth.headless does need sanitizing input as per the official docs. 
6) You should cache the headless API's config endpoint because it barely changes. Supported OAuth providers, MFA enabled or not, etc. This is a good point to note. And the read to write ratio is too overwhelming here, its somewhere close to 999:1 out of 1000 because for project scope we are not changing the auth providers only google and github are used. So, caching this endpoint is a good idea.
7) All auth/session endpoint is equivalent to api/auth/me endpoint. I feel like this might need two separate api endpoint. Let api/auth/me endpoint be the core source of truth for the user data (cached, invalidated via a write through) and api/auth/sessions endpoint be the list of endpoints, api/auth/sessions/<id> be the detail of a specific session. This is a good point to note.
8) We might also need a nuclear logout endpoint, which logs out the user from all devices. This is a good point to note. All auth by default does have a log out endpoint, but from current session. 
9) Headless API relies on username and password. But, my choice would be email, full name and password, this is one point to configure.
10) On the sign up endpoint, Django all auth headless said enter a valid email address. Does this mean that email address is already on the DB and this is being returned? If yes, then this is a huge security flaw, always return a generic resposne. "If this email is not registered, you will receive a confirmation email to complete the registration process." This prevents attackers from enumerating valid email addresses. When a structurally valid but already-existing email is submitted, django-allauth returns a 400 Bad Request with the message: "A user is already registered with this email address." Ahh nice. This guy right here, you need to pair this actually with Set ACCOUNT_PREVENT_ENUMERATION = True.

Pair it with ACCOUNT_EMAIL_VERIFICATION = "mandatory" to achieve seamless generic responses on signup without breaking your database schema. However, all auth on sign up based endpoints, esp. on passwords does not actually prevent any sort of timing attacks. You can do something like this: hash the password instantly (which will take some time), fire off a background job and return that same response immediately. This prevents timing based attacks. Or, detach that hashing process purely on a background job and return that same response immediately. This way, the response time will be consistent regardless of whether the email is registered or not.

11) I personally feel a lot of headless API's fields can be simplified. 
