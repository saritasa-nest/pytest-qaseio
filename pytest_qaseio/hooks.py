import pytest

from pytest_qaseio.debug_info import DebugInfo

from . import storage


@pytest.hookspec(firstresult=True)
def pytest_qase_file_storages() -> dict[str, storage.FileStorage]:  # type: ignore
    """Return mapping options to file storage instance.

    Example:
        {
            "qase": QaseFileStorage(),
        }

    """


@pytest.hookspec(firstresult=True)
def pytest_qase_browser_name(config: pytest.Config) -> str:  # type: ignore
    """Return name of browser to use in test run name and attachments path."""


@pytest.hookspec(firstresult=True)
def pytest_get_debug_info(item: pytest.Function) -> DebugInfo | None:
    """Return object with test debug information."""


@pytest.hookspec(firstresult=True)
def pytest_get_run_name(config: pytest.Config, env: str, browser: str) -> str:
    """Return name for test run to use in Qase."""
    return ""
