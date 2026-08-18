"""
Unit tests for custom fields functionality.

Author: FlexTools Development Team
"""

import unittest

import pytest

from flexlibs2 import FLExProject, AllProjectNames, FP_FileLockedError, FLExInitialize


# Test constants
TEST_PROJECT = "__flexlibs_testing"
CUSTOM_FIELD = "EntryFlags"
CUSTOM_VALUE = "Test.Value"


# This module opens a REAL FLEx project via FLExProject.OpenProject(). It
# lives under flexicon/tests/, not the root tests/ tree, so the session-wide
# initialize_flex_for_tests fixture in tests/conftest.py never reaches it --
# pytest conftest.py fixtures only apply within their own directory subtree.
# Without this marker the test runs during the offline
# `pytest -m "not requires_live_project"` selector and fails opening the
# project (FLEx services were never initialized in this process).
pytestmark = pytest.mark.requires_live_project


class TestSuite(unittest.TestCase):
    """Test custom field operations.

    Unlike the tests under tests/, this class cannot rely on a shared
    session fixture to have initialized FLEx first (see the pytestmark
    comment above) -- it previously depended on flexicon/tests/test_FLExInit.py
    happening to run first alphabetically within the same session, which
    fails when this file is collected/run on its own. Initialize explicitly
    here instead. FLExInitialize() is safe to call more than once (it
    tolerates SLDR already being initialized -- see FLExInit.py).
    """

    def _openProject(self):
        """Open the test project with write access.

        ``__flexlibs_testing`` is an upstream fixture project that is not
        shipped with this repository and is not one of the two projects
        CLAUDE.md designates (Target, Sena 3). Where it is absent this is a
        missing environmental precondition, not a failure, so skip rather
        than fail -- a red test nobody can make green destroys the signal of
        the live suite.
        """
        FLExInitialize()
        if TEST_PROJECT not in AllProjectNames():
            self.skipTest(
                f"Project '{TEST_PROJECT}' is not present on this machine. "
                "This is an upstream fixture project, not one of the two "
                "projects this repository provisions (Target, Sena 3)."
            )
        fp = FLExProject()
        try:
            fp.OpenProject(TEST_PROJECT, writeEnabled=True)
        except FP_FileLockedError:
            self.fail("The test project is open in another application. Please close it and try again.")
        except Exception as e:
            self.fail(f"Exception opening project {TEST_PROJECT}:\n{e}")
        return fp

    def _closeProject(self, fp):
        """Close the project."""
        fp.CloseProject()

    def test_WriteFields(self):
        """Test writing and reading custom field values."""
        fp = self._openProject()
        flags_field = fp.LexiconGetEntryCustomFieldNamed(CUSTOM_FIELD)
        if not flags_field:
            self.fail(f"Entry-level custom field named '{CUSTOM_FIELD}' not found.")

        # Traverse the whole lexicon
        for lexEntry in fp.LexiconAllEntries():
            self.assertIsInstance(fp.LexiconGetHeadword(lexEntry), str)
            try:
                fp.LexiconSetFieldText(lexEntry, flags_field, CUSTOM_VALUE)
            except Exception as e:
                self.fail(f"Exception writing custom field {CUSTOM_FIELD}:\n{e}")

        # Read back and check that the values were written.
        for lexEntry in fp.LexiconAllEntries():
            value = fp.LexiconGetFieldText(lexEntry, flags_field)
            self.assertEqual(value, CUSTOM_VALUE)

        # Clear the field again
        for lexEntry in fp.LexiconAllEntries():
            fp.LexiconSetFieldText(lexEntry, flags_field, "")

        self._closeProject(fp)


if __name__ == "__main__":
    unittest.main()
