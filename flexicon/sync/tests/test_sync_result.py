"""
Unit tests for SyncResult class - Phase 2

Tests sync result tracking and reporting.

Author: FlexTools Development Team
Date: 2025-11-26
"""

import unittest
import os
import tempfile
from unittest.mock import Mock
from flexlibs2.sync.engine import SyncResult
from flexlibs2.sync.merge_ops import SyncChange, SyncError


class TestSyncResultInit(unittest.TestCase):
    """Test SyncResult initialization."""

    def test_init_basic(self):
        """Test basic initialization."""
        result = SyncResult("Allomorph")

        self.assertEqual(result.object_type, "Allomorph")
        self.assertEqual(result.num_created, 0)
        self.assertEqual(result.num_updated, 0)
        self.assertEqual(result.num_deleted, 0)
        self.assertEqual(result.num_skipped, 0)
        self.assertEqual(result.num_errors, 0)
        self.assertEqual(len(result.changes), 0)
        self.assertEqual(len(result.errors), 0)
        self.assertTrue(result.success)

    def test_total_property(self):
        """Test total property."""
        result = SyncResult("LexEntry")

        self.assertEqual(result.total, 0)

        result.num_created = 5
        result.num_updated = 3
        result.num_deleted = 2

        self.assertEqual(result.total, 10)


class TestSyncResultAddChange(unittest.TestCase):
    """Test adding changes to result."""

    def test_add_create_change(self):
        """Test adding a create change."""
        result = SyncResult("Phoneme")
        change = SyncChange("create", "Phoneme", "guid-123")

        result.add_change(change)

        self.assertEqual(result.num_created, 1)
        self.assertEqual(len(result.changes), 1)
        self.assertEqual(result.changes[0], change)

    def test_add_update_change(self):
        """Test adding an update change."""
        result = SyncResult("LexSense")
        change = SyncChange("update", "LexSense", "guid-456")

        result.add_change(change)

        self.assertEqual(result.num_updated, 1)
        self.assertEqual(len(result.changes), 1)

    def test_add_delete_change(self):
        """Test adding a delete change."""
        result = SyncResult("MorphType")
        change = SyncChange("delete", "MorphType", "guid-789")

        result.add_change(change)

        self.assertEqual(result.num_deleted, 1)
        self.assertEqual(len(result.changes), 1)

    def test_skip_method(self):
        """Test skip() method."""
        result = SyncResult("PartOfSpeech")

        result.skip()

        self.assertEqual(result.num_skipped, 1)

    def test_add_multiple_changes(self):
        """Test adding multiple changes."""
        result = SyncResult("Allomorph")

        result.add_change(SyncChange("create", "Allomorph", "guid-1"))
        result.add_change(SyncChange("create", "Allomorph", "guid-2"))
        result.add_change(SyncChange("update", "Allomorph", "guid-3"))
        result.add_change(SyncChange("delete", "Allomorph", "guid-4"))

        self.assertEqual(result.num_created, 2)
        self.assertEqual(result.num_updated, 1)
        self.assertEqual(result.num_deleted, 1)
        self.assertEqual(result.total, 4)
        self.assertEqual(len(result.changes), 4)

    def test_add_unknown_operation_type(self):
        """Test adding change with unknown operation type."""
        result = SyncResult("LexEntry")
        change = SyncChange("merge", "LexEntry", "guid-xyz")

        result.add_change(change)

        # Should still add to changes list but not increment counters
        self.assertEqual(len(result.changes), 1)
        self.assertEqual(result.total, 0)


class TestSyncResultAddError(unittest.TestCase):
    """Test adding errors to result."""

    def test_add_error(self):
        """Test adding an error."""
        result = SyncResult("Phoneme")
        error = SyncError("create", "guid-err", "Failed to create phoneme")

        result.add_error(error)

        self.assertEqual(result.num_errors, 1)
        self.assertEqual(len(result.errors), 1)
        self.assertEqual(result.errors[0], error)
        self.assertFalse(result.success)

    def test_add_multiple_errors(self):
        """Test adding multiple errors."""
        result = SyncResult("LexEntry")

        result.add_error(SyncError("create", "guid-1", "Error 1"))
        result.add_error(SyncError("update", "guid-2", "Error 2"))
        result.add_error(SyncError("delete", "guid-3", "Error 3"))

        self.assertEqual(result.num_errors, 3)
        self.assertEqual(len(result.errors), 3)
        self.assertFalse(result.success)

    def test_success_property_with_errors(self):
        """Test success property with errors."""
        result = SyncResult("Allomorph")

        # Initially success
        self.assertTrue(result.success)

        # Add error
        result.add_error(SyncError("create", "guid-err", "Error"))

        # Now not success
        self.assertFalse(result.success)


class TestSyncResultSummary(unittest.TestCase):
    """Test summary generation."""

    def test_summary_no_changes(self):
        """Test summary with no changes."""
        result = SyncResult("Phoneme")
        summary = result.summary()

        self.assertIn("Phoneme", summary)
        self.assertIn("Created: 0", summary)
        self.assertIn("Updated: 0", summary)
        self.assertIn("Total: 0", summary)

    def test_summary_with_changes(self):
        """Test summary with changes."""
        result = SyncResult("Allomorph")

        result.add_change(SyncChange("create", "Allomorph", "g1"))
        result.add_change(SyncChange("create", "Allomorph", "g2"))
        result.add_change(SyncChange("update", "Allomorph", "g3"))

        summary = result.summary()

        self.assertIn("Allomorph", summary)
        self.assertIn("Total: 3", summary)
        self.assertIn("Created: 2", summary)
        self.assertIn("Updated: 1", summary)

    def test_summary_with_errors(self):
        """Test summary with errors."""
        result = SyncResult("LexEntry")

        result.add_change(SyncChange("create", "LexEntry", "g1"))
        result.add_error(SyncError("update", "g2", "Failed"))

        summary = result.summary()

        self.assertIn("Created: 1", summary)
        self.assertIn("Errors: 1", summary)
        self.assertTrue("⚠" in summary or "error" in summary.lower())

    def test_summary_success_indicator(self):
        """Test summary includes success indicator."""
        result1 = SyncResult("Phoneme")
        result1.add_change(SyncChange("create", "Phoneme", "g1"))
        summary1 = result1.summary()

        # Successful sync should have positive indicator
        self.assertIn("✅", summary1)

        result2 = SyncResult("Phoneme")
        result2.add_error(SyncError("create", "g1", "Error"))
        summary2 = result2.summary()

        # Failed sync should have negative indicator
        self.assertIn("⚠", summary2)


class TestSyncResultExportLog(unittest.TestCase):
    """Test log export functionality."""

    def test_export_log_basic(self):
        """Test exporting log to file."""
        result = SyncResult("Allomorph")

        result.add_change(SyncChange("create", "Allomorph", "guid-1", {"form": "test"}))
        result.add_change(SyncChange("update", "Allomorph", "guid-2"))

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "test_sync.log")
            result.export_log(log_file)

            # Verify file exists
            self.assertTrue(os.path.exists(log_file))

            # Read and verify content
            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("Allomorph", content)
            self.assertIn("CREATE", content)
            self.assertIn("UPDATE", content)
            self.assertIn("guid-1", content)
            self.assertIn("guid-2", content)

    def test_export_log_with_errors(self):
        """Test exporting log with errors."""
        result = SyncResult("LexEntry")

        result.add_change(SyncChange("create", "LexEntry", "guid-ok"))
        result.add_error(SyncError("update", "guid-err", "Update failed"))

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "error_sync.log")
            result.export_log(log_file)

            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("guid-ok", content)
            self.assertIn("guid-err", content)
            self.assertIn("Update failed", content)
            self.assertIn("ERROR", content.upper())

    def test_export_log_empty(self):
        """Test exporting log with no changes."""
        result = SyncResult("Phoneme")

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "empty_sync.log")
            result.export_log(log_file)

            self.assertTrue(os.path.exists(log_file))

            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("Phoneme", content)
            self.assertIn("Total: 0", content)

    def test_export_log_unicode(self):
        """Test exporting log with unicode content."""
        result = SyncResult("Allomorph")

        result.add_change(SyncChange("create", "Allomorph", "guid-unicode", {"form": "café", "gloss": "日本語"}))

        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "unicode_sync.log")
            result.export_log(log_file)

            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()

            self.assertIn("café", content)
            self.assertIn("日本語", content)


class TestSyncResultIntegration(unittest.TestCase):
    """Integration tests for SyncResult."""

    def test_full_sync_workflow(self):
        """Test complete sync workflow tracking."""
        result = SyncResult("Allomorph")

        # Add various changes
        for i in range(5):
            result.add_change(SyncChange("create", "Allomorph", f"new-{i}"))

        for i in range(3):
            result.add_change(SyncChange("update", "Allomorph", f"mod-{i}"))

        # Skip one
        result.skip()

        # Add an error
        result.add_error(SyncError("create", "err-1", "Failed"))

        # Verify counts
        self.assertEqual(result.num_created, 5)
        self.assertEqual(result.num_updated, 3)
        self.assertEqual(result.num_deleted, 0)
        self.assertEqual(result.num_skipped, 1)
        self.assertEqual(result.num_errors, 1)
        self.assertEqual(result.total, 8)  # created + updated
        self.assertFalse(result.success)

        # Export and verify
        with tempfile.TemporaryDirectory() as tmpdir:
            log_file = os.path.join(tmpdir, "workflow.log")
            result.export_log(log_file)

            with open(log_file, "r", encoding="utf-8") as f:
                content = f.read()

            # Should contain all types
            self.assertIn("create", content.lower())
            self.assertIn("update", content.lower())
            self.assertIn("error", content.lower())


if __name__ == "__main__":
    unittest.main()
