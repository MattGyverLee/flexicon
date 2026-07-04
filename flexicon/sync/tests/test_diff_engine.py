"""
Unit tests for DiffEngine

Author: FlexTools Development Team
Date: 2025-11-26
"""

import unittest
from unittest.mock import Mock, MagicMock


# Mock System.Guid
class MockGuid:
    def __init__(self, guid_string):
        self.value = guid_string

    def __str__(self):
        return self.value


from flexlibs2.sync.diff import DiffEngine, DiffResult, ChangeType, Change
from flexlibs2.sync.match_strategies import GuidMatchStrategy


class TestDiffResult(unittest.TestCase):
    """Test DiffResult class"""

    def setUp(self):
        """Set up test fixtures"""
        self.result = DiffResult("Allomorph")

    def test_initial_state(self):
        """Test initial empty state"""
        self.assertEqual(self.result.object_type, "Allomorph")
        self.assertEqual(self.result.total, 0)
        self.assertEqual(self.result.num_new, 0)
        self.assertEqual(self.result.num_modified, 0)
        self.assertEqual(self.result.num_deleted, 0)
        self.assertEqual(self.result.num_conflicts, 0)
        self.assertFalse(self.result.has_changes)
        self.assertFalse(self.result.has_conflicts)

    def test_add_new_change(self):
        """Test adding NEW change"""
        change = Change(
            change_type=ChangeType.NEW,
            source_guid="abc-123",
            target_guid=None,
            object_type="Allomorph",
            description="NEW: run-ing",
        )

        self.result.add_change(change)

        self.assertEqual(self.result.num_new, 1)
        self.assertEqual(self.result.total, 1)
        self.assertTrue(self.result.has_changes)
        self.assertIn(change, self.result.new_changes)

    def test_add_modified_change(self):
        """Test adding MODIFIED change"""
        change = Change(
            change_type=ChangeType.MODIFIED,
            source_guid="abc-123",
            target_guid="abc-123",
            object_type="Allomorph",
            description="MODIFIED: run-ing",
            details={"Form": "runing → run-ing"},
        )

        self.result.add_change(change)

        self.assertEqual(self.result.num_modified, 1)
        self.assertEqual(self.result.total, 1)
        self.assertTrue(self.result.has_changes)
        self.assertIn(change, self.result.modified_changes)

    def test_add_deleted_change(self):
        """Test adding DELETED change"""
        change = Change(
            change_type=ChangeType.DELETED,
            source_guid=None,
            target_guid="abc-123",
            object_type="Allomorph",
            description="DELETED: walk-ed",
        )

        self.result.add_change(change)

        self.assertEqual(self.result.num_deleted, 1)
        self.assertEqual(self.result.total, 1)
        self.assertTrue(self.result.has_changes)
        self.assertIn(change, self.result.deleted_changes)

    def test_add_conflict_change(self):
        """Test adding CONFLICT change"""
        change = Change(
            change_type=ChangeType.CONFLICT,
            source_guid="abc-123",
            target_guid="abc-123",
            object_type="Allomorph",
            description="CONFLICT: jump",
        )

        self.result.add_change(change)

        self.assertEqual(self.result.num_conflicts, 1)
        self.assertEqual(self.result.total, 1)
        self.assertTrue(self.result.has_changes)
        self.assertTrue(self.result.has_conflicts)
        self.assertIn(change, self.result.conflict_changes)

    def test_add_unchanged_change(self):
        """Test adding UNCHANGED change"""
        change = Change(
            change_type=ChangeType.UNCHANGED,
            source_guid="abc-123",
            target_guid="abc-123",
            object_type="Allomorph",
            description="UNCHANGED: test",
        )

        self.result.add_change(change)

        self.assertEqual(self.result.num_unchanged, 1)
        self.assertEqual(self.result.total, 0)  # Unchanged doesn't count in total
        self.assertFalse(self.result.has_changes)
        self.assertIn(change, self.result.unchanged_changes)

    def test_multiple_changes(self):
        """Test multiple changes of different types"""
        changes = [
            Change(ChangeType.NEW, "new-1", None, "Allomorph", "NEW 1"),
            Change(ChangeType.NEW, "new-2", None, "Allomorph", "NEW 2"),
            Change(ChangeType.MODIFIED, "mod-1", "mod-1", "Allomorph", "MOD 1"),
            Change(ChangeType.DELETED, None, "del-1", "Allomorph", "DEL 1"),
        ]

        for change in changes:
            self.result.add_change(change)

        self.assertEqual(self.result.num_new, 2)
        self.assertEqual(self.result.num_modified, 1)
        self.assertEqual(self.result.num_deleted, 1)
        self.assertEqual(self.result.total, 4)

    def test_summary(self):
        """Test summary generation"""
        summary = self.result.summary()

        self.assertIn("Allomorph", summary)
        self.assertIn("NEW", summary)
        self.assertIn("MODIFIED", summary)
        self.assertIn("DELETED", summary)
        self.assertIn("CONFLICTS", summary)

    def test_console_report(self):
        """Test console report generation"""
        # Add some changes
        self.result.add_change(Change(ChangeType.NEW, "new-1", None, "Allomorph", "NEW: test"))

        report = self.result.to_report(format="console", verbose=False)

        self.assertIn("DIFF SUMMARY", report)
        self.assertIn("NEW", report)
        self.assertIn("test", report)

    def test_markdown_report(self):
        """Test markdown report generation"""
        self.result.add_change(Change(ChangeType.NEW, "new-1", None, "Allomorph", "NEW: test"))

        report = self.result.to_report(format="markdown", verbose=False)

        self.assertIn("# Diff Report", report)
        self.assertIn("## Summary", report)
        self.assertIn("test", report)


class TestDiffEngine(unittest.TestCase):
    """Test DiffEngine class"""

    def setUp(self):
        """Set up test fixtures"""
        self.engine = DiffEngine()

        # Create mock operations
        self.source_ops = Mock()
        self.source_ops.__class__.__name__ = "AllomorphOperations"
        self.source_ops.GetForm = Mock(side_effect=lambda obj: obj.form)

        self.target_ops = Mock()
        self.target_ops.__class__.__name__ = "AllomorphOperations"
        self.target_ops.GetForm = Mock(side_effect=lambda obj: obj.form)

    def test_compare_empty_projects(self):
        """Test comparison with no objects"""
        self.source_ops.GetAll = Mock(return_value=[])
        self.target_ops.GetAll = Mock(return_value=[])

        result = self.engine.compare(self.source_ops, self.target_ops, None, None, GuidMatchStrategy())

        self.assertEqual(result.total, 0)
        self.assertFalse(result.has_changes)

    def test_compare_new_objects(self):
        """Test detection of NEW objects"""
        # Source has objects, target is empty
        source_obj = Mock()
        source_obj.Guid = MockGuid("abc-123")
        source_obj.form = "test"

        self.source_ops.GetAll = Mock(return_value=[source_obj])
        self.target_ops.GetAll = Mock(return_value=[])

        result = self.engine.compare(self.source_ops, self.target_ops, None, None, GuidMatchStrategy())

        self.assertEqual(result.num_new, 1)
        self.assertEqual(result.num_modified, 0)
        self.assertEqual(result.num_deleted, 0)

    def test_compare_deleted_objects(self):
        """Test detection of DELETED objects"""
        # Target has objects, source is empty
        target_obj = Mock()
        target_obj.Guid = MockGuid("abc-123")
        target_obj.form = "test"

        self.source_ops.GetAll = Mock(return_value=[])
        self.target_ops.GetAll = Mock(return_value=[target_obj])

        result = self.engine.compare(self.source_ops, self.target_ops, None, None, GuidMatchStrategy())

        self.assertEqual(result.num_new, 0)
        self.assertEqual(result.num_modified, 0)
        self.assertEqual(result.num_deleted, 1)

    def test_compare_unchanged_objects(self):
        """Test detection of UNCHANGED objects"""
        # Same object in both (same GUID, same form)
        source_obj = Mock()
        source_obj.Guid = MockGuid("abc-123")
        source_obj.form = "test"

        target_obj = Mock()
        target_obj.Guid = MockGuid("abc-123")
        target_obj.form = "test"

        self.source_ops.GetAll = Mock(return_value=[source_obj])
        self.target_ops.GetAll = Mock(return_value=[target_obj])

        result = self.engine.compare(self.source_ops, self.target_ops, None, None, GuidMatchStrategy())

        self.assertEqual(result.num_new, 0)
        self.assertEqual(result.num_modified, 0)
        self.assertEqual(result.num_deleted, 0)
        self.assertEqual(result.num_unchanged, 1)

    def test_compare_modified_objects(self):
        """Test detection of MODIFIED objects"""
        # Same GUID, different form
        source_obj = Mock()
        source_obj.Guid = MockGuid("abc-123")
        source_obj.form = "test-new"

        target_obj = Mock()
        target_obj.Guid = MockGuid("abc-123")
        target_obj.form = "test-old"

        self.source_ops.GetAll = Mock(return_value=[source_obj])
        self.target_ops.GetAll = Mock(return_value=[target_obj])

        result = self.engine.compare(self.source_ops, self.target_ops, None, None, GuidMatchStrategy())

        self.assertEqual(result.num_new, 0)
        self.assertEqual(result.num_modified, 1)
        self.assertEqual(result.num_deleted, 0)

        # Check details contain the change
        modified = result.modified_changes[0]
        self.assertIn("Form", modified.details)

    def test_compare_with_filter(self):
        """Test comparison with filter function"""
        obj1 = Mock()
        obj1.Guid = MockGuid("abc-123")
        obj1.form = "include-me"

        obj2 = Mock()
        obj2.Guid = MockGuid("def-456")
        obj2.form = "exclude-me"

        self.source_ops.GetAll = Mock(return_value=[obj1, obj2])
        self.target_ops.GetAll = Mock(return_value=[])

        # Filter: only include objects with "include" in form
        filter_fn = lambda obj: "include" in obj.form

        result = self.engine.compare(
            self.source_ops, self.target_ops, None, None, GuidMatchStrategy(), filter_fn=filter_fn
        )

        # Only obj1 should be included
        self.assertEqual(result.num_new, 1)

    def test_compare_with_progress_callback(self):
        """Test progress callback functionality"""
        source_obj = Mock()
        source_obj.Guid = MockGuid("abc-123")
        source_obj.form = "test"

        self.source_ops.GetAll = Mock(return_value=[source_obj])
        self.target_ops.GetAll = Mock(return_value=[])

        # Track callback invocations
        progress_messages = []

        def progress_callback(msg):
            progress_messages.append(msg)

        result = self.engine.compare(
            self.source_ops, self.target_ops, None, None, GuidMatchStrategy(), progress_callback=progress_callback
        )

        # Should have called progress callback
        self.assertGreater(len(progress_messages), 0)
        self.assertTrue(any("Loading source" in msg for msg in progress_messages))


if __name__ == "__main__":
    unittest.main()
