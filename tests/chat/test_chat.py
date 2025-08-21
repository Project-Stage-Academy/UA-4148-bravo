import tempfile
import time
from channels.testing import ChannelsLiveServerTestCase
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.common.keys import Keys
from webdriver_manager.chrome import ChromeDriverManager
from selenium.common.exceptions import NoAlertPresentException


class ChatTests(ChannelsLiveServerTestCase):
    """
    Integration tests for Django Channels chat using Selenium.

    Tests ensure:
    - Messages are received by all clients in the same room.
    - Messages are not received by clients in other rooms.
    """
    serve_static = True

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        options = Options()
        options.add_argument("--headless=new")
        options.add_argument("--no-sandbox")
        options.add_argument("--disable-dev-shm-usage")
        options.add_argument(f"--user-data-dir={tempfile.mkdtemp()}")

        try:
            cls.driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=options
            )
        except Exception as e:
            cls.tearDownClass()
            raise RuntimeError(f"Failed to start Chrome WebDriver: {e}")

    @classmethod
    def tearDownClass(cls):
        if hasattr(cls, "driver"):
            cls.driver.quit()
        super().tearDownClass()

    def test_message_visible_to_same_room(self):
        """Message sent in room_1 should be visible to all clients in the same room."""
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
        """Messages in one room should not be visible in another room."""
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

    def _enter_chat_room(self, room_name):
        """Open chat page and enter room name."""
        self.driver.get(self.live_server_url + "/chat/")
        ActionChains(self.driver).send_keys(room_name, Keys.ENTER).perform()
        timeout = time.time() + 10
        while time.time() < timeout:
            if room_name in self.driver.current_url:
                time.sleep(2)
                return
            time.sleep(0.2)
        raise TimeoutError(f"Room '{room_name}' did not load in time.")

    def _open_new_window(self):
        """Open a new browser tab and switch to it."""
        self.driver.execute_script('window.open("about:blank", "_blank");')
        self._switch_to_window(-1)

    def _close_all_new_windows(self):
        """Close additional tabs and return to first."""
        while len(self.driver.window_handles) > 1:
            self._switch_to_window(-1)
            self.driver.execute_script("window.close();")
        self._switch_to_window(0)

    def _switch_to_window(self, window_index):
        """Switch focus to a window by index."""
        self.driver.switch_to.window(self.driver.window_handles[window_index])

    def _post_message(self, message):
        """Send a message via chat input."""
        ActionChains(self.driver).send_keys(message, Keys.ENTER).perform()

    def wait_for_message(self, message, window_index=None, timeout=60):
        """
        Wait until a message appears in chat log, with optional window index.
        """
        if window_index is not None:
            self._switch_to_window(window_index)
        end_time = time.time() + timeout
        while time.time() < end_time:
            value = self.driver.execute_script(
                "return document.querySelector('#chat-log').value;"
            )
            if message in value:
                return
            time.sleep(0.2)
        raise TimeoutError(f"Message '{message}' was not received in time.")

    @property
    def _chat_log_value(self):
        """Get current contents of chat log in the active window."""
        return self.driver.execute_script(
            "return document.querySelector('#chat-log').value;"
        )

    def _dismiss_alert_if_present(self):
        """Close alert if present and return its text."""
        try:
            alert = self.driver.switch_to.alert
            text = alert.text
            alert.dismiss()
            return text
        except NoAlertPresentException:
            return None

    def test_empty_message_not_sent(self):
        """Empty messages should not be sent or appear in chat log."""
        try:
            self._enter_chat_room("room_edge")
            self._post_message("")
            time.sleep(1)
            alert_text = self._dismiss_alert_if_present()
            self.assertEqual(alert_text, "Cannot send an empty message.")

            self.assertEqual(self._chat_log_value.strip(), "")
        finally:
            self._close_all_new_windows()

    def test_forbidden_word_not_sent(self):
        """Messages with forbidden content should not appear in chat log."""
        try:
            self._enter_chat_room("room_edge")
            self.driver.execute_script("window.FORBIDDEN_WORDS_SET = ['casino'];")
            self._post_message("this has a casino word")
            time.sleep(1)

            alert_text = self._dismiss_alert_if_present()
            self.assertEqual(alert_text, "Your message contains forbidden content and cannot be sent.")

            self.assertNotIn("casino", self._chat_log_value)
        finally:
            self._close_all_new_windows()

    def test_too_long_message_not_sent(self):
        """Messages exceeding MAX_MESSAGE_LENGTH should not appear."""
        try:
            self._enter_chat_room("room_edge")
            self.driver.execute_script("window.MAX_MESSAGE_LENGTH = 10;")
            long_message = "x" * 50
            self._post_message(long_message)
            time.sleep(1)

            alert_text = self._dismiss_alert_if_present()
            self.assertEqual(alert_text, "Message must be at most 10 characters.")

            self.assertNotIn(long_message, self._chat_log_value,
                             "Too long message should not be sent")
        finally:
            self._close_all_new_windows()
