from django.apps import AppConfig


class TrakfitAppConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'trakfit_app'
    
    def ready(self):
        """Import signals when the app is ready."""
        import trakfit_app.signals
