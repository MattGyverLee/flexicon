#
#   test_issue624_possibility_list_name_ws.py
#
#   Possibility-list Operations classes must not resolve names through the
#   project's default analysis writing system when the caller gave no
#   writing system (issue #624, siblings of #604 / #183):
#
#     - Get* reads return the best analysis alternative when wsHandle is None
#     - Find* lookups match the best alternative plus every current analysis
#       writing system when wsHandle is None
#     - an explicit wsHandle is honoured exactly (no silent fallback)
#
#   Offline tests with fake multistrings; the live counterpart is
#   test_issue624_possibility_list_name_ws_live.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from unittest.mock import MagicMock, patch

import pytest

from flexicon.code.Shared import ws_text
from flexicon.code.Lists import possibility_item_base as item_base_mod
from flexicon.code.Lists import PossibilityListOperations as pl_mod
from flexicon.code.Lists import PublicationOperations as pub_mod
from flexicon.code.Lists import TranslationTypeOperations as tt_mod
from flexicon.code.Lists import AgentOperations as agent_mod
from flexicon.code.Notebook import AnthropologyOperations as anthro_mod
from flexicon.code.Notebook import LocationOperations as loc_mod
from flexicon.code.Notebook import PersonOperations as person_mod

PT = 100  # default analysis WS in these fixtures (holds no list text)
EN = 200  # second analysis WS (holds the catalog text)
SEH = 300  # vernacular WS
FR = 400  # not a current writing system


class _Ts:
    def __init__(self, text):
        self.Text = text


class FakeMulti:
    """IMultiString stand-in. Analysis order [PT, EN]; vernacular [SEH]."""

    def __init__(self, alts=None):
        self.alts = dict(alts or {})

    def get_String(self, handle):
        return _Ts(self.alts.get(handle))

    def _first(self, order):
        for h in order:
            if self.alts.get(h):
                return _Ts(self.alts[h])
        return _Ts("***")

    @property
    def BestAnalysisAlternative(self):
        return self._first((PT, EN))

    @property
    def BestVernacularAlternative(self):
        # LCM falls back from vernacular to analysis
        return self._first((SEH, PT, EN))


class FakeItem:
    ClassName = "CmPossibility"

    def __init__(self, name=None, abbr=None, desc=None, comment=None):
        self.Name = FakeMulti(name)
        self.Abbreviation = FakeMulti(abbr)
        self.Description = FakeMulti(desc)
        self.Comment = FakeMulti(comment)


def _ws(handle):
    w = MagicMock()
    w.Handle = handle
    return w


@pytest.fixture(autouse=True)
def _no_ts_cast():
    """ITsString(x) is a pythonnet cast; the fakes already expose .Text."""
    with patch.object(ws_text, "ITsString", lambda ts: ts):
        yield


def _project():
    project = MagicMock()
    project.project.DefaultAnalWs = PT
    project.lp.CurrentAnalysisWritingSystems = [_ws(PT), _ws(EN)]
    project.lp.CurrentVernacularWritingSystems = [_ws(SEH)]
    project._FLExProject__WSHandle = lambda ws, default: default if ws is None else ws
    return project


def _make(cls, **attrs):
    ops = cls.__new__(cls)
    ops.project = _project()
    for k, v in attrs.items():
        setattr(ops, k, v)
    return ops


def _catalog():
    """List text only in English while the default analysis WS is pt."""
    return FakeItem(
        name={EN: "Free translation"},
        abbr={EN: "Free"},
        desc={EN: "A free rendering"},
        comment={EN: "header text"},
    )


# ---------------------------------------------------------------- ws_text


class TestWsTextHelpers:
    def test_read_text_no_ws_uses_best_alternative(self):
        assert ws_text.read_text(_catalog().Name) == "Free translation"

    def test_read_text_prefers_default_when_both_populated(self):
        assert ws_text.read_text(FakeMulti({PT: "Livre", EN: "Free"})) == "Livre"

    def test_read_text_explicit_ws_is_exact(self):
        m = _catalog().Name
        assert ws_text.read_text(m, PT) == ""
        assert ws_text.read_text(m, EN) == "Free translation"

    def test_read_text_unset_is_empty(self):
        assert ws_text.read_text(FakeMulti()) == ""

    def test_read_text_vernacular_preference(self):
        m = FakeMulti({SEH: "Alicete", EN: "Alice"})
        assert ws_text.read_text(m, prefer="vernacular") == "Alicete"
        assert ws_text.read_text(m) == "Alice"

    def test_read_text_vernacular_falls_back_to_analysis(self):
        assert ws_text.read_text(FakeMulti({EN: "Default User"}), prefer="vernacular") == "Default User"

    def test_name_matches_non_default_alternative(self):
        assert ws_text.name_matches(_catalog().Name, "free translation", _project().lp)

    def test_name_matches_explicit_ws_is_exact(self):
        lp = _project().lp
        m = _catalog().Name
        assert not ws_text.name_matches(m, "free translation", lp, PT)
        assert ws_text.name_matches(m, "free translation", lp, EN)

    def test_name_matches_any_current_analysis_ws(self):
        m = FakeMulti({PT: "Livre", EN: "Free"})
        lp = _project().lp
        assert ws_text.name_matches(m, "livre", lp)
        assert ws_text.name_matches(m, "free", lp)

    def test_name_matches_explicit_ws_outside_current_list(self):
        m = FakeMulti({FR: "Libre"})
        lp = _project().lp
        assert not ws_text.name_matches(m, "libre", lp)
        assert ws_text.name_matches(m, "libre", lp, FR)

    def test_name_matches_unset_never_matches_null_marker(self):
        assert not ws_text.name_matches(FakeMulti(), "***", _project().lp)


# ------------------------------------------------- item base (Publication etc.)


class TestItemBaseReads:
    def _ops(self, items=()):
        return _make(
            pub_mod.PublicationOperations,
            _PossibilityItemOperations__ResolveObject=lambda o: o,
            GetAll=lambda *a, **k: list(items),
        )

    def test_get_name_without_ws(self):
        item = _catalog()
        assert self._ops().GetName(item) == "Free translation"

    def test_get_name_explicit_ws_exact(self):
        item = _catalog()
        ops = self._ops()
        assert ops.GetName(item, PT) == ""
        assert ops.GetName(item, EN) == "Free translation"

    def test_get_description_without_ws(self):
        assert self._ops().GetDescription(_catalog()) == "A free rendering"
        assert self._ops().GetDescription(_catalog(), PT) == ""

    def test_find_matches_non_default_alternative(self):
        item = _catalog()
        other = FakeItem(name={EN: "Other"})
        assert self._ops([other, item]).Find("FREE translation") is item

    def test_find_explicit_ws_exact(self):
        item = _catalog()
        ops = self._ops([item])
        assert ops.Find("Free translation", PT) is None
        assert ops.Find("Free translation", EN) is item

    def test_find_blank_and_missing(self):
        ops = self._ops([_catalog()])
        assert ops.Find("   ") is None
        assert ops.Find("Nope") is None

    def test_compare_to_uses_best_alternative(self):
        a = FakeItem(name={EN: "Apple"})
        b = FakeItem(name={EN: "Banana"})
        assert self._ops().CompareTo(a, b) == -1

    def test_publication_page_layout_and_header_without_ws(self):
        ops = self._ops()
        item = _catalog()
        assert ops.GetPageLayout(item) == "Free"
        assert ops.GetPageLayout(item, PT) == ""
        assert ops.GetHeaderFooter(item) == "header text"

    def test_translation_type_abbreviation_without_ws(self):
        ops = _make(
            tt_mod.TranslationTypeOperations,
            _PossibilityItemOperations__ResolveObject=lambda o: o,
        )
        item = _catalog()
        assert ops.GetAbbreviation(item) == "Free"
        assert ops.GetAbbreviation(item, PT) == ""


class TestAgentFind:
    def test_matches_non_default_alternative_and_explicit_exact(self):
        agent = FakeItem(name={EN: "Computer"})
        ops = _make(agent_mod.AgentOperations, GetAll=lambda *a, **k: [agent])
        assert ops.Find("computer") is agent
        assert ops.Find("Computer", PT) is None
        assert ops.Find("Computer", EN) is agent


# ------------------------------------------------------- PossibilityListOperations


class TestPossibilityListOperations:
    def _ops(self, lists=(), items=()):
        return _make(
            pl_mod.PossibilityListOperations,
            GetAllLists=lambda *a, **k: list(lists),
            GetItems=lambda *a, **k: list(items),
            _PossibilityListOperations__ResolveList=lambda o: o,
            _PossibilityListOperations__ResolveItem=lambda o: o,
        )

    def test_find_list_matches_non_default_alternative(self):
        lst = FakeItem(name={EN: "Parts Of Speech"})
        ops = self._ops(lists=[lst])
        assert ops.FindList("parts of speech") is lst
        assert ops.FindList("Parts Of Speech", PT) is None
        assert ops.FindList("Parts Of Speech", EN) is lst

    def test_get_list_name_without_ws(self):
        lst = FakeItem(name={EN: "Parts Of Speech"})
        ops = self._ops()
        assert ops.GetListName(lst) == "Parts Of Speech"
        assert ops.GetListName(lst, PT) == ""

    def test_find_item_matches_non_default_alternative(self):
        item = _catalog()
        ops = self._ops(items=[item])
        assert ops.FindItem(object(), "free translation") is item
        assert ops.FindItem(object(), "free translation", PT) is None

    def test_item_name_abbreviation_description_without_ws(self):
        item = _catalog()
        ops = self._ops()
        assert ops.GetItemName(item) == "Free translation"
        assert ops.GetItemAbbreviation(item) == "Free"
        assert ops.GetItemDescription(item) == "A free rendering"
        assert ops.GetItemName(item, PT) == ""
        assert ops.GetItemAbbreviation(item, PT) == ""
        assert ops.GetItemDescription(item, PT) == ""

    def test_syncable_properties_use_best_alternative(self):
        props = self._ops().GetSyncableProperties(_catalog())
        assert props["Name"] == "Free translation"
        assert props["Abbreviation"] == "Free"
        assert props["Description"] == "A free rendering"


# ------------------------------------------------------------ Notebook classes


class TestAnthropologyOperations:
    def _ops(self, items=()):
        return _make(
            anthro_mod.AnthropologyOperations,
            _AnthropologyOperations__GetItemObject=lambda o: o,
            GetAll=lambda *a, **k: list(items),
        )

    def test_reads_without_ws(self):
        item = _catalog()
        ops = self._ops()
        assert ops.GetName(item) == "Free translation"
        assert ops.GetAbbreviation(item) == "Free"
        assert ops.GetDescription(item) == "A free rendering"
        assert ops.GetName(item, PT) == ""

    def test_find(self):
        item = _catalog()
        ops = self._ops([item])
        assert ops.Find("Free Translation") is None  # case-sensitive by design
        assert ops.Find("Free translation") is item
        assert ops.Find("Free translation", PT) is None
        assert ops.Find("Free translation", EN) is item


class TestLocationOperations:
    def _ops(self, items=()):
        return _make(
            loc_mod.LocationOperations,
            _LocationOperations__ResolveObject=lambda o: o,
            GetAll=lambda *a, **k: list(items),
        )

    def test_reads_without_ws(self):
        item = _catalog()
        ops = self._ops()
        assert ops.GetName(item) == "Free translation"
        assert ops.GetAlias(item) == "Free"
        assert ops.GetDescription(item) == "A free rendering"
        assert ops.GetName(item, PT) == ""

    def test_find(self):
        item = _catalog()
        ops = self._ops([item])
        assert ops.Find("FREE TRANSLATION") is item
        assert ops.Find("Free translation", PT) is None


class TestPersonOperations:
    def _ops(self, items=()):
        return _make(
            person_mod.PersonOperations,
            _PersonOperations__ResolveObject=lambda o: o,
            GetAll=lambda *a, **k: list(items),
        )

    def test_name_prefers_vernacular_then_analysis(self):
        both = FakeItem(name={SEH: "Alicete", EN: "Alice"})
        only_en = FakeItem(name={EN: "Default User"})
        ops = self._ops()
        assert ops.GetName(both) == "Alicete"
        assert ops.GetName(only_en) == "Default User"
        assert ops.GetName(only_en, SEH) == ""

    def test_find_matches_vernacular_and_analysis(self):
        both = FakeItem(name={SEH: "Alicete", EN: "Alice"})
        only_en = FakeItem(name={EN: "Default User"})
        ops = self._ops([both, only_en])
        assert ops.Find("Alicete") is both
        assert ops.Find("Alice") is both
        assert ops.Find("Default User") is only_en
        assert ops.Find("Default User", SEH) is None
        assert ops.Find("Default User", EN) is only_en

    def test_address_and_education_without_ws(self):
        item = FakeItem(abbr={EN: "1 Main St"}, desc={EN: "PhD"})
        ops = self._ops()
        assert ops.GetAddress(item) == "1 Main St"
        assert ops.GetEducation(item) == "PhD"
        assert ops.GetAddress(item, PT) == ""
