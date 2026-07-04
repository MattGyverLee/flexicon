"""
Unit tests for custom fields functionality.

Author: FlexTools Development Team
"""

import unittest

from flexlibs2 import FLExProject, AllProjectNames, FP_FileLockedError


# Test constants
TEST_PROJECT = "__flexlibs_testing"
CUSTOM_FIELD = "EntryFlags"
CUSTOM_VALUE = "Test.Value"


class TestSuite(unittest.TestCase):
    """Test custom field operations.

    FLEx services (SLDR, ICU, registry, FLExInitialize) are owned by the
    session-wide fixture in tests/conftest.py::initialize_flex_for_tests.
    A per-class FLExCleanup() here would tear down SLDR for the remainder
    of the suite, causing later OpenProject calls to mark .ldml files as
    bad ("SLDR has not been initialized") and triggering the "Unable to
    create writing system" popup on the next run.
    """

    def _openProject(self):
        """Open the test project with write access."""
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
