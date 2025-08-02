import os
import django
from django.core.asgi import get_asgi_application
from starlette.routing import Mount
from starlette.applications import Starlette
from fastapi_app.main import app as fastapi_app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

django_asgi_app = get_asgi_application()

application = Starlette(
    routes=[
        Mount("/api/fastapi", app=fastapi_app),
        Mount("/", app=django_asgi_app),
    ]
)
