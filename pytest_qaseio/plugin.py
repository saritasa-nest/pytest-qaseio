import logging
import os
import pathlib
from typing import cast

import filelock
import pytest
from _pytest.terminal import TerminalReporter
from qaseio import models
from qaseio.exceptions import ApiException

from . import api_client, converter, plugin_exceptions, storage


def pytest_addoption(parser: pytest.Parser) -> None:
    """Add custom args to command line."""
    parser.addoption(
        "--qase-enabled",
        action="store_true",
        default=False,
        help="Store run result in qase",
    )
    parser.addoption(
        "--qase-file-storage",
        default="qase",
        help="Choose file storage to upload debug files",
    )


def pytest_addhooks(pluginmanager: pytest.PytestPluginManager) -> None:
    """Add hooks for plugin."""
    from . import hooks

    pluginmanager.add_hookspecs(hooks)


def _get_file_storage(config: pytest.Config) -> storage.FileStorage | None:
    """Provide file storage via pytest config."""
    file_storage_name: str = config.getoption("--qase-file-storage")
    if file_storage_name.lower() == "none":
        return None

    file_storages: dict[str, storage.FileStorage] = config.hook.pytest_qase_file_storages()

    if file_storage_name not in file_storages:
        logging.getLogger("qase").error(
            "Cannot find registered file storage for "
            f"`{file_storage_name}`, saving to storage is disabled. "
            f"Available storages: {file_storages}",
        )

    return file_storages.get(file_storage_name)


@pytest.hookimpl(trylast=True)
def pytest_qase_file_storages() -> dict[str, storage.FileStorage]:
    """Provide mapping of available file storages for qase debug files."""
    return {
        "qase": storage.QaseFileStorage(
            qase_token=os.environ["QASE_TOKEN"],
            qase_project_code=os.environ["QASE_PROJECT_CODE"],
        ),
    }


@pytest.hookimpl(trylast=True)
def pytest_qase_browser_name(config: pytest.Config) -> str:
    """Try to get browser name from `webdriver` pytest option."""
    return config.getoption("--webdriver")


@pytest.hookimpl(trylast=True)
def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest-qaseio plugin.

    Add `qase` marker for pytest.
    If qase enabled, register qase plugin.
    Get file storage for qase plugin.

    """
    config.addinivalue_line(
        "markers",
        "qase(test_case_url): Mark test for qase",
    )
    qase_enabled = config.getoption("--qase-enabled")
    if not qase_enabled:
        return

    browser_name: str = config.hook.pytest_qase_browser_name(config=config)

    config.pluginmanager.register(
        plugin=QasePlugin(
            browser=browser_name,
            file_storage=_get_file_storage(config),
        ),
        name="qase_plugin",
    )


class QasePlugin:
    """Pytest plugin for reporting tests result to Qase."""

    # We use .pytest-qaseio.lock to lock process, in other words make other workers wait, until
    # worker that locked file will create run and store run's id in .pytest-qaseio. After other
    # workers load run by id from .pytest-qaseio.
    __run_file = pathlib.Path(".pytest-qaseio")
    __run_file_lock = pathlib.Path(".pytest-qaseio.lock")

    def __init__(
        self,
        browser: str,
        file_storage: storage.FileStorage | None,
    ):
        """Save used browser for run's name and folder name."""
        self._client = api_client.QaseClient(
            token=os.environ["QASE_TOKEN"],
            project_code=os.environ["QASE_PROJECT_CODE"],
        )
        self._cases_ids_from_api: list[int] = self._client.load_cases_ids()
        self._current_run: models.Run | None = None
        self._converter = converter.QaseConverter(
            browser=browser,
            env=os.environ["ENVIRONMENT"],
            project_code=os.environ["QASE_PROJECT_CODE"],
            file_storage=file_storage,
        )

        # Mapping of pytest items ids and case id
        self._tests: dict[str, int | None] = dict()
        # Mapping of case ids and result hash from qase with status
        self._qase_results: dict[str, tuple[str, models.ResultCreate]] = dict()

    def pytest_sessionstart(self, session: pytest.Session) -> None:
        """Clear previously saved run, prepare lock file."""
        if hasattr(session.config, "workerinput"):
            # Do nothing if it is not master thread
            return
        self.__run_file.unlink(missing_ok=True)
        self.__run_file_lock.touch(exist_ok=True)

    @pytest.hookimpl(trylast=True)
    def pytest_collection_modifyitems(
        self,
        items: list[pytest.Function],
    ) -> None:
        """Create test run in qase."""
        with filelock.FileLock(self.__run_file_lock):
            try:
                run_data, self._tests = self._converter.prepare_run_data(
                    cases_ids_from_api=self._cases_ids_from_api,
                    items=items,
                )

                # Specifying plan allows to create run "from template".
                # New run will contain all cases from plan + cases that
                # specified in tests
                if plan_id := os.getenv("QASE_PLAN_ID"):
                    run_data.plan_id = int(plan_id)

                if environment_id := os.getenv("QASE_ENVIRONMENT_ID"):
                    run_data.environment_id = int(environment_id)

                if qase_url_custom_field_id := os.getenv(
                    "QASE_URL_CUSTOM_FIELD_ID",
                ):
                    run_data.custom_field = {
                        # This should be provided from script that runs test, f.e jenkins script
                        qase_url_custom_field_id: os.getenv("RUN_SOURCE_URL") or "",
                    }

                self._current_run = self._load_run_from_file()
                if self._current_run:
                    return

                self._current_run = self._client.create_run(
                    run_data=run_data,
                )
                with pathlib.Path(self.__run_file).open(mode="w") as lock_file:
                    lock_file.write(str(self._current_run.id))
            except plugin_exceptions.BaseQasePluginException as e:
                pytest.exit(e.message)

    @pytest.hookimpl(tryfirst=True, hookwrapper=True)
    def pytest_runtest_makereport(self, item: pytest.Function):  # noqa: ANN201
        """Represent standard pytest hook on test completion.

        At this hook we will report passed, skipped and failed tests.

        """
        provided_report = yield
        report: pytest.TestReport = provided_report.get_result()
        should_report = not (
            # Passed tests should be reported only on call
            report.passed and report.when in ("setup", "teardown")
        )
        if not should_report:
            return
        case_id = self._tests[item.nodeid]
        # No need to report same passed status,
        # while skipped and failed should be always reported
        if not case_id or item.nodeid in self._qase_results and report.passed:
            return
        if not self._current_run:
            raise plugin_exceptions.RunNotConfigured()
        try:
            self._qase_results[item.nodeid] = self._client.report_test_results(
                run=self._current_run,
                report_data=self._converter.prepare_report_data(
                    run_id=cast(int, self._current_run.id),
                    case_id=case_id,
                    item=item,
                    report=report,
                ),
            )

        except ApiException as error:
            if report.passed:
                return
            # Qase closes runs, once every case got result. So if try to report any other result,
            # we'll get an error `Test run is not active`.
            terminal_reporter: TerminalReporter = item.config.pluginmanager.get_plugin(
                "terminalreporter",  # type: ignore
            )
            terminal_reporter.ensure_newline()
            terminal_reporter.section(
                f"{error}. "
                f"Seems that Qase closed run, and we are unable to report failed {item.name}",
                sep="=",
            )

    def _load_run_from_file(
        self,
    ) -> models.Run | None:
        """Load run id and then load it from qase."""
        if not self.__run_file.exists():
            return None
        with pathlib.Path(self.__run_file).open() as lock_file:
            run_id = int(lock_file.read())
            return self._client.get_run(
                run_id=run_id,
            )
