#
#   test_issue486_inflation_feature_resolver_cast_live.py
#
#   Live gate for issue #486 InflectionFeatureOperations HVO resolver casts.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_486_"


@pytest.mark.requires_live_project
class TestIssue486InflectionClassNameHvoGate:
    """
    InflectionClassGetName resolves the class via __ResolveInflectionClass and
    reads Name -- subtype-only on IMoInflClass.
    """

    @pytest.mark.live_phase("InflectionFeatureOperations", "read")
    def test_inflection_class_get_name_via_genuine_ic_hvo(self, target_sandbox):
        from SIL.LCModel import IMoInflClassFactory
        from SIL.LCModel.Core.Text import TsStringUtils

        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures
        # InflectionClassCreate() cannot set this up: it adds the class to
        # ProdRestrictOA.PossibilitiesOS (an ICmPossibility list), which
        # pythonnet rejects -- inflection classes are owned by
        # IPartOfSpeech.InflectionClassesOC. Pre-existing bug, tracked
        # separately; build the class on a POS the LCM way instead.
        pos = sandbox.POS.Create(f"{TEST_PREFIX}pos", "t486")
        ic = sandbox.project.ServiceLocator.GetService(IMoInflClassFactory).Create()
        pos.InflectionClassesOC.Add(ic)
        ws = sandbox.project.DefaultAnalWs
        ic.Name.set_String(ws, TsStringUtils.MakeString(f"{TEST_PREFIX}ic", ws))
        hvo = ic.Hvo
        assert isinstance(hvo, int), (
            "test setup error: hvo must be a genuine Python int"
        )
        assert not hasattr(sandbox.Object(hvo), "Name"), (
            "precondition failed: Name reachable on bare ICmObject view "
            "-- re-derive the gate site"
        )

        try:
            name = infl_ops.InflectionClassGetName(hvo)
            assert isinstance(name, str)
            assert TEST_PREFIX in name
        finally:
            sandbox.POS.Delete(pos)  # owns the class; sandbox is discarded anyway
