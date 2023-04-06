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
