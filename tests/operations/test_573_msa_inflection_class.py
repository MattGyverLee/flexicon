"""
Test Suite for MSAOperations.GetInflectionClass / SetInflectionClass and
SetStemMsaPos(keep_inflection_class=...) (issue #573).

``IMoStemMsa.InflectionClassRA`` had no public flexicon surface; restoring
the inflection class after ``SetStemMsaPos`` was only possible in raw LCM.
Issue #573 adds:

- ``MSAOperations.GetInflectionClass`` -- returns the ``IMoInflClass`` or
  ``None`` (unset, or MSA is not a ``MoStemMsa``; never raises on a wrong
  ClassName, matching this file's never-raise read idiom).
- ``MSAOperations.SetInflectionClass`` -- writes (``None`` clears); the
  class must belong to the MSA's POS or its parent chain, otherwise
  ``FP_ParameterError`` (never silently attaches an incompatible class).
- ``SetStemMsaPos(..., keep_inflection_class=True)`` -- restores the old
  inflection class after the POS change when it is still valid for the new
  POS; logs a warning and leaves it cleared when it is not.

Uses mocks for the FLExProject/LCM layer -- no live FieldWorks project
required. The module-level LCM interface names (``IMoStemMsa``, ...)
are patched to identity casts so plain mocks flow through
``__GetMsaObject``'s ClassName-gated cast.

Author: Muse (issue #573)
"""

import contextlib
import os
import sys
from types import SimpleNamespace
from unittest.mock import Mock, patch

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.Lexicon.MSAOperations import MSAOperations
from flexicon.code.FLExProject import FP_ParameterError, FP_NullParameterError


def _make_ic(hvo, name="Regular Verb"):
    ic = Mock()
    ic.ClassName = "MoInflClass"
    ic.Hvo = hvo
    ic.Name = SimpleNamespace(
        BestAnalysisAlternative=SimpleNamespace(Text=name)
    )
    return ic


def _make_pos(name, classes=(), owner=None, hvo=1000):
    # SimpleNamespace (not Mock): __Resolve's hasattr(_obj) probe misfires
    # on Mocks, returning a bare auto-attribute instead of the POS.
    return SimpleNamespace(
        ClassName="PartOfSpeech",
        Hvo=hvo,
        InflectionClassesOC=list(classes),
        Owner=owner,
        Name=SimpleNamespace(
            BestAnalysisAlternative=SimpleNamespace(Text=name)
        ),
    )


def _make_stem_msa(pos, infl_class=None):
    msa = Mock()
    msa.ClassName = "MoStemMsa"
    msa.PartOfSpeechRA = pos
    msa.InflectionClassRA = infl_class
    return msa


@pytest.fixture
def ops_and_project():
    project = Mock()
    project.writeEnabled = True
    ops = MSAOperations(project)
    # Bypass the real transaction machinery (_NestingAwareTransaction) --
    # not under test here.
    ops._TransactionCM = Mock(return_value=contextlib.nullcontext())
    return ops, project


@pytest.fixture(autouse=True)
def _identity_msa_casts():
    """Let plain mocks flow through __GetMsaObject's ClassName-gated cast."""
    with patch(
        "flexicon.code.Lexicon.MSAOperations.IMoStemMsa",
        side_effect=lambda x: x,
    ), patch(
        "flexicon.code.Lexicon.MSAOperations.IMoInflAffMsa",
        side_effect=lambda x: x,
    ), patch(
        "flexicon.code.Lexicon.MSAOperations.IMoDerivAffMsa",
        side_effect=lambda x: x,
    ), patch(
        "flexicon.code.Lexicon.MSAOperations.IMoUnclassifiedAffixMsa",
        side_effect=lambda x: x,
    ):
        yield


# ------------------------- GetInflectionClass -------------------------


def test_get_returns_set_class(ops_and_project):
    ops, _ = ops_and_project
    ic = _make_ic(11)
    msa = _make_stem_msa(_make_pos("Verb"), infl_class=ic)
    assert ops.GetInflectionClass(msa) is ic


def test_get_returns_none_when_unset(ops_and_project):
    ops, _ = ops_and_project
    msa = _make_stem_msa(_make_pos("Verb"), infl_class=None)
    assert ops.GetInflectionClass(msa) is None


def test_get_returns_none_for_non_stem_msa(ops_and_project):
    ops, _ = ops_and_project
    msa = Mock()
    msa.ClassName = "MoInflAffMsa"
    # Never raises on a wrong ClassName -- the established read idiom.
    assert ops.GetInflectionClass(msa) is None


def test_get_via_hvo(ops_and_project):
    ops, project = ops_and_project
    ic = _make_ic(12)
    msa = _make_stem_msa(_make_pos("Verb"), infl_class=ic)
    project.Object = Mock(return_value=msa)
    assert ops.GetInflectionClass(4242) is ic
    project.Object.assert_called_once_with(4242)


def test_get_null_raises(ops_and_project):
    ops, _ = ops_and_project
    with pytest.raises(FP_NullParameterError):
        ops.GetInflectionClass(None)


# ------------------------- SetInflectionClass -------------------------


def test_set_valid_class_on_own_pos(ops_and_project):
    ops, _ = ops_and_project
    ic = _make_ic(21)
    pos = _make_pos("Verb", classes=[ic])
    msa = _make_stem_msa(pos)
    ops.SetInflectionClass(msa, ic)
    assert msa.InflectionClassRA is ic


def test_set_valid_class_from_parent_pos(ops_and_project):
    ops, _ = ops_and_project
    ic = _make_ic(22)
    parent = _make_pos("Verb", classes=[ic], hvo=2000)
    child = _make_pos("Transitive Verb", classes=[], owner=parent, hvo=2001)
    msa = _make_stem_msa(child)
    ops.SetInflectionClass(msa, ic)
    assert msa.InflectionClassRA is ic


def test_set_invalid_class_raises(ops_and_project):
    ops, _ = ops_and_project
    noun_ic = _make_ic(23, name="First Declension")
    verb_pos = _make_pos("Verb", classes=[])
    msa = _make_stem_msa(verb_pos)
    with pytest.raises(FP_ParameterError) as excinfo:
        ops.SetInflectionClass(msa, noun_ic)
    assert "does not belong" in str(excinfo.value)
    # Nothing was attached by the failed validation.
    assert msa.InflectionClassRA is None


def test_set_none_clears(ops_and_project):
    ops, _ = ops_and_project
    ic = _make_ic(24)
    pos = _make_pos("Verb", classes=[ic])
    msa = _make_stem_msa(pos, infl_class=ic)
    ops.SetInflectionClass(msa, None)
    assert msa.InflectionClassRA is None


def test_set_via_hvo(ops_and_project):
    ops, project = ops_and_project
    ic = _make_ic(25)
    pos = _make_pos("Verb", classes=[ic])
    msa = _make_stem_msa(pos)
    project.Object = Mock(side_effect=lambda hvo: {111: msa, 222: ic}[hvo])
    ops.SetInflectionClass(111, 222)
    assert msa.InflectionClassRA is ic


def test_set_rejects_non_inflclass_object(ops_and_project):
    ops, _ = ops_and_project
    pos = _make_pos("Verb", classes=[])
    msa = _make_stem_msa(pos)
    not_a_class = Mock()
    not_a_class.ClassName = "PartOfSpeech"
    with pytest.raises(FP_ParameterError):
        ops.SetInflectionClass(msa, not_a_class)


def test_set_rejects_non_stem_msa(ops_and_project):
    ops, _ = ops_and_project
    msa = Mock()
    msa.ClassName = "MoDerivAffMsa"
    with pytest.raises(FP_ParameterError) as excinfo:
        ops.SetInflectionClass(msa, _make_ic(26))
    assert "stem MSA" in str(excinfo.value)


def test_set_rejects_msa_without_pos(ops_and_project):
    ops, _ = ops_and_project
    msa = _make_stem_msa(None)
    with pytest.raises(FP_ParameterError) as excinfo:
        ops.SetInflectionClass(msa, _make_ic(27))
    assert "no part of speech" in str(excinfo.value)


def test_set_null_msa_raises(ops_and_project):
    ops, _ = ops_and_project
    with pytest.raises(FP_NullParameterError):
        ops.SetInflectionClass(None, None)


# ---------------- SetStemMsaPos keep_inflection_class ----------------


def _make_sense_with_stem_msa(stem_msa):
    # SimpleNamespace (not Mock) so __ResolveSense's hasattr(_obj) probe
    # does not misfire.
    return SimpleNamespace(MorphoSyntaxAnalysisRA=stem_msa)


class _StemMsaStub:
    """Stem-MSA stand-in that records InflectionClassRA writes."""

    def __init__(self, pos, infl_class=None):
        self.ClassName = "MoStemMsa"
        self.PartOfSpeechRA = pos
        self.infl_writes = []
        self._infl = infl_class

    @property
    def InflectionClassRA(self):
        return self._infl

    @InflectionClassRA.setter
    def InflectionClassRA(self, value):
        self.infl_writes.append(value)
        self._infl = value


def test_set_pos_restores_valid_class(ops_and_project):
    ops, _ = ops_and_project
    ic = _make_ic(31)
    old_pos = _make_pos("Verb", classes=[ic], hvo=3000)
    new_pos = _make_pos("Verb (revised)", classes=[ic], hvo=3001)
    msa = _StemMsaStub(old_pos, infl_class=ic)
    sense = _make_sense_with_stem_msa(msa)
    ops.SetStemMsaPos(sense, new_pos)
    assert msa.PartOfSpeechRA is new_pos
    # The restore write happened inside the same transaction.
    assert msa.infl_writes == [ic]
    assert msa.InflectionClassRA is ic


def test_set_pos_drops_invalid_class_with_warning(ops_and_project, caplog):
    ops, _ = ops_and_project
    ic = _make_ic(32, name="Regular Verb")
    old_pos = _make_pos("Verb", classes=[ic], hvo=3100)
    new_pos = _make_pos("Noun", classes=[], hvo=3101)
    msa = _StemMsaStub(old_pos, infl_class=ic)
    sense = _make_sense_with_stem_msa(msa)
    with caplog.at_level("WARNING", logger="flexicon.code.Lexicon.MSAOperations"):
        ops.SetStemMsaPos(sense, new_pos)
    assert msa.PartOfSpeechRA is new_pos
    # Class left cleared, warning logged -- never silently re-attached.
    assert msa.infl_writes == []
    assert any("inflection class" in r.message for r in caplog.records)


def test_set_pos_opt_out_drops_class(ops_and_project):
    ops, _ = ops_and_project
    ic = _make_ic(33)
    old_pos = _make_pos("Verb", classes=[ic], hvo=3000)
    new_pos = _make_pos("Verb (revised)", classes=[ic], hvo=3001)
    msa = _StemMsaStub(old_pos, infl_class=ic)
    sense = _make_sense_with_stem_msa(msa)
    ops.SetStemMsaPos(sense, new_pos, keep_inflection_class=False)
    assert msa.PartOfSpeechRA is new_pos
    # keep=False: no restore write at all.
    assert msa.infl_writes == []
