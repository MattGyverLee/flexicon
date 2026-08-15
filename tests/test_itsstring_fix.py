#
# test_itsstring_fix.py
#
# Test suite for EnvironmentOperations StringRepresentation ITsString fix
# Verifies that ITsString properties are copied correctly, not treated as MultiString
#
# Platform: Python.NET
#           FieldWorks Version 9+
#
# Copyright 2025
#

import pytest
from pathlib import Path


class TestITsStringFix:
    """Test suite for ITsString property copying fix."""

    def test_string_representation_uses_correct_method(self):
        """
        [INFO] Test: StringRepresentation is copied correctly for ITsString.

        Verifies that StringRepresentation uses .Text and TsStringUtils.MakeString()
        instead of the non-existent .CopyAlternatives() method.
        """
        env_ops_file = Path("flexicon/code/Grammar/EnvironmentOperations.py")
        content = env_ops_file.read_text(encoding="utf-8")

        # Check that the old broken method is not used on StringRepresentation
        assert (
            "duplicate.StringRepresentation.CopyAlternatives" not in content
        ), "StringRepresentation should not call .CopyAlternatives()"

        # Check that the correct method is used
        assert "notation = source.StringRepresentation.Text" in content, "Should extract .Text from ITsString"

        assert (
            "TsStringUtils.MakeString(notation, wsHandle)" in content
        ), "Should use TsStringUtils.MakeString to create ITsString"

        assert "duplicate.StringRepresentation = mkstr" in content, "Should assign ITsString directly"

    def test_itsstring_vs_multistring_documented(self):
        """
        [INFO] Test: ITsString vs MultiString properties are properly documented.

        Verifies the code has comments explaining the difference between
        ITsString (single value) and MultiString (multiple alternatives).
        """
        env_ops_file = Path("flexicon/code/Grammar/EnvironmentOperations.py")
        content = env_ops_file.read_text(encoding="utf-8")

        # Check for documentation in DuplicateEnvironment
        assert (
            "ITsString" in content and "MultiString" in content
        ), "Code should document ITsString vs MultiString difference"

    def test_getstring_representation_uses_text_property(self):
        """
        [INFO] Test: GetStringRepresentation correctly uses .Text property.

        Verifies that getting StringRepresentation uses .Text to extract the text.
        """
        env_ops_file = Path("flexicon/code/Grammar/EnvironmentOperations.py")
        content = env_ops_file.read_text(encoding="utf-8")

        # Check GetStringRepresentation implementation
        assert "env.StringRepresentation.Text" in content, "GetStringRepresentation should use .Text property"

    def test_setstring_representation_uses_makestring(self):
        """
        [INFO] Test: SetStringRepresentation correctly uses TsStringUtils.MakeString.

        Verifies that setting StringRepresentation uses TsStringUtils.MakeString().
        """
        env_ops_file = Path("flexicon/code/Grammar/EnvironmentOperations.py")
        content = env_ops_file.read_text(encoding="utf-8")

        # Check SetStringRepresentation implementation
        assert (
            "TsStringUtils.MakeString(notation, wsHandle)" in content
        ), "SetStringRepresentation should use TsStringUtils.MakeString()"

        assert "env.StringRepresentation = mkstr" in content, "Should assign ITsString directly to environment"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
