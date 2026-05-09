from slowapi import Limiter
from slowapi.util import get_remote_address
from app.core.config import settings


def _noop_decorator(*args, **kwargs):
    def decorator(func):
        return func
    return decorator


limiter = Limiter(key_func=get_remote_address) if settings.RATE_LIMIT_ENABLED else None


def limit(rate: str):
    if settings.RATE_LIMIT_ENABLED and limiter:
        return limiter.limit(rate)
    return _noop_decorator()
