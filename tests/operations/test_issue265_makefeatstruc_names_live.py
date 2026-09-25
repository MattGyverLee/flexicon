#
#   test_issue265_makefeatstruc_names_live.py
#
#   Live coverage for issue #265: MakeFeatStruc accepts plain feature and
#   value NAME operands, not only HVO / GUID operands.
#
#   The #265 change shipped with offline coverage only, and the name
#   resolvers imported ITsString from SIL.LCModel -- where it does not
#   exist (it lives in SIL.LCModel.Core.KernelInterfaces) -- so every
#   name operand raised ImportError against a real LCM. This file pins the
#   name path end to end on a sandbox copy of Target.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

from flexicon.code.BaseOperations import FP_ParameterError

pytestmark = pytest.mark.requires_live_project


TEST_PREFIX = "TEST_265_"


def _first_sense(sandbox, entry):
    from SIL.LCModel import ILexSenseFactory

    senses = list(entry.SensesOS)
    if senses:
        return senses[0]
    factory = sandbox.project.ServiceLocator.GetService(ILexSenseFactory)
    new_sense = factory.Create()
    entry.SensesOS.Add(new_sense)
    return new_sense


class TestIssue265MakeFeatStrucNamesLive:

    @pytest.mark.live_phase("InflectionFeatureOperations", "add")
    def test_name_operands_resolve_and_attach(self, target_sandbox):
        from SIL.LCModel import IFsClosedValue, IMoStemMsa

        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures

        entry = sandbox.LexEntry.Create(lexeme_form=f"{TEST_PREFIX}names")
        try:
            sense = _first_sense(sandbox, entry)
            pos = sandbox.POS.Create(f"{TEST_PREFIX}pos", "t265")
            stem_hvo = sandbox.MSA.CreateStem(sense, pos).Hvo

            number_feat = infl_ops.Create(
                f"{TEST_PREFIX}number", "t265n", type="closed"
            )
            sg_val = infl_ops.CreateValue(number_feat, f"{TEST_PREFIX}sg", "sg")
            sg_hvo = sg_val.Hvo

            # Plain names, differently cased: resolution is analysis-WS
            # casefold, the same rules as Find.
            infl_ops.MakeFeatStruc(
                [(f"{TEST_PREFIX}NUMBER", f"{TEST_PREFIX}SG")],
                owner=sandbox.Object(stem_hvo),
            )

            # Read back from a fresh lookup, never the reference passed in.
            fresh = IMoStemMsa(sandbox.Object(stem_hvo))
            struct = fresh.MsFeaturesOA
            assert struct is not None, "MsFeaturesOA not attached"
            specs = list(struct.FeatureSpecsOC)
            assert len(specs) == 1, f"expected 1 spec, found {len(specs)}"
            assert specs[0].ClassName == "FsClosedValue"
            spec = IFsClosedValue(specs[0])
            assert (
                spec.FeatureRA.Name.BestAnalysisAlternative.Text
                == f"{TEST_PREFIX}number"
            )
            assert spec.ValueRA.Hvo == sg_hvo
        finally:
            sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("InflectionFeatureOperations", "add")
    def test_unknown_feature_name_raises_parameter_error(self, target_sandbox):
        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures

        entry = sandbox.LexEntry.Create(lexeme_form=f"{TEST_PREFIX}unknown")
        try:
            sense = _first_sense(sandbox, entry)
            pos = sandbox.POS.Create(f"{TEST_PREFIX}pos2", "t265b")
            stem = sandbox.MSA.CreateStem(sense, pos)
            with pytest.raises(FP_ParameterError):
                infl_ops.MakeFeatStruc(
                    [(f"{TEST_PREFIX}no_such_feature", f"{TEST_PREFIX}x")],
                    owner=sandbox.Object(stem.Hvo),
                )
        finally:
            sandbox.LexEntry.Delete(entry)
