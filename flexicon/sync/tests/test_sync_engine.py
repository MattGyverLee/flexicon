"""
Unit tests for SyncEngine

Author: FlexTools Development Team
Date: 2025-11-26
"""

import unittest
from unittest.mock import Mock, MagicMock, patch


class MockGuid:
    def __init__(self, guid_string):
        self.value = guid_string

    def __str__(self):
        return self.value


from flexlibs2.sync.engine import SyncEngine, SyncMode, SyncResult
from flexlibs2.sync.match_strategies import GuidMatchStrategy, FieldMatchStrategy
from flexlibs2.sync.conflict_resolvers import SourceWinsResolver
from flexlibs2.sync.merge_ops import SyncChange


class TestSyncEngine(unittest.TestCase):
    """Test SyncEngine class"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mock projects
        self.source_project = Mock()
        self.source_project.ProjectName = Mock(return_value="SourceProject")

        self.target_project = Mock()
        self.target_project.ProjectName = Mock(return_value="TargetProject")

        # Mock operations
        self.mock_ops = Mock()
        self.mock_ops.__class__.__name__ = "AllomorphOperations"
        self.mock_ops.GetAll = Mock(return_value=[])

        self.source_project.Allomorph = self.mock_ops
        self.target_project.Allomorph = self.mock_ops

    def test_init_readonly_mode(self):
        """Test initialization in readonly mode"""
        self.target_project.writeEnabled = False

        engine = SyncEngine(self.source_project, self.target_project)

        self.assertEqual(engine.mode, SyncMode.READONLY)

    def test_init_write_mode(self):
        """Test initialization in write mode"""
        self.target_project.writeEnabled = True

        engine = SyncEngine(self.source_project, self.target_project)

        self.assertEqual(engine.mode, SyncMode.WRITE)

    def test_init_explicit_mode(self):
        """Test explicit mode override"""
        self.target_project.writeEnabled = False

        # Force write mode even though writeEnabled=False
        engine = SyncEngine(self.source_project, self.target_project, mode=SyncMode.WRITE)

        self.assertEqual(engine.mode, SyncMode.WRITE)

    def test_init_no_write_enabled_attribute(self):
        """Test when target has no writeEnabled attribute"""
        # Remove writeEnabled attribute
        if hasattr(self.target_project, "writeEnabled"):
            delattr(self.target_project, "writeEnabled")

        engine = SyncEngine(self.source_project, self.target_project)

        # Should default to readonly for safety
        self.assertEqual(engine.mode, SyncMode.READONLY)

    def test_register_strategy(self):
        """Test registering custom match strategy"""
        engine = SyncEngine(self.source_project, self.target_project)

        custom_strategy = FieldMatchStrategy(key_fields=["test"])
        engine.register_strategy("custom", custom_strategy)

        # Should be in registry
        self.assertIn("custom", engine._match_strategies)
        self.assertEqual(engine._match_strategies["custom"], custom_strategy)

    def test_register_resolver(self):
        """Test registering custom conflict resolver"""
        engine = SyncEngine(self.source_project, self.target_project)

        custom_resolver = SourceWinsResolver()
        engine.register_resolver("custom", custom_resolver)

        # Should be in registry
        self.assertIn("custom", engine._conflict_resolvers)
        self.assertEqual(engine._conflict_resolvers["custom"], custom_resolver)

    def test_get_operations_allomorph(self):
        """Test getting operations for Allomorph"""
        engine = SyncEngine(self.source_project, self.target_project)

        ops = engine._get_operations(self.source_project, "Allomorph")

        self.assertEqual(ops, self.mock_ops)

    def test_get_operations_invalid_type(self):
        """Test getting operations for invalid type"""
        engine = SyncEngine(self.source_project, self.target_project)

        with self.assertRaises(AttributeError) as cm:
            engine._get_operations(self.source_project, "InvalidType")

        self.assertIn("InvalidType", str(cm.exception))

    def test_compare_basic(self):
        """Test basic comparison"""
        self.target_project.writeEnabled = False
        engine = SyncEngine(self.source_project, self.target_project)

        # Add mock object to source
        obj = Mock()
        obj.Guid = MockGuid("abc-123")
        obj.form = "test"

        self.source_project.Allomorph.GetAll = Mock(return_value=[obj])
        self.target_project.Allomorph.GetAll = Mock(return_value=[])

        result = engine.compare(object_type="Allomorph")

        self.assertIsNotNone(result)
        self.assertEqual(result.object_type, "Allomorph")
        self.assertEqual(result.num_new, 1)

    def test_compare_with_guid_strategy(self):
        """Test comparison with explicit GUID strategy"""
        self.target_project.writeEnabled = False
        engine = SyncEngine(self.source_project, self.target_project)

        self.source_project.Allomorph.GetAll = Mock(return_value=[])
        self.target_project.Allomorph.GetAll = Mock(return_value=[])

        result = engine.compare(object_type="Allomorph", match_strategy=GuidMatchStrategy())

        self.assertIsNotNone(result)

    def test_compare_with_registered_strategy_name(self):
        """Test comparison using registered strategy name"""
        self.target_project.writeEnabled = False
        engine = SyncEngine(self.source_project, self.target_project)

        # Register custom strategy
        custom_strategy = FieldMatchStrategy(key_fields=["form"])
        engine.register_strategy("custom", custom_strategy)

        self.source_project.Allomorph.GetAll = Mock(return_value=[])
        self.target_project.Allomorph.GetAll = Mock(return_value=[])

        # Use strategy by name
        result = engine.compare(object_type="Allomorph", match_strategy="custom")

        self.assertIsNotNone(result)

    def test_compare_with_unknown_strategy_name(self):
        """Test comparison with unknown strategy name"""
        self.target_project.writeEnabled = False
        engine = SyncEngine(self.source_project, self.target_project)

        with self.assertRaises(ValueError) as cm:
            engine.compare(object_type="Allomorph", match_strategy="unknown_strategy")

        self.assertIn("Unknown match strategy", str(cm.exception))

    def test_compare_with_filter(self):
        """Test comparison with filter function"""
        self.target_project.writeEnabled = False
        engine = SyncEngine(self.source_project, self.target_project)

        obj1 = Mock()
        obj1.Guid = MockGuid("abc-123")
        obj1.form = "include"

        obj2 = Mock()
        obj2.Guid = MockGuid("def-456")
        obj2.form = "exclude"

        self.source_project.Allomorph.GetAll = Mock(return_value=[obj1, obj2])
        self.target_project.Allomorph.GetAll = Mock(return_value=[])
        self.source_project.Allomorph.GetForm = Mock(side_effect=lambda o: o.form)

        # Filter function
        filter_fn = lambda obj: "include" in obj.form

        result = engine.compare(object_type="Allomorph", filter_fn=filter_fn)

        # Only obj1 should be included
        self.assertEqual(result.num_new, 1)

    def test_compare_with_progress_callback(self):
        """Test comparison with progress callback"""
        self.target_project.writeEnabled = False
        engine = SyncEngine(self.source_project, self.target_project)

        self.source_project.Allomorph.GetAll = Mock(return_value=[])
        self.target_project.Allomorph.GetAll = Mock(return_value=[])

        messages = []

        def callback(msg):
            messages.append(msg)

        result = engine.compare(object_type="Allomorph", progress_callback=callback)

        # Should have received progress messages
        self.assertGreater(len(messages), 0)

    def test_sync_in_readonly_mode_raises_error(self):
        """Test that sync raises error in readonly mode"""
        self.target_project.writeEnabled = False
        engine = SyncEngine(self.source_project, self.target_project)

        with self.assertRaises(RuntimeError) as cm:
            engine.sync(object_type="Allomorph")

        self.assertIn("readonly mode", str(cm.exception))

    def test_sync_phase2_implemented(self):
        """Test that sync is now implemented in Phase 2"""
        self.target_project.writeEnabled = True
        engine = SyncEngine(self.source_project, self.target_project)

        # Setup empty projects
        self.source_project.Allomorph.GetAll = Mock(return_value=[])
        self.target_project.Allomorph.GetAll = Mock(return_value=[])

        # Should not raise NotImplementedError anymore
        result = engine.sync(object_type="Allomorph", dry_run=True)

        self.assertIsInstance(result, SyncResult)
        self.assertTrue(result.success)

    def test_compare_possibility_list_not_implemented(self):
        """Test that possibility list comparison is not yet implemented"""
        engine = SyncEngine(self.source_project, self.target_project)

        with self.assertRaises(NotImplementedError) as cm:
            engine.compare_possibility_list("PartsOfSpeech")

        self.assertIn("Phase 4", str(cm.exception))

    def test_validate_dependencies_not_implemented(self):
        """Test that dependency validation is not yet implemented"""
        engine = SyncEngine(self.source_project, self.target_project)

        with self.assertRaises(NotImplementedError) as cm:
            engine.validate_dependencies("Allomorph")

        self.assertIn("Phase 3", str(cm.exception))

    def test_create_snapshot_not_implemented(self):
        """Test that snapshot creation is not yet implemented"""
        engine = SyncEngine(self.source_project, self.target_project)

        with self.assertRaises(NotImplementedError) as cm:
            engine.create_snapshot(self.target_project)

        self.assertIn("Phase 4", str(cm.exception))


class TestSyncEnginePhase2Execution(unittest.TestCase):
    """Test Phase 2 sync execution functionality"""

    def setUp(self):
        """Set up test fixtures for sync execution"""
        # Create mock projects with write enabled
        self.source_project = Mock()
        self.source_project.ProjectName = Mock(return_value="SourceProject")
        self.source_project.Object = Mock()

        self.target_project = Mock()
        self.target_project.ProjectName = Mock(return_value="TargetProject")
        self.target_project.writeEnabled = True
        self.target_project.Object = Mock()

        # Mock operations
        self.source_ops = Mock()
        self.source_ops.__class__.__name__ = "AllomorphOperations"
        self.source_ops.GetAll = Mock(return_value=[])

        self.target_ops = Mock()
        self.target_ops.__class__.__name__ = "AllomorphOperations"
        self.target_ops.GetAll = Mock(return_value=[])
        self.target_ops.Create = Mock()
        self.target_ops.Delete = Mock()

        self.source_project.Allomorph = self.source_ops
        self.target_project.Allomorph = self.target_ops

    def test_sync_dry_run_no_changes(self):
        """Test dry run sync with no changes"""
        engine = SyncEngine(self.source_project, self.target_project)

        result = engine.sync(object_type="Allomorph", dry_run=True)

        self.assertIsInstance(result, SyncResult)
        self.assertEqual(result.total, 0)
        self.assertTrue(result.success)
        self.assertEqual(result.object_type, "Allomorph")

    @patch("flexlibs2.sync.merge_ops.MergeOperations")
    def test_sync_create_new_objects(self, mock_merger_class):
        """Test sync creates new objects"""
        engine = SyncEngine(self.source_project, self.target_project)

        # Setup source with new object
        source_obj = Mock()
        source_obj.Guid = MockGuid("new-guid-123")
        self.source_ops.GetAll = Mock(return_value=[source_obj])

        # Target is empty
        self.target_ops.GetAll = Mock(return_value=[])

        # Mock merger
        mock_merger = Mock()
        new_obj = Mock()
        mock_merger.create_object = Mock(return_value=new_obj)
        mock_merger_class.return_value = mock_merger

        # Mock Object() calls
        self.source_project.Object = Mock(return_value=source_obj)

        result = engine.sync(object_type="Allomorph", dry_run=False)

        # Should create the new object
        self.assertEqual(result.num_created, 1)
        self.assertEqual(result.total, 1)
        mock_merger.create_object.assert_called_once()

    @patch("flexlibs2.sync.merge_ops.MergeOperations")
    def test_sync_update_modified_objects(self, mock_merger_class):
        """Test sync updates modified objects"""
        engine = SyncEngine(self.source_project, self.target_project)

        # Setup matching objects with different content
        guid = "same-guid-456"
        source_obj = Mock()
        source_obj.Guid = MockGuid(guid)
        source_obj.form = "updated"

        target_obj = Mock()
        target_obj.Guid = MockGuid(guid)
        target_obj.form = "original"

        self.source_ops.GetAll = Mock(return_value=[source_obj])
        self.target_ops.GetAll = Mock(return_value=[target_obj])

        # Mock merger
        mock_merger = Mock()
        mock_merger.update_object = Mock(return_value=True)
        mock_merger_class.return_value = mock_merger

        # Mock Object() calls
        self.source_project.Object = Mock(return_value=source_obj)
        self.target_project.Object = Mock(return_value=target_obj)

        result = engine.sync(object_type="Allomorph", conflict_resolver="source_wins", dry_run=False)

        # Should update the object
        self.assertEqual(result.num_updated, 1)
        mock_merger.update_object.assert_called_once()

    def test_sync_skips_deletes_by_default(self):
        """Test sync skips deletions by default (safety)"""
        engine = SyncEngine(self.source_project, self.target_project)

        # Source is empty
        self.source_ops.GetAll = Mock(return_value=[])

        # Target has object to delete
        target_obj = Mock()
        target_obj.Guid = MockGuid("delete-me-789")
        self.target_ops.GetAll = Mock(return_value=[target_obj])

        result = engine.sync(object_type="Allomorph", dry_run=False)

        # Should skip delete (safety)
        self.assertEqual(result.num_deleted, 0)
        self.assertEqual(result.num_skipped, 1)
        self.target_ops.Delete.assert_not_called()

    @patch("flexlibs2.sync.merge_ops.MergeOperations")
    def test_sync_with_progress_callback(self, mock_merger_class):
        """Test sync calls progress callback"""
        engine = SyncEngine(self.source_project, self.target_project)

        self.source_ops.GetAll = Mock(return_value=[])
        self.target_ops.GetAll = Mock(return_value=[])

        messages = []

        def callback(msg):
            messages.append(msg)

        result = engine.sync(object_type="Allomorph", progress_callback=callback, dry_run=True)

        # Should have received progress messages
        self.assertGreater(len(messages), 0)

    @patch("flexlibs2.sync.merge_ops.MergeOperations")
    def test_sync_dry_run_doesnt_modify(self, mock_merger_class):
        """Test dry run doesn't actually create/update objects"""
        engine = SyncEngine(self.source_project, self.target_project)

        # Setup source with new object
        source_obj = Mock()
        source_obj.Guid = MockGuid("new-guid")
        self.source_ops.GetAll = Mock(return_value=[source_obj])
        self.target_ops.GetAll = Mock(return_value=[])

        # Mock merger
        mock_merger = Mock()
        mock_merger_class.return_value = mock_merger

        result = engine.sync(object_type="Allomorph", dry_run=True)

        # In dry_run mode, changes are skipped rather than executed
        self.assertEqual(result.num_skipped, 1)
        self.assertEqual(result.num_created, 0)

        # Should NOT actually call create_object
        mock_merger.create_object.assert_not_called()

    def test_sync_with_custom_match_strategy(self):
        """Test sync with custom match strategy"""
        engine = SyncEngine(self.source_project, self.target_project)

        # Register custom strategy
        custom_strategy = FieldMatchStrategy(key_fields=["form"])
        engine.register_strategy("custom", custom_strategy)

        self.source_ops.GetAll = Mock(return_value=[])
        self.target_ops.GetAll = Mock(return_value=[])

        result = engine.sync(object_type="Allomorph", match_strategy="custom", dry_run=True)

        self.assertIsInstance(result, SyncResult)

    def test_sync_with_conflict_resolver_string(self):
        """Test sync with conflict resolver by name"""
        engine = SyncEngine(self.source_project, self.target_project)

        self.source_ops.GetAll = Mock(return_value=[])
        self.target_ops.GetAll = Mock(return_value=[])

        # Use built-in resolver by name
        result = engine.sync(object_type="Allomorph", conflict_resolver="source_wins", dry_run=True)

        self.assertIsInstance(result, SyncResult)

    def test_sync_with_conflict_resolver_object(self):
        """Test sync with conflict resolver object"""
        engine = SyncEngine(self.source_project, self.target_project)

        self.source_ops.GetAll = Mock(return_value=[])
        self.target_ops.GetAll = Mock(return_value=[])

        # Use resolver object
        result = engine.sync(object_type="Allomorph", conflict_resolver=SourceWinsResolver(), dry_run=True)

        self.assertIsInstance(result, SyncResult)

    @patch("flexlibs2.sync.merge_ops.MergeOperations")
    def test_sync_handles_create_error(self, mock_merger_class):
        """Test sync handles errors during create"""
        engine = SyncEngine(self.source_project, self.target_project)

        # Setup source with new object
        source_obj = Mock()
        source_obj.Guid = MockGuid("error-guid")
        self.source_ops.GetAll = Mock(return_value=[source_obj])
        self.target_ops.GetAll = Mock(return_value=[])

        # Mock merger that raises exception
        mock_merger = Mock()
        mock_merger.create_object = Mock(side_effect=RuntimeError("Creation failed"))
        mock_merger_class.return_value = mock_merger

        self.source_project.Object = Mock(return_value=source_obj)

        result = engine.sync(object_type="Allomorph", dry_run=False)

        # Should record error
        self.assertEqual(result.num_errors, 1)
        self.assertFalse(result.success)

    @patch("flexlibs2.sync.merge_ops.MergeOperations")
    def test_sync_handles_update_error(self, mock_merger_class):
        """Test sync handles errors during update"""
        engine = SyncEngine(self.source_project, self.target_project)

        # Setup matching objects
        guid = "update-error-guid"
        source_obj = Mock()
        source_obj.Guid = MockGuid(guid)

        target_obj = Mock()
        target_obj.Guid = MockGuid(guid)

        self.source_ops.GetAll = Mock(return_value=[source_obj])
        self.target_ops.GetAll = Mock(return_value=[target_obj])

        # Mock merger that raises exception during update
        mock_merger = Mock()
        mock_merger.update_object = Mock(side_effect=RuntimeError("Update failed"))
        mock_merger_class.return_value = mock_merger

        self.source_project.Object = Mock(return_value=source_obj)
        self.target_project.Object = Mock(return_value=target_obj)

        result = engine.sync(object_type="Allomorph", conflict_resolver="source_wins", dry_run=False)

        # Should record error
        self.assertEqual(result.num_errors, 1)
        self.assertFalse(result.success)


if __name__ == "__main__":
    unittest.main()
