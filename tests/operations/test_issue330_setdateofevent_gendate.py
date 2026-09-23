#
#   test_issue330_setdateofevent_gendate.py
#
#   Class: TestIssue330GenDateFromInput,
#          TestIssue330SetDateOfEventAssignment
#          Offline regression for issue #330: SetDateOfEvent assigned a
#          System.DateTime (and, after #376, a str) to
#          IRnGenericRec.DateOfEvent (GenDate), raising TypeError on every
#          call. Live proof: test_issue330_setdateofevent_live.py.
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
from flexicon.code.Shared.gendate_utils import gendate_from_input  # noqa: E402
from SIL.LCModel.Core.Cellar import GenDate  # noqa: E402


def _ymd(gd):
    return (gd.Year, gd.Month, gd.Day)


class TestIssue330GenDateFromInput:
    def test_date_only_string(self):
        gd = gendate_from_input("2024-01-15")
        assert isinstance(gd, GenDate)
        assert _ymd(gd) == (2024, 1, 15)
        assert gd.Precision == GenDate.PrecisionType.Exact
        assert gd.IsAD

    def test_date_time_string_drops_time(self):
        assert _ymd(gendate_from_input("2024-01-15 14:30:00")) == (2024, 1, 15)

    def test_datetime_object(self):
        dt = DateTime(2024, 1, 15, 14, 30, 0)
        assert _ymd(gendate_from_input(dt)) == (2024, 1, 15)

    def test_gendate_passes_through(self):
        gd = GenDate(GenDate.PrecisionType.Approximate, 5, 6, 1999, True)
        assert gendate_from_input(gd) == gd

    def test_empty_string_only_when_allowed(self):
        assert gendate_from_input("  ", allow_empty=True).IsEmpty
        with pytest.raises(FP_ParameterError, match="Invalid date format"):
            gendate_from_input("")

    def test_invalid_string_raises_fp_parameter_error(self):
        with pytest.raises(FP_ParameterError, match="Invalid date format"):
            gendate_from_input("not-a-date")

    def test_unsupported_type_raises_fp_parameter_error(self):
        with pytest.raises(FP_ParameterError, match="Invalid date type"):
            gendate_from_input(20240115)


class TestIssue330SetDateOfEventAssignment:
    @staticmethod
    @contextmanager
    def _recording_transaction(_label):
        yield

    def _ops_for(self, record):
        ops = DataNotebookOperations.__new__(DataNotebookOperations)
        ops._EnsureWriteEnabled = lambda: None
        ops._ValidateParam = lambda *_a, **_k: None
        # Name-mangled private resolver: set it under the owning class's
        # mangled name, or the real one runs and needs ops.project.
        ops._DataNotebookOperations__GetRecordObject = lambda _x: record
        ops._TransactionCM = self._recording_transaction
        return ops

    def test_string_input_assigns_gendate(self):
        record = SimpleNamespace(DateOfEvent=None)
        self._ops_for(record).SetDateOfEvent(record, "2024-06-01")

        assert isinstance(record.DateOfEvent, GenDate)
        assert _ymd(record.DateOfEvent) == (2024, 6, 1)

    def test_datetime_input_assigns_gendate(self):
        record = SimpleNamespace(DateOfEvent=None)
        self._ops_for(record).SetDateOfEvent(record, DateTime(2024, 6, 1, 9, 15, 0))

        assert isinstance(record.DateOfEvent, GenDate)
        assert _ymd(record.DateOfEvent) == (2024, 6, 1)
