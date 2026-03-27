"""Debug logging setup for kpii."""

import logging


def get_logger(name: str) -> logging.Logger:
    """kpii 네임스페이스 로거 반환."""
    logger = logging.getLogger(f"kpii.{name}")
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(
            logging.Formatter("[%(name)s] %(levelname)s: %(message)s")
        )
        logger.addHandler(handler)
        logger.setLevel(logging.DEBUG)
    return logger
