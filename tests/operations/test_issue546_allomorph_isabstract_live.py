#
#   test_issue546_allomorph_isabstract_live.py
#
#   Live gate for issue #546: AllomorphOperations.GetIsAbstract /
#   SetIsAbstract, covering the lexeme form as well as alternate forms.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_546_"


def _make_entry(sandbox, tag):
    return sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")


@pytest.mark.requires_live_project
class TestAllomorphIsAbstractLive:
    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_new_allomorphs_default_to_not_abstract(self, target_sandbox):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "default")
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}default", morphType="suffix"
            )
            assert sandbox.Allomorphs.GetIsAbstract(allo) is False
            assert sandbox.Allomorphs.GetIsAbstract(entry.LexemeFormOA) is False
        finally:
            sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_set_and_clear_on_alternate_form(self, target_sandbox):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "alternate")
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}alt", morphType="suffix"
            )

            sandbox.Allomorphs.SetIsAbstract(allo, True)
            assert sandbox.Allomorphs.GetIsAbstract(allo) is True
            # Read back from the LCM, not from the passed-in value.
            reread = sandbox.Object(allo.Hvo)
            assert sandbox.Allomorphs.GetIsAbstract(reread) is True

            sandbox.Allomorphs.SetIsAbstract(allo, False)
            assert sandbox.Allomorphs.GetIsAbstract(allo) is False
        finally:
            sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_set_on_lexeme_form(self, target_sandbox):
        """The lexeme form (LexemeFormOA) is settable, not just alternates."""
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "lexeme")
        try:
            lexeme = entry.LexemeFormOA
            assert lexeme is not None

            sandbox.Allomorphs.SetIsAbstract(lexeme, True)
            assert sandbox.Allomorphs.GetIsAbstract(lexeme) is True
            reread = sandbox.Object(lexeme.Hvo)
            assert sandbox.Allomorphs.GetIsAbstract(reread) is True
        finally:
            sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_hvo_and_wrapper_paths(self, target_sandbox):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "paths")
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}paths", morphType="suffix"
            )
            hvo = allo.Hvo
            assert isinstance(hvo, int)

            sandbox.Allomorphs.SetIsAbstract(hvo, True)
            assert sandbox.Allomorphs.GetIsAbstract(hvo) is True

            (wrapped,) = [
                a for a in sandbox.Allomorphs.GetAll(entry)
                if a.lcm_object.Hvo == hvo
            ]
            assert sandbox.Allomorphs.GetIsAbstract(wrapped) is True
            sandbox.Allomorphs.SetIsAbstract(wrapped, False)
            assert sandbox.Allomorphs.GetIsAbstract(hvo) is False
        finally:
            sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_duplicate_preserves_isabstract(self, target_sandbox):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "dup")
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}dup", morphType="suffix"
            )
            sandbox.Allomorphs.SetIsAbstract(allo, True)

            dup = sandbox.Allomorphs.Duplicate(allo)
            assert sandbox.Allomorphs.GetIsAbstract(dup) is True
        finally:
            sandbox.LexEntry.Delete(entry)
