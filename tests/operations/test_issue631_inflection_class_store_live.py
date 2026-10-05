#
#   test_issue631_inflection_class_store_live.py
#
#   Live verification (Sena 3 sandbox) for issue 631: inflection classes
#   are owned by POS / parent classes; ProdRestrictOA holds exception
#   features. Modeled on test_target_live_smoke.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def _name(ops, ic):
    return ops.InflectionClassGetName(ic)


def _nome_pos(project):
    pos = project.POS.Find("Nome")
    assert pos is not None, "Sena 3 sandbox has no 'Nome' POS"
    return pos


class TestExceptionFeaturesLive:
    @pytest.mark.live_phase("InflectionFeatureOperations", "add")
    def test_exception_feature_create_getall_find(self, sena3_sandbox):
        ops = sena3_sandbox.InflectionFeatures
        before = [ops_name for ops_name in
                  (ef.Name.BestAnalysisAlternative.Text for ef in ops.ExceptionFeatureGetAll())]

        ef1 = ops.ExceptionFeatureCreate(f"{TEST_PREFIX}exc1", "te1")
        ops.ExceptionFeatureCreate(f"{TEST_PREFIX}exc2")

        # Read back from the LCM list itself, not from the returned objects.
        pr = sena3_sandbox.lp.MorphologicalDataOA.ProdRestrictOA
        stored = [p.Name.BestAnalysisAlternative.Text for p in pr.PossibilitiesOS]
        assert f"{TEST_PREFIX}exc1" in stored and f"{TEST_PREFIX}exc2" in stored

        after = [ef.Name.BestAnalysisAlternative.Text for ef in ops.ExceptionFeatureGetAll()]
        assert len(after) == len(before) + 2

        found = ops.ExceptionFeatureFind(f"{TEST_PREFIX}EXC1")
        assert found is not None and found.Hvo == ef1.Hvo
        assert found.Abbreviation.BestAnalysisAlternative.Text == "te1"
        assert ops.ExceptionFeatureFind(f"{TEST_PREFIX}nope") is None

        with pytest.raises(FP_ParameterError):
            ops.ExceptionFeatureCreate(f"{TEST_PREFIX}exc1")


class TestInflectionClassStoreLive:
    @pytest.mark.live_phase("InflectionFeatureOperations", "read")
    def test_getall_survives_exception_features_and_has_nome_classes(self, sena3_sandbox):
        ops = sena3_sandbox.InflectionFeatures
        nome = _nome_pos(sena3_sandbox)
        # The shipped Sena 3 backup carries no inflection classes on Nome
        # (verified live), so seed some; any pre-existing ones must also show.
        for i in (1, 2):
            ops.InflectionClassCreate(f"{TEST_PREFIX}cls{i}", pos=nome)
        for i in (1, 2, 3):
            ops.ExceptionFeatureCreate(f"{TEST_PREFIX}ef{i}")
        assert len(list(ops.ExceptionFeatureGetAll())) >= 3

        nome_names = {_name(ops, c) for c in nome.InflectionClassesOC}
        assert {f"{TEST_PREFIX}cls1", f"{TEST_PREFIX}cls2"} <= nome_names

        all_names = {_name(ops, c) for c in ops.InflectionClassGetAll()}  # must not raise
        assert nome_names <= all_names

    @pytest.mark.live_phase("InflectionFeatureOperations", "add")
    def test_name_only_create_raises(self, sena3_sandbox):
        with pytest.raises(FP_ParameterError):
            sena3_sandbox.InflectionFeatures.InflectionClassCreate(f"{TEST_PREFIX}x")

    @pytest.mark.live_phase("InflectionFeatureOperations", "add")
    def test_create_under_pos_and_parent_then_delete(self, sena3_sandbox):
        ops = sena3_sandbox.InflectionFeatures
        ops.ExceptionFeatureCreate(f"{TEST_PREFIX}ef")  # ProdRestrictOA must not matter
        nome = _nome_pos(sena3_sandbox)
        pr = sena3_sandbox.lp.MorphologicalDataOA.ProdRestrictOA
        pr_count = pr.PossibilitiesOS.Count

        n_before = nome.InflectionClassesOC.Count
        total_before = len(list(ops.InflectionClassGetAll()))

        top = ops.InflectionClassCreate(f"{TEST_PREFIX}top", pos=nome)
        # Read back via the owner's collection.
        assert nome.InflectionClassesOC.Count == n_before + 1
        assert f"{TEST_PREFIX}top" in {_name(ops, c) for c in nome.InflectionClassesOC}
        assert top.Owner.Hvo == nome.Hvo

        kid = ops.InflectionClassCreate(f"{TEST_PREFIX}kid", parent=top)
        assert top.SubclassesOC.Count == 1
        assert [_name(ops, c) for c in top.SubclassesOC] == [f"{TEST_PREFIX}kid"]
        assert kid.Owner.Hvo == top.Hvo

        # Never written into ProdRestrictOA.
        assert pr.PossibilitiesOS.Count == pr_count

        all_names = [_name(ops, c) for c in ops.InflectionClassGetAll()]
        assert f"{TEST_PREFIX}top" in all_names and f"{TEST_PREFIX}kid" in all_names
        assert len(all_names) == total_before + 2

        with pytest.raises(FP_ParameterError):
            ops.InflectionClassCreate(f"{TEST_PREFIX}TOP", pos=nome)

        ops.InflectionClassDelete(kid)
        assert top.SubclassesOC.Count == 0

        ops.InflectionClassDelete(top)
        assert nome.InflectionClassesOC.Count == n_before
        assert f"{TEST_PREFIX}top" not in {_name(ops, c) for c in nome.InflectionClassesOC}
        assert len(list(ops.InflectionClassGetAll())) == total_before
