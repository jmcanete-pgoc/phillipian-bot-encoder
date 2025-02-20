# my_django_app/tasks.py (Celery tasks)
from celery import shared_task
import time
import logging
from .module import Fetcher, Tagger
from celery.exceptions import SoftTimeLimitExceeded  # For time limits
from .utils import set_cancel_flag, delete_cancel_flag
from .models import WorkerMonitor
import requests
import os
from django.db import transaction  # For atomic operations
from django.utils import timezone  # Import timezone

logger = logging.getLogger(__name__)  # Get a logger instance


@shared_task(bind=True, soft_time_limit=3600, time_limit=3660)  # Add time limits
def run_task_fetcher(self, access_token, page_name):  # Add 'self'
    task_id = self.request.id  # Get the task ID
    r = set_cancel_flag(task_id, "False")  # Set the initial cancel flag to False

    fetcher = Fetcher(access_token, page_name, task_id)  # Create fetcher instance; Pass Redis connection to Fetcher

    try:
        self.update_state(state='STARTED', meta={'message': 'Fetcher is running'})  # Update task state
        fetcher.run()  # Or fetcher.run_forever() if that's your method name
        self.update_state(state='SUCCESS', meta={'message': 'Fetcher is finished.'})  # Update task state
    except SoftTimeLimitExceeded:  # Handle soft time limit
        logger.warning(f"Task run_task_fetcher timed out (soft limit). Revoking...")
        r = set_cancel_flag(task_id, "False")  # Set the initial cancel flag to False
        self.update_state(state='REVOKED', meta={'message': 'Soft time limit exceeded'})  # Update task state
        return  # Or raise an exception if you want to ensure it stops
    except Exception as e:
        logger.error(f"Task run_task_fetcher error: {e}")
        self.update_state(state='FAILURE', meta={'message': 'Exception '})  # Update task state
        # Handle exceptions appropriately (e.g., retry, log, etc.)
        raise  # Re-raise the exception to indicate failure
    finally:
        # Any cleanup code (e.g., closing connections, releasing resources)
        fetcher.cleanup() # Example cleanup method
        delete_cancel_flag(task_id)  # Delete the cancel flag after the task is done
        logger.info("Task run_task_fetcher finished (or revoked).")
        

    return  # Or return a result if needed




@shared_task(bind=True, soft_time_limit=3600, time_limit=3660)  # Add time limits
def run_task_tagger(self, access_token, page_name):  # Add 'self'
    task_id = self.request.id  # Get the task ID
    r = set_cancel_flag(task_id, "False")  # Set the initial cancel flag to False

    tagger = Tagger(access_token, page_name, task_id)  # Create fetcher instance; Pass Redis connection to Fetcher

    try:
        self.update_state(state='STARTED', meta={'message': 'Tagger is running'})  # Update task state
        tagger.run()  # Or tagger.run_forever() if that's your method name
        self.update_state(state='SUCCESS', meta={'message': 'Tagger is finished.'})  # Update task state

    except SoftTimeLimitExceeded:  # Handle soft time limit
        logger.warning(f"Task run_task_tagger timed out (soft limit). Revoking...")
        r = set_cancel_flag(task_id, "False")  # Set the initial cancel flag to False
        self.update_state(state='REVOKED', meta={'message': 'Soft time limit exceeded'})  # Update task state
        return  # Or raise an exception if you want to ensure it stops
    
    except Exception as e:
        logger.error(f"Task run_task_tagger error: {e}")
        self.update_state(state='FAILURE', meta={'message': 'Exception '})  # Update task state
        # Handle exceptions appropriately (e.g., retry, log, etc.)
        raise  # Re-raise the exception to indicate failure
    finally:
        # Any cleanup code (e.g., closing connections, releasing resources)
        tagger.cleanup() # Example cleanup method
        delete_cancel_flag(task_id)  # Delete the cancel flag after the task is done
        logger.info("Task run_task_tagger finished (or revoked).")
        

    return  # Or return a result if needed





@shared_task(bind=True, soft_time_limit=3600, time_limit=3660, retries=3, retry_backoff=True)  # Add retries
def monitor_task_tagger(self):  
    task_id = self.request.id  # Get the task ID
    try:
       
        # Make the HTTP request HERE:
        url = f"http://django:8000/pancake/celery/task/all"  # Or your URL
        response = requests.get(url, timeout=10) # Timeout added

        response.raise_for_status()  # Check for bad status codes (4xx or 5xx)
        response_data = response.json()  # Or response.text if not JSON
        logger.info(f"Task {task_id}: HTTP request successful. Status code: {response.status_code}")
        logger.debug(f"Task {task_id}: Response: {response_data}")

        # ... process the response data ...
        result = {"message": "Task completed", "data": response_data} # Example

        
        if response.status_code == 200:
            
            self.update_state(state='SUCCESS', meta=result)  # Update task state
            
            # print(f"Task {task_id}: Response: {response_data}")
            if len(response_data.get("tasks",[])) == 0:
                WorkerMonitor.objects.all().delete()
                logger.info(f"Task {task_id}: Deleted all WorkerMonitor records.")
                
            for task in response_data.get("tasks",[]):
                
                if task['type'] == 'tagger':
                    task_id = task['task_id']
                    type = task['type']
                    page = task['page']
                    status = task['status']
                    
                    if all([task_id, type, page, status]): # Check if all values are present
                        
                        with transaction.atomic():  # Ensure atomicity
                            worker_monitor, created = WorkerMonitor.objects.update_or_create(
                                worker_id=task_id,  # Use worker_id as the unique identifier
                                defaults={
                                    'worker_name': page,
                                    'worker_status': status,
                                    'worker_type': type,
                                    'updated_at': timezone.now() # Update the timestamp
                                }
                            )
                            if created:
                                logger.info(f"Task {task_id}: Created WorkerMonitor record for task {task_id}")
                            else:
                                logger.info(f"Task {task_id}: Updated WorkerMonitor record for task {task_id}")
                    else:
                        logger.warning(f"Task {task_id}: Incomplete data received for a tagger task: {task}")
                else:
                    logger.debug(f"Task {task_id}: Not a tagger task: {task.get('task_type')}") # Log non tagger tasks.

        return result

    except requests.exceptions.RequestException as e:
        error_message = f"Task {task_id}: HTTP request failed: {e}"
        logger.error(error_message)
        self.retry(exc=e)  # Retry the task
    except Exception as e: # Catch other exceptions
        error_message = f"Task {task_id}: An error occurred: {e}"
        logger.error(error_message)
        self.update_state(state='FAILURE', meta={'message': error_message})
        # raise # Only reraise if you want the task to fail completely
    finally:
        logger.info(f"Task {task_id}: Finished.")

    return  # Or return a result if needed




