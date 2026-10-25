import os
import hashlib
import uuid
from typing import Tuple
from fastapi import UploadFile, HTTPException, status
from backend.app.core.config import settings


class StorageService:
    def __init__(self, base_dir: str = settings.STORAGE_DIR):
        self.base_dir = os.path.abspath(base_dir)
        os.makedirs(self.base_dir, exist_ok=True)
        self.max_size_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
        self.allowed_extensions = {ext.strip().lower() for ext in settings.ALLOWED_EXTENSIONS.split(",")}

    def _validate_file_extension(self, filename: str) -> str:
        parts = filename.rsplit(".", 1)
        if len(parts) < 2:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="File has no extension. Allowed extensions: " + ", ".join(self.allowed_extensions)
            )
        ext = parts[1].lower()
        if ext not in self.allowed_extensions:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"File extension '.{ext}' is not permitted. Allowed: {', '.join(self.allowed_extensions)}"
            )
        return ext

    async def save_upload(self, upload_file: UploadFile) -> Tuple[str, str, int, str]:
        """
        Validates, computes SHA-256 hash, and saves an uploaded file safely.
        Returns: (stored_rel_path, sha256_hash, file_size, content_type)
        """
        original_name = upload_file.filename or "unnamed_document"
        ext = self._validate_file_extension(original_name)

        hasher = hashlib.sha256()
        total_size = 0
        chunks = []

        while True:
            chunk = await upload_file.read(1024 * 64)
            if not chunk:
                break
            total_size += len(chunk)
            if total_size > self.max_size_bytes:
                raise HTTPException(
                    status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                    detail=f"File size exceeds maximum permitted limit of {settings.MAX_UPLOAD_SIZE_MB}MB"
                )
            hasher.update(chunk)
            chunks.append(chunk)

        sha256_hash = hasher.hexdigest()
        safe_filename = f"{uuid.uuid4().hex}.{ext}"
        target_path = os.path.join(self.base_dir, safe_filename)

        with open(target_path, "wb") as f:
            for chunk in chunks:
                f.write(chunk)

        content_type = upload_file.content_type or "application/octet-stream"
        return safe_filename, sha256_hash, total_size, content_type

    def get_absolute_path(self, rel_filename: str) -> str:
        # Prevent path traversal
        clean_name = os.path.basename(rel_filename)
        full_path = os.path.join(self.base_dir, clean_name)
        if not os.path.exists(full_path):
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="File not found in storage")
        return full_path


storage_service = StorageService()
