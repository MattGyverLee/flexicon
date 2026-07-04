"""
Unit tests for BaseOperations Reordering Methods

Tests all 7 reordering methods inherited by operation classes:
- Sort
- MoveUp
- MoveDown
- MoveToIndex
- MoveBefore
- MoveAfter
- Swap

Author: FlexTools Development Team - Programmer 3 (Test Engineer)
Date: 2025-12-04 (Revised)
Project: BaseOperations Implementation - Phase 3
"""

import unittest
import sys
import os

# Add parent directory to sys.path to allow importing flexlibs2
_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.join(_test_dir, "..", "..", "..")
sys.path.insert(0, _project_root)

from flexlibs2 import FLExProject, FLExInitialize, FLExCleanup


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
# TEST CLASSES
# ============================================================================


class TestBaseOperationsInheritance(unittest.TestCase):
    """
    Test that BaseOperations is properly inherited by operation classes.
    Verifies all operation classes have reordering methods available.
    """

    @classmethod
    def setUpClass(cls):
        """Get reference to shared project."""
        cls.project = _test_project

    def test_lexsense_has_reordering_methods(self):
        """Test LexSenseOperations has all 7 reordering methods."""
        self.assertTrue(hasattr(self.project.Senses, "Sort"))
        self.assertTrue(hasattr(self.project.Senses, "MoveUp"))
        self.assertTrue(hasattr(self.project.Senses, "MoveDown"))
        self.assertTrue(hasattr(self.project.Senses, "MoveToIndex"))
        self.assertTrue(hasattr(self.project.Senses, "MoveBefore"))
        self.assertTrue(hasattr(self.project.Senses, "MoveAfter"))
        self.assertTrue(hasattr(self.project.Senses, "Swap"))

    def test_allomorph_has_reordering_methods(self):
        """Test AllomorphOperations has all 7 reordering methods."""
        self.assertTrue(hasattr(self.project.Allomorphs, "Sort"))
        self.assertTrue(hasattr(self.project.Allomorphs, "MoveUp"))
        self.assertTrue(hasattr(self.project.Allomorphs, "MoveDown"))
        self.assertTrue(hasattr(self.project.Allomorphs, "MoveToIndex"))
        self.assertTrue(hasattr(self.project.Allomorphs, "MoveBefore"))
        self.assertTrue(hasattr(self.project.Allomorphs, "MoveAfter"))
        self.assertTrue(hasattr(self.project.Allomorphs, "Swap"))

    def test_example_has_reordering_methods(self):
        """Test ExampleOperations has all 7 reordering methods."""
        self.assertTrue(hasattr(self.project.Examples, "Sort"))
        self.assertTrue(hasattr(self.project.Examples, "MoveUp"))
        self.assertTrue(hasattr(self.project.Examples, "MoveDown"))
        self.assertTrue(hasattr(self.project.Examples, "MoveToIndex"))
        self.assertTrue(hasattr(self.project.Examples, "MoveBefore"))
        self.assertTrue(hasattr(self.project.Examples, "MoveAfter"))
        self.assertTrue(hasattr(self.project.Examples, "Swap"))


class TestBaseOperationsSortMethod(unittest.TestCase):
    """Test Sort method with multiple test cases using EXISTING DATA."""

    @classmethod
    def setUpClass(cls):
        """Get reference to shared project and find entry with multiple senses."""
        cls.project = _test_project

        # Find an existing entry with multiple senses to test with
        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.SensesOS.Count >= 3:
                cls.test_entry = entry
                break

        if not cls.test_entry:
            raise unittest.SkipTest("No entry with 3+ senses found for testing")

    def test_sort_method_exists_and_returns_count(self):
        """Test that Sort() method works and returns item count."""
        # Get current sense count
        sense_count = self.test_entry.SensesOS.Count

        # Sort by gloss (whatever order)
        result = self.project.Senses.Sort(self.test_entry, key_func=lambda s: self.project.Senses.GetGloss(s) or "")

        # Verify it returns the count
        self.assertEqual(result, sense_count)

        # Verify all senses still present
        self.assertEqual(self.test_entry.SensesOS.Count, sense_count)

    def test_sort_preserves_all_senses(self):
        """Test that sorting doesn't lose any senses."""
        # Record GUIDs before sort
        original_guids = set(str(s.Guid) for s in self.test_entry.SensesOS)

        # Sort
        self.project.Senses.Sort(self.test_entry, key_func=lambda s: self.project.Senses.GetGloss(s) or "")

        # Verify same GUIDs present
        new_guids = set(str(s.Guid) for s in self.test_entry.SensesOS)
        self.assertEqual(original_guids, new_guids)


class TestBaseOperationsMoveUpMethod(unittest.TestCase):
    """Test MoveUp method with boundary conditions using EXISTING DATA."""

    @classmethod
    def setUpClass(cls):
        """Get reference to shared project and find suitable entry."""
        cls.project = _test_project

        # Find entry with 3+ senses
        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.SensesOS.Count >= 3:
                cls.test_entry = entry
                break

        if not cls.test_entry:
            raise unittest.SkipTest("No entry with 3+ senses found")

    def test_move_up_from_middle(self):
        """Test moving item up from middle position."""
        if self.test_entry.SensesOS.Count < 3:
            self.skipTest("Need at least 3 senses")

        # Get middle sense
        senses = list(self.test_entry.SensesOS)
        middle_index = len(senses) // 2
        sense_to_move = senses[middle_index]

        # Move up by 1
        moved = self.project.Senses.MoveUp(self.test_entry, sense_to_move, positions=1)

        # Should have moved 1 position
        self.assertEqual(moved, 1)

        # Verify new position
        new_index = list(self.test_entry.SensesOS).index(sense_to_move)
        self.assertEqual(new_index, middle_index - 1)

        # Move back to restore original order
        self.project.Senses.MoveDown(self.test_entry, sense_to_move, positions=1)

    def test_move_up_at_start_returns_zero(self):
        """Test that moving first item up returns 0."""
        first_sense = self.test_entry.SensesOS[0]

        moved = self.project.Senses.MoveUp(self.test_entry, first_sense, positions=1)

        # Should return 0 (can't move up from index 0)
        self.assertEqual(moved, 0)


class TestBaseOperationsMoveDownMethod(unittest.TestCase):
    """Test MoveDown method using EXISTING DATA."""

    @classmethod
    def setUpClass(cls):
        """Get reference to shared project and find suitable entry."""
        cls.project = _test_project

        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.SensesOS.Count >= 3:
                cls.test_entry = entry
                break

        if not cls.test_entry:
            raise unittest.SkipTest("No entry with 3+ senses found")

    def test_move_down_from_start(self):
        """Test moving first item down."""
        if self.test_entry.SensesOS.Count < 2:
            self.skipTest("Need at least 2 senses")

        first_sense = self.test_entry.SensesOS[0]

        moved = self.project.Senses.MoveDown(self.test_entry, first_sense, positions=1)

        self.assertEqual(moved, 1)

        # Verify new position
        new_index = list(self.test_entry.SensesOS).index(first_sense)
        self.assertEqual(new_index, 1)

        # Restore original order
        self.project.Senses.MoveUp(self.test_entry, first_sense, positions=1)

    def test_move_down_at_end_returns_zero(self):
        """Test that moving last item down returns 0."""
        last_sense = self.test_entry.SensesOS[self.test_entry.SensesOS.Count - 1]

        moved = self.project.Senses.MoveDown(self.test_entry, last_sense, positions=1)

        # Should return 0 (can't move down from last position)
        self.assertEqual(moved, 0)


class TestBaseOperationsMoveToIndexMethod(unittest.TestCase):
    """Test MoveToIndex method using EXISTING DATA."""

    @classmethod
    def setUpClass(cls):
        """Get reference to shared project."""
        cls.project = _test_project

        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.SensesOS.Count >= 3:
                cls.test_entry = entry
                break

        if not cls.test_entry:
            raise unittest.SkipTest("No entry with 3+ senses found")

    def test_move_to_index_forward(self):
        """Test moving item forward to specific index."""
        if self.test_entry.SensesOS.Count < 3:
            self.skipTest("Need at least 3 senses")

        # Move first sense to position 2
        first_sense = self.test_entry.SensesOS[0]
        original_index = 0
        target_index = 2

        result = self.project.Senses.MoveToIndex(self.test_entry, first_sense, target_index)

        self.assertTrue(result)

        # Verify new position
        new_index = list(self.test_entry.SensesOS).index(first_sense)
        self.assertEqual(new_index, target_index)

        # Restore
        self.project.Senses.MoveToIndex(self.test_entry, first_sense, original_index)


class TestBaseOperationsMoveBeforeMoveAfter(unittest.TestCase):
    """Test MoveBefore and MoveAfter methods using EXISTING DATA."""

    @classmethod
    def setUpClass(cls):
        """Get reference to shared project."""
        cls.project = _test_project

        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.SensesOS.Count >= 3:
                cls.test_entry = entry
                break

        if not cls.test_entry:
            raise unittest.SkipTest("No entry with 3+ senses found")

    def test_move_before(self):
        """Test moving item before another item."""
        if self.test_entry.SensesOS.Count < 3:
            self.skipTest("Need at least 3 senses")

        # Move last sense before first
        senses = list(self.test_entry.SensesOS)
        item_to_move = senses[-1]
        target = senses[0]

        result = self.project.Senses.MoveBefore(item_to_move, target)

        self.assertTrue(result)

        # item_to_move should now be before target
        new_senses = list(self.test_entry.SensesOS)
        move_index = new_senses.index(item_to_move)
        target_index = new_senses.index(target)

        self.assertLess(move_index, target_index)

        # Restore (move back to end)
        self.project.Senses.MoveToIndex(self.test_entry, item_to_move, self.test_entry.SensesOS.Count - 1)

    def test_move_after(self):
        """Test moving item after another item."""
        if self.test_entry.SensesOS.Count < 3:
            self.skipTest("Need at least 3 senses")

        # Move first sense after second
        senses = list(self.test_entry.SensesOS)
        item_to_move = senses[0]
        target = senses[1]

        result = self.project.Senses.MoveAfter(item_to_move, target)

        self.assertTrue(result)

        # item_to_move should now be after target
        new_senses = list(self.test_entry.SensesOS)
        move_index = new_senses.index(item_to_move)
        target_index = new_senses.index(target)

        self.assertGreater(move_index, target_index)

        # Restore
        self.project.Senses.MoveToIndex(self.test_entry, item_to_move, 0)


class TestBaseOperationsSwapMethod(unittest.TestCase):
    """Test Swap method using EXISTING DATA."""

    @classmethod
    def setUpClass(cls):
        """Get reference to shared project."""
        cls.project = _test_project

        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.SensesOS.Count >= 2:
                cls.test_entry = entry
                break

        if not cls.test_entry:
            raise unittest.SkipTest("No entry with 2+ senses found")

    def test_swap_two_items(self):
        """Test swapping two items."""
        if self.test_entry.SensesOS.Count < 2:
            self.skipTest("Need at least 2 senses")

        # Swap first two senses
        sense1 = self.test_entry.SensesOS[0]
        sense2 = self.test_entry.SensesOS[1]

        result = self.project.Senses.Swap(sense1, sense2)

        self.assertTrue(result)

        # Verify positions swapped
        new_senses = list(self.test_entry.SensesOS)
        self.assertEqual(new_senses[0], sense2)
        self.assertEqual(new_senses[1], sense1)

        # Swap back to restore
        self.project.Senses.Swap(sense1, sense2)


class TestBaseOperationsDataPreservation(unittest.TestCase):
    """Test that reordering preserves all object data using EXISTING DATA."""

    @classmethod
    def setUpClass(cls):
        """Get reference to shared project."""
        cls.project = _test_project

        cls.test_entry = None
        for entry in cls.project.LexEntry.GetAll():
            if entry.SensesOS.Count >= 2:
                cls.test_entry = entry
                break

        if not cls.test_entry:
            raise unittest.SkipTest("No entry with 2+ senses found")

    def test_reordering_preserves_guids(self):
        """Test that reordering doesn't change object GUIDs."""
        # Record original GUIDs
        original_guids = [str(s.Guid) for s in self.test_entry.SensesOS]
        original_count = len(original_guids)

        # Sort
        self.project.Senses.Sort(self.test_entry, key_func=lambda s: self.project.Senses.GetGloss(s) or "")

        # Verify same GUIDs present (may be in different order)
        new_guids = [str(s.Guid) for s in self.test_entry.SensesOS]
        self.assertEqual(len(new_guids), original_count)
        self.assertEqual(set(original_guids), set(new_guids))

    def test_reordering_preserves_properties(self):
        """Test that reordering preserves all properties."""
        # Record original data for each sense
        original_data = {}
        for sense in self.test_entry.SensesOS:
            guid = str(sense.Guid)
            original_data[guid] = {
                "gloss": self.project.Senses.GetGloss(sense),
                "definition": self.project.Senses.GetDefinition(sense),
            }

        # Reorder
        if self.test_entry.SensesOS.Count >= 2:
            self.project.Senses.Swap(self.test_entry.SensesOS[0], self.test_entry.SensesOS[1])

        # Verify all properties intact
        for sense in self.test_entry.SensesOS:
            guid = str(sense.Guid)
            self.assertEqual(self.project.Senses.GetGloss(sense), original_data[guid]["gloss"])
            self.assertEqual(self.project.Senses.GetDefinition(sense), original_data[guid]["definition"])

        # Restore order if we swapped
        if self.test_entry.SensesOS.Count >= 2:
            self.project.Senses.Swap(self.test_entry.SensesOS[0], self.test_entry.SensesOS[1])


class TestBaseOperationsIntegration(unittest.TestCase):
    """Integration tests across multiple operation classes using EXISTING DATA."""

    @classmethod
    def setUpClass(cls):
        """Get reference to shared project."""
        cls.project = _test_project

    def test_inheritance_works_across_all_classes(self):
        """Test that all operation classes have inherited methods."""
        # Test a variety of operation classes
        operations_to_test = [
            ("Senses", self.project.Senses),
            ("Examples", self.project.Examples),
            ("Allomorphs", self.project.Allomorphs),
            ("POS", self.project.POS),
            ("Phonemes", self.project.Phonemes),
        ]

        for name, ops in operations_to_test:
            with self.subTest(operation=name):
                self.assertTrue(hasattr(ops, "Sort"), f"{name} should have Sort method")
                self.assertTrue(hasattr(ops, "MoveUp"), f"{name} should have MoveUp method")
                self.assertTrue(hasattr(ops, "MoveDown"), f"{name} should have MoveDown method")
                self.assertTrue(hasattr(ops, "Swap"), f"{name} should have Swap method")


# Test runner
if __name__ == "__main__":
    # Run tests with verbose output
    unittest.main(verbosity=2)
