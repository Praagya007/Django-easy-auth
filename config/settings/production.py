from base import *

DEBUG = False  # Always set to False in production

CSRF_COOKIE_SECURE = True  # Ensures CSRF cookie is only sent over HTTPS
SESSION_COOKIE_SECURE = True  # Ensures session cookie is only sent over HTTPS

CSRF_COOKIE_HTTPONLY = False  # Never set to True, JS won't be able to read and send the CSRF token
SESSION_COOKIE_HTTPONLY = True  # Prevents JS from reading the session cookie, this always to False

SESSION_COOKIE_SAMESITE = "Lax"  # Prevents the browser from sending this cookie along with cross-site requests. Can be set to 'Strict', 'Lax', or 'None'
CSRF_COOKIE_SAMESITE = "Lax"  # Prevents the browser from sending this cookie along with cross-site requests. Can be set to 'Strict', 'Lax', or 'None'

CSRF_ALLOWED_ORIGINS = [
    "https://yourdomain.com",  # Replace with your actual domain
]

ALLOWED_HOSTS = ["yourdomain.com"]  # Replace with your actual domain
