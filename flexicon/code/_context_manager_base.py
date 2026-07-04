#
#   _context_manager_base.py
#
#   Class: _ContextManagerBase
#          Base class for context managers with consistent logging.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import logging


class _ContextManagerBase:
    """Base class for transaction & undoable operation managers with consistent logging.

    Provides common logging patterns for context managers that interact with FLEx projects,
    ensuring consistent log message formatting with context labels.
    """

    def __init__(self, project, label: str) -> None:
        """
        Initialize context manager base.

        Args:
            project:  The FLExProject instance
            label:    Human-readable description (for logging)
        """
        self._project = project
        self._label = label
        self._logger = logging.getLogger(self.__class__.__module__)

    def _log_debug(self, msg: str) -> None:
        """Log debug message with context label.

        Args:
            msg: The message to log
        """
        self._logger.debug(f"{self.__class__.__name__} '{self._label}': {msg}")

    def _log_warning(self, msg: str) -> None:
        """Log warning message with context label.

        Args:
            msg: The message to log
        """
        self._logger.warning(f"{self.__class__.__name__} '{self._label}': {msg}")

    def _log_error(self, msg: str) -> None:
        """Log error message with context label.

        Args:
            msg: The message to log
        """
        self._logger.error(f"{self.__class__.__name__} '{self._label}': {msg}")
