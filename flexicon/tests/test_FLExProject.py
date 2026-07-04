"""
Unit tests for FLExProject class.

Author: FlexTools Development Team
"""

import unittest
import logging

logging.basicConfig(filename="flexlibs2.log", filemode="w", level=logging.DEBUG)

from flexlibs2 import FLExProject, AllProjectNames


class TestFLExProject(unittest.TestCase):
    """Test FLExProject functionality.

    FLEx services (SLDR, ICU, registry, FLExInitialize) are owned by the
    session-wide fixture in tests/conftest.py::initialize_flex_for_tests.
    A per-class FLExCleanup() here would tear down SLDR for the remainder
    of the suite, causing later OpenProject calls to mark .ldml files as
    bad ("SLDR has not been initialized") and triggering the "Unable to
    create writing system" popup on the next run.
    """

    def test_AllProjectNames(self):
        """Test that AllProjectNames returns a list."""
        self.assertIsInstance(AllProjectNames(), list)

    def test_OpenProject(self):
        """Test opening and closing a project."""
        fp = FLExProject()
        # Grab the first project in the list
        projectName = AllProjectNames()[0]
        try:
            fp.OpenProject(projectName, writeEnabled=False)
        except Exception as e:
            self.fail(f"Exception opening project {projectName}:\n{e}")
        fp.CloseProject()

    def test_ReadLexicon(self):
        """Test reading lexicon entries from a project."""
        fp = FLExProject()
        projectName = AllProjectNames()[0]
        try:
            fp.OpenProject(projectName, writeEnabled=False)
        except Exception as e:
            self.fail(f"Exception opening project {projectName}: {e}")

        # Traverse the whole lexicon
        for lexEntry in fp.LexiconAllEntries():
            self.assertIsInstance(fp.LexiconGetHeadword(lexEntry), str)

        fp.CloseProject()


if __name__ == "__main__":
    unittest.main()
