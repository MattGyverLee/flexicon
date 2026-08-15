#
#   test_set_pos_msa_dispatch.py
#
#   Class: TestSetPartOfSpeechMsaDispatch
#          Regression coverage for issue #33: LexSenseOperations
#          .SetPartOfSpeech unconditionally created MoStemMsa even
#          when the entry's morph type was prefix/suffix/infix/
#          circumfix. The HermitCrab parser then rejected the affix
#          because inflectional templates only accept MoInflAffMsa.
#
#          The fix dispatches the MSA factory choice on the entry's
#          morph type:
#              - stem morphs       -> IMoStemMsa
#              - affix morphs      -> IMoInflAffMsa (parser-ready,
#                                     matching FLEx UI default)
#          When the existing MSA already matches the family (e.g.
#          MoDerivAffMsa on an affix entry), only PartOfSpeechRA is
#          updated -- the specific MSA subtype is preserved.
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


def _first_pos(project):
    """Return any existing IPartOfSpeech in the project, or None."""
    for p in project.POS.GetAll():
        return p
    return None


class TestSetPartOfSpeechMsaDispatch:
    """
    Coverage for the MSA-family dispatch in SetPartOfSpeech.

    Each test creates an entry of a specific morph type, calls
    SetPartOfSpeech, and inspects the resulting MSA's ClassName.
    Before the fix, every entry got an MoStemMsa regardless of morph
    type; after the fix the family matches the morph type and the
    affix subtype is preserved across repeated calls.
    """

    def test_stem_entry_gets_mo_stem_msa(self, writable_project):
        """
        SetPartOfSpeech on a stem entry must produce MoStemMsa. This
        is the unchanged baseline -- the fix must not regress stems.
        """
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values to assign in this project")

        lexeme = "qZ_stem_msa_baseline"
        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(lexeme, morph_type_name="stem")
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(sense, pos)

            msa = sense.MorphoSyntaxAnalysisRA
            assert msa is not None, (
                "SetPartOfSpeech did not assign a MorphoSyntaxAnalysisRA"
            )
            assert msa.ClassName == "MoStemMsa", (
                f"Stem entry got wrong MSA class: {msa.ClassName} "
                "(expected MoStemMsa)"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_prefix_entry_gets_mo_infl_aff_msa(self, writable_project):
        """
        Direct issue #33 reproducer. Before the fix this would have
        produced MoStemMsa, leaving the affix unusable by the parser.
        """
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values to assign in this project")

        lexeme = "qZ_prefix_msa_fix"
        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(
            lexeme, morph_type_name="prefix"
        )
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(sense, pos)

            msa = sense.MorphoSyntaxAnalysisRA
            assert msa is not None, (
                "SetPartOfSpeech did not assign a MorphoSyntaxAnalysisRA"
            )
            assert msa.ClassName == "MoInflAffMsa", (
                f"Prefix entry got wrong MSA class: {msa.ClassName} "
                "(expected MoInflAffMsa; this is exactly the #33 bug)"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_suffix_entry_gets_mo_infl_aff_msa(self, writable_project):
        """Same as prefix, for suffix morph type."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values to assign in this project")

        lexeme = "qZ_suffix_msa_fix"
        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(
            lexeme, morph_type_name="suffix"
        )
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(sense, pos)

            msa = sense.MorphoSyntaxAnalysisRA
            assert msa.ClassName == "MoInflAffMsa", (
                f"Suffix entry got wrong MSA class: {msa.ClassName}"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_setpos_idempotent_on_affix(self, writable_project):
        """
        Calling SetPartOfSpeech twice on an affix entry must NOT
        churn the MSA type. The second call's existing MSA is already
        MoInflAffMsa, so the wrapper should hit the family-matches
        branch and just update PartOfSpeechRA.
        """
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values to assign in this project")

        lexeme = "qZ_affix_idempotent"
        existing = writable_project.LexEntry.Find(lexeme)
        if existing is not None:
            writable_project.LexEntry.Delete(existing)

        entry = writable_project.LexEntry.Create(
            lexeme, morph_type_name="prefix"
        )
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(sense, pos)
            msa_first = sense.MorphoSyntaxAnalysisRA
            assert msa_first.ClassName == "MoInflAffMsa"

            # Re-apply: family already matches, should reuse same MSA.
            writable_project.Senses.SetPartOfSpeech(sense, pos)
            msa_second = sense.MorphoSyntaxAnalysisRA
            assert msa_second.ClassName == "MoInflAffMsa", (
                f"Second SetPartOfSpeech churned MSA type to "
                f"{msa_second.ClassName}"
            )
            assert msa_first.Hvo == msa_second.Hvo, (
                "Second SetPartOfSpeech created a new MSA instead of "
                "reusing the family-matching existing one "
                f"(first Hvo={msa_first.Hvo}, second Hvo={msa_second.Hvo})"
            )
        finally:
            writable_project.LexEntry.Delete(entry)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
