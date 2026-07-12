"""
Test Suite for Shared.morph_type_utils

Regression coverage for issues #213 and #214:

- #213: AllomorphOperations.Create / __IsStemType crashed with
  ``AttributeError: 'str' object has no attribute 'Guid'`` when a string
  morph-type name was passed. The fix introduces a single shared resolver
  (``find_morph_type``) reused by both LexEntryOperations and
  AllomorphOperations, plus a shared ``is_stem_morph_type`` classifier.
- #214: The morph-type resolver rejected FLEx's decorated display labels
  (``=enclitic``, ``proclitic=``, ``-suffix``) and the "not found" error
  ended in a vague "etc.". The fix strips display markers before lookup
  and lists the complete canonical name set in the error message.

Uses lightweight fake morph-type/project objects (no live FLEx required)
since MoMorphTypeTags GUIDs and IMultiString.BestAnalysisAlternative.Text
access are the only real-LCM surface these functions touch.

Author: Programmer Team - Bug fix verification (#213, #214)
"""

import os
import sys
from unittest.mock import Mock

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.Shared.morph_type_utils import (
    CANONICAL_MORPH_TYPE_NAMES,
    find_morph_type,
    is_stem_morph_type,
    morph_type_not_found_error,
    strip_display_marker,
)
from SIL.LCModel import MoMorphTypeTags


class _FakeSubPossibilities(list):
    """List subclass that also exposes .Count, mirroring ILcmOwningSequence."""

    @property
    def Count(self):
        return len(self)


class _FakeMorphType:
    """Minimal stand-in for IMoMorphType: .Name.BestAnalysisAlternative.Text, .Guid, .SubPossibilitiesOS."""

    def __init__(self, name, guid, sub_possibilities=None):
        self.Name = Mock(BestAnalysisAlternative=Mock(Text=name))
        self.Guid = guid
        self.SubPossibilitiesOS = _FakeSubPossibilities(sub_possibilities or [])


def _make_project(morph_types):
    """Build a fake project exposing project.lp.LexDbOA.MorphTypesOA.PossibilitiesOS."""
    project = Mock()
    project.lp.LexDbOA.MorphTypesOA.PossibilitiesOS = morph_types
    return project


@pytest.fixture
def sample_project():
    """A project whose morph-type list includes stem, suffix, and enclitic."""
    stem = _FakeMorphType("stem", MoMorphTypeTags.kguidMorphStem)
    suffix = _FakeMorphType("suffix", MoMorphTypeTags.kguidMorphSuffix)
    enclitic = _FakeMorphType("enclitic", MoMorphTypeTags.kguidMorphEnclitic)
    return _make_project([stem, suffix, enclitic])


class TestCanonicalMorphTypeNames:
    def test_is_complete_non_empty_tuple(self):
        assert isinstance(CANONICAL_MORPH_TYPE_NAMES, tuple)
        assert len(CANONICAL_MORPH_TYPE_NAMES) == 19

    def test_includes_clitic_family(self):
        # issue #214: clitic/enclitic/proclitic must be in the accepted set
        for name in ("clitic", "enclitic", "proclitic"):
            assert name in CANONICAL_MORPH_TYPE_NAMES


class TestStripDisplayMarker:
    @pytest.mark.parametrize(
        "decorated,bare",
        [
            ("=enclitic", "enclitic"),
            ("proclitic=", "proclitic"),
            ("-suffix", "suffix"),
            ("stem", "stem"),
            ("~simulfix~", "simulfix"),
            ("<infix>", "infix"),
        ],
    )
    def test_strips_leading_and_trailing_markers(self, decorated, bare):
        assert strip_display_marker(decorated) == bare


class TestFindMorphType:
    @pytest.mark.parametrize(
        "query",
        ["suffix", "-suffix", "SUFFIX", "  suffix  ".strip()],
    )
    def test_resolves_bare_and_decorated_names(self, sample_project, query):
        result = find_morph_type(sample_project, query)
        assert result is not None
        assert result.Guid == MoMorphTypeTags.kguidMorphSuffix

    @pytest.mark.parametrize(
        "query",
        ["=enclitic", "enclitic=", "enclitic"],
    )
    def test_resolves_clitic_decorated_labels(self, sample_project, query):
        # issue #214: '=enclitic' style labels must resolve
        result = find_morph_type(sample_project, query)
        assert result is not None
        assert result.Guid == MoMorphTypeTags.kguidMorphEnclitic

    def test_returns_none_for_unknown_name(self, sample_project):
        assert find_morph_type(sample_project, "not-a-real-type") is None


class TestIsStemMorphType:
    def test_none_defaults_to_stem(self):
        assert is_stem_morph_type(None) is True

    def test_stem_guid_is_stem(self):
        mt = _FakeMorphType("stem", MoMorphTypeTags.kguidMorphStem)
        assert is_stem_morph_type(mt) is True

    def test_enclitic_guid_is_stem(self):
        # clitics use MoStemAllomorph, not MoAffixAllomorph
        mt = _FakeMorphType("enclitic", MoMorphTypeTags.kguidMorphEnclitic)
        assert is_stem_morph_type(mt) is True

    def test_suffix_guid_is_not_stem(self):
        mt = _FakeMorphType("suffix", MoMorphTypeTags.kguidMorphSuffix)
        assert is_stem_morph_type(mt) is False

    def test_string_argument_raises_attributeerror_not_silently_wrong(self):
        # is_stem_morph_type itself still expects a resolved object;
        # callers (AllomorphOperations.__IsStemType) are responsible for
        # resolving strings first via find_morph_type. Documented here so
        # a future regression is caught at the right layer.
        with pytest.raises(AttributeError):
            is_stem_morph_type("suffix")


class TestMorphTypeNotFoundError:
    def test_message_has_no_vague_etc(self):
        msg = morph_type_not_found_error("bogus")
        assert "etc" not in msg.lower()

    def test_message_includes_full_canonical_list(self):
        msg = morph_type_not_found_error("bogus")
        for name in CANONICAL_MORPH_TYPE_NAMES:
            assert name in msg
