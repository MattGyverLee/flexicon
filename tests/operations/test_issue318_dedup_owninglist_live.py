#
#   test_issue318_dedup_owninglist_live.py
#
#   Class: LexEntryOperations / LexSenseOperations
#          Live-LCM verification for issue #318: the three private dedup
#          helpers behind MergeObject() (pronunciations, allomorphs,
#          examples) called `dupe.OwningList.Remove(dupe)`. `OwningList`
#          exists only on `ICmPossibility` in LCM 11 -- never on
#          `ILexPronunciation`, `IMoForm`, or `ILexExampleSentence` -- so
#          every removal attempt raised `AttributeError`, silently caught
#          by a broad `except Exception: logger.warning(...)`.
#          Deduplication never actually removed anything; `removed_count`
#          stayed 0 while the merge reported success.
#
#          The fix (commit a9573b6) removes via the correct owning
#          sequence (entry.PronunciationsOS / entry.AlternateFormsOS /
#          sense.ExamplesOS), narrows the inner `except` to nothing (no
#          benign LCM-side removal failure mode was identifiable), and
#          adds `FP_DeduplicationError`, raised when duplicates were
#          detected but not all could be removed.
#
#          The companion mock test `test_issue318_dedup_owninglist.py`
#          (DO NOT MODIFY) proves this shape against a mocked project.
#          This file proves the same shape against a real LCM 11 cache:
#          that `OwningList` genuinely does not exist on the live
#          interfaces, and that the merge path with auto_deduplicate=True
#          (the default) actually shrinks the owning sequences and
#          genuinely deletes the removed objects rather than orphaning
#          them.
#
#          Runs exclusively against target_sandbox (a tempdir copy of
#          the Target .fwbackup fixture) -- never target_project or a
#          sena3 fixture (no Sena 3 backup exists on this machine) --
#          because this is destructive, irreversible write-path testing
#          (MergeObject deletes the victim object).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon import cast_to_concrete
from flexicon.code.exceptions import FP_DeduplicationError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_318_"


# ---------------------------------------------------------------------------
# Shared setup helpers
# ---------------------------------------------------------------------------


def _multistring_text(project, multistring):
    """
    First non-empty alternative of an IMultiString/IMultiUnicode, across
    every writing system in the project.

    Mirrors how the dedup helpers themselves build a signature, so a test
    asserting on "the form" sees the same text the production code compared.
    """
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    if not multistring:
        return ""
    for ws in project.project.ServiceLocator.WritingSystems.AllWritingSystems:
        text = ITsString(multistring.get_String(ws.Handle)).Text
        if text:
            return text
    return ""


def _form_text(project, form_bearing):
    """Form text of an allomorph (IMoForm) or pronunciation."""
    return _multistring_text(project, getattr(form_bearing, "Form", None))


def _example_text(project, example):
    """Example-sentence text of an ILexExampleSentence."""
    return _multistring_text(project, getattr(example, "Example", None))


def _make_entry(project, lexeme_form, create_blank_sense=True):
    """Create a minimal TEST_-prefixed entry."""
    return project.LexEntry.Create(f"{TEST_PREFIX}{lexeme_form}", create_blank_sense=create_blank_sense)


# ===========================================================================
# Requirement 1 -- OwningList genuinely does not exist on live objects
# ===========================================================================


class TestOwningListDoesNotExistLive:
    """
    The entire #318 fix rests on `OwningList` not existing on these three
    live LCM interfaces. Confirm it directly against a real cache rather
    than trusting the issue text or the mock test's docstring.
    """

    @pytest.mark.live_phase("LexEntryOperations", "read")
    def test_pronunciation_allomorph_example_lack_owninglist(self, target_sandbox):
        entry = _make_entry(target_sandbox, "owninglist_probe")
        sense = list(entry.SensesOS)[0]

        pron = target_sandbox.Pronunciations.Create(entry, "probeform")
        allomorph = target_sandbox.Allomorphs.Create(entry, "probealt")
        example = target_sandbox.Examples.Create(sense, "Probe example sentence.")

        # If any of these genuinely HAS OwningList on this LCM build, that
        # contradicts the whole premise of the #318 fix -- let it fail loudly
        # rather than silently passing.
        assert not hasattr(pron, "OwningList"), (
            "ILexPronunciation unexpectedly HAS OwningList on this live LCM "
            "build -- the #318 fix's premise does not hold here."
        )
        assert not hasattr(allomorph, "OwningList"), (
            "IMoForm unexpectedly HAS OwningList on this live LCM build -- "
            "the #318 fix's premise does not hold here."
        )
        assert not hasattr(example, "OwningList"), (
            "ILexExampleSentence unexpectedly HAS OwningList on this live "
            "LCM build -- the #318 fix's premise does not hold here."
        )

        # And confirm the correct owning sequences DO exist, per the fix.
        assert hasattr(entry, "PronunciationsOS")
        assert hasattr(entry, "AlternateFormsOS")
        assert hasattr(sense, "ExamplesOS")


# ===========================================================================
# Requirements 2, 3, 5 -- dedup actually removes, removed_count is
# genuinely non-zero, and non-duplicate siblings/owned-object deletion
# semantics are preserved
# ===========================================================================


class TestDeduplicationRemovesLiveDuplicates:
    """
    Each test builds a survivor with a genuine duplicate PLUS one distinct
    sibling, merges in a trivial victim to trigger the
    auto_deduplicate=True default path, then re-queries the LCM (never
    trusting the return value or an un-re-read Python handle) to confirm:

      - the duplicate pair collapsed to 1 (the master survives, by Hvo)
      - the distinct sibling is untouched (no collateral damage)
      - the removed duplicate is genuinely deleted (IsValidObject is
        False, and re-resolving its Hvo through the project raises)
        rather than merely orphaned
      - the pre-fix silent-no-op is dead: the count actually dropped
        (this is exactly the quantity that stayed 0 before the fix)
    """

    @pytest.mark.live_phase("LexEntryOperations", "merge")
    def test_duplicate_pronunciations_removed_by_merge(self, target_sandbox):
        survivor = _make_entry(target_sandbox, "pron_survivor")
        victim = _make_entry(target_sandbox, "pron_victim")

        master = target_sandbox.Pronunciations.Create(survivor, "dupform")
        dupe = target_sandbox.Pronunciations.Create(survivor, "dupform")
        distinct = target_sandbox.Pronunciations.Create(survivor, "uniqueform")

        before = len(list(survivor.PronunciationsOS))
        assert before == 3

        target_sandbox.LexEntry.MergeObject(survivor, victim)

        # Re-fetch the survivor object fresh from the repository -- do not
        # trust the Python handle held before the merge.
        reread_survivor = cast_to_concrete(target_sandbox.project.ServiceLocator.GetObject(survivor.Hvo))
        after_forms = list(reread_survivor.PronunciationsOS)
        after = len(after_forms)

        removed_count = before - after
        assert removed_count > 0, (
            "PronunciationsOS length did not shrink -- this is exactly the "
            "pre-fix silent no-op (removed_count stayed 0 while the merge "
            "reported success)."
        )
        assert after == 2, f"Expected 1 duplicate collapsed + 1 distinct survivor, got {after} pronunciations"

        after_hvos = {p.Hvo for p in after_forms}
        assert master.Hvo in after_hvos, "The kept master pronunciation is missing after dedup."
        assert distinct.Hvo in after_hvos, "The distinct (non-duplicate) pronunciation was collaterally removed."
        assert dupe.Hvo not in after_hvos, "The duplicate pronunciation was not actually removed."

        # Genuinely deleted, not orphaned: owned objects cannot be
        # orphaned by .Remove() on their owning sequence -- confirm the
        # removed object is truly gone, re-read from the LCM.
        assert dupe.IsValidObject is False, (
            "Removed duplicate pronunciation is still IsValidObject=True -- "
            "it was orphaned rather than deleted."
        )
        with pytest.raises(Exception):
            target_sandbox.project.ServiceLocator.GetObject(dupe.Hvo)

    @pytest.mark.live_phase("LexEntryOperations", "merge")
    def test_duplicate_allomorphs_removed_by_merge(self, target_sandbox):
        survivor = _make_entry(target_sandbox, "allo_survivor")
        victim = _make_entry(target_sandbox, "allo_victim")

        master = target_sandbox.Allomorphs.Create(survivor, "dupalt")
        dupe = target_sandbox.Allomorphs.Create(survivor, "dupalt")
        distinct = target_sandbox.Allomorphs.Create(survivor, "uniquealt")

        before = len(list(survivor.AlternateFormsOS))
        assert before == 3

        target_sandbox.LexEntry.MergeObject(survivor, victim)

        reread_survivor = cast_to_concrete(target_sandbox.project.ServiceLocator.GetObject(survivor.Hvo))
        after_forms = list(reread_survivor.AlternateFormsOS)
        after = len(after_forms)

        # Do NOT assert on net length. LibLCM's own survivor.MergeObject()
        # appends the victim's lexeme form to AlternateFormsOS at the same
        # time the duplicate is collapsed, so `before - after` nets to zero
        # even on a fully successful dedup and would read as the pre-fix
        # silent no-op. The invariant that actually distinguishes fixed from
        # broken is how many allomorphs carrying the duplicated form survive:
        # exactly one after the fix, two before it.
        surviving_dupalt = [
            a for a in after_forms
            if _form_text(target_sandbox, a) == "dupalt"
        ]
        assert len(surviving_dupalt) == 1, (
            f"Expected exactly one allomorph bearing the duplicated form, "
            f"got {len(surviving_dupalt)}. Two means deduplication did not "
            f"run -- the pre-fix silent no-op."
        )
        assert after >= 2, f"Expected at least the master and the distinct allomorph, got {after}"

        after_hvos = {a.Hvo for a in after_forms}
        assert master.Hvo in after_hvos, "The kept master allomorph is missing after dedup."
        assert distinct.Hvo in after_hvos, "The distinct (non-duplicate) allomorph was collaterally removed."
        assert dupe.Hvo not in after_hvos, "The duplicate allomorph was not actually removed."

        assert dupe.IsValidObject is False, (
            "Removed duplicate allomorph is still IsValidObject=True -- "
            "it was orphaned rather than deleted."
        )
        with pytest.raises(Exception):
            target_sandbox.project.ServiceLocator.GetObject(dupe.Hvo)

    @pytest.mark.live_phase("LexSenseOperations", "merge")
    def test_duplicate_examples_removed_by_merge(self, target_sandbox):
        entry = _make_entry(target_sandbox, "example_entry", create_blank_sense=False)
        survivor_sense = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}survivor_gloss")
        victim_sense = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}victim_gloss")

        master = target_sandbox.Examples.Create(survivor_sense, "The duplicate example sentence.")
        dupe = target_sandbox.Examples.Create(survivor_sense, "The duplicate example sentence.")
        distinct = target_sandbox.Examples.Create(survivor_sense, "A different, unique example sentence.")

        before = len(list(survivor_sense.ExamplesOS))
        assert before == 3

        target_sandbox.Senses.MergeObject(survivor_sense, victim_sense)

        reread_sense = cast_to_concrete(target_sandbox.project.ServiceLocator.GetObject(survivor_sense.Hvo))
        after_examples = list(reread_sense.ExamplesOS)
        after = len(after_examples)

        # As in the allomorph case, net length is not the right signal: the
        # merge can move the victim sense's own examples into ExamplesOS
        # while the duplicate is collapsed. Assert on how many examples
        # bearing the duplicated text survive -- one when dedup ran, two
        # when it silently did nothing.
        surviving_dupes = [
            ex for ex in after_examples
            if _example_text(target_sandbox, ex) == "The duplicate example sentence."
        ]
        assert len(surviving_dupes) == 1, (
            f"Expected exactly one example bearing the duplicated sentence, "
            f"got {len(surviving_dupes)}. Two means deduplication did not "
            f"run -- the pre-fix silent no-op."
        )
        assert after >= 2, f"Expected at least the master and the distinct example, got {after}"

        after_hvos = {e.Hvo for e in after_examples}
        assert master.Hvo in after_hvos, "The kept master example is missing after dedup."
        assert distinct.Hvo in after_hvos, "The distinct (non-duplicate) example was collaterally removed."
        assert dupe.Hvo not in after_hvos, "The duplicate example was not actually removed."

        assert dupe.IsValidObject is False, (
            "Removed duplicate example is still IsValidObject=True -- it "
            "was orphaned rather than deleted."
        )
        with pytest.raises(Exception):
            target_sandbox.project.ServiceLocator.GetObject(dupe.Hvo)


# ===========================================================================
# Requirement 4 -- FP_DeduplicationError on partial-removal failure
# ===========================================================================


class TestDeduplicationErrorOnPartialFailure:
    """
    The ticket asks for a case where duplicates are detected but removal
    cannot complete, to prove FP_DeduplicationError actually fires.

    That case is NOT constructible honestly against a live LCM cache:
    the post-fix code has no inner try/except around
    `<owning_sequence>.Remove(dupe)` (per the programmer's cycle-2 note,
    no genuinely benign LCM-side removal-failure mode was identifiable),
    so on live LCM 11 the call either raises immediately (propagating,
    not silently reporting 0) or succeeds outright. There is no known way
    to make a live, real `ILcmOwningSequence.Remove()` call return
    normally while leaving the item in place -- which is exactly the
    "silent partial failure" shape FP_DeduplicationError exists to catch.

    The only way to exercise this branch is to make `.Remove()` a no-op
    that neither raises nor removes (monkeypatching the live sequence's
    `.Remove` method), which is indistinguishable from mocking behaviour
    on a live object -- exactly what a live-verification file must not
    fake. The mock test (`test_issue318_dedup_owninglist.py`) already
    covers this branch honestly, against a mock built for that purpose.

    This test is left in place, skipped, purely so the gap is visible in
    the live suite rather than silently absent.
    """

    @pytest.mark.skip(
        reason=(
            "No honest live-LCM construction of 'duplicates detected but "
            "removal cannot complete' exists without monkeypatching the "
            "live owning sequence's .Remove() -- see class docstring. "
            "Covered honestly by the mock test instead."
        )
    )
    def test_partial_removal_failure_raises_fp_deduplication_error(self, target_sandbox):
        raise NotImplementedError(
            "Intentionally unimplemented -- see the skip reason and class "
            "docstring for why this cannot be constructed honestly against "
            "a live LCM cache."
        )


# ===========================================================================
# Sanity: FP_DeduplicationError is importable and shaped as expected
# (does not require a live project, but kept here for locality with the
# rest of this file's #318 coverage)
# ===========================================================================


def test_fp_deduplication_error_message_shape():
    err = FP_DeduplicationError("pronunciations", 12345, found=2, removed=1)
    message = str(err)
    assert "pronunciations" in message
    assert "12345" in message
    assert "2 duplicate" in message
    assert "removed only 1" in message
