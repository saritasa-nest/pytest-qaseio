import logging
import sys

import qaseio
import qaseio.apis
from qaseio import models


class QaseClient:
    """Class for interacting with tests runs in Qase API."""

    def __init__(
        self,
        token: str,
        project_code: str,
    ):
        """Init client."""
        super().__init__()
        self._logger = logging.getLogger("qase")
        self._logger.addHandler(
            logging.StreamHandler(sys.stderr),
        )
        self._client = qaseio.ApiClient(
            configuration=qaseio.Configuration(
                api_key={
                    "TokenAuth": token,
                },
            ),
        )
        self._project_code: str = project_code

    def get_run(
        self,
        run_id: int,
    ) -> models.Run:
        return qaseio.apis.RunsApi(self._client).get_run(
            code=self._project_code, id=run_id,
        ).result

    def create_run(
        self,
        run_data: models.RunCreate,
    ) -> models.Run:
        """Create test run in Qase."""
        response = qaseio.apis.RunsApi(self._client).create_run(
            code=self._project_code,
            run_create=run_data,
        )
        return self.get_run(response.result.id)

    def load_cases_ids(
        self,
    ) -> list[int]:
        """Load all cases ids of project."""
        limit = 100
        cases: list[int] = []
        response: models.TestCaseListResponse = qaseio.apis.CasesApi(self._client).get_cases(
            code=self._project_code,
            limit=limit,
            offset=len(cases),
        )
        while True:
            response = qaseio.apis.CasesApi(self._client).get_cases(
                code=self._project_code,
                limit=limit,
                offset=len(cases),
            )
            new_cases = [case.id for case in response.result.entities]
            cases += new_cases
            if not new_cases:
                break
        return cases

    def report_test_results(
        self,
        run: models.RunCreate,
        report_data: models.ResultCreate,
    ) -> tuple[str, models.ResultCreate]:
        """Report test results back to Qase."""
        result = qaseio.apis.ResultsApi(self._client).create_result(
            code=self._project_code,
            id=run.id,
            result_create=report_data,
        ).result
        return result.hash, report_data.status
