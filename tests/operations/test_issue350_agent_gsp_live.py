#
#   test_issue350_agent_gsp_live.py
#
#   Live read-only coverage for issue #350: GetSyncableProperties on every agent.
#
#   Copyright 2026
#

import pytest


@pytest.mark.requires_live_project
def test_get_syncable_properties_on_all_agents(sena3_sandbox):
    project = sena3_sandbox
    agents = project.Agents.GetAll()
    assert agents, "expected at least one agent in Sena 3 sandbox"

    for agent in agents:
        props = project.Agents.GetSyncableProperties(agent)
        assert isinstance(props, dict)
        assert "Guid" in props
        assert "Human" in props
        assert "Description" not in props
