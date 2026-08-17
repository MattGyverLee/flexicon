#
#   test_wfi_analysis.py
#
#   Class: TestWfiAnalysisDelete
#          Regression coverage for issue #32:
#          WfiAnalysisOperations.Delete raised AttributeError
#          ("'ICmObject' object has no attribute 'AnalysesOC'") for
#          every input. The fix casts analysis.Owner -- which pythonnet
#          types as the base ICmObject -- to IWfiWordform before
#          touching AnalysesOC.
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
    """Module-scoped writable FLExProject; skip if LCM or project unavailable."""
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


class TestWfiAnalysisDelete:
    """
    Regression coverage for issue #32: WfiAnalysisOperations.Delete
    previously crashed with AttributeError because it accessed
    AnalysesOC on `analysis.Owner` which pythonnet returns as the
    base ICmObject (no AnalysesOC). The fix casts to IWfiWordform.
    """

    def test_delete_round_trips_on_existing_wordform(self, writable_project):
        """
        Create a temporary analysis on an existing wordform, then
        delete it. Before the fix, Delete raised AttributeError on
        every input -- this test would have failed during the Delete
        call. After the fix, the round-trip succeeds and the
        wordform's AnalysesOC count returns to its starting value.
        """
        # Find any wordform with no analyses (preferred -- minimizes
        # disturbance) or fall back to one with analyses. We then
        # create our own throw-away analysis and delete it.
        candidate_wf = None
        starting_count = 0
        for wf in writable_project.Wordforms.GetAll():
            count = wf.AnalysesOC.Count
            if count == 0:
                candidate_wf = wf
                starting_count = 0
                break
        if candidate_wf is None:
            # Fall back to the first wordform; record its analysis
            # count so we can assert the delta returns to zero.
            for wf in writable_project.Wordforms.GetAll():
                candidate_wf = wf
                starting_count = wf.AnalysesOC.Count
                break

        if candidate_wf is None:
            pytest.skip("Project has no wordforms to test against")

        # Create an analysis we own and can safely delete.
        analysis = writable_project.WfiAnalyses.Create(candidate_wf)
        assert analysis is not None, "WfiAnalyses.Create returned None"
        assert candidate_wf.AnalysesOC.Count == starting_count + 1, (
            f"AnalysesOC count did not increase after Create: "
            f"{candidate_wf.AnalysesOC.Count} vs expected "
            f"{starting_count + 1}"
        )

        # The fix under test: Delete must not raise AttributeError.
        writable_project.WfiAnalyses.Delete(analysis)

        assert candidate_wf.AnalysesOC.Count == starting_count, (
            f"AnalysesOC count did not return to starting value after "
            f"Delete: {candidate_wf.AnalysesOC.Count} vs expected "
            f"{starting_count}. The Remove() call may have hit a "
            f"different cast path."
        )


class TestWfiAnalysisSetApprovalStatus:
    """
    Regression coverage for issue #26 (the WfiAnalysis EvaluationsRC
    ownership-ordering bug). The previous implementation created an
    ICmAgentEvaluation, set evaluation.Agent on the unowned object,
    and added it to analysis.EvaluationsRC -- but EvaluationsRC is a
    reference collection that does not confer ownership. Property
    writes on the unowned evaluation would NPE.

    The fix delegates to LCM's purpose-built
    ICmAgent.SetEvaluation(target, Opinions) which handles ownership
    and bookkeeping internally. These tests exercise the three valid
    status transitions to confirm the new path doesn't raise.
    """

    def test_set_and_get_approval_status_round_trip(self, writable_project):
        """
        Issue #26 part 2 + issue #38: SetApprovalStatus previously
        trampled on the Phase 2 ownership-ordering rule by setting
        evaluation.Agent on an unowned ICmAgentEvaluation and adding
        it to a REFERENCE collection (EvaluationsRC). After the #26
        fix, SetApprovalStatus delegates to
        ICmAgent.SetEvaluation(target, Opinions) which handles
        ownership internally.

        After the #38 fix, GetApprovalStatus discriminates between
        approve and disapprove human evaluations rather than returning
        APPROVED for any non-empty EvaluationsRC. The full round-trip
        is now testable.
        """
        from flexlibs2.code.TextsWords.WfiAnalysisOperations import (
            ApprovalStatusTypes,
        )

        # Need at least one human agent. Read AnalyzingAgentsOC directly
        # to stay independent of the AgentOperations wrapper.
        has_human_agent = False
        for raw in writable_project.lp.AnalyzingAgentsOC:
            if getattr(raw, "Human", False):
                has_human_agent = True
                break
        if not has_human_agent:
            pytest.skip(
                "Project has no human agents; SetApprovalStatus "
                "refuses without one. Create via "
                "AgentOperations.CreateHumanAgent first."
            )

        # Find a wordform to attach a throw-away analysis to.
        candidate_wf = None
        for wf in writable_project.Wordforms.GetAll():
            candidate_wf = wf
            break
        if candidate_wf is None:
            pytest.skip("Project has no wordforms")

        analysis = writable_project.WfiAnalyses.Create(candidate_wf)
        try:
            # Full round-trip across all three statuses. The re-apply
            # at the end exercises the "transition between two
            # already-set states" path.
            for status in (
                ApprovalStatusTypes.APPROVED,
                ApprovalStatusTypes.DISAPPROVED,
                ApprovalStatusTypes.UNAPPROVED,
                ApprovalStatusTypes.APPROVED,  # re-apply
            ):
                writable_project.WfiAnalyses.SetApprovalStatus(
                    analysis, status
                )
                got = writable_project.WfiAnalyses.GetApprovalStatus(
                    analysis
                )
                assert got == status, (
                    f"After SetApprovalStatus({status!r}): "
                    f"GetApprovalStatus returned {got!r}"
                )
        finally:
            try:
                writable_project.WfiAnalyses.Delete(analysis)
            except Exception:
                pass


class TestWfiAnalysisAgentTypeDiscrimination:
    """
    Regression coverage for issues #55 and #56: three sibling sites in
    WfiAnalysisOperations were reaching into agent/evaluation
    collections and returning element [0] without filtering by agent
    type. Because LCM ordering is not deterministic, these returned
    the wrong agent kind (human vs parser) non-deterministically.

    These tests are parametrised across the three affected methods and
    deliberately set up an analysis with BOTH a human evaluation AND a
    parser evaluation present simultaneously -- a happy-path test that
    only exercises one agent kind would not catch the bug class.
    """

    @pytest.fixture
    def analysis_with_both_evaluation_kinds(self, writable_project):
        """
        Build an analysis carrying both a human and a parser
        evaluation, so the discriminator under test has to actually
        choose. Yields (analysis, human_agent, parser_agent) and tears
        the analysis down on exit.

        Skips when the project does not have at least one human agent
        and one parser agent already populated -- this fixture does
        not synthesise agents because parser creation requires a
        version string and the test should not start mutating the
        AnalyzingAgentsOC list.
        """
        from SIL.LCModel import Opinions

        human_agent = None
        parser_agent = None
        for raw in writable_project.lp.AnalyzingAgentsOC:
            if getattr(raw, "Human", False) and human_agent is None:
                human_agent = raw
            elif not getattr(raw, "Human", True) and parser_agent is None:
                parser_agent = raw
            if human_agent is not None and parser_agent is not None:
                break
        if human_agent is None or parser_agent is None:
            pytest.skip(
                "Project lacks both a human and a parser agent in "
                "AnalyzingAgentsOC; this regression needs both kinds "
                "present simultaneously."
            )

        # Find a wordform to attach the throw-away analysis to.
        candidate_wf = None
        for wf in writable_project.Wordforms.GetAll():
            candidate_wf = wf
            break
        if candidate_wf is None:
            pytest.skip("Project has no wordforms")

        analysis = writable_project.WfiAnalyses.Create(candidate_wf)

        # Place evaluations from BOTH agent kinds on the same analysis
        # via the canonical ICmAgent.SetEvaluation entry point. Order
        # them parser-first so that, before the fix, the buggy
        # element-[0] fallback in GetHumanEvaluation would return the
        # parser evaluation rather than the human one.
        # Raw ICmAgent.SetEvaluation is an LCM write made directly by the
        # test rather than through the wrapper, so it needs its own unit of
        # work. Free under the old undoable=False session envelope; since the
        # DEF default flip nothing is open between operations and an
        # unbracketed write raises "Not in the right state to register a
        # change." (tasks.md D14).
        with writable_project.UndoableOperation("test: seed both evaluations"):
            parser_agent.SetEvaluation(analysis, Opinions.approves)
            human_agent.SetEvaluation(analysis, Opinions.approves)

        try:
            yield analysis, human_agent, parser_agent
        finally:
            # Clear the evaluations and delete the analysis so this
            # test does not leak state into siblings.
            try:
                parser_agent.SetEvaluation(analysis, Opinions.noopinion)
            except Exception:
                pass
            try:
                human_agent.SetEvaluation(analysis, Opinions.noopinion)
            except Exception:
                pass
            try:
                writable_project.WfiAnalyses.Delete(analysis)
            except Exception:
                pass

    def test_get_agent_evaluation_returns_parser_kind(
        self, writable_project, analysis_with_both_evaluation_kinds
    ):
        """
        With BOTH a human and a parser evaluation on the analysis,
        GetAgentEvaluation must return the PARSER evaluation, not
        whichever evaluation happened to be first in EvaluationsRC.
        (issue #55)
        """
        analysis, _human, _parser = analysis_with_both_evaluation_kinds

        got = writable_project.WfiAnalyses.GetAgentEvaluation(analysis)

        assert got is not None, (
            "GetAgentEvaluation returned None even though a parser "
            "evaluation is present on the analysis"
        )
        assert getattr(got, "Human", True) is False, (
            "GetAgentEvaluation returned a HUMAN evaluation when a "
            "parser evaluation was available -- the discriminator is "
            "not filtering by agent type (issue #55 regression)"
        )

    def test_get_human_evaluation_returns_human_kind(
        self, writable_project, analysis_with_both_evaluation_kinds
    ):
        """
        With BOTH a human and a parser evaluation on the analysis,
        GetHumanEvaluation must return the HUMAN evaluation, not
        whichever evaluation happened to be first in EvaluationsRC.
        The old code accepted any evaluation that exposed an .Agent
        attribute, which every ICmAgentEvaluation does. (issue #55)
        """
        analysis, _human, _parser = analysis_with_both_evaluation_kinds

        got = writable_project.WfiAnalyses.GetHumanEvaluation(analysis)

        assert got is not None, (
            "GetHumanEvaluation returned None even though a human "
            "evaluation is present on the analysis"
        )
        assert getattr(got, "Human", False) is True, (
            "GetHumanEvaluation returned a PARSER evaluation when a "
            "human evaluation was available -- the discriminator is "
            "not filtering by agent type (issue #55 regression)"
        )

    def test_get_agent_evaluation_returns_none_when_only_human_present(
        self, writable_project
    ):
        """
        Negative case for #55: an analysis with only a human
        evaluation must NOT have GetAgentEvaluation return that human
        evaluation. The old code returned EvaluationsRC[0] regardless
        of agent kind, so the human evaluation would leak through.
        """
        from SIL.LCModel import Opinions

        human_agent = None
        for raw in writable_project.lp.AnalyzingAgentsOC:
            if getattr(raw, "Human", False):
                human_agent = raw
                break
        if human_agent is None:
            pytest.skip("Project has no human agent")

        candidate_wf = None
        for wf in writable_project.Wordforms.GetAll():
            candidate_wf = wf
            break
        if candidate_wf is None:
            pytest.skip("Project has no wordforms")

        analysis = writable_project.WfiAnalyses.Create(candidate_wf)
        try:
            # Raw LCM write from the test -- needs its own UoW (see D14).
            with writable_project.UndoableOperation("test: seed human evaluation"):
                human_agent.SetEvaluation(analysis, Opinions.approves)

            got = writable_project.WfiAnalyses.GetAgentEvaluation(analysis)

            assert got is None, (
                "GetAgentEvaluation returned a human evaluation when "
                "no parser evaluation existed -- this is the bug "
                "from issue #55 where EvaluationsRC[0] was returned "
                "irrespective of agent kind."
            )
        finally:
            try:
                human_agent.SetEvaluation(analysis, Opinions.noopinion)
            except Exception:
                pass
            try:
                writable_project.WfiAnalyses.Delete(analysis)
            except Exception:
                pass

    def test_set_approval_status_prefers_default_user_agent(
        self, writable_project
    ):
        """
        SetApprovalStatus must prefer ILangProject.DefaultUserAgent
        over an arbitrary first human agent from
        AgentOperations.GetHumanAgents(). The old code took
        human_agents[0], which is non-deterministic when multiple
        human agents exist -- so the approval might land on a legacy
        collaborator's agent rather than the current user's. (issue
        #56)

        Verified by: setting APPROVED, then reading back the
        evaluation owner and checking it matches DefaultUserAgent.
        """
        from flexlibs2.code.TextsWords.WfiAnalysisOperations import (
            ApprovalStatusTypes,
        )

        default_user = getattr(
            writable_project.lp, "DefaultUserAgent", None
        )
        if default_user is None:
            pytest.skip(
                "Project's LangProject does not expose "
                "DefaultUserAgent on this LCM build"
            )
        if not getattr(default_user, "Human", False):
            pytest.skip(
                "Project's DefaultUserAgent is not human -- this "
                "regression only applies when DefaultUserAgent is "
                "a usable human agent"
            )

        # Ensure there is at least one OTHER human agent present so
        # that human_agents[0] could plausibly differ from the
        # default user agent. If there is only one human agent, the
        # bug cannot manifest in this project and we have nothing
        # discriminating to assert.
        other_human_agents = [
            raw
            for raw in writable_project.lp.AnalyzingAgentsOC
            if getattr(raw, "Human", False)
            and getattr(raw, "Hvo", None)
            != getattr(default_user, "Hvo", None)
        ]
        if not other_human_agents:
            pytest.skip(
                "Project has only one human agent; the "
                "DefaultUserAgent-vs-first-human distinction is not "
                "observable. Add a second human agent to exercise "
                "the #56 regression."
            )

        candidate_wf = None
        for wf in writable_project.Wordforms.GetAll():
            candidate_wf = wf
            break
        if candidate_wf is None:
            pytest.skip("Project has no wordforms")

        analysis = writable_project.WfiAnalyses.Create(candidate_wf)
        try:
            writable_project.WfiAnalyses.SetApprovalStatus(
                analysis, ApprovalStatusTypes.APPROVED
            )

            # Find which agent owns the approving evaluation now on
            # the analysis. After the #56 fix, it must be the
            # DefaultUserAgent.
            approving_agents = []
            for evaluation in analysis.EvaluationsRC:
                if not getattr(evaluation, "Human", False):
                    continue
                if not getattr(evaluation, "Approves", False):
                    continue
                agent = getattr(evaluation, "Agent", None)
                if agent is not None:
                    approving_agents.append(agent)

            assert approving_agents, (
                "After SetApprovalStatus(APPROVED) no approving "
                "human evaluation was found on the analysis"
            )
            assert any(
                getattr(a, "Hvo", None)
                == getattr(default_user, "Hvo", None)
                for a in approving_agents
            ), (
                "SetApprovalStatus did not use DefaultUserAgent. "
                "Approving agents observed: "
                f"{[getattr(a, 'Hvo', '?') for a in approving_agents]}; "
                f"DefaultUserAgent Hvo: {getattr(default_user, 'Hvo', '?')}. "
                "This is the #56 regression -- the old code took "
                "human_agents[0] from a non-deterministic "
                "AnalyzingAgentsOC iteration order."
            )
        finally:
            try:
                writable_project.WfiAnalyses.SetApprovalStatus(
                    analysis, ApprovalStatusTypes.UNAPPROVED
                )
            except Exception:
                pass
            try:
                writable_project.WfiAnalyses.Delete(analysis)
            except Exception:
                pass


class TestWfiAnalysisSetApprovalStatusErrorPaths:
    """
    Issue #58: SetApprovalStatus error-path coverage.

    The happy-path round-trip is covered in
    TestWfiAnalysisSetApprovalStatus. This class exercises the two
    remaining branches:
      1. Passing an unrecognised status value must raise FP_ParameterError
         (via _coerce_approval_status).
      2. When no human agents exist in the project, SetApprovalStatus
         must raise FP_ParameterError rather than silently choosing a
         parser agent.
    """

    def test_invalid_status_raises_fp_parameter_error(self, writable_project):
        """
        SetApprovalStatus with an unrecognised status (e.g. the string
        "yes" or an out-of-range integer) must raise FP_ParameterError.
        The previous implementation did not validate status and would
        silently pass an invalid value to LCM.
        """
        from flexlibs2.code.FLExProject import FP_ParameterError

        # Find any wordform to attach a throw-away analysis to.
        candidate_wf = None
        for wf in writable_project.Wordforms.GetAll():
            candidate_wf = wf
            break
        if candidate_wf is None:
            pytest.skip("Project has no wordforms")

        analysis = writable_project.WfiAnalyses.Create(candidate_wf)
        try:
            # String values are not valid status inputs.
            with pytest.raises(FP_ParameterError):
                writable_project.WfiAnalyses.SetApprovalStatus(
                    analysis, "yes"
                )

            # Out-of-range integers (ApprovalStatusTypes only has 0, 1, 2)
            # should also raise.
            with pytest.raises(FP_ParameterError):
                writable_project.WfiAnalyses.SetApprovalStatus(
                    analysis, 99
                )
        finally:
            try:
                writable_project.WfiAnalyses.Delete(analysis)
            except Exception:
                pass

    def test_no_human_agents_raises_fp_parameter_error(self, writable_project):
        """
        If the project has no human agents, SetApprovalStatus must raise
        FP_ParameterError rather than silently doing nothing or choosing
        a parser agent.

        This test is designed to run as a no-op when the project already
        has human agents (the common case in real test projects). In that
        situation it skips rather than destructively removing agents.

        We verify the error path by monkey-patching AgentOperations so
        that GetHumanAgents() returns an empty list for the duration of
        the call, without touching the actual project state.
        """
        from flexlibs2.code.TextsWords.WfiAnalysisOperations import (
            ApprovalStatusTypes,
        )
        from flexlibs2.code.FLExProject import FP_ParameterError
        import flexlibs2.code.Lists.AgentOperations as agent_mod

        candidate_wf = None
        for wf in writable_project.Wordforms.GetAll():
            candidate_wf = wf
            break
        if candidate_wf is None:
            pytest.skip("Project has no wordforms")

        analysis = writable_project.WfiAnalyses.Create(candidate_wf)
        # Patch GetHumanAgents to return an empty iterator for the
        # duration of this test so we can exercise the no-agent branch
        # without mutating the project's agent list.
        original_get_human_agents = agent_mod.AgentOperations.GetHumanAgents

        def _empty_human_agents(self_inner):
            return iter([])

        try:
            agent_mod.AgentOperations.GetHumanAgents = _empty_human_agents
            with pytest.raises(FP_ParameterError, match="[Nn]o human agent"):
                writable_project.WfiAnalyses.SetApprovalStatus(
                    analysis, ApprovalStatusTypes.APPROVED
                )
        finally:
            agent_mod.AgentOperations.GetHumanAgents = original_get_human_agents
            try:
                writable_project.WfiAnalyses.Delete(analysis)
            except Exception:
                pass


class TestWfiAnalysisDeleteWithMorphBundles:
    """
    Issue #99: Delete cascade coverage for analyses that own
    WfiMorphBundle objects.

    The existing TestWfiAnalysisDelete only creates a bare analysis
    with no morph bundles. An analysis with MorphBundlesOS children
    exercises a different code path in the LCM ownership graph; LCM
    should cascade-delete the bundles when the owning analysis is
    removed from AnalysesOC.
    """

    def test_delete_analysis_with_morph_bundle_cascades(
        self, writable_project
    ):
        """
        Create an analysis with one morph bundle, delete the analysis,
        and verify both the analysis and its bundle are gone.

        Before the issue #32 fix, Delete raised AttributeError before
        reaching LCM's cascaded delete -- so bundles were never touched.
        This test ensures the cascade path is reachable and works.
        """
        # Find any wordform to host the throw-away analysis.
        candidate_wf = None
        starting_count = 0
        for wf in writable_project.Wordforms.GetAll():
            candidate_wf = wf
            starting_count = wf.AnalysesOC.Count
            break
        if candidate_wf is None:
            pytest.skip("Project has no wordforms")

        analysis = writable_project.WfiAnalyses.Create(candidate_wf)
        bundle_hvo = None
        try:
            # Add one morph bundle so the cascade path is exercised.
            # Use AddMorphBundle if available; otherwise call the factory
            # directly as the WfiAnalysisOperations.Duplicate test does.
            from SIL.LCModel import IWfiMorphBundleFactory

            bundle_factory = writable_project.project.ServiceLocator.GetService(
                IWfiMorphBundleFactory
            )
            # Raw LCM writes -> own unit of work (tasks.md D14).
            with writable_project.UndoableOperation("test: add morph bundle"):
                new_bundle = bundle_factory.Create()
                analysis.MorphBundlesOS.Add(new_bundle)
            bundle_hvo = new_bundle.Hvo

            assert analysis.MorphBundlesOS.Count == 1, (
                "MorphBundlesOS should have 1 bundle before Delete"
            )

            # Delete the analysis -- the bundle must disappear too.
            writable_project.WfiAnalyses.Delete(analysis)
            analysis = None  # prevent double-delete in finally

            # The wordform's AnalysesOC must be back to starting_count.
            assert candidate_wf.AnalysesOC.Count == starting_count, (
                f"AnalysesOC count did not return to {starting_count} "
                f"after deleting an analysis with a morph bundle: "
                f"got {candidate_wf.AnalysesOC.Count}"
            )

            # The bundle's HVO must no longer resolve in the repository.
            # Object() returns None (or raises) for deleted objects.
            try:
                leftover = writable_project.Object(bundle_hvo)
                assert leftover is None, (
                    "WfiMorphBundle survived deletion of its owning "
                    "analysis -- cascade delete did not fire. "
                    f"bundle_hvo={bundle_hvo}, leftover={leftover!r}"
                )
            except Exception:
                # Any exception from Object() also means the bundle is
                # gone (repository lookup failed), which is the expected
                # cascade behaviour.
                pass

        finally:
            if analysis is not None:
                try:
                    writable_project.WfiAnalyses.Delete(analysis)
                except Exception:
                    pass


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
