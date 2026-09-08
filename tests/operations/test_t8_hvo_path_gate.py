#
#   test_t8_hvo_path_gate.py
#
#   Class: TestHvoPathCastGetForm / TestHvoPathCastSetForm
#          Cycle-17 Checkpoint 5 gate, LEG 1 -- closes P4's unmeasured
#          HVO axis. AllomorphOperations.__GetAllomorphObject merges the
#          int and object branches at :1359-1362 and applies its single
#          getattr(obj,"ClassName")+cast at :1364-1369 AFTER the merge.
#          Passing an already-concrete object exercises the cast
#          VACUOUSLY (it is already the right type); these tests pass a
#          GENUINE Python int (an existing MoAffixAllomorph's .Hvo,
#          asserted isinstance(hvo, int) BEFORE the call) through two
#          independently-COVERED call sites -- GetForm (:813, read-only)
#          and SetForm (:858, mutates) -- so the cast is exercised on the
#          entry path that actually needs it.
#
#   Basis: cycle-16's P1 measured hasattr(bare_object, "Form") -> False
#          on a bare sandbox.Object(hvo) view of a real MoAffixAllomorph
#          (see TestT8LiveHasattrTrap in test_t8_allomorph_feature_sync.py),
#          so "Form" is itself concrete-only through the HVO entry path.
#          If __GetAllomorphObject's cast is deleted (mutation M-G1), a
#          bare ICmObject reaches `allomorph.Form...` and raises
#          AttributeError.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def _make_entry(sandbox, tag):
    return sandbox.LexEntry.Create(f"{TEST_PREFIX}{tag}")


class TestHvoPathCastGetForm:
    """
    Primary site (G1): GetForm (:813) is one of the 4 COVERED sites and
    is read-only, so it is safe to exercise directly on target_sandbox.
    """

    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_get_form_via_genuine_hvo_int_reads_concrete_form(self, target_sandbox):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "t8gate_getform")
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}gform", morphType="suffix"
            )
            hvo = allo.Hvo

            # THE TRAP: this must be a genuine int, not an already-typed
            # object -- otherwise the cast at :1364-1369 is exercised
            # vacuously (the object is already concrete before the call).
            assert isinstance(hvo, int), (
                "test setup error: hvo must be a genuine Python int, not "
                "an already-typed allomorph object -- otherwise the cast "
                "under test is exercised vacuously."
            )
            assert not hasattr(sandbox.Object(hvo), "Form"), (
                "P1 precondition failed: Form is reachable on the bare "
                "ICmObject view -- the trap this test relies on no "
                "longer holds; re-derive the site."
            )

            form_text = sandbox.Allomorphs.GetForm(hvo)
            assert form_text == f"{TEST_PREFIX}gform", (
                f"GetForm(hvo) did not reach the concrete Form member: "
                f"got {form_text!r}"
            )
        finally:
            sandbox.LexEntry.Delete(entry)


class TestHvoPathCastSetForm:
    """
    Second covered site (G1 falsifier step): SetForm (:858) mutates, so
    this is sandbox-only, and re-reads the value back from a FRESH
    sandbox.Object(hvo) re-fetch after the write (never asserts on the
    input value).
    """

    @pytest.mark.live_phase("AllomorphOperations", "modify")
    def test_set_form_via_genuine_hvo_int_writes_through_concrete_form(
        self, target_sandbox
    ):
        sandbox = target_sandbox
        entry = _make_entry(sandbox, "t8gate_setform")
        try:
            allo = sandbox.Allomorphs.Create(
                entry, f"{TEST_PREFIX}sform_old", morphType="suffix"
            )
            hvo = allo.Hvo
            assert isinstance(hvo, int)

            sandbox.Allomorphs.SetForm(hvo, f"{TEST_PREFIX}sform_new")

            # Re-fetch fresh from the LCM after the write -- never assert
            # on the value just passed in.
            reread = sandbox.Allomorphs.GetForm(sandbox.Object(hvo))
            assert reread == f"{TEST_PREFIX}sform_new", (
                f"SetForm(hvo, ...) did not persist through the concrete "
                f"Form member: re-read {reread!r}"
            )
        finally:
            sandbox.LexEntry.Delete(entry)
