#
#   test_parser_offline.py
#
#   Tier A1, behavioural half -- CP2a T005. Written BEFORE the facade it
#   describes (T010/T011), so until those land this file FAILS. That is the
#   intended state: these assertions are the contract the facade is built
#   to satisfy, not a description written after the fact.
#
#     A1.1 (SC-001, FR-004)  Import succeeds and availability reports
#                            UNAVAILABLE WITH A REASON, raising nothing,
#                            when the parser component cannot be resolved.
#     A1.4 (FR-002)          The public surface contains no method that
#                            records, files or writes a result -- asserted
#                            by ENUMERATION (set equality over the declared
#                            surface), never by inspecting names for
#                            write-looking verbs.
#     A1.5 (FR-005)          Bound parser operations are called
#                            POSITIONALLY, never by parameter name.
#     A1.6 (FR-043)          A grammar reported stale produces a reload
#                            BEFORE any word is parsed.
#
#   RE-TIERED PER D-A1. The cycle-1 brief framed A1 as a no-FieldWorks run.
#   It cannot be: `import flexicon` itself requires FieldWorks, because
#   flexicon/__init__.py pulls in FLExInit, whose module scope calls
#   InitialiseFWGlobals() and raises without the registry key. So this tier
#   runs WITH FieldWorks present and simulates the parser component's
#   resolution failing. SC-001 is unaffected -- it speaks about the PARSER
#   COMPONENT being absent, not FieldWorks.
#
#   SIMULATE ABSENCE, NEVER ASSUME IT. Every unavailability test here
#   actively points the component resolution at a path that does not exist.
#   A test that merely ran on a machine without a parser would pass for the
#   wrong reason on every other machine, and pass vacuously on this one.
#   There is no template for this shape anywhere in the package (research.md
#   F2, D-A4): flexicon today has exactly two behaviours, raise or silently
#   become None, and no precedent for degrading with a stated reason.
#
#   NO CACHE, NO PROJECT, NO GRAMMAR, NO WRITE RISK. Every test below either
#   scans source text or drives the facade against a hand-built stub. None
#   constructs an LcmCache, opens a project or loads a grammar -- which is
#   why the file carries no `requires_live_project` marker and runs in the
#   default tier. The live half is tier A3 (tests/operations/test_parser_live.py).
#
#   Platform: Python.NET, Windows, FieldWorks 9 installed.
#
#   Copyright 2026
#

import ast
import inspect
import os

import pytest


# ---------------------------------------------------------------------------
# The facade under test. Imported lazily inside a helper rather than at
# module scope: until T010/T011 land the import fails, and a module-scope
# failure is a COLLECTION error that takes the whole file down with an
# unreadable traceback. Routed through a helper, each test fails on its own
# with a message that says which task is outstanding.
# ---------------------------------------------------------------------------

FACADE_MODULE = "flexicon.code.Parser.ParserOperations"


def _facade():
    """Import the facade module, or fail with a message naming the gap."""
    try:
        import importlib

        return importlib.import_module(FACADE_MODULE)
    except ImportError as exc:
        pytest.fail(
            "%s could not be imported (%s).\n"
            "EXPECTED until T010/T011 land -- this tier is written first and "
            "fails until the facade satisfies it." % (FACADE_MODULE, exc)
        )


# ---------------------------------------------------------------------------
# A1.1 -- availability degrades with a reason and raises nothing (SC-001)
# ---------------------------------------------------------------------------
#
# The two documented seams the facade must expose so absence can be
# simulated. They are module-level functions, not inlined expressions,
# precisely so this tier can point them somewhere that does not exist --
# a probe with no seam can only be tested on a machine that happens to be
# broken, which is not a test.
#
#   _parser_component_path()  -> the resolved path of ParserCore.dll
#   _data_model_dir()         -> the directory the LOADED SIL.LCModel came
#                                from; FR-004 compares the two DIRECTORIES
#
# FR-004's check is directory equality and nothing else. Comparing the
# resolved component against the directory the data model actually loaded
# from is what makes the check non-trivial: a FWCodeDir pointing at a
# different install than the one already in the process is exactly the
# foreign-install case, and it is the one no version floor would catch.

REQUIRED_SEAMS = ("_parser_component_path", "_data_model_dir")


class TestA11AvailabilityDegradesWithAReason:
    """A1.1 (SC-001) -- asking never raises; it answers."""

    def test_the_documented_seams_exist(self):
        """The probe must be interceptable, or absence cannot be simulated."""
        module = _facade()
        missing = [name for name in REQUIRED_SEAMS if not hasattr(module, name)]
        assert not missing, (
            "%s does not expose %s. These are the documented seams tier A1 "
            "uses to simulate a component that cannot be resolved; without "
            "them SC-001 can only be observed on a broken machine." % (FACADE_MODULE, missing)
        )

    def test_importing_flexicon_does_not_require_the_parser(self):
        """FR-003's consequence: the import already happened, above."""
        import flexicon

        assert hasattr(flexicon, "ParserOperations"), (
            "flexicon imported but does not export ParserOperations (T014). "
            "The import succeeding is half of SC-001; the export is what "
            "makes the surface reachable."
        )

    def test_component_absent_reports_unavailable_with_a_reason(self, tmp_path, monkeypatch):
        """The component cannot be found. Answer, do not raise."""
        module = _facade()
        vanished = os.path.join(str(tmp_path), "no-such-install", "ParserCore.dll")
        monkeypatch.setattr(module, "_parser_component_path", lambda: vanished)

        status = module.ParserOperations(_StubProject()).GetAvailability()

        assert status.available is False
        assert status.reason, "unavailable with an EMPTY reason -- FR-004 requires the reason to state what was checked"
        assert status.version is None, "version must be None when the component was never loaded"

    def test_component_from_a_different_installation_is_refused(self, tmp_path, monkeypatch):
        """FR-004: directory equality, and the reason names both directories."""
        module = _facade()
        foreign = tmp_path / "FieldWorks 8"
        loaded = tmp_path / "FieldWorks 9"
        foreign.mkdir()
        loaded.mkdir()
        component = foreign / "ParserCore.dll"
        component.write_bytes(b"")  # exists, but in the wrong place

        monkeypatch.setattr(module, "_parser_component_path", lambda: str(component))
        monkeypatch.setattr(module, "_data_model_dir", lambda: str(loaded))

        status = module.ParserOperations(_StubProject()).GetAvailability()

        assert status.available is False
        assert str(foreign) in status.reason and str(loaded) in status.reason, (
            "the reason must NAME BOTH directories (%r); a caller who cannot "
            "see which two installs disagreed cannot act on it" % status.reason
        )

    def test_asking_never_raises_whatever_the_probe_hits(self, monkeypatch):
        """SC-001 in its strongest form: the probe itself explodes.

        A component that is present but corrupt, a pythonnet failure, a
        permissions error on the directory -- SC-001 says the ANSWER is
        still an answer. This drives the worst case by making resolution
        itself throw.
        """
        module = _facade()

        def detonate():
            raise OSError("simulated: resolution itself failed")

        monkeypatch.setattr(module, "_parser_component_path", detonate)

        status = module.ParserOperations(_StubProject()).GetAvailability()

        assert status.available is False
        assert status.reason

    def test_the_reason_claims_only_what_was_checked(self, tmp_path, monkeypatch):
        """Principle V. Directory equality does NOT verify provenance.

        A foreign ParserCore.dll copied into the correct directory passes
        FR-004's check undetected. The reason string must therefore never
        say the component was verified, validated, trusted or authentic --
        it says what was looked for and where.
        """
        module = _facade()
        vanished = os.path.join(str(tmp_path), "gone", "ParserCore.dll")
        monkeypatch.setattr(module, "_parser_component_path", lambda: vanished)

        reason = module.ParserOperations(_StubProject()).GetAvailability().reason.lower()

        overclaims = [word for word in ("verified", "validated", "authentic", "trusted", "genuine") if word in reason]
        assert not overclaims, (
            "the reason overclaims with %s. FR-004's test is directory "
            "equality only; stating more than was checked is the Principle V "
            "failure this assertion exists to catch. Reason was: %r" % (overclaims, reason)
        )

    def test_calling_an_operation_while_unavailable_raises_that_same_reason(self, tmp_path, monkeypatch):
        """Asking does not raise. CALLING does -- with the same words."""
        module = _facade()
        vanished = os.path.join(str(tmp_path), "gone", "ParserCore.dll")
        monkeypatch.setattr(module, "_parser_component_path", lambda: vanished)

        parser = module.ParserOperations(_StubProject())
        reason = parser.GetAvailability().reason

        with pytest.raises(Exception) as caught:
            parser.ParseWord("kata")
        assert reason in str(caught.value), (
            "the refusal message (%r) does not carry the availability reason "
            "(%r); a caller who asked and a caller who called should be told "
            "the same thing" % (str(caught.value), reason)
        )


# ---------------------------------------------------------------------------
# A1.4 -- no write, no record, no file (FR-002), BY ENUMERATION
# ---------------------------------------------------------------------------
#
# The surface is asserted by SET EQUALITY against a frozen list, not by
# scanning method names for write-looking verbs. A name scan passes anything
# whose author picked a gentle verb; set equality fails on ANY addition,
# whatever it is called. FR-002's absence has to be enforced by a control,
# not by the reviewer's vocabulary (Principle III).

EXPECTED_PUBLIC_SURFACE = frozenset(
    {
        "GetAvailability",  # the degrading-with-reason probe (SC-001)
        "ParseWord",  # plain parse -- live object references (FR-010)
        "ParseWordXml",  # structured parse -- serialized document
        "TraceWordXml",  # trace, optionally restricted to analyses
        "Reload",  # reset-then-update, TWO steps (D-A5, FR-043)
        "IsUpToDate",  # the currency read (FR-043)
    }
)

# Names that would reach a write path if they appeared in the module source.
# Scoped to the facade's own file, and used ONLY as a supplement to the
# enumeration above -- it is the enumeration that does the real work.
WRITE_SPINE_NAMES = ("_EnsureWriteEnabled", "_TransactionCM", "ProcessParse", "ParseFiler")


def _declared_public_names(cls):
    """Public callables DECLARED on the class, not inherited.

    Scoped to `vars(cls)` on purpose. Every Operations class in the package
    inherits BaseOperations' generic reordering helpers; those are not part
    of what CP2a adds and are handled separately below. The contract this
    test pins is the callable API surface, so helper attributes injected by
    decorators or descriptors do not count as public operations.
    """
    return {
        name
        for name in vars(cls)
        if not name.startswith("_") and inspect.isroutine(getattr(cls, name))
    }


class TestA14NoWriteSurface:
    """A1.4 (FR-002) -- the read-only claim, enforced by enumeration."""

    def test_the_declared_public_surface_is_exactly_the_five_operations_and_the_probe(self):
        module = _facade()
        declared = _declared_public_names(module.ParserOperations)

        assert declared == EXPECTED_PUBLIC_SURFACE, (
            "the parser surface is not what FR-001/FR-002 pin.\n"
            "  unexpected (added since the contract): %s\n"
            "  missing   (contracted but absent)    : %s\n"
            "This assertion is set equality by design: the read-only safety "
            "claim of BOTH CP2b tools rests on nothing else being reachable "
            "here, so an addition must be a deliberate contract change, not "
            "a passing edit."
            % (
                sorted(declared - EXPECTED_PUBLIC_SURFACE),
                sorted(EXPECTED_PUBLIC_SURFACE - declared),
            )
        )

    def test_the_module_never_names_the_write_spine(self):
        module = _facade()
        source = inspect.getsource(module)
        # The constants themselves appear in this test, not in the facade.
        found = [name for name in WRITE_SPINE_NAMES if name in source]
        assert not found, (
            "%s mentions %s. CP2a binds no write path: no _EnsureWriteEnabled, "
            "no _TransactionCM, and never the parse filer -- which is the "
            "component that RECORDS a result and is deliberately not bound "
            "until a later checkpoint." % (FACADE_MODULE, found)
        )

    def test_the_class_docstring_states_the_absence(self):
        """FR-002: the absence must be stated where a contributor reads it.

        An absence that is only true is not enough -- a later contributor
        adding a filing method would not know they were breaking a promise
        that lives in a spec they have never opened.
        """
        module = _facade()
        doc = (module.ParserOperations.__doc__ or "").lower()
        assert doc, "ParserOperations has no class docstring"
        assert "read-only" in doc or "read only" in doc, (
            "the class docstring does not state that this surface is "
            "read-only. FR-002 requires the absence to be stated where a "
            "future contributor will read it."
        )

    def test_the_inherited_sequence_reorderers_are_inert(self):
        """No `_GetSequence` override, so the four reorderers cannot write.

        BaseOperations.Sort / MoveUp / MoveDown / MoveToIndex all route
        through `_GetSequence`, which raises NotImplementedError unless a
        subclass names an owning sequence. ParserOperations names none, so
        they are inert rather than dangerous.

        Stated plainly, because it is the limit of this claim (Principle V):
        BaseOperations' remaining generics -- Swap, MoveBefore, MoveAfter,
        ApplySyncableProperties -- take their targets as arguments and do
        NOT route through `_GetSequence`. They are inherited by all 43
        Operations classes and are not parse-result writers; FR-002 is
        about recording a parse result, and none of them can. The facade
        adds no new reach.
        """
        module = _facade()
        assert "_GetSequence" not in vars(module.ParserOperations), (
            "ParserOperations overrides _GetSequence, which arms the four "
            "inherited sequence reorderers on the parser area. CP2a has no "
            "owning sequence to reorder and must not name one."
        )


# ---------------------------------------------------------------------------
# A1.5 -- positional binding (FR-005)
# ---------------------------------------------------------------------------
#
# IParser names its parameters `word`; HCParser implements them as `form`
# (IParser.cs:23,25). Keyword binding through pythonnet breaks on that
# mismatch -- on some machines and not others, depending on which type the
# call resolves against. Positional binding makes the disagreement harmless,
# so it is asserted structurally rather than left as a convention.

BOUND_PARSER_MEMBERS = frozenset({"ParseWord", "ParseWordXml", "TraceWordXml", "Update", "Reset", "IsUpToDate"})


def _keyword_bound_parser_calls(source, filename="<src>"):
    """Calls to a bound parser member that pass a keyword argument."""
    tree = ast.parse(source, filename=filename)
    offenders = []
    for node in ast.walk(tree):
        if not isinstance(node, ast.Call):
            continue
        func = node.func
        name = func.attr if isinstance(func, ast.Attribute) else getattr(func, "id", None)
        if name not in BOUND_PARSER_MEMBERS:
            continue
        if node.keywords:
            offenders.append("%s:%d %s(%s=...)" % (filename, node.lineno, name, node.keywords[0].arg))
    return offenders


class TestA15PositionalBinding:
    """A1.5 (FR-005) -- bound operations are called by position."""

    def test_detector_catches_a_planted_keyword_call(self):
        """Self-test: the scan is not vacuous."""
        planted = "def f(p):\n    return p.ParseWord(word='kata')\n"
        assert len(_keyword_bound_parser_calls(planted, filename="planted.py")) == 1

    def test_detector_accepts_the_positional_shape(self):
        """Self-test: the compliant call is not reported."""
        compliant = "def f(p):\n    return p.ParseWord('kata')\n"
        assert _keyword_bound_parser_calls(compliant, filename="planted.py") == []

    def test_the_facade_binds_every_parser_call_positionally(self):
        module = _facade()
        source = inspect.getsource(module)
        offenders = _keyword_bound_parser_calls(source, filename=FACADE_MODULE)
        assert offenders == [], (
            "keyword-bound parser calls at %s. IParser names its parameters "
            "`word` and HCParser implements them as `form`; a keyword call "
            "resolves against whichever one pythonnet picked, so it works on "
            "the author's machine and fails on someone else's." % offenders
        )


# ---------------------------------------------------------------------------
# A1.6 -- a stale grammar reloads BEFORE a word is parsed (FR-043)
# ---------------------------------------------------------------------------
#
# The stub records the ORDER of the calls the facade makes, because order is
# the whole requirement: SC-015 is "0 parses served from a grammar whose
# currency was not confirmed immediately before reuse". A reload that
# happens after the parse satisfies every count and none of the meaning.
#
# THE DOCUMENTED INJECTION SEAM. The facade holds its bound handle at
# `_parser` and its resolved status at `_availability`. Setting both is how
# this tier drives the currency path with no FieldWorks parser in the
# process. T010/T011 must honour those two names; they are contract here,
# not incidental implementation.


class _StubProject:
    """The least a BaseOperations subclass needs: something to hold."""

    def __init__(self):
        self.project = None  # would be the LcmCache
        self.ProjectName = "StubProject"


class _StubParser:
    """A hand-built IParser that records what it was asked, in order."""

    def __init__(self, up_to_date):
        self._up_to_date = up_to_date
        self.calls = []
        self.last_trace_restriction = "<never called>"

    def IsUpToDate(self):
        self.calls.append("IsUpToDate")
        return self._up_to_date

    def Reset(self):
        self.calls.append("Reset")
        self._up_to_date = True

    def Update(self):
        self.calls.append("Update")
        self._up_to_date = True

    def ParseWord(self, form):
        self.calls.append("ParseWord")
        return ("parse-result", form)

    def ParseWordXml(self, form):
        self.calls.append("ParseWordXml")
        return ("parse-xml", form)

    def TraceWordXml(self, form, analyses):
        self.calls.append("TraceWordXml")
        # Recorded separately: whether an unrestricted trace reaches the
        # component as null or as an empty sequence is the difference
        # between "no restriction" and "admit nothing".
        self.last_trace_restriction = analyses
        return ("trace-xml", form, analyses)


def _facade_with(stub):
    """A ParserOperations wired to `stub` and reported available."""
    module = _facade()
    parser = module.ParserOperations(_StubProject())
    parser._availability = module.ParserAvailability(available=True, reason="", version="9.3.10")
    parser._parser = stub
    return parser


class TestA16StaleGrammarReloadsBeforeParsing:
    """A1.6 (FR-043, SC-015) -- confirmed before reuse, reloaded when stale."""

    def test_a_stale_grammar_is_reloaded_before_the_word_is_parsed(self):
        stub = _StubParser(up_to_date=False)
        _facade_with(stub).ParseWord("kata")

        assert "ParseWord" in stub.calls, "the word was never parsed"
        assert stub.calls.index("Reset") < stub.calls.index("ParseWord"), (
            "the grammar was reloaded AFTER the parse (%r). SC-015 is about "
            "order: a parse served from a grammar the caller believes was "
            "discarded is the failure, and it counts the same whether the "
            "reload happened later or not at all." % stub.calls
        )
        assert stub.calls.index("Update") < stub.calls.index("ParseWord")

    def test_the_reload_is_reset_then_update_in_that_order(self):
        """D-A5. Two steps, and the discard comes first.

        HCParser.Update() is guarded by

            if (m_changeListener.Reset() || m_forceUpdate) LoadParser();

        so a bare update short-circuits on an unchanged model and serves the
        next parse from the stale grammar the caller believes was discarded.
        FieldWorks' own ParserWorker.ReloadGrammarAndLexicon() resets first.
        A reload bound to a bare update would ship a guarantee that is
        fiction -- the RollbackToMark shape Principle I exists to prevent.
        """
        stub = _StubParser(up_to_date=True)
        _facade_with(stub).Reload()

        assert "Reset" in stub.calls and "Update" in stub.calls, (
            "Reload() did not do both steps (%r). A bare Update() is the "
            "defect D-A5 names by name." % stub.calls
        )
        assert stub.calls.index("Reset") < stub.calls.index("Update"), (
            "Reload() updated before it reset (%r) -- the discard must come "
            "first or the update it guards short-circuits." % stub.calls
        )

    def test_a_current_grammar_is_not_reloaded(self):
        """Currency is CONFIRMED, not assumed -- and not over-served.

        The counterweight to the test above: if every parse reloaded, the
        order assertion would pass and the facade would be useless on a
        real grammar. Currency is asked, and only a stale answer reloads.
        """
        stub = _StubParser(up_to_date=True)
        _facade_with(stub).ParseWord("kata")

        assert "IsUpToDate" in stub.calls, (
            "the facade parsed without asking whether the grammar was "
            "current (%r). SC-015 requires the currency question before "
            "every reuse, and FR-043 requires it be asked of the PARSER, "
            "never answered from a local flag." % stub.calls
        )
        assert "Reset" not in stub.calls, (
            "a grammar reported current was reloaded anyway (%r) -- a cold "
            "grammar load on every word is not a safe default, it is a "
            "different bug." % stub.calls
        )

    def test_currency_is_asked_before_every_reuse_not_once(self):
        """SC-015 says every reuse, so the answer is never cached."""
        stub = _StubParser(up_to_date=True)
        parser = _facade_with(stub)
        parser.ParseWord("kata")
        parser.ParseWord("makan")

        assert stub.calls.count("IsUpToDate") == 2, (
            "currency was asked %d time(s) across two parses (%r). A cached "
            "answer is exactly the local flag FR-043 forbids: the model can "
            "change between the two calls." % (stub.calls.count("IsUpToDate"), stub.calls)
        )

    def test_the_currency_read_asks_the_parser(self):
        """IsUpToDate() is a passthrough, not a computed local opinion."""
        stub = _StubParser(up_to_date=False)
        assert _facade_with(stub).IsUpToDate() is False
        assert stub.calls == ["IsUpToDate"], (
            "the facade's currency read did something other than ask the "
            "parser (%r)." % stub.calls
        )

    def test_a_restricted_trace_clears_before_the_next_plain_parse(self):
        """The clear, pinned OFFLINE so a parser-less machine catches it too.

        The live tier pins the consequence (an untruncated parse); this pins
        the mechanism, in call order, where no FieldWorks is needed.
        """
        stub = _StubParser(up_to_date=True)
        parser = _facade_with(stub)
        parser.TraceWordXml("kata", [1, 2])
        parser.ParseWord("kata")

        assert "ParseWordXml" in stub.calls, (
            "no clearing call was made after a restricted trace (%r). The "
            "component leaves its selectors narrowed and a plain parse does "
            "not reset them." % stub.calls
        )
        assert stub.calls.index("ParseWordXml") < stub.calls.index("ParseWord"), (
            "the clear happened AFTER the parse (%r), so the parse it was "
            "supposed to protect was served truncated anyway." % stub.calls
        )

    def test_a_trace_that_raises_still_clears_before_the_next_parse(self):
        """The failure mode that makes the flag order load-bearing.

        The component installs its selectors at the START of the call, so a
        trace that throws part-way through has ALREADY narrowed them. If the
        facade recorded the restriction only on success, the flag would stay
        false, the clear would be skipped, and the next plain parse would be
        served truncated -- silently, indefinitely, which is verbatim the
        defect this mechanism exists to prevent. Failing safe costs one
        wasted parse; failing open costs a wrong answer.
        """
        stub = _StubParser(up_to_date=True)
        parser = _facade_with(stub)

        def exploding(form, analyses):
            stub.calls.append("TraceWordXml")
            raise RuntimeError("simulated: the parse threw after narrowing")

        stub.TraceWordXml = exploding

        with pytest.raises(RuntimeError):
            parser.TraceWordXml("kata", [1, 2])

        parser.ParseWord("kata")
        assert "ParseWordXml" in stub.calls, (
            "a trace that raised left the restriction uncleared (%r), so the "
            "next plain parse was served from a narrowed morpher." % stub.calls
        )
        assert stub.calls.index("ParseWordXml") < stub.calls.index("ParseWord")

    def test_an_empty_analysis_restriction_is_refused(self):
        """An empty restriction is a caller error, not "no restriction".

        The component branches on whether the restriction is null: a null
        reopens its entry/rule selectors, an EMPTY sequence installs a
        filter admitting nothing. The two are near-opposites, so reading
        empty as "unrestricted" is a guess, and it is the wrong one. The
        live tier pins the consequence; this pins the refusal so a machine
        with no parser still catches a regression here.
        """
        from flexicon.code.exceptions import FP_ParameterError

        stub = _StubParser(up_to_date=True)
        with pytest.raises(FP_ParameterError):
            _facade_with(stub).TraceWordXml("kata", [])
        assert "TraceWordXml" not in stub.calls, (
            "the refusal happened AFTER the component was called (%r). A "
            "request that is going to be refused must not reach the parser, "
            "or the restriction is installed anyway." % stub.calls
        )

    def test_an_unrestricted_trace_passes_null_not_an_empty_sequence(self):
        """None must reach the component as null, never as an empty array."""
        stub = _StubParser(up_to_date=True)
        _facade_with(stub).TraceWordXml("kata", None)
        assert stub.last_trace_restriction is None, (
            "an unrestricted trace passed %r to the component instead of "
            "None. An empty sequence there restricts the parser to nothing "
            "and leaves it that way." % (stub.last_trace_restriction,)
        )

    def test_the_structured_parse_and_trace_take_the_same_currency_path(self):
        """Every route to the parser, not just the plain one."""
        for method, args in (("ParseWordXml", ("kata",)), ("TraceWordXml", ("kata", None))):
            stub = _StubParser(up_to_date=False)
            getattr(_facade_with(stub), method)(*args)
            assert stub.calls.index("Reset") < stub.calls.index(method), (
                "%s reached the parser without reloading a stale grammar "
                "first (%r). SC-015 admits no exempt route." % (method, stub.calls)
            )
