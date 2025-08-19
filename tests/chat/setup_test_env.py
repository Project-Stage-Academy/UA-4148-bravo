import os
import mongoengine
import mongomock

ASGI_APPLICATION = "core.asgi.application"
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels.layers.InMemoryChannelLayer"
    }
}

MONGO_PORT = int(os.getenv("MONGO_PORT", 27017))

mongoengine.connect(
    db='mongoenginetest',
    host='mongodb://localhost',
    mongo_client_class=mongomock.MongoClient,
    port=MONGO_PORT
)
