from celery import shared_task


@shared_task
def send_test_email():
    """
    Throwaway task to prove the Celery pipeline end to end.
    Not real signup/verification logic — that's Day 14.
    """
    print("Test email task executed successfully.")
    return "done"