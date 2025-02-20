from import_export import resources, fields
from .models import Conversations, Page


class PageAdminResource(resources.ModelResource):
    class Meta:
        model = Page
        import_id_fields = ('page_name',)
        fields = ('page_name', 'access_token', 'is_import_confirmed')
    
    # def before_save_instance(self, instance, row, user, **kwargs):
    #     if not instance.is_import_confirmed:
    #         instance.is_import_confirmed = True


    def after_import(self, dataset, result, using_transactions, dry_run, **kwargs):
        """
        This runs after all rows have been imported.
        It ensures `is_import_confirmed` is set to True after confirmation.
        """
        
        if not dry_run:  # Prevent updates in preview mode
            Page.objects.filter(is_import_confirmed=False).update(is_import_confirmed=True)
            
        


    