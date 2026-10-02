from datetime import datetime
from typing import Optional
import boto3
from io import BytesIO

from ..core.config import settings


class PhotoService:
    def __init__(self):
        self.s3 = boto3.client(
            "s3",
            endpoint_url=settings.S3_ENDPOINT_URL,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            region_name=settings.S3_REGION,
        )

    def upload_photo(self, file_data: bytes, key: str, content_type: str = "image/jpeg") -> str:
        """Upload photo to S3."""
        self.s3.upload_fileobj(
            BytesIO(file_data),
            settings.S3_BUCKET_NAME,
            key,
            ExtraArgs={"ContentType": content_type},
        )
        return key

    def get_presigned_url(self, key: str, expires_in: int = 3600) -> str:
        """Generate presigned URL for photo access."""
        return self.s3.generate_presigned_url(
            "get_object",
            Params={"Bucket": settings.S3_BUCKET_NAME, "Key": key},
            ExpiresIn=expires_in,
        )

    def delete_photo(self, key: str) -> None:
        """Delete photo from S3."""
        self.s3.delete_object(Bucket=settings.S3_BUCKET_NAME, Key=key)


photo_service = PhotoService()