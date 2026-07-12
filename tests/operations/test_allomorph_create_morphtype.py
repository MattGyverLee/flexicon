"""
Test Suite for AllomorphOperations.Create() string morph-type resolution

Regression coverage for issues #213 and #214:

- #213: ``AllomorphOperations.Create(entry, form, morphType)`` crashed with
  ``AttributeError: 'str' object has no attribute 'Guid'`` when morphType
  was passed as a string (the natural input, matching
  ``LexEntryOperations.Create``'s string morph-type names). The fix routes
  string resolution through the same ``find_morph_type`` used by
  LexEntryOperations, and ``__IsStemType`` never sees an un-resolved string.
- #214: Decorated FLEx labels ('=enclitic', 'proclitic=', '-suffix') must
  resolve, and an unknown name must raise a clear FP_ParameterError listing
  the complete canonical name set (no "etc.").

Uses mocks for the FLExProject/LCM layer -- no live FieldWorks project
required.

Author: Programmer Team - Bug fix verification (#213, #214)
"""

import contextlib
import os
import sys
from unittest.mock import Mock, patch

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.Lexicon.AllomorphOperations import AllomorphOperations
from flexicon.code.FLExProject import FP_ParameterError
from SIL.LCModel import MoMorphTypeTags


class _FakeSubPossibilities(list):
    @property
    def Count(self):
        return len(self)


class _FakeMorphType:
    def __init__(self, name, guid):
        self.Name = Mock(BestAnalysisAlternative=Mock(Text=name))
        self.Guid = guid
        self.SubPossibilitiesOS = _FakeSubPossibilities()


def _make_project(morph_types, entry):
    """Build a minimal mock FLExProject sufficient to drive Create()."""
    project = Mock()
    project.writeEnabled = True
    project.lp.LexDbOA.MorphTypesOA.PossibilitiesOS = morph_types
    project.project.DefaultVernWs = 1

    def _resolve_ws(ws, default):
        return default

    project._FLExProject__WSHandle = Mock(side_effect=_resolve_ws)
    return project


def _make_entry(lexeme_form=None):
    entry = Mock()
    entry.LexemeFormOA = lexeme_form
    entry.AlternateFormsOS = Mock(Add=Mock())
    return entry


@pytest.fixture
def ops_and_project():
    suffix = _FakeMorphType("suffix", MoMorphTypeTags.kguidMorphSuffix)
    enclitic = _FakeMorphType("enclitic", MoMorphTypeTags.kguidMorphEnclitic)
    entry = _make_entry(lexeme_form=Mock())  # has a lexeme form -> new form is an alternate
    project = _make_project([suffix, enclitic], entry)
    ops = AllomorphOperations(project)
    # Bypass the real transaction machinery (_NestingAwareTransaction) --
    # not under test here.
    ops._TransactionCM = Mock(return_value=contextlib.nullcontext())
    return ops, project, entry


class TestCreateAcceptsStringMorphType:
    """Issue #213: passing morphType as a string must not raise AttributeError."""

    def test_bare_affix_name_does_not_raise_attributeerror(self, ops_and_project):
        ops, project, entry = ops_and_project
        with patch("flexicon.code.Lexicon.AllomorphOperations.TsStringUtils") as mock_tss:
            mock_tss.MakeString = Mock(return_value=Mock())
            allomorph = ops.Create(entry, "-ing", morphType="suffix")

        assert allomorph.MorphTypeRA.Guid == MoMorphTypeTags.kguidMorphSuffix

    def test_decorated_clitic_label_resolves(self, ops_and_project):
        # issue #214: '=enclitic' must resolve, not just 'enclitic'
        ops, project, entry = ops_and_project
        with patch("flexicon.code.Lexicon.AllomorphOperations.TsStringUtils") as mock_tss:
            mock_tss.MakeString = Mock(return_value=Mock())
            allomorph = ops.Create(entry, "=ki", morphType="=enclitic")

        assert allomorph.MorphTypeRA.Guid == MoMorphTypeTags.kguidMorphEnclitic

    def test_unknown_name_raises_clear_parameter_error(self, ops_and_project):
        ops, project, entry = ops_and_project
        with pytest.raises(FP_ParameterError) as excinfo:
            ops.Create(entry, "bogus-form", morphType="not-a-real-type")

        message = str(excinfo.value)
        assert "etc" not in message.lower()
        assert "enclitic" in message and "proclitic" in message and "clitic" in message


class TestIsStemTypeAcceptsString:
    """Issue #213: the private __IsStemType helper must not blow up on a raw string."""

    def test_string_suffix_is_not_stem(self, ops_and_project):
        ops, project, entry = ops_and_project
        is_stem = ops._AllomorphOperations__IsStemType("suffix")
        assert is_stem is False

    def test_string_enclitic_is_stem(self, ops_and_project):
        ops, project, entry = ops_and_project
        is_stem = ops._AllomorphOperations__IsStemType("=enclitic")
        assert is_stem is True

    def test_unresolvable_string_raises_parameter_error_not_attributeerror(self, ops_and_project):
        ops, project, entry = ops_and_project
        with pytest.raises(FP_ParameterError):
            ops._AllomorphOperations__IsStemType("not-a-real-type")
