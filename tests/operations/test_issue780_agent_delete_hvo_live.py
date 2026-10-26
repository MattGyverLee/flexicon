#
#   test_issue780_agent_delete_hvo_live.py
#
#   Live verification for issue #780 AgentOperations Delete HVO membership lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project


def test_issue780_delete_removes_from_analyzingagentsoc_by_hvo(target_sandbox):
    """Delete removes an agent after re-fetching by HVO."""
    project = target_sandbox
    agents = project.Agents
    test_name = "TEST_780_agent_delete_hvo"

    existing = agents.Find(test_name)
    if existing is not None:
        agents.Delete(existing)

    agent = agents.Create(test_name)
    try:
        hvo = agent.Hvo
        bare_view = project.Object(hvo)
        agents.Delete(bare_view)
        assert agents.Find(test_name) is None
        assert all(a.Hvo != hvo for a in agents.GetAll())
    finally:
        leftover = agents.Find(test_name)
        if leftover is not None:
            agents.Delete(leftover)
