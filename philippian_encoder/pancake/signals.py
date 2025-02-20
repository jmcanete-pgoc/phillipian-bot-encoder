# signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import Conversations, Page
from .tasks import *
from .utils import store_task_id, store_import_count, retrieve_import_count
from .middleware import get_current_user

@receiver(post_save, sender=Page)
def trigger_bot_encoder_fetcher(sender, instance, created, **kwargs):

    current_user = get_current_user()
    username = f"unkown_django_user_{instance.page_name}"  # Default username
    if current_user.is_authenticated:
        username = f"{current_user.username}_{instance.page_name}"

    print("USER:", username)
    count = retrieve_import_count(username)  # Retrieve import count
    if count and count == "1":
        store_import_count(username, 0)  # Store import count
    else:
        store_import_count(username, 1)

    print("COUNT:", count)

    if created and count:
        
        if count == "1":
            page = Page.objects.filter(page_name=instance.page_name).first()
            if page:
                task = run_task_fetcher.delay(page.access_token, page.page_name)
                task_id = task.id  # Get the task ID
                # Store task ID (e.g., in Redis, database, or a dedicated task registry)
                store_task_id(task_id, 'fetcher', page.page_name)

                task = run_task_tagger.delay(page.access_token, page.page_name)
                task_id = task.id  # Get the task ID
                # Store task ID (e.g., in Redis, database, or a dedicated task registry)
                store_task_id(task_id, 'tagger', page.page_name)

               

        
    