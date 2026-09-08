#
#   test_flexlibs2_alias_surface.py
#
#   Class: TestFlexlibs2AliasSurface
#          Behavioral tests for the `flexlibs2` compatibility alias itself
#          (issue #240). These are the "alias's own tests" the ratchet in
#          tests/test_flexlibs2_alias_ratchet.py exempts: they MUST walk
#          `flexlibs2` executably, because walking it is the thing under
#          test.
#
#   SCOPE FENCE -- read before adding anything here:
#       This file is listed in `_ALLOWED_PATHS` in
#       tests/test_flexlibs2_alias_ratchet.py, so the alias ratchet does
#       NOT see its imports. Only tests whose subject IS the alias belong
#       here. A test that merely needs FLExProject, lcm_casting or any
#       other library symbol must live in its own domain's test file and
#       import from `flexicon` -- putting it here to dodge the ratchet
#       would blind the very guard this file is exempted from.
#
#       Nothing here needs FieldWorks, pythonnet or a live project.
#
#   Platform: Python 3.8+
#   Copyright 2026
#

"""Tests for the deprecated `flexlibs2` import alias (issue #240)."""

import flexicon


class TestFlexlibs2AliasSurface:
    def test_capabilities_reachable_through_the_flexlibs2_alias(self):
        """`sys.modules["flexlibs2"]` is the flexicon module object itself, so
        the alias must expose the same set -- FlexTools scripts on disk still
        import under the old name.

        Moved here from tests/write_path_transactions/test_capabilities.py
        (task B4): the import is deliberate, and this file is the ratchet's
        sanctioned home for deliberate alias imports.
        """
        import warnings

        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            import flexlibs2

        assert flexlibs2.CAPABILITIES is flexicon.CAPABILITIES
