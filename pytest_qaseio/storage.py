import io
from typing import Protocol, cast

import qaseio
from qaseio.configuration import Configuration


class FileStorage(Protocol):
    """Base class for file uploader."""

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
        self._client = qaseio.ApiClient(
            configuration=Configuration(
                api_key={
                    "TokenAuth": qase_token,
                },
            ),
        )
        self._project_code = qase_project_code

    def save_file_obj(self, content: bytes, filename: str) -> str:
        """Upload file to Qase.io S3 bucket via attachment API."""
        file_obj = io.BytesIO(content)
        file_obj.name = filename

        attachment_response_result = (
            qaseio.AttachmentsApi(
                self._client,
            )
            .upload_attachment(
                code=self._project_code,
                file=[file_obj],
            )
            .result
        )
        assert attachment_response_result is not None

        return cast(str, attachment_response_result[0].url)
