#
#   test_issue377_stem_name_roundtrip_live.py
#
#   Issue #377 item 1: live proof that a set StemNameRA round-trips through
#   Allomorph.stem_name (StemNameRA.Name via best_analysis_text).
#
#   Requires Sena 3 backup data (IMoStemName catalog rows). Uses sena3_sandbox
#   so the real Sena 3 project is never mutated.
#
#   Platform: Python.NET, FieldWorks 9+
#
#   Copyright 2026
#

import pytest

from flexicon import cast_to_concrete
from flexicon.code.Lexicon.allomorph import Allomorph
from flexicon.code.Shared.string_utils import best_analysis_text

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_377_"


def _first_catalog_stem_name(project):
    """Return the first IMoStemName from any POS StemNamesOC, or None."""
    for pos in project.POS.GetAll():
        concrete_pos = cast_to_concrete(pos)
        if not hasattr(concrete_pos, "StemNamesOC"):
            continue
        collection = concrete_pos.StemNamesOC
        if collection is None or collection.Count == 0:
            continue
        for index in range(collection.Count):
            candidate = collection[index]
            if candidate is not None and getattr(candidate, "IsValidObject", True):
                return candidate
    return None


def _expected_stem_name_label(stem_name_obj):
    return best_analysis_text(getattr(stem_name_obj, "Name", None))


def _first_existing_stem_name_allomorph(project, entry_limit=200):
    """Return (entry, Allomorph wrapper) when Sena 3 has StemNameRA set."""
    for index, entry in enumerate(project.LexEntry.GetAll()):
        if index >= entry_limit:
            break
        for wrapped in project.Allomorphs.GetAll(entry):
            if not wrapped.is_stem_allomorph or wrapped.stem_name == "":
                continue
            concrete = wrapped.as_stem_allomorph()
            if concrete is None or getattr(concrete, "StemNameRA", None) is None:
                continue
            return entry, wrapped
    return None


@pytest.mark.requires_live_project
class TestIssue377StemNameRoundTrip:
    @pytest.mark.live_phase("Allomorph", "read")
    def test_existing_sena3_stem_name_readback(self, sena3_sandbox):
        """When Sena 3 already has StemNameRA set, wrapper matches LCM."""
        sandbox = sena3_sandbox
        found = _first_existing_stem_name_allomorph(sandbox)
        if found is None:
            pytest.skip(
                "No stem allomorph with StemNameRA found in Sena 3 sandbox "
                "(catalog may be empty in this backup)."
            )
        _entry, wrapped = found
        concrete = wrapped.as_stem_allomorph()
        expected = _expected_stem_name_label(concrete.StemNameRA)
        assert wrapped.is_stem_allomorph
        assert wrapped.stem_name == expected

    @pytest.mark.live_phase("AllomorphOperations", "write")
    def test_assign_stem_name_ra_round_trips_via_wrapper(self, sena3_sandbox):
        """Assign StemNameRA on a new stem allomorph; re-read by HVO."""
        sandbox = sena3_sandbox
        catalog_stem = _first_catalog_stem_name(sandbox)
        if catalog_stem is None:
            pytest.skip(
                "Sena 3 sandbox has no IMoStemName rows under POS.StemNamesOC."
            )

        expected = _expected_stem_name_label(catalog_stem)
        assert expected != "", (
            "catalog stem name must carry analysis text for a meaningful round-trip"
        )

        entry = sandbox.LexEntry.Create(f"{TEST_PREFIX}stem_entry")
        try:
            allo = sandbox.Allomorphs.Create(
                entry,
                f"{TEST_PREFIX}form",
                morphType="stem",
            )
            concrete = cast_to_concrete(allo)
            assert getattr(concrete, "ClassName", "") == "MoStemAllomorph"
            concrete.StemNameRA = catalog_stem

            hvo = allo.Hvo
            assert isinstance(hvo, int)
            refetched = cast_to_concrete(
                sandbox.project.ServiceLocator.GetObject(hvo)
            )
            assert refetched.StemNameRA is not None
            assert _expected_stem_name_label(refetched.StemNameRA) == expected

            wrapped = Allomorph(refetched)
            assert wrapped.stem_name == expected
        finally:
            sandbox.LexEntry.Delete(entry)
