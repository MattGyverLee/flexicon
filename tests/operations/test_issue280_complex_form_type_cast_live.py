#
#   test_issue280_complex_form_type_cast_live.py
#
#   Live write-path verification for issue #280:
#   FLExProject.LexiconSetComplexFormType (and its sibling
#   LexiconGetComplexFormType) gated their whole body on
#   `hasattr(entry_ref, "ComplexEntryTypesRS")` against a possibly
#   base-typed `entry_ref`, with no `else`. pythonnet only surfaces the
#   static type's attributes, so `hasattr` on an interface-typed
#   (ICmObject / HVO-resolved) view is always False regardless of the
#   concrete object -- the mechanism documented at
#   BaseOperations.py:1568-1576. That made LexiconSetComplexFormType a
#   silent no-op that reported success whenever entry_ref arrived
#   base-typed, and made LexiconGetComplexFormType silently return None
#   the same way.
#
#   The fix: cast_to_concrete(entry_ref) before the hasattr check, and
#   raise FP_ParameterError when the check is genuinely False (i.e. the
#   object really is not a LexEntryRef) instead of silently doing
#   nothing / returning None.
#
#   Each test re-reads the entry ref fresh from the LCM (by Hvo, through
#   ServiceLocator.GetObject, which is exactly the base-typed path that
#   used to defeat the hasattr check) so the assertions prove the write
#   actually persisted rather than asserting on the value just passed in.
#
#   Structure copied from tests/operations/test_target_live_smoke.py and
#   tests/operations/test_issue272_complex_form_live.py. Uses
#   target_sandbox (fresh tempdir copy of the Target .fwbackup), not the
#   in-place target_project, because other agents may be running live
#   sessions concurrently against the real Target.
#
#   Required invocation:
#
#       $env:FLEXLIBS_REQUIRE_LIVE = "1"
#       python -m pytest tests/operations/test_issue280_complex_form_type_cast_live.py \
#           -m requires_live_project -q
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon import cast_to_concrete
from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_"


def _first_complex_form_type(project):
    """
    Return the first ILexEntryType in the project's complex-form-types
    list (e.g. "Compound"), or skip the test if the Target has none.
    """
    complex_types_list = project.lp.LexDbOA.ComplexEntryTypesOA
    if complex_types_list is None:
        pytest.skip("Target has no ComplexEntryTypesOA list configured")

    types = list(complex_types_list.PossibilitiesOS)
    if not types:
        pytest.skip("Target's complex-form-types list is empty")
    return types[0]


def _base_typed_entry_ref(project, entry_ref):
    """
    Re-fetch entry_ref through ServiceLocator.GetObject(hvo) WITHOUT
    casting -- this is exactly the base-typed (ICmObject) shape that
    silently defeated the pre-fix `hasattr` guard. Deliberately does
    NOT call cast_to_concrete, unlike every other live test in this
    file, because reproducing the bug's precondition is the point.
    """
    return project.project.ServiceLocator.GetObject(entry_ref.Hvo)


def _reread_entry_ref_types(project, hvo):
    """Re-read ComplexEntryTypesRS straight from the LCM by Hvo."""
    reread = cast_to_concrete(project.project.ServiceLocator.GetObject(hvo))
    return [t.Hvo for t in reread.ComplexEntryTypesRS]


class TestLexiconSetComplexFormTypeCastLive:
    """LexiconSetComplexFormType must not silently no-op on a base-typed entry_ref."""

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_set_complex_form_type_persists_on_hvo_resolved_ref(
        self, target_sandbox
    ):
        """
        Pre-fix: hasattr(base_typed_entry_ref, "ComplexEntryTypesRS") was
        always False, so the method's body never ran and it reported
        success anyway (no exception, no write). Post-fix: the object is
        cast first, the write happens, and a fresh re-read confirms it.
        """
        assert target_sandbox.writeEnabled is True
        entries = target_sandbox.LexEntry
        cf_type = _first_complex_form_type(target_sandbox)

        component = None
        complex_form = None
        try:
            component = entries.Create(lexeme_form=f"{TEST_PREFIX}sun280")
            complex_form = entries.Create(
                lexeme_form=f"{TEST_PREFIX}sunflower280"
            )

            # Create a bare entry ref with no complex form type set yet.
            entry_ref = target_sandbox.LexiconAddComplexForm(
                complex_form, [component], None
            )
            assert entry_ref is not None
            ref_hvo = entry_ref.Hvo

            # --- pre-state, read back from the LCM ---
            before = _reread_entry_ref_types(target_sandbox, ref_hvo)
            assert before == [], (
                f"Expected no complex form type before the write, got {before}"
            )

            # Simulate the historically-untested HVO/base-typed path: the
            # object handed to LexiconSetComplexFormType is base-typed
            # (ICmObject), not the concrete ILexEntryRef.
            base_typed_ref = _base_typed_entry_ref(target_sandbox, entry_ref)
            assert not hasattr(base_typed_ref, "ComplexEntryTypesRS"), (
                "Precondition not met: ServiceLocator.GetObject() already "
                "surfaces ComplexEntryTypesRS on this pythonnet build, so "
                "this test would not be exercising the base-typed path "
                "the bug depended on."
            )

            target_sandbox.LexiconSetComplexFormType(base_typed_ref, cf_type)

            # --- post-state, re-queried fresh from the LCM ---
            after = _reread_entry_ref_types(target_sandbox, ref_hvo)
            assert after == [cf_type.Hvo], (
                "Complex form type did not persist to the LCM for a "
                f"base-typed entry_ref; re-read ComplexEntryTypesRS gave {after}. "
                "This is the issue #280 silent no-op."
            )
        finally:
            for created in (complex_form, component):
                if created is not None:
                    entries.Delete(created)

    @pytest.mark.live_phase("FLExProject", "modify")
    def test_set_complex_form_type_raises_on_wrong_object_type(
        self, target_sandbox
    ):
        """
        A genuinely wrong object type (a LexEntry, not a LexEntryRef)
        must raise FP_ParameterError rather than silently succeeding.
        """
        assert target_sandbox.writeEnabled is True
        entries = target_sandbox.LexEntry
        cf_type = _first_complex_form_type(target_sandbox)

        entry = None
        try:
            entry = entries.Create(lexeme_form=f"{TEST_PREFIX}notaref280")

            with pytest.raises(FP_ParameterError):
                target_sandbox.LexiconSetComplexFormType(entry, cf_type)
        finally:
            if entry is not None:
                entries.Delete(entry)


class TestLexiconGetComplexFormTypeCastLive:
    """LexiconGetComplexFormType must not silently return None on a base-typed entry_ref."""

    @pytest.mark.live_phase("FLExProject", "read")
    def test_get_complex_form_type_reads_on_hvo_resolved_ref(
        self, target_sandbox
    ):
        assert target_sandbox.writeEnabled is True
        entries = target_sandbox.LexEntry
        cf_type = _first_complex_form_type(target_sandbox)

        component = None
        complex_form = None
        try:
            component = entries.Create(lexeme_form=f"{TEST_PREFIX}moon280")
            complex_form = entries.Create(
                lexeme_form=f"{TEST_PREFIX}moonlight280"
            )

            entry_ref = target_sandbox.LexiconAddComplexForm(
                complex_form, [component], cf_type
            )
            ref_hvo = entry_ref.Hvo

            base_typed_ref = _base_typed_entry_ref(target_sandbox, entry_ref)
            assert not hasattr(base_typed_ref, "ComplexEntryTypesRS")

            result = target_sandbox.LexiconGetComplexFormType(base_typed_ref)
            assert result is not None and result.Hvo == cf_type.Hvo, (
                "LexiconGetComplexFormType silently returned "
                f"{result!r} for a base-typed entry_ref instead of the "
                "type actually set on it. This is the issue #280 shape "
                "applied to the getter."
            )

            # Re-read from a fresh Hvo lookup too, to rule out any state
            # cached on entry_ref/base_typed_ref themselves.
            reread_ref = target_sandbox.project.ServiceLocator.GetObject(
                ref_hvo
            )
            reread_result = target_sandbox.LexiconGetComplexFormType(
                reread_ref
            )
            assert reread_result is not None and reread_result.Hvo == cf_type.Hvo
        finally:
            for created in (complex_form, component):
                if created is not None:
                    entries.Delete(created)

    @pytest.mark.live_phase("FLExProject", "read")
    def test_get_complex_form_type_raises_on_wrong_object_type(
        self, target_sandbox
    ):
        assert target_sandbox.writeEnabled is True
        entries = target_sandbox.LexEntry

        entry = None
        try:
            entry = entries.Create(lexeme_form=f"{TEST_PREFIX}notaref280b")
            with pytest.raises(FP_ParameterError):
                target_sandbox.LexiconGetComplexFormType(entry)
        finally:
            if entry is not None:
                entries.Delete(entry)
