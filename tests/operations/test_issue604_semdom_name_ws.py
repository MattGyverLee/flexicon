#
#   test_issue604_semdom_name_ws.py
#
#   SemanticDomainOperations name paths must not resolve through the
#   project's default analysis writing system when the caller gave no
#   writing system (issue #604, follow-up to #183):
#
#     - GetName / GetDescription / GetAbbreviation / GetQuestions read the
#       best analysis alternative when wsHandle is None
#     - FindByName matches the best analysis alternative and every current
#       analysis writing system when wsHandle is None
#     - an explicit wsHandle is still honoured exactly (no silent fallback)
#     - SetName / Create write to the requested explicit alternative
#
#   Offline tests with fake multistrings; the live counterpart is
#   test_issue604_semdom_name_ws_live.py.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from unittest.mock import MagicMock, patch

import pytest

from flexicon.code.Lexicon import SemanticDomainOperations as sdo_mod

PT = 100  # default analysis WS in these fixtures (no semdom text)
EN = 200  # second analysis WS (holds the canonical catalog text)
FR = 300  # not a current analysis WS


class _Ts:
    def __init__(self, text):
        self.Text = text


class FakeMulti:
    """IMultiString stand-in: handle -> text, analysis order = [PT, EN]."""

    ANALYSIS_ORDER = (PT, EN)

    def __init__(self, alts=None):
        self.alts = dict(alts or {})

    def get_String(self, handle):
        return _Ts(self.alts.get(handle))

    def set_String(self, handle, tss):
        self.alts[handle] = tss.Text

    @property
    def BestAnalysisAlternative(self):
        for h in self.ANALYSIS_ORDER:
            if self.alts.get(h):
                return _Ts(self.alts[h])
        return _Ts("***")


class FakeQuestion:
    def __init__(self, alts):
        self.Question = FakeMulti(alts)


class FakeDomain:
    ClassName = "CmSemanticDomain-fake"

    def __init__(self, name=None, abbr=None, desc=None, questions=()):
        self.Name = FakeMulti(name)
        self.Abbreviation = FakeMulti(abbr)
        self.Description = FakeMulti(desc)
        self.QuestionsOS = list(questions)


def _ws(handle):
    w = MagicMock()
    w.Handle = handle
    return w


def _ops(domains):
    project = MagicMock()
    project.project.DefaultAnalWs = PT
    project.lp.CurrentAnalysisWritingSystems = [_ws(PT), _ws(EN)]
    # FLExProject.__WSHandle contract: ints pass through, None -> default
    project._FLExProject__WSHandle = lambda ws, default: default if ws is None else ws
    ops = sdo_mod.SemanticDomainOperations.__new__(sdo_mod.SemanticDomainOperations)
    ops.project = project
    ops.GetAll = lambda *a, **k: list(domains)
    return ops


@pytest.fixture(autouse=True)
def _no_ts_cast():
    """ITsString(x) is a pythonnet cast; the fakes already expose .Text."""
    with patch.object(sdo_mod, "ITsString", lambda ts: ts):
        yield


def _walk():
    """A catalog domain: text only in English, default analysis WS is pt."""
    return FakeDomain(
        name={EN: "Walk"},
        abbr={EN: "7.2.1.1"},
        desc={EN: "Move on foot"},
        questions=[FakeQuestion({EN: "What words mean walk?"})],
    )


class TestReadsUseBestAnalysisAlternative:
    def test_get_name_without_ws_finds_non_default_alternative(self):
        d = _walk()
        assert d.Name.get_String(PT).Text is None  # default WS really is empty
        assert _ops([d]).GetName(d) == "Walk"

    def test_get_name_prefers_default_ws_when_both_populated(self):
        d = FakeDomain(name={PT: "Andar", EN: "Walk"})
        assert _ops([d]).GetName(d) == "Andar"

    def test_get_name_unset_everywhere_is_empty_string(self):
        d = FakeDomain()
        assert _ops([d]).GetName(d) == ""

    def test_get_name_explicit_ws_is_exact_not_best(self):
        d = _walk()
        ops = _ops([d])
        assert ops.GetName(d, PT) == ""
        assert ops.GetName(d, EN) == "Walk"

    def test_get_description_without_ws(self):
        d = _walk()
        assert _ops([d]).GetDescription(d) == "Move on foot"
        assert _ops([d]).GetDescription(d, PT) == ""

    def test_get_abbreviation_without_ws(self):
        d = _walk()
        assert _ops([d]).GetAbbreviation(d) == "7.2.1.1"
        assert _ops([d]).GetAbbreviation(d, PT) == ""

    def test_get_questions_without_ws(self):
        d = _walk()
        assert _ops([d]).GetQuestions(d) == "What words mean walk?"
        assert _ops([d]).GetQuestions(d, PT) == ""


class TestFindByName:
    def test_matches_non_default_analysis_alternative(self):
        walk = _walk()
        other = FakeDomain(name={EN: "Run"})
        assert _ops([other, walk]).FindByName("Walk") is walk

    def test_case_insensitive(self):
        walk = _walk()
        assert _ops([walk]).FindByName("wALk") is walk

    def test_matches_name_in_any_current_analysis_ws(self):
        # best alternative is the pt text; the en name must still match
        d = FakeDomain(name={PT: "Andar", EN: "Walk"})
        ops = _ops([d])
        assert ops.FindByName("Andar") is d
        assert ops.FindByName("Walk") is d

    def test_no_match_returns_none(self):
        assert _ops([_walk()]).FindByName("Swim") is None

    def test_blank_name_returns_none(self):
        assert _ops([_walk()]).FindByName("   ") is None

    def test_explicit_ws_is_exact(self):
        walk = _walk()
        ops = _ops([walk])
        assert ops.FindByName("Walk", EN) is walk
        assert ops.FindByName("Walk", PT) is None

    def test_explicit_ws_outside_current_analysis_list(self):
        d = FakeDomain(name={FR: "Marcher"})
        ops = _ops([d])
        assert ops.FindByName("Marcher") is None  # not an analysis WS
        assert ops.FindByName("Marcher", FR) is d

    def test_unset_names_do_not_match_null_marker(self):
        # best_analysis_text normalizes "***" to ""; a search for "***"
        # must not match every unnamed domain.
        assert _ops([FakeDomain()]).FindByName("***") is None


class TestWritesTargetExplicitAlternative:
    @pytest.fixture(autouse=True)
    def _writable(self):
        fake_utils = MagicMock()
        fake_utils.MakeString = lambda text, ws: _Ts(text)
        with patch.object(sdo_mod, "TsStringUtils", fake_utils):
            yield

    def _writable_ops(self, domains):
        ops = _ops(domains)
        ops._EnsureWriteEnabled = lambda: None
        cm = MagicMock()
        cm.__enter__ = lambda s: None
        cm.__exit__ = lambda s, *a: False
        ops._TransactionCM = lambda label: cm
        return ops

    def test_set_name_explicit_ws_writes_only_that_alternative(self):
        d = _walk()
        self._writable_ops([d]).SetName(d, "Stroll", EN)
        assert d.Name.alts == {EN: "Stroll"}

    def test_set_name_default_ws_is_default_analysis(self):
        d = _walk()
        ops = self._writable_ops([d])
        ops.SetName(d, "Andar")
        assert d.Name.alts == {EN: "Walk", PT: "Andar"}
        # and the default-ws write is what the default read returns
        assert ops.GetName(d) == "Andar"

    def test_create_writes_name_and_number_to_requested_ws(self):
        ops = self._writable_ops([])
        created = FakeDomain()
        factory = MagicMock()
        factory.Create.return_value = created
        ops.project.project.ServiceLocator.GetService.return_value = factory
        ops.Exists = lambda number: False

        result = ops.Create("TEST_Custom", "900.1", wsHandle=EN)

        assert result is created
        assert created.Name.alts == {EN: "TEST_Custom"}
        assert created.Abbreviation.alts == {EN: "900.1"}
        # readable straight back through the default (no-ws) reads
        assert ops.GetName(created) == "TEST_Custom"
        assert ops.GetNumber(created) == "900.1"
