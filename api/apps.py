from django.apps import AppConfig


class ApiConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "api"
    
    def ready(self):
        import api.signals
        from tasks.fetch_news_task import fetch_news_task
        fetch_news_task(repeat=600)
