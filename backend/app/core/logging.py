import logging
from loguru import logger
from app.core.config import settings


class InterceptHandler(logging.Handler):
    def emit(self, record: logging.LogRecord) -> None:
        level = logger.level(record.levelname).name if record.levelname else record.levelno
        frame, depth = logging.currentframe(), 2
        while frame and frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1
        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging() -> None:
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(settings.LOG_LEVEL)
    logger.remove()
    logger.add(lambda msg: print(msg, end=""), level=settings.LOG_LEVEL)
