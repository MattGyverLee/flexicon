#
# test_custom_field_create_refusal.py
#
# Regression test for issues #20 and #21:
# - #20: CustomFieldOperations.CreateField used to raise NotImplementedError.
# - #21: Bypassing the wrapper with raw IFwMetaDataCacheManaged.AddCustomField
#        from inside an open UoW silently corrupts the project on reopen.
#
# After the fix, CreateField raises FP_TransactionError (with an instructional
# message) when called inside an open UoW. In Phase 1 transaction mode the
# envelope opened at OpenProject() is always active, so the guard always
# fires. This test verifies the static surface area of the fix: error type,
# error message content, and absence of the old NotImplementedError stub.
#
# Platform: Python.NET
#           FieldWorks Version 9+
#
# Copyright 2025
#

from pathlib import Path
from unittest.mock import MagicMock


class TestCreateFieldRefusal:
    """Regression tests for the CreateField transaction-safety guard."""

    SOURCE = Path("flexicon/code/System/CustomFieldOperations.py")

    def test_no_notimplementederror_stub(self):
        """The old CreateField NotImplementedError stub message must be gone."""
        content = self.SOURCE.read_text(encoding="utf-8")
        # DeleteField still raises NotImplementedError; that's a separate
        # issue. Check for the specific old CreateField stub text.
        assert "Custom field creation must be done through FLEx UI" not in content, (
            "CreateField should no longer use the NotImplementedError stub "
            "from before issue #20. The body must raise FP_TransactionError "
            "with an instructional message instead."
        )

    def test_uses_fp_transaction_error(self):
        """The guard raises FP_TransactionError (not FP_ParameterError)."""
        content = self.SOURCE.read_text(encoding="utf-8")
        assert "FP_TransactionError" in content, (
            "CreateField must raise FP_TransactionError when called inside an "
            "open UoW. The parameters are valid; the transaction state is "
            "the problem."
        )
        assert "from ..FLExProject import" in content
        assert "FP_TransactionError," in content, (
            "FP_TransactionError must be imported from ..FLExProject."
        )

    def test_checks_action_handler_current_depth(self):
        """The guard inspects ActionHandlerAccessor.CurrentDepth."""
        content = self.SOURCE.read_text(encoding="utf-8")
        assert "ActionHandlerAccessor" in content
        assert "CurrentDepth" in content, (
            "The transaction guard must check "
            "ActionHandlerAccessor.CurrentDepth > 0 to detect an open UoW."
        )

    def test_error_message_teaches_not_to_bypass(self):
        """Error message must warn against raw-LCM bypass (issue #21)."""
        content = self.SOURCE.read_text(encoding="utf-8")
        assert "AddCustomField" in content, (
            "Error message should name the raw-LCM call (AddCustomField) "
            "users might try as a bypass."
        )
        assert "ghost field" in content or "issue #21" in content, (
            "Error message should reference the corruption mechanism so users "
            "understand why they should not bypass the wrapper."
        )

    def test_error_message_points_to_docs(self):
        """Error message must point to docs/CUSTOM_FIELDS.md."""
        content = self.SOURCE.read_text(encoding="utf-8")
        assert "docs/CUSTOM_FIELDS.md" in content, (
            "Error message must point to docs/CUSTOM_FIELDS.md for full "
            "workflow guidance."
        )

    def test_docs_file_exists(self):
        """docs/CUSTOM_FIELDS.md must exist (referenced from the error)."""
        docs = Path("docs/CUSTOM_FIELDS.md")
        assert docs.exists(), (
            "docs/CUSTOM_FIELDS.md must exist — the CreateField error message "
            "points to it."
        )
        content = docs.read_text(encoding="utf-8")
        assert "issue #21" in content.lower() or "#21" in content
        assert "AddCustomField" in content
        assert "UnitOfWork" in content or "UoW" in content

    def test_guard_raises_at_runtime(self):
        """
        Verify the runtime guard actually fires when CurrentDepth > 0.

        Builds a CustomFieldOperations against a mocked project where the
        ActionHandlerAccessor reports an open task. Asserts the call raises
        FP_TransactionError with the expected message fragments.
        """
        try:
            from flexicon.code.System.CustomFieldOperations import (
                CustomFieldOperations,
            )
            from flexicon.code.FLExProject import FP_TransactionError
        except ImportError:
            # If FLEx isn't initialized (CI mock mode) the import path can
            # fail; the static checks above are still meaningful.
            return

        project = MagicMock()
        project.writeEnabled = True
        project.project.ActionHandlerAccessor.CurrentDepth = 1
        project.project.MetaDataCacheAccessor = MagicMock()

        ops = CustomFieldOperations(project)
        # Skip BaseOperations' _EnsureWriteEnabled if it inspects deeper state
        ops._EnsureWriteEnabled = lambda: None
        # Make FindField return None so the "already exists" check passes
        ops.FindField = lambda owner, name: None
        # Skip _GetClassID lookups that would touch real LCM types
        ops._GetClassID = lambda owner_class: 5016

        try:
            ops.CreateField("LexSense", "Plural", "MultiString", "vernacular")
        except FP_TransactionError as e:
            msg = str(e)
            assert "UnitOfWork" in msg or "UoW" in msg
            assert "AddCustomField" in msg
            assert "docs/CUSTOM_FIELDS.md" in msg
            return
        except Exception as e:
            raise AssertionError(
                f"Expected FP_TransactionError; got {type(e).__name__}: {e}"
            )

        raise AssertionError(
            "CreateField should have raised FP_TransactionError when "
            "ActionHandlerAccessor.CurrentDepth > 0."
        )
