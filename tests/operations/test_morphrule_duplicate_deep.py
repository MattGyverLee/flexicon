"""
Test Suite for MorphRuleOperations.Duplicate() 'deep' parameter

Regression coverage for issue #203:

``MorphRuleOperations.Duplicate`` read a local variable ``deep`` that was
not declared as a parameter, so every call that reached the affix-template
slot-copy block raised ``NameError: name 'deep' is not defined`` -- and
``Duplicate(template, deep=True)``, as shown in the method's own docstring,
raised ``TypeError`` because the signature didn't accept the keyword at
all. The fix adds ``deep=True`` to the signature. Per the ticket (#203)
and lead ruling, the default is ``True`` (deep copy), matching the
LexEntry/Text family's Duplicate default; Media/Wordform remain
``deep=False`` by design (a deliberate per-family split, not an
inconsistency).

Uses mocks for the FLExProject/LCM layer -- no live FieldWorks project
required.

Author: Programmer Team - Bug fix verification (#203)
"""

import contextlib
import inspect
import os
import sys
from unittest.mock import Mock

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.Grammar.MorphRuleOperations import MorphRuleOperations


class _FakeAffixTemplatesOS(list):
    """List-like fake for AffixTemplatesOS.

    Real code (MorphRuleOperations.__DuplicateAffixTemplate, post-#537)
    iterates this collection to find the source's index by HVO, then
    calls Insert/Add on it. A bare Mock() supports the calls but is not
    iterable, so `list(owner.AffixTemplatesOS)` raised
    "TypeError: 'Mock' object is not iterable". Subclassing list keeps
    iteration/indexing/len() working while still recording Insert/Add
    calls as Mocks so existing assertions on call_count/args keep working.
    """

    def __init__(self, *args):
        super().__init__(*args)
        self.IndexOf = Mock(side_effect=lambda item: self.index(item))
        self.Insert = Mock(side_effect=lambda idx, item: list.insert(self, idx, item))
        self.Add = Mock(side_effect=lambda item: list.append(self, item))


def _make_affix_template_fixture():
    """Build a mock project + source MoInflAffixTemplate + owner + duplicate."""
    project = Mock()
    project.writeEnabled = True

    source = Mock()
    source.ClassName = "MoInflAffixTemplate"
    source.Hvo = 1001
    source.StratumRA = None
    source.PrefixSlotsRS = [Mock(name="slot1"), Mock(name="slot2")]
    source.SuffixSlotsRS = []
    source.ProcliticSlotsRS = []
    source.EncliticSlotsRS = []

    owner = Mock()
    owner.ClassName = "PartOfSpeech"
    # source.Owner is what __DuplicateAffixTemplate actually resolves
    # through _GetTypedOwner (via source.Owner -> cast_to_concrete);
    # project.Object is not consulted on this path since source is
    # already a live object, not an HVO. Keep the two in sync so a
    # future refactor that switches resolution strategy doesn't silently
    # start reading a stale double.
    source.Owner = owner
    owner.AffixTemplatesOS = _FakeAffixTemplatesOS([source])
    project.Object = Mock(return_value=owner)

    duplicate = Mock()
    duplicate.Name = Mock(CopyAlternatives=Mock())
    duplicate.Description = Mock(CopyAlternatives=Mock())
    duplicate.PrefixSlotsRS = Mock(Add=Mock())
    duplicate.SuffixSlotsRS = Mock(Add=Mock())
    duplicate.ProcliticSlotsRS = Mock(Add=Mock())
    duplicate.EncliticSlotsRS = Mock(Add=Mock())

    factory = Mock(Create=Mock(return_value=duplicate))
    project.project.ServiceLocator.GetService = Mock(return_value=factory)

    ops = MorphRuleOperations(project)
    # Bypass the real transaction machinery -- not under test here.
    ops._TransactionCM = Mock(return_value=contextlib.nullcontext())

    return ops, source, duplicate, owner


class TestDuplicateSignature:
    def test_duplicate_declares_deep_parameter(self):
        # Duplicate is wrapped by the OperationsMethod descriptor; pull the
        # raw function out of the class __dict__ (bypassing __get__, which
        # returns a (project, *args, **kwargs) shim at class level).
        descriptor = MorphRuleOperations.__dict__["Duplicate"]
        func = descriptor.func
        while hasattr(func, "func"):
            func = func.func
        sig = inspect.signature(func)
        assert "deep" in sig.parameters
        assert sig.parameters["deep"].default is True


class TestDuplicateDeepGating:
    def test_default_call_does_not_raise_nameerror(self):
        """Issue #203: calling Duplicate() at all used to raise NameError."""
        ops, source, duplicate, owner = _make_affix_template_fixture()

        result = ops.Duplicate(source)  # no deep kwarg -- must not NameError

        assert result is duplicate
        # deep=True is now the default, so slot references ARE copied.
        assert duplicate.PrefixSlotsRS.Add.call_count == 2

    def test_deep_false_does_not_copy_slot_references(self):
        ops, source, duplicate, owner = _make_affix_template_fixture()

        ops.Duplicate(source, deep=False)

        duplicate.PrefixSlotsRS.Add.assert_not_called()
        duplicate.SuffixSlotsRS.Add.assert_not_called()

    def test_deep_true_copies_slot_references(self):
        """Docstring-documented usage: Duplicate(template, deep=True)."""
        ops, source, duplicate, owner = _make_affix_template_fixture()

        ops.Duplicate(source, deep=True)

        assert duplicate.PrefixSlotsRS.Add.call_count == 2
        for slot in source.PrefixSlotsRS:
            duplicate.PrefixSlotsRS.Add.assert_any_call(slot)
        duplicate.SuffixSlotsRS.Add.assert_not_called()
        duplicate.ProcliticSlotsRS.Add.assert_not_called()
        duplicate.EncliticSlotsRS.Add.assert_not_called()

    def test_deep_true_keyword_matches_docstring_example(self):
        # Reproduces the exact call shown in the docstring's Example section.
        ops, source, duplicate, owner = _make_affix_template_fixture()
        copy = ops.Duplicate(source, deep=True)
        assert copy is duplicate

    def test_insert_after_inserts_at_source_index_plus_one(self):
        """Issue #556: with insert_after=True (default), the duplicate must
        land immediately after the source in owner.AffixTemplatesOS. The
        fixture seeds AffixTemplatesOS with [source] at index 0, so the
        expected Insert call is (1, duplicate)."""
        ops, source, duplicate, owner = _make_affix_template_fixture()

        ops.Duplicate(source, insert_after=True)

        owner.AffixTemplatesOS.Insert.assert_called_once_with(1, duplicate)
        owner.AffixTemplatesOS.Add.assert_not_called()
