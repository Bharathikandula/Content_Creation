from datetime import datetime, timedelta
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
        self._ensure_bucket()

    def _ensure_bucket(self):
        """Ensure S3 bucket exists."""
        try:
            self.s3.head_bucket(Bucket=settings.S3_BUCKET_NAME)
        except Exception:
            try:
                self.s3.create_bucket(Bucket=settings.S3_BUCKET_NAME)
                # Set lifecycle policy for 24h expiry
                self.s3.put_bucket_lifecycle_configuration(
                    Bucket=settings.S3_BUCKET_NAME,
                    LifecycleConfiguration={
                        "Rules": [
                            {
                                "ID": "expire-photos",
                                "Status": "Enabled",
                                "Filter": {"Prefix": "photos/"},
                                "Expiration": {"Days": 1},
                            }
                        ]
                    },
                )
            except Exception as e:
                print(f"Error creating bucket: {e}")

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
            Params={
                "Bucket": settings.S3_BUCKET_NAME,
                "Key": key,
            },
            ExpiresIn=expires_in,
        )

    def delete_photo(self, key: str) -> None:
        """Delete photo from S3."""
        self.s3.delete_object(
            Bucket=settings.S3_BUCKET_NAME,
            Key=key,
        )

    def cleanup_expired_photos(self) -> int:
        """Delete expired photos. Returns count of deleted photos."""
        # This would query the database for expired photos
        # and delete them from S3
        # Implementation depends on database access
        return 0


# Singleton instance
photo_service = PhotoService()