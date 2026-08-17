#
#   test_target_live_smoke.py
#
#   Canonical template for live write-path verification against the
#   'Target' scratch FLEx project.
#
#   Copy this file's structure when adding live coverage for a new
#   write-path change. The two patterns it demonstrates are the only
#   two sanctioned ones:
#
#     1. target_sandbox  -- write to a tempdir copy of the Target
#                           .fwbackup. Nothing can leak into a real
#                           project. Use for anything destructive or
#                           anything you cannot restore.
#     2. target_project  -- write in-place to the real Target project,
#                           with capture-and-restore in a `finally:`
#                           block and a TEST_ prefix on created objects.
#
#   Both are gated by FLEXLIBS_REQUIRE_LIVE=1: with that set, an
#   unavailable Target fails the run instead of skipping it, so a
#   write-path change cannot be reported as verified off a mock pass.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_"


class TestTargetFixturesReachLiveLCM:
    """Prove the Target fixtures open a real LCM cache, not a mock."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_target_project_opens_write_enabled(self, target_project):
        """The real Target project opens with writes enabled."""
        assert target_project.writeEnabled is True, (
            "target_project fixture yielded a read-only project; "
            "write-path verification cannot run against it."
        )
        # A mock would not carry a real LCM cache.
        assert getattr(target_project, "project", None) is not None, (
            "target_project has no underlying LCM cache -- this is a "
            "mock, not a live project."
        )

    @pytest.mark.live_phase("FLExProject", "read")
    def test_target_sandbox_opens_write_enabled(self, target_sandbox):
        """A fresh sandbox copy of the Target backup opens for writing."""
        assert target_sandbox.writeEnabled is True
        assert getattr(target_sandbox, "project", None) is not None


class TestTargetSandboxRoundTrip:
    """Phase B pattern, sandbox flavour: create, verify, delete."""

    @pytest.mark.live_phase("LexEntryOperations", "add")
    def test_create_and_delete_entry_in_sandbox(self, target_sandbox):
        """
        Create a lexical entry in the sandbox, confirm it is really
        there, then delete it. Runs against a tempdir copy, so a
        failure mid-test cannot corrupt the user's Target.
        """
        entries = target_sandbox.LexEntry
        before = len(list(entries.GetAll()))

        created = entries.Create(lexeme_form=f"{TEST_PREFIX}smoke")
        assert created is not None, "Create returned None"

        try:
            after = len(list(entries.GetAll()))
            assert after == before + 1, (
                f"Entry count did not increase: {before} -> {after}. "
                "The create did not reach the LCM."
            )
        finally:
            entries.Delete(created)

        restored = len(list(entries.GetAll()))
        assert restored == before, (
            f"Cleanup failed: expected {before} entries, found {restored}"
        )
