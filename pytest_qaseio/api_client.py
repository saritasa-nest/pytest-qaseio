import logging
import sys
from typing import cast

import qaseio
from qaseio import configuration as qaseio_config
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
    ) -> models.Run:
        run_response = qaseio.RunsApi(self._client).get_run(
            code=self._project_code,
            id=run_id,
        )
        return cast(models.Run, run_response.result)

    def create_run(
        self,
        run_data: models.RunCreate,
    ) -> models.Run:
        """Create test run in Qase."""
        response = qaseio.RunsApi(self._client).create_run(
            code=self._project_code,
            run_create=run_data,
        )
        created_run = cast(models.IdResponseAllOfResult, response.result)

        return self.get_run(cast(int, created_run.id))

    def load_cases_ids(
        self,
    ) -> list[int]:
        """Load all cases ids of project."""
        limit = 100
        cases: list[int] = []
        response = qaseio.CasesApi(self._client).get_cases(
            code=self._project_code,
            limit=limit,
            offset=len(cases),
        )
        while True:
            response = qaseio.CasesApi(self._client).get_cases(
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
        run: models.Run,
        report_data: models.ResultCreate,
    ) -> tuple[str, models.ResultCreate]:
        """Report test results back to Qase."""
        result = (
            qaseio.ResultsApi(self._client)
            .create_result(
                code=self._project_code,
                id=cast(int, run.id),
                result_create=report_data,
            )
            .result
        )
        assert result
        return cast(str, result.hash), cast(models.ResultCreate, report_data.status)
