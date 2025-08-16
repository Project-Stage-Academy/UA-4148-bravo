import logging
import pytest
import os

@pytest.fixture(scope="session", autouse=True)
def configure_logging():
    """Configure logging for all tests.

    This fixture runs automatically for the entire test session.

    - Suppresses verbose Django logs by setting the Django logger to WARNING level.
    - Enables test logging (INFO level) only if the environment variable
      `DEBUG_TEST_LOGS` is set to "1".
    - Works with both Django TestCase and pytest tests.

    By default, test output remains clean, but detailed logs can be enabled
    for debugging purposes.

    Returns:
        None
    """
    logging.getLogger("django").setLevel(logging.WARNING)
    
    if os.environ.get("DEBUG_TEST_LOGS") == "1":
        logging.basicConfig(
            level=logging.INFO,
            format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
        )