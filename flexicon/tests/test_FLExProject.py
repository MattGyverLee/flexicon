"""
Unit tests for FLExProject class.

Author: FlexTools Development Team
"""

import unittest
import logging

import pytest

logging.basicConfig(filename="flexicon.log", filemode="w", level=logging.DEBUG)

from flexicon import FLExProject, AllProjectNames


class TestFLExProject(unittest.TestCase):
    """Test FLExProject functionality.

    FLEx services (SLDR, ICU, registry, FLExInitialize) are owned by the
    session-wide fixture in tests/flex_plugin.py::initialize_flex_for_tests.
    A per-class FLExCleanup() here would tear down SLDR for the remainder
    of the suite, causing later OpenProject calls to mark .ldml files as
    bad ("SLDR has not been initialized") and triggering the "Unable to
    create writing system" popup on the next run.
    """

    # AllProjectNames() reads the FieldWorks projects directory via
    # FwDirectoryFinder.ProjectsDirectory, which needs a real FieldWorks
    # install (see the offline-selector rationale above). issue #264.
    @pytest.mark.requires_live_project
    def test_AllProjectNames(self):
        """Test that AllProjectNames returns a list."""
        self.assertIsInstance(AllProjectNames(), list)

    # This test opens a REAL FLEx project (the first from AllProjectNames())
    # via fp.OpenProject(). Without this marker it runs during the offline
    # `pytest -m "not requires_live_project"` selector, which crashes
    # FLExInitialize()'s callers with a Windows access violation when no
    # FieldWorks/registry environment is present (see CLAUDE.md's Live LCM
    # Verification section -- every test that opens a real .fwdata project
    # must carry this marker). issue #264.
    @pytest.mark.requires_live_project
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

    # Opens a REAL FLEx project via fp.OpenProject() -- see test_OpenProject's
    # comment above. issue #264.
    @pytest.mark.requires_live_project
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
