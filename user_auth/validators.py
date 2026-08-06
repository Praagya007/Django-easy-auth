import os
from django.conf import settings

import logging

logger = logging.getLogger(__name__)

FILE_PATH = os.path.join(settings.BASE_DIR, 'assets', 'disposable_email_domains_blocklist.txt')
DISPOSABLE_EMAIL_DOMAINS = set()




try:
    with open(FILE_PATH, 'r', encoding='utf-8') as f:
        DISPOSABLE_EMAIL_DOMAINS = {line.strip().lower() for line in f if line.strip()}
        
    # We will log this as a serious issue in production.
except FileNotFoundError:
    logger.error(
        "Disposable email blocklist not found at %s — signup will accept "
        "disposable-domain emails until this is fixed.",
        FILE_PATH,
    )
    DISPOSABLE_EMAIL_DOMAINS = set()
