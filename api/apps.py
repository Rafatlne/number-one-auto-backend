from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    
    def ready(self):
        import api.signals
        # Remove background task initialization from here
        # It will be called from entrypoint.sh after migrations
