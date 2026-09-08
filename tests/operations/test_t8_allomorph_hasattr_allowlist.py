#
#   test_t8_allomorph_hasattr_allowlist.py
#
#   Class: TestAllomorphHasattrAllowlistModuleWide
#          Cycle-17 Checkpoint 5 gate, LEG 2 -- closes the coverage gap
#          identified by the cycle-17 archivist
#          (reviews/cycle17-archivist-leg2-static.md): the shipped AST
#          test in test_t8_allomorph_feature_sync.py only enumerates
#          GetSyncableProperties by NAME. Nine other call sites of
#          __GetAllomorphObject (GetForm, SetForm, SetFormAudio,
#          GetFormAudio, GetMorphType, SetMorphType, GetPhoneEnv,
#          AddPhoneEnv, RemovePhoneEnv) are free to gain a new hasattr
#          probe on the resolved allomorph object with NEITHER shipped
#          test noticing.
#
#   This test scopes MODULE-WIDE (ast.walk over the whole file, not
#   inspect.getsource per named function) and filters by FIRST-ARGUMENT
#   IDENTITY: only hasattr(...) calls whose first argument is a bare
#   Name node with .id == "allomorph". This is deliberate, NOT a total
#   hasattr count -- the module has SEVEN hasattr calls total: four in
#   Delete/Duplicate probe `owner`/`parent` (unrelated resolver-owner
#   checks, out of scope here) and three in GetSyncableProperties probe
#   `allomorph` (in scope). A "hasattr count == 3" or "== 7" assertion
#   would be right for the wrong reason in either direction; this test
#   asserts on the (function, literal) identity of the allomorph-scoped
#   subset only.
#
#   Residual limitation (disclosed, not hidden): this scoping is
#   defeated only if a future edit renames the resolved-object local
#   variable away from `allomorph` in the SAME statement that adds a
#   new hasattr call -- not a silent one-line addition, so acceptable
#   per the archivist's stated threat model.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import ast
import inspect

import pytest


@pytest.fixture(autouse=True)
def _require_lcmodel():
    """AllomorphOperations has module-level SIL.LCModel imports."""
    pytest.importorskip("SIL.LCModel")


def _module_source():
    from flexicon.code.Lexicon import AllomorphOperations as mod

    return inspect.getsource(mod)


def _enclosing_function_name(tree, call_node):
    """Find the nearest enclosing FunctionDef for an ast.Call node."""
    best = None
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            for child in ast.walk(node):
                if child is call_node:
                    # Prefer the innermost enclosing function found.
                    if best is None or (
                        node.lineno >= best.lineno and node.end_lineno <= best.end_lineno
                    ):
                        best = node
    return best.name if best is not None else None


def _allomorph_scoped_hasattr_calls(tree):
    """
    Return a list of (enclosing_fn_name, second_arg_literal) for every
    hasattr(...) call in the WHOLE module whose first argument is a
    bare Name identified as `allomorph`.
    """
    results = []
    for node in ast.walk(tree):
        if not (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "hasattr"
        ):
            continue
        if len(node.args) < 2:
            continue
        first_arg = node.args[0]
        if not (isinstance(first_arg, ast.Name) and first_arg.id == "allomorph"):
            continue
        second_arg = node.args[1]
        assert isinstance(second_arg, ast.Constant) and isinstance(
            second_arg.value, str
        ), f"hasattr(allomorph, ...) with a non-literal second argument: {ast.dump(node)}"
        fn_name = _enclosing_function_name(tree, node)
        results.append((fn_name, second_arg.value))
    return results


class TestAllomorphHasattrAllowlistModuleWide:
    """
    Module-wide, first-argument-identity-scoped allowlist. Supersedes
    needing to enumerate all 15 AllomorphOperations methods by name --
    Delete/Duplicate's probes target `owner`/`parent`, not `allomorph`,
    so they are naturally excluded and remain free to change.
    """

    def test_exactly_three_allomorph_scoped_hasattr_calls_module_wide(self):
        src = _module_source()
        tree = ast.parse(src)
        results = _allomorph_scoped_hasattr_calls(tree)

        assert len(results) == 3, (
            f"Expected exactly 3 hasattr(allomorph, ...) calls anywhere in "
            f"AllomorphOperations.py, found {len(results)}: {results}. "
            f"A new hasattr probe on the resolved allomorph object has "
            f"been added somewhere in the module -- confirm it belongs "
            f"in the T7/R16-2 allowlist (Form/IsAbstract/MorphTypeRA, "
            f"GetSyncableProperties only) before letting this pass."
        )

        expected = {
            ("GetSyncableProperties", "Form"),
            ("GetSyncableProperties", "IsAbstract"),
            ("GetSyncableProperties", "MorphTypeRA"),
        }
        assert set(results) == expected, (
            f"hasattr(allomorph, ...) call set changed: got {sorted(results)}, "
            f"expected {sorted(expected)}. This test is MODULE-WIDE (not "
            f"scoped to a named-function list), so a probe newly added in "
            f"GetForm, SetForm, or any of the other 9 __GetAllomorphObject "
            f"call sites is caught here even though the pre-existing "
            f"per-function test in test_t8_allomorph_feature_sync.py would "
            f"miss it."
        )

    def test_seven_total_hasattr_calls_not_asserted_as_a_gate(self):
        """
        Documents (does not gate on) the total: 7 hasattr calls exist in
        the module (4 owner/parent in Delete/Duplicate + 3 allomorph in
        GetSyncableProperties). This test exists so a reader does not
        mistake "3" above for "the only hasattr calls in the file" --
        the archivist's G2b finding is that a naive "count == 3" test
        would be WRONG for the whole-file scope. This test is
        informational: it fails loudly (not silently) if the owner/
        parent probes are removed or a truly new non-allomorph hasattr
        appears, so a reader investigates rather than assuming the
        allowlist test above is the only place a change would surface.
        """
        src = _module_source()
        tree = ast.parse(src)
        total = sum(
            1
            for node in ast.walk(tree)
            if isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id == "hasattr"
        )
        assert total == 7, (
            f"Total hasattr() call count in AllomorphOperations.py changed: "
            f"{total} (expected 7 -- 4 owner/parent in Delete/Duplicate + "
            f"3 allomorph in GetSyncableProperties). This is informational, "
            f"not a re-statement of the allomorph-scoped allowlist above; "
            f"investigate which bucket changed."
        )
