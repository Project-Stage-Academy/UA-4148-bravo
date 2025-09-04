from django.apps import AppConfig

class ProjectsConfig(AppConfig):
    name = 'projects'

    def ready(self):
        import startups.signals, projects.documents
        import projects.signals
