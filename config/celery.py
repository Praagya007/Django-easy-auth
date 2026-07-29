import os
from .celery import Celery

# Point Celery at whichever settings module is active — same pattern
# as manage.py/wsgi.py/asgi.py, so dev/prod split is respected here too.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings.dev")

# Initialize Celery app using the name of your project config folder.
app = Celery("config")

# Load configuration from Django settings, using the namespace 'CELERY' so all celery-related configuration keys should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Auto-discover tasks in all installed apps, so you don't have to manually list them.
app.autodiscover_tasks()