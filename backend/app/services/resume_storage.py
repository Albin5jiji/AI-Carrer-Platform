"""Private S3-compatible storage helpers for resume files."""
from pathlib import PurePosixPath
from uuid import uuid4

from fastapi import HTTPException, status

from ..config import settings

ALLOWED_CONTENT_TYPES = {"application/pdf"}


def _client():
    if not settings.resume_storage_bucket:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Resume file storage is not configured")
    try:
        import boto3
        # An empty endpoint means standard AWS S3. boto3 rejects an empty string,
        # so pass None rather than the optional setting's blank default.
        return boto3.client(
            "s3",
            region_name=settings.resume_storage_region,
            endpoint_url=settings.resume_storage_endpoint or None,
        )
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail="Resume file storage is unavailable") from exc


def validate_upload(filename: str, content_type: str, size: int) -> None:
    if content_type not in ALLOWED_CONTENT_TYPES or not filename.lower().endswith(".pdf"):
        raise HTTPException(status_code=422, detail="Only PDF resume files are supported")
    if size <= 0 or size > settings.resume_max_file_size_bytes:
        raise HTTPException(status_code=422, detail=f"Resume files must be at most {settings.resume_max_file_size_bytes} bytes")


def create_upload(student_id: int, resume_id: int, filename: str, content_type: str) -> tuple[str, str]:
    key = str(PurePosixPath(settings.resume_storage_prefix, str(student_id), str(resume_id), f"{uuid4().hex}.pdf"))
    url = _client().generate_presigned_url("put_object", Params={"Bucket": settings.resume_storage_bucket, "Key": key, "ContentType": content_type}, ExpiresIn=settings.resume_presign_expiry_seconds, HttpMethod="PUT")
    return key, url


def create_download(key: str) -> str:
    return _client().generate_presigned_url("get_object", Params={"Bucket": settings.resume_storage_bucket, "Key": key}, ExpiresIn=settings.resume_presign_expiry_seconds)


def delete_object(key: str) -> None:
    _client().delete_object(Bucket=settings.resume_storage_bucket, Key=key)


def read_object(key: str) -> bytes:
    return _client().get_object(Bucket=settings.resume_storage_bucket, Key=key)["Body"].read()
