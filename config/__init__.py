# To ensure the Celery app automatically loads when Django starts up: 

from .celery import app as celery_app

__all__ = ('celery_app',)
