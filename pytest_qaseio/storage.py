import io
from typing import Protocol, cast

from qase.api_client_v1 import configuration as qaseio_config
from qase.api_client_v1.api.attachments_api import AttachmentsApi
from qase.api_client_v1.api_client import ApiClient


class FileStorage(Protocol):
    """Base class for file uploader."""

    def save_file_obj(self, content: bytes, filename: str) -> str:
        """Upload file to storage and return URL."""
        ...


class FileIO(io.BytesIO):
    """Represent file object to pass in Qase API methods.

    Set `name` and `mime` attributes to objects since it's required in
    https://github.com/qase-tms/qase-python/blob/44d19a500246017a30e0fa06b35cace065135d96/qaseio/src/qaseio/api_client.py#L518

    """

    mime = "image/png"

    def __init__(self, *args, filename: str, **kwargs) -> None:
        super().__init__(*args, **kwargs)
        self.name = filename


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
        file_obj = FileIO(content, filename=filename)

        attachment_response_result = (
            AttachmentsApi(
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
