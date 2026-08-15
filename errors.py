"""
Surfacing failures instead of swallowing them.

The code had fifteen `except: pass`. Some are legitimate — closing an
audio device that already died — but others hid failures the user needed
to know about: a render that failed left a sound silently ignoring its own
settings, with no way to tell why.

Anything a user would notice goes through report(): it lands in a log file
and on a Qt signal the main window turns into a dismissable banner. Purely
defensive suppressions keep their bare `pass`.
"""

import traceback

from PySide6.QtCore import QObject, Signal

import paths

LOG_NAME = "errors.log"


class _Reporter(QObject):
    reported = Signal(str)


reporter = _Reporter()


def report(message, exc=None):
    """Records a user-visible failure and publishes it. Never raises: an
    error path that can itself fail is worse than the original error."""
    detail = message
    if exc is not None:
        detail = f"{message}\n{''.join(traceback.format_exception(exc))}"

    try:
        with open(paths.log_path(LOG_NAME), "a", encoding="utf-8") as f:
            f.write(detail + "\n\n")
    except OSError:
        pass

    try:
        reporter.reported.emit(message)
    except Exception:
        pass
