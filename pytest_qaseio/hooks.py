import pytest

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
