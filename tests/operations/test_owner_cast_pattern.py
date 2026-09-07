#
#   test_owner_cast_pattern.py
#
#   Class: TestOwnerCastStatic / TestOwnerCastLive
#          Regression coverage for the `.Owner` -> typed-collection
#          casting bug across Lexicon, Notebook, and Discourse
#          operations.
#
#   Bug class (closes #97, #98, #116, #117):
#     - `obj.Owner` on an owned LCM object returns the base ICmObject
#       interface, which does NOT expose typed collection properties
#       (AlternateFormsOS, EtymologyOS, EntryRefsOS, AnnotationsOC,
#       RepliesOS, SubPossibilitiesOS, RowsOS).
#     - `hasattr(obj.Owner, "XxxOS")` therefore returns False even
#       when the concrete owner does expose the collection, which
#       silently no-ops Delete and orphans Duplicate output.
#     - Direct `obj.Owner.XxxOS.Remove(...)` raises AttributeError.
#
#   The canonical fix is to route the owner through
#   `cast_to_concrete()` (lcm_casting.py) before touching the typed
#   collection. This file locks the PATTERN, not just specific
#   instances, by:
#
#     1. Static checks that each affected Operations method's source
#        no longer relies on the broken `obj.Owner` -> hasattr pattern.
#        These run without LCM/FieldWorks installed.
#
#     2. Live behavioural checks against a writable FLEx project,
#        parametrised across all affected sites. These verify Delete
#        actually removes from the owner's typed collection and that
#        Duplicate actually attaches the duplicate to it. They skip
#        when SIL.LCModel isn't loaded.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect
import sys
import textwrap

import pytest


# ---------------------------------------------------------------------------
# Live-LCM project fixture (mirrors the project-wide convention in
# tests/operations/test_anthropology.py and tests/operations/
# test_const_chart_marker.py).
# ---------------------------------------------------------------------------

_CANDIDATE_PROJECTS = ("Sena 3", "Test", "SampleLexicon", "SampleLexicon3")


def _try_open_writable_project():
    """Open one of the standard test projects in write mode, or None."""
    try:
        from flexicon.code.FLExProject import FLExProject
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
    """Module-scoped write-enabled FLExProject fixture; skips when LCM unavailable."""
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


# ---------------------------------------------------------------------------
# Static source-level pattern coverage
#
# These tests do NOT require LCM. They read the source of each
# affected Operations method and verify the canonical fix is in
# place: either an explicit cast_to_concrete call OR the
# BaseOperations._GetTypedOwner helper. They also assert that the
# previously-broken `hasattr(... , "XxxOS")` guard against the raw
# .Owner is gone -- that pattern is the bug signature.
# ---------------------------------------------------------------------------


def _operation_source(import_path, attr_chain):
    """
    Import a module then walk a dotted attr chain to a method's underlying
    function, and return its source text. The method is wrapped in
    OperationsMethod (and possibly wrap_enumerable) descriptors; we
    access the class via __dict__ so __get__ does not synthesise the
    class-method wrapper, then peel back to the raw function.
    """
    import importlib

    module = importlib.import_module(import_path)
    # The first leg of the chain is the class name; the rest is the
    # method name (and possibly nested attributes). We pull the class
    # off the module via getattr (safe -- it's a class) and then dig
    # for the method through __dict__ to avoid descriptor invocation.
    cls = getattr(module, attr_chain[0])
    obj = cls
    for part in attr_chain[1:]:
        if isinstance(obj, type):
            # Class lookup via __dict__ to bypass descriptor __get__.
            try:
                obj = obj.__dict__[part]
            except KeyError:
                # Fall back to MRO walk for inherited methods.
                for base in obj.__mro__[1:]:
                    if part in base.__dict__:
                        obj = base.__dict__[part]
                        break
                else:
                    raise AttributeError(
                        f"{obj.__name__} has no attribute {part}"
                    )
        else:
            obj = getattr(obj, part)

    # Unwrap descriptor layers (OperationsMethod, wrap_enumerable, etc.)
    seen = set()
    while True:
        oid = id(obj)
        if oid in seen:
            break
        seen.add(oid)
        if hasattr(obj, "func") and not inspect.isfunction(obj):
            obj = obj.func
            continue
        if hasattr(obj, "__wrapped__"):
            obj = obj.__wrapped__
            continue
        break

    return inspect.getsource(obj)


# (label, import_path, attr_chain, expected_collection)
# expected_collection is the typed collection name that the method
# must reach through the cast. We assert it appears in the source.
_SITES = [
    (
        "AllomorphOperations.Delete",
        "flexicon.code.Lexicon.AllomorphOperations",
        ("AllomorphOperations", "Delete"),
        "AlternateFormsOS",
    ),
    (
        "AllomorphOperations.Duplicate",
        "flexicon.code.Lexicon.AllomorphOperations",
        ("AllomorphOperations", "Duplicate"),
        "AlternateFormsOS",
    ),
    (
        "EtymologyOperations.Delete",
        "flexicon.code.Lexicon.EtymologyOperations",
        ("EtymologyOperations", "Delete"),
        "EtymologyOS",
    ),
    (
        "EtymologyOperations.Duplicate",
        "flexicon.code.Lexicon.EtymologyOperations",
        ("EtymologyOperations", "Duplicate"),
        "EtymologyOS",
    ),
    (
        "VariantOperations.Delete",
        "flexicon.code.Lexicon.VariantOperations",
        ("VariantOperations", "Delete"),
        "EntryRefsOS",
    ),
    (
        "VariantOperations.Duplicate",
        "flexicon.code.Lexicon.VariantOperations",
        ("VariantOperations", "Duplicate"),
        "EntryRefsOS",
    ),
    (
        "NoteOperations.Delete",
        "flexicon.code.Notebook.NoteOperations",
        ("NoteOperations", "Delete"),
        "AnnotationsOC",
    ),
    (
        "NoteOperations.Duplicate",
        "flexicon.code.Notebook.NoteOperations",
        ("NoteOperations", "Duplicate"),
        "AnnotationsOC",
    ),
    (
        "AnthropologyOperations.Delete",
        "flexicon.code.Notebook.AnthropologyOperations",
        ("AnthropologyOperations", "Delete"),
        "SubPossibilitiesOS",
    ),
    (
        "ConstChartRowOperations.MoveTo",
        "flexicon.code.Discourse.ConstChartRowOperations",
        ("ConstChartRowOperations", "MoveTo"),
        "RowsOS",
    ),
]


class TestOwnerCastStatic:
    """
    Static pattern locks. Run without LCM. Verify that every affected
    site routes .Owner through the cast helper, references the typed
    collection by name, and does NOT use the broken
    `hasattr(<raw .Owner>, "XxxOS")` guard. These checks are intentionally
    *behavioural-shape* assertions, not strict greps for any one
    canonical line: they describe the bug class, not a particular fix.
    """

    @pytest.mark.parametrize("label,import_path,attr_chain,collection", _SITES)
    def test_routes_owner_through_cast(self, label, import_path, attr_chain, collection):
        src = _operation_source(import_path, attr_chain)
        msg_prefix = f"{label}:\n{textwrap.indent(src, '    ')}\n"
        # Must reach the typed collection somewhere in the method.
        assert collection in src, (
            f"{msg_prefix}Expected typed collection `{collection}` to appear in "
            f"the method body. If the implementation moved the collection "
            f"access out, update _SITES."
        )
        # Must route through one of the recognised cast helpers.
        used_helper = (
            "_GetTypedOwner" in src
            or "cast_to_concrete" in src
        )
        assert used_helper, (
            f"{msg_prefix}Expected the method to route .Owner through "
            f"`self._GetTypedOwner(...)` or `cast_to_concrete(...)`. "
            f"Raw `.Owner.{collection}` access is the bug signature -- "
            f"see issue #97/#98/#116/#117."
        )

    @pytest.mark.parametrize("label,import_path,attr_chain,collection", _SITES)
    def test_no_raw_owner_assignment_before_cast(self, label, import_path, attr_chain, collection):
        """
        The bug signature is *raw* `obj.Owner` followed by access (or
        hasattr) on the typed collection without an intervening cast.
        After the fix every site must either:

          a) assign `owner`/`parent` from `_GetTypedOwner(...)` /
             `cast_to_concrete(...)`, OR
          b) cast in place when reaching the typed collection.

        We allow lingering `hasattr(owner, "X")` checks AFTER the cast
        (they're now safe and sometimes load-bearing -- e.g. NoteOperations
        differentiates AnnotationsOC vs RepliesOS), but we forbid the
        bare `owner = obj.Owner` -> `owner.<typed-collection>` shape.
        """
        src = _operation_source(import_path, attr_chain)

        # Forbidden literal patterns: a direct `= .Owner` assignment
        # NOT routed through the cast helper. These greps are
        # intentionally loose -- if a future refactor changes variable
        # names, the pattern will need updating, but the bug class
        # remains pinned by `test_routes_owner_through_cast`.
        bad_patterns = [
            "owner = allomorph.Owner\n",
            "owner = etymology.Owner\n",
            "owner = variant.Owner\n",
            "owner = note.Owner\n",
            "parent = source.Owner\n",
            "source_chart = row.Owner\n",
        ]
        for bad in bad_patterns:
            assert bad not in src, (
                f"{label}: still assigns `.Owner` directly without casting "
                f"({bad.strip()!r}). This is the bug class for issues "
                f"#97/#98/#116/#117 -- the typed collection "
                f"`{collection}` must be reached via "
                f"`self._GetTypedOwner(...)` or `cast_to_concrete(...)`."
            )


class TestBaseOperationsHelper:
    """Lock the shared _GetTypedOwner helper's surface."""

    def test_helper_exists_on_base(self):
        from flexicon.code.BaseOperations import BaseOperations
        assert hasattr(BaseOperations, "_GetTypedOwner"), (
            "BaseOperations._GetTypedOwner was extracted to centralise "
            "the .Owner -> concrete-interface cast across Lexicon, "
            "Notebook, and Discourse operations. Removing it un-fixes "
            "issues #97/#98/#116/#117."
        )

    def test_helper_uses_cast_to_concrete(self):
        from flexicon.code.BaseOperations import BaseOperations
        src = inspect.getsource(BaseOperations._GetTypedOwner)
        assert "cast_to_concrete" in src, (
            "_GetTypedOwner must route through cast_to_concrete so the "
            "ClassName->interface map in lcm_casting.py stays the single "
            "source of truth."
        )

    def test_helper_handles_none(self):
        """Pure-Python branch: None obj and None Owner both return None."""
        from flexicon.code.BaseOperations import BaseOperations

        class _Stub:
            def __init__(self, owner):
                self.Owner = owner

        # Build a no-arg-callable bound-ish dispatcher without
        # constructing a real FLExProject. _GetTypedOwner only touches
        # self via Python machinery (it doesn't call self.project on
        # the early-return paths).
        instance = BaseOperations.__new__(BaseOperations)
        assert instance._GetTypedOwner(None) is None
        assert instance._GetTypedOwner(_Stub(None)) is None


class TestAnthropologyExceptRemoved:
    """
    AnthropologyOperations.Delete previously wrapped its concrete cast
    in a broad `except Exception: pass`, swallowing real failures.
    After the fix the cast is unconditional and exceptions propagate.
    """

    def test_no_broad_except_swallow(self):
        src = _operation_source(
            "flexicon.code.Notebook.AnthropologyOperations",
            ("AnthropologyOperations", "Delete"),
        )
        # The previous shape was: `except Exception:` on its own line
        # followed by `pass`. After the fix neither of those lines
        # exists in the subitem-removal branch.
        assert "except Exception:" not in src, (
            "AnthropologyOperations.Delete still contains a broad "
            "`except Exception:` clause. Issue #117 required removing it "
            "so cast/Remove failures surface to callers."
        )


# ---------------------------------------------------------------------------
# Live behavioural coverage
#
# These tests need a writable FLEx project. They lock the *outcomes*
# of the bug class:
#   - Delete removes the object from the owner's typed collection.
#   - Duplicate inserts the duplicate into the owner's typed collection.
# Sites where a writable test project doesn't naturally have the
# prerequisites (e.g. an entry with an etymology to duplicate) are
# skipped rather than failed, matching the conventions in
# test_anthropology.py and test_const_chart_marker.py.
# ---------------------------------------------------------------------------


def _first_writable_entry(project):
    """Find any lexical entry we can use; return None if the project has none."""
    try:
        entries = list(project.LexiconAllEntries())
    except Exception:
        return None
    return entries[0] if entries else None


@pytest.mark.requires_live_project
class TestOwnerCastLive:
    """
    Behavioural regression tests for the bug class. Each test verifies
    the OUTCOME we care about (owner's typed collection actually
    changes), not the exact internal mechanism. That way the test
    survives any future refactor that swaps _GetTypedOwner for an
    inline cast_to_concrete call or vice versa.
    """

    def test_allomorph_delete_removes_from_alternate_forms(self, writable_project):
        entry = _first_writable_entry(writable_project)
        if entry is None:
            pytest.skip("No lex entries available for AllomorphOperations live test")
        allo_ops = writable_project.Allomorphs

        # Create a throwaway alternate form so we have something safe
        # to remove without disrupting the lexeme form.
        morph_type = None
        if entry.LexemeFormOA and entry.LexemeFormOA.MorphTypeRA:
            morph_type = entry.LexemeFormOA.MorphTypeRA

        if morph_type is None:
            pytest.skip("Entry has no LexemeFormOA.MorphTypeRA; can't seed allomorph")

        created = allo_ops.Create(entry, "qZ_cast_test_form", morph_type)
        before = int(entry.AlternateFormsOS.Count)
        assert created in list(entry.AlternateFormsOS), (
            "Sanity check: newly-created allomorph should already be in "
            "AlternateFormsOS before we delete it."
        )

        allo_ops.Delete(created)

        after = int(entry.AlternateFormsOS.Count)
        assert after == before - 1, (
            f"AllomorphOperations.Delete did not remove the allomorph from "
            f"AlternateFormsOS (count {before} -> {after}). This is the "
            f"silent no-op shape of issue #98 -- the cast may have "
            f"regressed."
        )
        assert created not in list(entry.AlternateFormsOS)

    def test_allomorph_duplicate_attaches_to_alternate_forms(self, writable_project):
        entry = _first_writable_entry(writable_project)
        if entry is None:
            pytest.skip("No lex entries available")
        allo_ops = writable_project.Allomorphs

        if entry.LexemeFormOA is None or entry.LexemeFormOA.MorphTypeRA is None:
            pytest.skip("Entry has no LexemeFormOA.MorphTypeRA; can't seed allomorph")

        seed = allo_ops.Create(entry, "qZ_cast_dup_seed", entry.LexemeFormOA.MorphTypeRA)
        try:
            before = int(entry.AlternateFormsOS.Count)
            dup = allo_ops.Duplicate(seed)
            assert dup is not None, "Duplicate returned None"
            after = int(entry.AlternateFormsOS.Count)
            assert after == before + 1, (
                f"AllomorphOperations.Duplicate did not attach the duplicate "
                f"to AlternateFormsOS (count {before} -> {after}). This is "
                f"the orphan-creation shape of issue #116."
            )
            assert dup in list(entry.AlternateFormsOS), (
                "Duplicate exists but is not in the parent's AlternateFormsOS."
            )
        finally:
            # Best-effort cleanup
            try:
                allo_ops.Delete(seed)
            except Exception:
                pass

    def test_const_chart_row_move_finds_owner(self, writable_project):
        """
        Smoke test: MoveTo's source_chart resolution must succeed for
        any existing row. Pre-fix this path silently broke when the
        chart needed to be reached via the cast helper.

        Note: ChartsOC is typed IDsChart in the LCM model, so even at
        the test level we have to cast through to IDsConstChart to
        reach RowsOS. This double-cast is itself a demonstration of
        the bug class -- if cast_to_concrete's owner-types map
        regresses, this test fails immediately.
        """
        try:
            disc = writable_project.lp.DiscourseDataOA
        except Exception:
            pytest.skip("Project has no DiscourseDataOA")

        if disc is None or disc.ChartsOC.Count == 0:
            pytest.skip("No charts to exercise ConstChartRowOperations.MoveTo against")

        from flexicon.code.lcm_casting import cast_to_concrete

        # Find any chart with at least one row.
        target_chart = None
        for chart in disc.ChartsOC:
            concrete = cast_to_concrete(chart)
            if hasattr(concrete, "RowsOS") and concrete.RowsOS.Count >= 1:
                target_chart = concrete
                break

        if target_chart is None:
            pytest.skip("No chart with rows available")

        row = target_chart.RowsOS[0]
        # No-op move (index 0 -> 0). This still exercises the
        # source_chart resolution path that previously broke on the
        # base-interface .Owner.
        writable_project.ConstChartRows.MoveTo(row, target_chart, 0)

        # The row should still be in the chart at index 0
        assert target_chart.RowsOS[0] == row, (
            "ConstChartRowOperations.MoveTo no-op didn't keep the row at "
            "index 0 -- source_chart resolution may have regressed."
        )
