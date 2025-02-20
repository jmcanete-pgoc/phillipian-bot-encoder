from django.contrib import admin
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin
from .models import Conversations, Page, WorkerMonitor
from django.contrib import messages
from django.http import HttpResponseRedirect
from .resources import *

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
    list_display = ('worker_id', 'worker_name', 'worker_status', 'created_at', 'updated_at')
    search_fields = ('worker_id', 'worker_name', 'worker_status')

    def has_add_permission(self, request):
        return False #  disabled/hide (+) add button
    
    def has_change_permission(self, request, obj=None): 
        return False


admin.site.register(Conversations, ConversationsAdmin)
admin.site.register(Page, PageAdmin)
admin.site.register(WorkerMonitor, WorkerMonitorAdmin)