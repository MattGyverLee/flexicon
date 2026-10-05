"""
Tests for MSAOperations exception-feature wrappers (issue #574).

Covers ``GetExceptionFeatures`` / ``AddExceptionFeature`` /
``RemoveExceptionFeature`` over ``ProdRestrictRC`` ("Exception features"
in FLEx, used by HermitCrab to block rules/affixes).

Uses mocks for the FLExProject/LCM layer -- no live FieldWorks project
required for the orchestration logic. The pythonnet interface casts
(``IMoStemMsa`` / ``IMoInflAffMsa`` / ``IMoDerivAffMsa`` /
``IMoUnclassifiedAffixMsa`` / ``ICmPossibility``) are patched to identity
because the fakes below are already concrete-typed stand-ins; the one
test that needs a failing cast re-patches ``ICmPossibility`` locally.

Copyright 2026
"""

import contextlib
from unittest.mock import Mock, patch

import pytest

from flexicon.code.Lexicon.MSAOperations import MSAOperations
import flexicon.code.Lexicon.MSAOperations as msa_ops_module
from flexicon.code.FLExProject import (
    FP_ParameterError,
    FP_NullParameterError,
    FP_ReadOnlyError,
)


class _FakeRC(list):
    """Stand-in for an LCM reference collection (ProdRestrictRC)."""

    @property
    def Count(self):
        return len(self)

    def Add(self, item):
        self.append(item)

    def Remove(self, item):
        super().remove(item)


class _FakeMSA:
    """Concrete-typed MSA stand-in (ClassName drives the per-type mapping).

    Mirrors LCM: MoStemMsa -> ProdRestrictRC; MoInflAffMsa ->
    FromProdRestrictRC; MoDerivAffMsa -> From/ToProdRestrictRC. Fields the
    real type lacks are absent (AttributeError), as in LCM (issue #630).
    """

    def __init__(self, class_name, features=(), to_features=()):
        self.ClassName = class_name
        if class_name == "MoStemMsa":
            self.ProdRestrictRC = _FakeRC(features)
        elif class_name == "MoInflAffMsa":
            self.FromProdRestrictRC = _FakeRC(features)
        elif class_name == "MoDerivAffMsa":
            self.FromProdRestrictRC = _FakeRC(features)
            self.ToProdRestrictRC = _FakeRC(to_features)


def _primary(msa):
    """The collection a default (side='from') call reads/writes."""
    if msa.ClassName == "MoStemMsa":
        return msa.ProdRestrictRC
    return msa.FromProdRestrictRC


class _FakePossibility:
    """ICmPossibility stand-in."""

    def __init__(self, name):
        self.name = name


@pytest.fixture
def ops():
    project = Mock()
    project.writeEnabled = True
    ops = MSAOperations(project)
    # Bypass the real transaction machinery -- not under test here.
    ops._TransactionCM = Mock(
        side_effect=lambda label: contextlib.nullcontext()
    )
    # Interface casts become identity: fakes are already concrete.
    patches = [
        patch.object(msa_ops_module, "IMoStemMsa", side_effect=lambda o: o),
        patch.object(msa_ops_module, "IMoInflAffMsa", side_effect=lambda o: o),
        patch.object(msa_ops_module, "IMoDerivAffMsa", side_effect=lambda o: o),
        patch.object(
            msa_ops_module, "IMoUnclassifiedAffixMsa", side_effect=lambda o: o
        ),
        patch.object(msa_ops_module, "ICmPossibility", side_effect=lambda o: o),
    ]
    for p in patches:
        p.start()
    yield ops
    for p in reversed(patches):
        p.stop()


# ---------- GetExceptionFeatures ----------

class TestGetExceptionFeatures:
    @pytest.mark.parametrize(
        "class_name",
        ["MoStemMsa", "MoInflAffMsa", "MoDerivAffMsa"],
    )
    def test_returns_features_for_supported_msa_types(self, ops, class_name):
        f1, f2 = _FakePossibility("pl"), _FakePossibility("3sg")
        msa = _FakeMSA(class_name, [f1, f2])

        assert ops.GetExceptionFeatures(msa) == [f1, f2]

    def test_unclassified_msa_warns_and_returns_empty(self, ops, caplog):
        msa = _FakeMSA("MoUnclassifiedAffixMsa")

        with caplog.at_level("WARNING"):
            assert ops.GetExceptionFeatures(msa) == []
        assert any("MoUnclassifiedAffixMsa" in r.getMessage() for r in caplog.records)

    def test_empty_collection_returns_empty(self, ops):
        assert ops.GetExceptionFeatures(_FakeMSA("MoStemMsa")) == []

    def test_accepts_hvo(self, ops):
        f1 = _FakePossibility("pl")
        msa = _FakeMSA("MoStemMsa", [f1])
        ops.project.Object = Mock(return_value=msa)

        assert ops.GetExceptionFeatures(1234) == [f1]
        ops.project.Object.assert_called_once_with(1234)

    def test_none_raises_null_parameter_error(self, ops):
        with pytest.raises(FP_NullParameterError):
            ops.GetExceptionFeatures(None)


# ---------- AddExceptionFeature ----------

class TestAddExceptionFeature:
    def test_adds_feature_and_opens_transaction(self, ops):
        msa = _FakeMSA("MoStemMsa")
        feat = _FakePossibility("pl")

        ops.AddExceptionFeature(msa, feat)

        assert list(_primary(msa)) == [feat]
        assert ops._TransactionCM.call_count == 1

    def test_redundant_add_is_noop_without_transaction(self, ops):
        feat = _FakePossibility("pl")
        msa = _FakeMSA("MoStemMsa", [feat])

        ops.AddExceptionFeature(msa, feat)

        assert list(_primary(msa)) == [feat]
        assert ops._TransactionCM.call_count == 0

    def test_add_by_hvo(self, ops):
        msa = _FakeMSA("MoInflAffMsa")
        feat = _FakePossibility("pl")
        ops.project.Object = Mock(side_effect=[msa, feat])

        ops.AddExceptionFeature(111, 222)

        assert list(_primary(msa)) == [feat]

    def test_unclassified_msa_raises_parameter_error(self, ops):
        msa = _FakeMSA("MoUnclassifiedAffixMsa")

        with pytest.raises(FP_ParameterError) as excinfo:
            ops.AddExceptionFeature(msa, _FakePossibility("pl"))

        assert "MoUnclassifiedAffixMsa" in str(excinfo.value)
        assert ops._TransactionCM.call_count == 0

    def test_non_possibility_feature_raises_parameter_error(self, ops):
        msa = _FakeMSA("MoStemMsa")
        not_a_possibility = Mock(ClassName="LexEntry")

        def _cast(obj):
            raise TypeError("cannot cast to ICmPossibility")

        with patch.object(msa_ops_module, "ICmPossibility", side_effect=_cast):
            with pytest.raises(FP_ParameterError):
                ops.AddExceptionFeature(msa, not_a_possibility)

        assert list(_primary(msa)) == []
        assert ops._TransactionCM.call_count == 0

    def test_none_msa_raises_null_parameter_error(self, ops):
        with pytest.raises(FP_NullParameterError):
            ops.AddExceptionFeature(None, _FakePossibility("pl"))

    def test_none_feature_raises_null_parameter_error(self, ops):
        with pytest.raises(FP_NullParameterError):
            ops.AddExceptionFeature(_FakeMSA("MoStemMsa"), None)

    def test_read_only_project_raises(self, ops):
        ops.project.writeEnabled = False

        with pytest.raises(FP_ReadOnlyError):
            ops.AddExceptionFeature(
                _FakeMSA("MoStemMsa"), _FakePossibility("pl")
            )


# ---------- RemoveExceptionFeature ----------

class TestRemoveExceptionFeature:
    def test_removes_present_feature_and_opens_transaction(self, ops):
        feat = _FakePossibility("pl")
        other = _FakePossibility("3sg")
        msa = _FakeMSA("MoDerivAffMsa", [feat, other])

        ops.RemoveExceptionFeature(msa, feat)

        assert list(_primary(msa)) == [other]
        assert ops._TransactionCM.call_count == 1

    def test_absent_feature_is_noop_without_transaction(self, ops):
        feat = _FakePossibility("pl")
        msa = _FakeMSA("MoStemMsa", [_FakePossibility("3sg")])

        ops.RemoveExceptionFeature(msa, feat)

        assert len(_primary(msa)) == 1
        assert ops._TransactionCM.call_count == 0

    def test_unclassified_msa_raises_parameter_error(self, ops):
        msa = _FakeMSA("MoUnclassifiedAffixMsa")

        with pytest.raises(FP_ParameterError):
            ops.RemoveExceptionFeature(msa, _FakePossibility("pl"))

        assert ops._TransactionCM.call_count == 0

    def test_none_msa_raises_null_parameter_error(self, ops):
        with pytest.raises(FP_NullParameterError):
            ops.RemoveExceptionFeature(None, _FakePossibility("pl"))

    def test_read_only_project_raises(self, ops):
        ops.project.writeEnabled = False

        with pytest.raises(FP_ReadOnlyError):
            ops.RemoveExceptionFeature(
                _FakeMSA("MoStemMsa"), _FakePossibility("pl")
            )


# ---------- Issue #630: per-type mapping and side keyword ----------

class TestPerTypeMappingAndSide:
    def test_infl_affix_reads_from_field(self, ops):
        f = _FakePossibility("pl")
        msa = _FakeMSA("MoInflAffMsa", [f])

        assert ops.GetExceptionFeatures(msa) == [f]
        assert ops.GetExceptionFeatures(msa, side="from") == [f]

    def test_infl_affix_add_remove_use_from_field(self, ops):
        msa = _FakeMSA("MoInflAffMsa")
        f = _FakePossibility("pl")

        ops.AddExceptionFeature(msa, f)
        ops.AddExceptionFeature(msa, f)  # second add: no change
        assert list(msa.FromProdRestrictRC) == [f]
        assert ops._TransactionCM.call_count == 1

        ops.RemoveExceptionFeature(msa, f)
        assert list(msa.FromProdRestrictRC) == []

    def test_deriv_sides_are_independent(self, ops):
        f, g = _FakePossibility("a"), _FakePossibility("b")
        msa = _FakeMSA("MoDerivAffMsa")

        ops.AddExceptionFeature(msa, f)  # default from
        ops.AddExceptionFeature(msa, g, side="to")

        assert list(msa.FromProdRestrictRC) == [f]
        assert list(msa.ToProdRestrictRC) == [g]
        assert ops.GetExceptionFeatures(msa, side="from") == [f]
        assert ops.GetExceptionFeatures(msa, side="to") == [g]

        ops.RemoveExceptionFeature(msa, g, side="to")
        assert list(msa.FromProdRestrictRC) == [f]
        assert list(msa.ToProdRestrictRC) == []

    @pytest.mark.parametrize("side", ["from", "to"])
    def test_stem_ignores_side(self, ops, side):
        f = _FakePossibility("pl")
        msa = _FakeMSA("MoStemMsa")

        ops.AddExceptionFeature(msa, f, side=side)

        assert list(msa.ProdRestrictRC) == [f]
        assert ops.GetExceptionFeatures(msa, side=side) == [f]

    def test_infl_affix_get_side_to_warns_and_returns_empty(self, ops, caplog):
        msa = _FakeMSA("MoInflAffMsa", [_FakePossibility("pl")])

        with caplog.at_level("WARNING"):
            assert ops.GetExceptionFeatures(msa, side="to") == []
        assert any("side='to'" in r.getMessage() for r in caplog.records)

    @pytest.mark.parametrize("method", ["add", "remove"])
    def test_infl_affix_side_to_raises(self, ops, method):
        msa = _FakeMSA("MoInflAffMsa")
        f = _FakePossibility("pl")
        calls = {
            "add": lambda: ops.AddExceptionFeature(msa, f, side="to"),
            "remove": lambda: ops.RemoveExceptionFeature(msa, f, side="to"),
        }
        with pytest.raises(FP_ParameterError) as excinfo:
            calls[method]()
        assert "FromProdRestrictRC" in str(excinfo.value)
        assert ops._TransactionCM.call_count == 0

    @pytest.mark.parametrize("class_name", ["MoStemMsa", "MoDerivAffMsa"])
    @pytest.mark.parametrize("bad", ["both", "FROM", "", None, 1])
    def test_invalid_side_raises(self, ops, class_name, bad):
        msa = _FakeMSA(class_name)
        f = _FakePossibility("pl")

        with pytest.raises(FP_ParameterError):
            ops.GetExceptionFeatures(msa, side=bad)
        with pytest.raises(FP_ParameterError):
            ops.AddExceptionFeature(msa, f, side=bad)
        with pytest.raises(FP_ParameterError):
            ops.RemoveExceptionFeature(msa, f, side=bad)

    def test_unsupported_type_error_message_names_real_fields(self, ops):
        msa = _FakeMSA("MoUnclassifiedAffixMsa")

        with pytest.raises(FP_ParameterError) as excinfo:
            ops.AddExceptionFeature(msa, _FakePossibility("pl"))

        msg = str(excinfo.value)
        assert "MoUnclassifiedAffixMsa" in msg
        for token in (
            "MoStemMsa (ProdRestrictRC)",
            "MoInflAffMsa (FromProdRestrictRC)",
            "ToProdRestrictRC",
        ):
            assert token in msg
        # The old self-contradicting wording is gone.
        assert "does not carry exception features (ProdRestrictRC)" not in msg


# ---------- ChangeAffixVariant: exception-feature carry-over / warnings ----------

class _FakeSense:
    def __init__(self, msa):
        self.MorphoSyntaxAnalysisRA = msa


class _FakeEntry:
    Hvo = 900

    def __init__(self):
        self.SensesOS = []
        self.MorphoSyntaxAnalysesOC = _FakeRC()


def _affix(class_name, entry, hvo, from_feats=(), to_feats=()):
    msa = _FakeMSA(class_name, from_feats, to_feats)
    msa.Hvo = hvo
    msa.Owner = entry
    msa.IsValidObject = True
    msa.PartOfSpeechRA = None
    msa.FromPartOfSpeechRA = None
    msa.ToPartOfSpeechRA = None
    msa.FromInflectionClassRA = None
    msa.ToInflectionClassRA = None
    msa.StratumRA = None
    msa.SlotsRC = _FakeRC()
    msa.InflFeatsOA = None
    return msa


@pytest.fixture
def cav(ops):
    """ops wired so ChangeAffixVariant runs against fakes."""
    extra = [
        patch.object(msa_ops_module, "ILexEntry", side_effect=lambda o: o),
        patch.object(msa_ops_module, "SandboxGenericMSA", new=Mock()),
        patch.object(msa_ops_module, "MsaType", new=Mock()),
    ]
    for p in extra:
        p.start()

    def run(source_class, target_kind, from_feats=(), to_feats=()):
        entry = _FakeEntry()
        src = _affix(source_class, entry, 1, from_feats, to_feats)
        entry.MorphoSyntaxAnalysesOC.append(src)
        entry.SensesOS.append(_FakeSense(src))
        target_class = {
            "infl": "MoInflAffMsa",
            "deriv": "MoDerivAffMsa",
            "unclassified": "MoUnclassifiedAffixMsa",
        }[target_kind]
        new = _affix(target_class, entry, 2)
        ops._MSAOperations__CreateAndAttach = Mock(return_value=new)
        return ops.ChangeAffixVariant(src, target_kind), src

    yield run
    for p in reversed(extra):
        p.stop()


def _lost_messages(caplog):
    return [r.getMessage() for r in caplog.records if "will be lost" in r.getMessage()]


class TestChangeAffixVariantExceptionFeatures:
    def test_infl_to_deriv_copies_from_no_lost_warning(self, cav, caplog):
        f = _FakePossibility("pl")
        with caplog.at_level("WARNING"):
            new, _ = cav("MoInflAffMsa", "deriv", from_feats=[f])
        assert list(new.FromProdRestrictRC) == [f]
        assert list(new.ToProdRestrictRC) == []
        assert _lost_messages(caplog) == []

    def test_infl_to_unclassified_warns_from_lost(self, cav, caplog):
        with caplog.at_level("WARNING"):
            cav("MoInflAffMsa", "unclassified", from_feats=[_FakePossibility("pl")])
        lost = _lost_messages(caplog)
        assert len(lost) == 1 and "FromProdRestrictRC" in lost[0]

    def test_infl_to_unclassified_empty_no_warning(self, cav, caplog):
        with caplog.at_level("WARNING"):
            cav("MoInflAffMsa", "unclassified")
        assert _lost_messages(caplog) == []

    def test_deriv_to_infl_copies_from_warns_only_to(self, cav, caplog):
        f, g = _FakePossibility("a"), _FakePossibility("b")
        with caplog.at_level("WARNING"):
            new, _ = cav("MoDerivAffMsa", "infl", from_feats=[f], to_feats=[g])
        assert list(new.FromProdRestrictRC) == [f]
        lost = _lost_messages(caplog)
        assert len(lost) == 1
        assert "ToProdRestrictRC" in lost[0] and "FromProdRestrictRC" not in lost[0]

    def test_deriv_to_infl_from_only_no_warning(self, cav, caplog):
        with caplog.at_level("WARNING"):
            new, _ = cav("MoDerivAffMsa", "infl", from_feats=[_FakePossibility("a")])
        assert len(new.FromProdRestrictRC) == 1
        assert _lost_messages(caplog) == []

    def test_deriv_to_unclassified_warns_both(self, cav, caplog):
        with caplog.at_level("WARNING"):
            cav(
                "MoDerivAffMsa", "unclassified",
                from_feats=[_FakePossibility("a")], to_feats=[_FakePossibility("b")],
            )
        lost = _lost_messages(caplog)
        assert len(lost) == 1
        assert "FromProdRestrictRC" in lost[0] and "ToProdRestrictRC" in lost[0]
