from django.urls import path
from . import views

app_name = "pancake"  # Add this line to fix the namespace issue

urlpatterns = [
    path('celery/task/start/fetcher', views.start_task_fetcher, name='start_task_fetcher'),
    path('celery/task/start/tagger', views.start_task_tagger, name='start_task_tagger'),
    path('celery/task/stop/', views.stop_specific_task, name='stop_specific_task'),
    path('celery/task/status/', views.task_status, name='task_status'), # For checking status
    path('redis/task/view/', views.view_redis_tasks, name='redis_tasks'),
    path('celery/task/all/', views.get_all_task_status, name='get_all_task_status'),
    path('celery/task/fetcher/revoke/', views.revoke_task_fetcher, name='revoke_task_fetcher'),
    path('view_worker/<int:object_id>/', views.view_worker, name="view_worker"),
]