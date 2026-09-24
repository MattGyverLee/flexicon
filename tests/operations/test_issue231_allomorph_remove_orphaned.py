#
#   test_issue231_allomorph_remove_orphaned.py
#
#   Mock-based unit tests for AllomorphOperations.RemoveOrphaned
#   (issue #231: duplicate lexeme-form entries and invalid stale alternates).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import contextlib
import os
import sys
from unittest.mock import Mock

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations
from flexicon.code.FLExProject import FP_ReadOnlyError
from SIL.LCModel import ILexEntryRepository


class FakeAllomorph:
    def __init__(self, hvo, class_name="MoStemAllomorph", valid=True):
        self.Hvo = hvo
        self.ClassName = class_name
        self.IsValidObject = valid


class FakeAlternateCollection(list):
    def Remove(self, item):
        self.remove(item)


class FakeEntry:
    def __init__(self, hvo, lexeme=None, alternates=None):
        self.Hvo = hvo
        self.LexemeFormOA = lexeme
        self.AlternateFormsOS = FakeAlternateCollection(alternates or [])


def _make_project(entries, write_enabled=True):
    project = Mock()
    project.writeEnabled = write_enabled

    def _objects_in(repo):
        if repo is ILexEntryRepository:
            return iter(entries)
        return iter([])

    project.ObjectsIn = Mock(side_effect=_objects_in)
    return project


def _make_ops(entries, write_enabled=True):
    project = _make_project(entries, write_enabled=write_enabled)
    ops = AllomorphOperations(project)
    ops._TransactionCM = Mock(return_value=contextlib.nullcontext())
    return ops


class TestAllomorphRemoveOrphanedDuplicates:
    def test_removes_duplicate_lexeme_from_alternates(self):
        lexeme = FakeAllomorph(10)
        duplicate = FakeAllomorph(10)
        other = FakeAllomorph(11)
        entry = FakeEntry(1, lexeme=lexeme, alternates=[duplicate, other])
        ops = _make_ops([entry])

        result = ops.RemoveOrphaned()

        assert result.removed_count == 1
        assert result.kept_count == 1
        assert entry.AlternateFormsOS == [other]
        assert result.removed[0].reason == "duplicate_lexeme"

    def test_keeps_distinct_alternates(self):
        lexeme = FakeAllomorph(10)
        alt = FakeAllomorph(11)
        entry = FakeEntry(1, lexeme=lexeme, alternates=[alt])
        ops = _make_ops([entry])

        result = ops.RemoveOrphaned()

        assert result.removed_count == 0
        assert result.kept_count == 1
        assert entry.AlternateFormsOS == [alt]

    def test_entry_scoped(self):
        lexeme = FakeAllomorph(10)
        dup = FakeAllomorph(10)
        scoped = FakeEntry(1, lexeme=lexeme, alternates=[dup])
        other_entry = FakeEntry(2, lexeme=FakeAllomorph(20), alternates=[])
        ops = _make_ops([scoped, other_entry])

        result = ops.RemoveOrphaned(entry=scoped)

        assert result.removed_count == 1
        assert scoped.AlternateFormsOS == []
        assert other_entry.AlternateFormsOS == []

    def test_read_only_raises(self):
        ops = _make_ops([], write_enabled=False)
        with pytest.raises(FP_ReadOnlyError):
            ops.RemoveOrphaned()

    def test_removes_invalid_stale_alternate(self):
        lexeme = FakeAllomorph(10)
        stale = FakeAllomorph(99, valid=False)
        good = FakeAllomorph(11)
        entry = FakeEntry(1, lexeme=lexeme, alternates=[stale, good])
        ops = _make_ops([entry])

        result = ops.RemoveOrphaned()

        assert result.removed_count == 1
        assert result.kept_count == 1
        assert entry.AlternateFormsOS == [good]
        assert result.removed[0].reason == "invalid_stale"

    def test_removes_invalid_duplicate_lexeme_in_alternates(self):
        lexeme = FakeAllomorph(10)
        stale_dup = FakeAllomorph(10, valid=False)
        entry = FakeEntry(1, lexeme=lexeme, alternates=[stale_dup])
        ops = _make_ops([entry])

        result = ops.RemoveOrphaned()

        assert result.removed_count == 1
        assert result.kept_count == 0
        assert entry.AlternateFormsOS == []
        assert result.removed[0].reason == "invalid_stale"
