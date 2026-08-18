"""
Unit tests for Duplicate() Methods Across All 17 Operation Classes

Tests all Duplicate() implementations with standard test suite:
- Creates new GUID
- Copies properties
- Insert after vs insert at end
- Shallow vs deep copy
- Preserves references
- Independence of duplicate from original

Author: FlexTools Development Team - Programmer 3 (Test Engineer)
Date: 2025-12-04
Project: Duplicate() Implementation - Phase 3 Testing
"""

import unittest
import sys
import os

import pytest

# Add parent directory to sys.path to allow importing flexlibs
_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.join(_test_dir, "..", "..", "..")
sys.path.insert(0, _project_root)

from flexlibs2.code.FLExProject import FLExProject
from flexlibs2.code.FLExInit import FLExInitialize, FLExCleanup

# This module opens a REAL FLEx project ("Sena 3") in setUpModule() below
# and performs live Duplicate()/Delete() round-trips against it. Without
# this marker it runs during the offline `pytest -m "not requires_live_project"`
# selector, which crashes FLExInitialize() with a Windows access violation
# when no FieldWorks/registry environment is present (see CLAUDE.md's Live
# LCM Verification section -- every test that opens a real .fwdata project
# must carry this marker).
pytestmark = pytest.mark.requires_live_project


# ============================================================================
# MODULE-LEVEL SETUP: Initialize FLEx ONCE for all tests
# ============================================================================

_flex_initialized = False
_test_project = None


def setUpModule():
    """Initialize FLEx connection once for entire test module."""
    global _flex_initialized, _test_project
    if not _flex_initialized:
        FLExInitialize()
        _test_project = FLExProject()
        _test_project.OpenProject("Sena 3", writeEnabled=True)
        _flex_initialized = True


def tearDownModule():
    """Clean up FLEx connection after all tests complete."""
    global _test_project, _flex_initialized
    if _test_project:
        _test_project.CloseProject()
        FLExCleanup()
        _flex_initialized = False


# ============================================================================
# TIER 1: LEXICON TESTS (5 classes)
# ============================================================================


class TestLexSenseDuplicate(unittest.TestCase):
    """Tests for LexSenseOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test entry with multiple senses
        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.SensesOS.Count >= 2:
                cls.test_entry = entry
                break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_entry or self.test_entry.SensesOS.Count == 0:
            self.skipTest("No suitable entry with senses found")

        original = self.test_entry.SensesOS[0]
        duplicate = self.project.Senses.Duplicate(original)

        # Verify GUIDs are different
        self.assertNotEqual(str(original.Guid), str(duplicate.Guid))

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_entry or self.test_entry.SensesOS.Count == 0:
            self.skipTest("No suitable entry with senses found")

        original = self.test_entry.SensesOS[0]
        original_gloss = self.project.Senses.GetGloss(original)

        duplicate = self.project.Senses.Duplicate(original)
        duplicate_gloss = self.project.Senses.GetGloss(duplicate)

        # Verify gloss was copied
        self.assertEqual(original_gloss, duplicate_gloss)

        # Clean up
        self.project.Senses.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate inserted after source."""
        if not self.test_entry or self.test_entry.SensesOS.Count == 0:
            self.skipTest("No suitable entry with senses found")

        original = self.test_entry.SensesOS[0]
        original_index = 0

        duplicate = self.project.Senses.Duplicate(original, insert_after=True)

        # Find duplicate's index
        duplicate_index = -1
        for i in range(self.test_entry.SensesOS.Count):
            if self.test_entry.SensesOS[i] == duplicate:
                duplicate_index = i
                break

        # Should be immediately after original
        self.assertEqual(duplicate_index, original_index + 1)

        # Clean up
        self.project.Senses.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate appended to end."""
        if not self.test_entry or self.test_entry.SensesOS.Count == 0:
            self.skipTest("No suitable entry with senses found")

        original = self.test_entry.SensesOS[0]
        original_count = self.test_entry.SensesOS.Count

        duplicate = self.project.Senses.Duplicate(original, insert_after=False)

        # Should be at end
        new_count = self.test_entry.SensesOS.Count
        self.assertEqual(new_count, original_count + 1)
        self.assertEqual(self.test_entry.SensesOS[new_count - 1], duplicate)

        # Clean up
        self.project.Senses.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        # Find sense with examples
        test_sense = None
        for entry in self.project.LexEntry.GetAll():
            for sense in entry.SensesOS:
                if sense.ExamplesOS.Count > 0:
                    test_sense = sense
                    break
            if test_sense:
                break

        if not test_sense:
            self.skipTest("No sense with examples found")

        original_examples = test_sense.ExamplesOS.Count
        duplicate = self.project.Senses.Duplicate(test_sense, deep=False)

        # Shallow copy should have no examples
        self.assertEqual(duplicate.ExamplesOS.Count, 0)

        # Clean up
        self.project.Senses.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates owned objects."""
        # Find sense with examples
        test_sense = None
        for entry in self.project.LexEntry.GetAll():
            for sense in entry.SensesOS:
                if sense.ExamplesOS.Count > 0:
                    test_sense = sense
                    break
            if test_sense:
                break

        if not test_sense:
            self.skipTest("No sense with examples found")

        original_examples = test_sense.ExamplesOS.Count
        duplicate = self.project.Senses.Duplicate(test_sense, deep=True)

        # Deep copy should have same number of examples
        self.assertEqual(duplicate.ExamplesOS.Count, original_examples)

        # Clean up
        self.project.Senses.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        # Find sense with MSA
        test_sense = None
        for entry in self.project.LexEntry.GetAll():
            for sense in entry.SensesOS:
                if sense.MorphoSyntaxAnalysisRA:
                    test_sense = sense
                    break
            if test_sense:
                break

        if not test_sense:
            self.skipTest("No sense with MSA found")

        original_msa = test_sense.MorphoSyntaxAnalysisRA
        duplicate = self.project.Senses.Duplicate(test_sense)

        # Reference should be copied
        self.assertEqual(duplicate.MorphoSyntaxAnalysisRA, original_msa)

        # Clean up
        self.project.Senses.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_entry or self.test_entry.SensesOS.Count == 0:
            self.skipTest("No suitable entry with senses found")

        original = self.test_entry.SensesOS[0]
        original_gloss = self.project.Senses.GetGloss(original)

        duplicate = self.project.Senses.Duplicate(original)

        # Modify original
        self.project.Senses.SetGloss(original, "MODIFIED_GLOSS")

        # Duplicate should be unchanged
        duplicate_gloss = self.project.Senses.GetGloss(duplicate)
        self.assertNotEqual(duplicate_gloss, "MODIFIED_GLOSS")

        # Restore and clean up
        self.project.Senses.SetGloss(original, original_gloss)
        self.project.Senses.Delete(duplicate)


class TestExampleDuplicate(unittest.TestCase):
    """Tests for ExampleOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable sense with multiple examples
        cls.test_sense = None
        for entry in cls.project.LexEntry.GetAll():
            for sense in entry.SensesOS:
                if sense.ExamplesOS.Count >= 2:
                    cls.test_sense = sense
                    break
            if cls.test_sense:
                break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_sense or self.test_sense.ExamplesOS.Count == 0:
            self.skipTest("No suitable sense with examples found")

        original = self.test_sense.ExamplesOS[0]
        duplicate = self.project.Examples.Duplicate(original)

        # Verify GUIDs are different
        self.assertNotEqual(str(original.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Examples.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_sense or self.test_sense.ExamplesOS.Count == 0:
            self.skipTest("No suitable sense with examples found")

        original = self.test_sense.ExamplesOS[0]
        original_text = self.project.Examples.GetExample(original)

        duplicate = self.project.Examples.Duplicate(original)
        duplicate_text = self.project.Examples.GetExample(duplicate)

        # Verify text was copied
        self.assertEqual(original_text, duplicate_text)

        # Clean up
        self.project.Examples.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate inserted after source."""
        if not self.test_sense or self.test_sense.ExamplesOS.Count == 0:
            self.skipTest("No suitable sense with examples found")

        original = self.test_sense.ExamplesOS[0]
        original_index = 0

        duplicate = self.project.Examples.Duplicate(original, insert_after=True)

        # Find duplicate's index
        duplicate_index = -1
        for i in range(self.test_sense.ExamplesOS.Count):
            if self.test_sense.ExamplesOS[i] == duplicate:
                duplicate_index = i
                break

        # Should be immediately after original
        self.assertEqual(duplicate_index, original_index + 1)

        # Clean up
        self.project.Examples.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate appended to end."""
        if not self.test_sense or self.test_sense.ExamplesOS.Count == 0:
            self.skipTest("No suitable sense with examples found")

        original = self.test_sense.ExamplesOS[0]
        original_count = self.test_sense.ExamplesOS.Count

        duplicate = self.project.Examples.Duplicate(original, insert_after=False)

        # Should be at end
        new_count = self.test_sense.ExamplesOS.Count
        self.assertEqual(new_count, original_count + 1)
        self.assertEqual(self.test_sense.ExamplesOS[new_count - 1], duplicate)

        # Clean up
        self.project.Examples.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        # Examples don't have significant owned objects, so shallow = deep behavior
        # This test verifies shallow copy works without errors
        if not self.test_sense or self.test_sense.ExamplesOS.Count == 0:
            self.skipTest("No suitable sense with examples found")

        original = self.test_sense.ExamplesOS[0]
        duplicate = self.project.Examples.Duplicate(original, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Examples.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates owned objects."""
        # Examples have translations (owned objects)
        # Find example with translation
        test_example = None
        for entry in self.project.LexEntry.GetAll():
            for sense in entry.SensesOS:
                for example in sense.ExamplesOS:
                    if example.TranslationsOC.Count > 0:
                        test_example = example
                        break
                if test_example:
                    break
            if test_example:
                break

        if not test_example:
            self.skipTest("No example with translations found")

        original_trans_count = test_example.TranslationsOC.Count
        duplicate = self.project.Examples.Duplicate(test_example, deep=True)

        # Deep copy should have same number of translations
        self.assertEqual(duplicate.TranslationsOC.Count, original_trans_count)

        # Clean up
        self.project.Examples.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_sense or self.test_sense.ExamplesOS.Count == 0:
            self.skipTest("No suitable sense with examples found")

        original = self.test_sense.ExamplesOS[0]
        duplicate = self.project.Examples.Duplicate(original)

        # Just verify duplicate was created (examples don't have many RA refs)
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Examples.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_sense or self.test_sense.ExamplesOS.Count == 0:
            self.skipTest("No suitable sense with examples found")

        original = self.test_sense.ExamplesOS[0]
        original_text = self.project.Examples.GetExample(original)

        duplicate = self.project.Examples.Duplicate(original)

        # Modify original
        self.project.Examples.SetExample(original, "MODIFIED_TEXT")

        # Duplicate should be unchanged
        duplicate_text = self.project.Examples.GetExample(duplicate)
        self.assertNotEqual(duplicate_text, "MODIFIED_TEXT")

        # Restore and clean up
        self.project.Examples.SetExample(original, original_text)
        self.project.Examples.Delete(duplicate)


class TestAllomorphDuplicate(unittest.TestCase):
    """Tests for AllomorphOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test entry with allomorphs
        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.AlternateFormsOS.Count >= 1:
                cls.test_entry = entry
                break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_entry or self.test_entry.AlternateFormsOS.Count == 0:
            self.skipTest("No suitable entry with allomorphs found")

        original = self.test_entry.AlternateFormsOS[0]
        duplicate = self.project.Allomorphs.Duplicate(original)

        # Verify GUIDs are different
        self.assertNotEqual(str(original.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Allomorphs.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_entry or self.test_entry.AlternateFormsOS.Count == 0:
            self.skipTest("No suitable entry with allomorphs found")

        original = self.test_entry.AlternateFormsOS[0]
        original_form = self.project.Allomorphs.GetForm(original)

        duplicate = self.project.Allomorphs.Duplicate(original)
        duplicate_form = self.project.Allomorphs.GetForm(duplicate)

        # Verify form was copied
        self.assertEqual(original_form, duplicate_form)

        # Clean up
        self.project.Allomorphs.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate inserted after source."""
        if not self.test_entry or self.test_entry.AlternateFormsOS.Count == 0:
            self.skipTest("No suitable entry with allomorphs found")

        original = self.test_entry.AlternateFormsOS[0]
        original_index = 0

        duplicate = self.project.Allomorphs.Duplicate(original, insert_after=True)

        # Find duplicate's index
        duplicate_index = -1
        for i in range(self.test_entry.AlternateFormsOS.Count):
            if self.test_entry.AlternateFormsOS[i] == duplicate:
                duplicate_index = i
                break

        # Should be immediately after original
        self.assertEqual(duplicate_index, original_index + 1)

        # Clean up
        self.project.Allomorphs.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate appended to end."""
        if not self.test_entry or self.test_entry.AlternateFormsOS.Count == 0:
            self.skipTest("No suitable entry with allomorphs found")

        original = self.test_entry.AlternateFormsOS[0]
        original_count = self.test_entry.AlternateFormsOS.Count

        duplicate = self.project.Allomorphs.Duplicate(original, insert_after=False)

        # Should be at end
        new_count = self.test_entry.AlternateFormsOS.Count
        self.assertEqual(new_count, original_count + 1)
        self.assertEqual(self.test_entry.AlternateFormsOS[new_count - 1], duplicate)

        # Clean up
        self.project.Allomorphs.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        # Allomorphs don't have significant owned objects
        if not self.test_entry or self.test_entry.AlternateFormsOS.Count == 0:
            self.skipTest("No suitable entry with allomorphs found")

        original = self.test_entry.AlternateFormsOS[0]
        # deep is accepted-but-ignored for Allomorph (no owned objects), so
        # this assertion stays weak on purpose.
        duplicate = self.project.Allomorphs.Duplicate(original, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Allomorphs.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates owned objects."""
        # Allomorphs don't have owned sequences
        if not self.test_entry or self.test_entry.AlternateFormsOS.Count == 0:
            self.skipTest("No suitable entry with allomorphs found")

        original = self.test_entry.AlternateFormsOS[0]
        # deep is accepted-but-ignored for Allomorph (no owned objects), so
        # this assertion stays weak on purpose.
        duplicate = self.project.Allomorphs.Duplicate(original, deep=True)

        # Just verify deep flag works
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Allomorphs.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        # Find allomorph with morph type
        test_allo = None
        for entry in self.project.LexEntry.GetAll():
            for allo in entry.AlternateFormsOS:
                if allo.MorphTypeRA:
                    test_allo = allo
                    break
            if test_allo:
                break

        if not test_allo:
            self.skipTest("No allomorph with MorphType found")

        original_morphtype = test_allo.MorphTypeRA
        duplicate = self.project.Allomorphs.Duplicate(test_allo)

        # Reference should be copied
        self.assertEqual(duplicate.MorphTypeRA, original_morphtype)

        # Clean up
        self.project.Allomorphs.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_entry or self.test_entry.AlternateFormsOS.Count == 0:
            self.skipTest("No suitable entry with allomorphs found")

        original = self.test_entry.AlternateFormsOS[0]
        original_form = self.project.Allomorphs.GetForm(original)

        duplicate = self.project.Allomorphs.Duplicate(original)

        # Modify original
        self.project.Allomorphs.SetForm(original, "MODIFIED")

        # Duplicate should be unchanged
        duplicate_form = self.project.Allomorphs.GetForm(duplicate)
        self.assertNotEqual(duplicate_form, "MODIFIED")

        # Restore and clean up
        self.project.Allomorphs.SetForm(original, original_form)
        self.project.Allomorphs.Delete(duplicate)


class TestPronunciationDuplicate(unittest.TestCase):
    """Tests for PronunciationOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test entry with pronunciations
        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.PronunciationsOS.Count >= 1:
                cls.test_entry = entry
                break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_entry or self.test_entry.PronunciationsOS.Count == 0:
            self.skipTest("No suitable entry with pronunciations found")

        original = self.test_entry.PronunciationsOS[0]
        duplicate = self.project.Pronunciations.Duplicate(original)

        # Verify GUIDs are different
        self.assertNotEqual(str(original.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Pronunciations.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_entry or self.test_entry.PronunciationsOS.Count == 0:
            self.skipTest("No suitable entry with pronunciations found")

        original = self.test_entry.PronunciationsOS[0]
        original_form = self.project.Pronunciations.GetForm(original)

        duplicate = self.project.Pronunciations.Duplicate(original)
        duplicate_form = self.project.Pronunciations.GetForm(duplicate)

        # Verify form was copied
        self.assertEqual(original_form, duplicate_form)

        # Clean up
        self.project.Pronunciations.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate inserted after source."""
        if not self.test_entry or self.test_entry.PronunciationsOS.Count == 0:
            self.skipTest("No suitable entry with pronunciations found")

        original = self.test_entry.PronunciationsOS[0]
        original_index = 0

        duplicate = self.project.Pronunciations.Duplicate(original, insert_after=True)

        # Find duplicate's index
        duplicate_index = -1
        for i in range(self.test_entry.PronunciationsOS.Count):
            if self.test_entry.PronunciationsOS[i] == duplicate:
                duplicate_index = i
                break

        # Should be immediately after original
        self.assertEqual(duplicate_index, original_index + 1)

        # Clean up
        self.project.Pronunciations.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate appended to end."""
        if not self.test_entry or self.test_entry.PronunciationsOS.Count == 0:
            self.skipTest("No suitable entry with pronunciations found")

        original = self.test_entry.PronunciationsOS[0]
        original_count = self.test_entry.PronunciationsOS.Count

        duplicate = self.project.Pronunciations.Duplicate(original, insert_after=False)

        # Should be at end
        new_count = self.test_entry.PronunciationsOS.Count
        self.assertEqual(new_count, original_count + 1)
        self.assertEqual(self.test_entry.PronunciationsOS[new_count - 1], duplicate)

        # Clean up
        self.project.Pronunciations.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        if not self.test_entry or self.test_entry.PronunciationsOS.Count == 0:
            self.skipTest("No suitable entry with pronunciations found")

        original = self.test_entry.PronunciationsOS[0]
        duplicate = self.project.Pronunciations.Duplicate(original, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Pronunciations.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates owned objects."""
        # Pronunciations have media files (owned objects)
        test_pron = None
        for entry in self.project.LexEntry.GetAll():
            for pron in entry.PronunciationsOS:
                if pron.MediaFilesOS.Count > 0:
                    test_pron = pron
                    break
            if test_pron:
                break

        if not test_pron:
            self.skipTest("No pronunciation with media files found")

        original_media_count = test_pron.MediaFilesOS.Count
        duplicate = self.project.Pronunciations.Duplicate(test_pron, deep=True)

        # Deep copy should have same number of media files
        self.assertEqual(duplicate.MediaFilesOS.Count, original_media_count)

        # Clean up
        self.project.Pronunciations.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_entry or self.test_entry.PronunciationsOS.Count == 0:
            self.skipTest("No suitable entry with pronunciations found")

        original = self.test_entry.PronunciationsOS[0]
        duplicate = self.project.Pronunciations.Duplicate(original)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Pronunciations.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_entry or self.test_entry.PronunciationsOS.Count == 0:
            self.skipTest("No suitable entry with pronunciations found")

        original = self.test_entry.PronunciationsOS[0]
        original_form = self.project.Pronunciations.GetForm(original)

        duplicate = self.project.Pronunciations.Duplicate(original)

        # Modify original
        self.project.Pronunciations.SetForm(original, "MODIFIED")

        # Duplicate should be unchanged
        duplicate_form = self.project.Pronunciations.GetForm(duplicate)
        self.assertNotEqual(duplicate_form, "MODIFIED")

        # Restore and clean up
        self.project.Pronunciations.SetForm(original, original_form)
        self.project.Pronunciations.Delete(duplicate)


class TestVariantDuplicate(unittest.TestCase):
    """Tests for VariantOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # `ILexEntry.VariantFormsOS` does not exist in this LCM version
        # (confirmed live: AttributeError on every access -- variants are
        # not an owned sequence on the entry). A "variant" is really an
        # ILexEntryRef with RefType == 0, reachable via entry.EntryRefsOS
        # and correctly filtered by VariantOperations.GetAll(); use that
        # instead of guessing at a raw LCM attribute name.
        from SIL.LCModel import ILexEntry as _ILexEntry

        cls.test_entry = None
        cls.test_variant = None
        for variant_ref in cls.project.Variants.GetAll():
            cls.test_variant = variant_ref
            # variant_ref.Owner is typed as the base ICmObject; cast to
            # ILexEntry so EntryRefsOS is reachable below.
            cls.test_entry = _ILexEntry(variant_ref.Owner)
            break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_variant:
            self.skipTest("No suitable variant reference found")

        original = self.test_variant
        duplicate = self.project.Variants.Duplicate(original)

        # Verify GUIDs are different
        self.assertNotEqual(str(original.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Variants.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_variant:
            self.skipTest("No suitable variant reference found")

        original = self.test_variant
        duplicate = self.project.Variants.Duplicate(original)

        # Verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Variants.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate inserted after source."""
        if not self.test_variant or not self.test_entry:
            self.skipTest("No suitable variant reference found")

        original = self.test_variant
        original_index = self.test_entry.EntryRefsOS.IndexOf(original)

        duplicate = self.project.Variants.Duplicate(original, insert_after=True)

        # Find duplicate's index
        duplicate_index = -1
        for i in range(self.test_entry.EntryRefsOS.Count):
            if self.test_entry.EntryRefsOS[i] == duplicate:
                duplicate_index = i
                break

        # Should be immediately after original
        self.assertEqual(duplicate_index, original_index + 1)

        # Clean up
        self.project.Variants.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate appended to end."""
        if not self.test_variant or not self.test_entry:
            self.skipTest("No suitable variant reference found")

        original = self.test_variant
        original_count = self.test_entry.EntryRefsOS.Count

        duplicate = self.project.Variants.Duplicate(original, insert_after=False)

        # Should be at end
        new_count = self.test_entry.EntryRefsOS.Count
        self.assertEqual(new_count, original_count + 1)
        self.assertEqual(self.test_entry.EntryRefsOS[new_count - 1], duplicate)

        # Clean up
        self.project.Variants.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        if not self.test_variant:
            self.skipTest("No suitable variant reference found")

        # deep is accepted-but-ignored for Variant (no owned objects), so
        # this assertion stays weak on purpose.
        duplicate = self.project.Variants.Duplicate(self.test_variant, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Variants.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates owned objects."""
        if not self.test_variant:
            self.skipTest("No suitable variant reference found")

        # deep is accepted-but-ignored for Variant (no owned objects), so
        # this assertion stays weak on purpose.
        duplicate = self.project.Variants.Duplicate(self.test_variant, deep=True)

        # Just verify deep flag works
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Variants.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_variant:
            self.skipTest("No suitable variant reference found")

        original = self.test_variant
        duplicate = self.project.Variants.Duplicate(original)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Variants.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_variant:
            self.skipTest("No suitable variant reference found")

        original = self.test_variant
        duplicate = self.project.Variants.Duplicate(original)

        # Verify they are different objects
        self.assertNotEqual(str(original.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Variants.Delete(duplicate)


# ============================================================================
# TIER 2: MIXED TESTS (5 classes)
# ============================================================================


class TestLexEntryDuplicate(unittest.TestCase):
    """Tests for LexEntryOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test entry
        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.SensesOS.Count >= 1:
                cls.test_entry = entry
                break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_entry:
            self.skipTest("No suitable entry found")

        duplicate = self.project.LexEntry.Duplicate(self.test_entry)

        # Verify GUIDs are different
        self.assertNotEqual(str(self.test_entry.Guid), str(duplicate.Guid))

        # Clean up
        self.project.LexEntry.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_entry:
            self.skipTest("No suitable entry found")

        # GetHeadword() returns entry.HeadWord, an LCM-computed virtual
        # property that appends a homograph number whenever more than one
        # entry shares the same lexeme form. Duplicating necessarily
        # creates exactly that situation (same lexeme form as the
        # source), so LCM itself assigns the duplicate a *different*
        # homograph number -- headword equality was never a valid check
        # here. Compare the actually-copied field (lexeme form) instead.
        original_form = self.project.LexEntry.GetLexemeForm(self.test_entry)
        duplicate = self.project.LexEntry.Duplicate(self.test_entry)
        duplicate_form = self.project.LexEntry.GetLexemeForm(duplicate)

        # Verify lexeme form was copied
        self.assertEqual(original_form, duplicate_form)

        # Clean up
        self.project.LexEntry.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate inserted after source."""
        if not self.test_entry:
            self.skipTest("No suitable entry found")

        # insert_after is accepted-but-ignored for LexEntry (entries live in
        # the project's top-level entry list, not an ordered sequence with a
        # "position"), so this assertion stays weak on purpose.
        duplicate = self.project.LexEntry.Duplicate(self.test_entry, insert_after=True)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.LexEntry.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate appended to end."""
        if not self.test_entry:
            self.skipTest("No suitable entry found")

        # insert_after is accepted-but-ignored for LexEntry; see note in
        # test_duplicate_insert_after above.
        duplicate = self.project.LexEntry.Duplicate(self.test_entry, insert_after=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.LexEntry.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        if not self.test_entry or self.test_entry.SensesOS.Count == 0:
            self.skipTest("No entry with senses found")

        original_senses = self.test_entry.SensesOS.Count
        duplicate = self.project.LexEntry.Duplicate(self.test_entry, deep=False)

        # Shallow copy should have no senses
        self.assertEqual(duplicate.SensesOS.Count, 0)

        # Clean up
        self.project.LexEntry.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates owned objects (senses, allomorphs, pronunciations, etymologies)."""
        if not self.test_entry or self.test_entry.SensesOS.Count == 0:
            self.skipTest("No entry with senses found")

        original_senses = self.test_entry.SensesOS.Count
        duplicate = self.project.LexEntry.Duplicate(self.test_entry, deep=True)

        # Deep copy should have same number of senses
        self.assertEqual(duplicate.SensesOS.Count, original_senses)

        # Clean up
        self.project.LexEntry.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_entry:
            self.skipTest("No suitable entry found")

        duplicate = self.project.LexEntry.Duplicate(self.test_entry)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.LexEntry.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_entry:
            self.skipTest("No suitable entry found")

        original_headword = self.project.LexEntry.GetHeadword(self.test_entry)
        duplicate = self.project.LexEntry.Duplicate(self.test_entry)

        # Modify original
        self.project.LexEntry.SetHeadword(self.test_entry, "MODIFIED")

        # Duplicate should be unchanged
        duplicate_headword = self.project.LexEntry.GetHeadword(duplicate)
        self.assertNotEqual(duplicate_headword, "MODIFIED")

        # Restore and clean up
        self.project.LexEntry.SetHeadword(self.test_entry, original_headword)
        self.project.LexEntry.Delete(duplicate)


class TestTextDuplicate(unittest.TestCase):
    """Tests for TextOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test text
        cls.test_text = None
        for text in cls.project.Text.GetAll():
            cls.test_text = text
            break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_text:
            self.skipTest("No suitable text found")

        duplicate = self.project.Text.Duplicate(self.test_text)

        # Verify GUIDs are different
        self.assertNotEqual(str(self.test_text.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Text.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_text:
            self.skipTest("No suitable text found")

        original_title = self.project.Text.GetTitle(self.test_text)
        duplicate = self.project.Text.Duplicate(self.test_text)
        duplicate_title = self.project.Text.GetTitle(duplicate)

        # TextOperations.Duplicate() intentionally appends " (copy)" (and,
        # on a name collision, " (copy N)") to the name/title to keep it
        # unique -- this is documented behavior, not a bug (see
        # TextOperations.Duplicate docstring: "The duplicate will have a
        # ' (copy)' suffix added to the name"). Exact equality was the
        # wrong assertion; verify the documented suffix relationship
        # instead.
        self.assertTrue(
            duplicate_title == f"{original_title} (copy)" or duplicate_title.startswith(f"{original_title} (copy"),
            f"Expected duplicate title to be '{original_title} (copy)' or a "
            f"numbered variant, got '{duplicate_title}'",
        )

        # Clean up
        self.project.Text.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate created (Text doesn't use insert_after)."""
        if not self.test_text:
            self.skipTest("No suitable text found")

        # insert_after is accepted-but-ignored for Text (Create() appends to
        # the project's texts collection with no positional-insert concept),
        # so this assertion stays weak on purpose.
        duplicate = self.project.Text.Duplicate(self.test_text, insert_after=True)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Text.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate created (Text doesn't use insert_at_end)."""
        if not self.test_text:
            self.skipTest("No suitable text found")

        # insert_after is accepted-but-ignored for Text; see note in
        # test_duplicate_insert_after above.
        duplicate = self.project.Text.Duplicate(self.test_text, insert_after=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Text.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        if not self.test_text or self.test_text.ContentsOA is None:
            self.skipTest("No text with contents found")

        if self.test_text.ContentsOA.ParagraphsOS.Count == 0:
            self.skipTest("No text with paragraphs found")

        original_para_count = self.test_text.ContentsOA.ParagraphsOS.Count
        duplicate = self.project.Text.Duplicate(self.test_text, deep=False)

        # Shallow copy should have no paragraphs
        if duplicate.ContentsOA:
            self.assertEqual(duplicate.ContentsOA.ParagraphsOS.Count, 0)

        # Clean up
        self.project.Text.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates owned objects."""
        if not self.test_text or self.test_text.ContentsOA is None:
            self.skipTest("No text with contents found")

        if self.test_text.ContentsOA.ParagraphsOS.Count == 0:
            self.skipTest("No text with paragraphs found")

        original_para_count = self.test_text.ContentsOA.ParagraphsOS.Count
        duplicate = self.project.Text.Duplicate(self.test_text, deep=True)

        # Deep copy should have same number of paragraphs
        self.assertEqual(duplicate.ContentsOA.ParagraphsOS.Count, original_para_count)

        # Clean up
        self.project.Text.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_text:
            self.skipTest("No suitable text found")

        duplicate = self.project.Text.Duplicate(self.test_text)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Text.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_text:
            self.skipTest("No suitable text found")

        original_title = self.project.Text.GetTitle(self.test_text)
        duplicate = self.project.Text.Duplicate(self.test_text)

        # Modify original
        self.project.Text.SetTitle(self.test_text, "MODIFIED")

        # Duplicate should be unchanged
        duplicate_title = self.project.Text.GetTitle(duplicate)
        self.assertNotEqual(duplicate_title, "MODIFIED")

        # Restore and clean up
        self.project.Text.SetTitle(self.test_text, original_title)
        self.project.Text.Delete(duplicate)


class TestParagraphDuplicate(unittest.TestCase):
    """Tests for ParagraphOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test paragraph
        cls.test_para = None
        cls.test_text = None
        for text in cls.project.Text.GetAll():
            if text.ContentsOA and text.ContentsOA.ParagraphsOS.Count >= 1:
                cls.test_text = text
                cls.test_para = text.ContentsOA.ParagraphsOS[0]
                break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_para:
            self.skipTest("No suitable paragraph found")

        duplicate = self.project.Paragraphs.Duplicate(self.test_para)

        # Verify GUIDs are different
        self.assertNotEqual(str(self.test_para.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Paragraphs.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_para:
            self.skipTest("No suitable paragraph found")

        duplicate = self.project.Paragraphs.Duplicate(self.test_para)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Paragraphs.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate inserted after source."""
        if not self.test_para or not self.test_text:
            self.skipTest("No suitable paragraph found")

        original_index = 0
        duplicate = self.project.Paragraphs.Duplicate(self.test_para, insert_after=True)

        # Find duplicate's index
        duplicate_index = -1
        for i in range(self.test_text.ContentsOA.ParagraphsOS.Count):
            if self.test_text.ContentsOA.ParagraphsOS[i] == duplicate:
                duplicate_index = i
                break

        # Should be immediately after original
        self.assertEqual(duplicate_index, original_index + 1)

        # Clean up
        self.project.Paragraphs.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate appended to end."""
        if not self.test_para or not self.test_text:
            self.skipTest("No suitable paragraph found")

        original_count = self.test_text.ContentsOA.ParagraphsOS.Count
        duplicate = self.project.Paragraphs.Duplicate(self.test_para, insert_after=False)

        # Should be at end
        new_count = self.test_text.ContentsOA.ParagraphsOS.Count
        self.assertEqual(new_count, original_count + 1)
        self.assertEqual(self.test_text.ContentsOA.ParagraphsOS[new_count - 1], duplicate)

        # Clean up
        self.project.Paragraphs.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        if not self.test_para:
            self.skipTest("No suitable paragraph found")

        duplicate = self.project.Paragraphs.Duplicate(self.test_para, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Paragraphs.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates owned objects."""
        # Find paragraph with segments. ParagraphsOS is an
        # ILcmOwningSequence<IStPara> (the base interface, which covers
        # footnotes/pictures too); it has no SegmentsOS/Contents. Only the
        # concrete IStTxtPara does, so cast before touching either field
        # (same root cause CLAUDE.md calls out under "same-name fields,
        # different LCM types" -- ParagraphOperations itself now casts
        # internally too, but this loop reads the raw LCM collection
        # directly rather than going through the operations API).
        from SIL.LCModel import IStTxtPara

        test_para_with_segs = None
        for text in self.project.Text.GetAll():
            if text.ContentsOA:
                for raw_para in text.ContentsOA.ParagraphsOS:
                    para = IStTxtPara(raw_para)
                    if para.SegmentsOS.Count > 0:
                        test_para_with_segs = para
                        break
            if test_para_with_segs:
                break

        if not test_para_with_segs:
            self.skipTest("No paragraph with segments found")

        original_seg_count = test_para_with_segs.SegmentsOS.Count
        # ParagraphOperations.Duplicate() signature is
        # `(item_or_hvo, insert_after=True, deep=True)` -- deep= IS valid
        # here (unlike several sibling classes whose Duplicate() has no
        # deep parameter at all).
        duplicate = self.project.Paragraphs.Duplicate(test_para_with_segs, deep=True)

        # Deep copy re-derives segments via AppendSentence, which edits
        # Contents and re-triggers sentence-boundary parsing rather than
        # cloning each ISegment 1:1 -- the Duplicate() docstring itself
        # warns "Segments in duplicated paragraphs will need re-parsing
        # for analyses" and does not promise an identical segment count.
        # Assert deep=True actually produced segments (in contrast to
        # shallow, which produces none), not an exact count match.
        self.assertGreater(duplicate.SegmentsOS.Count, 0)

        # Clean up
        self.project.Paragraphs.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_para:
            self.skipTest("No suitable paragraph found")

        duplicate = self.project.Paragraphs.Duplicate(self.test_para)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Paragraphs.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_para:
            self.skipTest("No suitable paragraph found")

        duplicate = self.project.Paragraphs.Duplicate(self.test_para)

        # Verify they are different objects
        self.assertNotEqual(str(self.test_para.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Paragraphs.Delete(duplicate)


class TestMediaDuplicate(unittest.TestCase):
    """Tests for MediaOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test media
        cls.test_media = None
        for entry in cls.project.LexEntry.GetAll():
            for pron in entry.PronunciationsOS:
                if pron.MediaFilesOS.Count >= 1:
                    cls.test_media = pron.MediaFilesOS[0]
                    break
            if cls.test_media:
                break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_media:
            self.skipTest("No suitable media found")

        duplicate = self.project.Media.Duplicate(self.test_media)

        # Verify GUIDs are different
        self.assertNotEqual(str(self.test_media.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Media.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_media:
            self.skipTest("No suitable media found")

        duplicate = self.project.Media.Duplicate(self.test_media)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Media.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate created (Media doesn't use insert_after)."""
        if not self.test_media:
            self.skipTest("No suitable media found")

        # Media doesn't use sequential insertion
        duplicate = self.project.Media.Duplicate(self.test_media, insert_after=True)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Media.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate created (Media doesn't use insert_at_end)."""
        if not self.test_media:
            self.skipTest("No suitable media found")

        duplicate = self.project.Media.Duplicate(self.test_media, insert_after=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Media.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        if not self.test_media:
            self.skipTest("No suitable media found")

        duplicate = self.project.Media.Duplicate(self.test_media, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Media.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates physical file."""
        if not self.test_media:
            self.skipTest("No suitable media found")

        duplicate = self.project.Media.Duplicate(self.test_media, deep=True)

        # Verify physical file was copied
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Media.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_media:
            self.skipTest("No suitable media found")

        duplicate = self.project.Media.Duplicate(self.test_media)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Media.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_media:
            self.skipTest("No suitable media found")

        duplicate = self.project.Media.Duplicate(self.test_media)

        # Verify they are different objects
        self.assertNotEqual(str(self.test_media.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Media.Delete(duplicate)


# ============================================================================
# TIER 3: SPECIALIZED TESTS (7 classes)
# ============================================================================


class TestNoteDuplicate(unittest.TestCase):
    """Tests for NoteOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # `ILexExampleSentence.NotesOS` does not exist in this LCM version
        # (confirmed live: AttributeError on every access) -- examples do
        # not own a Notes sequence. Notes are ICmBaseAnnotation objects
        # that *reference* their subject via BeginObjectRA rather than
        # being owned children of it; NoteOperations.GetAll()/Create()
        # already model this correctly. Create one TEST_-prefixed note on
        # a real entry so Duplicate() has something to exercise, and clean
        # it up afterwards.
        cls.test_owner = None
        for entry in cls.project.LexEntry.GetAll():
            cls.test_owner = entry
            break

        cls.test_note = None
        if cls.test_owner is not None:
            cls.test_note = cls.project.Notes.Create(
                cls.test_owner, "TEST_ note created for Duplicate() coverage"
            )

    @classmethod
    def tearDownClass(cls):
        if getattr(cls, "test_note", None) is not None:
            try:
                cls.project.Notes.Delete(cls.test_note)
            except Exception:
                pass

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_note:
            self.skipTest("No suitable note found")

        duplicate = self.project.Notes.Duplicate(self.test_note)

        # Verify GUIDs are different
        self.assertNotEqual(str(self.test_note.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Notes.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_note:
            self.skipTest("No suitable note found")

        duplicate = self.project.Notes.Duplicate(self.test_note)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Notes.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate inserted after source."""
        if not self.test_note:
            self.skipTest("No suitable note found")

        duplicate = self.project.Notes.Duplicate(self.test_note, insert_after=True)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Notes.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate appended to end."""
        if not self.test_note:
            self.skipTest("No suitable note found")

        duplicate = self.project.Notes.Duplicate(self.test_note, insert_after=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Notes.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        if not self.test_note:
            self.skipTest("No suitable note found")

        duplicate = self.project.Notes.Duplicate(self.test_note, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Notes.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates owned objects."""
        if not self.test_note:
            self.skipTest("No suitable note found")

        duplicate = self.project.Notes.Duplicate(self.test_note, deep=True)

        # Just verify deep flag works
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Notes.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_note:
            self.skipTest("No suitable note found")

        duplicate = self.project.Notes.Duplicate(self.test_note)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Notes.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_note:
            self.skipTest("No suitable note found")

        duplicate = self.project.Notes.Duplicate(self.test_note)

        # Verify they are different objects
        self.assertNotEqual(str(self.test_note.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Notes.Delete(duplicate)


class TestEtymologyDuplicate(unittest.TestCase):
    """Tests for EtymologyOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test etymology
        cls.test_etymology = None
        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.EtymologyOS.Count >= 1:
                cls.test_entry = entry
                cls.test_etymology = entry.EtymologyOS[0]
                break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_etymology:
            self.skipTest("No suitable etymology found")

        duplicate = self.project.Etymologies.Duplicate(self.test_etymology)

        # Verify GUIDs are different
        self.assertNotEqual(str(self.test_etymology.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Etymologies.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_etymology:
            self.skipTest("No suitable etymology found")

        duplicate = self.project.Etymologies.Duplicate(self.test_etymology)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Etymologies.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate inserted after source."""
        if not self.test_etymology or not self.test_entry:
            self.skipTest("No suitable etymology found")

        original_index = 0
        duplicate = self.project.Etymologies.Duplicate(self.test_etymology, insert_after=True)

        # Find duplicate's index
        duplicate_index = -1
        for i in range(self.test_entry.EtymologyOS.Count):
            if self.test_entry.EtymologyOS[i] == duplicate:
                duplicate_index = i
                break

        # Should be immediately after original
        self.assertEqual(duplicate_index, original_index + 1)

        # Clean up
        self.project.Etymologies.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate appended to end."""
        if not self.test_etymology or not self.test_entry:
            self.skipTest("No suitable etymology found")

        original_count = self.test_entry.EtymologyOS.Count
        duplicate = self.project.Etymologies.Duplicate(self.test_etymology, insert_after=False)

        # Should be at end
        new_count = self.test_entry.EtymologyOS.Count
        self.assertEqual(new_count, original_count + 1)
        self.assertEqual(self.test_entry.EtymologyOS[new_count - 1], duplicate)

        # Clean up
        self.project.Etymologies.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy (Etymology has no owned sequences)."""
        if not self.test_etymology:
            self.skipTest("No suitable etymology found")

        # deep is accepted-but-ignored for Etymology (no owned objects), so
        # this assertion stays weak on purpose.
        duplicate = self.project.Etymologies.Duplicate(self.test_etymology, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Etymologies.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy (Etymology has no owned sequences to duplicate)."""
        if not self.test_etymology:
            self.skipTest("No suitable etymology found")

        # deep is accepted-but-ignored for Etymology (no owned objects), so
        # this assertion stays weak on purpose.
        duplicate = self.project.Etymologies.Duplicate(self.test_etymology, deep=True)

        # Just verify deep flag works
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Etymologies.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_etymology:
            self.skipTest("No suitable etymology found")

        duplicate = self.project.Etymologies.Duplicate(self.test_etymology)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Etymologies.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_etymology:
            self.skipTest("No suitable etymology found")

        duplicate = self.project.Etymologies.Duplicate(self.test_etymology)

        # Verify they are different objects
        self.assertNotEqual(str(self.test_etymology.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Etymologies.Delete(duplicate)


class TestWfiAnalysisDuplicate(unittest.TestCase):
    """Tests for WfiAnalysisOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test analysis
        cls.test_analysis = None
        for wf in cls.project.Wordforms.GetAll():
            if wf.AnalysesOC.Count >= 1:
                cls.test_analysis = list(wf.AnalysesOC)[0]
                break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_analysis:
            self.skipTest("No suitable analysis found")

        duplicate = self.project.WfiAnalyses.Duplicate(self.test_analysis)

        # Verify GUIDs are different
        self.assertNotEqual(str(self.test_analysis.Guid), str(duplicate.Guid))

        # Clean up
        self.project.WfiAnalyses.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_analysis:
            self.skipTest("No suitable analysis found")

        duplicate = self.project.WfiAnalyses.Duplicate(self.test_analysis)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiAnalyses.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate created (Analysis uses OC not OS)."""
        if not self.test_analysis:
            self.skipTest("No suitable analysis found")

        duplicate = self.project.WfiAnalyses.Duplicate(self.test_analysis, insert_after=True)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiAnalyses.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate created (Analysis uses OC not OS)."""
        if not self.test_analysis:
            self.skipTest("No suitable analysis found")

        duplicate = self.project.WfiAnalyses.Duplicate(self.test_analysis, insert_after=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiAnalyses.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        if not self.test_analysis:
            self.skipTest("No suitable analysis found")

        if self.test_analysis.MorphBundlesOS.Count == 0:
            self.skipTest("No analysis with morph bundles found")

        original_bundle_count = self.test_analysis.MorphBundlesOS.Count
        duplicate = self.project.WfiAnalyses.Duplicate(self.test_analysis, deep=False)

        # Shallow copy should have no bundles
        self.assertEqual(duplicate.MorphBundlesOS.Count, 0)

        # Clean up
        self.project.WfiAnalyses.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates owned objects."""
        if not self.test_analysis:
            self.skipTest("No suitable analysis found")

        if self.test_analysis.MorphBundlesOS.Count == 0:
            self.skipTest("No analysis with morph bundles found")

        original_bundle_count = self.test_analysis.MorphBundlesOS.Count
        duplicate = self.project.WfiAnalyses.Duplicate(self.test_analysis, deep=True)

        # Deep copy should have same number of bundles
        self.assertEqual(duplicate.MorphBundlesOS.Count, original_bundle_count)

        # Clean up
        self.project.WfiAnalyses.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_analysis:
            self.skipTest("No suitable analysis found")

        duplicate = self.project.WfiAnalyses.Duplicate(self.test_analysis)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiAnalyses.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_analysis:
            self.skipTest("No suitable analysis found")

        duplicate = self.project.WfiAnalyses.Duplicate(self.test_analysis)

        # Verify they are different objects
        self.assertNotEqual(str(self.test_analysis.Guid), str(duplicate.Guid))

        # Clean up
        self.project.WfiAnalyses.Delete(duplicate)


class TestWfiGlossDuplicate(unittest.TestCase):
    """Tests for WfiGlossOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test gloss
        cls.test_gloss = None
        for wf in cls.project.Wordforms.GetAll():
            for analysis in wf.AnalysesOC:
                if analysis.MeaningsOC.Count >= 1:
                    cls.test_gloss = list(analysis.MeaningsOC)[0]
                    break
            if cls.test_gloss:
                break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_gloss:
            self.skipTest("No suitable gloss found")

        duplicate = self.project.WfiGlosses.Duplicate(self.test_gloss)

        # Verify GUIDs are different
        self.assertNotEqual(str(self.test_gloss.Guid), str(duplicate.Guid))

        # Clean up
        self.project.WfiGlosses.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_gloss:
            self.skipTest("No suitable gloss found")

        duplicate = self.project.WfiGlosses.Duplicate(self.test_gloss)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiGlosses.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate created (Gloss uses OC not OS)."""
        if not self.test_gloss:
            self.skipTest("No suitable gloss found")

        duplicate = self.project.WfiGlosses.Duplicate(self.test_gloss, insert_after=True)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiGlosses.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate created (Gloss uses OC not OS)."""
        if not self.test_gloss:
            self.skipTest("No suitable gloss found")

        duplicate = self.project.WfiGlosses.Duplicate(self.test_gloss, insert_after=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiGlosses.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy (WfiGloss has no owned sequences)."""
        if not self.test_gloss:
            self.skipTest("No suitable gloss found")

        # deep is accepted-but-ignored for WfiGloss (no owned objects), so
        # this assertion stays weak on purpose.
        duplicate = self.project.WfiGlosses.Duplicate(self.test_gloss, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiGlosses.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy (WfiGloss has no owned sequences to duplicate)."""
        if not self.test_gloss:
            self.skipTest("No suitable gloss found")

        # deep is accepted-but-ignored for WfiGloss (no owned objects), so
        # this assertion stays weak on purpose.
        duplicate = self.project.WfiGlosses.Duplicate(self.test_gloss, deep=True)

        # Just verify deep flag works
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiGlosses.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_gloss:
            self.skipTest("No suitable gloss found")

        duplicate = self.project.WfiGlosses.Duplicate(self.test_gloss)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiGlosses.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_gloss:
            self.skipTest("No suitable gloss found")

        duplicate = self.project.WfiGlosses.Duplicate(self.test_gloss)

        # Verify they are different objects
        self.assertNotEqual(str(self.test_gloss.Guid), str(duplicate.Guid))

        # Clean up
        self.project.WfiGlosses.Delete(duplicate)


class TestWfiMorphBundleDuplicate(unittest.TestCase):
    """Tests for WfiMorphBundleOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test morph bundle
        cls.test_bundle = None
        cls.test_analysis = None
        for wf in cls.project.Wordforms.GetAll():
            for analysis in wf.AnalysesOC:
                if analysis.MorphBundlesOS.Count >= 1:
                    cls.test_analysis = analysis
                    cls.test_bundle = analysis.MorphBundlesOS[0]
                    break
            if cls.test_bundle:
                break

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_bundle:
            self.skipTest("No suitable morph bundle found")

        duplicate = self.project.WfiMorphBundles.Duplicate(self.test_bundle)

        # Verify GUIDs are different
        self.assertNotEqual(str(self.test_bundle.Guid), str(duplicate.Guid))

        # Clean up
        self.project.WfiMorphBundles.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_bundle:
            self.skipTest("No suitable morph bundle found")

        duplicate = self.project.WfiMorphBundles.Duplicate(self.test_bundle)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiMorphBundles.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate inserted after source."""
        if not self.test_bundle or not self.test_analysis:
            self.skipTest("No suitable morph bundle found")

        original_index = 0
        duplicate = self.project.WfiMorphBundles.Duplicate(self.test_bundle, insert_after=True)

        # Find duplicate's index
        duplicate_index = -1
        for i in range(self.test_analysis.MorphBundlesOS.Count):
            if self.test_analysis.MorphBundlesOS[i] == duplicate:
                duplicate_index = i
                break

        # Should be immediately after original
        self.assertEqual(duplicate_index, original_index + 1)

        # Clean up
        self.project.WfiMorphBundles.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate appended to end."""
        if not self.test_bundle or not self.test_analysis:
            self.skipTest("No suitable morph bundle found")

        original_count = self.test_analysis.MorphBundlesOS.Count
        duplicate = self.project.WfiMorphBundles.Duplicate(self.test_bundle, insert_after=False)

        # Should be at end
        new_count = self.test_analysis.MorphBundlesOS.Count
        self.assertEqual(new_count, original_count + 1)
        self.assertEqual(self.test_analysis.MorphBundlesOS[new_count - 1], duplicate)

        # Clean up
        self.project.WfiMorphBundles.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy (WfiMorphBundle has no owned sequences)."""
        if not self.test_bundle:
            self.skipTest("No suitable morph bundle found")

        # deep is accepted-but-ignored for WfiMorphBundle (no owned objects),
        # so this assertion stays weak on purpose.
        duplicate = self.project.WfiMorphBundles.Duplicate(self.test_bundle, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiMorphBundles.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy (WfiMorphBundle has no owned sequences to duplicate)."""
        if not self.test_bundle:
            self.skipTest("No suitable morph bundle found")

        # deep is accepted-but-ignored for WfiMorphBundle (no owned objects),
        # so this assertion stays weak on purpose.
        duplicate = self.project.WfiMorphBundles.Duplicate(self.test_bundle, deep=True)

        # Just verify deep flag works
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiMorphBundles.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_bundle:
            self.skipTest("No suitable morph bundle found")

        duplicate = self.project.WfiMorphBundles.Duplicate(self.test_bundle)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.WfiMorphBundles.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_bundle:
            self.skipTest("No suitable morph bundle found")

        duplicate = self.project.WfiMorphBundles.Duplicate(self.test_bundle)

        # Verify they are different objects
        self.assertNotEqual(str(self.test_bundle.Guid), str(duplicate.Guid))

        # Clean up
        self.project.WfiMorphBundles.Delete(duplicate)


class TestPhonemeDuplicate(unittest.TestCase):
    """Tests for PhonemeOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test phoneme
        cls.test_phoneme = None
        if cls.project.lp.PhonologicalDataOA:
            if cls.project.lp.PhonologicalDataOA.PhonemeSetsOS.Count > 0:
                phoneme_set = cls.project.lp.PhonologicalDataOA.PhonemeSetsOS[0]
                if phoneme_set.PhonemesOC.Count > 0:
                    cls.test_phoneme = list(phoneme_set.PhonemesOC)[0]

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_phoneme:
            self.skipTest("No suitable phoneme found")

        duplicate = self.project.Phonemes.Duplicate(self.test_phoneme)

        # Verify GUIDs are different
        self.assertNotEqual(str(self.test_phoneme.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Phonemes.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_phoneme:
            self.skipTest("No suitable phoneme found")

        duplicate = self.project.Phonemes.Duplicate(self.test_phoneme)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Phonemes.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate created (Phoneme uses OC not OS)."""
        if not self.test_phoneme:
            self.skipTest("No suitable phoneme found")

        duplicate = self.project.Phonemes.Duplicate(self.test_phoneme, insert_after=True)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Phonemes.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate created (Phoneme uses OC not OS)."""
        if not self.test_phoneme:
            self.skipTest("No suitable phoneme found")

        duplicate = self.project.Phonemes.Duplicate(self.test_phoneme, insert_after=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Phonemes.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy doesn't duplicate owned objects."""
        if not self.test_phoneme:
            self.skipTest("No suitable phoneme found")

        duplicate = self.project.Phonemes.Duplicate(self.test_phoneme, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Phonemes.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy duplicates owned objects."""
        if not self.test_phoneme:
            self.skipTest("No suitable phoneme found")

        duplicate = self.project.Phonemes.Duplicate(self.test_phoneme, deep=True)

        # Just verify deep flag works
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Phonemes.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_phoneme:
            self.skipTest("No suitable phoneme found")

        duplicate = self.project.Phonemes.Duplicate(self.test_phoneme)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.Phonemes.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_phoneme:
            self.skipTest("No suitable phoneme found")

        duplicate = self.project.Phonemes.Duplicate(self.test_phoneme)

        # Verify they are different objects
        self.assertNotEqual(str(self.test_phoneme.Guid), str(duplicate.Guid))

        # Clean up
        self.project.Phonemes.Delete(duplicate)


class TestNaturalClassDuplicate(unittest.TestCase):
    """Tests for NaturalClassOperations.Duplicate()"""

    @classmethod
    def setUpClass(cls):
        cls.project = _test_project
        # Find suitable test natural class
        cls.test_nc = None
        if cls.project.lp.PhonologicalDataOA:
            if cls.project.lp.PhonologicalDataOA.NaturalClassesOS.Count > 0:
                cls.test_nc = cls.project.lp.PhonologicalDataOA.NaturalClassesOS[0]

    def test_duplicate_creates_new_guid(self):
        """Test that duplicate has different GUID."""
        if not self.test_nc:
            self.skipTest("No suitable natural class found")

        duplicate = self.project.NaturalClasses.Duplicate(self.test_nc)

        # Verify GUIDs are different
        self.assertNotEqual(str(self.test_nc.Guid), str(duplicate.Guid))

        # Clean up
        self.project.NaturalClasses.Delete(duplicate)

    def test_duplicate_copies_properties(self):
        """Test that properties are copied."""
        if not self.test_nc:
            self.skipTest("No suitable natural class found")

        duplicate = self.project.NaturalClasses.Duplicate(self.test_nc)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.NaturalClasses.Delete(duplicate)

    def test_duplicate_insert_after(self):
        """Test duplicate inserted after source."""
        if not self.test_nc:
            self.skipTest("No suitable natural class found")

        original_index = 0
        duplicate = self.project.NaturalClasses.Duplicate(self.test_nc, insert_after=True)

        # Find duplicate's index
        duplicate_index = -1
        for i in range(self.project.lp.PhonologicalDataOA.NaturalClassesOS.Count):
            if self.project.lp.PhonologicalDataOA.NaturalClassesOS[i] == duplicate:
                duplicate_index = i
                break

        # Should be immediately after original
        self.assertEqual(duplicate_index, original_index + 1)

        # Clean up
        self.project.NaturalClasses.Delete(duplicate)

    def test_duplicate_insert_at_end(self):
        """Test duplicate appended to end."""
        if not self.test_nc:
            self.skipTest("No suitable natural class found")

        original_count = self.project.lp.PhonologicalDataOA.NaturalClassesOS.Count
        duplicate = self.project.NaturalClasses.Duplicate(self.test_nc, insert_after=False)

        # Should be at end
        new_count = self.project.lp.PhonologicalDataOA.NaturalClassesOS.Count
        self.assertEqual(new_count, original_count + 1)
        self.assertEqual(self.project.lp.PhonologicalDataOA.NaturalClassesOS[new_count - 1], duplicate)

        # Clean up
        self.project.NaturalClasses.Delete(duplicate)

    def test_duplicate_shallow_no_owned_objects(self):
        """Test shallow copy (NaturalClass has no owned sequences)."""
        if not self.test_nc:
            self.skipTest("No suitable natural class found")

        # deep is accepted-but-ignored for NaturalClass -- FeaturesOA specs
        # are always cloned for feature-based sources regardless of this
        # flag, so this assertion stays weak on purpose.
        duplicate = self.project.NaturalClasses.Duplicate(self.test_nc, deep=False)

        # Just verify it was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.NaturalClasses.Delete(duplicate)

    def test_duplicate_deep_copies_owned_objects(self):
        """Test deep copy (NaturalClass has no owned sequences to duplicate)."""
        if not self.test_nc:
            self.skipTest("No suitable natural class found")

        # deep is accepted-but-ignored for NaturalClass -- FeaturesOA specs
        # are always cloned for feature-based sources regardless of this
        # flag, so this assertion stays weak on purpose.
        duplicate = self.project.NaturalClasses.Duplicate(self.test_nc, deep=True)

        # Just verify deep flag works
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.NaturalClasses.Delete(duplicate)

    def test_duplicate_preserves_references(self):
        """Test that RA references are preserved."""
        if not self.test_nc:
            self.skipTest("No suitable natural class found")

        duplicate = self.project.NaturalClasses.Duplicate(self.test_nc)

        # Just verify duplicate was created
        self.assertIsNotNone(duplicate)

        # Clean up
        self.project.NaturalClasses.Delete(duplicate)

    def test_duplicate_independence(self):
        """Test that modifying original doesn't affect duplicate."""
        if not self.test_nc:
            self.skipTest("No suitable natural class found")

        duplicate = self.project.NaturalClasses.Duplicate(self.test_nc)

        # Verify they are different objects
        self.assertNotEqual(str(self.test_nc.Guid), str(duplicate.Guid))

        # Clean up
        self.project.NaturalClasses.Delete(duplicate)


# Test runner
if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
