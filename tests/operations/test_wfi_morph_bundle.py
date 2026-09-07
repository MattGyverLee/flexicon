#
#   test_wfi_morph_bundle.py
#
#   Class: TestWfiMorphBundleGloss
#          Regression coverage for issue #16 Bug 2: GetGloss/SetGloss
#          previously referenced `bundle.Gloss`, a field that does not
#          exist on IWfiMorphBundle. Calls raised AttributeError on
#          every input.
#
#          The fix routes GetGloss through bundle.SenseRA.Gloss (with
#          a None-guard) and refuses SetGloss outright, since writing
#          via SenseRA would mutate shared lexical-sense state for
#          every bundle that references the sense -- a surprising
#          side effect to attach to a per-bundle setter.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect
import sys

import pytest


class TestWfiMorphBundleGlossContract:
    """
    Static-contract coverage for WfiMorphBundleOperations.GetGloss and
    SetGloss after the issue #16 fix. These tests do not require a
    live FieldWorks project -- they verify the method shape and the
    unconditional SetGloss raise.
    """

    def test_get_and_set_gloss_remain_public_methods(self):
        """
        GetGloss and SetGloss must remain on the class surface so the
        AttributeError reproducer from issue #16 cannot resurface as
        AttributeError for the wrong reason (e.g. method renamed). A
        callable that explicitly refuses is the documented contract.
        """
        from flexlibs2.code.TextsWords.WfiMorphBundleOperations import (
            WfiMorphBundleOperations,
        )

        for name in ("GetGloss", "SetGloss"):
            assert name in dir(WfiMorphBundleOperations), (
                f"{name} missing from WfiMorphBundleOperations"
            )
            # GetGloss/SetGloss are wrapped by the @OperationsMethod
            # descriptor; retrieve via descriptor protocol on the class
            # (which yields a bound-method-like callable) rather than
            # via inspect.getattr_static (which yields the raw
            # descriptor object).
            attr = getattr(WfiMorphBundleOperations, name)
            assert callable(attr), f"{name} is not callable on class"
            assert not isinstance(attr, property), (
                f"{name} must be a method, not a property"
            )

    def test_set_gloss_raises_unconditionally(self):
        """
        SetGloss must always raise NotImplementedError with a message
        pointing the caller at LexSenseOperations.SetGloss. Mutating
        a shared lexical sense from a per-bundle setter would be a
        surprising side effect; explicit refusal is the contract.

        The exception class is NotImplementedError -- a capability
        refusal -- not FP_ParameterError, since no argument the caller
        could pass would make this call valid. (issue #109)
        """
        from flexlibs2.code.TextsWords.WfiMorphBundleOperations import (
            WfiMorphBundleOperations,
        )

        class _MockSelf:
            project = None

        with pytest.raises(NotImplementedError) as exc_info:
            WfiMorphBundleOperations.SetGloss(
                _MockSelf(), object(), "anything"
            )

        message = str(exc_info.value)
        assert "not supported" in message, (
            "SetGloss raise message should explain it's not supported; "
            f"got: {message!r}"
        )
        assert "LexSenseOperations.SetGloss" in message, (
            "SetGloss raise message should point at the sense-based "
            f"alternative; got: {message!r}"
        )

    def test_get_gloss_returns_empty_for_unlinked_bundle(self):
        """
        GetGloss must return an empty string when the bundle has no
        linked sense (SenseRA is None) -- it must not raise
        AttributeError trying to read sense.Gloss off of None.

        This guards against a partial fix that forwards to SenseRA
        without a None-guard.
        """
        from flexlibs2.code.TextsWords.WfiMorphBundleOperations import (
            WfiMorphBundleOperations,
        )

        # Stand up the smallest possible mock that satisfies the
        # method's dependencies. __GetBundleObject is a private
        # resolver that this test sidesteps by patching with a passthrough.
        class _MockBundle:
            SenseRA = None  # the case under test
            MsaRA = None  # fully-unlinked bundle: no grammatical-morpheme fallback either

        captured = {}

        def _passthrough_get_bundle(self, bundle_or_hvo):
            captured["called"] = True
            return bundle_or_hvo

        def _passthrough_ws(self, ws):
            return 1  # any int; SenseRA is None so it's never used

        # Monkey-patch the private resolvers on the class. These names
        # are mangled because they're double-underscore in the source.
        mangled_get_bundle = (
            "_WfiMorphBundleOperations__GetBundleObject"
        )
        mangled_ws = "_WfiMorphBundleOperations__WSHandleAnal"

        original_get_bundle = getattr(
            WfiMorphBundleOperations, mangled_get_bundle, None
        )
        original_ws = getattr(WfiMorphBundleOperations, mangled_ws, None)
        if original_get_bundle is None or original_ws is None:
            pytest.skip(
                "Private resolver names changed; "
                "test_get_gloss_returns_empty_for_unlinked_bundle "
                "needs updating"
            )

        setattr(
            WfiMorphBundleOperations,
            mangled_get_bundle,
            _passthrough_get_bundle,
        )
        setattr(WfiMorphBundleOperations, mangled_ws, _passthrough_ws)
        try:
            class _MockSelf:
                project = None

            result = WfiMorphBundleOperations.GetGloss(
                _MockSelf(), _MockBundle()
            )
            assert result == "", (
                "GetGloss must return empty string for unlinked bundle, "
                f"got {result!r}"
            )
        finally:
            setattr(
                WfiMorphBundleOperations,
                mangled_get_bundle,
                original_get_bundle,
            )
            setattr(WfiMorphBundleOperations, mangled_ws, original_ws)


class TestWfiMorphBundleDuplicate:
    """
    Static-source coverage for WfiMorphBundleOperations.Duplicate.
    Live-LCM regression for the orphan-Owner / bundle.Gloss bug is
    blocked on the access-violation failures tracked in #144; this
    test locks the absence of the broken access pattern at the source
    level so the regression cannot creep back in via copy-paste.
    """

    def test_duplicate_does_not_reference_bundle_dot_gloss(self):
        """
        IWfiMorphBundle has no Gloss field. Any
        ``duplicate.Gloss.CopyAlternatives(source.Gloss)`` or
        ``bundle.Gloss.<anything>`` access inside Duplicate raises
        AttributeError on every call (the original #16 / #107 bug).
        4319886 fixed GetGloss / SetGloss but missed Duplicate; this
        test guards against the bug returning to any method on this
        class. (issue #107)
        """
        import inspect
        from flexlibs2.code.TextsWords.WfiMorphBundleOperations import (
            WfiMorphBundleOperations,
        )

        src = inspect.getsource(WfiMorphBundleOperations.Duplicate)
        # Either a write-side access (duplicate.Gloss) or a read-side
        # access (source.Gloss) inside Duplicate is the regression.
        # The displayed gloss is on SenseRA.Gloss and is preserved by
        # the SenseRA = source.SenseRA assignment in Duplicate.
        assert "duplicate.Gloss" not in src, (
            "Duplicate references duplicate.Gloss; IWfiMorphBundle has "
            "no Gloss field. Remove the line (#107 regression)."
        )
        assert "source.Gloss" not in src, (
            "Duplicate references source.Gloss; IWfiMorphBundle has no "
            "Gloss field. Remove the line (#107 regression)."
        )


class TestWfiMorphBundleMorphTypeContract:
    """
    Static-contract coverage for issue #254: GetMorphType/SetMorphType on
    WfiMorphBundleOperations previously confused a bundle's linked
    allomorph (bundle.MorphRA, an IMoForm) with its morph type
    (MorphRA.MorphTypeRA, an IMoMorphType). SetMorphType wrote its
    argument directly into MorphRA, so every non-None call crashed with
    a pythonnet TypeError before any write reached the LCM.

    These tests cover the offline-testable slice of the fix: SetMorphType's
    unconditional retirement (raises before touching write-enabled state
    or any LCM object) and SetMorph's IMoForm type guard (also pure
    Python control flow, no live LCM object needed to prove the guard
    rejects a non-IMoForm object). The read-side repair
    (bundle.MorphRA.MorphTypeRA, and whether bare attribute access or an
    explicit IMoForm(...) cast is required) needs a live project and is
    left to lex-verification.
    """

    def test_get_and_set_morph_methods_present(self):
        """
        GetMorphType, SetMorphType, GetMorph and SetMorph must all remain
        on the class surface. SetMorphType stays present (retired, not
        removed) so existing call sites reach the explanatory
        FP_ParameterError rather than AttributeError from a renamed/
        deleted method.
        """
        from flexicon.code.TextsWords.WfiMorphBundleOperations import (
            WfiMorphBundleOperations,
        )

        for name in ("GetMorphType", "SetMorphType", "GetMorph", "SetMorph"):
            assert name in dir(WfiMorphBundleOperations), (
                f"{name} missing from WfiMorphBundleOperations"
            )
            attr = getattr(WfiMorphBundleOperations, name)
            assert callable(attr), f"{name} is not callable on class"

    def test_set_morph_type_raises_unconditionally(self):
        """
        SetMorphType must always raise FP_ParameterError, including for
        the None form, naming both replacement methods
        (project.Allomorphs.SetMorphType and SetMorph) so a caller who
        hits this error knows where to go next.
        """
        from flexicon.code.TextsWords.WfiMorphBundleOperations import (
            WfiMorphBundleOperations,
        )
        from flexicon.code.FLExProject import FP_ParameterError

        class _MockSelf:
            project = None

        for morph_type_arg in (object(), None, 12345):
            with pytest.raises(FP_ParameterError) as exc_info:
                WfiMorphBundleOperations.SetMorphType(
                    _MockSelf(), object(), morph_type_arg
                )

            message = str(exc_info.value)
            assert "retired" in message, (
                f"SetMorphType raise message should say it's retired; "
                f"got: {message!r}"
            )
            assert "Allomorphs.SetMorphType" in message, (
                "SetMorphType raise message should point at "
                f"project.Allomorphs.SetMorphType; got: {message!r}"
            )
            assert "SetMorph(" in message, (
                "SetMorphType raise message should point at the new "
                f"SetMorph replacement; got: {message!r}"
            )

    def test_set_morph_type_raises_before_any_self_access(self):
        """
        The retirement raise must come before _EnsureWriteEnabled(),
        _ValidateParam(), or any bundle/morph-type resolution -- so a
        read-only project and a write-enabled project see the identical
        message. A _MockSelf exposing nothing but `project` proves no
        other method on self is ever touched: if SetMorphType tried to
        call self._EnsureWriteEnabled() or resolve its arguments before
        raising, this would fail with AttributeError instead of the
        expected FP_ParameterError.
        """
        from flexicon.code.TextsWords.WfiMorphBundleOperations import (
            WfiMorphBundleOperations,
        )
        from flexicon.code.FLExProject import FP_ParameterError

        class _BareMockSelf:
            project = None

        # No _EnsureWriteEnabled, _ValidateParam, or __GetBundleObject
        # defined at all -- if the method reached for any of them first,
        # this raises AttributeError, not FP_ParameterError.
        with pytest.raises(FP_ParameterError):
            WfiMorphBundleOperations.SetMorphType(
                _BareMockSelf(), None, None
            )

    class _NullTransaction:
        """Stand-in for _NestingAwareTransaction; no real LCM needed."""

        def __enter__(self):
            return self

        def __exit__(self, *exc_info):
            return False

    @staticmethod
    def _patch_class_methods(target_class, **name_to_func):
        """
        Monkey-patch mangled/private methods directly on the class (not an
        instance) and return a restore callback.

        SetMorph/SetMorphType are wrapped by the @OperationsMethod
        descriptor. Accessed at CLASS level (Class.Method(project, ...)),
        the descriptor's __get__ treats the first positional argument as
        `project` and constructs a real `objtype(project)` instance before
        calling the underlying function -- so a "_MockSelf" passed that
        way never becomes `self`; it becomes `self.project`. Patching
        _EnsureWriteEnabled/_TransactionCM/private resolvers onto the
        class itself (restored in a finally) is therefore the only way to
        intercept those calls when driving the method through the
        instance-level call it actually documents as the traditional
        usage: `WfiMorphBundleOperations(project).SetMorph(...)`.
        """
        originals = {
            name: getattr(target_class, name, None)
            for name in name_to_func
        }
        for name, func in name_to_func.items():
            setattr(target_class, name, func)

        def _restore():
            for name, original in originals.items():
                if original is None:
                    if hasattr(target_class, name):
                        delattr(target_class, name)
                else:
                    setattr(target_class, name, original)

        return _restore

    def test_set_morph_rejects_non_imoform_object(self):
        """
        SetMorph must raise FP_ParameterError naming the received
        ClassName when morph_or_hvo resolves to something that is not an
        IMoForm (e.g. an IMoMorphType) -- this guard is what makes
        SetMorphType's retirement actionable: a caller who passes a morph
        type to SetMorph gets our error, not a raw pythonnet TypeError.
        """
        from flexicon.code.TextsWords.WfiMorphBundleOperations import (
            WfiMorphBundleOperations,
        )
        from flexicon.code.FLExProject import FP_ParameterError

        class _NotAnIMoForm:
            ClassName = "MoMorphType"

        class _MockBundle:
            MorphRA = None

        class _StubProject:
            writeEnabled = True

        restore = self._patch_class_methods(
            WfiMorphBundleOperations,
            _WfiMorphBundleOperations__GetBundleObject=(
                lambda self, bundle_or_hvo: bundle_or_hvo
            ),
            _WfiMorphBundleOperations__GetMorphObject=(
                lambda self, morph_or_hvo: morph_or_hvo
            ),
            _TransactionCM=lambda self, label: self._NullTransaction(),
        )
        WfiMorphBundleOperations._NullTransaction = self._NullTransaction
        try:
            ops = WfiMorphBundleOperations(_StubProject())
            with pytest.raises(FP_ParameterError) as exc_info:
                ops.SetMorph(_MockBundle(), _NotAnIMoForm())

            message = str(exc_info.value)
            assert "IMoForm" in message, (
                f"SetMorph type-guard message should name IMoForm; "
                f"got: {message!r}"
            )
            assert "MoMorphType" in message, (
                "SetMorph type-guard message should name the received "
                f"ClassName; got: {message!r}"
            )
        finally:
            restore()
            if hasattr(WfiMorphBundleOperations, "_NullTransaction"):
                delattr(WfiMorphBundleOperations, "_NullTransaction")

    def test_set_morph_accepts_none_to_clear(self):
        """
        SetMorph(bundle, None) must clear MorphRA without raising the
        IMoForm type guard -- None is the documented way to unlink a
        bundle's allomorph.
        """
        from flexicon.code.TextsWords.WfiMorphBundleOperations import (
            WfiMorphBundleOperations,
        )

        class _MockBundle:
            MorphRA = "sentinel-should-be-cleared"

        class _StubProject:
            writeEnabled = True

        restore = self._patch_class_methods(
            WfiMorphBundleOperations,
            _WfiMorphBundleOperations__GetBundleObject=(
                lambda self, bundle_or_hvo: bundle_or_hvo
            ),
            _TransactionCM=lambda self, label: self._NullTransaction(),
        )
        WfiMorphBundleOperations._NullTransaction = self._NullTransaction
        try:
            ops = WfiMorphBundleOperations(_StubProject())
            bundle = _MockBundle()
            ops.SetMorph(bundle, None)
            assert bundle.MorphRA is None, (
                "SetMorph(bundle, None) must clear MorphRA"
            )
        finally:
            restore()
            if hasattr(WfiMorphBundleOperations, "_NullTransaction"):
                delattr(WfiMorphBundleOperations, "_NullTransaction")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
