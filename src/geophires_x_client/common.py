import logging
import sys

_geophires_x_client_loggers_by_name = {}


def _get_logger(logger_name=None):
    if logger_name is None:
        logger_name = __name__

    global _geophires_x_client_loggers_by_name
    if logger_name not in _geophires_x_client_loggers_by_name:
        sh = logging.StreamHandler(sys.stdout)
        sh.setLevel(logging.INFO)
        sh.setFormatter(logging.Formatter(fmt='[%(asctime)s][%(levelname)s] %(message)s', datefmt='%Y-%m-%d %H:%M:%S'))

        _geophires_x_client_loggers_by_name[logger_name] = logging.getLogger(logger_name)
        _geophires_x_client_loggers_by_name[logger_name].addHandler(sh)

    return _geophires_x_client_loggers_by_name[logger_name]
