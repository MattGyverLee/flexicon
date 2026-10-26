#
#   test_issue794_environment_delete_hvo_live.py
#
#   Live gate for issue #794 Delete HVO membership on EnvironmentsOS.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_794_"


@pytest.mark.requires_live_project
class TestIssue794EnvironmentDeleteHvoLive:
    """Delete must remove the environment when passed Object(hvo) after creation."""

    @pytest.mark.live_phase("EnvironmentOperations", "delete")
    def test_delete_via_resolved_hvo(self, target_sandbox):
        env_ops = target_sandbox.Environments
        name = f"{TEST_PREFIX}env"

        env = None
        try:
            env = env_ops.Create(name)
            assert env is not None
            env_hvo = int(env.Hvo)

            resolved = target_sandbox.Object(env_hvo)
            env_ops.Delete(resolved)

            for remaining in env_ops.GetAll():
                assert int(remaining.Hvo) != env_hvo
            env = None
        finally:
            if env is not None:
                try:
                    env_ops.Delete(env)
                except Exception:
                    pass
