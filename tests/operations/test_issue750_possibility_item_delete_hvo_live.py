#
#   test_issue750_possibility_item_delete_hvo_live.py
#
#   Live gate for issue #750 PossibilityItemOperations Delete HVO membership.
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_750_"


@pytest.mark.requires_live_project
class TestIssue750PossibilityItemDeleteHvoLive:
    """Delete must not rely on Python proxy identity in PossibilitiesOS."""

    def test_delete_confidence_via_resolved_hvo(self, target_project):
        project = target_project
        name = TEST_PREFIX + "confidence"
        item = project.Confidence.Create(name)
        hvo = int(item.Hvo)
        resolved = project.Object(hvo)
        project.Confidence.Delete(resolved)
        assert project.Confidence.Find(name) is None
