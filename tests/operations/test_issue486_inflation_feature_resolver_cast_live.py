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
        sandbox = target_sandbox
        infl_ops = sandbox.InflectionFeatures
        ic = infl_ops.InflectionClassCreate(f"{TEST_PREFIX}ic")
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
            infl_ops.InflectionClassDelete(ic)
