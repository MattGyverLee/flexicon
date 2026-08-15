#
#   test_lexentry_duplicate.py
#
#   Class: TestLexEntryDuplicateDeep
#          Regression coverage for issue #31:
#          LexEntryOperations.Duplicate(entry, deep=True) raised
#          AttributeError because _copy_sense_content in
#          LexSenseOperations called `.CopyAlternatives` on
#          duplicate.Source -- a single-string ITsString field that
#          has no multistring methods. The fix replaces the multistring
#          copy with a direct ITsString assignment.
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


class TestLexEntryDuplicateDeep:
    """
    Coverage for the deep-Duplicate path through _copy_sense_content
    after the issue #31 fix. The bug surfaced specifically when the
    duplicate code reached the Source field, which is ITsString and
    has no CopyAlternatives. The test creates an entry with a Source
    value set, duplicates it deep=True, and asserts no AttributeError.
    """

    def test_duplicate_deep_does_not_raise_on_source_field(
        self, writable_project
    ):
        """
        Direct reproducer from #31's stack trace:
            entry = leops.Find("some-stem")
            new_entry = leops.Duplicate(entry, deep=True)  # crashed here

        After the fix, Duplicate must complete without AttributeError
        even when the source sense has a non-empty Source field.
        """
        lexeme = "qZ_dup_source_regression"

        # Pre-clean: remove any leftover from a previous run.
        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(lexeme)
        duplicate = None
        try:
            senses = list(entry.SensesOS)
            assert len(senses) >= 1, (
                "Create with create_blank_sense=True should yield 1 sense"
            )
            sense = senses[0]

            # Set Source so the _copy_sense_content path under test
            # actually copies a non-empty ITsString. SetSource itself
            # has a pre-existing bug (assigns a Python str to an
            # ITsString field and crashes), so build the ITsString
            # directly via TsStringUtils to make this test independent
            # of that other issue.
            from SIL.LCModel.Core.Text import TsStringUtils

            ws = writable_project.project.DefaultVernWs
            sense.Source = TsStringUtils.MakeString(
                "qZ-regression-source", ws
            )

            # The call that previously crashed with:
            #   AttributeError: 'ITsString' object has no attribute
            #   'CopyAlternatives'
            duplicate = writable_project.LexEntry.Duplicate(entry, deep=True)

            assert duplicate is not None, "Duplicate returned None"
            dup_senses = list(duplicate.SensesOS)
            assert len(dup_senses) >= 1, (
                "Deep duplicate did not propagate senses to the new entry"
            )
            # Source must round-trip. Read the ITsString text via the
            # raw LCM .Text property to avoid SetSource/GetSource's
            # multi-string handling (they have pre-existing quirks
            # independent of #31).
            from SIL.LCModel.Core.KernelInterfaces import ITsString

            dup_source_tss = dup_senses[0].Source
            assert dup_source_tss is not None, (
                "Duplicate's Source is None; the fix did not assign it"
            )
            dup_source_text = ITsString(dup_source_tss).Text
            assert dup_source_text == "qZ-regression-source", (
                "Source did not round-trip through deep duplicate: "
                f"got {dup_source_text!r}"
            )
        finally:
            if duplicate is not None:
                try:
                    writable_project.LexEntry.Delete(duplicate)
                except Exception:
                    pass
            try:
                writable_project.LexEntry.Delete(entry)
            except Exception:
                pass


class TestLexEntryDuplicateFields:
    """
    Issue #94: additional field coverage for LexEntryOperations.Duplicate.

    The existing test only verifies the Source field on the sense.
    The Duplicate implementation copies several entry-level fields:
    LexemeForm, CitationForm, MorphType, and (with deep=True) all
    senses. This class verifies those fields round-trip correctly and
    that the duplicate gets a new GUID distinct from the source.
    """

    def test_duplicate_copies_lexeme_form(self, writable_project):
        """
        The duplicate's LexemeForm must match the source's LexemeForm.
        """
        lexeme = "qZ_dup_lexeme_field"
        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(lexeme)
        duplicate = None
        try:
            duplicate = writable_project.LexEntry.Duplicate(entry, deep=False)
            assert duplicate is not None, "Duplicate returned None"

            src_form = writable_project.LexEntry.GetLexemeForm(entry)
            dup_form = writable_project.LexEntry.GetLexemeForm(duplicate)
            assert dup_form == src_form, (
                f"LexemeForm did not round-trip through Duplicate: "
                f"source={src_form!r}, duplicate={dup_form!r}"
            )
        finally:
            for obj in (duplicate, entry):
                if obj is not None:
                    try:
                        writable_project.LexEntry.Delete(obj)
                    except Exception:
                        pass

    def test_duplicate_copies_citation_form(self, writable_project):
        """
        The duplicate's CitationForm must match the source's CitationForm.
        Duplicate() calls new_entry.CitationForm.CopyAlternatives(...).
        """
        lexeme = "qZ_dup_citation_field"
        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(lexeme)
        duplicate = None
        try:
            # Set a non-empty citation form so we have something to
            # round-trip (empty CitationForm would always match).
            writable_project.LexEntry.SetCitationForm(
                entry, "qZ-citation-form"
            )

            duplicate = writable_project.LexEntry.Duplicate(entry, deep=False)
            assert duplicate is not None, "Duplicate returned None"

            src_cf = writable_project.LexEntry.GetCitationForm(entry)
            dup_cf = writable_project.LexEntry.GetCitationForm(duplicate)
            assert dup_cf == src_cf, (
                f"CitationForm did not round-trip through Duplicate: "
                f"source={src_cf!r}, duplicate={dup_cf!r}"
            )
        finally:
            for obj in (duplicate, entry):
                if obj is not None:
                    try:
                        writable_project.LexEntry.Delete(obj)
                    except Exception:
                        pass

    def test_duplicate_copies_morph_type(self, writable_project):
        """
        The duplicate's MorphType must match the source's MorphType.
        Duplicate() passes the morph type name to Create().
        """
        lexeme = "qZ_dup_morphtype_field"
        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        # Create as "root" (distinct from the default "stem") so the
        # assertion has a non-trivial value to compare.
        is_valid, _mt, _is_stem = writable_project.LexEntry.ValidateMorphType(
            "root"
        )
        morph_type_name = "root" if is_valid else "stem"

        entry = writable_project.LexEntry.Create(lexeme, morph_type_name)
        duplicate = None
        try:
            duplicate = writable_project.LexEntry.Duplicate(entry, deep=False)
            assert duplicate is not None, "Duplicate returned None"

            src_mt = writable_project.LexEntry.GetMorphType(entry)
            dup_mt = writable_project.LexEntry.GetMorphType(duplicate)
            assert dup_mt is not None, (
                "Duplicate has no MorphType; Duplicate() should have "
                "passed the source's morph type name to Create()"
            )
            assert dup_mt.Hvo == src_mt.Hvo, (
                "MorphType did not round-trip through Duplicate: "
                f"source HVO={src_mt.Hvo}, duplicate HVO={dup_mt.Hvo}"
            )
        finally:
            for obj in (duplicate, entry):
                if obj is not None:
                    try:
                        writable_project.LexEntry.Delete(obj)
                    except Exception:
                        pass

    def test_duplicate_deep_copies_senses(self, writable_project):
        """
        With deep=True, the duplicate must have the same number of
        senses as the source. Duplicate() iterates source_entry.SensesOS
        and calls project.Senses._deep_copy_sense_to() for each one.
        """
        lexeme = "qZ_dup_senses_field"
        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        # Create with the default blank sense (count=1), then add a
        # second sense so the count assertion is more meaningful.
        entry = writable_project.LexEntry.Create(lexeme)
        duplicate = None
        try:
            writable_project.LexEntry.AddSense(entry, "second sense")
            src_count = writable_project.LexEntry.GetSenseCount(entry)
            assert src_count >= 2, (
                "Setup failed: source entry should have at least 2 senses"
            )

            duplicate = writable_project.LexEntry.Duplicate(entry, deep=True)
            assert duplicate is not None, "Duplicate returned None"

            dup_count = writable_project.LexEntry.GetSenseCount(duplicate)
            assert dup_count == src_count, (
                f"Deep duplicate should have {src_count} senses "
                f"(same as source), but got {dup_count}"
            )
        finally:
            for obj in (duplicate, entry):
                if obj is not None:
                    try:
                        writable_project.LexEntry.Delete(obj)
                    except Exception:
                        pass

    def test_duplicate_has_new_guid(self, writable_project):
        """
        The duplicate must have a different GUID from the source.
        Factory.Create() auto-generates a new GUID; if Duplicate() ever
        accidentally copied the Guid property the two would collide.
        """
        lexeme = "qZ_dup_guid_field"
        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(lexeme)
        duplicate = None
        try:
            duplicate = writable_project.LexEntry.Duplicate(entry, deep=False)
            assert duplicate is not None, "Duplicate returned None"

            src_guid = str(writable_project.LexEntry.GetGuid(entry))
            dup_guid = str(writable_project.LexEntry.GetGuid(duplicate))
            assert dup_guid != src_guid, (
                f"Duplicate has the same GUID as the source ({src_guid}); "
                "Factory.Create() should auto-generate a fresh GUID"
            )
        finally:
            for obj in (duplicate, entry):
                if obj is not None:
                    try:
                        writable_project.LexEntry.Delete(obj)
                    except Exception:
                        pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
