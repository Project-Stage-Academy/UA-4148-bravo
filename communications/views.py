from django.shortcuts import render
import logging

logger = logging.getLogger(__name__)

logger.debug("This is a debug message.")
logger.info("Informational message.")
logger.warning("Warning occurred!")
logger.error("An error happened.")
logger.critical("Critical issue!")

# Create your views here.
