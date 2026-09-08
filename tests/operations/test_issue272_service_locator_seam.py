#
#   test_issue272_service_locator_seam.py
#
#   Regression guard + mock coverage for issue #272:
#   "Complex-form write API is dead on arrival: ServiceLocator.GetInstance
#    sites never migrated to GetFactory (#124)".
#
#   Background (verified by offline reflection over LibLCM 11.0.0):
#
#       SIL.LCModel.ILcmServiceLocator declares NO GetInstance member.
#       Its only base interface is System.IServiceProvider, i.e.
#       GetService(Type). Pythonnet types the object returned by
#       LcmCache.ServiceLocator as that interface, so every
#       `ServiceLocator.GetInstance(...)` call raises
#       AttributeError: 'ILcmServiceLocator' object has no attribute
#       'GetInstance' at runtime -- which is exactly what production
#       logs showed for the complex-form write API.
#
#       The concrete implementation (SIL.LCModel.IOC.
#       StructureMapServiceLocator) DOES declare GetInstance<T>(),
#       GetInstance(Type), GetInstance(Type, String) and
#       GetInstance<T>(String) -- which is why FLExProject.GetFactory's
#       reflection path can reach it, and why the raw interface-level
#       call cannot.
#
#   The AST guard below is the missing piece that let #124 regress: it
#   fails on ANY new GetInstance call site in the shipped package
#   outside FLExProject.GetFactory itself.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import ast
import os
import sys
from types import SimpleNamespace

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

PACKAGE_ROOT = os.path.join(_project_root, "flexicon")

# The ONLY sanctioned GetInstance call site in the shipped package.
# Keyed by (path relative to the package root, enclosing function name).
# Every entry needs a reason; nothing gets added here without one.
GETINSTANCE_ALLOWLIST = {
    (
        os.path.join("code", "FLExProject.py"),
        "GetFactory",
    ): (
        "GetFactory is the resolution seam itself: Path 1 is the direct "
        "GetInstance(Type) call, kept because it binds cleanly on "
        "pythonnet builds that surface the concrete locator, with "
        "reflection over GetInstance<T>() and finally GetService(Type) "
        "as fallbacks."
    ),
}


def _iter_package_sources():
    for dirpath, dirnames, filenames in os.walk(PACKAGE_ROOT):
        dirnames[:] = [
            d for d in dirnames
            if d not in {"__pycache__", ".pytest_cache"}
        ]
        for filename in filenames:
            if filename.endswith(".py"):
                yield os.path.join(dirpath, filename)


def _getinstance_call_sites():
    """
    Every real `<expr>.GetInstance(...)` call in the shipped package.

    Uses the AST rather than a text grep so that comments, docstrings
    and prose about the historical bug do not trip the guard -- only
    executable call sites count.

    Returns:
        list[tuple[str, int, str]]: (relative path, line number,
            enclosing function name or '<module>').
    """
    sites = []
    for path in _iter_package_sources():
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source, filename=path)

        # Map every node to its enclosing function, so the allowlist can
        # be scoped to a function rather than to a whole file.
        enclosing = {}

        def walk(node, current):
            for child in ast.iter_child_nodes(node):
                if isinstance(
                    child, (ast.FunctionDef, ast.AsyncFunctionDef)
                ):
                    enclosing[child] = child.name
                    walk(child, child.name)
                else:
                    enclosing[child] = current
                    walk(child, current)

        walk(tree, "<module>")

        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Attribute)
                and node.func.attr == "GetInstance"
            ):
                sites.append(
                    (
                        os.path.relpath(path, PACKAGE_ROOT),
                        node.lineno,
                        enclosing.get(node, "<module>"),
                    )
                )
    return sites


class TestNoRawGetInstanceCallSites:
    """
    The regression guard issue #272 asks for.

    #124 scheduled this migration, closed without performing it, and
    nothing failed -- so nine months of new call sites accumulated. A
    failing test is the only thing that stops that recurring.
    """

    def test_no_getinstance_outside_getfactory(self):
        offenders = [
            site for site in _getinstance_call_sites()
            if (site[0], site[2]) not in GETINSTANCE_ALLOWLIST
        ]
        assert not offenders, (
            "ServiceLocator.GetInstance(...) is unreachable through the "
            "ILcmServiceLocator interface pythonnet sees (it declares no "
            "GetInstance member at all; its only base is "
            "System.IServiceProvider). Use project.GetFactory(iface) for "
            "factories or project.GetService(iface) for services and "
            "repositories. New raw call sites:\n"
            + "\n".join(
                f"  flexicon/{path}:{lineno} in {func}()"
                for path, lineno, func in offenders
            )
        )

    def test_allowlist_entries_still_exist(self):
        """
        A stale allowlist is a silent hole. Every allowlisted (file,
        function) pair must still contain a GetInstance call, otherwise
        the entry has to be deleted rather than left as a standing
        exemption.
        """
        present = {(path, func) for path, _, func in _getinstance_call_sites()}
        stale = [key for key in GETINSTANCE_ALLOWLIST if key not in present]
        assert not stale, (
            "GETINSTANCE_ALLOWLIST has entries with no corresponding "
            f"GetInstance call any more; delete them: {stale}"
        )


class TestMigratedCallSitesUseTheSeam:
    """
    Each site listed in issue #272 must resolve through the seam.

    Checked at the AST level against the enclosing method, so a future
    edit that reintroduces a raw ServiceLocator lookup in one of these
    specific methods fails here with a pointed message, not just in the
    package-wide guard above.
    """

    # (relative path, method name, expected seam attribute)
    EXPECTED = [
        (os.path.join("code", "FLExProject.py"),
         "LexiconAddComplexForm", "GetFactory"),
        (os.path.join("code", "Lexicon", "LexEntryOperations.py"),
         "AddComplexFormComponent", "GetFactory"),
        (os.path.join("code", "Lists", "PossibilityListOperations.py"),
         "CreateList", "GetFactory"),
        (os.path.join("code", "System", "CheckOperations.py"),
         "_GetOrCreateCheckList", "GetFactory"),
        (os.path.join("code", "Lists", "ConfidenceOperations.py"),
         "GetAnalysesWithConfidence", "GetService"),
        (os.path.join("code", "Lists", "ConfidenceOperations.py"),
         "GetGlossesWithConfidence", "GetService"),
        (os.path.join("code", "Lists", "TranslationTypeOperations.py"),
         "GetTextsWithType", "GetService"),
        (os.path.join("code", "System", "AnnotationDefOperations.py"),
         "GetAll", "GetService"),
    ]

    @staticmethod
    def _method_source(rel_path, method_name):
        path = os.path.join(PACKAGE_ROOT, rel_path)
        with open(path, "r", encoding="utf-8") as handle:
            source = handle.read()
        tree = ast.parse(source, filename=path)
        for node in ast.walk(tree):
            if (
                isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef))
                and node.name == method_name
            ):
                return node
        return None

    @pytest.mark.parametrize(
        "rel_path,method_name,seam",
        EXPECTED,
        ids=[f"{p}::{m}" for p, m, _ in EXPECTED],
    )
    def test_site_resolves_through_seam(self, rel_path, method_name, seam):
        node = self._method_source(rel_path, method_name)
        assert node is not None, (
            f"{rel_path} no longer defines {method_name}(); issue #272's "
            "call-site inventory needs updating."
        )

        seam_calls = [
            n for n in ast.walk(node)
            if isinstance(n, ast.Call)
            and isinstance(n.func, ast.Attribute)
            and n.func.attr == seam
        ]
        assert seam_calls, (
            f"{rel_path}::{method_name}() no longer calls {seam}(). "
            "Factories and repositories must be resolved through "
            "FLExProject.GetFactory / FLExProject.GetService -- a raw "
            "ServiceLocator.GetInstance call raises AttributeError at "
            "runtime (issue #272)."
        )

    def test_operations_sites_call_seam_on_the_wrapper_not_the_cache(self):
        """
        Receiver check. Inside an Operations class ``self.project`` is
        the FLExProject wrapper and ``self.project.project`` is the raw
        LcmCache. GetFactory/GetService live on the wrapper, so the
        correct receiver is ``self.project`` -- calling
        ``self.project.project.GetFactory(...)`` would swap one
        AttributeError for another.
        """
        bad = []
        for rel_path, method_name, seam in self.EXPECTED:
            if rel_path == os.path.join("code", "FLExProject.py"):
                continue  # inside FLExProject the receiver is `self`
            node = self._method_source(rel_path, method_name)
            for call in ast.walk(node):
                if not (
                    isinstance(call, ast.Call)
                    and isinstance(call.func, ast.Attribute)
                    and call.func.attr == seam
                ):
                    continue
                receiver = call.func.value
                ok = (
                    isinstance(receiver, ast.Attribute)
                    and receiver.attr == "project"
                    and isinstance(receiver.value, ast.Name)
                    and receiver.value.id == "self"
                )
                if not ok:
                    bad.append(
                        f"flexicon/{rel_path}:{call.lineno} in "
                        f"{method_name}()"
                    )
        assert not bad, (
            "Seam called on the wrong receiver; expected "
            f"self.project.<seam>(...): {bad}"
        )


class _LocatorWithoutGetInstance:
    """
    Stands in for the ILcmServiceLocator surface pythonnet actually
    hands back: no GetInstance member, only GetService(Type).

    Reproduces the production failure from issue #272 exactly --
    attribute access on GetInstance raises AttributeError -- and lets
    the resolution seam be exercised without a live project.
    """

    def __init__(self, resolved):
        self._resolved = resolved
        self.get_service_calls = []

    def __getattr__(self, name):
        # Mirrors pythonnet: the interface has no such member.
        raise AttributeError(
            f"'ILcmServiceLocator' object has no attribute '{name}'"
        )

    def GetService(self, interface_type):
        self.get_service_calls.append(interface_type)
        return self._resolved

    def GetType(self):
        # No GetInstance<T>() reachable by reflection either, so
        # GetFactory must fall through to GetService.
        return SimpleNamespace(GetMethods=lambda: [])


class TestGetFactoryFallsBackWhenGetInstanceIsMissing:
    """
    Mock-level cover for the seam itself.

    Before #272 the call sites bypassed this entirely; the point of
    these tests is that the seam survives a locator with no reachable
    GetInstance, which is the shape LibLCM 11.0.0 actually presents.
    """

    def test_getfactory_resolves_via_getservice(self):
        from flexicon.code.FLExProject import FLExProject

        sentinel = object()
        locator = _LocatorWithoutGetInstance(sentinel)
        project = FLExProject.__new__(FLExProject)
        project.project = SimpleNamespace(ServiceLocator=locator)

        assert project.GetFactory("ILexEntryRefFactory") is sentinel
        assert locator.get_service_calls == ["ILexEntryRefFactory"]

    def test_getfactory_rejects_none(self):
        from flexicon.code.FLExProject import (
            FLExProject,
            FP_NullParameterError,
        )

        project = FLExProject.__new__(FLExProject)
        project.project = SimpleNamespace(
            ServiceLocator=_LocatorWithoutGetInstance(object())
        )

        with pytest.raises(FP_NullParameterError):
            project.GetFactory(None)

    def test_raw_getinstance_on_such_a_locator_raises(self):
        """
        Sanity anchor: the pre-fix code shape really does blow up, so a
        green run of the tests above means something.
        """
        locator = _LocatorWithoutGetInstance(object())
        with pytest.raises(AttributeError, match="GetInstance"):
            locator.GetInstance("ILexEntryRefFactory")


class TestLexiconAddComplexFormUsesTheSeam:
    """
    Behavioural mock test for the headline broken entry point.

    This is the test that would have caught #272: it drives
    LexiconAddComplexForm with a locator that has no GetInstance, which
    is what production had. Pre-fix it raises AttributeError and the
    transaction rolls back; post-fix the entry ref is created.
    """

    def test_complex_form_ref_is_created_through_getfactory(
        self, monkeypatch
    ):
        from contextlib import contextmanager

        from flexicon.code.FLExProject import FLExProject

        created_ref = SimpleNamespace(
            ComponentLexemesRS=SimpleNamespace(
                appended=[],
            ),
            ComplexEntryTypesRS=SimpleNamespace(appended=[]),
            RefType=None,
            HideMinorEntry=None,
        )
        # Model .Add(), the member ILcmReferenceSequence<T> actually
        # exposes. This stub originally mirrored .Append(), which does
        # not exist on the interface -- so the mock passed against the
        # dead production code. Live verification caught it; the stub
        # now models the real API. (issue #272)
        created_ref.ComponentLexemesRS.Add = (
            created_ref.ComponentLexemesRS.appended.append
        )
        created_ref.ComplexEntryTypesRS.Add = (
            created_ref.ComplexEntryTypesRS.appended.append
        )

        factory = SimpleNamespace(Create=lambda: created_ref)
        locator = _LocatorWithoutGetInstance(factory)

        project = FLExProject.__new__(FLExProject)
        project.project = SimpleNamespace(ServiceLocator=locator)

        @contextmanager
        def _no_transaction(label):
            yield

        monkeypatch.setattr(project, "_TransactionCM", _no_transaction)

        entry = SimpleNamespace(EntryRefsOS=SimpleNamespace(added=[]))
        entry.EntryRefsOS.Add = entry.EntryRefsOS.added.append

        component_a = SimpleNamespace(name="black")
        component_b = SimpleNamespace(name="board")
        cf_type = SimpleNamespace(name="Compound")

        result = project.LexiconAddComplexForm(
            entry, [component_a, component_b], cf_type
        )

        assert result is created_ref
        assert entry.EntryRefsOS.added == [created_ref]
        assert created_ref.ComponentLexemesRS.appended == [
            component_a,
            component_b,
        ]
        assert created_ref.ComplexEntryTypesRS.appended == [cf_type]

        # RefType must be stamped krtComplexForm. A fresh ILexEntryRef
        # defaults to 0 == krtVariant, so omitting it silently filed the
        # components under a VARIANT reference and the entry was never a
        # complex form -- GetComplexFormComponents(), which filters on
        # krtComplexForm, then returned []. Caught by live verification
        # once the GetFactory migration unblocked this code path.
        from SIL.LCModel import LexEntryRefTags

        assert created_ref.RefType == LexEntryRefTags.krtComplexForm, (
            "LexiconAddComplexForm must set RefType = krtComplexForm; "
            f"got {created_ref.RefType!r}"
        )
        assert created_ref.HideMinorEntry == 0


class TestAudioPathBuilderMechanics:
    """
    Offline cover for the three string-argument sites in issue #272
    (FLExProject.py GetAudioPath / SetAudioPath).

    Those sites called ``ServiceLocator.GetInstance("TsStrBldr")`` and
    ``GetInstance("ITsPropsBldr")`` -- string lookups that cannot
    resolve through ILcmServiceLocator -- and derived the ObjData
    property tag as ``ord("k")`` (107) instead of
    ``FwTextPropType.ktptObjData`` (6).

    The replacement is ``TsStringUtils.MakeStrBldr()`` /
    ``MakePropsBldr()``, which need no ServiceLocator and no open
    project at all: this test proves the exact builder sequence
    SetAudioPath now uses round-trips through the tag GetAudioPath
    reads. Skips if LibLCM is not loadable in this environment.
    """

    @staticmethod
    def _lcm():
        try:
            from flexicon.code.FLExInit import FLExInitialize

            try:
                FLExInitialize()
            except Exception:
                # Already initialized, or a no-op in this environment;
                # the imports below are the real gate.
                pass
            from SIL.LCModel.Core.KernelInterfaces import (
                FwObjDataTypes,
                FwTextPropType,
            )
            from SIL.LCModel.Core.Text import TsStringUtils
        except Exception as exc:  # pragma: no cover - env dependent
            pytest.skip(f"LibLCM not loadable offline: {exc}")
        return TsStringUtils, FwTextPropType, FwObjDataTypes

    def test_objdata_tag_is_not_ord_k(self):
        _, prop_type, obj_types = self._lcm()
        assert int(prop_type.ktptObjData) != ord("k"), (
            "ord('k') was the tag the pre-fix SetAudioPath used"
        )
        assert int(prop_type.ktptObjData) == 6
        assert int(obj_types.kodtExternalPathName) == 4

    def test_builders_need_no_service_locator(self):
        ts_string_utils, prop_type, obj_types = self._lcm()

        tag = int(prop_type.ktptObjData)
        file_path = "LinkedFiles/AudioVisual/TEST_issue272.wav"
        obj_data = chr(int(obj_types.kodtExternalPathName)) + file_path

        # Exactly the sequence SetAudioPath performs.
        bldr = ts_string_utils.MakeStrBldr()
        bldr.Clear()
        bldr.Replace(0, 0, "￼", None)
        props_bldr = ts_string_utils.MakePropsBldr()
        props_bldr.SetStrPropValue(tag, obj_data)
        bldr.SetProperties(0, 1, props_bldr.GetTextProps())
        tss = bldr.GetString()

        # Exactly the read GetAudioPath performs.
        assert tss.Length == 1
        read_back = tss.get_Properties(0).GetStrPropValue(tag)
        assert read_back is not None
        assert read_back[0] == chr(int(obj_types.kodtExternalPathName))
        assert read_back[1:] == file_path
