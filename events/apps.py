from django.apps import AppConfig


class EventsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'events'
    
    def ready(self):
        # Import des signaux pour s'assurer qu'ils sont enregistrés
        import events.signals
