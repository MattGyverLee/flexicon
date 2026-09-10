#
# conftest.py
#
# Directory-local pytest configuration for tests/.
#
# The FieldWorks initialization fixture and the shared fixtures/hooks that
# used to live here now live in tests/flex_plugin.py, registered globally by
# the repository-root conftest.py. Only genuinely directory-local settings
# belong here: collect_ignore is resolved relative to its own conftest, so
# it cannot move into a plugin module.
#
# Platform: Python.NET
#           FieldWorks Version 9+
#
# Copyright 2025
#

# Mock-only test files that stub sys.modules["SIL"] = MagicMock() at module
# scope. That stub poisons the real CLR namespace pythonnet would otherwise
# populate, so importing flexicon anywhere later in the same process fails
# with "'SIL' is not a package". These tests never exercise real library
# behavior (they just test mock orchestration), so skip collection and let
# the live-DB suite carry the actual coverage. Replace with live tests if
# the wrapper logic needs verification.
collect_ignore = [
    "test_affix_template_wrappers.py",
    "test_annotation_wrappers.py",
    "test_prohibition_wrappers.py",
]
