import io
from typing import Protocol

import qaseio
import qaseio.apis


class FileStorage(Protocol):
    """Base class for file uploader."""

    def save_file_obj(self, content: bytes, filename: str) -> str:
        """Upload file to storage and return URL."""


class QaseFileStorage:
    """Upload files to Qase S3 bucket as attachment."""

    def __init__(
        self,
        qase_token: str,
        qase_project_code: str,
    ):
        """Prepare ApiClient for qase io using credentials."""
        self._client = qaseio.ApiClient(
            configuration=qaseio.Configuration(
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

        result = qaseio.apis.AttachmentsApi(self._client).upload_attachment(
            code=self._project_code,
            file=[file_obj],
        ).result[0]
        return result["url"]
