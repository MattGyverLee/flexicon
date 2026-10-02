# -*- coding: utf-8 -*-
#
#   flexicon.code.Shared.ws_change_log
#
#   Producer attribution for the writing-system change log
#   (WritingSystemStore/idchangelog.xml).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#
"""
Stamp ``Producer`` / ``ProducerVersion`` on writing-system change-log entries.

Every ``<Add>`` / ``<Delete>`` / ``<Change>`` entry in
``WritingSystemStore/idchangelog.xml`` carries a ``Producer`` and
``ProducerVersion`` attribute. libpalaso fills them in from
``Assembly.GetEntryAssembly()``, which is ``null`` when the host process is
Python (the entry assembly is native ``python.exe``), so every entry written
through flexicon reads ``Producer="???" ProducerVersion="unknown"`` -- see
issue #608. libpalaso exposes no setter for this, so
``install_producer_stamp()`` slips a thin pass-through
``IWritingSystemChangeLogDataMapper`` in front of the real one. It rewrites
only the unattributed (``"???"``) events and delegates everything else, so
entries written by FieldWorks (or any other producer) are never touched.
"""

import logging

logger = logging.getLogger(__name__)

# libpalaso's fallback when GetEntryAssembly() is null.
_UNKNOWN_PRODUCER = "???"

_mapper_class = None


def _build_mapper_class():
    """Define (once) the Python-implemented IWritingSystemChangeLogDataMapper."""
    global _mapper_class
    if _mapper_class is not None:
        return _mapper_class

    from SIL.WritingSystems import IWritingSystemChangeLogDataMapper

    class ProducerStampingMapper(IWritingSystemChangeLogDataMapper):
        """Pass-through mapper that attributes unattributed events."""

        __namespace__ = "Flexicon.Interop"

        def __init__(self, inner, producer, producer_version):
            self._inner = inner
            self._producer = producer
            self._producer_version = producer_version

        def _stamp(self, event):
            if event.Producer != _UNKNOWN_PRODUCER:
                return
            # The Producer/ProducerVersion setters are non-public.
            t = event.GetType()
            while t is not None and t.Name != "WritingSystemLogEvent":
                t = t.BaseType
            t.GetProperty("Producer").GetSetMethod(True).Invoke(
                event, [self._producer])
            t.GetProperty("ProducerVersion").GetSetMethod(True).Invoke(
                event, [self._producer_version])

        # IWritingSystemChangeLogDataMapper
        def Read(self, log):
            self._inner.Read(log)

        def Write(self, log):
            # Full rewrite (used when the log file does not exist yet).
            for event in log.Events:
                self._stamp(event)
            self._inner.Write(log)

        def AppendEvent(self, event):
            self._stamp(event)
            self._inner.AppendEvent(event)

        # pythonnet needs the accessor methods spelled out for interface
        # properties.
        def get_FilePath(self):
            return self._inner.FilePath

        def set_FilePath(self, value):
            self._inner.FilePath = value

    _mapper_class = ProducerStampingMapper
    return _mapper_class


def install_producer_stamp(lcm_cache, producer, producer_version):
    """
    Make writing-system change-log entries written through ``lcm_cache``
    carry the given producer name and version.

    Best effort: this reaches into libpalaso internals (the change log's
    private data mapper), so any failure is logged and swallowed -- opening a
    project must never fail because of log attribution. Idempotent.

    Args:
        lcm_cache: the open ``LcmCache``.
        producer (str): name to record (e.g. ``"flexicon"``).
        producer_version (str): version to record (e.g. ``"4.11.0"``).

    Returns:
        bool: True if the stamp is installed, False if it could not be.
    """
    try:
        from System.Reflection import BindingFlags

        flags = BindingFlags.Instance | BindingFlags.NonPublic | BindingFlags.Public
        store = lcm_cache.ServiceLocator.WritingSystemManager.WritingSystemStore

        field = None
        t = store.GetType()
        while t is not None and field is None:
            field = t.GetField("_changeLog", flags)
            t = t.BaseType
        if field is None:
            logger.debug("Writing-system repository has no _changeLog field.")
            return False
        change_log = field.GetValue(store)
        if change_log is None:
            return False

        mapper_field = change_log.GetType().GetField("_dataMapper", flags)
        if mapper_field is None:
            logger.debug("Writing-system change log has no _dataMapper field.")
            return False
        current = mapper_field.GetValue(change_log)
        if current is None:
            return False

        cls = _build_mapper_class()
        if current.GetType().FullName == "Flexicon.Interop.ProducerStampingMapper":
            return True  # already installed
        mapper_field.SetValue(change_log, cls(current, producer, producer_version))
        return True
    except Exception as exc:  # noqa: BLE001 - best effort, see docstring
        logger.warning(
            "Could not set writing-system change-log producer to %r: %s",
            producer, exc)
        return False
