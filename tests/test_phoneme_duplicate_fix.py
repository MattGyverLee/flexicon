#
# test_phoneme_duplicate_fix.py
#
# Test suite for PhonemeOperations.DuplicatePhoneme fix
# Verifies that deep copy uses SetCloneProperties pattern (FieldWorks standard)
# NOT the broken CopyObject method which doesn't exist in ICmObjectRepository
#
# Platform: Python.NET
#           FieldWorks Version 9+
#
# Copyright 2025
#

import pytest
from unittest.mock import Mock, MagicMock, patch
from pathlib import Path


class TestPhonemeDuplicateFix:
    """Test suite for PhonemeOperations.DuplicatePhoneme fix."""

    def test_service_locator_pattern_in_code(self):
        """
        [INFO] Test: Code uses SetCloneProperties for deep copy (FieldWorks pattern).

        Verifies the code correctly uses SetCloneProperties() to copy objects,
        which is the actual method available in LCM (CopyObject doesn't exist).
        """
        phoneme_ops_file = Path("flexicon/code/Grammar/PhonemeOperations.py")
        content = phoneme_ops_file.read_text(encoding="utf-8")

        # Verify the correct pattern is used
        assert "SetCloneProperties" in content, "Code should use SetCloneProperties for deep copy"

        # Verify ObjectRepository.NewObject is used to create new objects
        assert (
            "ObjectRepository.NewObject" in content
        ), "Code should create new objects with ObjectRepository.NewObject()"

    def test_no_copyobject_method_calls(self):
        """
        [INFO] Test: No broken cache.CopyObject() calls in source code.

        Verify that the broken pattern (cache.CopyObject) is not used,
        since CopyObject doesn't actually exist on ICmObjectRepository.
        """
        from pathlib import Path

        phoneme_ops_file = Path("flexicon/code/Grammar/PhonemeOperations.py")
        content = phoneme_ops_file.read_text(encoding="utf-8")

        # Check that generic bracket syntax is not used
        assert "CopyObject[" not in content, "File still contains CopyObject[T] generic syntax"

        # Check that CloneLcmObject is not used
        assert "CloneLcmObject" not in content, "File still contains CloneLcmObject method call"

        # Check that broken cache.CopyObject pattern is not used
        assert "cache.CopyObject" not in content, "File should not use cache.CopyObject (method doesn't exist)"

        # Verify SetCloneProperties is used instead
        assert "SetCloneProperties" in content, "File should use SetCloneProperties for deep copy"


class TestCopyObjectImportRemoved:
    """Test that CopyObject import has been removed."""

    def test_copy_object_import_removed(self):
        """
        [INFO] Test: CopyObject import is removed from PhonemeOperations.

        The old optional import of CopyObject from SIL.LCModel.DomainServices
        should be removed since we're using ServiceLocator instead.
        """
        from pathlib import Path

        phoneme_ops_file = Path("flexicon/code/Grammar/PhonemeOperations.py")
        content = phoneme_ops_file.read_text(encoding="utf-8")

        # Check that the try/except import is removed
        assert (
            "from SIL.LCModel.DomainServices import CopyObject" not in content
        ), "CopyObject import from DomainServices should be removed"

        # Check that CopyObject = None fallback is removed
        assert "CopyObject = None" not in content, "CopyObject = None fallback should be removed"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
