from fastapi import APIRouter
from app.utils.responses import success

router = APIRouter(prefix="/health", tags=["health"])


@router.get("")
async def health():
    return success({"status": "ok"})
