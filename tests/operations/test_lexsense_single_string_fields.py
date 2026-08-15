#
#   test_lexsense_single_string_fields.py
#
#   Round-trip coverage for the three ILexSense ITsString fields:
#   Source, ScientificName, ImportResidue.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


# Every test in this module opens a real .fwdata project via the
# writable_project fixture.
pytestmark = pytest.mark.requires_live_project


_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_writable_project():
    try:
        from flexicon.code.FLExProject import FLExProject
    except Exception:
        return None
    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=True)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def writable_project():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    project = _try_open_writable_project()
    if project is None:
        pytest.skip(
            "No writable FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


class TestLexSenseSingleStringFields:
    """
    Round-trip coverage for the three single-string sense fields after
    the issue #36 fix:
      - Source         (bibliographic source / citation)
      - ScientificName (binomial nomenclature for biological entries)
      - ImportResidue  (carry-over from non-LIFT import)
    All three are ITsString on ILexSense; each had a matching pair of
    broken getter+setter that this test now pins in tree.
    """

    @pytest.mark.parametrize(
        "getter_name,setter_name,sentinel",
        [
            ("GetSource",         "SetSource",         "qZ_source_value"),
            ("GetScientificName", "SetScientificName", "qZ_scientific_name"),
            ("GetImportResidue",  "SetImportResidue",  "qZ_import_residue"),
        ],
    )
    def test_round_trip(
        self, writable_project, getter_name, setter_name, sentinel
    ):
        """
        Create an entry with a blank sense, Set the field, Get it
        back, assert equal. Before the fix, the Set call raised
        TypeError before ever touching the project.
        """
        lexeme = f"qZ_lexsense_{setter_name}_roundtrip"

        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(lexeme)
        try:
            sense = list(entry.SensesOS)[0]

            setter = getattr(writable_project.Senses, setter_name)
            getter = getattr(writable_project.Senses, getter_name)

            # The call that previously crashed with:
            #   TypeError: 'str' value cannot be converted to
            #   ...ITsString
            setter(sense, sentinel)

            got = getter(sense)
            assert got == sentinel, (
                f"{setter_name}/{getter_name} did not round-trip: "
                f"wrote {sentinel!r}, read {got!r}"
            )
        finally:
            try:
                writable_project.LexEntry.Delete(entry)
            except Exception:
                pass

    def test_get_returns_empty_string_when_unset(self, writable_project):
        """
        Get* on an unset single-string field must return "" -- not
        None, not the FLEX null marker "***". The fix's _ReadTsString
        helper normalises both None and "***".
        """
        lexeme = "qZ_lexsense_single_string_empty"

        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(lexeme)
        try:
            sense = list(entry.SensesOS)[0]
            for getter_name in (
                "GetSource", "GetScientificName", "GetImportResidue"
            ):
                getter = getattr(writable_project.Senses, getter_name)
                value = getter(sense)
                assert isinstance(value, str), (
                    f"{getter_name}() returned {type(value).__name__}; "
                    "expected str"
                )
                assert value == "", (
                    f"{getter_name}() on a fresh sense returned "
                    f"{value!r}; expected empty string"
                )
        finally:
            try:
                writable_project.LexEntry.Delete(entry)
            except Exception:
                pass


class TestLexEntrySingleStringFields:
    """
    Round-trip coverage for the ILexEntry ITsString single-string field
    surfaced by the issue #39 / #115 fix:
      - ImportResidue (carry-over from non-LIFT import; stored as ITsString)

    Before the fix, SetImportResidue assigned a Python str directly to the
    ITsString attribute (TypeError at the pythonnet boundary) and
    GetImportResidue passed the raw ITsString through
    _NormalizeMultiString (returning a COM-wrapped object instead of a
    str). The promoted BaseOperations._MakeTsString / _ReadTsString
    helpers fix both shapes.
    """

    def test_set_get_import_residue_round_trip(self, writable_project):
        """
        Set takes a Python str, Get returns a Python str equal to what
        was written. Before the fix Set raised TypeError before ever
        reaching FLEx storage.
        """
        lexeme = "qZ_lexentry_import_residue_roundtrip"
        sentinel = "<custom><field>qZ_residue_value</field></custom>"

        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(lexeme)
        try:
            writable_project.LexEntry.SetImportResidue(entry, sentinel)
            got = writable_project.LexEntry.GetImportResidue(entry)
            assert got == sentinel, (
                f"LexEntry.ImportResidue did not round-trip: "
                f"wrote {sentinel!r}, read {got!r}"
            )
        finally:
            try:
                writable_project.LexEntry.Delete(entry)
            except Exception:
                pass

    def test_get_import_residue_empty_on_fresh_entry(self, writable_project):
        """
        On an entry that has never had ImportResidue set, the getter
        must return "" -- not None, not "***", not a raw ITsString.
        """
        lexeme = "qZ_lexentry_import_residue_empty"

        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(lexeme)
        try:
            value = writable_project.LexEntry.GetImportResidue(entry)
            assert isinstance(value, str), (
                f"GetImportResidue() returned {type(value).__name__}; "
                "expected str"
            )
            assert value == "", (
                f"GetImportResidue() on a fresh entry returned "
                f"{value!r}; expected empty string"
            )
        finally:
            try:
                writable_project.LexEntry.Delete(entry)
            except Exception:
                pass


class TestBaseOperationsTsStringHelpersPromoted:
    """
    Lock the helper promotion: _MakeTsString and _ReadTsString must
    resolve to BaseOperations (not to a subclass-local re-declaration)
    when accessed from LexSenseOperations and LexEntryOperations.
    """

    def test_helpers_live_on_base_operations(self):
        """
        After promotion (issue #42), both helpers must be defined
        directly on BaseOperations -- not on either Operations
        subclass. This prevents accidental re-introduction of the
        duplicated definitions the consolidation removed.
        """
        try:
            from flexicon.code.BaseOperations import BaseOperations
            from flexicon.code.Lexicon.LexSenseOperations import (
                LexSenseOperations,
            )
            from flexicon.code.Lexicon.LexEntryOperations import (
                LexEntryOperations,
            )
        except Exception as exc:
            pytest.skip(f"flexicon imports unavailable: {exc}")

        # The helpers must exist on BaseOperations itself.
        assert "_MakeTsString" in vars(BaseOperations), (
            "_MakeTsString must be defined directly on BaseOperations"
        )
        assert "_ReadTsString" in vars(BaseOperations), (
            "_ReadTsString must be defined directly on BaseOperations"
        )

        # The helpers must NOT shadow on either subclass (would defeat
        # consolidation and re-introduce drift).
        assert "_MakeTsString" not in vars(LexSenseOperations), (
            "LexSenseOperations must not redeclare _MakeTsString"
        )
        assert "_ReadTsString" not in vars(LexSenseOperations), (
            "LexSenseOperations must not redeclare _ReadTsString"
        )
        assert "_MakeTsString" not in vars(LexEntryOperations), (
            "LexEntryOperations must not redeclare _MakeTsString"
        )
        assert "_ReadTsString" not in vars(LexEntryOperations), (
            "LexEntryOperations must not redeclare _ReadTsString"
        )

        # And the OLD name-mangled helpers must be gone from
        # LexSenseOperations -- the rename completed.
        assert not hasattr(
            LexSenseOperations, "_LexSenseOperations__MakeTsString"
        ), (
            "Old name-mangled __MakeTsString must be removed from "
            "LexSenseOperations after promotion"
        )
        assert not hasattr(
            LexSenseOperations, "_LexSenseOperations__ReadTsString"
        ), (
            "Old name-mangled __ReadTsString must be removed from "
            "LexSenseOperations after promotion"
        )

    def test_mro_resolves_helpers_through_base(self):
        """
        Both Operations subclasses must reach _MakeTsString /
        _ReadTsString via normal MRO from BaseOperations. Single-
        underscore (not double) is required for this -- double would
        trigger Python name-mangling and break subclass access.
        """
        try:
            from flexicon.code.BaseOperations import BaseOperations
            from flexicon.code.Lexicon.LexSenseOperations import (
                LexSenseOperations,
            )
            from flexicon.code.Lexicon.LexEntryOperations import (
                LexEntryOperations,
            )
        except Exception as exc:
            pytest.skip(f"flexicon imports unavailable: {exc}")

        for cls in (LexSenseOperations, LexEntryOperations):
            assert cls._MakeTsString is BaseOperations._MakeTsString, (
                f"{cls.__name__}._MakeTsString must resolve to "
                "BaseOperations._MakeTsString via MRO"
            )
            assert cls._ReadTsString is BaseOperations._ReadTsString, (
                f"{cls.__name__}._ReadTsString must resolve to "
                "BaseOperations._ReadTsString via MRO"
            )

    def test_read_tsstring_handles_none_and_null_marker(self):
        """
        _ReadTsString must collapse None to "". It cannot test ***
        collapse without an actual ITsString instance, but None handling
        is the most-load-bearing branch and is reachable without FLEx.
        """
        try:
            from flexicon.code.BaseOperations import BaseOperations
        except Exception as exc:
            pytest.skip(f"flexicon imports unavailable: {exc}")

        # Build a minimal instance without going through __init__:
        # _ReadTsString only touches the argument and self._NormalizeMultiString.
        inst = BaseOperations.__new__(BaseOperations)
        assert inst._ReadTsString(None) == ""


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
