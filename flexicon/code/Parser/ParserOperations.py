#
#   ParserOperations.py
#
#   Class: ParserOperations
#          READ-ONLY access to the FieldWorks morphological parser for
#          SIL Language and Culture Model (LCM) projects.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

# ---------------------------------------------------------------------------
# NOTHING FROM THE PARSER COMPONENT IS IMPORTED AT MODULE SCOPE.
#
# This is the whole of FR-003, and it is not a style preference. `import
# flexicon` must keep working on a machine whose parser component is missing,
# renamed or relocated -- such a machine degrades to "parser unavailable",
# never to a broken package import. Every reference to ParserCore below sits
# INSIDE a function, and tests/test_parser_structure.py (A1.3) asserts that
# by AST walk, in both directions: no module-scope parser import anywhere in
# the package, and at least one function-local one here.
# ---------------------------------------------------------------------------

import os
from dataclasses import dataclass
from typing import Optional

from ..BaseOperations import BaseOperations, OperationsMethod
from ..exceptions import FP_ParameterError, FP_RuntimeError


# ---------------------------------------------------------------------------
# What the facade binds, and where it looks
# ---------------------------------------------------------------------------

PARSER_COMPONENT = "ParserCore.dll"
DATA_MODEL_COMPONENT = "SIL.LCModel.dll"

PARSER_NAMESPACE = "SIL.FieldWorks.WordWorks.Parser"
PARSER_ASSEMBLY = "ParserCore"

#: Every member this facade calls, rendered the way the C# source spells it.
#: Verified against the real installed component by tier A2
#: (tests/test_parser_reflective.py) BEFORE any of the behaviour below was
#: written -- Constitution Principle I. `Reset()` and `IsUpToDate()` had
#: never been verified anywhere, in either repository, before that tier.
#:
#: Deliberately NOT the same list as FlexToolsMCP's
#: src/flextoolsmcp/server/parser_probe.py. The two diverge in both
#: directions and neither is a superset of the other: that module
#: additionally requires the filing member, which is the write spine and
#: which this read facade never binds; this list additionally requires the
#: reset and currency members, which that module does not cover. Each check
#: probes what its OWN surface binds, and CP2a changes zero lines of the
#: other one (FR-041, Decision D1).
REQUIRED_MEMBERS = (
    "HCParser(LcmCache)",
    "Update()",
    "Reset()",
    "IsUpToDate()",
    "ParseWord(string)",
    "ParseWordXml(string)",
    "TraceWordXml(string, IEnumerable<int>)",
)

_CLR_PRIMITIVE_NAMES = {
    "String": "string",
    "Int32": "int",
    "Boolean": "bool",
    "Void": "void",
    "Object": "object",
}


# ---------------------------------------------------------------------------
# ParserAvailability
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class ParserAvailability:
    """Whether this project can reach the parser, and why not if it cannot.

    Returned, never raised. Asking whether the parser is reachable succeeds
    on every machine, in every condition -- a missing component, a component
    from another FieldWorks install, a component whose surface has moved, a
    permissions error on the directory, a pythonnet failure. That is SC-001,
    and it is the single property tier A1 exists to test.

    This is the first degrading-with-reason return in flexicon. The package
    otherwise has exactly two behaviours, raise or silently become None, and
    neither is right here: a script that wants to know whether it can parse
    should be able to ask without guarding the question in a try block.

    Attributes:
        available (bool): Whether the parser operations may be called.
        reason (str): Why not, when `available` is False. Empty when
            available. States WHAT WAS CHECKED and nothing more.
        version (str or None): The detected component version, or None when
            the component was never loaded. Reported, never compared.

    Notes:
        - `version` is REPORTED AND NEVER COMPARED AGAINST A MINIMUM
          (FR-006). A version floor is the check that looks reasonable in
          review and then refuses to run on the one machine whose
          FieldWorks build number sorts the wrong way. The gate is the two
          checks below, neither of which reads a number:
          same-installation, and the bound surface exists. A standing AST
          test on each side of the repository boundary asserts zero
          comparisons (tests/test_parser_structure.py, A1.2).
        - The same-installation check is DIRECTORY EQUALITY ONLY. See
          `GetAvailability` for the limit of what that proves.

    Example:
        >>> status = project.Parser.GetAvailability()
        >>> if not status.available:
        ...     print(f"No parser: {status.reason}")
        ... else:
        ...     print(f"Parser {status.version} ready")
        Parser 9.3.10 ready

    See Also:
        ParserOperations.GetAvailability
    """

    available: bool
    reason: str
    version: Optional[str] = None


# ---------------------------------------------------------------------------
# Resolution seams
#
# These two are module-level functions rather than expressions inlined into
# the probe for a reason that is testable rather than aesthetic: tier A1
# replaces them to simulate a component that cannot be resolved. A probe with
# no seam can only be observed on a machine that happens to be broken, which
# is not a test -- it is a machine. tests/test_parser_offline.py asserts both
# names exist, so they are contract, not incidental implementation.
# ---------------------------------------------------------------------------


def _parser_component_path():
    """Where ParserCore.dll is expected, per flexicon's own install resolution.

    Uses FLExGlobals.FWCodeDir -- the registry-derived FieldWorks directory
    that `import flexicon` has already resolved through FLExInit. Deliberately
    not FlexToolsMCP's resolution: this repository does not import that one
    (Decision D1), and the two checks stay independent on purpose.
    """
    from .. import FLExGlobals

    if not FLExGlobals.FWCodeDir:
        FLExGlobals.InitialiseFWGlobals()
    return os.path.join(os.path.normpath(FLExGlobals.FWCodeDir), PARSER_COMPONENT)


def _data_model_dir():
    """The directory the LOADED data model assembly actually came from.

    "The data model in use" in FR-004 means the SIL.LCModel already resolved
    into this process, not the one a directory happens to contain. Reading
    the loaded assembly's own location is what makes the comparison in
    `GetAvailability` non-trivial: an install directory pointing somewhere
    other than where the data model was loaded from IS the foreign-install
    case, and it is the failure no version floor would have caught.

    Returns None when the assembly cannot be located, which the caller
    reports as unavailable rather than treating as a match.
    """
    try:
        import System

        for assembly in System.AppDomain.CurrentDomain.GetAssemblies():
            if assembly.GetName().Name == "SIL.LCModel":
                location = assembly.Location
                if location:
                    return os.path.dirname(os.path.normpath(location))
    except Exception:
        return None
    return None


def _format_clr_type(clr_type):
    """Render a .NET System.Type the way the C# source spells it."""
    try:
        if clr_type.IsGenericType:
            import re

            base = re.sub(r"`\d+", "", clr_type.Name)
            args = ", ".join(_format_clr_type(a) for a in clr_type.GetGenericArguments())
            return "%s<%s>" % (base, args)
    except Exception:
        pass
    try:
        if clr_type.IsArray:
            return "%s[]" % _format_clr_type(clr_type.GetElementType())
    except Exception:
        pass
    name = getattr(clr_type, "Name", str(clr_type))
    return _CLR_PRIMITIVE_NAMES.get(name, name)


def _reflect_member_surface(component_path):
    """(present member names, detected version) for the component on disk.

    Reflection only -- Assembly.LoadFile plus GetConstructors/GetMethods. No
    cache is constructed, no grammar is loaded and no word is parsed, so
    probing is free of side effects on the project.
    """
    import System
    from System.Reflection import BindingFlags

    assembly = System.Reflection.Assembly.LoadFile(component_path)
    name = assembly.GetName()
    detected = "%d.%d.%d" % (name.Version.Major, name.Version.Minor, name.Version.Build)

    flags = BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly
    present = set()
    for clr_type in assembly.GetTypes():
        if clr_type.Name != "HCParser":
            continue
        for ctor in clr_type.GetConstructors(flags):
            params = ", ".join(_format_clr_type(p.ParameterType) for p in ctor.GetParameters())
            present.add("%s(%s)" % (clr_type.Name, params))
        for method in clr_type.GetMethods(flags):
            params = ", ".join(_format_clr_type(p.ParameterType) for p in method.GetParameters())
            present.add("%s(%s)" % (method.Name, params))

    return present, detected


def _probe_availability():
    """Resolve availability. Never raises, whatever it hits.

    The blanket except is deliberate and is the requirement, not laziness:
    SC-001 says the ANSWER is still an answer when the probe itself fails.
    A corrupt component, a pythonnet that will not load, a directory the
    process cannot stat -- each produces an unavailable status carrying what
    went wrong, because a caller who asked a question deserves a sentence
    rather than a traceback.
    """
    try:
        component = _parser_component_path()
    except Exception as exc:
        return ParserAvailability(False, "the FieldWorks installation could not be resolved: %s" % exc)

    try:
        if not os.path.exists(component):
            return ParserAvailability(
                False,
                "%s was not found at %s" % (PARSER_COMPONENT, component),
            )

        model_dir = _data_model_dir()
        if model_dir is None:
            return ParserAvailability(
                False,
                "the loaded %s could not be located, so the same-installation "
                "check could not be made" % DATA_MODEL_COMPONENT,
            )

        component_dir = os.path.dirname(component)
        if os.path.normcase(component_dir) != os.path.normcase(model_dir):
            return ParserAvailability(
                False,
                "%s was found in %s but the data model in use was loaded from "
                "%s; the two directories differ, so the component belongs to a "
                "different FieldWorks installation"
                % (PARSER_COMPONENT, component_dir, model_dir),
            )

        present, detected = _reflect_member_surface(component)
        missing = sorted(set(REQUIRED_MEMBERS) - present)
        if missing:
            return ParserAvailability(
                False,
                "%s at %s does not declare %s"
                % (PARSER_COMPONENT, component, ", ".join(missing)),
            )

        return ParserAvailability(True, "", detected)

    except Exception as exc:
        return ParserAvailability(
            False,
            "%s at %s could not be inspected: %s" % (PARSER_COMPONENT, component, exc),
        )


# ---------------------------------------------------------------------------
# ParserOperations
# ---------------------------------------------------------------------------


class ParserOperations(BaseOperations):
    """
    READ-ONLY access to the FieldWorks morphological parser.

    Reached as ``project.Parser``. Ask a word whether it parses, get the
    parser's structured answer, or trace an attempt to see why it failed.

    THIS SURFACE IS READ-ONLY BY CONSTRUCTION, AND THAT IS LOAD-BEARING.
    There is no operation here that records, files or otherwise writes a
    parse result back into the project, and there is no transaction and no
    write-enable check anywhere in this module -- because there is nothing
    to guard. If you are about to add a method that persists a parse, stop:
    the read-only safety claim made by every caller of this surface rests on
    that absence, and a standing test enumerates the public surface by set
    equality to keep it true (tests/test_parser_offline.py, A1.4). Persisting
    a parse is a later checkpoint's work and arrives with its own guards.

    THE EXACT LIMIT OF THAT CLAIM, since a caller is entitled to know where
    it stops. "Read-only" covers everything this class ADDS -- all six
    methods above. It does not extend to the generic reordering helpers every
    Operations class inherits from BaseOperations. Four of them (Sort,
    MoveUp, MoveDown, MoveToIndex) are inert here because they route through
    `_GetSequence`, which this class deliberately does not override. The rest
    -- Swap, MoveBefore, MoveAfter, ApplySyncableProperties -- take their
    targets as arguments and WILL write if you hand them writable objects.
    None of them can record a parse result, and this class adds no new reach,
    but `project.Parser.Swap(a, b)` is not a no-op and should not be read as
    one.

    DEGRADES, DOES NOT EXPLODE. On a machine where the parser component is
    missing, relocated, or from a different FieldWorks installation,
    importing flexicon still works and ``GetAvailability()`` answers with a
    reason. Only CALLING an operation raises, and it raises with that same
    reason. Ask first if you are not sure::

        status = project.Parser.GetAvailability()
        if not status.available:
            report.Warning(status.reason)

    ONE GRAMMAR, AND ITS CURRENCY IS ASKED, NEVER ASSUMED. At most one
    loaded grammar is held at a time, for the project in use; switching
    projects releases the previous one. Before every parse the parser is
    ASKED whether its grammar is current, and a stale grammar is reloaded
    before the word is parsed -- never after, and never from a local flag
    that this class maintains, because a local flag is exactly what goes
    stale when something else changes the model.

    Usage::

        from flexicon import FLExProject

        project = FLExProject()
        project.OpenProject("IndonesianHC-Complete", writeEnabled=False)

        status = project.Parser.GetAvailability()
        if status.available:
            result = project.Parser.ParseWord("mengambil")
            trace = project.Parser.TraceWordXml("mengambil")

        project.CloseProject()

    See Also:
        ParserAvailability
    """

    def __init__(self, project):
        """
        Initialize ParserOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)
        # Resolved once, lazily, on the first question asked. The probe is
        # terminal per instance: a component that was absent a moment ago is
        # not going to appear mid-script, and re-probing per call would make
        # every parse pay for reflection.
        self._availability = None
        # The bound parser handle and the cache it was built for. Holding the
        # cache alongside the handle is how "at most one grammar, for the
        # project in use" is enforced without a registry: a handle built for
        # a different cache is released rather than reused.
        #
        # These two names, with `_availability` above, are the documented
        # seam tier A1 drives the currency path through. They are contract.
        self._parser = None
        self._parser_cache = None
        # Whether the last operation left the component's morpher filtered to
        # a subset of entries and rules. See _ClearAnyRestriction: this is not
        # bookkeeping for its own sake, it is what stops a restricted trace
        # from silently truncating the NEXT plain parse.
        self._restricted = False

    # --- Availability ---

    @OperationsMethod
    def GetAvailability(self):
        """
        Report whether this project can reach the parser, and why not if it cannot.

        Asking NEVER raises, on any machine, in any condition. A missing
        component, a component from another FieldWorks install, a component
        whose surface has moved, a permissions error, a pythonnet failure --
        each produces a status carrying what went wrong.

        Args:
            None

        Returns:
            ParserAvailability: `available`, `reason`, and the detected
            `version` (reported, never compared against a minimum).

        Example:
            >>> status = project.Parser.GetAvailability()
            >>> print(status.available, status.version)
            True 9.3.10

        Notes:
            - Two checks, and NEITHER READS A VERSION NUMBER (FR-006):
              (1) the component resolves from the same directory the data
              model in use was loaded from, and (2) every member this class
              calls is present on it.
            - WHAT CHECK 1 DOES NOT PROVE, stated here because the reason
              string must not imply more than was tested: the test is
              DIRECTORY EQUALITY ONLY. A foreign ParserCore.dll copied into
              the correct FieldWorks directory passes it undetected. It
              catches the accident -- two installs mixed across an
              in-process boundary -- not the adversary.
            - The member list checked here is deliberately NOT the same list
              FlexToolsMCP's src/flextoolsmcp/server/parser_probe.py checks,
              and the two are not drifting apart by accident. That module
              probes the surface IT binds, which includes the member that
              files a parse result; this class never binds that member, and
              it additionally requires the reset and currency members, which
              that module has no use for. Neither list is a superset of the
              other and neither should be reconciled into the other
              (Decision D1).
            - The result is cached for the lifetime of this instance.

        See Also:
            ParserAvailability
        """
        if self._availability is None:
            self._availability = _probe_availability()
        return self._availability

    # --- Parsing ---

    @OperationsMethod
    def ParseWord(self, word):
        """
        Parse a single word form and return the parser's result object.

        Args:
            word (str): The word form to parse, in the vernacular.

        Returns:
            ParseResult: The parser's own result. Analyses on it carry LIVE
            references to the lexical objects they were built from --
            IMoForm, IMoMorphSynAnalysis, ILexEntryInflType -- not their
            text. A caller can go from a parse straight back to the entry
            that produced it without a lookup.

        Raises:
            FP_RuntimeError: If the parser is unavailable, carrying the same
                reason `GetAvailability()` would have reported.

        Example:
            >>> result = project.Parser.ParseWord("mengambil")
            >>> print(result.Analyses.Count)
            2

        Notes:
            - The grammar's currency is confirmed immediately before the
              parse, and a stale grammar is reloaded first.
            - Object identity is preserved here and NOT on the serialized
              forms below: once the parser has written a document, the
              objects in it survive only as integer identifiers.

        See Also:
            ParseWordXml, TraceWordXml, GetAvailability
        """
        handle = self._CurrentHandle()
        self._ClearAnyRestriction(handle, word)
        return handle.ParseWord(word)

    @OperationsMethod
    def ParseWordXml(self, word):
        """
        Parse a single word form and return the parser's structured document.

        Args:
            word (str): The word form to parse, in the vernacular.

        Returns:
            XDocument: The parser's serialized parse document.

        Raises:
            FP_RuntimeError: If the parser is unavailable, carrying the same
                reason `GetAvailability()` would have reported.

        Example:
            >>> doc = project.Parser.ParseWordXml("mengambil")
            >>> print(doc.Root.Name.LocalName)
            Wordform

        Notes:
            - Lexical objects survive on this document as integer
              identifiers, not as live references. Use `ParseWord` when you
              need to reach the objects themselves.
            - The grammar's currency is confirmed immediately before the
              parse, and a stale grammar is reloaded first.

        See Also:
            ParseWord, TraceWordXml
        """
        result = self._CurrentHandle().ParseWordXml(word)
        # The component resets its own selectors on this path (it passes a
        # null restriction through), so whatever a previous trace narrowed is
        # open again once this returns.
        self._restricted = False
        return result

    @OperationsMethod
    def TraceWordXml(self, word, analyses=None):
        """
        Trace a parse attempt, optionally restricted to specific analyses.

        A trace explains an attempt: which rules fired, which failed, and
        where a candidate was rejected. It is the expensive answer, and the
        one worth asking for when a plain parse came back empty.

        Args:
            word (str): The word form to trace, in the vernacular.
            analyses (iterable of int, optional): Identifiers of the
                analyses to restrict the trace to. None traces without
                restriction. An EMPTY sequence is refused -- see Raises.

        Returns:
            XDocument: The parser's serialized trace document.

        Raises:
            FP_RuntimeError: If the parser is unavailable, carrying the same
                reason `GetAvailability()` would have reported.
            FP_ParameterError: If `analyses` is an empty sequence. Pass None
                for an unrestricted trace; an empty restriction would limit
                the trace to no analyses at all.

        Example:
            >>> doc = project.Parser.TraceWordXml("mengambil")
            >>> print(doc.Root.Name.LocalName)
            Wordform

        Notes:
            - The restriction is passed through EXACTLY as given. This
              method never substitutes a different restriction, never
              widens one to an unrestricted search, and never reorders or
              scores what it was handed. That is also why an empty
              restriction is refused instead of being read as "no
              restriction" -- widening it would answer a different question.
            - A RESTRICTION OUTLIVES THE CALL, inside the component. The
              component narrows its morpher's entry and rule selectors and
              leaves them narrowed, and a plain parse does not reset them.
              This class undoes that before the next plain parse, so callers
              do not have to know; the cost is one extra parse, paid only
              when a restricted trace is actually followed by a plain parse.
            - Objects in the returned document are integer identifiers;
              turning them back into lexical objects is a repository lookup
              the caller makes, and this class deliberately does not do it
              for them.
            - The grammar's currency is confirmed immediately before the
              trace, and a stale grammar is reloaded first.

        See Also:
            ParseWord, ParseWordXml
        """
        restriction = self._AsIdentifierSequence(analyses)
        handle = self._CurrentHandle()
        # SET BEFORE THE CALL, NOT AFTER, AND THE ORDER IS THE WHOLE POINT.
        # The component installs its selectors at the START of the call, so
        # they are narrowed the moment it begins. If the parse then throws --
        # a difficult form, a bad identifier in the restriction, a
        # marshalling failure -- a flag set afterwards would never be set,
        # _ClearAnyRestriction would return early, and the next plain parse
        # would be served truncated: silently, indefinitely, which is
        # verbatim the defect this whole mechanism exists to prevent.
        # Setting it first fails the safe way. The worst case is one wasted
        # clearing parse; the worst case the other way round is a wrong
        # answer.
        self._restricted = restriction is not None
        return handle.TraceWordXml(word, restriction)

    # --- Grammar lifetime ---

    @OperationsMethod
    def Reload(self):
        """
        Discard the loaded grammar and load it again. Unconditionally.

        Args:
            None

        Returns:
            None

        Raises:
            FP_RuntimeError: If the parser is unavailable, carrying the same
                reason `GetAvailability()` would have reported.

        Example:
            >>> project.Parser.Reload()
            >>> print(project.Parser.IsUpToDate())
            True

        Notes:
            - THIS IS TWO STEPS, RESET THEN UPDATE, AND THE ORDER MATTERS.
              The component's own update is guarded by a condition that
              short-circuits when it believes the model has not changed, so
              a reload bound to a bare update would return having done
              nothing and serve the next parse from the very grammar the
              caller just asked to have discarded. The reset is what makes
              the update unconditional. FieldWorks' own reload does the same
              two steps in the same order.
            - You rarely need to call this. Every parse already confirms
              currency and reloads a stale grammar on its own; this is for
              the case where you changed the model yourself and want the
              cost paid now rather than on the next word.

        See Also:
            IsUpToDate
        """
        handle = self._CurrentHandle(confirm_currency=False)
        handle.Reset()
        handle.Update()
        # A reloaded grammar has open selectors, so nothing is left to undo.
        # Kept in step deliberately: the flag is meant to TRACK the
        # component's state, not merely to remember what this class last did.
        self._restricted = False

    @OperationsMethod
    def IsUpToDate(self):
        """
        Ask the parser whether its loaded grammar is current.

        Args:
            None

        Returns:
            bool: True if the loaded grammar matches the project's current
            model, False if it is stale.

        Raises:
            FP_RuntimeError: If the parser is unavailable, carrying the same
                reason `GetAvailability()` would have reported.

        Example:
            >>> print(project.Parser.IsUpToDate())
            True

        Notes:
            - The question is put to the PARSER every time it is asked. This
              class keeps no flag of its own, because a flag it maintained
              would be right only until something outside this class changed
              the model -- which is precisely the case the question exists
              to detect.

        See Also:
            Reload
        """
        return bool(self._CurrentHandle(confirm_currency=False).IsUpToDate())

    # --- Internals ---
    #
    # Every call into the component below is bound POSITIONALLY, never by
    # parameter name. The interface declares its parameter as `word` and the
    # implementation spells it `form`, so a keyword call resolves against
    # whichever of the two pythonnet happened to pick -- working on the
    # author's machine and failing on someone else's. Positional binding
    # makes the disagreement harmless, and tier A1 asserts it structurally
    # rather than leaving it as a convention to remember.

    def _Require(self):
        """Refuse with the availability reason, or return the status."""
        status = self.GetAvailability()
        if not status.available:
            raise FP_RuntimeError(status.reason)
        return status

    def _ReleaseGrammar(self):
        """Drop the held grammar, discarding it first if we still can.

        Best-effort by design: this runs when we are switching away from a
        cache, and a handle whose project is already closing may refuse the
        discard. Failing to tidy up an outgoing grammar must not break the
        incoming one.
        """
        handle = self._parser
        self._parser = None
        self._parser_cache = None
        # The next handle is a fresh parser with open selectors.
        self._restricted = False
        if handle is None:
            return
        try:
            handle.Reset()
        except Exception:
            pass

    def _CurrentHandle(self, confirm_currency=True):
        """The bound parser for the project in use, with a current grammar.

        Enforces both grammar-lifetime clauses in one place, which is why
        every public operation goes through it and none reaches the
        component directly: at most one grammar is held, for the cache in
        use, and its currency is confirmed immediately before it is reused.
        """
        self._Require()
        cache = self.project.project

        if self._parser is None or self._parser_cache is not cache:
            # A handle built for another project is released before the new
            # one is built, never alongside it -- "at most one" is a bound on
            # what is held at any instant, not a tidy-up done afterwards.
            self._ReleaseGrammar()
            handle = self._ConstructParser(cache)
            handle.Update()
            self._parser = handle
            self._parser_cache = cache
            return handle

        handle = self._parser
        if confirm_currency and not handle.IsUpToDate():
            handle.Reset()
            handle.Update()
        return handle

    def _ConstructParser(self, cache):
        """Bind the component and construct a parser over `cache`.

        The import is FUNCTION-LOCAL, and that is FR-003: loading the
        component is triggered by USE, so a machine that never touches
        project.Parser never needs ParserCore.dll to exist, and one whose
        installation moved degrades to unavailable instead of failing to
        import flexicon at all.
        """
        import clr

        clr.AddReference(PARSER_ASSEMBLY)
        from SIL.FieldWorks.WordWorks.Parser import HCParser

        return HCParser(cache)

    def _ClearAnyRestriction(self, handle, word):
        """Undo a restriction a previous trace left on the component.

        WHY THIS EXISTS -- verified against the component's source and
        against a live project, not inferred. ParserCore's ParseToXml sets

            m_morpher.LexEntrySelector / m_morpher.RuleSelector

        from the restriction it was handed, at the START of every call, and
        those selectors OUTLIVE the call. Plain ParseWord is the one entry
        point that never touches them -- it calls the morpher directly. So a
        restricted trace followed by a plain parse returns a truncated
        answer, silently and indefinitely, until something else happens to
        reset the selectors.

        Observed live on IndonesianHC-Complete: a word parsing with one
        analysis returns ZERO after any restricted trace, and keeps
        returning zero, until an unrestricted call re-opens the selectors.
        No exception, no warning -- just a wrong answer, which is the worst
        shape a defect can take.

        The reset uses the component's OWN path: ParseWordXml passes a null
        restriction, which is what makes ParseToXml reopen both selectors.
        It costs one extra parse, paid only when a restricted trace actually
        preceded a plain parse, never on the common unrestricted route.
        """
        if not self._restricted:
            return
        handle.ParseWordXml(word)
        self._restricted = False

    def _AsIdentifierSequence(self, analyses):
        """Render `analyses` as the restriction the component expects.

        None means DO NOT RESTRICT, and the component spells that as null --
        NOT as an empty sequence. The distinction is load-bearing and the
        two are near-opposites: ParseToXml branches on
        `selectTraceMorphs != null`, so a null reopens the selectors while
        an EMPTY array installs a filter that admits nothing. Passing an
        empty array for "no restriction" is therefore not a harmless
        approximation -- it restricts the parser to nothing at all, and
        leaves it that way.

        An explicitly empty sequence is refused rather than quietly widened.
        Restricting to no analyses can only ever produce no analyses, so it
        is a caller error; and silently turning it into an unrestricted
        search would be answering a different question than the one asked.
        """
        if analyses is None:
            return None

        values = [int(item) for item in analyses]
        if not values:
            raise FP_ParameterError(
                "analyses is empty. An empty restriction limits the trace to "
                "no analyses at all, which can only return nothing. Pass None "
                "to trace without restriction, or pass the analyses you want."
            )

        import System

        sequence = System.Array[System.Int32](len(values))
        for index, value in enumerate(values):
            sequence[index] = value
        return sequence
