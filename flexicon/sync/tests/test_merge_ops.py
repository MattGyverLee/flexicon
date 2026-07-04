"""
Unit tests for MergeOperations module - Phase 2

Tests safe execution of Create/Update/Delete operations.

Author: FlexTools Development Team
Date: 2025-11-26
"""

import unittest
from unittest.mock import Mock, MagicMock, patch, call
from flexlibs2.sync.merge_ops import MergeOperations, SyncChange, SyncError


class TestSyncChange(unittest.TestCase):
    """Test SyncChange data class."""

    def test_sync_change_create(self):
        """Test creating a SyncChange for create operation."""
        change = SyncChange(
            operation="create", object_type="Allomorph", object_guid="test-guid-123", details={"form": "test"}
        )

        self.assertEqual(change.operation, "create")
        self.assertEqual(change.object_type, "Allomorph")
        self.assertEqual(change.object_guid, "test-guid-123")
        self.assertEqual(change.details, {"form": "test"})

    def test_sync_change_minimal(self):
        """Test creating a SyncChange with minimal info."""
        change = SyncChange(operation="update", object_type="LexEntry", object_guid="guid-456")

        self.assertEqual(change.operation, "update")
        self.assertEqual(change.details, {})


class TestSyncError(unittest.TestCase):
    """Test SyncError data class."""

    def test_sync_error_create(self):
        """Test creating a SyncError."""
        error = SyncError(operation="create", object_guid="error-guid", error_message="Failed to create object")

        self.assertEqual(error.operation, "create")
        self.assertEqual(error.object_guid, "error-guid")
        self.assertEqual(error.error_message, "Failed to create object")

    def test_sync_error_minimal(self):
        """Test creating a SyncError without guid."""
        error = SyncError(operation="delete", object_guid=None, error_message="Object not found")

        self.assertEqual(error.operation, "delete")
        self.assertIsNone(error.object_guid)
        self.assertEqual(error.error_message, "Object not found")


class TestMergeOperationsInit(unittest.TestCase):
    """Test MergeOperations initialization."""

    def test_init_with_write_enabled(self):
        """Test initialization with writeEnabled=True."""
        project = Mock()
        project.writeEnabled = True

        merger = MergeOperations(project)

        self.assertEqual(merger.target_project, project)

    def test_init_readonly_raises_error(self):
        """Test initialization with writeEnabled=False raises error."""
        project = Mock()
        project.writeEnabled = False

        with self.assertRaises(RuntimeError) as ctx:
            MergeOperations(project)

        self.assertIn("not opened with writeEnabled=True", str(ctx.exception))

    def test_init_no_write_enabled_attribute(self):
        """Test initialization with project lacking writeEnabled attribute."""
        project = Mock(spec=[])  # No writeEnabled attribute

        # Should succeed - assumes write enabled
        merger = MergeOperations(project)
        self.assertEqual(merger.target_project, project)


class TestMergeOperationsCopyProperties(unittest.TestCase):
    """Test property copying between objects."""

    def test_copy_form_property(self):
        """Test copying Form property (MultiString)."""
        source_obj = Mock()
        target_obj = Mock()
        source_ops = Mock()
        target_ops = Mock()

        # Setup GetForm/SetForm
        source_form = Mock()
        source_ops.GetForm.return_value = source_form
        target_ops.SetForm.return_value = None

        merger = MergeOperations(Mock(writeEnabled=True))
        result = merger.copy_properties(source_obj, target_obj, source_ops, target_ops)

        self.assertTrue(result)
        source_ops.GetForm.assert_called_once_with(source_obj)
        target_ops.SetForm.assert_called_once_with(target_obj, source_form)

    def test_copy_name_property(self):
        """Test copying Name property (string)."""
        source_obj = Mock()
        target_obj = Mock()
        source_ops = Mock()
        target_ops = Mock()

        # Setup GetName/SetName
        source_ops.GetName.return_value = "Test Name"
        source_ops.GetForm = Mock(side_effect=AttributeError)  # No Form
        target_ops.SetName.return_value = None

        merger = MergeOperations(Mock(writeEnabled=True))
        result = merger.copy_properties(source_obj, target_obj, source_ops, target_ops)

        self.assertTrue(result)
        source_ops.GetName.assert_called_once_with(source_obj)
        target_ops.SetName.assert_called_once_with(target_obj, "Test Name")

    def test_copy_no_common_properties(self):
        """Test copying when no common properties exist."""
        source_obj = Mock()
        target_obj = Mock()
        source_ops = Mock()
        target_ops = Mock()

        # All getters raise AttributeError
        source_ops.GetForm = Mock(side_effect=AttributeError)
        source_ops.GetName = Mock(side_effect=AttributeError)
        source_ops.GetDescription = Mock(side_effect=AttributeError)
        source_ops.GetAbbreviation = Mock(side_effect=AttributeError)

        merger = MergeOperations(Mock(writeEnabled=True))
        result = merger.copy_properties(source_obj, target_obj, source_ops, target_ops)

        # Should still return True (no properties = nothing to copy = success)
        self.assertTrue(result)


class TestMergeOperationsCreate(unittest.TestCase):
    """Test object creation."""

    def test_create_simple_object(self):
        """Test creating a simple object without parent."""
        target_project = Mock(writeEnabled=True)
        target_ops = Mock()
        source_obj = Mock()
        source_ops = Mock()

        # Setup mocks
        new_obj = Mock()
        target_ops.Create.return_value = new_obj
        source_ops.GetForm.return_value = "test-form"

        merger = MergeOperations(target_project)

        with patch.object(merger, "copy_properties", return_value=True) as mock_copy:
            result = merger.create_object(target_ops, source_obj, source_ops)

        self.assertEqual(result, new_obj)
        target_ops.Create.assert_called_once()
        mock_copy.assert_called_once_with(source_obj, new_obj, source_ops, target_ops)

    def test_create_with_parent(self):
        """Test creating an object with parent (e.g., Allomorph in LexEntry)."""
        target_project = Mock(writeEnabled=True)
        target_ops = Mock()
        source_obj = Mock()
        source_ops = Mock()
        parent_obj = Mock()

        new_obj = Mock()
        new_obj.Guid = Mock()
        new_obj.Guid.__str__ = Mock(return_value="new-guid-123")
        target_ops.Create.return_value = new_obj

        # Setup GetForm for Allomorph
        source_ops.GetForm = Mock(return_value="test-form")
        source_ops.GetMorphType = Mock(return_value=None)

        merger = MergeOperations(target_project)

        with patch.object(merger, "copy_properties", return_value=True):
            result = merger.create_object(target_ops, source_obj, source_ops, parent_obj=parent_obj)

        self.assertEqual(result, new_obj)
        # Should pass parent and form to Create
        call_args = target_ops.Create.call_args[0]
        self.assertEqual(call_args[0], parent_obj)
        self.assertEqual(call_args[1], "test-form")

    def test_create_fails_raises_error(self):
        """Test create operation that fails raises RuntimeError."""
        target_project = Mock(writeEnabled=True)
        target_ops = Mock()
        source_obj = Mock()
        source_ops = Mock()

        # Create raises exception
        target_ops.Create.side_effect = Exception("Creation failed")
        source_ops.GetForm = Mock(return_value="test-form")

        merger = MergeOperations(target_project)

        with self.assertRaises(RuntimeError) as ctx:
            merger.create_object(target_ops, source_obj, source_ops)

        self.assertIn("creation failed", str(ctx.exception).lower())


class TestMergeOperationsUpdate(unittest.TestCase):
    """Test object updates."""

    def test_update_all_fields(self):
        """Test updating object with all fields."""
        target_project = Mock(writeEnabled=True)
        target_obj = Mock()
        source_obj = Mock()
        source_ops = Mock()
        target_ops = Mock()

        merger = MergeOperations(target_project)

        with patch.object(merger, "copy_properties", return_value=True) as mock_copy:
            result = merger.update_object(target_obj, source_obj, source_ops, target_ops)

        self.assertTrue(result)
        mock_copy.assert_called_once_with(source_obj, target_obj, source_ops, target_ops)

    def test_update_specific_fields(self):
        """Test updating only specific fields."""
        target_project = Mock(writeEnabled=True)
        target_obj = Mock()
        source_obj = Mock()
        source_ops = Mock()
        target_ops = Mock()

        # Setup specific field getters/setters
        source_ops.GetForm.return_value = "updated-form"
        source_ops.GetName.return_value = "updated-name"

        merger = MergeOperations(target_project)
        result = merger.update_object(target_obj, source_obj, source_ops, target_ops, fields=["form", "name"])

        self.assertTrue(result)
        # Should call SetForm and SetName
        target_ops.SetForm.assert_called_once()
        target_ops.SetName.assert_called_once()

    def test_update_fails_returns_false(self):
        """Test update that fails."""
        target_project = Mock(writeEnabled=True)
        target_obj = Mock()
        source_obj = Mock()
        source_ops = Mock()
        target_ops = Mock()

        merger = MergeOperations(target_project)

        with patch.object(merger, "copy_properties", return_value=False):
            result = merger.update_object(target_obj, source_obj, source_ops, target_ops)

        self.assertFalse(result)


class TestMergeOperationsDelete(unittest.TestCase):
    """Test object deletion."""

    def test_delete_without_validation(self):
        """Test deleting object without safety validation."""
        target_project = Mock(writeEnabled=True)
        target_ops = Mock()
        target_obj = Mock()

        target_ops.Delete.return_value = True

        merger = MergeOperations(target_project)
        result = merger.delete_object(target_ops, target_obj, validate_safe=False)

        self.assertTrue(result)
        target_ops.Delete.assert_called_once_with(target_obj)

    def test_delete_with_validation_no_references(self):
        """Test deleting object with validation (no references)."""
        target_project = Mock(writeEnabled=True)
        target_ops = Mock()
        target_obj = Mock()

        # Object has no referring objects
        target_ops.GetReferringObjects = Mock(return_value=[])
        target_ops.Delete.return_value = True

        merger = MergeOperations(target_project)
        result = merger.delete_object(target_ops, target_obj, validate_safe=True)

        self.assertTrue(result)
        target_ops.Delete.assert_called_once_with(target_obj)

    def test_delete_with_validation_has_references(self):
        """Test deleting object with validation.

        Note: Phase 2 validation is stubbed (passes). Will be implemented in Phase 3.
        """
        target_project = Mock(writeEnabled=True)
        target_ops = Mock()
        target_obj = Mock()
        target_obj.Guid = Mock()
        target_obj.Guid.__str__ = Mock(return_value="delete-guid-123")

        # Object has referring objects
        target_ops.GetReferringObjects = Mock(return_value=[Mock(), Mock()])

        merger = MergeOperations(target_project)
        result = merger.delete_object(target_ops, target_obj, validate_safe=True)

        # Phase 2: Validation is stubbed, so delete proceeds
        # Phase 3 will add actual reference checking
        self.assertTrue(result)
        target_ops.Delete.assert_called_once()

    def test_delete_no_validation_method(self):
        """Test deleting when GetReferringObjects doesn't exist."""
        target_project = Mock(writeEnabled=True)
        target_ops = Mock(spec=["Delete"])  # No GetReferringObjects
        target_obj = Mock()

        target_ops.Delete.return_value = True

        merger = MergeOperations(target_project)
        result = merger.delete_object(target_ops, target_obj, validate_safe=True)

        # Should proceed with delete (can't validate, so trust user)
        self.assertTrue(result)
        target_ops.Delete.assert_called_once_with(target_obj)

    def test_delete_fails_raises_error(self):
        """Test delete operation that fails raises RuntimeError."""
        target_project = Mock(writeEnabled=True)
        target_ops = Mock()
        target_obj = Mock()

        target_ops.Delete.side_effect = Exception("Delete failed")

        merger = MergeOperations(target_project)

        with self.assertRaises(RuntimeError) as ctx:
            merger.delete_object(target_ops, target_obj, validate_safe=False)

        self.assertIn("deletion failed", str(ctx.exception).lower())


class TestMergeOperationsIntegration(unittest.TestCase):
    """Integration tests for MergeOperations workflows."""

    def test_full_create_update_workflow(self):
        """Test creating then updating an object."""
        target_project = Mock(writeEnabled=True)
        target_ops = Mock()
        source_ops = Mock()
        source_obj = Mock()

        # Create phase
        new_obj = Mock()
        target_ops.Create.return_value = new_obj
        source_ops.GetForm.return_value = "initial-form"

        merger = MergeOperations(target_project)

        with patch.object(merger, "copy_properties", return_value=True):
            created = merger.create_object(target_ops, source_obj, source_ops)

        self.assertEqual(created, new_obj)

        # Update phase
        source_obj_updated = Mock()
        source_ops.GetForm.return_value = "updated-form"

        with patch.object(merger, "copy_properties", return_value=True):
            updated = merger.update_object(new_obj, source_obj_updated, source_ops, target_ops)

        self.assertTrue(updated)


if __name__ == "__main__":
    unittest.main()
