#
#   test_issue231_allomorph_remove_orphaned_live.py
#
#   Issue #231 slice 3: live LCM verification for
#   AllomorphOperations.RemoveOrphaned duplicate-lexeme purge and
#   entry= int HVO scoping.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_231_"


@pytest.mark.requires_live_project
class TestIssue231RemoveOrphanedDuplicateLexemeLive:
    """
    Mock tests prove list mutation logic; this gate proves the sweep
    reaches a real AlternateFormsOS on a sandbox copy of Target.
    """

    @pytest.mark.skip(
        reason=(
            "Setup cannot be built through the LCM API: AlternateFormsOS is an "
            "owning sequence, so AlternateFormsOS.Add(entry.LexemeFormOA) MOVES "
            "the lexeme (LexemeFormOA becomes None) instead of duplicating it. "
            "Live-proven on a Target sandbox 2026-09-25 (before: lexeme 10443, "
            "alts []; after: LexemeFormOA None, alts [10443]). Needs a fixture "
            "carrying the #231 state from a real project file."
        )
    )
    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_remove_duplicate_lexeme_via_entry_hvo_int(self, target_sandbox):
        sandbox = target_sandbox
        entry = sandbox.LexEntry.Create(f"{TEST_PREFIX}dup_live")
        try:
            lexeme = entry.LexemeFormOA
            assert lexeme is not None, "test setup: entry must have LexemeFormOA"

            morph_type = lexeme.MorphTypeRA
            assert morph_type is not None, (
                "test setup: LexemeFormOA must carry MorphTypeRA"
            )

            kept_alt = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}alt", morphType="suffix"
            )
            assert kept_alt is not None

            entry.AlternateFormsOS.Add(lexeme)
            dup_in_list = sum(
                1 for allo in entry.AlternateFormsOS if allo.Hvo == lexeme.Hvo
            )
            assert dup_in_list >= 2, (
                "precondition failed: lexeme must appear twice in "
                "AlternateFormsOS (once via Create path, once injected)"
            )

            entry_hvo = entry.Hvo
            assert isinstance(entry_hvo, int), (
                "test setup: entry HVO must be a genuine Python int"
            )

            result = sandbox.Allomorphs.RemoveOrphaned(entry=entry_hvo)

            assert result.removed_count == 1
            assert result.kept_count >= 1
            assert any(r.reason == "duplicate_lexeme" for r in result.removed)

            fresh = sandbox.Object(entry_hvo)
            alternate_hvos = {allo.Hvo for allo in fresh.AlternateFormsOS}
            assert lexeme.Hvo not in alternate_hvos, (
                "post-condition failed: duplicate lexeme still listed in "
                "AlternateFormsOS after RemoveOrphaned"
            )
            assert kept_alt.Hvo in alternate_hvos, (
                "post-condition failed: non-duplicate alternate was removed"
            )
            assert fresh.LexemeFormOA is not None
            assert fresh.LexemeFormOA.Hvo == lexeme.Hvo
        finally:
            sandbox.LexEntry.Delete(entry)
