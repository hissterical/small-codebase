import os
import uuid
from datetime import timedelta
from typing import Any

import google.cloud.storage as storage


class GCSImageStore:
    """Small abstraction around Google Cloud Storage image operations."""

    def __init__(self, bucket_name: str | None = None, folder: str = "uploads") -> None:
        self.bucket_name = bucket_name or os.getenv("AWS_S3_BUCKET_NAME")
        if not self.bucket_name:
            raise ValueError("AWS_S3_BUCKET_NAME is required")

        self.folder = folder.strip("/")
        self.client = storage.Client()
        self.bucket = self.client.bucket(self.bucket_name)

    def upload_image(self, file_storage: Any) -> str:
        if not file_storage or not getattr(file_storage, "filename", None):
            raise ValueError("No file provided")

        ext = os.path.splitext(file_storage.filename)[1].lower()
        object_name = f"{self.folder}/{uuid.uuid4().hex}{ext}"
        blob = self.bucket.blob(object_name)
        blob.upload_from_file(file_storage.stream, content_type=file_storage.mimetype)
        return object_name

    def list_image_urls(self, expires_minutes: int = 30) -> list[str]:
        urls: list[str] = []
        prefix = f"{self.folder}/"

        for blob in self.client.list_blobs(self.bucket, prefix=prefix):
            if blob.name.endswith("/"):
                continue
            url = blob.generate_signed_url(
                version="v4",
                expiration=timedelta(minutes=expires_minutes),
                method="GET",
            )
            urls.append(url)

        return urls
