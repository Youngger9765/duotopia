"""
Image upload service for vocabulary set images
"""

import os
import uuid
import json
from datetime import datetime
from typing import Optional
from fastapi import UploadFile, HTTPException
from google.cloud import storage


class ImageUploadService:
    def __init__(self):
        # Storage settings: GCS or local file system
        self.use_gcs = os.getenv("USE_GCS_STORAGE", "false").lower() == "true"
        self.bucket_name = os.getenv("GCS_BUCKET_NAME", "duotopia-audio")
        self.storage_client = None
        self.max_file_size = 2 * 1024 * 1024  # 2MB limit
        self.allowed_formats = [
            "image/jpeg",
            "image/jpg",
            "image/png",
            "image/gif",
            "image/webp",
        ]
        self.environment = os.getenv("ENVIRONMENT", "development")

        # Backend URL (for generating full image URLs)
        self.backend_url = os.getenv("BACKEND_URL", "").rstrip("/")

        # Local storage directory (when not using GCS)
        self.local_image_dir = os.path.join(
            os.path.dirname(__file__), "..", "static", "images"
        )
        if not self.use_gcs:
            os.makedirs(self.local_image_dir, exist_ok=True)

    def _get_storage_client(self):
        """Lazily initialize GCS client (using same auth logic as tts.py)"""
        if not self.storage_client:
            if not self.bucket_name:
                raise ValueError("GCS_BUCKET_NAME environment variable is not set")

            # Method 1: Try using service account key (production)
            backend_dir = os.path.dirname(os.path.dirname(__file__))
            key_path = os.path.join(backend_dir, "service-account-key.json")

            if os.path.exists(key_path):
                try:
                    if os.path.getsize(key_path) > 0:
                        with open(key_path, "r") as f:
                            json.load(f)  # Validate JSON format
                        try:
                            self.storage_client = (
                                storage.Client.from_service_account_json(key_path)
                            )
                            print(
                                "Image Upload GCS client initialized with service account key"
                            )
                            return self.storage_client
                        except Exception as e:
                            print(f"Failed to use service account key: {e}")
                    else:
                        print("Service account key file is empty, skipping")
                except (json.JSONDecodeError, ValueError) as e:
                    print(f"Service account key file is invalid JSON: {e}, skipping")

            # Method 2: Use Application Default Credentials (local development)
            original_creds = os.environ.pop("GOOGLE_APPLICATION_CREDENTIALS", None)
            try:
                self.storage_client = storage.Client()
                print(
                    "Image Upload GCS client initialized with Application Default Credentials"
                )
                return self.storage_client
            except Exception as e:
                print(f"Image Upload GCS client initialization failed: {e}")
                if original_creds:
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = original_creds
                return None
            finally:
                if original_creds:
                    os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = original_creds

        return self.storage_client

    async def upload_image(
        self,
        file: UploadFile,
        content_id: Optional[int] = None,
        item_index: Optional[int] = None,
    ) -> str:
        """
        Upload image to GCS

        Args:
            file: Uploaded image file
            content_id: Content ID (for tracking)
            item_index: Item index (for tracking)

        Returns:
            Image URL
        """
        try:
            # Check file type
            content_type = file.content_type or ""
            base_content_type = content_type.split(";")[0].strip().lower()

            if base_content_type not in self.allowed_formats:
                raise HTTPException(
                    status_code=400,
                    detail=f"Invalid file type '{content_type}'. Allowed: {', '.join(self.allowed_formats)}",
                )

            # Read file content
            content = await file.read()

            # Check file size (minimum 1KB, maximum 2MB)
            min_file_size = 1 * 1024  # 1KB
            if len(content) < min_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"Image file too small ({len(content)} bytes). Must be at least {min_file_size / 1024}KB.",
                )

            if len(content) > self.max_file_size:
                raise HTTPException(
                    status_code=400,
                    detail=f"File too large. Maximum size: {self.max_file_size / 1024 / 1024}MB",
                )

            # Generate unique filename
            file_id = str(uuid.uuid4())
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Determine extension based on content type
            ext_map = {
                "image/jpeg": "jpg",
                "image/jpg": "jpg",
                "image/png": "png",
                "image/gif": "gif",
                "image/webp": "webp",
            }
            extension = ext_map.get(base_content_type, "jpg")

            # Build filename with optional content_id and item_index for tracking
            if content_id is not None and item_index is not None:
                filename = f"content_{content_id}_item_{item_index}_{timestamp}_{file_id}.{extension}"
            else:
                filename = f"{timestamp}_{file_id}.{extension}"

            if self.use_gcs:
                # Upload to GCS
                blob_name = f"images/{self.environment}/{filename}"
                client = self._get_storage_client()
                if not client:
                    raise HTTPException(
                        status_code=500,
                        detail="GCS client initialization failed",
                    )

                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(blob_name)

                # Upload with content type
                blob.upload_from_string(content, content_type=base_content_type)

                # Make public
                blob.make_public()

                image_url = blob.public_url
                print(f"Image uploaded to GCS: {image_url}")
            else:
                # Local storage (development)
                local_path = os.path.join(self.local_image_dir, filename)
                with open(local_path, "wb") as f:
                    f.write(content)

                # Return local URL
                if self.backend_url:
                    image_url = f"{self.backend_url}/static/images/{filename}"
                else:
                    image_url = f"/static/images/{filename}"
                print(f"Image saved locally: {image_url}")

            return image_url

        except HTTPException:
            raise
        except Exception as e:
            print(f"Image upload failed: {e}")
            raise HTTPException(
                status_code=500,
                detail=f"Image upload failed: {str(e)}",
            )

    def delete_image(self, image_url: str) -> bool:
        """
        Delete image from GCS or local storage

        Args:
            image_url: URL of the image to delete

        Returns:
            True if deleted successfully, False otherwise
        """
        try:
            if not image_url:
                return False

            # Check if it's a GCS URL
            if "storage.googleapis.com" in image_url:
                # Extract blob name from URL
                # URL format: https://storage.googleapis.com/bucket-name/blob-name
                parts = image_url.split(f"{self.bucket_name}/")
                if len(parts) > 1:
                    blob_name = parts[1]
                else:
                    return False

                client = self._get_storage_client()
                if not client:
                    return False

                bucket = client.bucket(self.bucket_name)
                blob = bucket.blob(blob_name)

                if blob.exists():
                    blob.delete()
                    print(f"Image deleted from GCS: {blob_name}")
                    return True
                return False

            elif "/static/images/" in image_url:
                # Local file
                # Extract filename from URL like /static/images/filename.jpg
                filename = image_url.split("/static/images/")[-1]
                file_path = os.path.join(self.local_image_dir, filename)

                if os.path.exists(file_path):
                    os.remove(file_path)
                    print(f"Image deleted locally: {file_path}")
                    return True
                return False

            else:
                return False

        except Exception as e:
            print(f"Image deletion failed: {e}")
            return False


# Singleton instance
_image_upload_service = None


def get_image_upload_service() -> ImageUploadService:
    """Get singleton image upload service instance"""
    global _image_upload_service
    if _image_upload_service is None:
        _image_upload_service = ImageUploadService()
    return _image_upload_service
