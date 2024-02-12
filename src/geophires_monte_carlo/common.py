import logging
import sys

_geophires_monte_carlo_logger = None


def _get_logger():
    global _geophires_monte_carlo_logger
    if _geophires_monte_carlo_logger is None:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(logging.Formatter(fmt='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

        _geophires_monte_carlo_logger = logging.getLogger(__name__)
        _geophires_monte_carlo_logger.setLevel(logging.INFO)
        _geophires_monte_carlo_logger.addHandler(sh)

    return _geophires_monte_carlo_logger
