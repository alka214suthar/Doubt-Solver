from __future__ import annotations

import io
import time
import uuid
import warnings
from pathlib import Path

from fastapi import UploadFile
from PIL import Image, UnidentifiedImageError

from config import DOUBT_RETENTION_DAYS, MAX_IMAGE_SIZE_BYTES, UPLOAD_DIR
from errors import FileValidationError

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}
FORMAT_EXTENSIONS = {
    "JPEG": {".jpg", ".jpeg"},
    "PNG": {".png"},
    "WEBP": {".webp"},
}
READ_CHUNK_SIZE = 1024 * 1024


async def save_validated_image(upload: UploadFile) -> Path:
    extension = Path(upload.filename or "").suffix.lower()
    if extension not in ALLOWED_EXTENSIONS:
        raise FileValidationError(
            "Only .jpg, .jpeg, .png, and .webp images are allowed."
        )

    data = bytearray()
    try:
        while chunk := await upload.read(READ_CHUNK_SIZE):
            data.extend(chunk)
            if len(data) > MAX_IMAGE_SIZE_BYTES:
                raise FileValidationError(
                    "Image must be 5 MB or smaller.",
                    status_code=413,
                )
    finally:
        await upload.close()

    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(io.BytesIO(data)) as image:
                image_format = image.format
                image.verify()
    except (
        Image.DecompressionBombError,
        Image.DecompressionBombWarning,
        UnidentifiedImageError,
        OSError,
        SyntaxError,
        ValueError,
    ) as exc:
        raise FileValidationError("Uploaded file is not a valid image.") from exc

    if image_format not in FORMAT_EXTENSIONS:
        raise FileValidationError("Image content must be JPEG, PNG, or WebP.")
    if extension not in FORMAT_EXTENSIONS[image_format]:
        raise FileValidationError(
            "Image extension does not match its content."
        )

    filename = f"{uuid.uuid4().hex}{extension}"
    destination = Path(UPLOAD_DIR) / filename
    destination.write_bytes(data)
    return destination


def delete_expired_uploads(now: float | None = None) -> int:
    cutoff = (now if now is not None else time.time()) - (
        DOUBT_RETENTION_DAYS * 24 * 60 * 60
    )
    deleted = 0

    for path in Path(UPLOAD_DIR).iterdir():
        if (
            path.is_file()
            and path.suffix.lower() in ALLOWED_EXTENSIONS
            and path.stat().st_mtime < cutoff
        ):
            path.unlink(missing_ok=True)
            deleted += 1

    return deleted
