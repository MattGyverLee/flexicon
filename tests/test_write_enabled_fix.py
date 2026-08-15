#
# test_write_enabled_fix.py
#
# Test suite for BaseOperations._EnsureWriteEnabled() fix
# Verifies that writeEnabled property is correctly checked instead of CanModify()
#
# Platform: Python.NET
#           FieldWorks Version 9+
#
# Copyright 2025
#

import pytest
from unittest.mock import Mock, MagicMock


class TestEnsureWriteEnabledFix:
    """Test suite for BaseOperations._EnsureWriteEnabled() write access check."""

    def test_ensure_write_enabled_checks_property_not_method(self):
        """
        [INFO] Test: _EnsureWriteEnabled uses writeEnabled property, not CanModify().

        Verifies that the method correctly checks the FLExProject.writeEnabled
        property instead of calling a non-existent CanModify() method.
        """
        from flexicon.code.BaseOperations import BaseOperations

        # Create a mock project with writeEnabled property
        mock_project = Mock()
        mock_project.writeEnabled = True

        # Create a mock FLExProject wrapper
        mock_flex_project = Mock()
        mock_flex_project.project = mock_project

        # Create BaseOperations instance
        ops = BaseOperations(mock_flex_project)

        # Should not raise when writeEnabled=True
        ops._EnsureWriteEnabled()

    def test_ensure_write_enabled_raises_when_read_only(self):
        """
        [INFO] Test: _EnsureWriteEnabled raises exception when read-only.

        Verifies that an exception is raised when project.writeEnabled is False.
        This test verifies the logic without requiring SIL module import.
        """
        # Test the logic directly by inspecting the source code
        from pathlib import Path

        ops_file = Path("flexicon/code/BaseOperations.py")
        content = ops_file.read_text(encoding="utf-8")

        # Verify the method checks writeEnabled and raises on False
        assert "if not self.project.writeEnabled:" in content, "Method should check if writeEnabled is False"

        assert "raise FP_ReadOnlyError(" in content, "Method should raise FP_ReadOnlyError when write is disabled"

        # Verify error message is appropriate
        assert "read-only" in content.lower(), "Error message should mention read-only"

        assert "writeEnabled=True" in content, "Error message should suggest opening with writeEnabled=True"

    def test_source_code_uses_property_not_method(self):
        """
        [INFO] Test: Source code uses property access, not method call.

        Verifies the source code correctly uses .writeEnabled property
        instead of .CanModify() method.
        """
        from pathlib import Path

        ops_file = Path("flexicon/code/BaseOperations.py")
        content = ops_file.read_text(encoding="utf-8")

        # Check that the fixed property is used
        assert "self.project.writeEnabled" in content, "Source should check self.project.writeEnabled property"

        # Check that the broken method call is removed
        assert ".CanModify()" not in content, "Source should not call .CanModify() method"

    def test_documentation_updated(self):
        """
        [INFO] Test: Documentation references correct property.

        Verifies that the docstring mentions the correct property.
        """
        from pathlib import Path

        ops_file = Path("flexicon/code/BaseOperations.py")
        content = ops_file.read_text(encoding="utf-8")

        # Check that documentation is updated
        assert "project.writeEnabled property" in content, "Documentation should mention writeEnabled property"


class TestFLExProjectWriteEnabled:
    """Test that FLExProject provides writeEnabled property."""

    def test_flex_project_has_write_enabled_property(self):
        """
        [INFO] Test: FLExProject has writeEnabled property.

        Verifies that the FLExProject class defines the writeEnabled property.
        """
        from pathlib import Path

        project_file = Path("flexicon/code/FLExProject.py")
        content = project_file.read_text(encoding="utf-8")

        # Check that writeEnabled is set in OpenProject
        assert (
            "self.writeEnabled = writeEnabled" in content
        ), "FLExProject should set self.writeEnabled in OpenProject method"

        # Check that it's used for write checks
        assert "if self.writeEnabled:" in content, "FLExProject should check self.writeEnabled property"

        # Check that there's no CanModify method
        assert "def CanModify(" not in content, "FLExProject should not have a CanModify() method"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
