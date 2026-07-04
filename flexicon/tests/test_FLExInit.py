"""
Unit tests for FLEx initialization and cleanup.

Author: FlexTools Development Team
"""

import unittest
from flexlibs2 import FLExInitialize, FLExCleanup


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
