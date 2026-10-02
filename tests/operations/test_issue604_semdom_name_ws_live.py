#
#   test_issue604_semdom_name_ws_live.py
#
#   Live verification (sena3_sandbox -- tempdir copy of Sena 3) that the
#   SemanticDomainOperations name paths no longer depend on the default
#   analysis writing system (issue #604).
#
#   Sena 3: default analysis WS is 'pt', current analysis WSs are
#   [pt, en]; the canonical semantic-domain catalog text lives ONLY in
#   'en'. Every "pre-state" assertion below re-queries the LCM directly
#   (get_String on the raw multistring) rather than trusting the API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"
KNOWN_NUMBER = "7.2.1.1"  # "Walk" in the canonical catalog


def _raw(multi, handle):
    """Raw LCM read of one alternative, bypassing flexicon."""
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    return ITsString(multi.get_String(handle)).Text or ""


def _handles(project):
    lp = project.lp
    default = lp.DefaultAnalysisWritingSystem
    others = [w for w in lp.CurrentAnalysisWritingSystems if w.Id != default.Id]
    return default, others


@pytest.fixture
def sd_env(sena3_sandbox):
    """(project, ops, domain, default_ws, en_ws) with a text-less default WS."""
    project = sena3_sandbox
    sd = project.SemanticDomains
    domain = sd.Find(KNOWN_NUMBER)
    assert domain is not None, f"Sena 3 sandbox has no domain {KNOWN_NUMBER}"
    default, others = _handles(project)
    en = [w for w in others if w.Id.startswith("en")]
    assert en, f"no non-default English analysis WS: {[w.Id for w in others]}"
    return project, sd, domain, default, en[0]


class TestReadsWithTextOnlyInNonDefaultWs:
    @pytest.mark.live_phase("SemanticDomainOperations", "read")
    def test_precondition_default_ws_has_no_semdom_text(self, sd_env):
        _project, _sd, domain, default, en = sd_env
        pre_default = _raw(domain.Name, default.Handle)
        pre_en = _raw(domain.Name, en.Handle)
        print(f"[INFO] pre-state default({default.Id})={pre_default!r} en={pre_en!r}")
        assert pre_default == "", "default analysis WS unexpectedly holds text"
        assert pre_en != ""

    @pytest.mark.live_phase("SemanticDomainOperations", "read")
    def test_get_name_returns_best_alternative(self, sd_env):
        _project, sd, domain, _default, en = sd_env
        expected = _raw(domain.Name, en.Handle)
        got = sd.GetName(domain)
        print(f"[INFO] GetName={got!r} expected={expected!r}")
        assert got and got == expected

    @pytest.mark.live_phase("SemanticDomainOperations", "read")
    def test_get_abbreviation_and_description_best_alternative(self, sd_env):
        _project, sd, domain, default, en = sd_env
        assert sd.GetAbbreviation(domain) == _raw(domain.Abbreviation, en.Handle) == KNOWN_NUMBER
        assert sd.GetDescription(domain) == _raw(domain.Description, en.Handle)
        # explicit ws stays exact: the default WS has nothing
        assert sd.GetAbbreviation(domain, default.Handle) == ""

    @pytest.mark.live_phase("SemanticDomainOperations", "read")
    def test_get_questions_best_alternative(self, sd_env):
        _project, sd, domain, default, en = sd_env
        expected = "\n".join(
            t for t in (_raw(q.Question, en.Handle) for q in domain.QuestionsOS) if t
        )
        got = sd.GetQuestions(domain)
        print(f"[INFO] questions chars={len(got)} expected={len(expected)}")
        assert got == expected
        assert sd.GetQuestions(domain, default.Handle) == ""

    @pytest.mark.live_phase("SemanticDomainOperations", "read")
    def test_find_by_name_matches_non_default_alternative(self, sd_env):
        _project, sd, domain, default, en = sd_env
        name = _raw(domain.Name, en.Handle)
        found = sd.FindByName(name)
        assert found is not None
        assert sd.GetNumber(found) == KNOWN_NUMBER
        # case-insensitive
        assert sd.FindByName(name.upper()) is not None
        # explicit ws is exact: nothing in the default WS, so no match there
        assert sd.FindByName(name, default.Handle) is None
        assert sd.FindByName(name, en.Handle) is not None
        assert sd.FindByName("TEST_no_such_domain_name") is None

    @pytest.mark.live_phase("SemanticDomainOperations", "read")
    def test_reads_survive_switching_default_to_a_text_less_ws(self, sd_env):
        """Make a different (text-less) analysis WS the default and re-read."""
        project, sd, domain, default, en = sd_env
        # Add a fresh French analysis WS and make it the default: it holds
        # no semantic-domain text at all.
        project.WritingSystems.Ensure("fr", "French", is_vernacular=False)
        project.WritingSystems.SetDefaultAnalysis("fr")
        new_default = project.lp.DefaultAnalysisWritingSystem
        assert new_default.Id.startswith("fr")
        assert _raw(domain.Name, new_default.Handle) == ""

        expected = _raw(domain.Name, en.Handle)
        assert sd.GetName(domain) == expected
        assert sd.FindByName(expected) is not None
        assert sd.GetNumber(domain) == KNOWN_NUMBER


class TestWritesRequeriedFromLcm:
    @pytest.mark.live_phase("SemanticDomainOperations", "update")
    def test_set_name_explicit_ws_lands_in_that_alternative_only(self, sd_env):
        project, sd, _domain, default, en = sd_env
        custom = sd.Create(f"{TEST_PREFIX}Custom", "900.604", wsHandle=en.Handle)
        try:
            assert _raw(custom.Name, default.Handle) == ""  # pre-state
            assert _raw(custom.Name, en.Handle) == f"{TEST_PREFIX}Custom"

            sd.SetName(custom, f"{TEST_PREFIX}Renamed", wsHandle=en.Handle)

            # re-query the LCM object, not the value we passed in
            refetched = sd.Find("900.604")
            assert refetched is not None
            assert _raw(refetched.Name, en.Handle) == f"{TEST_PREFIX}Renamed"
            assert _raw(refetched.Name, default.Handle) == ""
            # ... and the no-ws reads see it even though default WS is empty
            assert sd.GetName(refetched) == f"{TEST_PREFIX}Renamed"
            assert sd.FindByName(f"{TEST_PREFIX}Renamed") is not None
            print(
                f"[INFO] post-state en={_raw(refetched.Name, en.Handle)!r} "
                f"default({default.Id})={_raw(refetched.Name, default.Handle)!r}"
            )
        finally:
            sd.Delete(custom)

    @pytest.mark.live_phase("SemanticDomainOperations", "update")
    def test_set_name_default_ws_is_read_back_by_default_get_name(self, sd_env):
        project, sd, _domain, default, en = sd_env
        custom = sd.Create(f"{TEST_PREFIX}Base", "900.605", wsHandle=en.Handle)
        try:
            sd.SetName(custom, f"{TEST_PREFIX}Default")  # no ws -> default WS
            refetched = sd.Find("900.605")
            assert _raw(refetched.Name, default.Handle) == f"{TEST_PREFIX}Default"
            assert _raw(refetched.Name, en.Handle) == f"{TEST_PREFIX}Base"
            # best-analysis prefers the default WS, so the write is visible
            assert sd.GetName(refetched) == f"{TEST_PREFIX}Default"
            assert sd.FindByName(f"{TEST_PREFIX}Default") is not None
            assert sd.FindByName(f"{TEST_PREFIX}Base") is not None
        finally:
            sd.Delete(custom)

    @pytest.mark.live_phase("SemanticDomainOperations", "create")
    def test_create_in_non_default_ws_is_findable_by_number_and_name(self, sd_env):
        project, sd, _domain, default, en = sd_env
        custom = sd.Create(f"{TEST_PREFIX}Findable", "900.606", wsHandle=en.Handle)
        try:
            assert sd.Find("900.606") is not None
            assert sd.GetNumber(custom) == "900.606"
            assert sd.FindByName(f"{TEST_PREFIX}Findable") is not None
            assert _raw(custom.Abbreviation, default.Handle) == ""
        finally:
            sd.Delete(custom)
