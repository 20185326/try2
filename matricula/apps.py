from django.apps import AppConfig


class MatriculaConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'matricula'
    
    def ready(self):
        import matricula.signals
    
