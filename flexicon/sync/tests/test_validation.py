"""
Unit tests for Linguistic Validation Framework - Phase 2.5

Tests reference validation, data integrity checks, and linguistic safety.

Author: FlexTools Development Team
Date: 2025-11-27
"""

import unittest
from unittest.mock import Mock, MagicMock
from datetime import datetime

from flexlibs2.sync.validation import (
    LinguisticValidator,
    ValidationResult,
    ValidationIssue,
    ValidationSeverity,
    ValidationError,
)


class TestValidationIssue(unittest.TestCase):
    """Test ValidationIssue data class."""

    def test_create_issue(self):
        """Test creating a validation issue."""
        issue = ValidationIssue(
            severity=ValidationSeverity.CRITICAL,
            category="missing_reference",
            object_type="LexSense",
            object_guid="abc-123",
            message="POS reference missing",
            details={"ref_guid": "def-456"},
        )

        self.assertEqual(issue.severity, ValidationSeverity.CRITICAL)
        self.assertEqual(issue.category, "missing_reference")
        self.assertEqual(issue.object_type, "LexSense")
        self.assertEqual(issue.object_guid, "abc-123")
        self.assertIn("POS reference missing", issue.message)
        self.assertEqual(issue.details["ref_guid"], "def-456")

    def test_issue_string_representation(self):
        """Test issue string formatting."""
        issue = ValidationIssue(
            severity=ValidationSeverity.WARNING,
            category="owned_objects",
            object_type="Allomorph",
            object_guid="test-guid-12345678",
            message="Has phonological environments",
        )

        issue_str = str(issue)
        self.assertIn("WARNING", issue_str)
        self.assertIn("Allomorph", issue_str)
        # GUID is truncated to first 8 characters: "test-gui"
        self.assertIn("test-gui", issue_str)
        self.assertIn("phonological environments", issue_str)


class TestValidationResult(unittest.TestCase):
    """Test ValidationResult class."""

    def test_empty_result(self):
        """Test empty validation result."""
        result = ValidationResult()

        self.assertEqual(len(result.issues), 0)
        self.assertFalse(result.has_critical)
        self.assertFalse(result.has_warnings)
        self.assertEqual(result.num_critical, 0)
        self.assertEqual(result.num_warnings, 0)
        self.assertEqual(result.num_info, 0)

    def test_add_critical_issue(self):
        """Test adding critical issue."""
        result = ValidationResult()

        issue = ValidationIssue(
            severity=ValidationSeverity.CRITICAL,
            category="test",
            object_type="LexEntry",
            object_guid="guid-1",
            message="Critical problem",
        )

        result.add_issue(issue)

        self.assertTrue(result.has_critical)
        self.assertEqual(result.num_critical, 1)
        self.assertEqual(len(result.issues), 1)

    def test_add_multiple_issues(self):
        """Test adding multiple issues of different severities."""
        result = ValidationResult()

        result.add_issue(ValidationIssue(ValidationSeverity.CRITICAL, "cat1", "Type1", "g1", "msg1"))
        result.add_issue(ValidationIssue(ValidationSeverity.CRITICAL, "cat2", "Type2", "g2", "msg2"))
        result.add_issue(ValidationIssue(ValidationSeverity.WARNING, "cat3", "Type3", "g3", "msg3"))
        result.add_issue(ValidationIssue(ValidationSeverity.INFO, "cat4", "Type4", "g4", "msg4"))

        self.assertEqual(result.num_critical, 2)
        self.assertEqual(result.num_warnings, 1)
        self.assertEqual(result.num_info, 1)
        self.assertTrue(result.has_critical)
        self.assertTrue(result.has_warnings)

    def test_summary_with_no_issues(self):
        """Test summary with no issues."""
        result = ValidationResult()
        summary = result.summary()

        self.assertIn("Critical Issues: 0", summary)
        self.assertIn("Warnings: 0", summary)
        self.assertIn("✅", summary)

    def test_summary_with_critical_issues(self):
        """Test summary with critical issues."""
        result = ValidationResult()
        result.add_issue(ValidationIssue(ValidationSeverity.CRITICAL, "test", "Type", "guid", "Problem"))

        summary = result.summary()

        self.assertIn("Critical Issues: 1", summary)
        self.assertIn("❌", summary)

    def test_summary_with_warnings_only(self):
        """Test summary with warnings but no critical."""
        result = ValidationResult()
        result.add_issue(ValidationIssue(ValidationSeverity.WARNING, "test", "Type", "guid", "Warning"))

        summary = result.summary()

        self.assertIn("Warnings: 1", summary)
        self.assertIn("⚠", summary)
        self.assertFalse(result.has_critical)

    def test_detailed_report(self):
        """Test detailed report generation."""
        result = ValidationResult()

        result.add_issue(
            ValidationIssue(
                ValidationSeverity.CRITICAL,
                "missing_ref",
                "LexSense",
                "abc-123",
                "Missing POS",
                {"ref_guid": "def-456"},
            )
        )

        report = result.detailed_report()

        self.assertIn("VALIDATION RESULTS", report)
        self.assertIn("ISSUES:", report)
        self.assertIn("CRITICAL", report)
        self.assertIn("LexSense", report)
        self.assertIn("Missing POS", report)
        self.assertIn("ref_guid", report)


class TestLinguisticValidator(unittest.TestCase):
    """Test LinguisticValidator class."""

    def setUp(self):
        """Set up test fixtures."""
        self.target_project = Mock()
        self.target_project.Object = Mock()
        self.source_project = Mock()

        self.validator = LinguisticValidator(self.target_project)

    def test_validator_initialization(self):
        """Test validator initializes correctly."""
        self.assertEqual(self.validator.target_project, self.target_project)
        self.assertIsInstance(self.validator._cache, dict)

    def test_validate_object_with_no_issues(self):
        """Test validation of object with no issues."""
        # Simple object with no references
        obj = Mock()
        obj.Guid = Mock()
        obj.Guid.__str__ = Mock(return_value="test-guid-123")

        result = self.validator.validate_before_create(
            source_obj=obj, source_project=self.source_project, object_type="SimpleType"
        )

        # Should pass with no critical issues
        self.assertFalse(result.has_critical)

    def test_validate_missing_pos_reference(self):
        """Test validation detects missing POS reference."""
        # Create sense with POS reference
        sense = Mock()
        sense.Guid = Mock()
        sense.Guid.__str__ = Mock(return_value="sense-guid")

        # POS reference that doesn't exist in target
        pos_ref = Mock()
        pos_ref.Guid = Mock()
        pos_ref.Guid.__str__ = Mock(return_value="pos-guid")

        sense.MorphoSyntaxAnalysisRA = pos_ref

        # Make target.Object return None (doesn't exist)
        self.target_project.Object = Mock(return_value=None)

        result = self.validator.validate_before_create(
            source_obj=sense, source_project=self.source_project, object_type="LexSense"
        )

        # Should have critical issue
        self.assertTrue(result.has_critical)
        self.assertGreater(result.num_critical, 0)

        # Check issue details
        critical_issues = [i for i in result.issues if i.severity == ValidationSeverity.CRITICAL]
        self.assertTrue(any("POS" in i.message or "MSA" in i.message for i in critical_issues))

    def test_validate_missing_semantic_domain(self):
        """Test validation detects missing semantic domain."""
        sense = Mock()
        sense.Guid = Mock()
        sense.Guid.__str__ = Mock(return_value="sense-guid")

        # Semantic domain that doesn't exist
        domain = Mock()
        domain.Guid = Mock()
        domain.Guid.__str__ = Mock(return_value="domain-guid")

        sense.SemanticDomainsRC = [domain]

        # Make target.Object return None
        self.target_project.Object = Mock(return_value=None)

        result = self.validator.validate_before_create(
            source_obj=sense, source_project=self.source_project, object_type="LexSense"
        )

        # Should have critical issue
        self.assertTrue(result.has_critical)

        # Check issue mentions semantic domain
        critical_issues = [i for i in result.issues if i.severity == ValidationSeverity.CRITICAL]
        self.assertTrue(any("semantic domain" in i.message.lower() for i in critical_issues))

    def test_validate_missing_morph_type(self):
        """Test validation detects missing morph type."""
        allomorph = Mock()
        allomorph.Guid = Mock()
        allomorph.Guid.__str__ = Mock(return_value="allo-guid")

        # Morph type reference
        morph_type = Mock()
        morph_type.Guid = Mock()
        morph_type.Guid.__str__ = Mock(return_value="type-guid")

        allomorph.MorphTypeRA = morph_type

        # Mock other attributes
        allomorph.Owner = None
        allomorph.PhonologicalEnvironments = []

        # Make target.Object return None
        self.target_project.Object = Mock(return_value=None)

        result = self.validator.validate_before_create(
            source_obj=allomorph, source_project=self.source_project, object_type="Allomorph"
        )

        # Should have critical issue
        self.assertTrue(result.has_critical)

        # Check issue mentions morph type
        critical_issues = [i for i in result.issues if i.severity == ValidationSeverity.CRITICAL]
        self.assertTrue(any("morph type" in i.message.lower() for i in critical_issues))

    def test_validate_warns_about_phonological_environments(self):
        """Test validation warns about phonological environments."""
        allomorph = Mock()
        allomorph.Guid = Mock()
        allomorph.Guid.__str__ = Mock(return_value="allo-guid")

        # Has phonological environments - use actual list
        env1 = Mock()
        env2 = Mock()
        allomorph.PhonologicalEnvironments = [env1, env2]

        # Mock other attributes that might be checked
        allomorph.Owner = None
        allomorph.MorphTypeRA = None

        result = self.validator.validate_before_create(
            source_obj=allomorph, source_project=self.source_project, object_type="Allomorph"
        )

        # Should have warning
        self.assertTrue(result.has_warnings)

        # Check warning mentions environments
        warnings = [i for i in result.issues if i.severity == ValidationSeverity.WARNING]
        self.assertTrue(any("phonological environment" in i.message.lower() for i in warnings))
        self.assertTrue(any("2" in i.message for i in warnings))  # Count = 2

    def test_validate_warns_about_examples(self):
        """Test validation warns about examples that won't be copied."""
        sense = Mock()
        sense.Guid = Mock()
        sense.Guid.__str__ = Mock(return_value="sense-guid")

        # Has examples - use actual list
        ex1 = Mock()
        ex2 = Mock()
        ex3 = Mock()
        sense.ExamplesOS = [ex1, ex2, ex3]

        # Mock other attributes
        sense.MorphoSyntaxAnalysisRA = None
        sense.SemanticDomainsRC = []
        sense.Gloss = Mock()  # Has gloss
        sense.Definition = Mock()  # Has definition

        result = self.validator.validate_before_create(
            source_obj=sense, source_project=self.source_project, object_type="LexSense"
        )

        # Should have warning
        self.assertTrue(result.has_warnings)

        # Check warning mentions examples
        warnings = [i for i in result.issues if i.severity == ValidationSeverity.WARNING]
        self.assertTrue(any("example" in i.message.lower() for i in warnings))

    def test_validate_missing_parent_for_allomorph(self):
        """Test validation detects missing parent entry."""
        allomorph = Mock()
        allomorph.Guid = Mock()
        allomorph.Guid.__str__ = Mock(return_value="allo-guid")

        # Has owner (parent entry)
        owner = Mock()
        owner.Guid = Mock()
        owner.Guid.__str__ = Mock(return_value="owner-guid")
        allomorph.Owner = owner

        # Mock other attributes
        allomorph.MorphTypeRA = None
        allomorph.PhonologicalEnvironments = []

        # Owner doesn't exist in target
        self.target_project.Object = Mock(return_value=None)

        result = self.validator.validate_before_create(
            source_obj=allomorph, source_project=self.source_project, object_type="Allomorph"
        )

        # Should have critical issue
        self.assertTrue(result.has_critical)

        # Check issue mentions parent
        critical_issues = [i for i in result.issues if i.severity == ValidationSeverity.CRITICAL]
        self.assertTrue(any("parent" in i.message.lower() for i in critical_issues))

    def test_validate_sense_without_gloss(self):
        """Test validation gives info about sense without gloss."""
        sense = Mock()
        sense.Guid = Mock()
        sense.Guid.__str__ = Mock(return_value="sense-guid")

        # No gloss or definition
        sense.Gloss = None
        sense.Definition = None

        # Mock other attributes
        sense.MorphoSyntaxAnalysisRA = None
        sense.SemanticDomainsRC = []
        sense.ExamplesOS = []

        result = self.validator.validate_before_create(
            source_obj=sense, source_project=self.source_project, object_type="LexSense"
        )

        # Should have info message
        self.assertGreater(result.num_info, 0)

    def test_validate_entry_without_senses(self):
        """Test validation gives info about entry without senses."""
        entry = Mock()
        entry.Guid = Mock()
        entry.Guid.__str__ = Mock(return_value="entry-guid")

        # Has lexeme form
        entry.LexemeFormOA = Mock()

        # No senses - use actual empty list
        entry.SensesOS = []

        result = self.validator.validate_before_create(
            source_obj=entry, source_project=self.source_project, object_type="LexEntry"
        )

        # Should have info message
        info_issues = [i for i in result.issues if i.severity == ValidationSeverity.INFO]
        self.assertTrue(any("no senses" in i.message.lower() for i in info_issues))

    def test_validation_error_exception(self):
        """Test ValidationError exception."""
        result = ValidationResult()
        result.add_issue(ValidationIssue(ValidationSeverity.CRITICAL, "test", "Type", "guid", "Critical error"))

        error = ValidationError(result)

        self.assertIsInstance(error, Exception)
        self.assertEqual(error.result, result)
        self.assertIn("Critical Issues: 1", str(error))


class TestValidationIntegration(unittest.TestCase):
    """Integration tests for validation workflow."""

    def test_full_validation_workflow(self):
        """Test complete validation workflow."""
        target_project = Mock()
        source_project = Mock()

        # Create sense with multiple issues
        sense = Mock()
        sense.Guid = Mock()
        sense.Guid.__str__ = Mock(return_value="sense-guid-12345")

        # Missing POS
        pos = Mock()
        pos.Guid = Mock()
        pos.Guid.__str__ = Mock(return_value="pos-guid")
        sense.MorphoSyntaxAnalysisRA = pos

        # Missing semantic domain
        domain = Mock()
        domain.Guid = Mock()
        domain.Guid.__str__ = Mock(return_value="domain-guid")
        sense.SemanticDomainsRC = [domain]

        # Has examples (warning) - use actual list
        ex1 = Mock()
        ex2 = Mock()
        sense.ExamplesOS = [ex1, ex2]

        # No gloss (info)
        sense.Gloss = None
        sense.Definition = None

        # Make all lookups fail (objects don't exist in target)
        target_project.Object = Mock(return_value=None)

        validator = LinguisticValidator(target_project)
        result = validator.validate_before_create(
            source_obj=sense, source_project=source_project, object_type="LexSense"
        )

        # Should have issues at all levels
        self.assertTrue(result.has_critical)
        self.assertTrue(result.has_warnings)
        self.assertGreater(result.num_info, 0)

        # Should have at least 2 critical (POS + domain)
        self.assertGreaterEqual(result.num_critical, 2)

        # Summary should block operation
        summary = result.summary()
        self.assertIn("❌", summary)
        self.assertIn("CRITICAL", summary.upper())


if __name__ == "__main__":
    unittest.main()
