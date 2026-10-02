#
#   test_issue619_reversal_ws_tag.py
#
#   Issue #619: ReversalIndexOperations.Create stored str(writing_system)
#   -- a stringified int handle -- into IReversalIndex.WritingSystem, which
#   holds a language TAG. Create must accept a handle or a tag and always
#   store the canonical tag; FindByWritingSystem must find the index by
#   either form. Offline (mocked) tests; the live counterpart is
#   test_issue619_reversal_ws_tag_live.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from contextlib import nullcontext
from unittest.mock import MagicMock

import pytest

from flexicon.code.FLExProject import FP_ParameterError
from flexicon.code.Reversal import ReversalIndexOperations as rio_module
from flexicon.code.Reversal.ReversalIndexOperations import ReversalIndexOperations


def _ws(handle, tag):
    ws = MagicMock()
    ws.Handle = handle
    ws.tag = tag
    return ws


def _make_ops(existing_indexes=()):
    en = _ws(10, "en")
    fr = _ws(11, "fr-FR")
    vern = _ws(20, "qaa-x-vern")
    project = MagicMock()
    project.writeEnabled = True
    project.WritingSystems.GetAnalysis.return_value = [en, fr]
    project.WritingSystems.GetVernacular.return_value = [vern]
    project.WritingSystems.GetLanguageTag.side_effect = lambda ws: ws.tag
    ops = ReversalIndexOperations(project)
    ops.GetAll = MagicMock(return_value=list(existing_indexes))
    ops._TransactionCM = lambda *a, **k: nullcontext()
    new_index = MagicMock()
    ops._CreateWithGuid = MagicMock(return_value=new_index)
    return ops, project, new_index


@pytest.fixture(autouse=True)
def _patch_tsstring(monkeypatch):
    monkeypatch.setattr(rio_module, "TsStringUtils", MagicMock())


class TestCreateStoresTag:
    @pytest.mark.parametrize(
        "arg, expected",
        [(10, "en"), ("en", "en"), ("EN", "en"), (11, "fr-FR"), ("fr_fr", "fr-FR")],
    )
    def test_create_stores_canonical_tag(self, arg, expected):
        ops, _, new_index = _make_ops()
        ops.Create("Idx", arg)
        assert new_index.WritingSystem == expected
        assert isinstance(new_index.WritingSystem, str)
        assert not str(new_index.WritingSystem).isdigit()

    def test_handle_is_never_stringified_into_index(self):
        ops, _, new_index = _make_ops()
        ops.Create("Idx", 10)
        assert new_index.WritingSystem != "10"

    def test_unknown_tag_rejected_before_mutation(self):
        ops, project, _ = _make_ops()
        with pytest.raises(FP_ParameterError):
            ops.Create("Idx", "zz")
        project.lp.LexDbOA.ReversalIndexesOC.Add.assert_not_called()

    def test_bool_is_not_a_handle(self):
        ops, _, _ = _make_ops()
        with pytest.raises(FP_ParameterError):
            ops.Create("Idx", True)

    def test_duplicate_detected_across_handle_and_tag_forms(self):
        existing = MagicMock()
        existing.WritingSystem = "en"
        ops, project, _ = _make_ops([existing])
        for arg in (10, "en"):
            with pytest.raises(FP_ParameterError):
                ops.Create("Idx", arg)
        project.lp.LexDbOA.ReversalIndexesOC.Add.assert_not_called()


class TestFindByWritingSystem:
    def _idx(self, ws_value):
        idx = MagicMock()
        idx.WritingSystem = ws_value
        return idx

    @pytest.mark.parametrize("arg", [10, "en", "EN"])
    def test_finds_tag_stored_index_by_handle_or_tag(self, arg):
        idx = self._idx("en")
        ops, _, _ = _make_ops([self._idx("fr-FR"), idx])
        assert ops.FindByWritingSystem(arg) is idx

    def test_vernacular_handle_resolves_to_tag(self):
        idx = self._idx("qaa-x-vern")
        ops, _, _ = _make_ops([idx])
        assert ops.FindByWritingSystem(20) is idx

    def test_not_found_returns_none(self):
        ops, _, _ = _make_ops([self._idx("fr-FR")])
        assert ops.FindByWritingSystem(10) is None

    def test_unknown_value_falls_back_to_plain_string_match(self):
        """A legacy index holding a stringified handle can still be located."""
        legacy = self._idx("999000001")
        ops, _, _ = _make_ops([legacy])
        assert ops.FindByWritingSystem(999000001) is legacy
