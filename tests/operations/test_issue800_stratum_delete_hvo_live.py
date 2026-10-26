#
#   test_issue800_stratum_delete_hvo_live.py
#
#   Live gate for issue #800 Delete HVO membership on StrataOS.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_800_"


@pytest.mark.requires_live_project
class TestIssue800StratumDeleteHvoLive:
    """Delete must remove the stratum when passed Object(hvo) after creation."""

    @pytest.mark.live_phase("StratumOperations", "delete")
    def test_delete_via_resolved_hvo(self, target_sandbox):
        stratum_ops = target_sandbox.Strata
        name = f"{TEST_PREFIX}stratum"

        stratum = None
        try:
            stratum = stratum_ops.Create(name)
            assert stratum is not None
            stratum_hvo = int(stratum.Hvo)

            before = len(list(stratum_ops.GetAll()))
            resolved = target_sandbox.Object(stratum_hvo)
            stratum_ops.Delete(resolved)

            assert len(list(stratum_ops.GetAll())) == before - 1
            for remaining in stratum_ops.GetAll():
                assert int(remaining.Hvo) != stratum_hvo
            stratum = None
        finally:
            if stratum is not None:
                try:
                    stratum_ops.Delete(stratum)
                except Exception:
                    pass
