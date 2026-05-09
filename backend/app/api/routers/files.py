from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse
from pathlib import Path
from jose import JWTError
from app.core.config import settings
from app.core.security import decode_access_token

router = APIRouter(prefix="/files", tags=["files"])


def _validate_token(request: Request, token: str | None) -> None:
    auth = request.headers.get("authorization") or ""
    bearer = None
    if auth.lower().startswith("bearer "):
        bearer = auth.split(" ", 1)[1].strip()
    token_to_check = bearer or token
    if not token_to_check:
        raise HTTPException(status_code=401, detail="Unauthorized")
    try:
        decode_access_token(token_to_check)
    except JWTError:
        raise HTTPException(status_code=401, detail="Unauthorized")


@router.get("")
async def get_file(request: Request, path: str, token: str | None = None):
    _validate_token(request, token)
    base = Path(settings.UPLOAD_DIR).resolve()
    file_path = Path(path).resolve()
    if not str(file_path).startswith(str(base)):
        raise HTTPException(status_code=403, detail="Forbidden")
    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(file_path)
