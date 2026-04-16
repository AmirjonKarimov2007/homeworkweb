from typing import Any


def success(data: Any = None, message: str = "OK") -> dict:
    return {"success": True, "message": message, "data": data}


def error(message: str, code: str | None = None) -> dict:
    payload = {"success": False, "message": message}
    if code:
        payload["code"] = code
    return payload
