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


def in_jupyter() -> bool:
    # Reference: https://stackoverflow.com/a/47428575
    try:
        from IPython.core import getipython  # type: ignore
    except (ImportError, ModuleNotFoundError):  # pragma: no cover
        return False

    # <class 'ipykernel.zmqshell.ZMQInteractiveShell'>
    return "zmqshell" in str(type(getipython.get_ipython()))
