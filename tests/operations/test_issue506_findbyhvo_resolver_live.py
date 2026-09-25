#
#   test_issue506_findbyhvo_resolver_live.py
#
#   Live gate for issue #506 FindByHvo HVO resolution.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_506_"


@pytest.mark.requires_live_project
class TestIssue506FindByHvoHvoGate:
    """FindByHvo must resolve genuine HVO ints via __ResolveObject."""

    @pytest.mark.live_phase("ConstChartOperations", "read")
    def test_const_chart_findbyhvo_returns_chart_for_hvo(self, target_sandbox):
        chart = target_sandbox.ConstCharts.Create(f"{TEST_PREFIX}Chart")
        found = target_sandbox.ConstCharts.FindByHvo(chart.Hvo)
        assert found is not None
        assert target_sandbox.ConstCharts.GetName(found) == f"{TEST_PREFIX}Chart"
        assert target_sandbox.ConstCharts.GetName(chart.Hvo) == f"{TEST_PREFIX}Chart"

    @pytest.mark.live_phase("ReversalIndexEntryOperations", "add")
    def test_reversal_entry_findbyhvo_returns_entry_for_hvo(self, target_sandbox):
        en_ws = target_sandbox.WSHandle("en")
        index = target_sandbox.ReversalIndexes.Create(f"{TEST_PREFIX}Idx", en_ws)
        entry = target_sandbox.ReversalEntries.Create(
            index.Hvo, f"{TEST_PREFIX}form", wsHandle=en_ws
        )
        found = target_sandbox.ReversalEntries.FindByHvo(entry.Hvo)
        assert found is not None
        assert (
            target_sandbox.ReversalEntries.GetForm(found, wsHandle=en_ws)
            == f"{TEST_PREFIX}form"
        )

    @pytest.mark.live_phase("ReversalIndexEntryOperations", "read")
    def test_findbyhvo_returns_none_for_wrong_type_hvo(self, target_sandbox):
        en_ws = target_sandbox.WSHandle("en")
        index = target_sandbox.ReversalIndexes.Create(f"{TEST_PREFIX}Idx2", en_ws)
        assert target_sandbox.ReversalEntries.FindByHvo(index.Hvo) is None
