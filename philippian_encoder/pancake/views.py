from django.shortcuts import render
from .tasks import *
from django.http import HttpResponse, JsonResponse
from django.urls import reverse
from celery.result import AsyncResult
from .utils import store_task_id, get_all_stored_task_ids, get_task_details, set_cancel_flag
# Create your views here.



def start_task_fetcher(request):
    access_token = request.GET.get('access_token')
    page_name = request.GET.get('page_name')

    if not access_token or not page_name:
        return HttpResponse("Missing access_token or page_name parameters.")
    
    task = run_task_fetcher.delay(access_token, page_name)  # Start the task
    task_id = task.id  # Get the task ID

    # Store task ID (e.g., in Redis, database, or a dedicated task registry)
    # ... (Implementation depends on your chosen storage mechanism)
    store_task_id(task_id, 'fetcher')

    return JsonResponse({'task_id': task_id, 'task_type': 'fetcher'})  # Return JSON response with task ID


def start_task_tagger(request):
    access_token = request.GET.get('access_token')
    page_name = request.GET.get('page_name')

    if not access_token or not page_name:
        return HttpResponse("Missing access_token or page_name parameters.")
    
    task = run_task_tagger.delay(access_token, page_name)  # Start the task
    task_id = task.id  # Get the task ID

    # Store task ID (e.g., in Redis, database, or a dedicated task registry)
    # ... (Implementation depends on your chosen storage mechanism)
    store_task_id(task_id, 'tagger')

    return JsonResponse({'task_id': task_id, 'task_type': 'tagger'})  # Return JSON response with task ID



def stop_specific_task(request):
    task_id = request.GET.get('task_id')

    if not task_id:
        # return HttpResponse("No task ID provided.")
        return JsonResponse({'task_id': task_id, 'message': 'No task ID provided.'})

    task = AsyncResult(task_id)

    if task.status != 'REVOKED':
        task.revoke(terminate=True)  # Force termination if needed
        # return HttpResponse(f"Task {task_id} revoked.")
        return JsonResponse({'task_id': task_id, 'message': f'Task ID ({task_id}) revoked.'})
    else:
        # return HttpResponse(f"Task {task_id} is already revoked.")
        return JsonResponse({'task_id': task_id, 'message': f'Task ID ({task_id}) is already revoked.'})



def get_all_task_status(request):
    task_ids = get_all_stored_task_ids()  # Assuming this function gets task IDs

    data = []

    for task_id_bytes in task_ids:
        task_id_str = task_id_bytes.decode('utf-8')
        task = AsyncResult(task_id_str)
        details = get_task_details(task_id_str)  # Your function for other details

        try:
            details['status'] = task.status
        except Exception as e:  # Catch potential errors during status retrieval
            details['status'] = f"Error getting status: {str(e)}"  # Or a default status
            # Log the error for debugging.
            import logging
            logger = logging.getLogger(__name__)  # Or get your logger
            logger.error(f"Error getting task status for {task_id_str}: {e}")

        try:
            if task.status == 'SUCCESS': # Check if the task is successful
                details['result'] = task.result # Get the result if successful
            elif task.status == 'FAILURE': # Check if the task failed
                details['result'] = str(task.info) # Get the exception info
            else: # If the task is PENDING or STARTED
                details['result'] = None # Set result to None
        except Exception as e:  # Handle issues with result/info access
            details['result'] = f"Error getting result/info: {str(e)}"
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Error getting task result/info for {task_id_str}: {e}")

        data.append(details)

    return JsonResponse({'tasks': data})




def task_status(request):
    task_id = request.session.get('task_id')
    if task_id:
        task = AsyncResult(task_id)
        return HttpResponse(f"Task status: {task.status}")
    else:
        return HttpResponse("No task ID found in session.")
    


def view_redis_tasks(request):
    task_ids = get_all_stored_task_ids()
    tasks = []

    for task_id in task_ids:
        task_details = get_task_details(task_id)
        tasks.append(task_details)

    return render(request, 'pancake/redis_tasks.html', {'tasks': tasks})



def revoke_task_fetcher(request):
    task_id = request.GET.get('task_id')
    if task_id:
        set_cancel_flag(task_id, "True")
        return JsonResponse({"message": f"Cancellation signal sent to task {task_id}"})
    return JsonResponse({"message": f"Failed sending cancellation signal to task {task_id}"})
