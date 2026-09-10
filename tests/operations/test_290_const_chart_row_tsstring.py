#
#   test_290_const_chart_row_tsstring.py
#
#   Class: TestBareTsStringFixtureShape /
#          TestGetLabelGetNotesRouteThroughReadTsString /
#          TestSetLabelSetNotesRouteThroughMakeTsString /
#          TestCreateRoutesLabelNotesThroughMakeTsString
#          Regression coverage for issue #290: ConstChartRowOperations
#          treated IConstChartRow.Label and .Notes as IMultiString
#          fields (``.get_String(ws)`` / ``.set_String(ws, ts)``), but
#          live reflection confirmed both are BARE ITsString values
#          with no such methods -- see
#          specs/299-300-290-reorder-and-tsstring/evidence/
#          live-290-reflection.md (Q1-Q3, all CONFIRMED live) and
#          specs/299-300-290-reorder-and-tsstring/reviews/
#          cycle1-verification.md.
#
#          Six call sites (Create :132/:137, GetLabel :299, SetLabel
#          :339, GetNotes :375, SetNotes :414) previously raised
#          AttributeError live. The fix routes all six through the
#          house BaseOperations._MakeTsString / _ReadTsString adapters
#          (the same idiom already used for ILexSense.Source /
#          .ScientificName / .ImportResidue -- Category 8 same-name,
#          different-LCM-type fields).
#
#          These are mock-only regression tests (no live LCM project
#          opened, no .fwdata/.fwbackup file touched). The mock
#          IConstChartRow's Label/Notes are genuine bare ITsString
#          instances built via TsStringUtils.MakeString -- the exact
#          CLR type confirmed live -- rather than a plain Python stand-
#          in, because BaseOperations._ReadTsString's ``ITsString(tss)``
#          cast raises TypeError on anything that does not really
#          implement the interface ("object does not implement
#          ITsString"), so a duck-typed fake cannot exercise the real
#          getter/setter code paths. TsStringUtils.MakeString needs only
#          the loaded SIL.LCModel assembly, not an open project -- it is
#          used the same way, unmarked, elsewhere in this suite (e.g.
#          tests/test_lcm_api_real.py, tests/test_lcm_direct.py). Every
#          test still asserts the mock genuinely lacks get_String /
#          set_String, so a regression back to the IMultiString-shaped
#          call pattern fails loudly with AttributeError.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


def _require_lcm():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")


# --- Minimal write-path scaffolding -----------------------------------
#
# ConstChartRowOperations.Create/SetLabel/SetNotes call
# _EnsureWriteEnabled(), _TransactionCM(), and (Create only) a
# ServiceLocator-backed factory. None of these need a live LcmCache --
# only enough surface to let execution reach the Label/Notes
# assignment this issue is about.


class _FakeTransaction:
    """No-op context manager standing in for the Phase 1
    (_FLExTransaction) leg of _NestingAwareTransaction."""

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        return False


class _MockServiceLocator:
    def __init__(self, factory):
        self._factory = factory

    def GetService(self, service_type):
        return self._factory


class _MockRowFactory:
    """Stand-in for IConstChartRowFactory -- always hands back the
    caller-supplied row, so tests control its Label/Notes directly."""

    def __init__(self, row):
        self._row = row

    def Create(self):
        return self._row


class _MockLcmCache:
    """Stand-in for FLExProject.project (the LcmCache-shaped object)."""

    def __init__(self, row):
        self.DefaultAnalWs = 1
        self.ServiceLocator = _MockServiceLocator(_MockRowFactory(row))


class _MockFLExProject:
    """
    Stand-in for a write-enabled FLExProject in Phase 1 (non-undoable)
    mode -- just enough surface for Create()/SetLabel()/SetNotes() to
    run without a live LCM session.
    """

    def __init__(self, row=None):
        self.writeEnabled = True
        self._undoable = False
        self.project = _MockLcmCache(row)

    def Transaction(self, label):
        return _FakeTransaction()

    def _FLExProject__WSHandle(self, language_tag_or_handle, default_ws):
        # Mirrors FLExProject.__WSHandle's int-passthrough branch --
        # every test here already passes a resolved int handle.
        if language_tag_or_handle is None:
            return default_ws
        return language_tag_or_handle


class _MockRowsOS(list):
    """Stand-in for IDsConstChart.RowsOS -- an owning sequence exposing
    .Add(), not a plain list."""

    def Add(self, item):
        self.append(item)


class _MockConstChart:
    def __init__(self):
        self.RowsOS = _MockRowsOS()


class _MockConstChartRow:
    """
    Stand-in for IConstChartRow. Label/Notes default to a genuine bare
    ITsString (built the same way the fixed Create() path builds them)
    so both read and write sides can be exercised without a live LCM
    project. Deliberately has no get_String/set_String -- see module
    docstring.
    """

    def __init__(self):
        from SIL.LCModel.Core.Text import TsStringUtils

        self.Label = TsStringUtils.MakeString("", 1)
        self.Notes = TsStringUtils.MakeString("", 1)
        self.CellsOS = []


def _make_ops(row=None):
    from flexicon.code.Discourse.ConstChartRowOperations import (
        ConstChartRowOperations,
    )

    project = _MockFLExProject(row)
    return ConstChartRowOperations(project)


class TestBareTsStringFixtureShape:
    """
    Guards the mock's own shape: Label/Notes must NOT expose
    get_String/set_String -- that is precisely the IMultiString-shaped
    surface issue #290 found missing live (dir() on the real
    IConstChartRow.Label/.Notes has 29 members, none named
    get_String/set_String).
    """

    def test_label_has_no_get_or_set_string(self):
        _require_lcm()
        row = _MockConstChartRow()
        assert not hasattr(row.Label, "get_String"), (
            "test setup error: mock Label must not expose get_String -- "
            "that is precisely the missing method issue #290 found live"
        )
        assert not hasattr(row.Label, "set_String"), (
            "test setup error: mock Label must not expose set_String -- "
            "that is precisely the missing method issue #290 found live"
        )

    def test_notes_has_no_get_or_set_string(self):
        _require_lcm()
        row = _MockConstChartRow()
        assert not hasattr(row.Notes, "get_String"), (
            "test setup error: mock Notes must not expose get_String -- "
            "that is precisely the missing method issue #290 found live"
        )
        assert not hasattr(row.Notes, "set_String"), (
            "test setup error: mock Notes must not expose set_String -- "
            "that is precisely the missing method issue #290 found live"
        )

    def test_old_get_string_pattern_raises_attributeerror(self):
        """
        Direct falsifier: calling the OLD buggy pattern
        (``field.get_String(ws)``) on this mock raises AttributeError,
        exactly as it does live. This is what made GetLabel/GetNotes
        crash before the fix.
        """
        _require_lcm()
        row = _MockConstChartRow()
        with pytest.raises(AttributeError):
            row.Label.get_String(1)

    def test_old_set_string_pattern_raises_attributeerror(self):
        """
        Direct falsifier for the write side: the OLD buggy pattern
        (``field.set_String(ws, ts)``) also raises AttributeError.
        This is what made Create()/SetLabel()/SetNotes() crash before
        the fix.
        """
        _require_lcm()
        row = _MockConstChartRow()
        with pytest.raises(AttributeError):
            row.Label.set_String(1, row.Label)


class TestGetLabelGetNotesRouteThroughReadTsString:
    """
    GetLabel/GetNotes must read via BaseOperations._ReadTsString
    (``self._ReadTsString(row.Label)``), never
    ``row.Label.get_String(ws)`` -- issue #290.
    """

    def test_get_label_reads_bare_tsstring_text(self):
        _require_lcm()
        from SIL.LCModel.Core.Text import TsStringUtils

        row = _MockConstChartRow()
        row.Label = TsStringUtils.MakeString("Verse 1", 1)

        ops = _make_ops()
        assert ops.GetLabel(row) == "Verse 1"

    def test_get_notes_reads_bare_tsstring_text(self):
        _require_lcm()
        from SIL.LCModel.Core.Text import TsStringUtils

        row = _MockConstChartRow()
        row.Notes = TsStringUtils.MakeString("Complex clause", 1)

        ops = _make_ops()
        assert ops.GetNotes(row) == "Complex clause"

    def test_get_label_empty_string_when_unset(self):
        """
        GetLabel on an unset (empty-text) bare ITsString must return
        "" -- not None, not a raw ITsString.
        """
        _require_lcm()
        row = _MockConstChartRow()  # Label = MakeString("", 1)

        ops = _make_ops()
        value = ops.GetLabel(row)
        assert isinstance(value, str)
        assert value == ""

    def test_get_notes_empty_string_when_unset(self):
        _require_lcm()
        row = _MockConstChartRow()

        ops = _make_ops()
        value = ops.GetNotes(row)
        assert isinstance(value, str)
        assert value == ""


class TestSetLabelSetNotesRouteThroughMakeTsString:
    """
    SetLabel/SetNotes must assign via BaseOperations._MakeTsString
    (``row.Label = self._MakeTsString(text, wsHandle)``), never
    ``row.Label.set_String(ws, ts)`` -- issue #290.
    """

    def test_set_label_round_trips_through_get_label(self):
        _require_lcm()
        row = _MockConstChartRow()
        ops = _make_ops()

        ops.SetLabel(row, "Verse 1a")

        assert ops.GetLabel(row) == "Verse 1a"
        # The field SetLabel wrote is still a bare ITsString -- proves
        # the write went through property assignment, not set_String.
        assert not hasattr(row.Label, "get_String")
        assert not hasattr(row.Label, "set_String")

    def test_set_notes_round_trips_through_get_notes(self):
        _require_lcm()
        row = _MockConstChartRow()
        ops = _make_ops()

        ops.SetNotes(row, "Subject-predicate structure")

        assert ops.GetNotes(row) == "Subject-predicate structure"
        assert not hasattr(row.Notes, "get_String")
        assert not hasattr(row.Notes, "set_String")

    def test_set_label_can_clear_to_empty(self):
        _require_lcm()
        row = _MockConstChartRow()
        ops = _make_ops()

        ops.SetLabel(row, "Verse 1a")
        ops.SetLabel(row, "")

        assert ops.GetLabel(row) == ""


class TestCreateRoutesLabelNotesThroughMakeTsString:
    """
    Create() must assign new_row.Label / new_row.Notes via
    _MakeTsString, never ``new_row.Label.set_String(...)`` -- issue
    #290.
    """

    def test_create_with_label_and_notes(self):
        _require_lcm()
        row = _MockConstChartRow()
        chart = _MockConstChart()
        ops = _make_ops(row=row)

        created = ops.Create(chart, label="Verse 2", notes="A note")

        assert created is row
        assert row in chart.RowsOS
        assert ops.GetLabel(created) == "Verse 2"
        assert ops.GetNotes(created) == "A note"
        assert not hasattr(created.Label, "get_String")
        assert not hasattr(created.Label, "set_String")
        assert not hasattr(created.Notes, "get_String")
        assert not hasattr(created.Notes, "set_String")

    def test_create_without_label_or_notes_leaves_fields_empty(self):
        """
        Create()'s ``if label:`` / ``if notes:`` guards are falsy for
        the default empty string, so no _MakeTsString call happens at
        all for this branch -- this is the branch that was safe from
        the line 132/137 crash even before the fix (Q1 in the live
        reflection evidence). Pinned here so it stays safe.
        """
        _require_lcm()
        row = _MockConstChartRow()
        chart = _MockConstChart()
        ops = _make_ops(row=row)

        created = ops.Create(chart)

        assert created is row
        assert ops.GetLabel(created) == ""
        assert ops.GetNotes(created) == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
