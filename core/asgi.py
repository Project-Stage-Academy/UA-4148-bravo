import os
from django.core.asgi import get_asgi_application
from fastapi_app.main import app as fastapi_app
from django.urls import path
from django.conf.urls import re_path

django_asgi_app = get_asgi_application()

from fastapi.middleware.asgi import ASGIApp

application = ASGIApp(
    app=django_asgi_app,
    lifespan=None,
    sub_apps=[("/api/fastapi", fastapi_app)],
)