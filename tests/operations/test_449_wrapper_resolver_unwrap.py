#
#   test_449_wrapper_resolver_unwrap.py
#
#   Class: TestUnwrapLcmHelper / TestResolversUnwrapWrapperItems
#          Offline regression coverage for issue #449 -- GetAll() wrapper
#          objects (Allomorph, MorphosyntaxAnalysis, CompoundRule,
#          AffixTemplate, PhonologicalRule) crashing or silently no-op'ing
#          when passed back into another Operations method.
#
#          Uses plain Python stand-ins (fake LCM objects with a ClassName
#          attribute) and monkeypatches each module's pythonnet cast
#          symbol with a pass-through recorder, following the pattern in
#          tests/operations/test_allomorph_owner.py. This proves each
#          resolver unwraps the wrapper to the raw fake LCM object BEFORE
#          doing anything else with it -- the shape of the bug (equality/
#          IndexOf/Remove/cast against a wrapper instance instead of the
#          raw object) rather than any one call site.
#
#          These tests FAIL on unmodified origin/main code: before the
#          fix, each resolver hands the wrapper itself (not the raw
#          object) to the recorder, which the assertions below reject.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import sys

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.BaseOperations import BaseOperations
from flexicon.code.Shared.wrapper_base import LCMObjectWrapper
from flexicon.code.PythonicWrapper import PythonicWrapper

from flexicon.code.Lexicon import AllomorphOperations as allomorph_module
from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations

from flexicon.code.Lexicon import MSAOperations as msa_module
from flexicon.code.Lexicon.MSAOperations import MSAOperations

from flexicon.code.Grammar import MorphRuleOperations as morph_rule_module
from flexicon.code.Grammar.MorphRuleOperations import MorphRuleOperations

from flexicon.code.Grammar import PhonologicalRuleOperations as phon_rule_module
from flexicon.code.Grammar.PhonologicalRuleOperations import PhonologicalRuleOperations

from flexicon.code.TextsWords import WfiMorphBundleOperations as morph_bundle_module
from flexicon.code.TextsWords.WfiMorphBundleOperations import WfiMorphBundleOperations


# ---------------------------------------------------------------------------
# Minimal LCM stand-ins -- no FieldWorks project required
# ---------------------------------------------------------------------------


class _FakeLcmObject:
    """Stand-in for a raw LCM object reachable via .ClassName."""

    def __init__(self, class_name, hvo=1):
        self.ClassName = class_name
        self.Hvo = hvo


class _FakeProject:
    """Minimal stand-in satisfying BaseOperations.__init__'s `project` arg."""

    def __init__(self):
        self._objects = {}

    def Object(self, hvo):
        return self._objects[hvo]


# ---------------------------------------------------------------------------
# T2: BaseOperations._UnwrapLcm unit tests
# ---------------------------------------------------------------------------


class TestUnwrapLcmHelper:
    """BaseOperations._UnwrapLcm in isolation."""

    def _ops(self):
        return BaseOperations(_FakeProject())

    def test_unwraps_lcm_object_wrapper(self):
        raw = _FakeLcmObject("SomeUnrecognisedClass")
        wrapped = LCMObjectWrapper(raw)

        result = self._ops()._UnwrapLcm(wrapped)

        assert result is raw

    def test_unwraps_pythonic_wrapper(self):
        raw = _FakeLcmObject("SomeUnrecognisedClass")
        wrapped = PythonicWrapper(raw)

        result = self._ops()._UnwrapLcm(wrapped)

        assert result is raw

    def test_passes_through_raw_object(self):
        raw = _FakeLcmObject("SomeUnrecognisedClass")

        assert self._ops()._UnwrapLcm(raw) is raw

    @pytest.mark.parametrize("value", [1, 0, -5, "some-guid", "", None])
    def test_passes_through_int_str_and_none(self, value):
        assert self._ops()._UnwrapLcm(value) is value

    def test_idempotent_on_already_unwrapped_value(self):
        raw = _FakeLcmObject("SomeUnrecognisedClass")
        wrapped = LCMObjectWrapper(raw)

        once = self._ops()._UnwrapLcm(wrapped)
        twice = self._ops()._UnwrapLcm(once)

        assert once is raw
        assert twice is raw


# ---------------------------------------------------------------------------
# T2 continued: BaseOperations._GetObject / reorder methods unwrap wrappers
# ---------------------------------------------------------------------------


class _FakeSequence(list):
    """Stand-in for an ILcmOwningSequence: list plus a .Count and .MoveTo."""

    @property
    def Count(self):
        return len(self)

    def MoveTo(self, ihvoStart, ihvoEnd, dest, ihvoDstStart):
        # Minimal single-item MoveTo emulation sufficient for these tests.
        item = self.pop(ihvoStart)
        if ihvoDstStart > ihvoStart:
            ihvoDstStart -= 1
        self.insert(ihvoDstStart, item)


class _ReorderOps(BaseOperations):
    """BaseOperations subclass exposing a fixed sequence for reorder tests."""

    def __init__(self, sequence):
        super().__init__(_FakeProject())
        self._sequence = sequence

    def _GetSequence(self, parent):
        return self._sequence

    def _EnsureWriteEnabled(self):
        pass

    def _TransactionCM(self, label):
        import contextlib

        @contextlib.contextmanager
        def _cm():
            yield

        return _cm()


class TestBaseOperationsResolversUnwrap:
    """MoveToIndex (representative of the reorder family) unwraps its item."""

    def test_get_object_unwraps_wrapper(self):
        raw = _FakeLcmObject("LexEntry")
        wrapped = LCMObjectWrapper(raw)

        ops = BaseOperations(_FakeProject())
        result = ops._GetObject(wrapped)

        assert result is raw, (
            "_GetObject must unwrap a wrapper to its raw LCM object "
            "(issue #449); it must not return the wrapper unchanged."
        )

    def test_move_to_index_locates_wrapped_item_in_raw_sequence(self):
        raw0, raw1, raw2 = (
            _FakeLcmObject("MoStemAllomorph", hvo=0),
            _FakeLcmObject("MoStemAllomorph", hvo=1),
            _FakeLcmObject("MoStemAllomorph", hvo=2),
        )
        sequence = _FakeSequence([raw0, raw1, raw2])
        ops = _ReorderOps(sequence)

        # Item handed back to MoveToIndex is a wrapper around raw2, exactly
        # the shape of an item taken from a wrapper-returning GetAll().
        wrapped_item = LCMObjectWrapper(raw2)

        moved = ops.MoveToIndex(parent_or_hvo=object(), item=wrapped_item, new_index=0)

        assert moved is True
        assert list(sequence) == [raw2, raw0, raw1], (
            "MoveToIndex must find the wrapper's raw object in the raw "
            "sequence via equality; on origin/main code the wrapper never "
            "compares equal to any raw sequence element, so ValueError "
            "'Item not found in sequence' is raised instead."
        )

    def test_find_common_sequence_unwraps_both_items(self):
        owner = _FakeLcmObject("LexEntry", hvo=100)
        raw1 = _FakeLcmObject("MoStemAllomorph", hvo=1)
        raw2 = _FakeLcmObject("MoStemAllomorph", hvo=2)
        for r in (raw1, raw2):
            r.Owner = owner
            r.OwningFlid = 555

        class _OwnerWithSequence:
            ClassName = "LexEntry"
            AlternateFormsOS = _FakeSequence([raw1, raw2])

            def GetType(self):
                return self

            def GetProperties(self):
                class _PropInfo:
                    def __init__(self, name, value):
                        self.Name = name
                        self._value = value

                    def GetValue(self, parent, _):
                        return self._value

                return [_PropInfo("AlternateFormsOS", self.AlternateFormsOS)]

        ops = BaseOperations(_FakeProject())
        ops._GetObject = lambda hvo: _OwnerWithSequence()

        wrapped1 = LCMObjectWrapper(raw1)
        wrapped2 = LCMObjectWrapper(raw2)

        sequence = ops._FindCommonSequence(wrapped1, wrapped2)

        assert list(sequence) == [raw1, raw2]


# ---------------------------------------------------------------------------
# T2 continued: per-Operations-class private resolvers
# ---------------------------------------------------------------------------


@pytest.fixture
def allomorph_cast_recorder(monkeypatch):
    """Pass-through recorders for IMoStemAllomorph / IMoAffixAllomorph."""
    calls = []

    def _record(name):
        def _cast(obj):
            calls.append((name, obj))
            return obj

        return _cast

    monkeypatch.setattr(allomorph_module, "IMoStemAllomorph", _record("IMoStemAllomorph"))
    monkeypatch.setattr(allomorph_module, "IMoAffixAllomorph", _record("IMoAffixAllomorph"))
    return calls


class TestAllomorphOperationsResolverUnwraps:
    def test_get_allomorph_object_unwraps_before_casting(self, allomorph_cast_recorder):
        raw = _FakeLcmObject("MoStemAllomorph", hvo=42)
        wrapped = LCMObjectWrapper(raw)

        ops = AllomorphOperations(_FakeProject())
        result = ops._AllomorphOperations__GetAllomorphObject(wrapped)

        assert result is raw, (
            "__GetAllomorphObject must resolve a GetAll() wrapper to the "
            "raw allomorph before casting; on origin/main code the cast is "
            "attempted on the wrapper itself, which raises TypeError "
            "against a real pythonnet interface."
        )
        assert allomorph_cast_recorder == [("IMoStemAllomorph", raw)]

    def test_get_allomorph_object_unwraps_pythonic_wrapper(self, allomorph_cast_recorder):
        raw = _FakeLcmObject("MoAffixAllomorph", hvo=7)
        wrapped = PythonicWrapper(raw)

        ops = AllomorphOperations(_FakeProject())
        result = ops._AllomorphOperations__GetAllomorphObject(wrapped)

        assert result is raw
        assert allomorph_cast_recorder == [("IMoAffixAllomorph", raw)]


@pytest.fixture
def msa_cast_recorder(monkeypatch):
    calls = []

    def _record(name):
        def _cast(obj):
            calls.append((name, obj))
            return obj

        return _cast

    monkeypatch.setattr(msa_module, "IMoStemMsa", _record("IMoStemMsa"))
    monkeypatch.setattr(msa_module, "IMoInflAffMsa", _record("IMoInflAffMsa"))
    monkeypatch.setattr(msa_module, "IMoDerivAffMsa", _record("IMoDerivAffMsa"))
    monkeypatch.setattr(msa_module, "IMoUnclassifiedAffixMsa", _record("IMoUnclassifiedAffixMsa"))
    return calls


class TestMSAOperationsResolverUnwraps:
    def test_get_msa_object_unwraps_before_casting(self, msa_cast_recorder):
        raw = _FakeLcmObject("MoInflAffMsa", hvo=9)
        wrapped = LCMObjectWrapper(raw)

        ops = MSAOperations(_FakeProject())
        result = ops._MSAOperations__GetMsaObject(wrapped)

        assert result is raw, (
            "__GetMsaObject's ad-hoc `._obj` branch has been replaced with "
            "the shared _UnwrapLcm helper (issue #449); it must still "
            "unwrap an LCMObjectWrapper."
        )
        assert msa_cast_recorder == [("IMoInflAffMsa", raw)]


class TestMorphRuleOperationsResolverUnwraps:
    def test_resolve_object_unwraps_compound_rule_wrapper(self):
        raw = _FakeLcmObject("MoEndoCompound", hvo=3)
        wrapped = LCMObjectWrapper(raw)

        ops = MorphRuleOperations(_FakeProject())
        result = ops._MorphRuleOperations__ResolveObject(wrapped)

        assert result is raw, (
            "__ResolveObject must unwrap a CompoundRule/AffixTemplate "
            "wrapper before any downstream sequence membership check "
            "(IndexOf/Remove) or attribute assignment (StratumRA, "
            "Disabled), both of which silently fail against the wrapper "
            "itself on origin/main code."
        )

    def test_resolve_object_unwraps_pythonic_wrapper(self):
        raw = _FakeLcmObject("MoInflAffixTemplate", hvo=4)
        wrapped = PythonicWrapper(raw)

        ops = MorphRuleOperations(_FakeProject())
        result = ops._MorphRuleOperations__ResolveObject(wrapped)

        assert result is raw


class TestPhonologicalRuleOperationsResolverUnwraps:
    def test_resolve_object_unwraps_via_shared_helper(self):
        raw = _FakeLcmObject("PhRegularRule", hvo=5)
        wrapped = LCMObjectWrapper(raw)

        ops = PhonologicalRuleOperations(_FakeProject())
        result = ops._PhonologicalRuleOperations__ResolveObject(wrapped)

        assert result is raw, (
            "The old ad-hoc `hasattr(rule_or_hvo, '_obj') and "
            "hasattr(rule_or_hvo, '_concrete')` duck-typed check has been "
            "replaced with the shared _UnwrapLcm isinstance check; it must "
            "still unwrap an LCMObjectWrapper the same way."
        )

    def test_resolve_object_unwraps_pythonic_wrapper_too(self):
        """
        The old duck-typed check only recognised LCMObjectWrapper-shaped
        objects (via `_obj`/`_concrete`); a PythonicWrapper item was left
        unwrapped. The shared helper fixes both.
        """
        raw = _FakeLcmObject("PhMetathesisRule", hvo=6)
        wrapped = PythonicWrapper(raw)

        ops = PhonologicalRuleOperations(_FakeProject())
        result = ops._PhonologicalRuleOperations__ResolveObject(wrapped)

        assert result is raw


@pytest.fixture
def morph_bundle_cast_recorder(monkeypatch):
    calls = []

    def _record(obj):
        calls.append(obj)
        return obj

    monkeypatch.setattr(morph_bundle_module, "cast_to_concrete", _record)
    return calls


class TestWfiMorphBundleOperationsResolversUnwrap:
    def test_get_morph_object_unwraps_before_cast_to_concrete(self, morph_bundle_cast_recorder):
        raw = _FakeLcmObject("MoStemAllomorph", hvo=11)
        wrapped = LCMObjectWrapper(raw)

        ops = WfiMorphBundleOperations(_FakeProject())
        result = ops._WfiMorphBundleOperations__GetMorphObject(wrapped)

        assert result is raw
        assert morph_bundle_cast_recorder == [raw]

    def test_get_msa_object_unwraps_before_cast_to_concrete(self, morph_bundle_cast_recorder):
        raw = _FakeLcmObject("MoDerivAffMsa", hvo=12)
        wrapped = LCMObjectWrapper(raw)

        ops = WfiMorphBundleOperations(_FakeProject())
        result = ops._WfiMorphBundleOperations__GetMSAObject(wrapped)

        assert result is raw
        assert morph_bundle_cast_recorder == [raw]


class TestLexSenseSetGrammaticalInfoUnwraps:
    def test_unwraps_msa_wrapper_before_assignment(self):
        from flexicon.code.Lexicon.LexSenseOperations import LexSenseOperations

        raw_msa = _FakeLcmObject("MoStemMsa", hvo=21)
        wrapped_msa = LCMObjectWrapper(raw_msa)

        class _FakeSense:
            def __init__(self):
                self.MorphoSyntaxAnalysisRA = None

        sense = _FakeSense()

        class _Ops(LexSenseOperations):
            def __init__(self):
                super().__init__(_FakeProject())

            def _EnsureWriteEnabled(self):
                pass

            def _ValidateParam(self, value, name):
                pass

            def _TransactionCM(self, label):
                import contextlib

                @contextlib.contextmanager
                def _cm():
                    yield

                return _cm()

            def _LexSenseOperations__GetSenseObject(self, sense_or_hvo):
                return sense

        _Ops().SetGrammaticalInfo(sense, wrapped_msa)

        assert sense.MorphoSyntaxAnalysisRA is raw_msa, (
            "SetGrammaticalInfo must unwrap a MorphosyntaxAnalysis wrapper "
            "before assigning to MorphoSyntaxAnalysisRA; assigning the "
            "wrapper itself raises a pythonnet TypeError."
        )
