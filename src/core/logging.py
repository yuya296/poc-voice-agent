from loguru import logger
import sys


def setup_logging(level: str = "INFO", json_format: bool = False):
    logger.remove()  # デフォルトハンドラを削除
    
    if json_format:
        logger.add(
            sys.stderr,
            level=level,
            serialize=True,
            format="{time} | {level} | {name}:{function}:{line} | {message}"
        )
    else:
        logger.add(
            sys.stderr,
            level=level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>"
        )
    
    return logger