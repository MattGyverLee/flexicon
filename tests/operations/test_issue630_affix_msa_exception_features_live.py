#
#   test_issue630_affix_msa_exception_features_live.py
#
#   Live verification (Sena 3 sandbox) for issue 630: MSA exception
#   features on affix MSAs. IMoInflAffMsa -> FromProdRestrictRC;
#   IMoDerivAffMsa -> FromProdRestrictRC / ToProdRestrictRC;
#   IMoStemMsa -> ProdRestrictRC. Every assertion re-reads the LCM field
#   directly (never the wrapper's own getter alone). Modeled on
#   test_target_live_smoke.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_630_"


def _cast(name, obj):
    """Cast to a concrete LCM interface (SIL imports only work after init)."""
    import SIL.LCModel as lcm

    return getattr(lcm, name)(obj)


def _pos(project):
    pos = project.POS.Find("Nome")
    assert pos is not None, "Sena 3 sandbox has no 'Nome' POS"
    return pos


def _sense(project, label):
    entry = project.LexEntry.Create(
        f"{TEST_PREFIX}{label}", create_blank_sense=False
    )
    return project.Senses.Create(entry, f"{TEST_PREFIX}{label}_gloss")


def _hvos(rc):
    return sorted(item.Hvo for item in rc)


def _feature(project, name):
    return project.InflectionFeatures.ExceptionFeatureCreate(
        f"{TEST_PREFIX}{name}"
    )


class TestInflAffixExceptionFeaturesLive:
    @pytest.mark.live_phase("MSAOperations", "update")
    def test_add_idempotent_remove_on_from_field(self, sena3_sandbox):
        p = sena3_sandbox
        msa = p.MSA.CreateInflAff(_sense(p, "infl"), _pos(p))
        raw = _cast("IMoInflAffMsa", msa)
        feat = _feature(p, "inflfeat")

        pre = _hvos(raw.FromProdRestrictRC)
        assert pre == []

        p.MSA.AddExceptionFeature(msa, feat)
        post_add = _hvos(_cast("IMoInflAffMsa", p.Object(msa.Hvo)).FromProdRestrictRC)
        assert post_add == [feat.Hvo]

        # Second add changes nothing.
        p.MSA.AddExceptionFeature(msa, feat)
        post_add2 = _hvos(_cast("IMoInflAffMsa", p.Object(msa.Hvo)).FromProdRestrictRC)
        assert post_add2 == [feat.Hvo]
        assert [f.Hvo for f in p.MSA.GetExceptionFeatures(msa)] == [feat.Hvo]

        p.MSA.RemoveExceptionFeature(msa, feat)
        post_rm = _hvos(_cast("IMoInflAffMsa", p.Object(msa.Hvo)).FromProdRestrictRC)
        assert post_rm == []
        assert p.MSA.GetExceptionFeatures(msa) == []

    @pytest.mark.live_phase("MSAOperations", "update")
    def test_side_to_raises_and_writes_nothing(self, sena3_sandbox):
        p = sena3_sandbox
        msa = p.MSA.CreateInflAff(_sense(p, "infl_to"), _pos(p))
        feat = _feature(p, "infltofeat")

        with pytest.raises(FP_ParameterError):
            p.MSA.AddExceptionFeature(msa, feat, side="to")
        with pytest.raises(FP_ParameterError):
            p.MSA.GetExceptionFeatures(msa, side="to")
        with pytest.raises(FP_ParameterError):
            p.MSA.RemoveExceptionFeature(msa, feat, side="to")
        assert _hvos(_cast("IMoInflAffMsa", p.Object(msa.Hvo)).FromProdRestrictRC) == []


class TestDerivAffixExceptionFeaturesLive:
    @pytest.mark.live_phase("MSAOperations", "update")
    def test_from_and_to_are_independent(self, sena3_sandbox):
        p = sena3_sandbox
        pos = _pos(p)
        msa = p.MSA.CreateDerivAff(_sense(p, "deriv"), pos, pos)
        f_from = _feature(p, "derivfrom")
        f_to = _feature(p, "derivto")

        def read():
            raw = _cast("IMoDerivAffMsa", p.Object(msa.Hvo))
            return _hvos(raw.FromProdRestrictRC), _hvos(raw.ToProdRestrictRC)

        assert read() == ([], [])

        p.MSA.AddExceptionFeature(msa, f_from)  # default side == "from"
        assert read() == ([f_from.Hvo], [])

        p.MSA.AddExceptionFeature(msa, f_to, side="to")
        assert read() == ([f_from.Hvo], [f_to.Hvo])

        # Idempotent on both sides.
        p.MSA.AddExceptionFeature(msa, f_from, side="from")
        p.MSA.AddExceptionFeature(msa, f_to, side="to")
        assert read() == ([f_from.Hvo], [f_to.Hvo])

        assert [f.Hvo for f in p.MSA.GetExceptionFeatures(msa, side="from")] == [f_from.Hvo]
        assert [f.Hvo for f in p.MSA.GetExceptionFeatures(msa, side="to")] == [f_to.Hvo]

        p.MSA.RemoveExceptionFeature(msa, f_to, side="to")
        assert read() == ([f_from.Hvo], [])

        p.MSA.RemoveExceptionFeature(msa, f_from)
        assert read() == ([], [])

    @pytest.mark.live_phase("MSAOperations", "update")
    def test_invalid_side_raises(self, sena3_sandbox):
        p = sena3_sandbox
        pos = _pos(p)
        msa = p.MSA.CreateDerivAff(_sense(p, "deriv_bad"), pos, pos)
        feat = _feature(p, "derivbad")
        with pytest.raises(FP_ParameterError):
            p.MSA.AddExceptionFeature(msa, feat, side="both")


class TestStemExceptionFeaturesRegressionLive:
    @pytest.mark.live_phase("MSAOperations", "update")
    def test_stem_msa_still_works_and_ignores_side(self, sena3_sandbox):
        p = sena3_sandbox
        msa = p.MSA.CreateStem(_sense(p, "stem"), _pos(p))
        feat = _feature(p, "stemfeat")

        def read():
            return _hvos(_cast("IMoStemMsa", p.Object(msa.Hvo)).ProdRestrictRC)

        assert read() == []
        p.MSA.AddExceptionFeature(msa, feat)
        assert read() == [feat.Hvo]
        p.MSA.AddExceptionFeature(msa, feat, side="to")  # ignored, no-op
        assert read() == [feat.Hvo]
        assert [f.Hvo for f in p.MSA.GetExceptionFeatures(msa, side="to")] == [feat.Hvo]
        p.MSA.RemoveExceptionFeature(msa, feat)
        assert read() == []
