#
#   test_issue330_setdateofevent_gendate.py
#
#   Class: TestIssue330GenDateStringFromInput,
#          TestIssue330SetDateOfEventAssignment
#          Offline regression for issue #330: SetDateOfEvent assigned a
#          System.DateTime to IRnGenericRec.DateOfEvent (GenDate), raising
#          TypeError on every call.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import sys
from contextlib import contextmanager
from types import SimpleNamespace

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    import clr  # noqa: F401
except RuntimeError:
    pytest.skip(
        "pythonnet/.NET runtime unavailable on this host",
        allow_module_level=True,
    )

from System import DateTime  # noqa: E402

from flexicon.code.FLExProject import FP_ParameterError  # noqa: E402
from flexicon.code.Notebook.DataNotebookOperations import (  # noqa: E402
    DataNotebookOperations,
)


class TestIssue330GenDateStringFromInput:
    def test_date_only_string(self):
        assert (
            DataNotebookOperations._GenDateStringFromInput("2024-01-15")
            == "2024-01-15"
        )

    def test_date_time_string(self):
        assert (
            DataNotebookOperations._GenDateStringFromInput("2024-01-15 14:30:00")
            == "2024-01-15 14:30:00"
        )

    def test_datetime_object_date_only(self):
        dt = DateTime(2024, 1, 15, 0, 0, 0)
        assert DataNotebookOperations._GenDateStringFromInput(dt) == "2024-01-15"

    def test_datetime_object_with_time(self):
        dt = DateTime(2024, 1, 15, 14, 30, 0)
        assert (
            DataNotebookOperations._GenDateStringFromInput(dt)
            == "2024-01-15 14:30:00"
        )

    def test_invalid_string_raises_fp_parameter_error(self):
        with pytest.raises(FP_ParameterError, match="Invalid date format"):
            DataNotebookOperations._GenDateStringFromInput("not-a-date")


class TestIssue330SetDateOfEventAssignment:
    @staticmethod
    @contextmanager
    def _recording_transaction(_label):
        yield

    def test_assigns_string_not_datetime(self):
        record = SimpleNamespace(DateOfEvent=None)
        ops = DataNotebookOperations.__new__(DataNotebookOperations)
        ops.writeEnabled = True
        ops._EnsureWriteEnabled = lambda: None
        ops._ValidateParam = lambda *_a, **_k: None
        ops.__GetRecordObject = lambda _x: record
        ops._TransactionCM = self._recording_transaction

        ops.SetDateOfEvent(record, "2024-06-01")

        assert record.DateOfEvent == "2024-06-01"
        assert not isinstance(record.DateOfEvent, DateTime)

    def test_datetime_input_becomes_string(self):
        record = SimpleNamespace(DateOfEvent=None)
        ops = DataNotebookOperations.__new__(DataNotebookOperations)
        ops.writeEnabled = True
        ops._EnsureWriteEnabled = lambda: None
        ops._ValidateParam = lambda *_a, **_k: None
        ops.__GetRecordObject = lambda _x: record
        ops._TransactionCM = self._recording_transaction

        ops.SetDateOfEvent(record, DateTime(2024, 6, 1, 9, 15, 0))

        assert record.DateOfEvent == "2024-06-01 09:15:00"
        assert not isinstance(record.DateOfEvent, DateTime)
