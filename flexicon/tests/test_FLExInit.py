"""
Unit tests for FLEx initialization and cleanup.

Author: FlexTools Development Team
"""

import unittest

import pytest

from flexicon import FLExInitialize, FLExCleanup

# This module calls the real FLExInitialize()/FLExCleanup()/FLExInitialize()
# sequence below, tearing down and rebuilding the session-wide SLDR
# singleton owned by tests/conftest.py::initialize_flex_for_tests. Without
# this marker it runs during the offline `pytest -m "not requires_live_project"`
# selector and disturbs that singleton mid-run (see CLAUDE.md's Live LCM
# Verification section -- every test that touches FLEx init/cleanup directly
# must carry this marker). issue #264.
pytestmark = pytest.mark.requires_live_project


class TestFLExInit(unittest.TestCase):
    """Test FLEx initialization and cleanup functions."""

    def test_InitializeCleanup(self):
        """Test that FLEx can be initialized and cleaned up without errors.

        FLEx services (SLDR, ICU, registry) are owned by the session-wide
        fixture in tests/conftest.py::initialize_flex_for_tests. This test
        verifies the public API still works, but MUST re-initialize after
        Cleanup -- otherwise the suite's SLDR singleton stays torn down
        and every later live-DB test marks .ldml files as bad
        ("SLDR has not been initialized"), triggering the "Unable to
        create writing system" popup on the next run.
        """
        try:
            FLExInitialize()
        except Exception as e:
            self.fail(f"Failed to initialize: {e}")
        try:
            FLExCleanup()
        except Exception as e:
            self.fail(f"Failed to cleanup: {e}")
        # Restore session-wide SLDR state so subsequent tests keep working.
        FLExInitialize()


if __name__ == "__main__":
    unittest.main()
