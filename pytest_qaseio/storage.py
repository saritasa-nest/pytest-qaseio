from typing import Protocol, cast

from qase.api_client_v1 import configuration as qaseio_config
from qase.api_client_v1.api.attachments_api import AttachmentsApi
from qase.api_client_v1.api_client import ApiClient


class FileStorage(Protocol):
    """Protocol for representing required file uploader interfaces."""

    def save_file_obj(self, content: bytes, filename: str) -> str:
        """Upload file to storage and return URL."""
        ...


class QaseFileStorage:
    """Upload files to Qase S3 bucket as attachment."""

    def __init__(
        self,
        qase_token: str,
        qase_project_code: str,
    ):
        """Prepare ApiClient for qase io using credentials."""
        self._client = ApiClient(
            configuration=qaseio_config.Configuration(
                api_key={
                    "TokenAuth": qase_token,
                },
            ),
        )
        self._project_code = qase_project_code

    def save_file_obj(self, content: bytes, filename: str) -> str:
        """Upload file to Qase.io S3 bucket via attachment API."""
        attachment_response_result = (
            AttachmentsApi(
                self._client,
            )
            .upload_attachment(
                code=self._project_code,
                file=[content],
            )
            .result
        )
        assert attachment_response_result is not None

        return cast(str, attachment_response_result[0].url)
