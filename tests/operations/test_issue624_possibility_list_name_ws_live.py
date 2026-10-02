#
#   test_issue624_possibility_list_name_ws_live.py
#
#   Live verification (sena3_sandbox -- tempdir copy of Sena 3) that the
#   possibility-list Operations classes no longer depend on the default
#   analysis writing system for name reads / lookups (issue #624).
#
#   Sena 3: default analysis WS is 'pt', current analysis WSs are
#   [pt, en]; the list text lives ONLY in 'en'. Every "pre-state"
#   assertion re-queries the LCM directly (get_String on the raw
#   multistring) rather than trusting the API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


def _raw(multi, handle):
    """Raw LCM read of one alternative, bypassing flexicon."""
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    return ITsString(multi.get_String(handle)).Text or ""


@pytest.fixture
def env(sena3_sandbox):
    """(project, default_ws, en_ws)."""
    lp = sena3_sandbox.lp
    default = lp.DefaultAnalysisWritingSystem
    en = [w for w in lp.CurrentAnalysisWritingSystems if w.Id.startswith("en")]
    assert default.Id.startswith("pt") and en, "unexpected Sena 3 writing systems"
    return sena3_sandbox, default, en[0]


def _first_en_only(items, en, default):
    for item in items:
        if _raw(item.Name, default.Handle) == "" and _raw(item.Name, en.Handle):
            return item
    raise AssertionError("no item with text only in en")


class TestItemBaseClasses:
    @pytest.mark.live_phase("PublicationOperations", "read")
    def test_publication_find_and_get_name(self, env):
        project, default, en = env
        pub = _first_en_only(project.Publications.GetAll(), en, default)
        expected = _raw(pub.Name, en.Handle)
        print(f"[INFO] pre-state pt={_raw(pub.Name, default.Handle)!r} en={expected!r}")
        assert project.Publications.GetName(pub) == expected
        assert project.Publications.Find(expected) is not None
        assert project.Publications.Find(expected.upper()) is not None
        # explicit ws is exact
        assert project.Publications.GetName(pub, default.Handle) == ""
        assert project.Publications.Find(expected, default.Handle) is None
        assert project.Publications.Find(expected, en.Handle) is not None

    @pytest.mark.live_phase("TranslationTypeOperations", "read")
    def test_translation_type_find_and_get_name(self, env):
        project, default, en = env
        tt = _first_en_only(project.TranslationTypes.GetAll(), en, default)
        expected = _raw(tt.Name, en.Handle)
        assert project.TranslationTypes.GetName(tt) == expected
        assert project.TranslationTypes.Find(expected) is not None
        assert project.TranslationTypes.Find(expected, default.Handle) is None
        assert project.TranslationTypes.GetAbbreviation(tt) == _raw(tt.Abbreviation, en.Handle)

    @pytest.mark.live_phase("AgentOperations", "read")
    def test_agent_find(self, env):
        project, default, en = env
        agent = _first_en_only(project.Agents.GetAll(), en, default)
        expected = _raw(agent.Name, en.Handle)
        found = project.Agents.Find(expected)
        assert found is not None and found.Hvo == agent.Hvo
        assert project.Agents.Find(expected, default.Handle) is None
        assert project.Agents.GetName(agent) == expected


class TestPossibilityLists:
    @pytest.mark.live_phase("PossibilityListOperations", "read")
    def test_find_list_and_names(self, env):
        project, default, en = env
        pl = project.PossibilityLists
        lst = _first_en_only(pl.GetAllLists(), en, default)
        expected = _raw(lst.Name, en.Handle)
        print(f"[INFO] pre-state list pt={_raw(lst.Name, default.Handle)!r} en={expected!r}")
        assert pl.GetListName(lst) == expected
        found = pl.FindList(expected)
        assert found is not None and found.Hvo == lst.Hvo
        assert pl.FindList(expected, default.Handle) is None

    @pytest.mark.live_phase("PossibilityListOperations", "read")
    def test_find_item_and_item_names(self, env):
        project, default, en = env
        pl = project.PossibilityLists
        for lst in pl.GetAllLists():
            items = list(pl.GetItems(lst))
            candidates = [
                i for i in items
                if _raw(i.Name, default.Handle) == "" and _raw(i.Name, en.Handle)
            ]
            if candidates:
                item = candidates[0]
                break
        else:
            pytest.fail("no possibility list holds an en-only item")
        expected = _raw(item.Name, en.Handle)
        assert pl.GetItemName(item) == expected
        assert pl.GetItemName(item, default.Handle) == ""
        assert pl.FindItem(lst, expected) is not None
        assert pl.FindItem(lst, expected, default.Handle) is None
        assert pl.GetSyncableProperties(item)["Name"] == expected


class TestNotebook:
    @pytest.mark.live_phase("AnthropologyOperations", "read")
    def test_anthropology_find_and_names(self, env):
        project, default, en = env
        an = project.Anthropology
        item = _first_en_only(an.GetAll(), en, default)
        expected = _raw(item.Name, en.Handle)
        print(f"[INFO] pre-state anthro pt={_raw(item.Name, default.Handle)!r} en={expected!r}")
        assert an.GetName(item) == expected
        assert an.GetName(item, default.Handle) == ""
        assert an.GetDescription(item) == _raw(item.Description, en.Handle)
        assert an.GetAbbreviation(item) == _raw(item.Abbreviation, en.Handle)
        found = an.Find(expected)
        assert found is not None
        assert an.GetName(found) == expected
        assert an.Find(expected, default.Handle) is None

    @pytest.mark.live_phase("PersonOperations", "read")
    def test_person_find_and_name(self, env):
        project, default, en = env
        persons = project.Person
        person = next(
            p for p in persons.GetAll()
            if _raw(p.Name, en.Handle) and not any(
                _raw(p.Name, w.Handle) for w in project.lp.CurrentVernacularWritingSystems
            )
        )
        expected = _raw(person.Name, en.Handle)
        print(f"[INFO] pre-state person en={expected!r} (no vernacular text)")
        assert persons.GetName(person) == expected
        assert persons.Find(expected) is not None
        assert persons.Find(expected, default.Handle) is None

    @pytest.mark.live_phase("LocationOperations", "create")
    def test_location_created_in_en_is_readable_and_findable(self, env):
        project, default, en = env
        loc = project.Location.Create(f"{TEST_PREFIX}Site", wsHandle=en.Handle)
        try:
            assert _raw(loc.Name, default.Handle) == ""  # pre-state
            assert _raw(loc.Name, en.Handle) == f"{TEST_PREFIX}Site"
            assert project.Location.GetName(loc) == f"{TEST_PREFIX}Site"
            found = project.Location.Find(f"{TEST_PREFIX}Site")
            assert found is not None
            assert project.Location.Find(f"{TEST_PREFIX}Site", default.Handle) is None
            print(
                f"[INFO] post-state en={_raw(loc.Name, en.Handle)!r} "
                f"pt={_raw(loc.Name, default.Handle)!r}"
            )
        finally:
            project.Location.Delete(loc)


class TestWritesRequeriedFromLcm:
    @pytest.mark.live_phase("PublicationOperations", "update")
    def test_set_name_default_ws_is_read_back_and_explicit_ws_is_exact(self, env):
        project, default, en = env
        pubs = project.Publications
        item = pubs.Create(f"{TEST_PREFIX}Pub", wsHandle=en.Handle)
        try:
            assert _raw(item.Name, default.Handle) == ""  # pre-state
            assert pubs.GetName(item) == f"{TEST_PREFIX}Pub"

            pubs.SetName(item, f"{TEST_PREFIX}PubDefault")  # no ws -> default WS
            refetched = pubs.Find(f"{TEST_PREFIX}PubDefault")
            assert refetched is not None
            assert _raw(refetched.Name, default.Handle) == f"{TEST_PREFIX}PubDefault"
            assert _raw(refetched.Name, en.Handle) == f"{TEST_PREFIX}Pub"
            # both alternatives stay findable; best alternative prefers default
            assert pubs.GetName(refetched) == f"{TEST_PREFIX}PubDefault"
            assert pubs.Find(f"{TEST_PREFIX}Pub") is not None
            print(
                f"[INFO] post-state pt={_raw(refetched.Name, default.Handle)!r} "
                f"en={_raw(refetched.Name, en.Handle)!r}"
            )
        finally:
            pubs.Delete(item)
