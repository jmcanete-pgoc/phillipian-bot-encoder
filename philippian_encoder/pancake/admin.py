from django.contrib import admin
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin
from .models import Conversations, Page, WorkerMonitor
from django.contrib import messages
from django.http import HttpResponseRedirect
from .resources import *
from django.utils.html import format_html
from django.urls import reverse
from django.shortcuts import get_object_or_404, redirect

# Register your models here.
class ConversationsAdmin(ExportActionModelAdmin):
    list_display = ('conversation_id', 'customer_id', 'customer_fb_id', 'customer_name', 'chats', 'address', 'tag', 'page_name', 'status', 'remarks', 'created_at', 'updated_at')
    search_fields = ('conversation_id', 'customer_id', 'customer_fb_id', 'customer_name', 'page_name', 'status')
    
    def has_add_permission(self, request):
        return False #  disabled/hide (+) add button
    
    def has_change_permission(self, request, obj=None): 
        return False
    

# Register your models here.
class PageAdmin(ImportExportModelAdmin):
    list_display = ('page_id', 'page_name', 'access_token', 'page_access_token', 'page_category', 'page_description', 'page_status', 'created_at', 'updated_at')
    search_fields = ('page_id', 'page_name', 'page_category', 'page_status')
    resource_classes = [PageAdminResource]
    
    def has_add_permission(self, request):
        return False #  disabled/hide (+) add button
    
    def has_change_permission(self, request, obj=None): 
        return False


class WorkerMonitorAdmin(admin.ModelAdmin):
    list_display = ('worker_id', 'worker_name', 'worker_status', 'created_at', 'updated_at', 'action_buttons')
    search_fields = ('worker_id', 'worker_name', 'worker_status')

   
    def action_buttons(self, obj):
        """Add 'View' and 'Stop' buttons to each row."""
        view_url = reverse('pancake:view_worker', args=[obj.id])  # URL for the new tab view
        # stop_url = reverse('admin:stop_worker', args=[obj.id])

        buttons = f'<a class="button" style="margin-right:5px; background: #007bff; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px;" target="_blank" href="{view_url}">View</a>'
        
        if obj.worker_status != "SUCCESS":  # Show "Stop" button only if not already stopped
            buttons += f' <a class="button" style="background: red; color: white; padding: 5px 10px; text-decoration: none; border-radius: 4px;" href="#">Stop</a>'
        else:
            buttons = ' <span style="color: gray;"><i class="fa fa-eye-slash"></i></span>'  # Eye icon for unviewed
            buttons += ' <span style="color: gray;">Stopped</span>'  # Show text instead of the button

        return format_html(buttons)

    action_buttons.short_description = "Actions"

    def has_add_permission(self, request):
        return False #  disabled/hide (+) add button
    
    def has_change_permission(self, request, obj=None): 
        return False


admin.site.register(Conversations, ConversationsAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(WorkerMonitor, WorkerMonitorAdmin)