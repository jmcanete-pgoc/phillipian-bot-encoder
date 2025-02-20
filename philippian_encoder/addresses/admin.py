from django.contrib import admin
from import_export.admin import ExportActionModelAdmin, ImportExportModelAdmin
from .models import AreaInfo, PhilippineAddress

# Register your models here.
class AreaInfoAdmin(ExportActionModelAdmin):
    list_display = ('id', 'province', 'city', 'barangay', 'commune_id', 'district_id', 'province_id')
    search_fields = ('province', 'city', 'barangay', 'commune_id', 'district_id', 'province_id')
    
    def has_add_permission(self, request):
        return False #  disabled/hide (+) add button
    
    def has_change_permission(self, request, obj=None): 
        return False


class PhilippineAddressAdmin(ExportActionModelAdmin):
    list_display = ('id', 'region','province', 'municipality_city', 'barangay','postal', 'latitude', 'longitude')
    search_fields = ('province', 'municipality_city', 'barangay', 'region')
    
    def has_add_permission(self, request):
        return False #  disabled/hide (+) add button
    
    def has_change_permission(self, request, obj=None): 
        return False


admin.site.register(AreaInfo, AreaInfoAdmin)
admin.site.register(PhilippineAddress, PhilippineAddressAdmin)