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


def _make_affix_template_fixture():
    """Build a mock project + source MoInflAffixTemplate + owner + duplicate."""
    project = Mock()
    project.writeEnabled = True

    owner = Mock()
    owner.AffixTemplatesOS = Mock()
    owner.AffixTemplatesOS.IndexOf = Mock(return_value=0)
    owner.AffixTemplatesOS.Insert = Mock()
    owner.AffixTemplatesOS.Add = Mock()

    source = Mock()
    source.ClassName = "MoInflAffixTemplate"
    source.Owner = Mock(Hvo=555)
    source.StratumRA = None
    source.PrefixSlotsRS = [Mock(name="slot1"), Mock(name="slot2")]
    source.SuffixSlotsRS = []
    source.ProcliticSlotsRS = []
    source.EncliticSlotsRS = []

    duplicate = Mock()
    duplicate.Name = Mock(CopyAlternatives=Mock())
    duplicate.Description = Mock(CopyAlternatives=Mock())
    duplicate.PrefixSlotsRS = Mock(Add=Mock())
    duplicate.SuffixSlotsRS = Mock(Add=Mock())
    duplicate.ProcliticSlotsRS = Mock(Add=Mock())
    duplicate.EncliticSlotsRS = Mock(Add=Mock())

    factory = Mock(Create=Mock(return_value=duplicate))
    project.project.ServiceLocator.GetService = Mock(return_value=factory)
    project.Object = Mock(return_value=owner)

    ops = MorphRuleOperations(project)
    # Bypass the real transaction machinery -- not under test here.
    ops._TransactionCM = Mock(return_value=contextlib.nullcontext())

    return ops, source, duplicate


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
        ops, source, duplicate = _make_affix_template_fixture()

        result = ops.Duplicate(source)  # no deep kwarg -- must not NameError

        assert result is duplicate
        # deep=True is now the default, so slot references ARE copied.
        assert duplicate.PrefixSlotsRS.Add.call_count == 2

    def test_deep_false_does_not_copy_slot_references(self):
        ops, source, duplicate = _make_affix_template_fixture()

        ops.Duplicate(source, deep=False)

        duplicate.PrefixSlotsRS.Add.assert_not_called()
        duplicate.SuffixSlotsRS.Add.assert_not_called()

    def test_deep_true_copies_slot_references(self):
        """Docstring-documented usage: Duplicate(template, deep=True)."""
        ops, source, duplicate = _make_affix_template_fixture()

        ops.Duplicate(source, deep=True)

        assert duplicate.PrefixSlotsRS.Add.call_count == 2
        for slot in source.PrefixSlotsRS:
            duplicate.PrefixSlotsRS.Add.assert_any_call(slot)
        duplicate.SuffixSlotsRS.Add.assert_not_called()
        duplicate.ProcliticSlotsRS.Add.assert_not_called()
        duplicate.EncliticSlotsRS.Add.assert_not_called()

    def test_deep_true_keyword_matches_docstring_example(self):
        # Reproduces the exact call shown in the docstring's Example section.
        ops, source, duplicate = _make_affix_template_fixture()
        copy = ops.Duplicate(source, deep=True)
        assert copy is duplicate
