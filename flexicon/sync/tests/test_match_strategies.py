"""
Unit tests for match strategies

Author: FlexTools Development Team
Date: 2025-11-26
"""

import unittest
from unittest.mock import Mock, MagicMock


# Mock System.Guid for testing
class MockGuid:
    def __init__(self, guid_string):
        self.value = guid_string

    def __str__(self):
        return self.value

    def __eq__(self, other):
        return str(self) == str(other)


from flexlibs2.sync.match_strategies import (
    GuidMatchStrategy,
    FieldMatchStrategy,
    HybridMatchStrategy,
)


class TestGuidMatchStrategy(unittest.TestCase):
    """Test GUID-based matching"""

    def setUp(self):
        """Set up test fixtures"""
        self.strategy = GuidMatchStrategy()

        # Create mock objects with GUIDs
        self.source_obj = Mock()
        self.source_obj.Guid = MockGuid("abc-123-def-456")

        self.target_obj1 = Mock()
        self.target_obj1.Guid = MockGuid("abc-123-def-456")  # Matches

        self.target_obj2 = Mock()
        self.target_obj2.Guid = MockGuid("xyz-789-uvw-012")  # No match

        self.target_candidates = [self.target_obj1, self.target_obj2]

    def test_match_found(self):
        """Test matching when GUID exists in target"""
        match = self.strategy.match(
            self.source_obj, self.target_candidates, None, None  # Projects not used in GUID strategy
        )

        self.assertIsNotNone(match)
        self.assertEqual(match, self.target_obj1)

    def test_match_not_found(self):
        """Test when no matching GUID in target"""
        # Remove matching object
        candidates = [self.target_obj2]

        match = self.strategy.match(self.source_obj, candidates, None, None)

        self.assertIsNone(match)

    def test_empty_candidates(self):
        """Test with empty candidate list"""
        match = self.strategy.match(self.source_obj, [], None, None)

        self.assertIsNone(match)

    def test_multiple_candidates_first_match(self):
        """Test that first matching candidate is returned"""
        # Create duplicate GUID
        duplicate = Mock()
        duplicate.Guid = MockGuid("abc-123-def-456")

        candidates = [self.target_obj1, duplicate]

        match = self.strategy.match(self.source_obj, candidates, None, None)

        # Should return first match
        self.assertEqual(match, self.target_obj1)


class TestFieldMatchStrategy(unittest.TestCase):
    """Test field-based matching"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mock operations class
        self.mock_ops = Mock()
        self.mock_ops.GetForm = Mock(side_effect=lambda obj: obj.form)
        self.mock_ops.__class__.__name__ = "AllomorphOperations"

        # Create mock projects
        self.source_project = Mock()
        self.source_project.Allomorph = self.mock_ops

        self.target_project = Mock()
        self.target_project.Allomorph = self.mock_ops

        # Create mock objects
        self.source_obj = Mock()
        self.source_obj.form = "run-ing"
        self.source_obj.ClassName = "MoStemAllomorph"

        self.target_obj1 = Mock()
        self.target_obj1.form = "run-ing"  # Matches
        self.target_obj1.ClassName = "MoStemAllomorph"

        self.target_obj2 = Mock()
        self.target_obj2.form = "walk-ed"  # No match
        self.target_obj2.ClassName = "MoStemAllomorph"

        self.target_candidates = [self.target_obj1, self.target_obj2]

    def test_match_found_single_field(self):
        """Test matching on single field"""
        strategy = FieldMatchStrategy(key_fields=["form"])

        match = strategy.match(self.source_obj, self.target_candidates, self.source_project, self.target_project)

        self.assertIsNotNone(match)
        self.assertEqual(match, self.target_obj1)

    def test_match_not_found(self):
        """Test when no matching field value"""
        strategy = FieldMatchStrategy(key_fields=["form"])

        # Only non-matching candidate
        candidates = [self.target_obj2]

        match = strategy.match(self.source_obj, candidates, self.source_project, self.target_project)

        self.assertIsNone(match)

    def test_case_insensitive_matching(self):
        """Test case-insensitive matching"""
        strategy = FieldMatchStrategy(key_fields=["form"], case_sensitive=False)

        # Create object with different case
        target_different_case = Mock()
        target_different_case.form = "RUN-ING"  # Different case
        target_different_case.ClassName = "MoStemAllomorph"

        match = strategy.match(self.source_obj, [target_different_case], self.source_project, self.target_project)

        self.assertIsNotNone(match)
        self.assertEqual(match, target_different_case)

    def test_case_sensitive_matching(self):
        """Test case-sensitive matching (default)"""
        strategy = FieldMatchStrategy(key_fields=["form"], case_sensitive=True)

        # Create object with different case
        target_different_case = Mock()
        target_different_case.form = "RUN-ING"  # Different case
        target_different_case.ClassName = "MoStemAllomorph"

        match = strategy.match(self.source_obj, [target_different_case], self.source_project, self.target_project)

        # Should NOT match (case-sensitive)
        self.assertIsNone(match)


class TestHybridMatchStrategy(unittest.TestCase):
    """Test hybrid GUID + field matching"""

    def setUp(self):
        """Set up test fixtures"""
        # Create mock operations
        self.mock_ops = Mock()
        self.mock_ops.GetForm = Mock(side_effect=lambda obj: obj.form)
        self.mock_ops.__class__.__name__ = "AllomorphOperations"

        self.source_project = Mock()
        self.source_project.Allomorph = self.mock_ops

        self.target_project = Mock()
        self.target_project.Allomorph = self.mock_ops

        # Create source object
        self.source_obj = Mock()
        self.source_obj.Guid = MockGuid("abc-123")
        self.source_obj.form = "run-ing"
        self.source_obj.ClassName = "MoStemAllomorph"

        # Create target with matching GUID
        self.target_guid_match = Mock()
        self.target_guid_match.Guid = MockGuid("abc-123")
        self.target_guid_match.form = "run-ing"
        self.target_guid_match.ClassName = "MoStemAllomorph"

        # Create target with matching form but different GUID
        self.target_form_match = Mock()
        self.target_form_match.Guid = MockGuid("xyz-789")
        self.target_form_match.form = "run-ing"
        self.target_form_match.ClassName = "MoStemAllomorph"

    def test_guid_match_preferred(self):
        """Test that GUID match is preferred over field match"""
        strategy = HybridMatchStrategy(fallback_fields=["form"])

        # Both GUID and field matches available
        candidates = [self.target_form_match, self.target_guid_match]

        match = strategy.match(self.source_obj, candidates, self.source_project, self.target_project)

        # Should prefer GUID match
        self.assertEqual(match, self.target_guid_match)

    def test_fallback_to_field_match(self):
        """Test fallback to field matching when GUID doesn't match"""
        strategy = HybridMatchStrategy(fallback_fields=["form"])

        # Only field match available (no GUID match)
        candidates = [self.target_form_match]

        match = strategy.match(self.source_obj, candidates, self.source_project, self.target_project)

        # Should fall back to field match
        self.assertEqual(match, self.target_form_match)

    def test_no_match(self):
        """Test when neither GUID nor field matches"""
        strategy = HybridMatchStrategy(fallback_fields=["form"])

        # Create non-matching object
        no_match = Mock()
        no_match.Guid = MockGuid("xyz-789")
        no_match.form = "walk-ed"
        no_match.ClassName = "MoStemAllomorph"

        match = strategy.match(self.source_obj, [no_match], self.source_project, self.target_project)

        self.assertIsNone(match)


if __name__ == "__main__":
    unittest.main()
