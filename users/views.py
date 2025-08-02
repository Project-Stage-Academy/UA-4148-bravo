import logging
from rest_framework_simplejwt.views import TokenObtainPairView
from .serializers import CustomTokenObtainPairSerializer

# Custom view to use the custom JWT serializer
class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

# Optional logging setup (can be removed if not needed)
logger = logging.getLogger(__name__)
logger.debug("This is a debug message.")
logger.info("Informational message.")
logger.warning("Warning occurred!")
logger.error("An error happened.")
logger.critical("Critical issue!")


