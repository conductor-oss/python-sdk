"""Client for Conductor file storage (``/api/files``).

Workflows exchange files as opaque handles of the form ``conductor://file/<id>``.
The server stores file records and enforces workflow ownership; the configured
backend (``conductor``, ``s3``, ``azure-blob`` or ``gcs``) stores the bytes.
Workers upload and download through short-lived URLs the server issues, so they
need no storage credentials.

This is a port of the Java SDK ``FileClient``. It covers single-request uploads,
downloads and metadata. Multipart uploads, which only S3 and Azure Blob Storage
support, are not implemented yet; every backend accepts a single-request upload.

Example::

    from conductor.client.file_client import FileClient, FileUploadOptions

    files = FileClient(configuration)
    handle = files.upload(workflow_id, "report.pdf")
    files.download(workflow_id, handle, "/tmp/report.pdf")
"""

from __future__ import annotations

import os
import re
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Dict, Optional, TypeVar, Union

import requests

from conductor.client.configuration.configuration import Configuration
from conductor.client.http.api_client import ApiClient
from conductor.client.http.rest import ApiException

FILE_HANDLE_PREFIX = "conductor://file/"

_MAX_FILENAME_LENGTH = 255
_FILE_ID_PATTERN = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,255}")
_UNSAFE_FILENAME = re.compile(r'[\x00-\x1f:*?"<>|/\\]')
_DEFAULT_CONTENT_TYPE = "application/octet-stream"
_AUTH_SETTINGS = ["api_key"]
# Statuses worth retrying. A signed URL may have expired (401/403); the upload
# path asks the server for a fresh one before the next attempt.
_RETRYABLE_TRANSFER_STATUSES = {401, 403, 408, 425, 429}
_RETRYABLE_SERVER_STATUSES = {0, 408, 425, 429}
_SERVER_ERROR = 500
_HTTP_OK_MIN, _HTTP_OK_MAX = 200, 300

T = TypeVar("T")


class FileStorageError(Exception):
    """A file operation failed. The message never contains a signed URL."""


class _TransferError(Exception):
    def __init__(self, operation: str, status: Optional[int] = None):
        super().__init__(f"{operation} failed" + (f" with HTTP {status}" if status else ""))
        self.status = status


@dataclass
class FileUploadOptions:
    """Optional metadata recorded with an upload."""

    file_name: Optional[str] = None
    content_type: Optional[str] = None
    task_id: Optional[str] = None


@dataclass
class FileMetadata:
    """Server-side metadata for an uploaded file."""

    file_handle_id: str
    file_name: Optional[str] = None
    content_type: Optional[str] = None
    file_size: Optional[int] = None
    content_hash: Optional[str] = None
    storage_type: Optional[str] = None
    upload_status: Optional[str] = None
    workflow_id: Optional[str] = None
    task_id: Optional[str] = None
    created_at: Optional[int] = None
    updated_at: Optional[int] = None

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "FileMetadata":
        return cls(
            file_handle_id=data.get("fileHandleId"),
            file_name=data.get("fileName"),
            content_type=data.get("contentType"),
            file_size=data.get("fileSize"),
            content_hash=data.get("contentHash"),
            storage_type=data.get("storageType"),
            upload_status=data.get("uploadStatus"),
            workflow_id=data.get("workflowId"),
            task_id=data.get("taskId"),
            created_at=data.get("createdAt"),
            updated_at=data.get("updatedAt"),
        )


class FileClient:
    """Upload, download and inspect files owned by workflow executions.

    Server calls go through the shared :class:`ApiClient`, so authentication is
    the same as every other client. Transfers to the issued URLs use a plain
    HTTP session with no Conductor credentials attached.
    """

    def __init__(
        self,
        configuration: Optional[Configuration] = None,
        *,
        retry_count: int = 3,
        api_client: Optional[ApiClient] = None,
        session: Optional[requests.Session] = None,
        timeout: float = 60.0,
    ):
        if retry_count < 0:
            raise FileStorageError("retry_count must not be negative")
        self._api_client = api_client or ApiClient(configuration or Configuration())
        self._session = session or requests.Session()
        self._retry_count = retry_count
        self._timeout = timeout

    # ── public API ───────────────────────────────────────────────────────

    def upload(
        self,
        workflow_id: str,
        source: Union[str, os.PathLike],
        options: Optional[FileUploadOptions] = None,
    ) -> str:
        """Upload a local file and return its ``conductor://file/<id>`` handle."""
        _validate_workflow_id(workflow_id)
        path = Path(source)
        if not path.is_file() or not os.access(path, os.R_OK):
            raise FileStorageError("Upload source must be a readable regular file")
        resolved = _resolve_options(options, default_name=path.name)
        return self._upload(workflow_id, resolved, lambda: path.read_bytes())

    def upload_bytes(self, workflow_id: str, data: bytes, options: FileUploadOptions) -> str:
        """Upload in-memory content. ``options.file_name`` is required."""
        _validate_workflow_id(workflow_id)
        if data is None:
            raise FileStorageError("Upload data is required")
        if options is None or not options.file_name:
            raise FileStorageError("A filename is required when uploading bytes")
        resolved = _resolve_options(options, default_name=None)
        payload = bytes(data)
        return self._upload(workflow_id, resolved, lambda: payload)

    def download(
        self, workflow_id: str, file_handle_id: str, destination: Union[str, os.PathLike]
    ) -> Path:
        """Download a file to *destination*, replacing it only after a complete transfer."""
        target = _validate_destination(destination)
        data = self.download_bytes(workflow_id, file_handle_id)
        target.parent.mkdir(parents=True, exist_ok=True)
        fd, temporary = tempfile.mkstemp(
            prefix=f".{target.name}.", suffix=".part", dir=str(target.parent)
        )
        try:
            with os.fdopen(fd, "wb") as out:
                out.write(data)
            os.replace(temporary, target)
        except OSError as e:
            raise FileStorageError("File download failed") from e
        finally:
            if os.path.exists(temporary):
                os.unlink(temporary)
        return target

    def download_bytes(self, workflow_id: str, file_handle_id: str) -> bytes:
        """Download a file's content into memory."""
        _validate_workflow_id(workflow_id)
        file_id = _to_file_id(file_handle_id)

        def attempt(_: int) -> bytes:
            url = self._server(
                "GET", "/files/{workflowId}/{fileId}/download-url", workflow_id, file_id
            ).get("downloadUrl")
            if not url:
                raise FileStorageError("Server returned an empty download URL response")
            return self._transfer("GET", url, None, "File download")

        return self._with_transfer_retries("File download", attempt)

    def get_metadata(self, workflow_id: str, file_handle_id: str) -> FileMetadata:
        """Return metadata for a file visible to *workflow_id*'s workflow family."""
        _validate_workflow_id(workflow_id)
        file_id = _to_file_id(file_handle_id)
        data = self._with_server_retries(
            lambda: self._server("GET", "/files/{workflowId}/{fileId}", workflow_id, file_id)
        )
        if not data:
            raise FileStorageError("Server returned empty file metadata")
        return FileMetadata.from_dict(data)

    # ── upload internals ─────────────────────────────────────────────────

    def _upload(
        self, workflow_id: str, options: FileUploadOptions, read: Callable[[], bytes]
    ) -> str:
        body = {
            "workflowId": workflow_id,
            "fileName": options.file_name,
            "contentType": options.content_type,
            "taskId": options.task_id,
        }
        created = self._server("POST", "/files", body=body)
        if not created:
            raise FileStorageError("Server returned an empty file creation response")
        handle = created.get("fileHandleId")
        file_id = _to_file_id(handle)
        owner = created.get("workflowId")
        if owner and owner != workflow_id:
            raise FileStorageError("The server returned a file owned by a different workflow")
        storage_type = created.get("storageType")

        def attempt(n: int) -> None:
            url = created.get("uploadUrl")
            if n > 0:
                url = self._server(
                    "GET", "/files/{workflowId}/{fileId}/upload-url", workflow_id, file_id
                ).get("uploadUrl")
            if not url:
                raise FileStorageError("Server returned an empty upload URL response")
            self._transfer("PUT", url, read(), "File upload", _upload_headers(storage_type))

        self._with_transfer_retries("File upload", attempt)
        self._complete_upload(workflow_id, file_id)
        return handle

    def _complete_upload(self, workflow_id: str, file_id: str) -> None:
        """Confirm the upload, treating an already-confirmed file as success."""
        last: Optional[Exception] = None
        for _ in range(self._retry_count + 1):
            try:
                self._server(
                    "POST", "/files/{workflowId}/{fileId}/upload-complete", workflow_id, file_id
                )
                return
            except ApiException as e:
                if not _retryable_server(e):
                    raise
                last = e
                if self._already_uploaded(workflow_id, file_id):
                    return
        raise FileStorageError("Unable to confirm file upload completion") from last

    def _already_uploaded(self, workflow_id: str, file_id: str) -> bool:
        try:
            data = self._server("GET", "/files/{workflowId}/{fileId}", workflow_id, file_id)
        except ApiException:
            return False
        return bool(data) and data.get("uploadStatus") == "UPLOADED"

    # ── transport ────────────────────────────────────────────────────────

    def _server(
        self,
        method: str,
        path: str,
        workflow_id: Optional[str] = None,
        file_id: Optional[str] = None,
        body: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        path_params = {}
        if workflow_id is not None:
            path_params["workflowId"] = workflow_id
        if file_id is not None:
            path_params["fileId"] = file_id
        headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        return self._api_client.call_api(
            path,
            method,
            path_params,
            [],
            headers,
            body=body,
            post_params=[],
            files={},
            response_type="object",
            auth_settings=_AUTH_SETTINGS,
            _return_http_data_only=True,
            _preload_content=True,
        )

    def _transfer(
        self,
        method: str,
        url: str,
        data: Optional[bytes],
        operation: str,
        headers: Optional[Dict[str, str]] = None,
    ) -> bytes:
        if not url.startswith(("http://", "https://")):
            raise FileStorageError("Signed URL must use HTTP(S)")
        try:
            response = self._session.request(
                method, url, data=data, headers=headers or {}, timeout=self._timeout
            )
        except requests.RequestException:
            # Drop the original exception text: it can contain the signed URL.
            raise _TransferError(operation) from None
        if not _HTTP_OK_MIN <= response.status_code < _HTTP_OK_MAX:
            raise _TransferError(operation, response.status_code)
        return response.content

    def _with_transfer_retries(self, operation: str, attempt: Callable[[int], T]) -> T:
        last: Optional[Exception] = None
        for n in range(self._retry_count + 1):
            try:
                return attempt(n)
            except _TransferError as e:
                retryable = (
                    e.status is None
                    or e.status in _RETRYABLE_TRANSFER_STATUSES
                    or e.status >= _SERVER_ERROR
                )
                if not retryable:
                    raise FileStorageError(str(e)) from None
                last = e
            except ApiException as e:
                if not _retryable_server(e):
                    raise
                last = e
        raise FileStorageError(
            f"{operation} failed after {self._retry_count + 1} attempts"
        ) from last

    def _with_server_retries(self, read: Callable[[], T]) -> T:
        last: Optional[Exception] = None
        for _ in range(self._retry_count + 1):
            try:
                return read()
            except ApiException as e:
                if not _retryable_server(e):
                    raise
                last = e
        raise FileStorageError("Server request failed") from last


# ── helpers ──────────────────────────────────────────────────────────────


def _retryable_server(error: ApiException) -> bool:
    status = getattr(error, "status", None) or 0
    return status in _RETRYABLE_SERVER_STATUSES or status >= _SERVER_ERROR


def _upload_headers(storage_type: Optional[str]) -> Dict[str, str]:
    # Azure rejects a single-request PUT without the blob type.
    if (storage_type or "").strip().upper() == "AZURE_BLOB":
        return {"x-ms-blob-type": "BlockBlob"}
    return {}


def _resolve_options(
    options: Optional[FileUploadOptions], default_name: Optional[str]
) -> FileUploadOptions:
    options = options or FileUploadOptions()
    name = options.file_name or default_name
    _validate_file_name(name)
    return FileUploadOptions(
        file_name=name,
        content_type=options.content_type or _DEFAULT_CONTENT_TYPE,
        task_id=options.task_id,
    )


def _validate_workflow_id(workflow_id: str) -> None:
    if not workflow_id or not str(workflow_id).strip():
        raise FileStorageError("workflow_id is required")


def _validate_file_name(name: Optional[str]) -> None:
    if (
        not name
        or not name.strip()
        or len(name) > _MAX_FILENAME_LENGTH
        or name in (".", "..")
        or _UNSAFE_FILENAME.search(name)
    ):
        raise FileStorageError("Filename is unsafe")


def _validate_destination(destination: Union[str, os.PathLike]) -> Path:
    if destination is None:
        raise FileStorageError("Download destination is required")
    target = Path(destination).absolute()
    if target.exists() and (target.is_dir() or target.is_symlink() or not target.is_file()):
        raise FileStorageError("Download destination must name a regular file")
    return target


def _to_file_id(file_handle_id: Optional[str]) -> str:
    if not file_handle_id or not file_handle_id.startswith(FILE_HANDLE_PREFIX):
        raise FileStorageError("Malformed file handle")
    file_id = file_handle_id[len(FILE_HANDLE_PREFIX) :]
    if not _FILE_ID_PATTERN.fullmatch(file_id):
        raise FileStorageError("Malformed file handle")
    return file_id


__all__ = [
    "FILE_HANDLE_PREFIX",
    "FileClient",
    "FileMetadata",
    "FileStorageError",
    "FileUploadOptions",
]
