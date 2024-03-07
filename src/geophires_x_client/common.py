import logging
import sys

_geophires_x_client_logger = None


def _get_logger(logger_name=None):
    global _geophires_x_client_logger
    if _geophires_x_client_logger is None:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(logging.Formatter(fmt='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

        if logger_name is None:
            logger_name = __name__

        _geophires_x_client_logger = logging.getLogger(logger_name)
        _geophires_x_client_logger.addHandler(sh)

    return _geophires_x_client_logger
