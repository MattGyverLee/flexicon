#
#   test_issue618_resolver_type_check.py
#
#   Issue #618: Operations resolvers used to return any non-int argument
#   unchanged, so a wrong-type caller (a str, a list, a float) got a raw
#   AttributeError deep inside the method instead of an FP_ParameterError.
#   The shared root was BaseOperations._GetObject; per-class resolvers had
#   the same shape (issue #600 / WordformOperations.__ResolveWordform is
#   the model).
#
#   Offline: calls each private resolver directly on a bare instance.
#   The live counterpart is test_issue618_resolver_type_check_live.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import importlib
from types import SimpleNamespace

import pytest

from flexicon.code.exceptions import FP_NullParameterError, FP_ParameterError
from flexicon.code.BaseOperations import BaseOperations
from flexicon.code.Shared.arg_checks import is_non_lcm_value, require_lcm_object
from flexicon.code.Shared.wrapper_base import LCMObjectWrapper

# (module under flexicon.code, class, mangled-less private method name)
RESOLVERS = [
    ("Discourse.ConstChartCellTagOperations", "ConstChartCellTagOperations", "__ResolveRow"),
    ("Discourse.ConstChartCellTagOperations", "ConstChartCellTagOperations", "__ResolveTag"),
    ("Discourse.ConstChartClauseMarkerOperations", "ConstChartClauseMarkerOperations", "__ResolveObject"),
    ("Discourse.ConstChartClauseMarkerOperations", "ConstChartClauseMarkerOperations", "__ResolveRow"),
    ("Discourse.ConstChartMarkerOperations", "ConstChartMarkerOperations", "__ResolveMarker"),
    ("Discourse.ConstChartMovedTextOperations", "ConstChartMovedTextOperations", "__ResolveObject"),
    ("Discourse.ConstChartMovedTextOperations", "ConstChartMovedTextOperations", "__ResolveWordGroup"),
    ("Discourse.ConstChartMovedTextOperations", "ConstChartMovedTextOperations", "__ResolveChart"),
    ("Discourse.ConstChartOperations", "ConstChartOperations", "__ResolveObject"),
    ("Discourse.ConstChartRowOperations", "ConstChartRowOperations", "__ResolveObject"),
    ("Discourse.ConstChartRowOperations", "ConstChartRowOperations", "__ResolveChart"),
    ("Discourse.ConstChartWordGroupOperations", "ConstChartWordGroupOperations", "__ResolveObject"),
    ("Discourse.ConstChartWordGroupOperations", "ConstChartWordGroupOperations", "__ResolveRow"),
    ("Grammar.EnvironmentOperations", "EnvironmentOperations", "__ResolveObject"),
    ("Grammar.InflectionFeatureOperations", "InflectionFeatureOperations", "__ResolveInflectionClass"),
    ("Grammar.InflectionFeatureOperations", "InflectionFeatureOperations", "__ResolveFeatureStructure"),
    ("Grammar.InflectionFeatureOperations", "InflectionFeatureOperations", "__ResolveFeature"),
    ("Grammar.InflectionFeatureOperations", "InflectionFeatureOperations", "__ResolveFeatureSystem"),
    ("Grammar.InflectionFeatureOperations", "InflectionFeatureOperations", "__ResolvePOS"),
    ("Grammar.MorphRuleOperations", "MorphRuleOperations", "__ResolveObject"),
    ("Grammar.NaturalClassOperations", "NaturalClassOperations", "__GetNaturalClassObject"),
    ("Grammar.NaturalClassOperations", "NaturalClassOperations", "__GetPhonemeObject"),
    ("Grammar.POSOperations", "POSOperations", "__ResolveStemName"),
    ("Grammar.POSOperations", "POSOperations", "__ResolveObject"),
    ("Grammar.PhonFeatureOperations", "PhonFeatureOperations", "__ResolveObject"),
    ("Grammar.PhonemeOperations", "PhonemeOperations", "__GetPhonemeObject"),
    ("Grammar.PhonemeOperations", "PhonemeOperations", "__GetCodeObject"),
    ("Grammar.PhonologicalRuleOperations", "PhonologicalRuleOperations", "__ResolveFeature"),
    ("Grammar.PhonologicalRuleOperations", "PhonologicalRuleOperations", "__ResolveLcmObject"),
    ("Grammar.PhonologicalRuleOperations", "PhonologicalRuleOperations", "__ResolveObject"),
    ("Grammar.StratumOperations", "StratumOperations", "__ResolveObject"),
    ("Lexicon.AllomorphOperations", "AllomorphOperations", "__GetEntryObject"),
    ("Lexicon.AllomorphOperations", "AllomorphOperations", "__GetAllomorphObject"),
    ("Lexicon.AllomorphOperations", "AllomorphOperations", "__ResolveStemName"),
    ("Lexicon.AllomorphOperations", "AllomorphOperations", "__ResolveInflectionClass"),
    ("Lexicon.AllomorphOperations", "AllomorphOperations", "__GetEnvironmentObject"),
    ("Lexicon.EtymologyOperations", "EtymologyOperations", "__GetEntryObject"),
    ("Lexicon.EtymologyOperations", "EtymologyOperations", "__GetEtymologyObject"),
    ("Lexicon.ExampleOperations", "ExampleOperations", "__GetSenseObject"),
    ("Lexicon.ExampleOperations", "ExampleOperations", "__GetExampleObject"),
    ("Lexicon.LexEntryOperations", "LexEntryOperations", "__ResolveObject"),
    ("Lexicon.LexReferenceOperations", "LexReferenceOperations", "__ResolveRefType"),
    ("Lexicon.LexReferenceOperations", "LexReferenceOperations", "__ResolveLexRef"),
    ("Lexicon.LexReferenceOperations", "LexReferenceOperations", "__ResolveSenseOrEntry"),
    ("Lexicon.LexReferenceOperations", "LexReferenceOperations", "__ResolveEntry"),
    ("Lexicon.LexSenseOperations", "LexSenseOperations", "__GetEntryObject"),
    ("Lexicon.LexSenseOperations", "LexSenseOperations", "__GetSenseObject"),
    ("Lexicon.LexSenseOperations", "LexSenseOperations", "__GetSenseOwnerObject"),
    ("Lexicon.LexSenseOperations", "LexSenseOperations", "__GetSemanticDomainObject"),
    ("Lexicon.MSAOperations", "MSAOperations", "__ResolveSense"),
    ("Lexicon.MSAOperations", "MSAOperations", "__Resolve"),
    ("Lexicon.PronunciationOperations", "PronunciationOperations", "__GetEntryObject"),
    ("Lexicon.PronunciationOperations", "PronunciationOperations", "__GetPronunciationObject"),
    ("Lexicon.SemanticDomainOperations", "SemanticDomainOperations", "__ResolveObject"),
    ("Lexicon.VariantOperations", "VariantOperations", "__GetEntryObject"),
    ("Lexicon.VariantOperations", "VariantOperations", "__GetVariantObject"),
    ("Lists.OverlayOperations", "OverlayOperations", "__ResolveOverlay"),
    ("Lists.OverlayOperations", "OverlayOperations", "__ResolvePossList"),
    ("Lists.PossibilityListOperations", "PossibilityListOperations", "__ResolveList"),
    ("Lists.PossibilityListOperations", "PossibilityListOperations", "__ResolveItem"),
    ("Lists.possibility_item_base", "PossibilityItemOperations", "__ResolveObject"),
    ("Notebook.LocationOperations", "LocationOperations", "__ResolveObject"),
    ("Notebook.PersonOperations", "PersonOperations", "__ResolveObject"),
    ("Reversal.ReversalIndexEntryOperations", "ReversalIndexEntryOperations", "__ResolveObject"),
    ("Reversal.ReversalIndexEntryOperations", "ReversalIndexEntryOperations", "__GetIndexObject"),
    ("Reversal.ReversalIndexOperations", "ReversalIndexOperations", "__ResolveObject"),
    ("Scripture.ScrAnnotationsOperations", "ScrAnnotationsOperations", "__ResolveObject"),
    ("Scripture.ScrAnnotationsOperations", "ScrAnnotationsOperations", "__ResolveBook"),
    ("Scripture.ScrBookOperations", "ScrBookOperations", "__ResolveObject"),
    ("Scripture.ScrDraftOperations", "ScrDraftOperations", "__ResolveObject"),
    ("Scripture.ScrNoteOperations", "ScrNoteOperations", "__ResolveObject"),
    ("Scripture.ScrNoteOperations", "ScrNoteOperations", "__ResolveBook"),
    ("Scripture.ScrNoteOperations", "ScrNoteOperations", "__ResolveParagraph"),
    ("Scripture.ScrSectionOperations", "ScrSectionOperations", "__ResolveObject"),
    ("Scripture.ScrSectionOperations", "ScrSectionOperations", "__ResolveBook"),
    ("Scripture.ScrTxtParaOperations", "ScrTxtParaOperations", "__ResolveObject"),
    ("Scripture.ScrTxtParaOperations", "ScrTxtParaOperations", "__ResolveSection"),
    ("System.AnnotationDefOperations", "AnnotationDefOperations", "__AsDefn"),
    ("TextsWords.DiscourseOperations", "DiscourseOperations", "__GetTextObject"),
    ("TextsWords.DiscourseOperations", "DiscourseOperations", "__GetChartObject"),
    ("TextsWords.DiscourseOperations", "DiscourseOperations", "__GetRowObject"),
    ("TextsWords.ParagraphOperations", "ParagraphOperations", "__GetTextObject"),
    ("TextsWords.ParagraphOperations", "ParagraphOperations", "__GetParagraphObject"),
    ("TextsWords.SegmentOperations", "SegmentOperations", "__GetParagraphObject"),
    ("TextsWords.SegmentOperations", "SegmentOperations", "__GetSegmentObject"),
    ("TextsWords.SegmentOperations", "SegmentOperations", "__GetAnalysisObject"),
    ("TextsWords.TextOperations", "TextOperations", "__GetTextObject"),
    ("TextsWords.WfiAnalysisOperations", "WfiAnalysisOperations", "__GetWordformObject"),
    ("TextsWords.WfiAnalysisOperations", "WfiAnalysisOperations", "__GetAnalysisObject"),
    ("TextsWords.WfiAnalysisOperations", "WfiAnalysisOperations", "__GetAgentObject"),
    ("TextsWords.WfiAnalysisOperations", "WfiAnalysisOperations", "__ResolveOwningAnalysis"),
    ("TextsWords.WfiGlossOperations", "WfiGlossOperations", "__ResolveAnalysis"),
    ("TextsWords.WfiMorphBundleOperations", "WfiMorphBundleOperations", "__GetBundleObject"),
    ("TextsWords.WfiMorphBundleOperations", "WfiMorphBundleOperations", "__GetAnalysisObject"),
    ("TextsWords.WfiMorphBundleOperations", "WfiMorphBundleOperations", "__GetSenseObject"),
    ("TextsWords.WfiMorphBundleOperations", "WfiMorphBundleOperations", "__GetMorphObject"),
    ("TextsWords.WfiMorphBundleOperations", "WfiMorphBundleOperations", "__GetMSAObject"),
    ("TextsWords.WfiMorphBundleOperations", "WfiMorphBundleOperations", "__GetInflectionClassObject"),
]

WRONG_TYPE_ARGS = [
    pytest.param("not-an-object", id="str"),
    pytest.param(["a", "list"], id="list"),
    pytest.param(1.5, id="float"),
    pytest.param({"k": "v"}, id="dict"),
    pytest.param(b"bytes", id="bytes"),
    pytest.param(None, id="None"),
]


# Public methods that resolve their object-or-HVO argument inline (no
# separate private resolver). (module, class, method, call) where call
# builds the argument list around the wrong-type value ``bad``.
_STUB = SimpleNamespace(Hvo=1, MediaFilesOS=[], FeaturesOC=[])
PUBLIC_INLINE = [
    ("Grammar.InflectionFeatureOperations", "InflectionFeatureOperations", "GetFeatures", lambda b: (b,)),
    ("Grammar.InflectionFeatureOperations", "InflectionFeatureOperations", "GetFeatureConstraints", lambda b: (b,)),
    ("Lexicon.ExampleOperations", "ExampleOperations", "RemoveMediaFile", lambda b: (_STUB, b)),
    ("Lexicon.PronunciationOperations", "PronunciationOperations", "RemoveMediaFile", lambda b: (_STUB, b)),
    ("TextsWords.SegmentOperations", "SegmentOperations", "GetGloss", lambda b: (b,)),
    ("Shared.MediaOperations", "MediaOperations", "Delete", lambda b: (b,)),
    ("Shared.MediaOperations", "MediaOperations", "Duplicate", lambda b: (b,)),
    ("Shared.MediaOperations", "MediaOperations", "GetInternalPath", lambda b: (b,)),
    ("Shared.MediaOperations", "MediaOperations", "GetExternalPath", lambda b: (b,)),
    ("Shared.MediaOperations", "MediaOperations", "SetInternalPath", lambda b: (b, "x")),
    ("Shared.MediaOperations", "MediaOperations", "RenameMediaFile", lambda b: (b, "x.wav")),
    ("Shared.MediaOperations", "MediaOperations", "GetLabel", lambda b: (b,)),
    ("Shared.MediaOperations", "MediaOperations", "SetLabel", lambda b: (b, "x")),
    ("Shared.MediaOperations", "MediaOperations", "GetMediaType", lambda b: (b,)),
    ("Shared.MediaOperations", "MediaOperations", "GetOwners", lambda b: (b,)),
    ("Shared.MediaOperations", "MediaOperations", "GetGuid", lambda b: (b,)),
]


@pytest.mark.parametrize("module_name,class_name,method,call", PUBLIC_INLINE)
@pytest.mark.parametrize("bad", WRONG_TYPE_ARGS[:4])
def test_public_inline_resolver_wrong_type_raises_parameter_error(
    module_name, class_name, method, call, bad
):
    """Public methods with an inline int-or-object resolve also reject wrong types."""
    ops = _make_ops(module_name, class_name)
    with pytest.raises(FP_ParameterError):
        getattr(ops, method)(*call(bad))


class _Project:
    """Minimal project stand-in: Object(hvo) returns a marker stub."""

    writeEnabled = True

    def __init__(self):
        self.object_calls = []

    def Object(self, hvo):
        self.object_calls.append(hvo)
        return SimpleNamespace(Hvo=hvo)


def _make_ops(module_name, class_name):
    mod = importlib.import_module("flexicon.code." + module_name)
    cls = getattr(mod, class_name)
    ops = object.__new__(cls)
    ops.project = _Project()
    return ops


def _resolver(ops, class_name, method):
    # Private (double-underscore) methods are name-mangled with the
    # *defining* class; BaseOperations-style single-underscore names are not.
    if method.startswith("__"):
        return getattr(ops, "_" + class_name + method)
    return getattr(ops, method)


@pytest.mark.parametrize("module_name,class_name,method", RESOLVERS)
@pytest.mark.parametrize("bad", WRONG_TYPE_ARGS)
def test_resolver_wrong_type_raises_parameter_error(module_name, class_name, method, bad):
    """Every resolver turns a wrong-type argument into FP_ParameterError."""
    ops = _make_ops(module_name, class_name)
    resolver = _resolver(ops, class_name, method)
    # Resolvers that already ran _ValidateParam keep their dedicated
    # FP_NullParameterError for None; everything else must be the typed
    # FP_ParameterError (never a raw AttributeError).
    expected = (FP_ParameterError, FP_NullParameterError) if bad is None else FP_ParameterError
    with pytest.raises(expected):
        resolver(bad)


@pytest.mark.parametrize("module_name,class_name,method", RESOLVERS)
def test_resolver_object_is_not_rejected_by_type_check(module_name, class_name, method):
    """A non-builtin object (the LCM stand-in) is never rejected as wrong-typed.

    Resolvers may still reject it for class reasons (their own checks) or fail
    a pythonnet cast on a stub, but the #618 type check must not fire.
    """
    ops = _make_ops(module_name, class_name)
    resolver = _resolver(ops, class_name, method)
    stub = SimpleNamespace(Hvo=42)
    try:
        resolver(stub)
    except FP_ParameterError as e:
        assert "object or an int HVO, got" not in str(e)
    except Exception:
        # A stub cannot satisfy every concrete-interface cast; that is
        # not what this test is about.
        pass


class TestGetObjectSharedResolver:
    """BaseOperations._GetObject, the shared root of #618."""

    def _ops(self):
        ops = object.__new__(BaseOperations)
        ops.project = _Project()
        return ops

    @pytest.mark.parametrize("bad", WRONG_TYPE_ARGS)
    def test_wrong_type_raises_parameter_error_naming_expected(self, bad):
        ops = self._ops()
        with pytest.raises(FP_ParameterError, match="Expected an LCM object or an int HVO"):
            ops._GetObject(bad)

    def test_error_names_the_offending_type(self):
        with pytest.raises(FP_ParameterError, match="got str"):
            self._ops()._GetObject("oops")

    def test_int_hvo_still_resolves_through_project(self):
        ops = self._ops()
        obj = ops._GetObject(1234)
        assert ops.project.object_calls == [1234]
        assert obj.Hvo == 1234

    def test_lcm_object_still_returned_unchanged(self):
        ops = self._ops()
        stub = SimpleNamespace(Hvo=7)
        assert ops._GetObject(stub) is stub
        assert ops.project.object_calls == []

    def test_wrapper_is_unwrapped_to_the_raw_object(self):
        ops = self._ops()
        stub = SimpleNamespace(Hvo=7)
        assert ops._GetObject(LCMObjectWrapper(stub)) is stub


class TestArgChecksHelper:
    def test_require_returns_object_identity(self):
        stub = SimpleNamespace(Hvo=1)
        assert require_lcm_object(stub, "X") is stub

    @pytest.mark.parametrize("bad", ["s", [1], 1.5, {}, (), b"b", None, {1}])
    def test_require_rejects_builtins_and_none(self, bad):
        with pytest.raises(FP_ParameterError, match="Expected IFoo object"):
            require_lcm_object(bad, "IFoo")
        assert is_non_lcm_value(bad)

    def test_is_non_lcm_value_false_for_objects(self):
        assert not is_non_lcm_value(SimpleNamespace())
