#
#   test_277_environment_sequence_property.py
#
#   Class: TestP1LiveReflectionPropertyNames / TestP2GetSequenceRegression /
#          TestP3ReorderEndToEndViaTypedParent / TestP4ParentHvoContract
#          Issue #277, EnvironmentOperations half -- the reorder-hook defect.
#
#          Grammar/EnvironmentOperations.py `_GetSequence` (:72-88) read
#          `parent.EnvironmentsOA.PossibilitiesOS`. `IPhPhonData` (the
#          `parent` here -- `project.lp.PhonologicalDataOA`) has no
#          `EnvironmentsOA` property anywhere in the LCM API; it owns
#          `EnvironmentsOS` directly, with no intervening possibility
#          list. `EnvironmentsOA` appears nowhere else in the codebase --
#          this reads like a copy/paste of
#          `InflectionFeatureOperations._GetSequence`'s
#          `parent.FeaturesOA.PossibilitiesOS` (correct for THAT parent
#          type, never true for `IPhPhonData`).
#
#          Every BaseOperations reorder method (`Sort`, `MoveUp`,
#          `MoveDown`, `MoveToIndex` -- BaseOperations.py:693/799/896/982)
#          calls `self._GetSequence(parent)`, so all four raised
#          `AttributeError` for environments before this fix.
#
#          This file pins TWO SEPARATE claims, deliberately not conflated
#          (see the task briefing for issue #277):
#
#            1. The property name is now correct (`EnvironmentsOS`, not
#               `EnvironmentsOA.PossibilitiesOS`) -- TestP1 (live
#               reflection) and TestP2 (direct `_GetSequence` call, the
#               regression that fails on the OLD code and passes on the
#               fix).
#
#            2. The reorder path is genuinely exercisable end-to-end when
#               callers pass the already-typed parent object (the only
#               way `EnvironmentOperations` itself ever obtains
#               `PhonologicalDataOA`, per `GetAll`/`Create`/`Delete`/
#               `Duplicate`, all of which read
#               `self.project.lp.PhonologicalDataOA` directly rather than
#               resolving an HVO) -- TestP3.
#
#          Claim 2 is deliberately NOT extended to the HVO-parent entry
#          path. TestP4 measures, live, whether
#          `BaseOperations._GetObject` resolves a genuine `IPhPhonData`
#          HVO into something that still exposes `EnvironmentsOS` --
#          per the flexicon#260 lesson, a bare `project.Object(hvo)`
#          view is pythonnet's static-wrapper-gated `ICmObject`, which
#          does not surface interface-specific members without a cast.
#          `_GetObject` (BaseOperations.py:1673-1675) performs no such
#          cast. TestP4 documents whatever this codebase's ACTUAL live
#          behaviour is; it does not assume the HVO path works just
#          because the object path does.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


class TestP1LiveReflectionPropertyNames:
    """
    P1 (live reflection): confirm via .NET reflection on IPhPhonData that
    EnvironmentsOS is real and EnvironmentsOA does not exist -- the
    ground truth the fix in EnvironmentOperations._GetSequence rests on.
    """

    @pytest.mark.live_phase("EnvironmentOperations", "read")
    def test_environments_os_exists_environments_oa_does_not(self, target_sandbox):
        from SIL.LCModel import IPhPhonData
        import clr

        clr_type = clr.GetClrType(IPhPhonData)
        prop_names = {p.Name for p in clr_type.GetProperties()}

        assert "EnvironmentsOS" in prop_names, (
            "expected IPhPhonData.EnvironmentsOS to exist -- if this now "
            "fails, the LCM API has changed and this fix must be "
            "re-derived."
        )
        assert "EnvironmentsOA" not in prop_names, (
            "EnvironmentsOA now exists on IPhPhonData -- the original "
            "code may have been targeting a different (newer/older) LCM "
            "version; re-verify before assuming the fix is still correct."
        )


class TestP2GetSequenceRegression:
    """
    P2 (load-bearing regression): call `_GetSequence` directly on the
    resolved IPhPhonData. This fails with AttributeError on the
    unmodified source (`parent.EnvironmentsOA` does not exist) and
    passes once `_GetSequence` reads `parent.EnvironmentsOS`.

    `_GetSequence` is a single-underscore method (not name-mangled), so
    it is reachable directly for this narrow, deterministic pin -- this
    is the smallest possible falsifier for the exact line that broke.
    """

    @pytest.mark.live_phase("EnvironmentOperations", "read")
    def test_get_sequence_returns_the_real_environments_owning_sequence(
        self, target_sandbox
    ):
        sandbox = target_sandbox
        phon_data = sandbox.lp.PhonologicalDataOA
        assert phon_data is not None, (
            "test setup error: Target has no PhonologicalDataOA -- cannot "
            "exercise this regression."
        )

        before_count = len(list(sandbox.Environments.GetAll()))

        # THE ACTUAL DEFECT SITE: on unmodified source this line raises
        # AttributeError: 'PhPhonData' object has no attribute
        # 'EnvironmentsOA' (or, once pythonnet resolves the cast, no
        # such member at all). On the fix, it returns the real
        # EnvironmentsOS owning sequence.
        sequence = sandbox.Environments._GetSequence(phon_data)

        assert sequence.Count == before_count, (
            f"_GetSequence(phon_data) did not return the real "
            f"EnvironmentsOS sequence: Count={sequence.Count!r} but "
            f"GetAll() enumerated {before_count} environments."
        )


class TestP3ReorderEndToEndViaTypedParent:
    """
    P3 (load-bearing, end-to-end): with the fix, MoveUp genuinely
    reorders environments in the LCM when called with the same
    already-typed PhonologicalDataOA object that GetAll/Create/Delete/
    Duplicate all use internally. Re-reads via a FRESH GetAll() call,
    never the in-memory objects just created.
    """

    @pytest.mark.live_phase("EnvironmentOperations", "modify")
    def test_move_up_reorders_environments_via_typed_parent(self, target_sandbox):
        sandbox = target_sandbox
        phon_data = sandbox.lp.PhonologicalDataOA

        env_a = sandbox.Environments.Create(f"{TEST_PREFIX}277_a")
        env_b = sandbox.Environments.Create(f"{TEST_PREFIX}277_b")
        env_c = sandbox.Environments.Create(f"{TEST_PREFIX}277_c")
        try:
            # Sanity: freshly created environments append at the end, in
            # creation order (a, b, c).
            names_before = [
                sandbox.Environments.GetName(e)
                for e in sandbox.Environments.GetAll()
            ]
            idx_b = names_before.index(f"{TEST_PREFIX}277_b")
            idx_c = names_before.index(f"{TEST_PREFIX}277_c")
            assert idx_b == idx_c - 1, (
                "test setup error: expected 'b' immediately before 'c' "
                f"before any reordering; got order {names_before!r}"
            )

            # THE PATH UNDER TEST: MoveUp -> BaseOperations.MoveUp ->
            # self._GetObject(phon_data) [already an object, passthrough]
            # -> self._GetSequence(parent) [the fixed line].
            moved = sandbox.Environments.MoveUp(phon_data, env_c, positions=1)
            assert moved == 1, f"expected MoveUp to move exactly 1 position, got {moved}"

            # Fresh re-fetch -- never the env_c/phon_data objects held
            # above -- via a brand-new GetAll() enumeration.
            names_after = [
                sandbox.Environments.GetName(e)
                for e in sandbox.Environments.GetAll()
            ]
            idx_c_after = names_after.index(f"{TEST_PREFIX}277_c")
            idx_b_after = names_after.index(f"{TEST_PREFIX}277_b")
            assert idx_c_after == idx_b_after - 1, (
                f"MoveUp did not persist through the LCM: expected 'c' "
                f"immediately before 'b' after the move; got "
                f"{names_after!r}"
            )
        finally:
            sandbox.Environments.Delete(env_a)
            sandbox.Environments.Delete(env_b)
            sandbox.Environments.Delete(env_c)


class TestP4ParentHvoContractFinding:
    """
    P4 (finding, not a fix): measures live whether
    `BaseOperations._GetObject` resolving a genuine IPhPhonData HVO
    (int) yields an object that still exposes `EnvironmentsOS`, per the
    flexicon#260 lesson that a bare `project.Object(hvo)` view is
    pythonnet's static-wrapper-gated `ICmObject` and does not surface
    interface-specific members without an explicit cast.

    This class documents the MEASURED outcome; see the module header
    and the task's cycle report for what it implies about the
    HVO-parent entry path into MoveUp/MoveDown/MoveToIndex/Sort for
    EnvironmentOperations specifically.
    """

    @pytest.mark.live_phase("EnvironmentOperations", "read")
    def test_get_object_on_genuine_phon_data_hvo_environments_os_reachability(
        self, target_sandbox
    ):
        sandbox = target_sandbox
        phon_data = sandbox.lp.PhonologicalDataOA
        phon_data_hvo = phon_data.Hvo

        assert isinstance(phon_data_hvo, int), (
            "test setup error: phon_data_hvo must be a genuine Python "
            "int -- otherwise the HVO entry path under test is not "
            "actually exercised."
        )

        resolved = sandbox.Environments._GetObject(phon_data_hvo)

        # This is the MEASURED finding, not an assumption: record
        # whatever pythonnet actually does with a bare-resolved
        # IPhPhonData HVO. If this assertion ever flips to True on an
        # unmodified BaseOperations._GetObject, the HVO-parent path has
        # started working for free and the finding in the task report
        # is stale -- re-derive it.
        has_environments_os = hasattr(resolved, "EnvironmentsOS")
        assert has_environments_os is False, (
            "_GetObject(phon_data_hvo) now exposes EnvironmentsOS on the "
            "resolved object -- the HVO-parent reorder path may now work "
            "end-to-end where it previously would not; re-verify and "
            "update the #277 report/finding before relying on this "
            "result. (Measured value: "
            f"hasattr(resolved, 'EnvironmentsOS') = {has_environments_os!r})"
        )
