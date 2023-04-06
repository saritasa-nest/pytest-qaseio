import base64
import logging

import arrow
from _pytest.python import Function
from selenium.common.exceptions import WebDriverException
from selenium.webdriver.remote.webdriver import WebDriver

from . import constants, storage


class DebugInfo:
    """Representation of debug information."""

    def __init__(self, item: Function, webdriver: WebDriver):
        """Set error log and extract data from extra."""
        self.webdriver: WebDriver = webdriver
        self.test_name = item.name
        self.logger = logging.getLogger(__name__)
        self.screenshot = self._extract_screenshot()
        self.html = self._extract_html()
        self.browser_log = self._extract_browser_log()
        self.url = self._extract_url()

    def _extract_screenshot(self) -> bytes:
        return base64.b64decode(self.webdriver.get_screenshot_as_base64().encode("utf-8"))

    def _extract_html(self) -> bytes:
        return self.webdriver.page_source.encode("utf-8")

    def _extract_url(self) -> str:
        return self.webdriver.current_url

    def _extract_browser_log(self) -> str:
        logs = []
        try:
            for name in self.webdriver.log_types:
                logs.append(self._format_log(self.webdriver.get_log(name)))  # type: ignore
        except WebDriverException:
            # https://github.com/mozilla/geckodriver/issues/284
            return ""
        return "\n".join(logs)

    @staticmethod
    def _format_log(log) -> str:
        """Format logs.

        Copied from pytest-selenium.

        """
        timestamp_format = "%Y-%m-%d %H:%M:%S.%f"
        entries = []
        for entry in log:
            timestamp = arrow.get(entry["timestamp"] / 1000.0).strftime(timestamp_format)
            entries.append(f"{timestamp} {entry['level']} - {entry['message']}")
        log = "\n".join(entries)
        return log

    def generate_debug_comment(
        self,
        file_storage: storage.FileStorage,
        folder: str,
    ) -> str:
        try:
            screenshot_url = file_storage.save_file_obj(
                content=self.screenshot, filename=f"{folder}/screenshot.png",
            )
        except BaseException:
            self.logger.error(msg="Can't save screenshot to storage", exc_info=True)
            screenshot_url = ""

        try:
            html_url = file_storage.save_file_obj(
                content=self.html, filename=f"{folder}/html.html",
            )
        except BaseException:
            self.logger.error(msg="Can't save HTML to storage", exc_info=True)
            html_url = ""

        try:
            browser_log_url = file_storage.save_file_obj(
                content=self.browser_log.encode("utf-8"),
                filename=f"{folder}/browser_log.txt",
            )
        except BaseException:
            self.logger.error(msg="Can't save browser log to storage", exc_info=True)
            browser_log_url = ""

        return constants.FAILED_TEST_REPORT_TEMPLATE.format(
            url=self.url,
            screenshot_url=screenshot_url,
            html_url=html_url,
            browser_log_url=browser_log_url,
        )
