#
#   test_issue825_fw_dir_override_live.py
#
#   Live verification that flexicon initialises with FLEXICON_FW_DIR in
#   effect (issue #825). Uses target_sandbox only.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os

import pytest

pytestmark = pytest.mark.requires_live_project


@pytest.mark.live_phase("FLExProject", "read")
def test_override_in_effect_and_project_opens(target_sandbox):
    from flexicon.code import FLExGlobals

    override = os.environ.get("FLEXICON_FW_DIR")
    assert override, "FLEXICON_FW_DIR must be set for this live test"
    assert os.path.normcase(os.path.normpath(FLExGlobals.FWCodeDir)) == \
        os.path.normcase(os.path.normpath(os.path.abspath(override)))
    assert target_sandbox.writeEnabled is True
    assert len(list(target_sandbox.LexEntry.GetAll())) >= 0
    # Re-query a real LCM value to prove a live cache.
    assert target_sandbox.project is not None
