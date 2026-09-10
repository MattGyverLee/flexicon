#
#   test_249_sldr_init_live.py
#
#   Module: Live verification of the SLDR init/cleanup guard in
#           flexicon.code.FLExInit (issue #249).
#
#   Structure copied from tests/operations/test_target_live_smoke.py, the
#   canonical live template. Unlike that file this one needs no project
#   fixture: the subject under test is the process-wide SLDR singleton in
#   SIL.WritingSystems, not a .fwdata file. Every assertion reads state
#   back out of the CLR after the call rather than restating an argument
#   that was passed in.
#
#   SESSION CONTRACT: the SLDR is a session-wide singleton owned by
#   tests/flex_plugin.py::initialize_flex_for_tests. This module tears it
#   down deliberately to exercise the cleanup guard, so it MUST leave it
#   INITIALIZED again -- exactly as flexicon/tests/test_FLExInit.py:34
#   does. If it does not, every later live test in the session reads LDML
#   through a dead SLDR, liblcm renames the project's .ldml files to
#   .ldml.bad and re-synthesizes writing systems from defaults, and the
#   next FieldWorks open shows "Unable to create writing system". The
#   restore therefore lives in a `finally:` and is additionally enforced
#   by an autouse fixture below.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

# Import order matters: flexicon.code.FLExInit is what configures the FW
# DLL path and does the clr.AddReference("SIL.WritingSystems"), so the SIL
# namespace does not exist until after this import. The Sldr import is then
# deliberately made *independently* of FLExInit's own module global, so
# these assertions read the real CLR type rather than whatever name
# FLExInit happens to have bound.
from flexicon.code.FLExInit import FLExInitialize, FLExCleanup  # noqa: E402

from SIL.WritingSystems import Sldr  # noqa: E402

pytestmark = pytest.mark.requires_live_project


@pytest.fixture(autouse=True)
def restore_session_sldr():
    """Backstop: whatever a test in this module does, hand the session
    back an initialized SLDR."""
    yield
    if not Sldr.IsInitialized:
        FLExInitialize()
    assert Sldr.IsInitialized is True, (
        "Could not restore the session-wide SLDR singleton; later live "
        "tests in this session would run against a dead SLDR."
    )


class TestSldrIsRealAndLive:
    """Prove this is the real CLR SLDR, not a double."""

    @pytest.mark.live_phase("FLExInit", "read")
    def test_sldr_isinitialized_is_a_real_clr_bool_probe(self):
        """IsInitialized is readable and is a genuine bool.

        Reading it is the guard's precondition; live reflection said it is
        a public static bool getter that never throws.
        """
        value = Sldr.IsInitialized
        assert isinstance(value, bool), (
            f"Sldr.IsInitialized returned {type(value)!r}, not a bool -- "
            "this is not the real CLR property."
        )


class TestFLExInitializeIsIdempotentLive:
    """FLExInitialize() brings the SLDR up and stays a no-op thereafter."""

    @pytest.mark.live_phase("FLExInit", "read")
    def test_initialize_then_initialize_again_does_not_raise(self):
        """A second FLExInitialize() must not raise and must leave the
        SLDR up.

        Before the fix, the second call still reached Sldr.Initialize(),
        caught the resulting InvalidOperationException in a bare
        `except Exception`, and logged it as a warning -- masking the
        genuine-failure case. Now the IsInitialized probe short-circuits
        it entirely.
        """
        FLExInitialize()
        assert Sldr.IsInitialized is True, (
            "SLDR is not up after FLExInitialize()"
        )

        # The idempotence assertion: calling again is a no-op, not a throw.
        FLExInitialize()
        assert Sldr.IsInitialized is True, (
            "A second FLExInitialize() left the SLDR down"
        )

        # Read back through a real SLDR data path, not just the flag.
        assert Sldr.LanguageTags.Count > 0, (
            "SLDR reports initialized but LanguageTags is empty -- the "
            "SLDR is not actually functional."
        )


class TestFLExCleanupIsIdempotentLive:
    """The new cleanup guard: a second FLExCleanup() must not throw."""

    @pytest.mark.live_phase("FLExInit", "read")
    def test_double_cleanup_then_reinitialize_full_cycle(self):
        """init -> cleanup -> cleanup -> init, all read back from the CLR.

        The second FLExCleanup() is the regression point: the real
        Sldr.Cleanup() raises
        InvalidOperationException("The SLDR has not been initialized.")
        when cold, so before the guard this call propagated that error out
        of a teardown function.
        """
        # Pre-state: bring the SLDR up and confirm it from the CLR.
        FLExInitialize()
        assert Sldr.IsInitialized is True
        tags_before = Sldr.LanguageTags.Count
        assert tags_before > 0, (
            f"SLDR up but LanguageTags.Count == {tags_before}"
        )
        print(f"[INFO] pre-state:  IsInitialized=True  "
              f"LanguageTags.Count={tags_before}")

        try:
            FLExCleanup()
            assert Sldr.IsInitialized is False, (
                "FLExCleanup() returned but the SLDR is still initialized"
            )

            # THE #249 CLEANUP PIN: this call threw before the fix.
            FLExCleanup()
            assert Sldr.IsInitialized is False, (
                "A second FLExCleanup() unexpectedly changed SLDR state"
            )
            print("[INFO] mid-state:  IsInitialized=False after two "
                  "FLExCleanup() calls, neither raised")
        finally:
            # Restore the session singleton no matter what failed above.
            FLExInitialize()

        # Post-state: read back that the re-init produced a *functional*
        # SLDR, not merely a flipped flag. An empty LanguageTags here
        # would mean later LDML reads fail and .ldml quarantine begins.
        assert Sldr.IsInitialized is True, (
            "SLDR did not come back up after the cleanup cycle"
        )
        tags_after = Sldr.LanguageTags.Count
        assert tags_after > 0, (
            f"SLDR re-initialized but LanguageTags.Count == {tags_after} -- "
            "the re-init cycle produced a non-functional SLDR."
        )
        print(f"[INFO] post-state: IsInitialized=True  "
              f"LanguageTags.Count={tags_after}")
        assert tags_after == tags_before, (
            f"LanguageTags.Count changed across the cleanup/re-init cycle: "
            f"{tags_before} -> {tags_after}"
        )
