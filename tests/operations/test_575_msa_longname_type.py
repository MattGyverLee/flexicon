"""
Test Suite for MSAOperations.GetLongName / GetMSAType and
LexSenseOperations.GetGrammaticalInfoText (issue #575).

Scripts used to read ``msa.LongName`` on the raw LCM object (what FLEx
shows as the grammatical info, e.g. ``"Verb  Pl.3"``) and to dispatch on
``msa.ClassName`` to tell stem / inflectional-affix / derivational-affix /
unclassified MSAs apart. Issue #575 adds public wrappers for both idioms:

- ``MSAOperations.GetLongName`` -- reads the ``LongName`` LCM property,
  normalizing FLEx's empty placeholder ``"***"`` to ``""``.
- ``MSAOperations.GetMSAType`` -- maps the four known MSA ClassNames to
  ``"stem"`` / ``"inflectional"`` / ``"derivational"`` / ``"unclassified"``,
  falling back to the raw ClassName for unrecognized subtypes.
- ``LexSenseOperations.GetGrammaticalInfoText`` -- trivial composition:
  sense -> MSA -> ``GetLongName``.

Uses mocks for the FLExProject/LCM layer -- no live FieldWorks project
required.

Author: Muse (issue #575)
"""

import os
import sys
from unittest.mock import Mock, patch

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.Lexicon.MSAOperations import MSAOperations
from flexicon.code.Lexicon.LexSenseOperations import LexSenseOperations
from flexicon.code.FLExProject import FP_NullParameterError


def _make_msa(long_name="Verb  Pl.3", class_name="MoStemMsa"):
    msa = Mock()
    msa.LongName = long_name
    msa.ClassName = class_name
    return msa


@pytest.fixture(autouse=True)
def _identity_msa_casts():
    """Let plain mocks flow through the ClassName-gated MSA cast."""
    base = "flexicon.code.Lexicon.MSAOperations."
    names = ("IMoStemMsa", "IMoInflAffMsa", "IMoDerivAffMsa",
             "IMoUnclassifiedAffixMsa")
    patches = [patch(base + n, side_effect=lambda x: x) for n in names]
    for p in patches:
        p.start()
    yield
    for p in patches:
        p.stop()


@pytest.fixture
def ops_and_project():
    project = Mock()
    project.writeEnabled = True
    msa_ops = MSAOperations(project)
    sense_ops = LexSenseOperations(project)
    # Wire project.MSA so GetGrammaticalInfoText's composition hits the
    # real GetLongName rather than an auto-mock.
    project.MSA = msa_ops
    return msa_ops, sense_ops, project


# ------------------------- GetLongName -------------------------


def test_get_long_name_returns_display_text(ops_and_project):
    msa_ops, _, _ = ops_and_project
    msa = _make_msa(long_name="Verb  Pl.3")
    assert msa_ops.GetLongName(msa) == "Verb  Pl.3"


def test_get_long_name_normalizes_stars(ops_and_project):
    msa_ops, _, _ = ops_and_project
    msa = _make_msa(long_name="***")
    assert msa_ops.GetLongName(msa) == ""


def test_get_long_name_unset_returns_empty(ops_and_project):
    msa_ops, _, _ = ops_and_project
    msa = _make_msa(long_name=None)
    assert msa_ops.GetLongName(msa) == ""


def test_get_long_name_via_hvo(ops_and_project):
    msa_ops, _, project = ops_and_project
    msa = _make_msa(long_name="Noun  Sg")
    project.Object = Mock(return_value=msa)
    assert msa_ops.GetLongName(12345) == "Noun  Sg"
    project.Object.assert_called_once_with(12345)


def test_get_long_name_null_raises(ops_and_project):
    msa_ops, _, _ = ops_and_project
    with pytest.raises(FP_NullParameterError):
        msa_ops.GetLongName(None)


# ------------------------- GetMSAType -------------------------


@pytest.mark.parametrize(
    "class_name,expected",
    [
        ("MoStemMsa", "stem"),
        ("MoInflAffMsa", "inflectional"),
        ("MoDerivAffMsa", "derivational"),
        ("MoUnclassifiedAffixMsa", "unclassified"),
    ],
)
def test_get_msa_type_known_subtypes(ops_and_project, class_name, expected):
    msa_ops, _, _ = ops_and_project
    msa = _make_msa(class_name=class_name)
    assert msa_ops.GetMSAType(msa) == expected


def test_get_msa_type_falls_back_to_raw_classname(ops_and_project):
    msa_ops, _, _ = ops_and_project
    msa = _make_msa(class_name="MoDerivStepMsa")
    assert msa_ops.GetMSAType(msa) == "MoDerivStepMsa"


def test_get_msa_type_via_hvo(ops_and_project):
    msa_ops, _, project = ops_and_project
    msa = _make_msa(class_name="MoInflAffMsa")
    project.Object = Mock(return_value=msa)
    assert msa_ops.GetMSAType(777) == "inflectional"


def test_get_msa_type_null_raises(ops_and_project):
    msa_ops, _, _ = ops_and_project
    with pytest.raises(FP_NullParameterError):
        msa_ops.GetMSAType(None)


# -------------------- GetGrammaticalInfoText --------------------


def test_get_grammatical_info_text_composes_msa_longname(ops_and_project):
    _, sense_ops, _ = ops_and_project
    sense = Mock()
    sense.MorphoSyntaxAnalysisRA = _make_msa(long_name="Verb  Pl.3")
    assert sense_ops.GetGrammaticalInfoText(sense) == "Verb  Pl.3"


def test_get_grammatical_info_text_normalizes_stars(ops_and_project):
    _, sense_ops, _ = ops_and_project
    sense = Mock()
    sense.MorphoSyntaxAnalysisRA = _make_msa(long_name="***")
    assert sense_ops.GetGrammaticalInfoText(sense) == ""


def test_get_grammatical_info_text_no_msa(ops_and_project):
    _, sense_ops, _ = ops_and_project
    sense = Mock()
    sense.MorphoSyntaxAnalysisRA = None
    assert sense_ops.GetGrammaticalInfoText(sense) == ""


def test_get_grammatical_info_text_null_raises(ops_and_project):
    _, sense_ops, _ = ops_and_project
    with pytest.raises(FP_NullParameterError):
        sense_ops.GetGrammaticalInfoText(None)
