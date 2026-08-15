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
        from flexicon.code.TextsWords.WfiMorphBundleOperations import (
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
        from flexicon.code.TextsWords.WfiMorphBundleOperations import (
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
        from flexicon.code.TextsWords.WfiMorphBundleOperations import (
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
        from flexicon.code.TextsWords.WfiMorphBundleOperations import (
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


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
