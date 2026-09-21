#
#   test_paragraph_sync_props.py
#
#   Regression tests for ParagraphOperations.GetSyncableProperties
#   (issue #351).
#
#   Root cause: the old implementation called
#       item.Contents.get_WritingSystemAt(0)
#   IStTxtPara.Contents is a bare ITsString, which exposes NO
#   get_WritingSystemAt accessor, so every paragraph with content raised
#   AttributeError at runtime. The `Length > 0` guard made it worse: it
#   only ensured the string was non-empty -- exactly when the missing
#   method got called -- so a paragraph with content always raised and an
#   empty paragraph was the only case that survived.
#
#   Fix: read the WS handle off run 0's text props, mirroring
#   SegmentOperations.GetSyncableProperties:
#       item.Contents.get_Properties(0).GetIntPropValues(1, 0)[0]
#   (ktpRunWs == 1, first alternative == 0), then resolve that handle to
#   a WritingSystemDefinition.Id. Also dropped the redundant
#   `ITsString(item.Contents)` cast -- Contents is already an ITsString.
#
#   These tests are pure Python -- no SIL.LCModel / FieldWorks dependency
#   beyond the module import (same shape as test_segment_baseline_text.py).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from flexicon.code.TextsWords.ParagraphOperations import ParagraphOperations


# ---------------------------------------------------------------------------
# Stubs
# ---------------------------------------------------------------------------

def _make_paragraph(ws_handle, text_value, ws_id="en"):
    """
    Build a minimal fake IStTxtPara whose Contents is ITsString-like:

      - contents.get_Properties(0).GetIntPropValues(1, 0) -> (ws_handle, 0)
      - contents.Text -> text_value
      - contents.Length > 0 (a guard that is only true for non-empty text)

    This mirrors the real LCM call chain verified live, same shape as
    the SegmentOperations BaselineText mock.
    """
    contents = MagicMock()
    contents.Text = text_value
    contents.Length = len(text_value)
    contents.get_Properties.return_value.GetIntPropValues.return_value = (ws_handle, 0)

    para = SimpleNamespace(Contents=contents)
    return para, contents


def _make_ops(wsdefs):
    """
    Create a ParagraphOperations instance that does not need a real
    project: bypasses __init__ and wires project.WritingSystems.GetAll()
    to return the supplied WritingSystemDefinition stubs.
    """
    ops = object.__new__(ParagraphOperations)
    ops.project = MagicMock()
    ops.project.WritingSystems.GetAll.return_value = wsdefs
    return ops


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestGetSyncablePropertiesContents:
    """
    Lock the Contents extraction inside GetSyncableProperties against the
    regression in issue #351 (get_WritingSystemAt called on an ITsString,
    which has no such method).
    """

    def setup_method(self):
        self.ws_handle = 999000003
        self.ws_defs = [SimpleNamespace(Handle=self.ws_handle, Id="en")]
        self.ops = _make_ops(self.ws_defs)

    def test_non_empty_paragraph_returns_contents_dict(self):
        """
        The pre-fix bug: any paragraph with content raised AttributeError.
        Post-fix, a non-empty paragraph must return a 'Contents' key with
        the text and writing system resolved to its Id.
        """
        para, _ = _make_paragraph(self.ws_handle, "In the beginning")
        props = self.ops.GetSyncableProperties(para)
        assert props == {"Contents": {"en": "In the beginning"}}

    def test_contents_keyed_by_ws_id_not_handle(self):
        """
        The dict must be keyed by the WritingSystemDefinition.Id (language
        tag), not the integer WS handle -- the ws_dict is populated via
        ws_def.Id.
        """
        para, _ = _make_paragraph(self.ws_handle, "hello")
        props = self.ops.GetSyncableProperties(para)
        assert "en" in props["Contents"]
        assert self.ws_handle not in props["Contents"]

    def test_get_properties_call_shape(self):
        """
        Lock the call shape so a future regression back to
        get_WritingSystemAt(0) would cause a mock assertion error here.
        """
        para, contents = _make_paragraph(self.ws_handle, "test")
        self.ops.GetSyncableProperties(para)

        contents.get_Properties.assert_called_once_with(0)
        contents.get_Properties.return_value.GetIntPropValues.assert_called_once_with(1, 0)

    def test_get_writing_system_at_not_called(self):
        """
        Regression guard: get_WritingSystemAt must NOT be called on the
        ITsString. If it were, the live call would raise AttributeError
        because IStTxtPara.Contents (ITsString) has no such method.
        """
        para, contents = _make_paragraph(self.ws_handle, "hello")
        self.ops.GetSyncableProperties(para)
        assert not contents.get_WritingSystemAt.called, (
            "get_WritingSystemAt was called on ITsString -- regression detected"
        )

    def test_unknown_ws_handle_leaves_empty_contents_dict(self):
        """
        If no WritingSystemDefinition matches the run's WS handle, the
        Contents dict must be empty (not raise).
        """
        ops = _make_ops([SimpleNamespace(Handle=42, Id="en")])
        para, _ = _make_paragraph(self.ws_handle, "hello")
        props = ops.GetSyncableProperties(para)
        assert props == {"Contents": {}}

    def test_empty_text_returns_empty_contents_dict(self):
        """
        An empty paragraph (Contents.Text == '') must not try to read a
        run WS and must return an empty Contents dict.
        """
        para, contents = _make_paragraph(self.ws_handle, "")
        props = self.ops.GetSyncableProperties(para)
        assert props == {"Contents": {}}
        assert not contents.get_Properties.called

    def test_no_contents_attribute_returns_no_contents_key(self):
        """
        A paragraph-shaped object with no Contents attribute must yield a
        props dict with no 'Contents' key at all.
        """
        para = SimpleNamespace()
        props = self.ops.GetSyncableProperties(para)
        assert "Contents" not in props

    def test_none_contents_returns_no_contents_key(self):
        """
        Item.Contents is None (falsy) -> no 'Contents' key, no WS read.
        """
        para = SimpleNamespace(Contents=None)
        props = self.ops.GetSyncableProperties(para)
        assert "Contents" not in props


if __name__ == "__main__":
    pytest.main([__file__, "-v"])