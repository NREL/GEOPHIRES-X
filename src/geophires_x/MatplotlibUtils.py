"""
Workarounds for intermittent Windows GitHub Actions failures - see https://github.com/NREL/GEOPHIRES-X/issues/365

TODO fix the actual Tcl/Tk installation issue (perhaps using suggestions from i.e.
https://stackoverflow.com/questions/29320039/trying-to-use-tkinter-throws-tcl-error-cant-find-a-usable-init-tcl)
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


def plt_figure(*args, **kw_args) -> Any:
    try:
        return plt.figure(*args, **kw_args)
    except Exception as e:
        _handle_tcl_error_on_windows_github_actions(e)


def _handle_tcl_error_on_windows_github_actions(e) -> None:
    # Can't import TclError directly since Python is not configured for Tk on all systems
    tcl_error_name = 'TclError'
    is_tcl_error = e.__class__.__name__ == tcl_error_name

    if is_tcl_error and os.name == 'nt' and 'TOXPYTHON' in os.environ:
        _logger.warning(f'Ignoring {tcl_error_name} when attempting to show plot '
                        f'since we appear to be running on Windows in GitHub Actions ({str(e)})')
    else:
        raise e
