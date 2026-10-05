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
    def test_side_to_write_raises_and_read_returns_empty(self, sena3_sandbox, caplog):
        p = sena3_sandbox
        msa = p.MSA.CreateInflAff(_sense(p, "infl_to"), _pos(p))
        feat = _feature(p, "infltofeat")
        # Put a "from" feature in place so an empty "to" read is meaningful.
        p.MSA.AddExceptionFeature(msa, feat)
        assert _hvos(_cast("IMoInflAffMsa", p.Object(msa.Hvo)).FromProdRestrictRC) == [feat.Hvo]

        with pytest.raises(FP_ParameterError):
            p.MSA.AddExceptionFeature(msa, feat, side="to")
        with pytest.raises(FP_ParameterError):
            p.MSA.RemoveExceptionFeature(msa, feat, side="to")
        with caplog.at_level("WARNING"):
            assert p.MSA.GetExceptionFeatures(msa, side="to") == []
        assert any("side='to'" in r.getMessage() for r in caplog.records)
        # Nothing was written or removed on the "from" side.
        assert _hvos(_cast("IMoInflAffMsa", p.Object(msa.Hvo)).FromProdRestrictRC) == [feat.Hvo]

    @pytest.mark.live_phase("MSAOperations", "update")
    def test_unclassified_get_returns_empty_add_raises(self, sena3_sandbox, caplog):
        p = sena3_sandbox
        msa = p.MSA.CreateUnclassifiedAffix(_sense(p, "uncl_get"), _pos(p))
        feat = _feature(p, "unclfeat")
        with caplog.at_level("WARNING"):
            assert p.MSA.GetExceptionFeatures(msa) == []
        assert any("MoUnclassifiedAffixMsa" in r.getMessage() for r in caplog.records)
        with pytest.raises(FP_ParameterError):
            p.MSA.AddExceptionFeature(msa, feat)


class TestProdRestrictListMissingLive:
    @pytest.mark.live_phase("InflectionFeatureOperations", "add")
    def test_create_when_prodrestrict_is_none(self, sena3_sandbox):
        p = sena3_sandbox
        md = p.lp.MorphologicalDataOA
        # Pre-state: remove the list so Create has to build it.
        with p.Transaction("TEST_630 clear ProdRestrictOA"):
            md.ProdRestrictOA = None
        assert p.lp.MorphologicalDataOA.ProdRestrictOA is None

        feat = p.InflectionFeatures.ExceptionFeatureCreate(f"{TEST_PREFIX}nolist")

        # Post-state: re-query the LCM.
        pr = p.lp.MorphologicalDataOA.ProdRestrictOA
        assert pr is not None, "ExceptionFeatureCreate did not create the list"
        stored = [x.Hvo for x in pr.PossibilitiesOS]
        assert stored == [feat.Hvo]
        assert (
            pr.PossibilitiesOS[0].Name.BestAnalysisAlternative.Text
            == f"{TEST_PREFIX}nolist"
        )


class TestChangeAffixVariantExceptionFeaturesLive:
    @pytest.mark.live_phase("MSAOperations", "update")
    def test_infl_to_deriv_keeps_from_features_without_lost_warning(
        self, sena3_sandbox, caplog
    ):
        p = sena3_sandbox
        msa = p.MSA.CreateInflAff(_sense(p, "cav_deriv"), _pos(p))
        feat = _feature(p, "cavfeat")
        p.MSA.AddExceptionFeature(msa, feat)

        with caplog.at_level("WARNING"):
            new = p.MSA.ChangeAffixVariant(msa, "deriv")

        raw = _cast("IMoDerivAffMsa", p.Object(new.Hvo))
        assert _hvos(raw.FromProdRestrictRC) == [feat.Hvo]
        assert _hvos(raw.ToProdRestrictRC) == []
        assert not any(
            "FromProdRestrictRC" in r.getMessage() for r in caplog.records
        ), "FromProdRestrictRC is copied, so it must not be reported lost"

    @pytest.mark.live_phase("MSAOperations", "update")
    def test_deriv_to_infl_copies_from_and_warns_only_about_to(
        self, sena3_sandbox, caplog
    ):
        p = sena3_sandbox
        pos = _pos(p)
        msa = p.MSA.CreateDerivAff(_sense(p, "cav_infl"), pos, pos)
        f_from = _feature(p, "cavfrom")
        f_to = _feature(p, "cavto")
        p.MSA.AddExceptionFeature(msa, f_from)
        p.MSA.AddExceptionFeature(msa, f_to, side="to")

        with caplog.at_level("WARNING"):
            new = p.MSA.ChangeAffixVariant(msa, "infl")

        raw = _cast("IMoInflAffMsa", p.Object(new.Hvo))
        assert _hvos(raw.FromProdRestrictRC) == [f_from.Hvo]
        lost = [r.getMessage() for r in caplog.records if "will be lost" in r.getMessage()]
        assert any("ToProdRestrictRC" in m for m in lost)
        assert not any("FromProdRestrictRC" in m for m in lost)

    @pytest.mark.live_phase("MSAOperations", "update")
    def test_infl_to_unclassified_warns_from_lost(self, sena3_sandbox, caplog):
        p = sena3_sandbox
        msa = p.MSA.CreateInflAff(_sense(p, "cav_uncl"), _pos(p))
        feat = _feature(p, "cavuncl")
        p.MSA.AddExceptionFeature(msa, feat)

        with caplog.at_level("WARNING"):
            new = p.MSA.ChangeAffixVariant(msa, "unclassified")

        assert p.Object(new.Hvo).ClassName == "MoUnclassifiedAffixMsa"
        assert any(
            "will be lost" in r.getMessage() and "FromProdRestrictRC" in r.getMessage()
            for r in caplog.records
        )


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
