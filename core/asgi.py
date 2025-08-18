import os
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter
from channels.routing import URLRouter
from channels.security.websocket import AllowedHostsOriginValidator
from django.core.asgi import get_asgi_application
from starlette.applications import Starlette
from starlette.routing import Mount
from chat.routing import websocket_urlpatterns
from fastapi_app.main import app as fastapi_app

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')

# Django HTTP
django_asgi_app = get_asgi_application()

# Django WebSockets
django_channels_app = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

# Django WebSockets + FastAPI
application = Starlette(
    routes=[
        Mount("/api/fastapi", app=fastapi_app),
        Mount("/", app=django_channels_app),
    ]
)
