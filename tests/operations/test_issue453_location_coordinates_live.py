#
#   test_issue453_location_coordinates_live.py
#
#   Live gate for issue #453: SetCoordinates must fail loud, not open a
#   write transaction that persists nothing.
#
#   Platform: Python.NET, FieldWorks 9+
#   Copyright 2026
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_453_"


@pytest.mark.requires_live_project
class TestIssue453LocationSetCoordinatesLive:
    @pytest.mark.live_phase("LocationOperations", "write")
    def test_set_coordinates_raises_on_target_sandbox(self, target_sandbox):
        sandbox = target_sandbox
        loc = sandbox.Location.Create(f"{TEST_PREFIX}geo_gate", "en")
        try:
            with pytest.raises(FP_ParameterError, match="issue #453"):
                sandbox.Location.SetCoordinates(loc, -1.23, -70.45)
            hvo = loc.Hvo
            assert sandbox.Location.GetCoordinates(hvo) is None
        finally:
            sandbox.Location.Delete(loc)
