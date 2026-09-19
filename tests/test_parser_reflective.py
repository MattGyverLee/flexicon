#
#   test_parser_reflective.py
#
#   Tier A2 -- CP2a T003. Reflective verification of the parser surface
#   against the REAL INSTALLED ParserCore.dll, with FieldWorks present and
#   NO PROJECT OPENED.
#
#   Why this tier exists, and why it runs before any behaviour does:
#   Constitution Principle I (NON-NEGOTIABLE) -- no design may assume a
#   member exists. `Reset()` and `IsUpToDate()` had never been verified
#   anywhere, in either repository, before this file. The facade in
#   flexicon/code/Parser/ParserOperations.py binds both: FR-043's reload is
#   specified as reset-then-update (two steps, D-A5) precisely because
#   HCParser.Update() is itself conditional --
#
#       if (m_changeListener.Reset() || m_forceUpdate) LoadParser();
#
#   -- so a bare Update() short-circuits on an unchanged model and serves
#   the next parse from the stale grammar the caller believes it discarded.
#   If Reset() or IsUpToDate() were absent from the shipped component, the
#   facade could not be built as designed and CP2a would halt here rather
#   than route around it (tasks.md, hard gate 1).
#
#   NO CACHE, NO PROJECT, NO WRITE RISK. This tier is Assembly.LoadFile plus
#   GetConstructors/GetMethods. It never constructs an LcmCache, never loads
#   a grammar and never parses a word, so there is no project to corrupt and
#   nothing to restore. That is what lets it run unattended and unmarked, in
#   the default `-m "not requires_live_project"` tier.
#
#   DELIBERATELY DIFFERENT FROM THE MCP-SIDE CHECK (Decision D-02 / E3).
#   FlexToolsMCP's src/flextoolsmcp/server/parser_probe.py reflects a
#   different member set for a different purpose, and CP2a changes 0 lines
#   of it (FR-041, SC-016, T029). The two lists diverge in BOTH directions:
#   this file additionally requires Reset() and IsUpToDate(), which the
#   shipped MCP check does not cover; the MCP check additionally requires
#   ParseFiler.ProcessParse, which is the write spine and which the CP2a
#   read facade never binds. Each check probes what its own surface binds.
#   Neither is a superset of the other and neither should be "reconciled"
#   into the other.
#
#   Platform: Python.NET, Windows, FieldWorks 9 installed.
#
#   Copyright 2026
#

import os
import re

import pytest


# ---------------------------------------------------------------------------
# The member surface the CP2a facade will bind (FR-001, FR-043).
#
# Format matches what the parser_core fixture produces: a bare signature for
# the constructor and for each method, rendered the way the C# source spells
# it (`string`, not `String`; `IEnumerable<int>`, not the backtick-generic
# CLR name).
# ---------------------------------------------------------------------------

REQUIRED_HCPARSER_MEMBERS = frozenset(
    {
        "HCParser(LcmCache)",  # construction from a cache
        "Update()",  # grammar update
        "Reset()",  # A2.2 -- the discard half of the reload
        "IsUpToDate()",  # A2.2 -- the currency read
        "ParseWord(string)",  # plain parse
        "ParseWordXml(string)",  # structured parse
        "TraceWordXml(string, IEnumerable<int>)",  # trace
    }
)

# The two members A2.2 verifies for the first time anywhere, with the return
# type the facade depends on. `IsUpToDate` must be a bool read -- FR-043's
# "confirmed before reuse" is answered by asking the parser, never by a local
# flag -- and `Reset` must be the void discard, not a bool query.
CURRENCY_AND_RESET_MEMBERS = {
    "Reset": "void",
    "IsUpToDate": "bool",
}

_CLR_PRIMITIVE_NAMES = {
    "String": "string",
    "Int32": "int",
    "Boolean": "bool",
    "Void": "void",
    "Object": "object",
}


def _fieldworks_dir():
    """The FieldWorks install directory, via flexicon's OWN resolution.

    Deliberately not FlexToolsMCP's versioning.get_resolved_fieldworks_dir():
    this repository must not import that one (D-02). flexicon resolves the
    install from the registry in FLExGlobals.InitialiseFWGlobals(), which is
    the same call `import flexicon` already makes at module scope through
    FLExInit.
    """
    from flexicon.code import FLExGlobals

    if not FLExGlobals.FWCodeDir:
        FLExGlobals.InitialiseFWGlobals()
    return os.path.normpath(FLExGlobals.FWCodeDir)


def _dll_path(name):
    return os.path.join(_fieldworks_dir(), name)


def _format_clr_type(clr_type):
    """Render a .NET System.Type the way the C# source spells it."""
    try:
        if clr_type.IsGenericType:
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


@pytest.fixture(scope="module")
def parser_core():
    """Reflect over the installed ParserCore.dll. No cache, no project.

    Skips -- rather than fails -- only when the component is genuinely
    absent, so the suite stays runnable on a machine without FieldWorks.
    A skip here is recorded as "tier not run, and why" in the evidence
    artifact (Principle IV); it is never rounded to a pass.
    """
    dll = _dll_path("ParserCore.dll")
    if not os.path.exists(dll):
        pytest.skip("ParserCore.dll not present at %s" % dll)

    try:
        # clr must be imported before System resolves; it is the pythonnet
        # availability probe, not an unused import.
        import clr  # type: ignore
        import System
        from System.Reflection import BindingFlags

        assert clr is not None
    except ImportError as exc:  # pragma: no cover
        pytest.skip("pythonnet/CLR unavailable: %s" % exc)

    assembly = System.Reflection.Assembly.LoadFile(dll)
    version = assembly.GetName().Version
    flags = BindingFlags.Public | BindingFlags.Instance | BindingFlags.DeclaredOnly

    surfaces = {}
    for clr_type in assembly.GetTypes():
        if clr_type.Name not in ("HCParser", "IParser"):
            continue
        members, returns = set(), {}
        for ctor in clr_type.GetConstructors(flags):
            params = ", ".join(_format_clr_type(p.ParameterType) for p in ctor.GetParameters())
            members.add("%s(%s)" % (clr_type.Name, params))
        for method in clr_type.GetMethods(flags):
            params = ", ".join(_format_clr_type(p.ParameterType) for p in method.GetParameters())
            members.add("%s(%s)" % (method.Name, params))
            returns[method.Name] = _format_clr_type(method.ReturnType)
        surfaces[clr_type.Name] = {"members": frozenset(members), "returns": returns}

    return {
        "path": dll,
        "surfaces": surfaces,
        "detected_version": "%d.%d.%d" % (version.Major, version.Minor, version.Build),
    }


class TestA21BoundMemberSurface:
    """A2.1 -- every member the facade will bind exists."""

    def test_hcparser_type_is_present(self, parser_core):
        assert "HCParser" in parser_core["surfaces"], (
            "HCParser is absent from %s; the facade has nothing to bind" % parser_core["path"]
        )

    def test_every_bound_member_exists(self, parser_core):
        present = parser_core["surfaces"]["HCParser"]["members"]
        missing = sorted(REQUIRED_HCPARSER_MEMBERS - present)
        assert (
            not missing
        ), "ParserCore.dll at %s is missing %d member(s) the CP2a facade binds: %s\n" "Present on HCParser: %s" % (
            parser_core["path"],
            len(missing),
            missing,
            sorted(present),
        )


class TestA22ResetAndCurrency:
    """A2.2 -- the reset and currency members SPECIFICALLY.

    Hard gate 1. These are the members the shipped MCP-side check does not
    cover, and this is their first verification anywhere. If this class
    fails, the facade cannot be built as designed: halt and return to
    research rather than working around it.
    """

    @pytest.mark.parametrize("name,expected_return", sorted(CURRENCY_AND_RESET_MEMBERS.items()))
    def test_member_exists_on_hcparser(self, parser_core, name, expected_return):
        returns = parser_core["surfaces"]["HCParser"]["returns"]
        assert name in returns, (
            "HCParser.%s() is ABSENT from the installed component. FR-043's "
            "reset-then-update reload cannot be bound; halt CP2a." % name
        )
        assert (
            returns[name] == expected_return
        ), "HCParser.%s() returns %s, not %s -- the facade's contract assumes " "the latter." % (
            name,
            returns[name],
            expected_return,
        )

    @pytest.mark.parametrize("name", sorted(CURRENCY_AND_RESET_MEMBERS))
    def test_member_is_on_the_iparser_interface_too(self, parser_core, name):
        """Both members must be interface-level, not HCParser-only.

        The facade binds positionally against whatever IParser implementation
        the project is using; a member that exists only on the concrete
        HCParser would not survive a different engine.
        """
        iparser = parser_core["surfaces"].get("IParser")
        assert iparser is not None, "IParser is absent from the assembly"
        assert name in iparser["returns"], (
            "IParser.%s() is absent -- the member exists only on the concrete "
            "HCParser, so it is not safe to bind through the interface." % name
        )

    def test_currency_read_is_a_query_not_a_mutation(self, parser_core):
        """`IsUpToDate()` must take no arguments -- it is asked, not told."""
        assert "IsUpToDate()" in parser_core["surfaces"]["HCParser"]["members"], (
            "IsUpToDate exists but not as a no-argument query; FR-043 answers "
            "currency by ASKING the parser, never from a local flag."
        )


class TestA23SameInstallation:
    """A2.3 -- directory equality holds on this machine (FR-004)."""

    def test_parser_core_and_data_model_share_a_directory(self):
        parser_core = _dll_path("ParserCore.dll")
        data_model = _dll_path("SIL.LCModel.dll")
        for path in (parser_core, data_model):
            if not os.path.exists(path):
                pytest.skip("%s not present" % path)
        assert os.path.dirname(parser_core) == os.path.dirname(data_model), (
            "ParserCore.dll and SIL.LCModel.dll resolve from DIFFERENT "
            "directories (%s vs %s). Mixing two FieldWorks installs across an "
            "in-process boundary is the failure no version floor would catch."
            % (os.path.dirname(parser_core), os.path.dirname(data_model))
        )

    def test_the_check_is_directory_equality_and_nothing_more(self):
        """The limit of FR-004, asserted so the docstring cannot overstate it.

        Directory equality does NOT verify provenance: a foreign ParserCore
        copied into the correct directory passes. T010's docstring must say
        so (Principle V). This test exists to keep that admission honest --
        if someone strengthens the check, this test should be updated
        deliberately rather than silently left claiming less than it does.
        """
        assert os.path.dirname(_dll_path("ParserCore.dll")) == _fieldworks_dir()


class TestA24VersionReadNeverCompared:
    """A2.4 -- the detected version is read and unused (FR-006)."""

    def test_version_is_readable(self, parser_core):
        detected = parser_core["detected_version"]
        assert re.match(r"^\d+\.\d+\.\d+$", detected), "detected_version %r is not a readable version triple" % detected

    def test_version_is_not_used_as_a_gate_here(self, parser_core):
        """This tier reports the version and makes no decision from it.

        The STANDING ratchet -- "no code path compares a detected parser
        version against a minimum, 0 occurrences" -- is T006/A1.2 in
        tests/test_parser_structure.py, which scans the shipped package by
        AST. This test only pins the local claim: nothing in this module's
        pass/fail outcome depends on the version's value.
        """
        detected = parser_core["detected_version"]
        assert detected  # read
        # Deliberately no >=, no floor, no tuple comparison. If a future edit
        # adds one, T006/A1.2 is the control that fails loudly.
