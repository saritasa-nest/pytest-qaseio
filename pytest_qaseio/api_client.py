import logging
import sys
from typing import cast

from qase.api_client_v1 import configuration as qaseio_config
from qase.api_client_v1.api.cases_api import CasesApi
from qase.api_client_v1.api.results_api import ResultsApi
from qase.api_client_v1.api.runs_api import RunsApi
from qase.api_client_v1.api_client import ApiClient
from qase.api_client_v1.models.id_response_all_of_result import IdResponseAllOfResult
from qase.api_client_v1.models.result_create import ResultCreate
from qase.api_client_v1.models.run import Run
from qase.api_client_v1.models.run_create import RunCreate


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
        self._client = ApiClient(
            configuration=qaseio_config.Configuration(
                api_key={
                    "TokenAuth": token,
                },
            ),
        )
        self._project_code: str = project_code

    def get_run(
        self,
        run_id: int,
    ) -> Run:
        run_response = RunsApi(self._client).get_run(
            code=self._project_code,
            id=run_id,
        )
        return cast(Run, run_response.result)

    def create_run(
        self,
        run_data: RunCreate,
    ) -> Run:
        """Create test run in Qase."""
        response = RunsApi(self._client).create_run(
            code=self._project_code,
            run_create=run_data,
        )
        created_run = cast(IdResponseAllOfResult, response.result)

        return self.get_run(cast(int, created_run.id))

    def load_cases_ids(
        self,
    ) -> list[int]:
        """Load all cases ids of project."""
        limit = 100
        cases: list[int] = []
        response = CasesApi(self._client).get_cases(
            code=self._project_code,
            limit=limit,
            offset=len(cases),
        )
        while True:
            response = CasesApi(self._client).get_cases(
                code=self._project_code,
                limit=limit,
                offset=len(cases),
            )
            response_cases = getattr(response.result, "entities", [])
            new_cases = [case.id for case in response_cases]
            cases += new_cases
            if not new_cases:
                break
        return cases

    def report_test_results(
        self,
        run: Run,
        report_data: ResultCreate,
    ) -> tuple[str, ResultCreate]:
        """Report test results back to Qase."""
        result = (
            ResultsApi(self._client)
            .create_result(
                code=self._project_code,
                id=cast(int, run.id),
                result_create=report_data,
            )
            .result
        )
        assert result
        return cast(str, result.hash), cast(ResultCreate, report_data.status)
