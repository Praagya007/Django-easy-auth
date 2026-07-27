from .base import *  # noqa: F401,F403

# Local dev never needs HTTPS-only cookies — explicit here, not just inherited from base
SESSION_COOKIE_SECURE = False