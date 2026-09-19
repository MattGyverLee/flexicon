#
#   test_parser_live.py
#
#   Tier A3 -- CP2a T018/T019/T020. The LIVE half of the parser evidence,
#   run against real installed FieldWorks projects with a real grammar.
#
#     A3.1 (T018)  The parser constructs against a real cache and a real
#                  update loads a grammar.
#     A3.2 (T018)  A word parses and a trace returns.
#     A3.3 (T019)  THE GATE WITHIN THE GATE. With no model change between
#                  calls, the plain update does NOT reload and the reload
#                  DOES. A reload that cannot be shown to discard has not
#                  been proven, and CP2b does not start.
#     A3.4 (T018)  FR-010 -- plain-parse results carry live object
#                  references, not strings.
#     A3.5 (T020)  SC-014/SC-015 -- at most one grammar held, released on
#                  a project switch, and no parse served from a grammar
#                  whose currency was not confirmed.
#     A3.6 (T018)  The active parser is the expected engine on both live
#                  projects.
#
#   READ-ONLY, AND THAT IS WHY IT NEEDS NO HUMAN AT THE KEYBOARD. Every
#   project here is opened with writeEnabled=False. Nothing is written,
#   nothing is restored, and there is no sandbox to clean up -- which is
#   what lets this tier run unattended. The live half of FR-043's stale
#   branch WOULD need a write (something must change the model to make the
#   grammar stale on purpose), and it is therefore NOT here: it is tier A4,
#   deferred to CP2b with needs_human (escalation E-D).
#
#   INSTALLED PROJECTS ONLY, NEVER A .fwbackup SANDBOX. Opening a sandbox
#   read-only triggers a modal liblcm dialog that freezes the suite. These
#   two projects are opened in place.
#
#   Required invocation (Constitution Principle II):
#
#       $env:FLEXLIBS_REQUIRE_LIVE = "1"
#       python -m pytest tests/operations/test_parser_live.py \
#           -m requires_live_project -q
#
#   FLEXLIBS_REQUIRE_LIVE=1 turns silent mock degradation into a usage
#   error, so a run that quietly fell back to mocks cannot be mistaken for
#   live evidence. Confirm tests/live_status.json shows "run_mode": "live"
#   before recording anything from this file.
#
#   Platform: Python.NET, Windows, FieldWorks 9 installed.
#
#   Copyright 2026
#

import os
import sys

import pytest


pytestmark = pytest.mark.requires_live_project


# The two projects named in the spec's Verbatim Constraints, both confirmed
# installed under C:\ProgramData\SIL\FieldWorks\Projects. IndonesianHC is the
# primary target: 41 entries and 3 phonological rules, small enough that a
# cold grammar load stays fast. Malay is the second project A3.5 switches to.
PRIMARY_PROJECT = "IndonesianHC-Complete"
SECONDARY_PROJECT = "Malay Parsing-20230810withHC"

# Both are configured for HermitCrab. Sena 3 is XAmple with 0 phonological
# rules and was ruled out as a verification target for exactly that reason.
EXPECTED_ENGINE = "HC"

# A word the primary lexicon can actually be asked about.
#
# IndonesianHC-Complete stores its lexeme forms in IPA, not in orthography,
# so an orthographic probe returns zero analyses and A3.4 has nothing to
# inspect. This is "manis" as that project actually spells it: m + U+0251
# (LATIN SMALL LETTER ALPHA) + n + i + s. Written as an escape rather than
# literally so this file stays pure ASCII.
#
# Chosen by enumerating the project's 41 entries and parsing each: all 41
# parse, each with exactly one analysis, so this is representative rather
# than a lucky pick.
#
# Most assertions below deliberately do NOT require a successful parse --
# whether a given form parses is a property of someone's linguistic data,
# not of this facade, and pinning it would make the suite fail when a
# linguist edits their own project. A3.4 is the exception: it needs a real
# analysis to inspect, and it skips (loudly, naming the word and project)
# rather than failing if the data ever stops providing one.
PROBE_WORD = "m\u0251nis"


def _open(name):
    """Open an installed project read-only, or skip with the reason."""
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    try:
        from flexicon.code.FLExProject import FLExProject
    except Exception as exc:
        pytest.skip("flexicon could not be imported: %s" % exc)

    project = FLExProject()
    try:
        project.OpenProject(name, writeEnabled=False)
    except Exception as exc:
        pytest.skip("%s could not be opened read-only: %s" % (name, exc))
    return project


@pytest.fixture(scope="module")
def primary():
    project = _open(PRIMARY_PROJECT)
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


@pytest.fixture(scope="module")
def secondary():
    project = _open(SECONDARY_PROJECT)
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


@pytest.fixture(scope="module")
def available_parser(primary):
    """The primary project's parser area, or a skip naming why not."""
    status = primary.Parser.GetAvailability()
    if not status.available:
        pytest.skip("parser unavailable: %s" % status.reason)
    return primary.Parser


# ---------------------------------------------------------------------------
# The A3.3 witness (D-A11)
# ---------------------------------------------------------------------------
#
# HCParser.LoadParser() REPLACES the private m_morpher instance. So the
# identity of that instance across two calls is a direct witness of whether
# the grammar was actually reloaded:
#
#     same instance  -> LoadParser() did not run -> nothing was discarded
#     new instance   -> LoadParser() ran         -> the grammar was discarded
#
# Reading a private field is acceptable HERE and nowhere else: this is a test
# whose whole job is to witness an internal effect that has no public
# signal, and it says so. It is unacceptable in shipped code, and none of
# flexicon/code/Parser/ does it.
#
# WHY NOT TIME IT. Elapsed time is a correlation, not a witness. A small
# grammar on a warm cache reloads fast enough that a threshold either passes
# a no-op or fails a real reload, depending on the machine. The documented
# fallback, if the private read proves unreliable, is the rewrite of the
# {ProjectName}HCLoadErrors.xml side file, which CP1 already treats as the
# load signal -- implemented below and used only if the field read fails.

MORPHER_FIELD = "m_morpher"


def _morpher_identity(handle):
    """The identity of the parser's internal morpher, or None if unreadable."""
    try:
        from System.Reflection import BindingFlags

        field = handle.GetType().GetField(MORPHER_FIELD, BindingFlags.NonPublic | BindingFlags.Instance)
        if field is None:
            return None
        value = field.GetValue(handle)
        if value is None:
            return None
        # Identity, not equality: two distinct Morpher objects built from the
        # same model would compare equal on any value-based comparison.
        import System

        return System.Runtime.CompilerServices.RuntimeHelpers.GetHashCode(value)
    except Exception:
        return None


def _load_errors_side_file(handle, project):
    """Where the component writes its HC load-errors side file, if anywhere.

    Located from the component's source rather than guessed --
    ParserCore/HCParser.cs:152 builds it as

        Path.Combine(m_outputDirectory, m_cache.ProjectId.Name + "HCLoadErrors.xml")

    and `m_outputDirectory` is NOT the project directory: on this machine it
    resolves to the user's temp directory. An earlier version of this helper
    looked under FWProjectsDir and therefore always returned None, which made
    the "documented fallback" below unrunnable -- a stated guarantee that
    could not execute. Reading the field is the same private read that
    `_morpher_identity` justifies above, and for the same reason: there is no
    public signal for it.
    """
    try:
        from System.Reflection import BindingFlags

        field = handle.GetType().GetField("m_outputDirectory", BindingFlags.NonPublic | BindingFlags.Instance)
        outdir = field.GetValue(handle) if field is not None else None
        if not outdir:
            return None
        candidate = os.path.join(str(outdir), "%sHCLoadErrors.xml" % project.ProjectName())
        return candidate if os.path.exists(candidate) else None
    except Exception:
        return None


def _load_errors_mtime(handle, project):
    """Fallback witness: the mtime of the HC load-errors side file."""
    path = _load_errors_side_file(handle, project)
    if path is None:
        return None
    try:
        return os.path.getmtime(path)
    except Exception:
        return None


# ---------------------------------------------------------------------------
# A3.1 / A3.2 / A3.4 / A3.6 -- T018
# ---------------------------------------------------------------------------


class TestA31ConstructsAndLoads:
    """A3.1 -- a real cache, a real parser, a real grammar."""

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_availability_is_reported_available_on_a_real_install(self, primary):
        status = primary.Parser.GetAvailability()
        assert status.available, "parser reported unavailable on a live install: %s" % status.reason
        assert status.version, "available but no version was detected"
        assert status.reason == "", "available with a non-empty reason: %r" % status.reason

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_the_grammar_loads_and_the_parser_reports_itself_current(self, available_parser):
        """Constructing and updating must leave a grammar that is current."""
        assert available_parser.IsUpToDate() is True, (
            "the parser reports its grammar stale immediately after loading it. "
            "Either the update did not run or the change listener is not being "
            "cleared -- both make SC-015 unmeetable, since every parse would "
            "reload."
        )


class TestA32ParseAndTrace:
    """A3.2 -- a word parses and a trace returns."""

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_a_word_parses(self, available_parser):
        result = available_parser.ParseWord(PROBE_WORD)
        assert result is not None, "ParseWord returned nothing for %r" % PROBE_WORD
        assert hasattr(result, "Analyses"), (
            "the plain parse did not return a result carrying Analyses; got %r. "
            "FR-010 depends on this being the parser's own result object, not "
            "a rendering of it." % type(result)
        )

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_the_structured_parse_returns_a_document(self, available_parser):
        doc = available_parser.ParseWordXml(PROBE_WORD)
        assert doc is not None and doc.Root is not None, "ParseWordXml returned no document"

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_an_unrestricted_trace_returns_a_document(self, available_parser):
        doc = available_parser.TraceWordXml(PROBE_WORD)
        assert doc is not None and doc.Root is not None, "TraceWordXml returned no document"

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_an_empty_restriction_is_refused(self, available_parser):
        """An empty restriction is a caller error, not "no restriction".

        The component branches on `selectTraceMorphs != null`, so a null
        reopens its selectors while an EMPTY array installs a filter that
        admits nothing. Reading empty as "unrestricted" would be a guess,
        and it would be the wrong one -- verified live, below.
        """
        from flexicon.code.exceptions import FP_ParameterError

        with pytest.raises(FP_ParameterError):
            available_parser.TraceWordXml(PROBE_WORD, [])

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_a_restricted_trace_does_not_truncate_the_next_plain_parse(self, available_parser):
        """The regression pin for the wrong-answer defect A3 actually found.

        ParserCore's ParseToXml sets the morpher's LexEntrySelector and
        RuleSelector from the restriction it is handed, at the start of
        every call, and those selectors OUTLIVE the call. Plain ParseWord is
        the one entry point that never touches them. So before this was
        fixed, a restricted trace made the NEXT plain parse return zero
        analyses -- silently, indefinitely, with no exception. A wrong
        answer, which is the worst shape a defect can take.

        Observed on IndonesianHC-Complete: 1 analysis, then 0 after any
        restricted trace, staying 0 until an unrestricted call re-opened the
        selectors.
        """
        before = len(list(available_parser.ParseWord(PROBE_WORD).Analyses))
        if before == 0:
            pytest.skip("%r has no analyses in %s; nothing could be truncated" % (PROBE_WORD, PRIMARY_PROJECT))

        # A restriction that matches nothing real is the strongest form of
        # the trap: it narrows the selectors as far as they go.
        available_parser.TraceWordXml(PROBE_WORD, [-1])
        after = len(list(available_parser.ParseWord(PROBE_WORD).Analyses))

        assert after == before, (
            "a plain parse returned %d analyses after a restricted trace but "
            "%d before it. The restriction leaked out of the trace and "
            "truncated an unrelated parse -- the caller gets a wrong answer "
            "with no error to notice." % (after, before)
        )


class TestA34ObjectIdentityIsPreserved:
    """A3.4 (FR-010) -- results carry live objects, not their text."""

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_plain_parse_analyses_carry_live_lexical_references(self, available_parser):
        """The claim FR-010 actually makes, tested on a real analysis.

        Skips rather than fails when the probe word happens not to parse in
        this lexicon: "this word has no analyses" is a fact about someone's
        linguistic data, and failing on it would make the tier report a
        defect in the facade that is nothing of the kind. What must never
        happen is an analysis that carries only strings -- that IS a facade
        defect, and it is what the assertions below catch.
        """
        result = available_parser.ParseWord(PROBE_WORD)
        analyses = list(result.Analyses)
        if not analyses:
            pytest.skip("%r produced no analyses in %s; nothing to inspect for identity" % (PROBE_WORD, PRIMARY_PROJECT))

        morphs = list(analyses[0].Morphs)
        assert morphs, "an analysis with no morphs -- nothing to check identity against"

        first = morphs[0]
        # The morph must expose the lexical objects themselves. A string
        # rendering would satisfy "the parse came back" and fail the one
        # requirement FR-010 makes.
        assert hasattr(first, "Form"), "the morph exposes no Form reference"
        assert not isinstance(first.Form, str), (
            "the morph's Form came back as a str, so identity was lost in "
            "crossing into script-visible form. FR-010 requires the live "
            "IMoForm, which is what lets a caller go from a parse back to "
            "the entry that produced it."
        )
        assert hasattr(first.Form, "Hvo"), (
            "the morph's Form has no Hvo, so it is not a live data-model "
            "object; got %r" % type(first.Form)
        )


class TestA36ExpectedEngine:
    """A3.6 -- both live projects are configured for the expected engine."""

    @pytest.mark.live_phase("ParserOperations", "read")
    @pytest.mark.parametrize("fixture_name", ["primary", "secondary"])
    def test_the_configured_engine_is_the_expected_one(self, request, fixture_name):
        """Reads ActiveParser off the project, exactly as the MCP side does.

        Recorded because the evidence is only about HermitCrab: a project
        configured for XAmple exercises a different component, and a pass
        here would not transfer to it.
        """
        project = request.getfixturevalue(fixture_name)
        engine = project.project.LangProject.MorphologicalDataOA.ActiveParser
        assert engine == EXPECTED_ENGINE, (
            "%s is configured for parser engine %r, not %r. The A3 evidence "
            "is only about the expected engine; a different one is a "
            "different component and this tier does not speak for it."
            % (project.ProjectName(), engine, EXPECTED_ENGINE)
        )


# ---------------------------------------------------------------------------
# A3.3 -- T019. THE GATE.
# ---------------------------------------------------------------------------


class TestA33ReloadDiscardsUnconditionally:
    """A3.3 -- the reload discards; the bare update does not.

    This is hard gate 2. If the discard cannot be WITNESSED, it has not been
    proven and CP2b does not start. The point is not that a test with this
    name passes: every one of flexicon's four structural ratchets would have
    passed a reload bound to a bare update, which is the precise defect
    cycle 1 found. Only this class looks at whether the grammar actually
    went away.
    """

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_a_bare_update_with_no_model_change_does_not_reload(self, available_parser):
        """The premise of D-A5, verified rather than assumed.

        HCParser.Update() is guarded by

            if (m_changeListener.Reset() || m_forceUpdate) LoadParser();

        so with nothing changed it must short-circuit. If this test ever
        fails -- if a bare update DOES reload -- then D-A5's premise is
        wrong and the two-step reload should be revisited rather than kept
        out of habit.
        """
        handle = available_parser._parser
        assert handle is not None, "no parser handle is held; the fixture did not construct one"

        before = _morpher_identity(handle)
        if before is None:
            pytest.skip(
                "the %s private field could not be read on this build; the "
                "discard is witnessed by the reload test below via the "
                "load-errors side file instead" % MORPHER_FIELD
            )

        handle.Update()
        after = _morpher_identity(handle)

        assert after == before, (
            "a bare Update() with no model change REPLACED the morpher, so it "
            "reloaded. That contradicts D-A5's premise that Update() "
            "short-circuits -- the reset-then-update reload may be "
            "unnecessary, and the decision should be revisited on this "
            "evidence rather than left standing."
        )

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_reload_discards_the_grammar_even_with_no_model_change(self, available_parser, primary):
        """THE GATE. Reload() must reload when a bare update would not.

        Same starting condition as the test above -- nothing has changed --
        so the two together are the whole claim: under identical conditions
        the bare update does nothing and the reload discards.
        """
        handle = available_parser._parser
        assert handle is not None, "no parser handle is held"

        before_id = _morpher_identity(handle)
        before_mtime = _load_errors_mtime(handle, primary)

        available_parser.Reload()

        after_id = _morpher_identity(handle)

        if before_id is not None and after_id is not None:
            assert after_id != before_id, (
                "Reload() did NOT replace the morpher, so it did not discard "
                "the grammar. A reload that cannot be shown to discard has "
                "not been proven: the next parse would be served from the "
                "very grammar the caller believes was thrown away. CP2b does "
                "not start on this result -- fix the binding, do not relax "
                "the assertion."
            )
            return

        # Documented fallback: the load-errors side file is rewritten on load.
        after_mtime = _load_errors_mtime(handle, primary)
        if before_mtime is None or after_mtime is None:
            pytest.fail(
                "NEITHER WITNESS WAS AVAILABLE. The %s field could not be read "
                "and the HC load-errors side file was not found, so this run "
                "proves nothing about whether Reload() discards. This is a "
                "FAIL, not a skip: the gate is the evidence, and an absent "
                "witness is absent evidence." % MORPHER_FIELD
            )
        assert after_mtime > before_mtime, (
            "the HC load-errors side file was not rewritten, so the grammar "
            "was not reloaded."
        )

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_the_fallback_witness_is_actually_available(self, available_parser, primary):
        """The backup witness must be able to run, not merely be written.

        This test exists because the fallback ONCE COULD NOT RUN and nothing
        noticed. It looked under the project directory for the side file,
        which the component does not write there, so it always returned None
        -- a documented guarantee that silently could not execute. It would
        have been discovered only on the day the primary witness broke, which
        is the worst possible day to discover it.

        So the fallback is now exercised on every run, independently of
        whether it is needed. An unusable backup is not a backup.
        """
        handle = available_parser._parser
        assert handle is not None

        path = _load_errors_side_file(handle, primary)
        assert path is not None, (
            "the fallback witness cannot locate %sHCLoadErrors.xml. It is "
            "built from the component's private m_outputDirectory (see "
            "HCParser.cs:152); if that field moved, repoint the helper rather "
            "than deleting the fallback." % primary.ProjectName()
        )
        assert _load_errors_mtime(handle, primary) is not None, (
            "the side file at %s could not be stat'd, so the fallback would "
            "silently yield nothing if the primary witness ever failed" % path
        )

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_the_parser_is_current_again_after_a_reload(self, available_parser):
        """A discard that does not reload would leave nothing loaded."""
        available_parser.Reload()
        assert available_parser.IsUpToDate() is True


# ---------------------------------------------------------------------------
# A3.5 -- T020. One grammar, and its currency confirmed before reuse.
# ---------------------------------------------------------------------------


class TestA35OneGrammarHeldAndCurrencyConfirmed:
    """A3.5 (SC-014, SC-015) -- across a sequence spanning both projects."""

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_one_area_holds_one_grammar_across_repeated_parses(self, available_parser):
        """SC-014: repeated use must not accumulate grammars."""
        first = available_parser.ParseWord(PROBE_WORD)
        held_after_first = available_parser._parser
        second = available_parser.ParseWord(PROBE_WORD)
        held_after_second = available_parser._parser

        assert first is not None and second is not None
        assert held_after_first is held_after_second, (
            "a second parse replaced the held parser, so two grammars were "
            "loaded where one was needed. SC-014 bounds what is held at any "
            "instant to one."
        )

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_switching_projects_releases_the_previous_grammar(self, primary, secondary):
        """SC-014: 0 grammars retained for a project not in use.

        The two projects have separate parser areas, since each hangs off
        its own FLExProject. What must hold is that neither holds a grammar
        built for the other's cache -- a handle bound to a closed or
        unrelated cache is the leak SC-014 names.
        """
        for project in (primary, secondary):
            status = project.Parser.GetAvailability()
            if not status.available:
                pytest.skip("parser unavailable on %s: %s" % (project.ProjectName(), status.reason))

        primary.Parser.ParseWord(PROBE_WORD)
        secondary.Parser.ParseWord(PROBE_WORD)

        assert primary.Parser._parser_cache is primary.project, (
            "the primary area holds a parser built for a cache that is not "
            "its own project's"
        )
        assert secondary.Parser._parser_cache is secondary.project, (
            "the secondary area holds a parser built for a cache that is not "
            "its own project's"
        )
        assert primary.Parser._parser is not secondary.Parser._parser, (
            "both projects are sharing one parser handle, so one of them is "
            "being served from a grammar loaded for the other's model"
        )

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_a_project_switch_within_one_area_releases_before_it_rebinds(self, primary, secondary):
        """The same area pointed at a second cache must not keep the first.

        Drives the release path directly rather than relying on two areas
        happening not to interfere: the area is asked for a handle, then its
        project's cache is swapped underneath it, and the next use must
        produce a handle bound to the new cache with the old one gone.
        """
        from flexicon.code.Parser.ParserOperations import ParserOperations

        area = ParserOperations(primary)
        status = area.GetAvailability()
        if not status.available:
            pytest.skip("parser unavailable: %s" % status.reason)

        area.ParseWord(PROBE_WORD)
        first_handle = area._parser
        assert first_handle is not None
        assert area._parser_cache is primary.project

        # Point the same area at the other project's cache.
        area.project = secondary
        area.ParseWord(PROBE_WORD)

        assert area._parser is not first_handle, (
            "the area reused the grammar it had loaded for the previous "
            "project's model. SC-014 requires the previous one be released "
            "when another project's grammar is needed."
        )
        assert area._parser_cache is secondary.project

    @pytest.mark.live_phase("ParserOperations", "read")
    def test_no_parse_is_served_without_confirming_currency(self, available_parser, monkeypatch):
        """SC-015, counted rather than asserted in the abstract.

        Wraps the held parser's currency read to count calls, then makes
        three parses by three different routes. Three parses, three
        confirmations -- a cached answer or an exempt route shows up here as
        a count that does not match.
        """
        handle = available_parser._parser
        assert handle is not None

        calls = {"n": 0}
        real = handle.IsUpToDate

        def counting():
            calls["n"] += 1
            return real()

        monkeypatch.setattr(handle, "IsUpToDate", counting, raising=False)

        available_parser.ParseWord(PROBE_WORD)
        available_parser.ParseWordXml(PROBE_WORD)
        available_parser.TraceWordXml(PROBE_WORD)

        assert calls["n"] == 3, (
            "currency was confirmed %d time(s) across three parses. SC-015 is "
            "0 parses served from a grammar whose currency was not confirmed "
            "IMMEDIATELY BEFORE reuse, so every route pays the question every "
            "time." % calls["n"]
        )
