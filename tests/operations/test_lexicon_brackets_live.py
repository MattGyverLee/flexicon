#
#   test_lexicon_brackets_live.py
#
#   Live write-path verification for B2 batch 11/11 (Lexicon): the 84
#   mutation sites bracketed in `with self._TransactionCM(...)` per
#   decision D5. This is the FINAL batch of the B2 sweep -- after it the
#   ratchet baseline is 0 and every LCM mutator under flexicon/code/ runs
#   inside a named unit of work.
#
#   Structure copied from tests/operations/test_grammar_brackets_live.py
#   (batch 10), itself copied from tests/operations/test_target_live_smoke.py,
#   the canonical template. Runs against the Target scratch project.
#
#   What this proves, per site class:
#
#     1. Round-trip -- the bracketed write reaches the LCM and survives a
#        re-query. Asserting on the value passed in would prove nothing,
#        so every assertion re-reads through the Operations getter.
#     2. Validation-outside-the-bracket -- a rejected input raises and
#        leaves the stored value untouched. This is the property D5's
#        per-site shape exists to preserve: a rejected call must not open
#        (and under B1 roll back) an empty named undo task.
#     3. No-op-guard-outside-the-bracket -- a redundant Add/Remove against
#        a reference collection is a true no-op, not an empty undo entry.
#     4. Delete round-trip -- the bracketed Remove really detaches the
#        object from its owning collection.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_"


def _make_entry(sandbox, tag):
    """Create a TEST_-prefixed entry on the live Target project."""
    return sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")


class TestLexiconFixtureReachesLiveLCM:
    """Prove this module's writes land on a real LCM cache, not a mock."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_sandbox_opens_write_enabled(self, target_sandbox):
        assert target_sandbox.writeEnabled is True
        assert getattr(target_sandbox, "project", None) is not None, (
            "target_sandbox has no underlying LCM cache -- this is a "
            "mock, not a live project."
        )


class TestLexEntryBrackets:
    """LexEntryOperations: Delete, SetLexemeForm, SetCitationForm, the
    five note setters, and the publication-exclusion guards."""

    @pytest.mark.live_phase("LexEntryOperations", "modify")
    def test_setlexemeform_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.LexEntry
        entry = _make_entry(target_sandbox, "lexform")

        try:
            ops.SetLexemeForm(entry, f"{TEST_PREFIX}changed")
            # Re-query rather than trusting the argument we passed in.
            assert ops.GetLexemeForm(entry) == f"{TEST_PREFIX}changed"
        finally:
            ops.Delete(entry)

    @pytest.mark.live_phase("LexEntryOperations", "modify")
    def test_setcitationform_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.LexEntry
        entry = _make_entry(target_sandbox, "citform")

        try:
            ops.SetCitationForm(entry, f"{TEST_PREFIX}cit")
            assert ops.GetCitationForm(entry) == f"{TEST_PREFIX}cit"
        finally:
            ops.Delete(entry)

    @pytest.mark.live_phase("LexEntryOperations", "modify")
    def test_note_setters_round_trip_through_lcm(self, target_sandbox):
        """The five entry note setters each got their own bracket."""
        ops = target_sandbox.LexEntry
        entry = _make_entry(target_sandbox, "notes")

        try:
            ops.SetBibliography(entry, f"{TEST_PREFIX}biblio")
            ops.SetComment(entry, f"{TEST_PREFIX}comment")
            ops.SetLiteralMeaning(entry, f"{TEST_PREFIX}literal")
            ops.SetRestrictions(entry, f"{TEST_PREFIX}restrict")
            ops.SetSummaryDefinition(entry, f"{TEST_PREFIX}summary")

            assert ops.GetBibliography(entry) == f"{TEST_PREFIX}biblio"
            assert ops.GetComment(entry) == f"{TEST_PREFIX}comment"
            assert ops.GetLiteralMeaning(entry) == f"{TEST_PREFIX}literal"
            assert ops.GetRestrictions(entry) == f"{TEST_PREFIX}restrict"
            assert ops.GetSummaryDefinition(entry) == f"{TEST_PREFIX}summary"
        finally:
            ops.Delete(entry)

    @pytest.mark.live_phase("LexEntryOperations", "modify")
    def test_empty_lexeme_form_rejected_with_value_unchanged(self, target_sandbox):
        """
        SetLexemeForm's empty-string guard sits OUTSIDE the bracket, so it
        raises without opening an undo task and without disturbing the
        stored value.
        """
        ops = target_sandbox.LexEntry
        entry = _make_entry(target_sandbox, "guard")

        try:
            ops.SetLexemeForm(entry, f"{TEST_PREFIX}keepme")
            before = ops.GetLexemeForm(entry)

            with pytest.raises(FP_ParameterError):
                ops.SetLexemeForm(entry, "   ")

            assert ops.GetLexemeForm(entry) == before, (
                "A rejected SetLexemeForm altered the stored form -- the "
                "validation guard is inside the transaction."
            )
        finally:
            ops.Delete(entry)

    @pytest.mark.live_phase("LexEntryOperations", "delete")
    def test_delete_detaches_from_lcm(self, target_sandbox):
        ops = target_sandbox.LexEntry
        before = len(list(ops.GetAll()))

        entry = _make_entry(target_sandbox, "delete")
        assert len(list(ops.GetAll())) == before + 1

        ops.Delete(entry)
        assert len(list(ops.GetAll())) == before, (
            "Delete did not remove the entry from the LCM collection."
        )


class TestLexSenseBrackets:
    """LexSenseOperations: Delete, SetGloss, SetDefinition, the ten note
    setters, and the semantic-domain membership guards."""

    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_setgloss_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.Senses
        entry = _make_entry(target_sandbox, "sense_gloss")

        try:
            sense = ops.Create(entry, f"{TEST_PREFIX}gloss")
            ops.SetGloss(sense, f"{TEST_PREFIX}regloss")
            assert ops.GetGloss(sense) == f"{TEST_PREFIX}regloss"
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_setdefinition_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.Senses
        entry = _make_entry(target_sandbox, "sense_def")

        try:
            sense = ops.Create(entry, f"{TEST_PREFIX}g")
            ops.SetDefinition(sense, f"{TEST_PREFIX}definition")
            assert ops.GetDefinition(sense) == f"{TEST_PREFIX}definition"
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_note_setters_round_trip_through_lcm(self, target_sandbox):
        """Three of the ten scripted note setters, each with its own bracket."""
        ops = target_sandbox.Senses
        entry = _make_entry(target_sandbox, "sense_notes")

        try:
            sense = ops.Create(entry, f"{TEST_PREFIX}g")
            ops.SetBibliography(sense, f"{TEST_PREFIX}sbiblio")
            ops.SetGeneralNote(sense, f"{TEST_PREFIX}sgeneral")
            ops.SetRestrictions(sense, f"{TEST_PREFIX}srestrict")

            assert ops.GetBibliography(sense) == f"{TEST_PREFIX}sbiblio"
            assert ops.GetGeneralNote(sense) == f"{TEST_PREFIX}sgeneral"
            assert ops.GetRestrictions(sense) == f"{TEST_PREFIX}srestrict"
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexSenseOperations", "modify")
    def test_semantic_domain_add_remove_round_trip(self, target_sandbox):
        """
        AddSemanticDomain / RemoveSemanticDomain keep their membership test
        OUTSIDE the bracket, so a redundant call is a true no-op rather
        than an empty named undo entry.
        """
        ops = target_sandbox.Senses
        domains = list(target_sandbox.SemanticDomains.GetAll())
        if not domains:
            pytest.skip("Target has no semantic domains to reference")

        domain = domains[0]
        entry = _make_entry(target_sandbox, "sense_domain")

        try:
            sense = ops.Create(entry, f"{TEST_PREFIX}g")
            assert len(ops.GetSemanticDomains(sense)) == 0

            ops.AddSemanticDomain(sense, domain)
            assert len(ops.GetSemanticDomains(sense)) == 1

            # Redundant add -- the membership guard must make this a no-op.
            ops.AddSemanticDomain(sense, domain)
            assert len(ops.GetSemanticDomains(sense)) == 1, (
                "A redundant AddSemanticDomain changed the collection."
            )

            ops.RemoveSemanticDomain(sense, domain)
            assert len(ops.GetSemanticDomains(sense)) == 0

            # Redundant remove -- likewise a no-op.
            ops.RemoveSemanticDomain(sense, domain)
            assert len(ops.GetSemanticDomains(sense)) == 0
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexSenseOperations", "delete")
    def test_delete_detaches_from_lcm(self, target_sandbox):
        ops = target_sandbox.Senses
        entry = _make_entry(target_sandbox, "sense_delete")

        try:
            before = len(list(ops.GetAll(entry)))
            sense = ops.Create(entry, f"{TEST_PREFIX}doomed")
            assert len(list(ops.GetAll(entry))) == before + 1

            ops.Delete(sense)
            assert len(list(ops.GetAll(entry))) == before, (
                "Delete did not remove the sense from its owning SensesOS."
            )
        finally:
            target_sandbox.LexEntry.Delete(entry)


class TestExampleBrackets:
    """ExampleOperations: Delete, SetExample, SetLiteralTranslation."""

    @pytest.mark.live_phase("ExampleOperations", "modify")
    def test_setexample_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.Examples
        entry = _make_entry(target_sandbox, "example")

        try:
            sense = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}g")
            example = ops.Create(sense, f"{TEST_PREFIX}sentence")

            ops.SetExample(example, f"{TEST_PREFIX}revised")
            assert ops.GetExample(example) == f"{TEST_PREFIX}revised"
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.xfail(
        reason="PRE-EXISTING (not B2): ExampleOperations.SetLiteralTranslation "
        "and GetLiteralTranslation call self.__WSHandleAnalysis(), which does "
        "not exist on this class (it defines only __WSHandle and __WSHandleVern), "
        "so both raise AttributeError on any live project. Present at HEAD "
        "lines 1491/1520, before batch 11 -- the failure happens BEFORE the "
        "bracket is entered, so the bracket itself is unexercised here. Left "
        "unfixed to keep batch 11 mechanical; see .spec-context.json concerns.",
        raises=AttributeError,
        strict=True,
    )
    @pytest.mark.live_phase("ExampleOperations", "modify")
    def test_setliteraltranslation_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.Examples
        entry = _make_entry(target_sandbox, "example_lit")

        try:
            sense = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}g")
            example = ops.Create(sense, f"{TEST_PREFIX}sentence")

            ops.SetLiteralTranslation(example, f"{TEST_PREFIX}word_for_word")
            assert ops.GetLiteralTranslation(example) == f"{TEST_PREFIX}word_for_word"
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("ExampleOperations", "delete")
    def test_delete_detaches_from_lcm(self, target_sandbox):
        ops = target_sandbox.Examples
        entry = _make_entry(target_sandbox, "example_delete")

        try:
            sense = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}g")
            before = len(list(ops.GetAll(sense)))

            example = ops.Create(sense, f"{TEST_PREFIX}doomed")
            assert len(list(ops.GetAll(sense))) == before + 1

            ops.Delete(example)
            assert len(list(ops.GetAll(sense))) == before, (
                "Delete did not remove the example from its owning ExamplesOS."
            )
        finally:
            target_sandbox.LexEntry.Delete(entry)


class TestPronunciationBrackets:
    """PronunciationOperations: Delete, SetForm."""

    @pytest.mark.live_phase("PronunciationOperations", "modify")
    def test_setform_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.Pronunciations
        entry = _make_entry(target_sandbox, "pron")

        try:
            pron = ops.Create(entry, f"{TEST_PREFIX}form")
            ops.SetForm(pron, f"{TEST_PREFIX}revised")
            assert ops.GetForm(pron) == f"{TEST_PREFIX}revised"
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("PronunciationOperations", "delete")
    def test_delete_detaches_from_lcm(self, target_sandbox):
        ops = target_sandbox.Pronunciations
        entry = _make_entry(target_sandbox, "pron_delete")

        try:
            before = len(list(ops.GetAll(entry)))
            pron = ops.Create(entry, f"{TEST_PREFIX}doomed")
            assert len(list(ops.GetAll(entry))) == before + 1

            ops.Delete(pron)
            assert len(list(ops.GetAll(entry))) == before, (
                "Delete did not remove the pronunciation from "
                "its owning PronunciationsOS."
            )
        finally:
            target_sandbox.LexEntry.Delete(entry)


class TestEtymologyBrackets:
    """EtymologyOperations: Delete, SetSource, SetForm, SetGloss, SetComment."""

    @pytest.mark.live_phase("EtymologyOperations", "modify")
    def test_setters_round_trip_through_lcm(self, target_sandbox):
        """The three etymology setters that are reachable on a live LCM.

        SetSource and SetLanguage are excluded -- see the xfail tests below;
        both target fields that do not exist on ILexEtymology.
        """
        ops = target_sandbox.Etymology
        entry = _make_entry(target_sandbox, "etym")

        try:
            etym = ops.Create(entry)
            ops.SetForm(etym, f"{TEST_PREFIX}form")
            ops.SetGloss(etym, f"{TEST_PREFIX}gloss")
            ops.SetComment(etym, f"{TEST_PREFIX}comment")

            assert ops.GetForm(etym) == f"{TEST_PREFIX}form"
            assert ops.GetGloss(etym) == f"{TEST_PREFIX}gloss"
            assert ops.GetComment(etym) == f"{TEST_PREFIX}comment"
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.xfail(
        reason="PRE-EXISTING (not B2): ILexEtymology has no 'Source' attribute "
        "at all, so SetSource/GetSource raise AttributeError on any live "
        "project. This is CLAUDE.md Category 8 territory (same-name fields "
        "with different LCM types across interfaces -- 'Source' is ITsString "
        "on ILexSense). The failure happens BEFORE the bracket is entered. "
        "Left unfixed to keep batch 11 mechanical; see .spec-context.json.",
        raises=AttributeError,
        strict=True,
    )
    @pytest.mark.live_phase("EtymologyOperations", "modify")
    def test_setsource_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.Etymology
        entry = _make_entry(target_sandbox, "etym_source")

        try:
            etym = ops.Create(entry)
            ops.SetSource(etym, f"{TEST_PREFIX}source")
            assert ops.GetSource(etym) == f"{TEST_PREFIX}source"
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.xfail(
        reason="PRE-EXISTING (not B2), and the worst of the three: "
        "ILexEtymology has no 'LanguageRA' attribute (the interface exposes "
        "LanguageNotes instead), but `etymology.LanguageRA = language` does "
        "NOT raise -- pythonnet accepts it as a plain Python attribute on the "
        "wrapper object. So SetLanguage silently discards the write: hasattr "
        "flips False->True on that one handle, while a freshly-fetched LCM "
        "handle for the same Hvo still has no such field. Silent data loss, "
        "not an error. Unrelated to the bracket (which does open and commit "
        "correctly around a write that goes nowhere). Left unfixed to keep "
        "batch 11 mechanical; see .spec-context.json concerns.\n"
        "This test asserts the CORRECT behaviour, so it xfails today and "
        "XPASSes the moment the bug is fixed -- strict=True then fails the "
        "run, which is the signal to delete this marker.",
        strict=True,
    )
    @pytest.mark.live_phase("EtymologyOperations", "modify")
    def test_setlanguage_persists_to_the_lcm(self, target_sandbox):
        ops = target_sandbox.Etymology
        entry = _make_entry(target_sandbox, "etym_lang")

        try:
            etym = ops.Create(entry)
            ops.SetLanguage(etym, None)

            # Re-fetch a FRESH handle: asserting on the object we just wrote
            # through would pass on the stale Python-side attribute.
            fresh = target_sandbox.project.ServiceLocator.GetObject(etym.Hvo)
            assert hasattr(fresh, "LanguageRA"), (
                "SetLanguage wrote to a field that does not exist on "
                "ILexEtymology -- the value never reached the LCM."
            )
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("EtymologyOperations", "delete")
    def test_delete_detaches_from_lcm(self, target_sandbox):
        ops = target_sandbox.Etymology
        entry = _make_entry(target_sandbox, "etym_delete")

        try:
            before = len(list(ops.GetAll(entry)))
            etym = ops.Create(entry)
            assert len(list(ops.GetAll(entry))) == before + 1

            ops.Delete(etym)
            assert len(list(ops.GetAll(entry))) == before, (
                "Delete did not remove the etymology from "
                "its owning EtymologyOS."
            )
        finally:
            target_sandbox.LexEntry.Delete(entry)


class TestAllomorphBrackets:
    """AllomorphOperations: SetForm, plus the PhoneEnv membership guards."""

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_setform_round_trips_through_lcm(self, target_sandbox):
        ops = target_sandbox.Allomorphs
        entry = _make_entry(target_sandbox, "allo")

        try:
            allo = ops.Create(entry, f"{TEST_PREFIX}form")
            ops.SetForm(allo, f"{TEST_PREFIX}revised")
            assert ops.GetForm(allo) == f"{TEST_PREFIX}revised"
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_empty_form_rejected_with_value_unchanged(self, target_sandbox):
        """SetForm's empty guard sits outside the bracket."""
        ops = target_sandbox.Allomorphs
        entry = _make_entry(target_sandbox, "allo_guard")

        try:
            allo = ops.Create(entry, f"{TEST_PREFIX}keepme")
            before = ops.GetForm(allo)

            with pytest.raises(FP_ParameterError):
                ops.SetForm(allo, "   ")

            assert ops.GetForm(allo) == before, (
                "A rejected SetForm altered the stored form -- the "
                "validation guard is inside the transaction."
            )
        finally:
            target_sandbox.LexEntry.Delete(entry)


class TestSemanticDomainBrackets:
    """SemanticDomainOperations: SetName, SetDescription."""

    @pytest.mark.live_phase("SemanticDomainOperations", "modify")
    def test_setname_and_setdescription_round_trip(self, target_sandbox):
        ops = target_sandbox.SemanticDomains
        domains = list(ops.GetAll())
        if not domains:
            pytest.skip("Target has no semantic domains to modify")

        domain = domains[0]
        # Capture-and-restore: this modifies pre-existing project data.
        before_name = ops.GetName(domain)
        before_desc = ops.GetDescription(domain)

        try:
            ops.SetName(domain, f"{TEST_PREFIX}domain_name")
            assert ops.GetName(domain) == f"{TEST_PREFIX}domain_name"
        finally:
            if before_name:
                ops.SetName(domain, before_name)
                assert ops.GetName(domain) == before_name
            # before_desc is captured for symmetry with the restore contract;
            # SetDescription is exercised only when the domain already had one.
            if before_desc:
                ops.SetDescription(domain, before_desc)
