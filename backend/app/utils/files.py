import os
from pathlib import Path
from uuid import uuid4
import aiofiles
from fastapi import UploadFile, HTTPException, status
from app.core.config import settings


def sanitize_filename(filename: str) -> str:
    keep = "._-"
    return "".join(c for c in filename if c.isalnum() or c in keep).strip("._")


async def save_upload_file(upload: UploadFile, subdir: str, allowed_types: list[str] | None = None) -> str:
    if allowed_types and upload.content_type not in allowed_types:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid file type")

    ext = os.path.splitext(upload.filename or "")[1]
    safe_name = f"{uuid4().hex}{ext}"
    dest_dir = Path(settings.UPLOAD_DIR) / subdir
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_path = dest_dir / safe_name

    max_size = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    size = 0
    async with aiofiles.open(dest_path, "wb") as out:
        while True:
            chunk = await upload.read(1024 * 1024)
            if not chunk:
                break
            size += len(chunk)
            if size > max_size:
                raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail="File too large")
            await out.write(chunk)

    return str(dest_path)
