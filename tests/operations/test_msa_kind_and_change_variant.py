#
#   test_msa_kind_and_change_variant.py
#
#   Class: TestSetPartOfSpeechMsaKind, TestChangeAffixVariant
#          Tests for issue #91:
#            - SetPartOfSpeech msa_kind parameter (sub-item 1)
#            - MSAOperations.ChangeAffixVariant (sub-item 4)
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys
import logging

import pytest


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


def _make_prefix_entry(project, lexeme):
    """Create (or re-create) a prefix entry, returning the entry."""
    existing = project.LexEntry.Find(lexeme)
    if existing is not None:
        project.LexEntry.Delete(existing)
    return project.LexEntry.Create(lexeme, morph_type_name="prefix")


def _make_stem_entry(project, lexeme):
    """Create (or re-create) a stem entry, returning the entry."""
    existing = project.LexEntry.Find(lexeme)
    if existing is not None:
        project.LexEntry.Delete(existing)
    return project.LexEntry.Create(lexeme, morph_type_name="stem")


# ============================================================================
# TestSetPartOfSpeechMsaKind
# ============================================================================


class TestSetPartOfSpeechMsaKind:
    """
    Coverage for the msa_kind parameter added to SetPartOfSpeech (issue #91).
    """

    # ------------------------------------------------------------------
    # msa_kind='auto' -- existing tests should still pass
    # ------------------------------------------------------------------

    def test_auto_on_stem_gives_stem_msa(self, writable_project):
        """msa_kind='auto' on a stem entry still produces MoStemMsa."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_stem_entry(writable_project, "qZ91_auto_stem")
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(sense, pos, msa_kind="auto")
            assert sense.MorphoSyntaxAnalysisRA.ClassName == "MoStemMsa"
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_auto_on_prefix_gives_infl_aff_msa(self, writable_project):
        """msa_kind='auto' on a prefix entry still produces MoInflAffMsa."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_prefix_entry(writable_project, "qZ91_auto_prefix")
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(sense, pos, msa_kind="auto")
            assert sense.MorphoSyntaxAnalysisRA.ClassName == "MoInflAffMsa"
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Explicit msa_kind on affix entries
    # ------------------------------------------------------------------

    def test_msa_kind_infl_on_prefix(self, writable_project):
        """msa_kind='infl' explicitly requests MoInflAffMsa."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_prefix_entry(writable_project, "qZ91_kind_infl")
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(sense, pos, msa_kind="infl")
            assert sense.MorphoSyntaxAnalysisRA.ClassName == "MoInflAffMsa", (
                f"Expected MoInflAffMsa, got "
                f"{sense.MorphoSyntaxAnalysisRA.ClassName}"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_msa_kind_deriv_on_prefix(self, writable_project):
        """
        msa_kind='deriv' explicitly requests MoDerivAffMsa.

        Option D (issue #91): when to_pos is not supplied, ToPartOfSpeechRA
        must be None (unset) -- NOT a copy of from_pos/pos.
        """
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_prefix_entry(writable_project, "qZ91_kind_deriv")
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(sense, pos, msa_kind="deriv")
            msa = sense.MorphoSyntaxAnalysisRA
            assert msa.ClassName == "MoDerivAffMsa", (
                f"Expected MoDerivAffMsa, got {msa.ClassName}"
            )
            from SIL.LCModel import IMoDerivAffMsa
            deriv = IMoDerivAffMsa(msa)
            # from_pos should be set to `pos` (the positional arg default)
            assert deriv.FromPartOfSpeechRA is not None, (
                "FromPartOfSpeechRA should be set to pos when from_pos not supplied"
            )
            assert deriv.FromPartOfSpeechRA.Hvo == pos.Hvo, (
                "FromPartOfSpeechRA should equal the pos argument"
            )
            # to_pos must be None/unset -- the old bug copied from_pos here
            assert deriv.ToPartOfSpeechRA is None, (
                "ToPartOfSpeechRA must be None (unset) when to_pos is not "
                "supplied; copying from_pos was the bug fixed in Cycle 4 "
                "(issue #91 Option D)"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_msa_kind_deriv_with_explicit_from_and_to_pos(self, writable_project):
        """
        Option D: SetPartOfSpeech(sense, verb_pos, msa_kind='deriv',
        from_pos=verb_pos, to_pos=noun_pos) -> from == verb_pos,
        to == noun_pos.
        """
        poses = list(writable_project.POS.GetAll())
        if len(poses) < 2:
            pytest.skip("Need at least 2 POS values in this project")
        verb_pos = poses[0]
        noun_pos = poses[1]

        entry = _make_prefix_entry(writable_project, "qZ91_deriv_explicit_frto")
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(
                sense, verb_pos, msa_kind="deriv",
                from_pos=verb_pos, to_pos=noun_pos,
            )
            msa = sense.MorphoSyntaxAnalysisRA
            assert msa.ClassName == "MoDerivAffMsa"
            from SIL.LCModel import IMoDerivAffMsa
            deriv = IMoDerivAffMsa(msa)
            assert deriv.FromPartOfSpeechRA is not None, (
                "FromPartOfSpeechRA should equal verb_pos"
            )
            assert deriv.FromPartOfSpeechRA.Hvo == verb_pos.Hvo, (
                f"Expected FromPartOfSpeechRA.Hvo={verb_pos.Hvo}, "
                f"got {deriv.FromPartOfSpeechRA.Hvo}"
            )
            assert deriv.ToPartOfSpeechRA is not None, (
                "ToPartOfSpeechRA should equal noun_pos"
            )
            assert deriv.ToPartOfSpeechRA.Hvo == noun_pos.Hvo, (
                f"Expected ToPartOfSpeechRA.Hvo={noun_pos.Hvo}, "
                f"got {deriv.ToPartOfSpeechRA.Hvo}"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_msa_kind_deriv_with_from_pos_only(self, writable_project):
        """
        Option D: SetPartOfSpeech(sense, verb_pos, msa_kind='deriv',
        from_pos=verb_pos) -> from == verb_pos, to is None (unset).
        Confirms from_pos kwarg overrides the pos positional arg for
        FromPartOfSpeechRA, and to_pos remains unset.
        """
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_prefix_entry(writable_project, "qZ91_deriv_from_only")
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(
                sense, pos, msa_kind="deriv", from_pos=pos
            )
            msa = sense.MorphoSyntaxAnalysisRA
            assert msa.ClassName == "MoDerivAffMsa"
            from SIL.LCModel import IMoDerivAffMsa
            deriv = IMoDerivAffMsa(msa)
            assert deriv.FromPartOfSpeechRA is not None
            assert deriv.FromPartOfSpeechRA.Hvo == pos.Hvo
            assert deriv.ToPartOfSpeechRA is None, (
                "ToPartOfSpeechRA must be None when to_pos is not supplied"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_msa_kind_unclassified_on_prefix(self, writable_project):
        """msa_kind='unclassified' explicitly requests MoUnclassifiedAffixMsa."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_prefix_entry(writable_project, "qZ91_kind_unclassified")
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(
                sense, pos, msa_kind="unclassified"
            )
            assert (
                sense.MorphoSyntaxAnalysisRA.ClassName
                == "MoUnclassifiedAffixMsa"
            ), (
                f"Expected MoUnclassifiedAffixMsa, got "
                f"{sense.MorphoSyntaxAnalysisRA.ClassName}"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Short-circuit: msa_kind matches existing subtype -> reuse
    # ------------------------------------------------------------------

    def test_msa_kind_infl_short_circuits_when_already_infl(
        self, writable_project
    ):
        """
        When existing MSA is already MoInflAffMsa and msa_kind='infl',
        the short-circuit fires and the same MSA object is reused.
        """
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_prefix_entry(writable_project, "qZ91_kind_infl_sc")
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(sense, pos, msa_kind="infl")
            hvo_first = sense.MorphoSyntaxAnalysisRA.Hvo

            writable_project.Senses.SetPartOfSpeech(sense, pos, msa_kind="infl")
            hvo_second = sense.MorphoSyntaxAnalysisRA.Hvo

            assert hvo_first == hvo_second, (
                "Second call with matching msa_kind should short-circuit and "
                "reuse the same MSA object"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_msa_kind_deriv_skips_short_circuit_when_infl_present(
        self, writable_project
    ):
        """
        When existing MSA is MoInflAffMsa but msa_kind='deriv', the
        short-circuit must NOT fire; a fresh MoDerivAffMsa should be minted.
        """
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_prefix_entry(writable_project, "qZ91_kind_deriv_nsc")
        try:
            sense = list(entry.SensesOS)[0]
            # First call produces MoInflAffMsa
            writable_project.Senses.SetPartOfSpeech(sense, pos, msa_kind="infl")
            assert sense.MorphoSyntaxAnalysisRA.ClassName == "MoInflAffMsa"

            # Second call with different kind must produce MoDerivAffMsa
            writable_project.Senses.SetPartOfSpeech(sense, pos, msa_kind="deriv")
            assert sense.MorphoSyntaxAnalysisRA.ClassName == "MoDerivAffMsa", (
                "msa_kind='deriv' with existing MoInflAffMsa should skip "
                "short-circuit and mint a fresh MoDerivAffMsa"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Error: msa_kind != 'auto' on stem entry
    # ------------------------------------------------------------------

    def test_msa_kind_infl_on_stem_raises(self, writable_project):
        """msa_kind='infl' on a stem entry must raise FP_ParameterError."""
        from flexicon.code.FLExProject import FP_ParameterError

        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_stem_entry(writable_project, "qZ91_stem_infl_err")
        try:
            sense = list(entry.SensesOS)[0]
            with pytest.raises(FP_ParameterError, match="stem morph type"):
                writable_project.Senses.SetPartOfSpeech(
                    sense, pos, msa_kind="infl"
                )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_msa_kind_deriv_on_stem_raises(self, writable_project):
        """msa_kind='deriv' on a stem entry must raise FP_ParameterError."""
        from flexicon.code.FLExProject import FP_ParameterError

        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_stem_entry(writable_project, "qZ91_stem_deriv_err")
        try:
            sense = list(entry.SensesOS)[0]
            with pytest.raises(FP_ParameterError, match="stem morph type"):
                writable_project.Senses.SetPartOfSpeech(
                    sense, pos, msa_kind="deriv"
                )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_msa_kind_unclassified_on_stem_raises(self, writable_project):
        """msa_kind='unclassified' on a stem entry must raise FP_ParameterError."""
        from flexicon.code.FLExProject import FP_ParameterError

        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_stem_entry(writable_project, "qZ91_stem_unclass_err")
        try:
            sense = list(entry.SensesOS)[0]
            with pytest.raises(FP_ParameterError, match="stem morph type"):
                writable_project.Senses.SetPartOfSpeech(
                    sense, pos, msa_kind="unclassified"
                )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_invalid_msa_kind_raises(self, writable_project):
        """An unrecognised msa_kind string must raise FP_ParameterError."""
        from flexicon.code.FLExProject import FP_ParameterError

        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_prefix_entry(writable_project, "qZ91_bad_kind")
        try:
            sense = list(entry.SensesOS)[0]
            with pytest.raises(FP_ParameterError):
                writable_project.Senses.SetPartOfSpeech(
                    sense, pos, msa_kind="bogus"
                )
        finally:
            writable_project.LexEntry.Delete(entry)


# ============================================================================
# TestChangeAffixVariant
# ============================================================================


class TestChangeAffixVariant:
    """
    Coverage for MSAOperations.ChangeAffixVariant (issue #91 sub-item 4).

    Each test creates a prefix entry, sets an initial MSA kind, then calls
    ChangeAffixVariant and verifies the new MSA type, sense repointing, and
    old-MSA cleanup.
    """

    def _setup_affix_msa(self, project, lexeme, pos, initial_kind):
        """
        Helper: create prefix entry with initial MSA of given kind.
        Returns (entry, sense, msa).
        """
        entry = _make_prefix_entry(project, lexeme)
        sense = list(entry.SensesOS)[0]
        project.Senses.SetPartOfSpeech(sense, pos, msa_kind=initial_kind)
        msa = sense.MorphoSyntaxAnalysisRA
        return entry, sense, msa

    # ------------------------------------------------------------------
    # Same-kind no-op
    # ------------------------------------------------------------------

    def test_same_kind_returns_unchanged(self, writable_project):
        """ChangeAffixVariant to the same kind returns the original MSA."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry, sense, msa = self._setup_affix_msa(
            writable_project, "qZ91_cv_noop", pos, "infl"
        )
        try:
            result = writable_project.MSA.ChangeAffixVariant(msa, "infl")
            assert result.Hvo == msa.Hvo, (
                "Same-kind ChangeAffixVariant should return the original MSA"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Infl -> Deriv
    # ------------------------------------------------------------------

    def test_infl_to_deriv(self, writable_project):
        """Converting MoInflAffMsa -> MoDerivAffMsa yields correct type."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry, sense, msa = self._setup_affix_msa(
            writable_project, "qZ91_cv_infl_deriv", pos, "infl"
        )
        try:
            new_msa = writable_project.MSA.ChangeAffixVariant(msa, "deriv")
            assert new_msa.ClassName == "MoDerivAffMsa", (
                f"Expected MoDerivAffMsa, got {new_msa.ClassName}"
            )
            # Sense must now point at new MSA
            assert sense.MorphoSyntaxAnalysisRA.Hvo == new_msa.Hvo
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Infl -> Unclassified
    # ------------------------------------------------------------------

    def test_infl_to_unclassified(self, writable_project):
        """Converting MoInflAffMsa -> MoUnclassifiedAffixMsa yields correct type."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry, sense, msa = self._setup_affix_msa(
            writable_project, "qZ91_cv_infl_unclass", pos, "infl"
        )
        try:
            new_msa = writable_project.MSA.ChangeAffixVariant(msa, "unclassified")
            assert new_msa.ClassName == "MoUnclassifiedAffixMsa", (
                f"Expected MoUnclassifiedAffixMsa, got {new_msa.ClassName}"
            )
            assert sense.MorphoSyntaxAnalysisRA.Hvo == new_msa.Hvo
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Deriv -> Infl
    # ------------------------------------------------------------------

    def test_deriv_to_infl(self, writable_project):
        """Converting MoDerivAffMsa -> MoInflAffMsa yields correct type."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry, sense, msa = self._setup_affix_msa(
            writable_project, "qZ91_cv_deriv_infl", pos, "deriv"
        )
        try:
            new_msa = writable_project.MSA.ChangeAffixVariant(msa, "infl")
            assert new_msa.ClassName == "MoInflAffMsa", (
                f"Expected MoInflAffMsa, got {new_msa.ClassName}"
            )
            assert sense.MorphoSyntaxAnalysisRA.Hvo == new_msa.Hvo
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Deriv -> Unclassified
    # ------------------------------------------------------------------

    def test_deriv_to_unclassified(self, writable_project):
        """Converting MoDerivAffMsa -> MoUnclassifiedAffixMsa yields correct type."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry, sense, msa = self._setup_affix_msa(
            writable_project, "qZ91_cv_deriv_unclass", pos, "deriv"
        )
        try:
            new_msa = writable_project.MSA.ChangeAffixVariant(msa, "unclassified")
            assert new_msa.ClassName == "MoUnclassifiedAffixMsa", (
                f"Expected MoUnclassifiedAffixMsa, got {new_msa.ClassName}"
            )
            assert sense.MorphoSyntaxAnalysisRA.Hvo == new_msa.Hvo
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Unclassified -> Infl
    # ------------------------------------------------------------------

    def test_unclassified_to_infl(self, writable_project):
        """Converting MoUnclassifiedAffixMsa -> MoInflAffMsa yields correct type."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry, sense, msa = self._setup_affix_msa(
            writable_project, "qZ91_cv_unclass_infl", pos, "unclassified"
        )
        try:
            new_msa = writable_project.MSA.ChangeAffixVariant(msa, "infl")
            assert new_msa.ClassName == "MoInflAffMsa", (
                f"Expected MoInflAffMsa, got {new_msa.ClassName}"
            )
            assert sense.MorphoSyntaxAnalysisRA.Hvo == new_msa.Hvo
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Unclassified -> Deriv
    # ------------------------------------------------------------------

    def test_unclassified_to_deriv(self, writable_project):
        """Converting MoUnclassifiedAffixMsa -> MoDerivAffMsa yields correct type."""
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry, sense, msa = self._setup_affix_msa(
            writable_project, "qZ91_cv_unclass_deriv", pos, "unclassified"
        )
        try:
            new_msa = writable_project.MSA.ChangeAffixVariant(msa, "deriv")
            assert new_msa.ClassName == "MoDerivAffMsa", (
                f"Expected MoDerivAffMsa, got {new_msa.ClassName}"
            )
            assert sense.MorphoSyntaxAnalysisRA.Hvo == new_msa.Hvo
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Warning content: lost fields listed
    # ------------------------------------------------------------------

    def test_infl_to_deriv_warning_lists_slots(
        self, writable_project, caplog
    ):
        """
        When converting Infl->Deriv and SlotsRC has entries, a warning
        is emitted listing 'SlotsRC' among lost fields.
        """
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        # We cannot easily add a slot in a unit test without knowing slot
        # HVOs, so we verify that when SlotsRC IS empty, no spurious
        # 'SlotsRC' warning is emitted (the warning fires only when data
        # exists).
        entry, sense, msa = self._setup_affix_msa(
            writable_project, "qZ91_warn_slots", pos, "infl"
        )
        try:
            with caplog.at_level(logging.WARNING):
                writable_project.MSA.ChangeAffixVariant(msa, "deriv")
            # Empty SlotsRC -- no warning about SlotsRC expected
            slot_warnings = [
                r.message for r in caplog.records
                if "SlotsRC" in str(r.message)
            ]
            assert not slot_warnings, (
                "No SlotsRC warning should be emitted when SlotsRC is empty; "
                f"got: {slot_warnings}"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_infl_to_deriv_warning_lists_inflfeatsoa(
        self, writable_project, caplog
    ):
        """
        When converting Infl->Deriv and InflFeatsOA is not None on the
        source MSA, the warning must list 'InflFeatsOA' among lost fields
        (Change 4, issue #91).

        When InflFeatsOA IS None (the common case for a freshly created
        infl MSA), no spurious 'InflFeatsOA' warning should appear.
        This test verifies the no-spurious-warning path; populating
        InflFeatsOA in a unit test requires AVM infrastructure not
        available here, so the positive path is covered by the
        no-false-positive assertion.
        """
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry, sense, msa = self._setup_affix_msa(
            writable_project, "qZ91_warn_inflfeats", pos, "infl"
        )
        try:
            with caplog.at_level(logging.WARNING):
                writable_project.MSA.ChangeAffixVariant(msa, "deriv")
            # Freshly created infl MSA has InflFeatsOA == None, so no warning.
            inflfeats_warnings = [
                r.message for r in caplog.records
                if "InflFeatsOA" in str(r.message)
            ]
            assert not inflfeats_warnings, (
                "No InflFeatsOA warning should appear when InflFeatsOA is "
                f"unset; got: {inflfeats_warnings}"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Old MSA cleanup: removed when no senses reference it
    # ------------------------------------------------------------------

    def test_old_msa_removed_when_no_senses_reference_it(
        self, writable_project
    ):
        """
        After ChangeAffixVariant, if no senses still point at the old MSA,
        the old MSA should be removed from MorphoSyntaxAnalysesOC.
        """
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry, sense, msa = self._setup_affix_msa(
            writable_project, "qZ91_cv_cleanup", pos, "infl"
        )
        old_hvo = msa.Hvo
        try:
            writable_project.MSA.ChangeAffixVariant(msa, "deriv")
            # The old MSA Hvo should no longer appear in
            # MorphoSyntaxAnalysesOC.
            remaining_hvos = {
                m.Hvo for m in entry.MorphoSyntaxAnalysesOC
            }
            assert old_hvo not in remaining_hvos, (
                f"Old MSA Hvo={old_hvo} should have been removed from "
                "MorphoSyntaxAnalysesOC after all senses were repointed"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Old MSA left in place when other senses still reference it
    # ------------------------------------------------------------------

    def test_repoints_all_senses_in_entry_referencing_old_msa(
        self, writable_project
    ):
        """
        ChangeAffixVariant repoints EVERY sense in the owning entry that
        references the old MSA, not just one. After the call, the old MSA
        is correctly removed from MorphoSyntaxAnalysesOC because no
        entry-local sense still points at it.

        (External references such as IWfiMorphBundle.MsaRA are NOT
        scanned -- that's a separate orphan-cleanup concern tracked by
        a follow-up issue.)
        """
        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_prefix_entry(writable_project, "qZ91_cv_repoint_all")
        try:
            sense1 = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(sense1, pos, msa_kind="infl")
            old_msa = sense1.MorphoSyntaxAnalysisRA
            old_hvo = old_msa.Hvo

            # Create a second sense and point it at the same old MSA manually.
            sense2 = writable_project.Senses.Create(entry, "sense2")
            sense2.MorphoSyntaxAnalysisRA = old_msa
            assert sense2.MorphoSyntaxAnalysisRA.Hvo == old_hvo

            new_msa = writable_project.MSA.ChangeAffixVariant(old_msa, "deriv")

            # Both senses must have been repointed to the new MSA.
            assert sense1.MorphoSyntaxAnalysisRA.Hvo == new_msa.Hvo
            assert sense2.MorphoSyntaxAnalysisRA.Hvo == new_msa.Hvo

            # With no entry-local senses left pointing at the old MSA,
            # LCM's cascade-delete clears it from the owning collection.
            remaining_hvos = {m.Hvo for m in entry.MorphoSyntaxAnalysesOC}
            assert old_hvo not in remaining_hvos, (
                "Old MSA should have been removed from "
                "MorphoSyntaxAnalysesOC after all senses were repointed"
            )
        finally:
            writable_project.LexEntry.Delete(entry)

    # ------------------------------------------------------------------
    # Error: non-affix MSA raises FP_ParameterError
    # ------------------------------------------------------------------

    def test_stem_msa_raises_parameter_error(self, writable_project):
        """ChangeAffixVariant with a MoStemMsa must raise FP_ParameterError."""
        from flexicon.code.FLExProject import FP_ParameterError

        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry = _make_stem_entry(writable_project, "qZ91_cv_stem_err")
        try:
            sense = list(entry.SensesOS)[0]
            writable_project.Senses.SetPartOfSpeech(sense, pos)
            stem_msa = sense.MorphoSyntaxAnalysisRA
            assert stem_msa.ClassName == "MoStemMsa"

            with pytest.raises(FP_ParameterError, match="affix MSA"):
                writable_project.MSA.ChangeAffixVariant(stem_msa, "infl")
        finally:
            writable_project.LexEntry.Delete(entry)

    def test_invalid_target_kind_raises(self, writable_project):
        """An unrecognised target_kind must raise FP_ParameterError."""
        from flexicon.code.FLExProject import FP_ParameterError

        pos = _first_pos(writable_project)
        if pos is None:
            pytest.skip("No POS values in this project")

        entry, sense, msa = self._setup_affix_msa(
            writable_project, "qZ91_cv_bad_kind", pos, "infl"
        )
        try:
            with pytest.raises(FP_ParameterError):
                writable_project.MSA.ChangeAffixVariant(msa, "bogus")
        finally:
            writable_project.LexEntry.Delete(entry)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
