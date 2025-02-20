from django.apps import AppConfig


class PancakeConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'pancake'

    def ready(self):
        import pancake.signals
