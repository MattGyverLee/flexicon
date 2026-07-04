"""
Linguistic Validation Framework

Validates linguistic data integrity before sync operations.
Prevents orphaned references, broken hierarchies, and data corruption.

Author: FlexTools Development Team
Date: 2025-11-27
"""

import logging
from typing import Any, List, Dict, Optional, Set
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger(__name__)


class ValidationSeverity(Enum):
    """Severity levels for validation issues."""

    CRITICAL = "critical"  # Blocks operation
    WARNING = "warning"  # User should review
    INFO = "info"  # Informational only


@dataclass
class ValidationIssue:
    """
    A single validation issue found during pre-sync checks.

    Attributes:
        severity: How serious the issue is
        category: Type of issue (reference, hierarchy, etc.)
        object_type: Type of object with issue
        object_guid: GUID of problematic object
        message: Human-readable description
        details: Additional context
    """

    severity: ValidationSeverity
    category: str
    object_type: str
    object_guid: str
    message: str
    details: Dict[str, Any] = field(default_factory=dict)

    def __str__(self):
        return f"[{self.severity.value.upper()}] {self.object_type} {self.object_guid[:8]}: {self.message}"


@dataclass
class ValidationResult:
    """
    Results from validation checks.

    Tracks all issues found and provides summary.
    """

    issues: List[ValidationIssue] = field(default_factory=list)

    @property
    def has_critical(self) -> bool:
        """Check if any critical issues found."""
        return any(issue.severity == ValidationSeverity.CRITICAL for issue in self.issues)

    @property
    def has_warnings(self) -> bool:
        """Check if any warnings found."""
        return any(issue.severity == ValidationSeverity.WARNING for issue in self.issues)

    @property
    def num_critical(self) -> int:
        """Count critical issues."""
        return sum(1 for issue in self.issues if issue.severity == ValidationSeverity.CRITICAL)

    @property
    def num_warnings(self) -> int:
        """Count warnings."""
        return sum(1 for issue in self.issues if issue.severity == ValidationSeverity.WARNING)

    @property
    def num_info(self) -> int:
        """Count info messages."""
        return sum(1 for issue in self.issues if issue.severity == ValidationSeverity.INFO)

    def add_issue(self, issue: ValidationIssue):
        """Add a validation issue."""
        self.issues.append(issue)
        logger.debug(f"Validation issue: {issue}")

    def summary(self) -> str:
        """Generate summary report."""
        lines = [
            "VALIDATION RESULTS",
            "-" * 40,
            f"Critical Issues: {self.num_critical}",
            f"Warnings: {self.num_warnings}",
            f"Info: {self.num_info}",
            f"Total: {len(self.issues)}",
            "",
        ]

        if self.has_critical:
            lines.append("❌ CRITICAL ISSUES - OPERATION BLOCKED")
        elif self.has_warnings:
            lines.append("⚠️  WARNINGS - REVIEW RECOMMENDED")
        else:
            lines.append("✅ VALIDATION PASSED")

        return "\n".join(lines)

    def detailed_report(self) -> str:
        """Generate detailed report with all issues."""
        lines = [self.summary(), "", "ISSUES:", "-" * 40]

        for issue in sorted(self.issues, key=lambda i: (i.severity.value, i.category)):
            lines.append(str(issue))
            if issue.details:
                for key, value in issue.details.items():
                    lines.append(f"  {key}: {value}")

        return "\n".join(lines)


class LinguisticValidator:
    """
    Validates linguistic data integrity before sync operations.

    Checks for:
    - Missing reference targets (POS, semantic domains, etc.)
    - Orphaned owned objects (phonological environments, etc.)
    - Broken hierarchical relationships
    - Invalid linguistic constraints

    Usage:
        >>> validator = LinguisticValidator(target_project)
        >>> result = validator.validate_before_create(source_obj, source_project)
        >>> if result.has_critical:
        ...     raise ValidationError(result.summary())
    """

    def __init__(self, target_project: Any):
        """
        Initialize validator.

        Args:
            target_project: Target FLEx project to validate against
        """
        self.target_project = target_project
        self._cache: Dict[str, Set[str]] = {}

    def validate_before_create(self, source_obj: Any, source_project: Any, object_type: str) -> ValidationResult:
        """
        Validate object before creating in target.

        Args:
            source_obj: Object to be created
            source_project: Source project
            object_type: Type of object

        Returns:
            ValidationResult with any issues found
        """
        result = ValidationResult()

        try:
            # Get object GUID for reporting
            guid = str(source_obj.Guid) if hasattr(source_obj, "Guid") else "unknown"

            # Check references
            self._validate_references(source_obj, object_type, guid, result)

            # Check owned objects
            self._check_owned_objects(source_obj, object_type, guid, result)

            # Check hierarchical relationships
            self._validate_hierarchy(source_obj, source_project, object_type, guid, result)

            # Type-specific validation
            if object_type == "LexSense":
                self._validate_sense(source_obj, guid, result)
            elif object_type == "Allomorph" or object_type == "MoForm":
                self._validate_allomorph(source_obj, guid, result)
            elif object_type == "LexEntry":
                self._validate_entry(source_obj, guid, result)

        except Exception as e:
            logger.error(f"Validation error: {e}")
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="validation_error",
                    object_type=object_type,
                    object_guid=guid,
                    message=f"Validation failed: {e}",
                )
            )

        return result

    def _validate_references(self, obj: Any, object_type: str, guid: str, result: ValidationResult):
        """Check if referenced objects exist in target."""

        # Check MorphoSyntaxAnalysis (POS) reference
        if hasattr(obj, "MorphoSyntaxAnalysisRA"):
            msa = obj.MorphoSyntaxAnalysisRA
            if msa is not None and not self._exists_in_target(msa):
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        category="missing_reference",
                        object_type=object_type,
                        object_guid=guid,
                        message="Referenced POS/MSA does not exist in target project",
                        details={"reference_guid": str(msa.Guid)},
                    )
                )

        # Check SemanticDomains
        if hasattr(obj, "SemanticDomainsRC"):
            domains = obj.SemanticDomainsRC
            if domains:
                for domain in domains:
                    if not self._exists_in_target(domain):
                        result.add_issue(
                            ValidationIssue(
                                severity=ValidationSeverity.CRITICAL,
                                category="missing_reference",
                                object_type=object_type,
                                object_guid=guid,
                                message=f"Semantic domain not found in target",
                                details={"domain_guid": str(domain.Guid)},
                            )
                        )

        # Check MorphType reference
        if hasattr(obj, "MorphTypeRA"):
            morph_type = obj.MorphTypeRA
            if morph_type is not None and not self._exists_in_target(morph_type):
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.CRITICAL,
                        category="missing_reference",
                        object_type=object_type,
                        object_guid=guid,
                        message="Morph type does not exist in target project",
                        details={"morph_type_guid": str(morph_type.Guid)},
                    )
                )

    def _check_owned_objects(self, obj: Any, object_type: str, guid: str, result: ValidationResult):
        """Warn about owned objects that won't be copied."""

        # Check PhonologicalEnvironments
        if hasattr(obj, "PhonologicalEnvironments"):
            envs = obj.PhonologicalEnvironments
            if envs and len(envs) > 0:
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="owned_objects",
                        object_type=object_type,
                        object_guid=guid,
                        message=f"Object has {len(envs)} phonological environment(s) that will NOT be copied",
                        details={"num_environments": len(envs)},
                    )
                )

        # Check Examples
        if hasattr(obj, "ExamplesOS"):
            examples = obj.ExamplesOS
            if examples and len(examples) > 0:
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="owned_objects",
                        object_type=object_type,
                        object_guid=guid,
                        message=f"Sense has {len(examples)} example(s) that will NOT be copied",
                        details={"num_examples": len(examples)},
                    )
                )

        # Check Subsenses
        if hasattr(obj, "SensesOS"):
            subsenses = obj.SensesOS
            if subsenses and len(subsenses) > 0:
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="owned_objects",
                        object_type=object_type,
                        object_guid=guid,
                        message=f"Sense has {len(subsenses)} subsense(s) that will NOT be copied",
                        details={"num_subsenses": len(subsenses)},
                    )
                )

    def _validate_hierarchy(self, obj: Any, source_project: Any, object_type: str, guid: str, result: ValidationResult):
        """Validate hierarchical relationships."""

        # Check if object requires parent
        if object_type in ["Allomorph", "MoForm"]:
            # Allomorphs must belong to an entry
            if hasattr(obj, "Owner"):
                owner = obj.Owner
                if owner is not None:
                    owner_guid = str(owner.Guid)
                    if not self._exists_in_target_by_guid(owner_guid):
                        result.add_issue(
                            ValidationIssue(
                                severity=ValidationSeverity.CRITICAL,
                                category="missing_parent",
                                object_type=object_type,
                                object_guid=guid,
                                message="Parent entry does not exist in target project",
                                details={"parent_guid": owner_guid},
                            )
                        )

        elif object_type == "LexSense":
            # Senses must belong to entry or parent sense
            if hasattr(obj, "Owner"):
                owner = obj.Owner
                if owner is not None:
                    owner_guid = str(owner.Guid)
                    if not self._exists_in_target_by_guid(owner_guid):
                        result.add_issue(
                            ValidationIssue(
                                severity=ValidationSeverity.CRITICAL,
                                category="missing_parent",
                                object_type=object_type,
                                object_guid=guid,
                                message="Parent entry/sense does not exist in target project",
                                details={"parent_guid": owner_guid},
                            )
                        )

    def _validate_sense(self, obj: Any, guid: str, result: ValidationResult):
        """Sense-specific validation."""

        # Check if sense has gloss or definition
        has_content = False

        if hasattr(obj, "Gloss"):
            gloss = obj.Gloss
            if gloss and hasattr(gloss, "AnalysisDefaultWritingSystem"):
                if gloss.AnalysisDefaultWritingSystem:
                    has_content = True

        if not has_content and hasattr(obj, "Definition"):
            definition = obj.Definition
            if definition and hasattr(definition, "AnalysisDefaultWritingSystem"):
                if definition.AnalysisDefaultWritingSystem:
                    has_content = True

        if not has_content:
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="data_quality",
                    object_type="LexSense",
                    object_guid=guid,
                    message="Sense has no gloss or definition",
                )
            )

    def _validate_allomorph(self, obj: Any, guid: str, result: ValidationResult):
        """Allomorph-specific validation."""

        # Check if allomorph has form
        if hasattr(obj, "Form"):
            form = obj.Form
            if not form or not hasattr(form, "VernacularDefaultWritingSystem"):
                result.add_issue(
                    ValidationIssue(
                        severity=ValidationSeverity.WARNING,
                        category="data_quality",
                        object_type="Allomorph",
                        object_guid=guid,
                        message="Allomorph has no vernacular form",
                    )
                )

    def _validate_entry(self, obj: Any, guid: str, result: ValidationResult):
        """Entry-specific validation."""

        # Check if entry has lexeme form
        has_lexeme = False
        if hasattr(obj, "LexemeFormOA"):
            if obj.LexemeFormOA is not None:
                has_lexeme = True

        if not has_lexeme:
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.WARNING,
                    category="data_quality",
                    object_type="LexEntry",
                    object_guid=guid,
                    message="Entry has no lexeme form",
                )
            )

        # Check if entry has at least one sense
        has_senses = False
        if hasattr(obj, "SensesOS"):
            if obj.SensesOS and len(obj.SensesOS) > 0:
                has_senses = True

        if not has_senses:
            result.add_issue(
                ValidationIssue(
                    severity=ValidationSeverity.INFO,
                    category="data_quality",
                    object_type="LexEntry",
                    object_guid=guid,
                    message="Entry has no senses",
                )
            )

    def _exists_in_target(self, obj: Any) -> bool:
        """Check if object exists in target project."""
        if obj is None:
            return False

        try:
            guid = str(obj.Guid)
            return self._exists_in_target_by_guid(guid)
        except (AttributeError, KeyError):
            return False

    def _exists_in_target_by_guid(self, guid: str) -> bool:
        """Check if object with GUID exists in target."""
        try:
            target_obj = self.target_project.Object(guid)
            return target_obj is not None
        except (AttributeError, KeyError):
            return False


class ValidationError(Exception):
    """Raised when validation fails with critical issues."""

    def __init__(self, validation_result: ValidationResult):
        self.result = validation_result
        super().__init__(validation_result.summary())
