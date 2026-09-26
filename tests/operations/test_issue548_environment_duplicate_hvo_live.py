#
#   test_issue548_environment_duplicate_hvo_live.py
#
#   Live verification for issue #548 Duplicate insert_after HVO index lookup.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_548_"


def _environment_hvos(project):
    phon_data = project.lp.PhonologicalDataOA
    return [int(env.Hvo) for env in phon_data.EnvironmentsOS]


class TestIssue548EnvironmentDuplicateHvoLive:
    """Duplicate(insert_after=True) must insert after source for raw Object(hvo)."""

    @pytest.mark.live_phase("EnvironmentOperations", "write")
    def test_duplicate_insert_after_raw_object_view(self, target_sandbox):
        project = target_sandbox
        env_ops = project.Environments

        env0 = env_ops.Create(f"{TEST_PREFIX}a", "#_")
        env1 = env_ops.Create(f"{TEST_PREFIX}b", "_#")
        env2 = env_ops.Create(f"{TEST_PREFIX}c", "#_#")

        raw_mid = project.Object(env1.Hvo)
        dup = env_ops.Duplicate(raw_mid, insert_after=True, deep=False)

        order = _environment_hvos(project)
        assert order.index(int(dup.Hvo)) == order.index(int(env1.Hvo)) + 1

        for env in list(env_ops.GetAll()):
            name = env_ops.GetName(env)
            if name.startswith(TEST_PREFIX):
                env_ops.Delete(env)
