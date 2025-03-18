import collections
import datetime
import logging
import sys

import pytest
from qase.api_client_v1.models.result_create import ResultCreate
from qase.api_client_v1.models.run_create import RunCreate

from . import constants, debug_info, plugin_exceptions, storage


class QaseConverter:
    """Class for converting data from pytest to qase."""

    def __init__(
        self,
        browser: str,
        env: str,
        project_code: str,
        file_storage: storage.FileStorage | None,
    ):
        """Init converter."""
        super().__init__()
        self._logger = logging.getLogger("qase")
        self._logger.addHandler(
            logging.StreamHandler(sys.stderr),
        )
        self._env = env
        self._browser = browser
        self._project_code = project_code
        self._file_storage = file_storage

    def prepare_run_data(
        self,
        cases_ids_from_api: list[int],
        items: list[pytest.Function],
    ) -> tuple[RunCreate, dict[str, int | None]]:
        """Prepare data needed to create test run."""
        cases, tests = self._prepare_cases_for_run(
            cases_ids_from_api=cases_ids_from_api,
            items=items,
        )
        title = constants.RUN_NAME_TEMPLATE.format(
            env=self._env.capitalize(),
            browser=self._browser.capitalize(),
            date=datetime.datetime.now(tz=datetime.UTC).strftime("%m/%d/%Y %H:%M:%S"),
        )
        run_data = RunCreate(
            title=title,
            cases=cases,
        )

        return run_data, tests

    def prepare_report_data(
        self,
        case_id: int,
        run_id: int,
        item: pytest.Function,
        report: pytest.TestReport,
    ) -> ResultCreate:
        """Create a test result based on results from pytest."""
        if hasattr(report, "wasxfail"):
            return self._prepare_xfailed_test_report(
                case_id=case_id,
                report=report,
            )
        match report.outcome:
            case "passed":
                return self._prepare_passed_test_report(
                    case_id=case_id,
                    report=report,
                )
            case "skipped":
                return self._prepare_skipped_test_report(
                    case_id=case_id,
                    report=report,
                )
            case "failed":
                return self._prepare_failed_test_report(
                    case_id=case_id,
                    run_id=run_id,
                    item=item,
                    report=report,
                )
        raise ValueError("Failed to convert test result!")

    def _prepare_passed_test_report(
        self,
        case_id: int,
        report: pytest.TestReport,
    ) -> ResultCreate:
        """Prepare result report for passed test."""
        return ResultCreate(
            case_id=case_id,
            status="passed",
            comment=constants.TEST_PASSED,
            time_ms=int(report.duration * 1000),
        )

    def _prepare_skipped_test_report(
        self,
        case_id: int,
        report: pytest.TestReport,
    ) -> ResultCreate:
        """Prepare result report for skipped test."""
        *_, skip_reason = report.longrepr  # type: ignore
        return ResultCreate(
            case_id=case_id,
            status="skipped",
            comment=skip_reason,
            time_ms=int(report.duration * 1000),
        )

    def _prepare_xfailed_test_report(
        self,
        case_id: int,
        report: pytest.TestReport,
    ) -> ResultCreate:
        """Prepare result report for xfailed test.

        We use the `blocked` status so as not to mislead the QA team. If they
        see a `failed` case, they will go to retest it. But `xfail` implies
        that the case fails for some already known reason. So the `blocked`
        status will let them know that the case is blocked for some reason
        described in the `xfail` comment (this comment will be duplicated as
        a result of the case run).

        """
        return ResultCreate(
            case_id=case_id,
            status="blocked",
            comment=report.wasxfail,
            time_ms=int(report.duration * 1000),
        )

    def _prepare_failed_test_report(
        self,
        case_id: int,
        run_id: int,
        item: pytest.Function,
        report: pytest.TestReport,
    ) -> ResultCreate:
        """Prepare result report for failed test."""
        comment = constants.TEST_FAILED.format(when=report.when)
        debug_information = (
            debug_info.DebugInfo(
                item=item,
                webdriver=item._webdriver,
            )
            if hasattr(item, "_webdriver")
            else None
        )
        if debug_information and self._file_storage:
            folder = constants.REPORT_FOLDER_TEMPLATE.format(
                env=self._env,
                id=run_id,
                browser=self._browser,
                test_name=item.name,
            )
            debug_comment = debug_information.generate_debug_comment(
                file_storage=self._file_storage,
                folder=folder,
            )
            comment += f"\n{debug_comment}"

        return ResultCreate(
            case_id=case_id,
            status="failed",
            comment=comment,
            time_ms=int(report.duration * 1000),
            stacktrace=report.longreprtext,
        )

    def _prepare_cases_for_run(
        self,
        cases_ids_from_api: list[int],
        items: list[pytest.Function],
    ) -> tuple[list[int], dict[str, int | None]]:
        """Collect test cases from test markers.

        Raise InvalidCaseId in case if incorrect case id was provided. Raise DuplicatingCaseId in
        case if duplicated cased ids were provided.

        """
        cases_ids = []

        case_id_invalid = False
        # list of parsed markers to track duplicating case IDs in different tests
        parsed_markers_ids = []
        # Mapping of pytest items ids and case id
        tests: dict[str, int | None] = {}
        for item in items:
            case_id = self._extract_case_id_from_test(
                project_code=self._project_code,
                item=item,
            )
            tests[item.nodeid] = case_id
            qase_marker = self._extract_qase_marker(item)
            qase_marker_id = id(qase_marker)
            if qase_marker_id in parsed_markers_ids:
                continue
            parsed_markers_ids.append(qase_marker_id)

            if not case_id:
                self._logger.error(
                    f"No case id not found for {item.name}! "
                    f"Please add case id for {item.location[0]}:1",
                )
                case_id_invalid = True
                continue
            if case_id not in cases_ids_from_api:
                self._logger.error(
                    f"Case with ID {case_id} not found for {item.name}! "
                    f"Please check case id for {item.location[0]}",
                )
                case_id_invalid = True
                continue
            cases_ids.append(case_id)

        duplicating_ids = [
            case_id for case_id, counter in collections.Counter(cases_ids).items() if counter > 1
        ]
        if duplicating_ids:
            raise plugin_exceptions.DuplicatingCaseId(duplicating_ids)

        if case_id_invalid:
            raise plugin_exceptions.InvalidCaseId()
        return cases_ids, tests

    def _extract_qase_marker(
        self,
        item: pytest.Function,
    ) -> pytest.Mark | None:
        """Extract qase's `Mark` object from test item."""
        qase_markers = [marker for marker in item.own_markers if marker.name == "qase"]
        if not qase_markers:
            return None

        if len(qase_markers) == 1:
            return qase_markers[0]

        self._logger.error(
            f"Multiple qase IDs associated with: {item}",
        )
        raise plugin_exceptions.MultipleIDsForTest()

    def _extract_case_id_from_marker(
        self,
        project_code: str,
        marker: pytest.Mark,
    ) -> None | int:
        """Shortcut to extract qase case ID from marker."""
        if len(marker.args) != 1:
            return None
        url = marker.args[0]
        return int(url.split(f"{project_code}-")[-1])

    def _extract_case_id_from_test(
        self,
        project_code: str,
        item: pytest.Function,
    ) -> int | None:
        """Get test case's id marker from test item."""
        marker = self._extract_qase_marker(item=item)
        if not marker:
            return None
        return self._extract_case_id_from_marker(project_code=project_code, marker=marker)
