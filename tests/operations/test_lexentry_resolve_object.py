#
#   test_lexentry_resolve_object.py
#
#   Class: TestLexEntryResolveObject
#          Offline regression coverage for issue #269:
#          LexEntryOperations.__ResolveObject never cast its input, so
#          an ICmObject-typed entry from a polymorphic collection blew
#          up on `entry.HeadWord` (defect 1), and the HVO branch's
#          `isinstance(obj, ILexEntry)` guard rejected genuine entries
#          because FLExProject.Object() -> ServiceLocator.GetObject()
#          is declared to return ICmObject (defect 2).
#
#          These tests use plain Python stand-ins, so the real
#          cast_to_concrete's ILexEntry(obj) attempt always fails and
#          it returns the object unchanged (it is total by design).
#          The ClassName dispatch is therefore what is exercised here;
#          the actual downcast is covered by the live test in
#          test_lexentry_resolve_object_live.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import sys
from unittest.mock import Mock, patch

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from tests.operations import mock_flex_project  # noqa: F401


class _FakeLCMObject:
    """Minimal stand-in for an LCM object reached as ICmObject."""

    def __init__(self, class_name, hvo=1):
        self.ClassName = class_name
        self.Hvo = hvo


def _make_ops(project):
    from flexicon.code.Lexicon.LexEntryOperations import LexEntryOperations

    return LexEntryOperations(project)


def _resolve(ops, value):
    # __ResolveObject is name-mangled private.
    return ops._LexEntryOperations__ResolveObject(value)


class TestLexEntryResolveObject:
    """Coverage for both branches of __ResolveObject after #269."""

    def test_entry_object_is_returned(self, mock_flex_project):
        """Non-int branch: an entry object resolves to an entry."""
        ops = _make_ops(mock_flex_project)
        entry = _FakeLCMObject("LexEntry", hvo=101)

        result = _resolve(ops, entry)

        assert result is entry
        assert result.ClassName == "LexEntry"

    def test_entry_object_is_routed_through_cast_to_concrete(
        self, mock_flex_project
    ):
        """
        Defect 1: the non-int branch must not be an identity return.
        Patch cast_to_concrete and prove the object goes through it.
        """
        ops = _make_ops(mock_flex_project)
        entry = _FakeLCMObject("LexEntry", hvo=102)
        cast_entry = _FakeLCMObject("LexEntry", hvo=102)

        with patch(
            "flexicon.code.lcm_casting.cast_to_concrete",
            return_value=cast_entry,
        ) as fake_cast:
            result = _resolve(ops, entry)

        fake_cast.assert_called_once_with(entry)
        assert result is cast_entry

    def test_entry_hvo_is_accepted(self, mock_flex_project):
        """
        Defect 2: an HVO that resolves to a LexEntry must be accepted,
        even though project.Object() hands back an ICmObject-typed view
        that fails isinstance(obj, ILexEntry).
        """
        entry = _FakeLCMObject("LexEntry", hvo=4242)
        mock_flex_project.Object = Mock(return_value=entry)
        ops = _make_ops(mock_flex_project)

        result = _resolve(ops, 4242)

        mock_flex_project.Object.assert_called_once_with(4242)
        assert result is entry

    def test_entry_hvo_is_routed_through_cast_to_concrete(
        self, mock_flex_project
    ):
        """The HVO branch casts too, not only the object branch."""
        entry = _FakeLCMObject("LexEntry", hvo=4243)
        cast_entry = _FakeLCMObject("LexEntry", hvo=4243)
        mock_flex_project.Object = Mock(return_value=entry)
        ops = _make_ops(mock_flex_project)

        with patch(
            "flexicon.code.lcm_casting.cast_to_concrete",
            return_value=cast_entry,
        ) as fake_cast:
            result = _resolve(ops, 4243)

        fake_cast.assert_called_once_with(entry)
        assert result is cast_entry

    def test_sense_hvo_is_rejected(self, mock_flex_project):
        """
        The legitimate rejection survives: ComponentLexemesRS may hold
        an ILexSense, and a sense's HVO is not a lexical entry.
        """
        from flexicon.code.FLExProject import FP_ParameterError

        sense = _FakeLCMObject("LexSense", hvo=777)
        mock_flex_project.Object = Mock(return_value=sense)
        ops = _make_ops(mock_flex_project)

        with pytest.raises(FP_ParameterError) as excinfo:
            _resolve(ops, 777)

        assert "does not refer to a lexical entry" in str(excinfo.value)

    def test_non_entry_hvo_of_unknown_class_is_rejected(
        self, mock_flex_project
    ):
        """A ClassName that is neither LexEntry nor castable is refused."""
        from flexicon.code.FLExProject import FP_ParameterError

        other = _FakeLCMObject("WfiWordform", hvo=888)
        mock_flex_project.Object = Mock(return_value=other)
        ops = _make_ops(mock_flex_project)

        with pytest.raises(FP_ParameterError):
            _resolve(ops, 888)

    def test_unrecognised_classname_object_passes_through_unchanged(
        self, mock_flex_project
    ):
        """
        cast_to_concrete is total: an object whose ClassName is not in
        the registry comes back unchanged rather than raising, so the
        non-int branch cannot regress any call that works today.
        """
        ops = _make_ops(mock_flex_project)
        exotic = _FakeLCMObject("SomeClassNotInTheRegistry", hvo=9)

        result = _resolve(ops, exotic)

        assert result is exotic

    def test_object_without_classname_passes_through_unchanged(
        self, mock_flex_project
    ):
        """An object with no ClassName at all is still returned as-is."""
        ops = _make_ops(mock_flex_project)

        class _NoClassName:
            Hvo = 5

        obj = _NoClassName()

        result = _resolve(ops, obj)

        assert result is obj
