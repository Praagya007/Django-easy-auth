from celery import shared_task

@shared_task
def process_initial_registration(data): 
    return "hello world" 