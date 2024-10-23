from django.apps import AppConfig

class MyAppConfig(AppConfig):
    name = 'rimtex'

    def ready(self):
        import rimtex.signals