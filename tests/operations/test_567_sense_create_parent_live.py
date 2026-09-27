#
#   test_567_sense_create_parent_live.py
#
#   Live verification for issue #567: Senses.Create is canonical over an
#   entry-or-sense parent; CreateSubsense and LexEntry.AddSense delegate.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_567_"


def _make_entry(sandbox, lexeme):
    return sandbox.LexEntry.Create(lexeme, create_blank_sense=False)


def _glosses(sandbox, entry):
    return sorted(
        sandbox.Senses.GetGloss(s)
        for s in sandbox.Senses.GetAll(entry, recursive=True)
    )


class TestCreateEntryOrSenseParent:
    @pytest.mark.live_phase("LexSenseOperations", "add")
    def test_create_with_sense_parent_makes_subsense(self, target_sandbox):
        entry = _make_entry(target_sandbox, f"{TEST_PREFIX}parent")
        try:
            parent = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}pgloss")
            child = target_sandbox.Senses.Create(parent, f"{TEST_PREFIX}cgloss")
            assert child is not None

            # Read back from the LCM: child is a subsense of parent.
            subs = list(target_sandbox.Senses.GetSubsenses(parent, recursive=False))
            assert [s.Hvo for s in subs] == [child.Hvo]
            assert target_sandbox.Senses.GetParentSense(child).Hvo == parent.Hvo
            assert target_sandbox.Senses.GetParentSense(parent) is None
            assert f"{TEST_PREFIX}cgloss" in _glosses(target_sandbox, entry)
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexSenseOperations", "add")
    def test_create_with_sense_hvo_parent(self, target_sandbox):
        entry = _make_entry(target_sandbox, f"{TEST_PREFIX}hvoparent")
        try:
            parent = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}hpgloss")
            child = target_sandbox.Senses.Create(parent.Hvo, f"{TEST_PREFIX}hcgloss")
            assert target_sandbox.Senses.GetParentSense(child).Hvo == parent.Hvo
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexSenseOperations", "add")
    def test_create_with_entry_parent_unchanged(self, target_sandbox):
        entry = _make_entry(target_sandbox, f"{TEST_PREFIX}topparent")
        try:
            sense = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}topgloss")
            assert target_sandbox.Senses.GetParentSense(sense) is None
            top = list(target_sandbox.Senses.GetAll(entry, recursive=False))
            assert sense.Hvo in [s.Hvo for s in top]
        finally:
            target_sandbox.LexEntry.Delete(entry)


class TestCreateSubsenseDelegation:
    @pytest.mark.live_phase("LexSenseOperations", "add")
    def test_createsubsense_still_works(self, target_sandbox):
        entry = _make_entry(target_sandbox, f"{TEST_PREFIX}subwrapper")
        try:
            parent = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}swpgloss")
            child = target_sandbox.Senses.CreateSubsense(parent, f"{TEST_PREFIX}swcgloss")
            assert target_sandbox.Senses.GetParentSense(child).Hvo == parent.Hvo
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexSenseOperations", "add")
    def test_createsubsense_rejects_entry_parent(self, target_sandbox):
        entry = _make_entry(target_sandbox, f"{TEST_PREFIX}subreject")
        try:
            with pytest.raises(FP_ParameterError):
                target_sandbox.Senses.CreateSubsense(entry, f"{TEST_PREFIX}bad")
            with pytest.raises(FP_ParameterError):
                target_sandbox.Senses.CreateSubsense(entry.Hvo, f"{TEST_PREFIX}bad")
            # Nothing was written.
            assert f"{TEST_PREFIX}bad" not in _glosses(target_sandbox, entry)
        finally:
            target_sandbox.LexEntry.Delete(entry)


class TestAddSenseDelegation:
    @pytest.mark.live_phase("LexEntryOperations", "add")
    def test_addsense_still_works(self, target_sandbox):
        entry = _make_entry(target_sandbox, f"{TEST_PREFIX}addsense")
        try:
            sense = target_sandbox.LexEntry.AddSense(entry, f"{TEST_PREFIX}asgloss")
            assert sense is not None
            assert target_sandbox.Senses.GetParentSense(sense) is None
            assert f"{TEST_PREFIX}asgloss" in _glosses(target_sandbox, entry)
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexEntryOperations", "add")
    def test_addsense_rejects_sense_parent(self, target_sandbox):
        entry = _make_entry(target_sandbox, f"{TEST_PREFIX}addreject")
        try:
            parent = target_sandbox.Senses.Create(entry, f"{TEST_PREFIX}arpgloss")
            with pytest.raises(FP_ParameterError):
                target_sandbox.LexEntry.AddSense(parent, f"{TEST_PREFIX}bad")
            with pytest.raises(FP_ParameterError):
                target_sandbox.LexEntry.AddSense(parent.Hvo, f"{TEST_PREFIX}bad")
            assert f"{TEST_PREFIX}bad" not in _glosses(target_sandbox, entry)
        finally:
            target_sandbox.LexEntry.Delete(entry)
