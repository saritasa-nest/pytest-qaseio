import base64
import logging
import typing
from collections.abc import Iterable

import arrow
from _pytest.python import Function
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

    def _extract_screenshot(self) -> bytes | None:
        try:
            return base64.b64decode(self.webdriver.get_screenshot_as_base64().encode("utf-8"))
        except Exception:
            self.logger.error(msg="Can't extract screenshot from webdriver", exc_info=True)
            return None

    def _extract_html(self) -> bytes | None:
        try:
            return self.webdriver.page_source.encode("utf-8")
        except Exception:
            self.logger.error(msg="Can't extract html page source from webdriver", exc_info=True)
            return None

    def _extract_url(self) -> str:
        try:
            return self.webdriver.current_url
        except Exception:
            self.logger.error(msg="Can't extract url from webdriver", exc_info=True)
            return ""

    def _extract_browser_log(self) -> str:
        logs = []
        try:
            for name in self.webdriver.log_types:
                logs.append(self._format_log(self.webdriver.get_log(name)))  # type: ignore
        except Exception:
            # Sometimes there can be problems reading some logs from the browser here
            # (such as `ProtocolError('Connection broken')`). So we skip them if this happens.

            # Also, this method can't work correctly with Geckodriver (raises `WebDriverException`
            # error) because of the following issue
            # https://github.com/mozilla/geckodriver/issues/284
            self.logger.error(msg="Can't extract browser log", exc_info=True)
            pass
        return "\n".join(logs)

    @staticmethod
    def _format_log(log: Iterable[dict[str, typing.Any]]) -> str:
        """Format logs.

        Copied from pytest-selenium.

        """
        timestamp_format = "%Y-%m-%d %H:%M:%S.%f"
        entries: list[str] = []
        for entry in log:
            timestamp = arrow.get(entry["timestamp"] / 1000.0).strftime(timestamp_format)
            entries.append(f"{timestamp} {entry['level']} - {entry['message']}")
        return "\n".join(entries)

    def generate_debug_comment(
        self,
        file_storage: storage.FileStorage,
        folder: str,
    ) -> str:
        screenshot_url = ""
        if self.screenshot:
            try:
                screenshot_url = file_storage.save_file_obj(
                    content=self.screenshot,
                    filename=f"{folder}/screenshot.png",
                )
            except Exception:
                self.logger.error(msg="Can't save screenshot to storage", exc_info=True)

        html_url = ""
        if self.html:
            try:
                html_url = file_storage.save_file_obj(
                    content=self.html,
                    filename=f"{folder}/html.html",
                )
            except Exception:
                self.logger.error(msg="Can't save HTML to storage", exc_info=True)

        try:
            browser_log_url = file_storage.save_file_obj(
                content=self.browser_log.encode("utf-8"),
                filename=f"{folder}/browser_log.txt",
            )
        except Exception:
            self.logger.error(msg="Can't save browser log to storage", exc_info=True)
            browser_log_url = ""

        return constants.FAILED_TEST_REPORT_TEMPLATE.format(
            url=self.url,
            screenshot_url=screenshot_url,
            html_url=html_url,
            browser_log_url=browser_log_url,
        )
