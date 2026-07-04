"""
Unit tests for Selective Import - Phase 2.5

Tests one-way selective import operations matching linguistic workflows.

Author: FlexTools Development Team
Date: 2025-11-27
"""

import unittest
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime

from flexlibs2.sync.selective_import import SelectiveImport
from flexlibs2.sync.validation import ValidationResult, ValidationIssue, ValidationSeverity
from flexlibs2.sync.engine import SyncResult
from flexlibs2.sync.merge_ops import SyncChange, SyncError


class TestSelectiveImportInitialization(unittest.TestCase):
    """Test SelectiveImport initialization."""

    def test_init_with_write_enabled_project(self):
        """Test initialization with write-enabled target."""
        source = Mock()
        target = Mock()
        target.writeEnabled = True

        importer = SelectiveImport(source, target)

        self.assertEqual(importer.source_project, source)
        self.assertEqual(importer.target_project, target)
        self.assertIsNotNone(importer.validator)
        self.assertIsNotNone(importer.merger)

    def test_init_with_readonly_target_raises_error(self):
        """Test initialization fails with readonly target."""
        source = Mock()
        target = Mock()
        target.writeEnabled = False

        with self.assertRaises(RuntimeError) as ctx:
            SelectiveImport(source, target)

        self.assertIn("writeEnabled=True", str(ctx.exception))

    def test_init_without_writeEnabled_attribute(self):
        """Test initialization with target that has no writeEnabled attribute."""
        source = Mock()
        target = Mock(spec=["Object"])  # No writeEnabled attribute

        # Should succeed - assumes write access
        importer = SelectiveImport(source, target)
        self.assertIsNotNone(importer)


class TestImportNewObjects(unittest.TestCase):
    """Test import_new_objects method."""

    def setUp(self):
        """Set up test fixtures."""
        self.source = Mock()
        self.target = Mock()
        self.target.writeEnabled = True

        # Mock operations classes
        self.source_ops = Mock()
        self.target_ops = Mock()

        self.source.Allomorph = self.source_ops
        self.target.Allomorph = self.target_ops

        self.importer = SelectiveImport(self.source, self.target)

    def test_import_new_objects_by_date_filter(self):
        """Test importing objects created after specific date."""
        # Create mock objects with dates
        old_obj = Mock()
        old_obj.Guid = Mock()
        old_obj.Guid.__str__ = Mock(return_value="old-guid")
        old_obj.DateCreated = datetime(2025, 10, 1)

        new_obj = Mock()
        new_obj.Guid = Mock()
        new_obj.Guid.__str__ = Mock(return_value="new-guid")
        new_obj.DateCreated = datetime(2025, 11, 15)

        self.source_ops.GetAll = Mock(return_value=[old_obj, new_obj])

        # Neither exists in target
        self.target.Object = Mock(return_value=None)

        # Mock merger
        self.importer.merger.create_object = Mock(return_value=Mock())

        # Import only objects after Nov 1
        cutoff_date = datetime(2025, 11, 1)
        result = self.importer.import_new_objects(
            object_type="Allomorph", created_after=cutoff_date, validate_references=False, dry_run=False
        )

        # Should only import new_obj
        self.assertEqual(result.num_created, 1)

    def test_import_never_overwrites_existing(self):
        """Test that import skips objects that already exist in target."""
        # Object that exists in target
        existing_obj = Mock()
        existing_obj.Guid = Mock()
        existing_obj.Guid.__str__ = Mock(return_value="existing-guid")
        existing_obj.DateCreated = datetime(2025, 11, 15)

        # Object that doesn't exist
        new_obj = Mock()
        new_obj.Guid = Mock()
        new_obj.Guid.__str__ = Mock(return_value="new-guid")
        new_obj.DateCreated = datetime(2025, 11, 15)

        self.source_ops.GetAll = Mock(return_value=[existing_obj, new_obj])

        # Mock target.Object to return object for existing_obj, None for new_obj
        def mock_object_lookup(guid):
            if guid == "existing-guid":
                return Mock()  # Exists
            return None  # Doesn't exist

        self.target.Object = Mock(side_effect=mock_object_lookup)

        # Mock merger
        self.importer.merger.create_object = Mock(return_value=Mock())

        result = self.importer.import_new_objects(
            object_type="Allomorph", created_after=datetime(2025, 11, 1), validate_references=False, dry_run=False
        )

        # Should only import new_obj (not existing_obj)
        self.assertEqual(result.num_created, 1)
        self.importer.merger.create_object.assert_called_once()

    def test_import_with_validation_enabled(self):
        """Test import validates references when enabled."""
        obj = Mock()
        obj.Guid = Mock()
        obj.Guid.__str__ = Mock(return_value="test-guid")
        obj.DateCreated = datetime(2025, 11, 15)

        self.source_ops.GetAll = Mock(return_value=[obj])
        self.target.Object = Mock(return_value=None)

        # Mock validation to pass
        mock_validation = ValidationResult()
        self.importer.validator.validate_before_create = Mock(return_value=mock_validation)

        # Mock merger
        self.importer.merger.create_object = Mock(return_value=Mock())

        result = self.importer.import_new_objects(
            object_type="Allomorph", created_after=datetime(2025, 11, 1), validate_references=True, dry_run=False
        )

        # Validation should have been called
        self.importer.validator.validate_before_create.assert_called_once()
        self.assertEqual(result.num_created, 1)

    def test_import_validation_blocks_on_critical(self):
        """Test import is blocked when validation finds critical issues."""
        obj = Mock()
        obj.Guid = Mock()
        obj.Guid.__str__ = Mock(return_value="test-guid")
        obj.DateCreated = datetime(2025, 11, 15)

        self.source_ops.GetAll = Mock(return_value=[obj])
        self.target.Object = Mock(return_value=None)

        # Mock validation to fail with critical issue
        mock_validation = ValidationResult()
        mock_validation.add_issue(
            ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="missing_ref",
                object_type="Allomorph",
                object_guid="test-guid",
                message="Missing POS reference",
            )
        )

        self.importer.validator.validate_before_create = Mock(return_value=mock_validation)

        # Should raise ValidationError (NOT in dry_run mode)
        from flexlibs2.sync.validation import ValidationError

        with self.assertRaises(ValidationError):
            result = self.importer.import_new_objects(
                object_type="Allomorph",
                created_after=datetime(2025, 11, 1),
                validate_references=True,
                dry_run=False,  # Critical: must be False to raise error
            )

    def test_import_validation_errors_in_dry_run(self):
        """Test validation errors are logged but don't raise in dry_run."""
        obj = Mock()
        obj.Guid = Mock()
        obj.Guid.__str__ = Mock(return_value="test-guid")
        obj.DateCreated = datetime(2025, 11, 15)

        self.source_ops.GetAll = Mock(return_value=[obj])
        self.target.Object = Mock(return_value=None)

        # Mock validation to fail
        mock_validation = ValidationResult()
        mock_validation.add_issue(
            ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="missing_ref",
                object_type="Allomorph",
                object_guid="test-guid",
                message="Missing POS reference",
            )
        )

        self.importer.validator.validate_before_create = Mock(return_value=mock_validation)

        # In dry_run mode, should not raise but log errors
        result = self.importer.import_new_objects(
            object_type="Allomorph",
            created_after=datetime(2025, 11, 1),
            validate_references=True,
            dry_run=True,  # Dry run mode
        )

        # Should have errors logged
        self.assertGreater(result.num_errors, 0)

    def test_import_dry_run_does_not_create(self):
        """Test dry_run mode previews without creating objects."""
        obj = Mock()
        obj.Guid = Mock()
        obj.Guid.__str__ = Mock(return_value="test-guid")
        obj.DateCreated = datetime(2025, 11, 15)

        self.source_ops.GetAll = Mock(return_value=[obj])
        self.target.Object = Mock(return_value=None)

        # Mock merger
        self.importer.merger.create_object = Mock(return_value=Mock())

        result = self.importer.import_new_objects(
            object_type="Allomorph", created_after=datetime(2025, 11, 1), validate_references=False, dry_run=True
        )

        # Should not have called create_object
        self.importer.merger.create_object.assert_not_called()

        # Should have skipped 1 object
        self.assertEqual(result.num_skipped, 1)
        self.assertEqual(result.num_created, 0)

    def test_import_with_progress_callback(self):
        """Test progress callback is invoked during import."""
        obj = Mock()
        obj.Guid = Mock()
        obj.Guid.__str__ = Mock(return_value="test-guid")
        obj.DateCreated = datetime(2025, 11, 15)

        self.source_ops.GetAll = Mock(return_value=[obj])
        self.target.Object = Mock(return_value=None)

        # Track progress messages
        progress_messages = []

        def progress_callback(msg):
            progress_messages.append(msg)

        # Mock merger
        self.importer.merger.create_object = Mock(return_value=Mock())

        result = self.importer.import_new_objects(
            object_type="Allomorph",
            created_after=datetime(2025, 11, 1),
            validate_references=False,
            progress_callback=progress_callback,
            dry_run=False,
        )

        # Should have received progress updates
        self.assertGreater(len(progress_messages), 0)
        self.assertTrue(any("Scanning" in msg for msg in progress_messages))

    def test_import_modified_after_filter(self):
        """Test filtering by modification date."""
        # Object modified before cutoff
        old_obj = Mock()
        old_obj.Guid = Mock()
        old_obj.Guid.__str__ = Mock(return_value="old-guid")
        old_obj.DateModified = datetime(2025, 10, 15)

        # Object modified after cutoff
        new_obj = Mock()
        new_obj.Guid = Mock()
        new_obj.Guid.__str__ = Mock(return_value="new-guid")
        new_obj.DateModified = datetime(2025, 11, 15)

        self.source_ops.GetAll = Mock(return_value=[old_obj, new_obj])
        self.target.Object = Mock(return_value=None)

        # Mock merger
        self.importer.merger.create_object = Mock(return_value=Mock())

        result = self.importer.import_new_objects(
            object_type="Allomorph", modified_after=datetime(2025, 11, 1), validate_references=False, dry_run=False
        )

        # Should only import new_obj
        self.assertEqual(result.num_created, 1)

    def test_import_handles_create_failure(self):
        """Test handling of object creation failure."""
        obj = Mock()
        obj.Guid = Mock()
        obj.Guid.__str__ = Mock(return_value="test-guid")
        obj.DateCreated = datetime(2025, 11, 15)

        self.source_ops.GetAll = Mock(return_value=[obj])
        self.target.Object = Mock(return_value=None)

        # Mock merger to return None (creation failed)
        self.importer.merger.create_object = Mock(return_value=None)

        result = self.importer.import_new_objects(
            object_type="Allomorph", created_after=datetime(2025, 11, 1), validate_references=False, dry_run=False
        )

        # Should have error
        self.assertGreater(result.num_errors, 0)
        self.assertEqual(result.num_created, 0)

    def test_import_handles_exception_during_create(self):
        """Test handling of exception during creation."""
        obj = Mock()
        obj.Guid = Mock()
        obj.Guid.__str__ = Mock(return_value="test-guid")
        obj.DateCreated = datetime(2025, 11, 15)

        self.source_ops.GetAll = Mock(return_value=[obj])
        self.target.Object = Mock(return_value=None)

        # Mock merger to raise exception
        self.importer.merger.create_object = Mock(side_effect=Exception("Creation failed"))

        result = self.importer.import_new_objects(
            object_type="Allomorph", created_after=datetime(2025, 11, 1), validate_references=False, dry_run=False
        )

        # Should have logged error
        self.assertGreater(result.num_errors, 0)
        self.assertEqual(result.num_created, 0)


class TestImportByFilter(unittest.TestCase):
    """Test import_by_filter method."""

    def setUp(self):
        """Set up test fixtures."""
        self.source = Mock()
        self.target = Mock()
        self.target.writeEnabled = True

        self.source_ops = Mock()
        self.target_ops = Mock()

        self.source.Allomorph = self.source_ops
        self.target.Allomorph = self.target_ops

        self.importer = SelectiveImport(self.source, self.target)

    def test_import_by_filter_custom_function(self):
        """Test importing with custom filter function."""
        # Create objects with status attribute
        verified_obj = Mock()
        verified_obj.Guid = Mock()
        verified_obj.Guid.__str__ = Mock(return_value="verified-guid")
        verified_obj.Status = "Verified"

        unverified_obj = Mock()
        unverified_obj.Guid = Mock()
        unverified_obj.Guid.__str__ = Mock(return_value="unverified-guid")
        unverified_obj.Status = "Draft"

        self.source_ops.GetAll = Mock(return_value=[verified_obj, unverified_obj])
        self.target.Object = Mock(return_value=None)

        # Mock merger
        self.importer.merger.create_object = Mock(return_value=Mock())

        # Filter function: only verified
        def is_verified(obj):
            return hasattr(obj, "Status") and obj.Status == "Verified"

        result = self.importer.import_by_filter(
            object_type="Allomorph", filter_fn=is_verified, validate_references=False, dry_run=False
        )

        # Should only import verified_obj
        self.assertEqual(result.num_created, 1)

    def test_import_by_filter_skips_existing(self):
        """Test filter respects existing objects in target."""
        # Object that exists in target
        existing_obj = Mock()
        existing_obj.Guid = Mock()
        existing_obj.Guid.__str__ = Mock(return_value="existing-guid")
        existing_obj.Status = "Verified"

        # Object that doesn't exist
        new_obj = Mock()
        new_obj.Guid = Mock()
        new_obj.Guid.__str__ = Mock(return_value="new-guid")
        new_obj.Status = "Verified"

        self.source_ops.GetAll = Mock(return_value=[existing_obj, new_obj])

        # Mock existing object
        def mock_object_lookup(guid):
            if guid == "existing-guid":
                return Mock()
            return None

        self.target.Object = Mock(side_effect=mock_object_lookup)

        # Mock merger
        self.importer.merger.create_object = Mock(return_value=Mock())

        # Filter that matches both
        def is_verified(obj):
            return obj.Status == "Verified"

        result = self.importer.import_by_filter(
            object_type="Allomorph", filter_fn=is_verified, validate_references=False, dry_run=False
        )

        # Should only import new_obj (existing is skipped)
        self.assertEqual(result.num_created, 1)

    def test_import_by_filter_with_validation(self):
        """Test filter import validates references."""
        obj = Mock()
        obj.Guid = Mock()
        obj.Guid.__str__ = Mock(return_value="test-guid")
        obj.Status = "Verified"

        self.source_ops.GetAll = Mock(return_value=[obj])
        self.target.Object = Mock(return_value=None)

        # Mock validation with critical issue
        mock_validation = ValidationResult()
        mock_validation.add_issue(
            ValidationIssue(
                severity=ValidationSeverity.CRITICAL,
                category="test",
                object_type="Allomorph",
                object_guid="test-guid",
                message="Validation failed",
            )
        )

        self.importer.validator.validate_before_create = Mock(return_value=mock_validation)

        def is_verified(obj):
            return obj.Status == "Verified"

        result = self.importer.import_by_filter(
            object_type="Allomorph", filter_fn=is_verified, validate_references=True, dry_run=False
        )

        # Should have error, no objects created
        self.assertGreater(result.num_errors, 0)
        self.assertEqual(result.num_created, 0)

    def test_import_by_filter_handles_filter_exception(self):
        """Test handling of exception in filter function."""
        obj = Mock()
        obj.Guid = Mock()
        obj.Guid.__str__ = Mock(return_value="test-guid")

        self.source_ops.GetAll = Mock(return_value=[obj])
        self.target.Object = Mock(return_value=None)

        # Filter function that raises exception
        def bad_filter(obj):
            raise Exception("Filter error")

        result = self.importer.import_by_filter(
            object_type="Allomorph", filter_fn=bad_filter, validate_references=False, dry_run=False
        )

        # Should handle gracefully - no objects imported
        self.assertEqual(result.num_created, 0)

    def test_import_by_filter_dry_run(self):
        """Test filter import in dry_run mode."""
        obj = Mock()
        obj.Guid = Mock()
        obj.Guid.__str__ = Mock(return_value="test-guid")
        obj.Status = "Verified"

        self.source_ops.GetAll = Mock(return_value=[obj])
        self.target.Object = Mock(return_value=None)

        # Mock merger
        self.importer.merger.create_object = Mock(return_value=Mock())

        def is_verified(obj):
            return obj.Status == "Verified"

        result = self.importer.import_by_filter(
            object_type="Allomorph", filter_fn=is_verified, validate_references=False, dry_run=True
        )

        # Should not create
        self.importer.merger.create_object.assert_not_called()
        self.assertEqual(result.num_skipped, 1)


class TestSelectiveImportHelpers(unittest.TestCase):
    """Test helper methods."""

    def setUp(self):
        """Set up test fixtures."""
        self.source = Mock()
        self.target = Mock()
        self.target.writeEnabled = True
        self.importer = SelectiveImport(self.source, self.target)

    def test_get_operations_success(self):
        """Test getting operations class."""
        self.source.Allomorph = Mock()

        ops = self.importer._get_operations(self.source, "Allomorph")

        self.assertIsNotNone(ops)

    def test_get_operations_missing_raises_error(self):
        """Test error when operations class doesn't exist."""
        # Create source without NonExistentType attribute
        source_no_attr = Mock(spec=[])  # Empty spec - no attributes

        with self.assertRaises(AttributeError) as ctx:
            self.importer._get_operations(source_no_attr, "NonExistentType")

        self.assertIn("NonExistentType", str(ctx.exception))

    def test_exists_in_target_returns_true(self):
        """Test _exists_in_target when object exists."""
        self.target.Object = Mock(return_value=Mock())

        exists = self.importer._exists_in_target("test-guid")

        self.assertTrue(exists)

    def test_exists_in_target_returns_false(self):
        """Test _exists_in_target when object doesn't exist."""
        self.target.Object = Mock(return_value=None)

        exists = self.importer._exists_in_target("test-guid")

        self.assertFalse(exists)

    def test_exists_in_target_handles_exception(self):
        """Test _exists_in_target when lookup raises exception."""
        self.target.Object = Mock(side_effect=Exception("Lookup failed"))

        exists = self.importer._exists_in_target("test-guid")

        self.assertFalse(exists)

    def test_get_project_name_with_attribute(self):
        """Test getting project name when ProjectName method exists."""
        self.source.ProjectName = Mock(return_value="TestProject")

        name = self.importer._get_project_name(self.source)

        self.assertEqual(name, "TestProject")

    def test_get_project_name_without_attribute(self):
        """Test getting project name when ProjectName doesn't exist."""
        # Create project without ProjectName method
        project_no_name = Mock(spec=[])  # Empty spec - no ProjectName

        name = self.importer._get_project_name(project_no_name)

        self.assertEqual(name, "unknown")


class TestLinguisticWorkflowIntegration(unittest.TestCase):
    """Integration tests for complete linguistic workflows."""

    def test_complete_linguist_workflow(self):
        """Test complete workflow: backup → test → import new."""
        source = Mock()
        target = Mock()
        target.writeEnabled = True

        source_ops = Mock()
        target_ops = Mock()

        source.Allomorph = source_ops
        target.Allomorph = target_ops

        # Simulate backup date
        backup_time = datetime(2025, 11, 1, 10, 0, 0)

        # Source has 3 allomorphs:
        # 1. Old (before backup) - should be skipped
        # 2. New (after backup) - should be imported
        # 3. Existing in target (after backup) - should be skipped

        old_allo = Mock()
        old_allo.Guid = Mock()
        old_allo.Guid.__str__ = Mock(return_value="old-guid")
        old_allo.DateCreated = datetime(2025, 10, 15)

        new_allo = Mock()
        new_allo.Guid = Mock()
        new_allo.Guid.__str__ = Mock(return_value="new-guid")
        new_allo.DateCreated = datetime(2025, 11, 15)

        existing_allo = Mock()
        existing_allo.Guid = Mock()
        existing_allo.Guid.__str__ = Mock(return_value="existing-guid")
        existing_allo.DateCreated = datetime(2025, 11, 15)

        source_ops.GetAll = Mock(return_value=[old_allo, new_allo, existing_allo])

        # Mock target.Object
        def mock_object_lookup(guid):
            if guid == "existing-guid":
                return Mock()  # Exists
            return None

        target.Object = Mock(side_effect=mock_object_lookup)

        importer = SelectiveImport(source, target)

        # Mock merger
        importer.merger.create_object = Mock(return_value=Mock())

        # Import new allomorphs
        result = importer.import_new_objects(
            object_type="Allomorph", created_after=backup_time, validate_references=False, dry_run=False
        )

        # Should only import new_allo
        self.assertEqual(result.num_created, 1)
        self.assertEqual(result.num_errors, 0)

    def test_multi_source_consolidation_workflow(self):
        """Test importing from multiple consultant projects."""
        consultant_a = Mock()
        consultant_b = Mock()
        main_project = Mock()
        main_project.writeEnabled = True

        # Setup operations
        a_ops = Mock()
        b_ops = Mock()
        main_ops = Mock()

        consultant_a.LexEntry = a_ops
        consultant_b.LexEntry = b_ops
        main_project.LexEntry = main_ops

        # Consultant A has 2 new entries
        a_entry1 = Mock()
        a_entry1.Guid = Mock()
        a_entry1.Guid.__str__ = Mock(return_value="a-entry1")
        a_entry1.DateCreated = datetime(2025, 11, 10)

        a_entry2 = Mock()
        a_entry2.Guid = Mock()
        a_entry2.Guid.__str__ = Mock(return_value="a-entry2")
        a_entry2.DateCreated = datetime(2025, 11, 11)

        a_ops.GetAll = Mock(return_value=[a_entry1, a_entry2])

        # Consultant B has 1 new entry
        b_entry1 = Mock()
        b_entry1.Guid = Mock()
        b_entry1.Guid.__str__ = Mock(return_value="b-entry1")
        b_entry1.DateCreated = datetime(2025, 11, 12)

        b_ops.GetAll = Mock(return_value=[b_entry1])

        # None exist in main
        main_project.Object = Mock(return_value=None)

        # Import from consultant A
        importer_a = SelectiveImport(consultant_a, main_project)
        importer_a.merger.create_object = Mock(return_value=Mock())

        result_a = importer_a.import_new_objects(
            object_type="LexEntry", created_after=datetime(2025, 11, 1), validate_references=False, dry_run=False
        )

        # Import from consultant B
        importer_b = SelectiveImport(consultant_b, main_project)
        importer_b.merger.create_object = Mock(return_value=Mock())

        result_b = importer_b.import_new_objects(
            object_type="LexEntry", created_after=datetime(2025, 11, 1), validate_references=False, dry_run=False
        )

        # Total imported
        total = result_a.num_created + result_b.num_created
        self.assertEqual(total, 3)


if __name__ == "__main__":
    unittest.main()
