#
#   test_pos_catalog.py
#
#   Class: TestPOSCatalog
#          Phase 5a (issue #14) live-LCM integration tests for the new
#          catalog-driven POS creation methods on POSOperations:
#            - CreateFromCatalog(source_id)
#            - Create(name, abbreviation, catalogSourceId="GOLD:...")
#              (enhanced to consult the catalog when the prefix is GOLD:)
#
#          Uses the same writable-project fixture pattern as
#          tests/operations/test_phon_rules.py / test_phonemes.py.
#
#          IMPORTANT: GOLDEtic 'Adjective' assigns the same canonical GUID
#          (30d07580-5052-4d91-bc24-469b8b2d7df9) every time. Re-running
#          the test suite must therefore NOT leave an Adjective POS behind
#          or idempotency tests on subsequent runs would observe pre-existing
#          state. Cleanup tracks GUIDs we created and deletes them in
#          try/finally, never touching POSs that were already in the project.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


# Every test in this module opens a real .fwdata project via the
# writable_project fixture.
pytestmark = pytest.mark.requires_live_project


# ---------------------------------------------------------------------------
# Live-LCM project fixture
# ---------------------------------------------------------------------------

_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_writable_project():
    """Open one of the standard test projects in write mode, or None."""
    try:
        from flexlibs2.code.FLExProject import FLExProject
    except Exception:
        return None

    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=True)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def writable_project():
    """
    Module-scoped write-enabled FLExProject fixture. Skips dependent
    tests if SIL.LCModel isn't loaded or no candidate project can be
    opened in write mode.
    """
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")

    project = _try_open_writable_project()
    if project is None:
        pytest.skip(
            "No writable FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )

    yield project

    try:
        project.CloseProject()
    except Exception:
        pass


# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

ADJECTIVE_CANONICAL_GUID = "30d07580-5052-4d91-bc24-469b8b2d7df9"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _find_pos_by_guid(project, guid_str):
    """
    Walk all POSs (top-level + recursive SubPossibilitiesOS) and return
    the one whose GUID matches `guid_str` case-insensitively, or None.
    """
    target = guid_str.lower()
    pos_list = project.lp.PartsOfSpeechOA
    if pos_list is None:
        return None

    def _walk(collection):
        from SIL.LCModel import IPartOfSpeech

        for raw in collection:
            pos = IPartOfSpeech(raw)
            if str(pos.Guid).lower() == target:
                return pos
            if pos.SubPossibilitiesOS.Count > 0:
                found = _walk(pos.SubPossibilitiesOS)
                if found is not None:
                    return found
        return None

    return _walk(pos_list.PossibilitiesOS)


def _delete_pos_by_guid(project, guid_str):
    """
    Best-effort: find a POS by GUID and remove it from its owner. Safe to
    call when the POS doesn't exist or was already deleted.
    """
    if not guid_str:
        return
    try:
        target = _find_pos_by_guid(project, guid_str)
        if target is None:
            return
        # Determine owner: SubPossibilitiesOS if nested, else the
        # PartsOfSpeechOA list.
        from SIL.LCModel import IPartOfSpeech

        # Raw LCM writes -> own unit of work (tasks.md D14). Note the inner
        # `except` is a genuine owner-shape fallback, so each branch takes its
        # own bracket rather than wrapping the whole try (a failed first
        # branch must not leave a half-open unit of work for the second).
        try:
            parent_pos = IPartOfSpeech(target.Owner)
            with project.UndoableOperation("test cleanup: delete sub-POS"):
                parent_pos.SubPossibilitiesOS.Remove(target)
        except Exception:
            pos_list = project.lp.PartsOfSpeechOA
            with project.UndoableOperation("test cleanup: delete POS"):
                pos_list.PossibilitiesOS.Remove(target)
    except Exception:
        # Cleanup must never raise — leave traces for the next test to
        # observe if anything goes wrong.
        pass


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPOSCatalog:
    """
    Coverage for the catalog-aware POS creation paths added in Phase 5a:
    CreateFromCatalog() and the enhanced Create(catalogSourceId="GOLD:...").
    """

    # --- CreateFromCatalog ----------------------------------------------

    def test_create_from_catalog_uses_canonical_guid(self, writable_project):
        """
        CreateFromCatalog('GOLD:Adjective') must produce a POS whose GUID
        is the canonical GOLDEtic GUID for Adjective. If the Programmer's
        last-resort fallback ran (factory.Create() with no GUID), this
        assertion fails — that's the deeper issue called out in the
        verification-agent instructions.
        """
        # If the project already has an Adjective POS with the canonical
        # GUID (e.g. left over from a previous run, or imported wholesale),
        # idempotency will return that POS rather than creating a new one.
        # Track whether we created it so we only delete what we added.
        pre_existing = (
            _find_pos_by_guid(writable_project, ADJECTIVE_CANONICAL_GUID)
            is not None
        )
        created_guid = None
        try:
            pos = writable_project.POS.CreateFromCatalog("GOLD:Adjective")
            assert pos is not None, "CreateFromCatalog returned None"

            actual_guid = str(pos.Guid).lower()
            assert actual_guid == ADJECTIVE_CANONICAL_GUID, (
                f"POS GUID {actual_guid!r} != canonical "
                f"{ADJECTIVE_CANONICAL_GUID!r}. The Programmer's fallback "
                "path may have activated — investigate the "
                "IPartOfSpeechFactory.Create(Guid, ...) overloads."
            )
            assert pos.CatalogSourceId == "GOLD:Adjective", (
                f"CatalogSourceId = {pos.CatalogSourceId!r}, "
                "expected 'GOLD:Adjective'"
            )

            if not pre_existing:
                created_guid = ADJECTIVE_CANONICAL_GUID
        finally:
            if created_guid is not None:
                _delete_pos_by_guid(writable_project, created_guid)

    def test_create_from_catalog_imports_localized_name(self, writable_project):
        """
        After CreateFromCatalog, the English-WS name should be 'Adjective'
        (whatever the catalog ships). Read the name via the existing
        GetName(pos, wsHandle=...) API.
        """
        pre_existing = (
            _find_pos_by_guid(writable_project, ADJECTIVE_CANONICAL_GUID)
            is not None
        )
        created_guid = None
        try:
            pos = writable_project.POS.CreateFromCatalog("GOLD:Adjective")
            if not pre_existing:
                created_guid = ADJECTIVE_CANONICAL_GUID

            en_handle = writable_project.WSHandle("en")
            if en_handle is None:
                pytest.skip(
                    "Project has no 'en' writing system — can't verify "
                    "localized name. (CreateFromCatalog still ran.)"
                )

            name_en = writable_project.POS.GetName(pos, en_handle)
            assert name_en == "Adjective", (
                f"GetName(pos, wsHandle=en) = {name_en!r}, expected 'Adjective'"
            )
        finally:
            if created_guid is not None:
                _delete_pos_by_guid(writable_project, created_guid)

    def test_create_from_catalog_is_idempotent(self, writable_project):
        """
        Calling CreateFromCatalog twice with the same source_id must NOT
        create two POSs. The documented behaviour (per docstring) is that
        the second call returns the same POS. If the Programmer chose to
        raise instead, this test should be relaxed accordingly — failure
        below documents whichever behaviour actually shipped.
        """
        pre_existing = (
            _find_pos_by_guid(writable_project, ADJECTIVE_CANONICAL_GUID)
            is not None
        )
        created_guid = None
        try:
            first = writable_project.POS.CreateFromCatalog("GOLD:Adjective")
            if not pre_existing:
                created_guid = ADJECTIVE_CANONICAL_GUID

            # Second call: per docstring "if a POS with the catalog's
            # canonical GUID already exists in the project, that existing
            # POS is returned unchanged."
            second = writable_project.POS.CreateFromCatalog("GOLD:Adjective")

            assert second is not None
            assert str(first.Guid).lower() == str(second.Guid).lower(), (
                "Idempotency violated: second CreateFromCatalog returned "
                "a different POS"
            )

            # And only one POS with this GUID exists in the project.
            from SIL.LCModel import IPartOfSpeech

            matches = 0

            def _walk(collection):
                nonlocal matches
                for raw in collection:
                    p = IPartOfSpeech(raw)
                    if str(p.Guid).lower() == ADJECTIVE_CANONICAL_GUID:
                        matches += 1
                    if p.SubPossibilitiesOS.Count > 0:
                        _walk(p.SubPossibilitiesOS)

            _walk(writable_project.lp.PartsOfSpeechOA.PossibilitiesOS)
            assert matches == 1, (
                f"Expected exactly one POS with canonical Adjective GUID, "
                f"found {matches}"
            )
        finally:
            if created_guid is not None:
                _delete_pos_by_guid(writable_project, created_guid)

    def test_create_from_catalog_accepts_bare_id(self, writable_project):
        """
        CreateFromCatalog('Adjective') (no GOLD: prefix) must work the
        same as the prefixed form: same canonical GUID.
        """
        pre_existing = (
            _find_pos_by_guid(writable_project, ADJECTIVE_CANONICAL_GUID)
            is not None
        )
        created_guid = None
        try:
            pos = writable_project.POS.CreateFromCatalog("Adjective")
            assert pos is not None
            assert str(pos.Guid).lower() == ADJECTIVE_CANONICAL_GUID, (
                "Bare-id CreateFromCatalog produced wrong GUID"
            )
            if not pre_existing:
                created_guid = ADJECTIVE_CANONICAL_GUID
        finally:
            if created_guid is not None:
                _delete_pos_by_guid(writable_project, created_guid)

    # --- Enhanced Create(catalogSourceId="GOLD:...") --------------------

    def test_create_enhanced_with_gold_catalog_id(self, writable_project):
        """
        Create(name='MyAdj', abbreviation='myadj', catalogSourceId='GOLD:Adjective')
        must (a) attach the canonical GOLD GUID and (b) honour the
        user-supplied name+abbreviation in the default analysis WS.
        Catalog localized values land in OTHER WSes (per code comment).
        """
        pre_existing = (
            _find_pos_by_guid(writable_project, ADJECTIVE_CANONICAL_GUID)
            is not None
        )
        created_guid = None
        try:
            pos = writable_project.POS.Create(
                name="MyAdj",
                abbreviation="myadj",
                catalogSourceId="GOLD:Adjective",
            )
            assert pos is not None

            actual_guid = str(pos.Guid).lower()
            assert actual_guid == ADJECTIVE_CANONICAL_GUID, (
                f"Enhanced Create with GOLD: prefix produced GUID "
                f"{actual_guid!r}, expected canonical "
                f"{ADJECTIVE_CANONICAL_GUID!r}. Programmer's fallback "
                "may have activated."
            )
            if not pre_existing:
                created_guid = ADJECTIVE_CANONICAL_GUID

            # Default-analysis WS should now hold the user override,
            # not the catalog's 'Adjective'.
            anal_ws = writable_project.project.DefaultAnalWs
            name_anal = writable_project.POS.GetName(pos, anal_ws)
            abbr_anal = writable_project.POS.GetAbbreviation(pos, anal_ws)
            assert name_anal == "MyAdj", (
                f"Name in default-analysis WS = {name_anal!r}, "
                "expected user override 'MyAdj'"
            )
            assert abbr_anal == "myadj", (
                f"Abbreviation in default-analysis WS = {abbr_anal!r}, "
                "expected user override 'myadj'"
            )
        finally:
            if created_guid is not None:
                _delete_pos_by_guid(writable_project, created_guid)

    def test_create_unchanged_without_gold_prefix(self, writable_project):
        """
        When catalogSourceId does NOT start with 'GOLD:', the catalog
        must NOT be consulted: the POS gets a random GUID and the
        provided id is preserved verbatim in CatalogSourceId.
        """
        from SIL.LCModel import IPartOfSpeech  # noqa: F401 (sanity import)

        pos = None
        created_guid = None
        # Pick a unique-ish name so this test never collides with
        # pre-existing project state.
        test_name = "VerificationAgent_NonGoldPOS"
        test_abbr = "vapos"
        try:
            # Pre-clean any leftover from a previous failed run.
            existing = writable_project.POS.Find(test_name)
            if existing is not None:
                writable_project.POS.Delete(existing)

            pos = writable_project.POS.Create(
                name=test_name,
                abbreviation=test_abbr,
                catalogSourceId="ProjectSpecific:Foo",
            )
            assert pos is not None
            created_guid = str(pos.Guid).lower()

            # The GUID must NOT be the canonical Adjective GUID — and
            # since 'ProjectSpecific:Foo' isn't anywhere in GOLDEtic,
            # we can also assert it's a fresh GUID by checking it didn't
            # collide with any canonical catalog GUID. The simplest
            # invariant is "definitely not Adjective".
            assert created_guid != ADJECTIVE_CANONICAL_GUID, (
                "Create() with non-GOLD prefix should NOT have hit the "
                "catalog, but somehow got the canonical Adjective GUID"
            )

            # CatalogSourceId must be preserved verbatim.
            assert pos.CatalogSourceId == "ProjectSpecific:Foo", (
                f"CatalogSourceId = {pos.CatalogSourceId!r}, "
                "expected 'ProjectSpecific:Foo' (preserved verbatim)"
            )
        finally:
            if created_guid is not None:
                _delete_pos_by_guid(writable_project, created_guid)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
