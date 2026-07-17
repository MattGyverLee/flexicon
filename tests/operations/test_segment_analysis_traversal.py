#
#   test_segment_analysis_traversal.py
#
#   Live-project regression tests for issue #212:
#   SegmentOperations.GetAnalyses returns polymorphic IAnalysis tokens; reading
#   a gloss/category off them without an explicit IWfiGloss cast silently
#   returned ''. These tests pin the new traversal helpers and the GetForm cast
#   fix against a real FieldWorks project.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import sys

import pytest


pytestmark = pytest.mark.requires_live_project

_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_project():
    try:
        from flexicon.code.FLExProject import FLExProject
    except Exception:
        return None
    project = FLExProject()
    for name in _CANDIDATE_PROJECTS:
        try:
            project.OpenProject(name, writeEnabled=False)
            return project
        except Exception:
            continue
    return None


@pytest.fixture(scope="module")
def live_project():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    project = _try_open_project()
    if project is None:
        pytest.skip(
            "No FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


def _class_name(obj):
    try:
        return obj.ClassName
    except Exception:
        return type(obj).__name__


@pytest.fixture(scope="module")
def analysis_tokens(live_project):
    """
    Scan the project's interlinear texts for a segment whose AnalysesRS
    contains at least one IWfiGloss token, and return a dict bucketing the
    segment's tokens by concrete ClassName (used by tests that need several
    token kinds co-located in the same segment). Skips if none is found.
    """
    project = live_project
    from SIL.LCModel import IStTxtPara

    buckets = {}
    for text in project.Texts.GetAll():
        contents = getattr(text, "ContentsOA", None)
        if contents is None:
            continue
        for raw_para in contents.ParagraphsOS:
            # ParagraphsOS yields base-typed IStPara; cast so SegmentsOS surfaces.
            para = IStTxtPara(raw_para)
            try:
                segments = list(project.Segments.GetAll(para))
            except Exception:
                continue
            for seg in segments:
                tokens = project.Segments.GetAnalyses(seg)
                if not tokens:
                    continue
                by_kind = {}
                for tok in tokens:
                    by_kind.setdefault(_class_name(tok), []).append(tok)
                if "WfiGloss" in by_kind:
                    return {
                        "segment": seg,
                        "tokens": tokens,
                        "by_kind": by_kind,
                    }
                # Remember any segment as a weak fallback for non-gloss checks.
                if not buckets:
                    buckets = {"segment": seg, "tokens": tokens, "by_kind": by_kind}

    if not buckets:
        pytest.skip("No segment with analyses found in candidate project")
    pytest.skip(
        "No fully-glossed (IWfiGloss) token found; interlinear text may be "
        "unglossed in this project"
    )


@pytest.fixture(scope="module")
def project_wide_tokens(live_project):
    """
    Scan every interlinear segment in the project and bucket ONE example
    token per concrete ClassName, project-wide (not restricted to a single
    segment). This is what lets the per-kind value-asserting tests below
    exercise all four legitimate IAnalysis kinds (IWfiWordform,
    IWfiAnalysis, IWfiGloss, IPunctuationForm) even when no single segment
    happens to contain all four together.
    """
    project = live_project
    from SIL.LCModel import IStTxtPara

    by_kind = {}
    for text in project.Texts.GetAll():
        contents = getattr(text, "ContentsOA", None)
        if contents is None:
            continue
        for raw_para in contents.ParagraphsOS:
            para = IStTxtPara(raw_para)
            try:
                segments = list(project.Segments.GetAll(para))
            except Exception:
                continue
            for seg in segments:
                tokens = project.Segments.GetAnalyses(seg)
                for tok in tokens:
                    kind = _class_name(tok)
                    by_kind.setdefault(kind, tok)
        # Early-exit once all four legitimate kinds have been seen.
        if {"WfiWordform", "WfiAnalysis", "WfiGloss", "PunctuationForm"} <= set(
            by_kind
        ):
            break

    if not by_kind:
        pytest.skip("No segment with analyses found in candidate project")
    return by_kind


def _token_for_kind(by_kind, kind, label):
    tok = by_kind.get(kind)
    if tok is None:
        pytest.skip(f"No {label} token found in candidate project")
    return tok


class TestSegmentGlossTraversal:
    """SegmentOperations.GetGloss + WfiGlosses.GetForm cast fix (issue #212)."""

    @pytest.mark.live_phase("SegmentOperations", "read")
    def test_get_gloss_returns_text_for_gloss_token(self, live_project, analysis_tokens):
        """GetGloss on an IWfiGloss token returns non-empty gloss text."""
        gloss_tok = analysis_tokens["by_kind"]["WfiGloss"][0]
        gloss = live_project.Segments.GetGloss(gloss_tok)
        assert isinstance(gloss, str)
        assert gloss != "", (
            "GetGloss returned '' for an IWfiGloss token -- the #212 "
            "silent-empty bug is not fixed"
        )

    @pytest.mark.live_phase("WfiGlossOperations", "read")
    def test_getform_casts_base_typed_gloss_token(self, live_project, analysis_tokens):
        """
        The regression: WfiGlosses.GetForm, given a gloss token exactly as
        GetAnalyses returns it (base IAnalysis-typed), must surface the real
        Form via the internal IWfiGloss cast -- not silently return ''.
        """
        gloss_tok = analysis_tokens["by_kind"]["WfiGloss"][0]
        form = live_project.WfiGlosses.GetForm(gloss_tok)
        assert isinstance(form, str)
        assert form != "", (
            "GetForm silently returned '' for an un-cast IWfiGloss token "
            "(issue #212 root cause)"
        )
        # And it agrees with the high-level SegmentOperations.GetGloss helper.
        assert form == live_project.Segments.GetGloss(gloss_tok)

    @pytest.mark.live_phase("WfiGlossOperations", "read")
    def test_getform_raises_on_non_gloss_token(self, live_project, analysis_tokens):
        """GetForm on a genuinely non-gloss token raises instead of returning ''."""
        from flexicon.code.exceptions import FP_ParameterError

        non_gloss_kinds = [
            k for k in analysis_tokens["by_kind"] if k != "WfiGloss"
        ]
        if not non_gloss_kinds:
            pytest.skip("Segment has only gloss tokens; no non-gloss to test")
        tok = analysis_tokens["by_kind"][non_gloss_kinds[0]][0]
        with pytest.raises(FP_ParameterError):
            live_project.WfiGlosses.GetForm(tok)

    @pytest.mark.live_phase("SegmentOperations", "read")
    def test_get_gloss_empty_for_non_gloss_token(self, live_project, analysis_tokens):
        """GetGloss returns '' (not an exception) for non-gloss tokens."""
        non_gloss_kinds = [
            k for k in analysis_tokens["by_kind"] if k != "WfiGloss"
        ]
        if not non_gloss_kinds:
            pytest.skip("Segment has only gloss tokens")
        tok = analysis_tokens["by_kind"][non_gloss_kinds[0]][0]
        assert live_project.Segments.GetGloss(tok) == ""


class TestAnalysisOwnerResolvingHelpers:
    """WfiAnalyses.GetCategoryAbbrev / GetMorphemeBundles owner-resolution."""

    @pytest.mark.live_phase("WfiAnalysisOperations", "read")
    def test_category_abbrev_resolves_owner_for_gloss_token(
        self, live_project, analysis_tokens
    ):
        """
        GetCategoryAbbrev on an IWfiGloss token resolves the owning
        IWfiAnalysis and returns its POS abbreviation as a string.
        """
        gloss_tok = analysis_tokens["by_kind"]["WfiGloss"][0]
        abbr = live_project.WfiAnalyses.GetCategoryAbbrev(gloss_tok)
        assert isinstance(abbr, str)

        # Cross-check against manual owner-chase + GetCategory + POS.GetAbbreviation.
        from SIL.LCModel import IWfiAnalysis

        owning = IWfiAnalysis(gloss_tok.Owner)
        expected = ""
        cat = owning.CategoryRA
        if cat is not None:
            expected = live_project.POS.GetAbbreviation(cat)
        assert abbr == expected

    @pytest.mark.live_phase("WfiAnalysisOperations", "read")
    def test_morpheme_bundles_resolves_owner_for_gloss_token(
        self, live_project, analysis_tokens
    ):
        """
        GetMorphemeBundles on an IWfiGloss token returns the owning analysis's
        MorphBundlesOS (a list), where the strict GetMorphBundles would need a
        manual owner cast.
        """
        gloss_tok = analysis_tokens["by_kind"]["WfiGloss"][0]
        bundles = live_project.WfiAnalyses.GetMorphemeBundles(gloss_tok)
        assert isinstance(bundles, list)

        from SIL.LCModel import IWfiAnalysis

        owning = IWfiAnalysis(gloss_tok.Owner)
        assert len(bundles) == owning.MorphBundlesOS.Count

    @pytest.mark.live_phase("WfiAnalysisOperations", "read")
    def test_helpers_graceful_on_non_analysis_token(
        self, live_project, analysis_tokens
    ):
        """Wordform / punctuation tokens yield '' / [] rather than raising."""
        non_gloss_kinds = [
            k
            for k in analysis_tokens["by_kind"]
            if k in ("WfiWordform", "PunctuationForm")
        ]
        if not non_gloss_kinds:
            pytest.skip("No wordform/punctuation token available")
        tok = analysis_tokens["by_kind"][non_gloss_kinds[0]][0]
        assert live_project.WfiAnalyses.GetCategoryAbbrev(tok) == ""
        assert live_project.WfiAnalyses.GetMorphemeBundles(tok) == []


class TestAllFourTokenKindsGlossAndCategory:
    """
    Explicit value-asserting coverage for GetGloss / GetCategoryAbbrev /
    GetMorphemeBundles across each of the FOUR legitimate concrete kinds
    that can appear in ISegment.AnalysesRS (domain report cycle1-domain-212,
    section 1 / Recommendation 4): IWfiWordform, IWfiAnalysis, IWfiGloss,
    IPunctuationForm. Each test picks one real example of its kind
    project-wide via ``project_wide_tokens`` rather than assuming any single
    segment contains all four, and skips (rather than fails) if the sample
    project has none of that kind.
    """

    @pytest.mark.live_phase("SegmentOperations", "read")
    def test_wordform_token_has_no_gloss_no_category_no_bundles(
        self, live_project, project_wide_tokens
    ):
        tok = _token_for_kind(project_wide_tokens, "WfiWordform", "IWfiWordform")
        assert live_project.Segments.GetGloss(tok) == ""
        assert live_project.WfiAnalyses.GetCategoryAbbrev(tok) == ""
        assert live_project.WfiAnalyses.GetMorphemeBundles(tok) == []

    @pytest.mark.live_phase("SegmentOperations", "read")
    def test_punctuation_token_has_no_gloss_no_category_no_bundles(
        self, live_project, project_wide_tokens
    ):
        tok = _token_for_kind(
            project_wide_tokens, "PunctuationForm", "IPunctuationForm"
        )
        # Must not crash: punctuation is a legitimate IAnalysis member, not
        # an error case (domain report section 4).
        assert live_project.Segments.GetGloss(tok) == ""
        assert live_project.WfiAnalyses.GetCategoryAbbrev(tok) == ""
        assert live_project.WfiAnalyses.GetMorphemeBundles(tok) == []

    @pytest.mark.live_phase("SegmentOperations", "read")
    def test_bare_analysis_token_has_no_gloss_but_may_have_category(
        self, live_project, project_wide_tokens
    ):
        """
        IWfiAnalysis (analyzed, not yet glossed): gloss is always '', but
        category/morph bundles come straight from the analysis itself (no
        owner-resolution needed) and must match direct LCM access.
        """
        tok = _token_for_kind(project_wide_tokens, "WfiAnalysis", "IWfiAnalysis")
        assert live_project.Segments.GetGloss(tok) == ""

        from SIL.LCModel import IWfiAnalysis

        concrete = IWfiAnalysis(tok)
        expected_abbr = ""
        if concrete.CategoryRA is not None:
            expected_abbr = live_project.POS.GetAbbreviation(concrete.CategoryRA)
        assert live_project.WfiAnalyses.GetCategoryAbbrev(tok) == expected_abbr

        bundles = live_project.WfiAnalyses.GetMorphemeBundles(tok)
        assert isinstance(bundles, list)
        assert len(bundles) == concrete.MorphBundlesOS.Count

    @pytest.mark.live_phase("SegmentOperations", "read")
    def test_gloss_token_gloss_and_category_match_owning_analysis(
        self, live_project, project_wide_tokens
    ):
        """
        IWfiGloss: gloss text comes from the gloss itself; category is
        inherited from the OWNING IWfiAnalysis.CategoryRA (never
        gloss.CategoryRA, which raises AttributeError in pythonnet --
        domain report section 4).
        """
        tok = _token_for_kind(project_wide_tokens, "WfiGloss", "IWfiGloss")

        gloss_text = live_project.Segments.GetGloss(tok)
        assert isinstance(gloss_text, str)
        assert gloss_text != ""
        assert gloss_text == live_project.WfiGlosses.GetForm(tok)

        from SIL.LCModel import IWfiAnalysis

        owning = IWfiAnalysis(tok.Owner)
        expected_abbr = ""
        if owning.CategoryRA is not None:
            expected_abbr = live_project.POS.GetAbbreviation(owning.CategoryRA)
        assert live_project.WfiAnalyses.GetCategoryAbbrev(tok) == expected_abbr

        bundles = live_project.WfiAnalyses.GetMorphemeBundles(tok)
        assert len(bundles) == owning.MorphBundlesOS.Count

        # Never write to bundle.SenseRA.Gloss -- read-only spot check only.
        for mb in bundles:
            assert mb is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
