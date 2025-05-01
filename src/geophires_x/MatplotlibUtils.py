"""
Workarounds for intermittent Windows GitHub Actions failures - see https://github.com/NREL/GEOPHIRES-X/issues/365
"""

from __future__ import annotations

import logging
import os
from typing import Any

from matplotlib import pyplot as plt

_logger = logging.getLogger(__name__)


def plt_show(**kw_args):
    try:
        plt.show(**kw_args)
    except Exception as e:
        _handle_tcl_error_on_windows_github_actions(e)


def plt_subplot() -> Any:
    try:
        return plt.subplot()
    except Exception as e:
        _handle_tcl_error_on_windows_github_actions(e)


def plt_subplots(**kw_args) -> Any:
    try:
        return plt.subplots(**kw_args)
    except Exception as e:
        _handle_tcl_error_on_windows_github_actions(e)


def _handle_tcl_error_on_windows_github_actions(e) -> None:
    # Can't import TclError directly since Python is not configured for Tk on all systems
    is_tcl_error = e.__class__.__name__ == 'TclError'

    if os.name == 'nt' and 'TOXPYTHON' in os.environ:
        _logger.warning(f'Ignoring TclError when attempting to show plot '
                        f'since we appear to be running on Windows in GitHub Actions ({str(e)})')
    else:
        raise e
