import logging
import os
import tempfile
import time
import mongomock
from channels.testing import ChannelsLiveServerTestCase
from mongoengine import connect, disconnect
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from core.settings import FORBIDDEN_WORDS_SET
from users.documents import UserDocument, UserRoleDocument, UserRoleEnum
from mongoengine.errors import NotUniqueError
from typing import Callable, Optional

os.environ['DJANGO_SETTINGS_MODULE'] = 'tests.chat.setup_test_env.'
TEST_USER_PASSWORD = os.getenv("TEST_USER_PASSWORD", "testpassword123")
MAX_MESSAGE_LENGTH = int(os.getenv("MAX_MESSAGE_LENGTH", 1000))

logger = logging.getLogger(__name__)


class ChatTests(ChannelsLiveServerTestCase):
    serve_static = True

    @classmethod
    def setUpClass(cls):
        """
        Set up in-memory MongoDB, test user, and Selenium WebDriver before running tests.
        """
        super().setUpClass()
        disconnect()
        connect(
            db='mongoenginetest',
            host='mongodb://localhost',
            mongo_client_class=mongomock.MongoClient
        )
        role = UserRoleDocument.objects(role=UserRoleEnum.USER).first()
        if not role:
            role = UserRoleDocument(role=UserRoleEnum.USER)
            role.save()

        cls.user = UserDocument(
            email="testuser@example.com",
            first_name="Test",
            last_name="User",
            password=TEST_USER_PASSWORD,
            role=role
        )
        try:
            cls.user.save()
        except NotUniqueError:
            cls.user = UserDocument.objects.get(email="testuser@example.com")

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

        cls.driver = webdriver.Chrome(
            service=Service(ChromeDriverManager().install()),
            options=options
        )

    @classmethod
    def tearDownClass(cls):
        """
        Clean up after tests: remove test users and close the Selenium WebDriver.
        """
        try:
            if hasattr(cls, "user") and cls.user:
                UserDocument.objects(email=cls.user.email).delete()
        except Exception as e:
            logger.warning("Failed to delete test user: %s", e)

        if hasattr(cls, "driver"):
            cls.driver.quit()

        disconnect()

        super().tearDownClass()

    def _enter_chat_room(self, room_name):
        """
        Open the chat page, enter the room name, and wait for WebSocket connection.
        """
        self.driver.get(self.live_server_url + "/chat/")
        ActionChains(self.driver).send_keys(room_name, Keys.ENTER).perform()
        self.wait_for_condition(lambda: room_name in self.driver.current_url, timeout=10)

        self.wait_for_condition(
            lambda: self.driver.execute_script(
                "return window.chatSocket && window.chatSocket.readyState === 1;"
            ),
            timeout=10
        )

    def _open_new_window(self):
        """Open a new browser tab and switch focus to it."""
        self.driver.execute_script('window.open("about:blank", "_blank");')
        self._switch_to_window(-1)

    def _close_all_new_windows(self):
        """Close all additional tabs and return focus to the first tab."""
        while len(self.driver.window_handles) > 1:
            self._switch_to_window(-1)
            self.driver.execute_script("window.close();")
        self._switch_to_window(0)

    def _switch_to_window(self, window_index):
        """Switch focus to a browser tab by index."""
        self.driver.switch_to.window(self.driver.window_handles[window_index])

    def _post_message(self, message):
        """Send a chat message in the active browser tab."""
        input_box = self.driver.find_element("id", "chat-message-input")
        input_box.clear()
        input_box.send_keys(message)
        input_box.send_keys(Keys.ENTER)

    def wait_for_condition(self, condition_fn: Callable[[], bool], timeout: float = 60,
                           poll_interval: float = 0.2) -> None:
        """
        Wait until a condition function returns True or timeout is reached.
        Raises TimeoutError if the condition is not met in time.
        """
        end_time = time.time() + timeout
        while time.time() < end_time:
            if condition_fn():
                return
            time.sleep(poll_interval)
        raise TimeoutError("Condition was not met in time.")

    def wait_for_message(self, message: str, window_index: Optional[int] = None, timeout: float = 60) -> None:
        """
        Wait until a message appears in the chat log, optionally in a specified tab.
        """
        if window_index is not None:
            self._switch_to_window(window_index)
        self.wait_for_condition(lambda: message in self._chat_log_value, timeout=timeout)

    @property
    def _chat_log_value(self) -> str:
        """Return the current contents of the chat log in the active tab."""
        return self.driver.execute_script(
            "return document.querySelector('#chat-log').value || "
            "document.querySelector('#chat-log').innerText;"
        )

    def test_message_visible_to_same_room(self):
        """
        Verify that messages sent in one chat room are visible to all clients in the same room.
        """
        try:
            self._enter_chat_room("room_1")
            self._open_new_window()
            self._enter_chat_room("room_1")

            self._switch_to_window(0)
            self._post_message("hello")
            self.wait_for_message("hello", window_index=0)

            self._switch_to_window(1)
            self.wait_for_message("hello", window_index=1)
        finally:
            self._close_all_new_windows()

    def test_message_not_visible_to_different_room(self):
        """
        Verify that messages sent in one chat room are not visible to clients in a different room.
        """
        try:
            self._enter_chat_room("room_1")
            self._open_new_window()
            self._enter_chat_room("room_2")

            self._switch_to_window(0)
            self._post_message("hello")
            self.wait_for_message("hello", window_index=0)

            self._switch_to_window(1)
            self._post_message("world")
            self.wait_for_message("world", window_index=1)

            self.assertTrue(
                "hello" not in self._chat_log_value,
                "Message from room_1 incorrectly received in room_2"
            )
        finally:
            self._close_all_new_windows()

    def test_empty_message(self):
        """Verify that sending an empty message is blocked."""
        self._enter_chat_room("room_edge")
        self._post_message("")
        with self.assertRaises(TimeoutError):
            self.wait_for_message("", timeout=2)

    def test_forbidden_content_message(self):
        """Verify that sending a message containing forbidden words is blocked."""
        forbidden_word = next(iter(FORBIDDEN_WORDS_SET))
        self._enter_chat_room("room_edge")
        self._post_message(f"This contains {forbidden_word}")
        with self.assertRaises(TimeoutError):
            self.wait_for_message(forbidden_word, timeout=2)

    def test_exceeding_length_message(self):
        """Verify that sending a message longer than MAX_MESSAGE_LENGTH is blocked."""
        long_message = "x" * (MAX_MESSAGE_LENGTH + 10)
        self._enter_chat_room("room_edge")
        self._post_message(long_message)
        with self.assertRaises(TimeoutError):
            self.wait_for_message(long_message, timeout=2)
