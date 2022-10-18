"""Internal utilities."""

import logging
import sys


def get_logger(name: str) -> logging.Logger:
    """Get logger, with fancy format and configured for stdout."""

    logger = logging.getLogger(name)
    sh = logging.StreamHandler(sys.stdout)
    f = logging.Formatter(
        "[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s",
        datefmt=r"%d-%b-%Y %H:%M:%S",
    )
    sh.setFormatter(f)
    logger.addHandler(sh)

    return logger
