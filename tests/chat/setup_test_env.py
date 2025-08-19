import os
import mongoengine

ASGI_APPLICATION = "core.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

MONGO_DB = os.getenv("MONGO_DB", "my_database")
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))

mongoengine.connect(
    db=MONGO_DB,
    host=MONGO_HOST,
    port=MONGO_PORT,
)
