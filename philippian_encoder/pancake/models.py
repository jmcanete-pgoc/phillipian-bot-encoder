from django.db import models
from django.utils import timezone  # Import timezone
# Create your models here.

class Conversations(models.Model):
    conversation_id = models.CharField(max_length=255, blank=True, null=True)
    customer_id = models.CharField(max_length=255, blank=True, null=True)
    customer_fb_id = models.CharField(max_length=255, blank=True, null=True)
    customer_name = models.CharField(max_length=255, blank=True, null=True)
    chats = models.TextField(blank=True, null=True)  # Use TextField for long text
    address = models.TextField(blank=True, null=True)
    tag = models.CharField(max_length=255, blank=True, null=True)
    page_name = models.CharField(max_length=255, blank=True, null=True)
    status = models.CharField(max_length=1, blank=True, null=True)  # CharField for single character
    remarks = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)  # System generated on creation
    updated_at = models.DateTimeField(default=timezone.now)      # System generated on every update

    class Meta:
        # Add indexes for frequently queried fields
        indexes = [
            models.Index(fields=['conversation_id'], name='conv_conversation_id_idx'),
            models.Index(fields=['customer_id'], name='conv_customer_id_idx'),
            models.Index(fields=['customer_fb_id'], name='conv_customer_fb_id_idx'),
            models.Index(fields=['customer_name'], name='conv_customer_name_idx'),
            models.Index(fields=['page_name'], name='conv_page_name_idx'),
            models.Index(fields=['status'], name='conv_status_idx'),  # If frequently queried
            # ... add more indexes as needed
        ]

    def __str__(self):
        return f"Conversation ID: {self.conversation_id}"  # Customize as needed
    


class Page(models.Model):
    page_id = models.CharField(max_length=255, blank=True, null=True)
    page_name = models.CharField(max_length=255, blank=True, null=True)
    access_token = models.TextField(blank=True, null=True)
    page_access_token = models.TextField(blank=True, null=True)
    page_category = models.CharField(max_length=255, blank=True, null=True)
    page_description = models.TextField(blank=True, null=True)
    page_status = models.CharField(max_length=1, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)  # System generated on creation
    updated_at = models.DateTimeField(default=timezone.now)      # System generated on every update
    is_import_confirmed = models.BooleanField(default=False)  # Added field

    class Meta:
        indexes = [
            models.Index(fields=['page_id'], name='page_page_id_idx'),
            models.Index(fields=['page_name'], name='page_page_name_idx'),
            models.Index(fields=['page_category'], name='page_page_category_idx'),
            models.Index(fields=['page_status'], name='page_status_idx'),
            # ... add more indexes as needed
        ]

    def __str__(self):
        return f"Page ID: {self.page_id}"  # Customize as needed
    


class WorkerMonitor(models.Model):
    worker_id = models.CharField(max_length=255, blank=True, null=True)
    worker_name = models.CharField(max_length=255, blank=True, null=True)
    worker_status = models.CharField(max_length=255, blank=True, null=True)
    worker_type = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(default=timezone.now)  # System generated on creation
    updated_at = models.DateTimeField(default=timezone.now)      # System generated on every update

    class Meta:
        indexes = [
            models.Index(fields=['worker_id'], name='worker_worker_id_idx'),
            models.Index(fields=['worker_name'], name='worker_worker_name_idx'),
            models.Index(fields=['worker_status'], name='worker_status_idx'),
            models.Index(fields=['worker_type'], name='worker_type_idx'),
            # ... add more indexes as needed
        ]

    def __str__(self):
        return f"Worker ID: {self.worker_id}"  # Customize as needed