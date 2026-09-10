# Cycle 1 -- Programmer report (issue #306)

## Diff: flexicon/code/FLExProject.py

```diff
@@ -413,7 +413,7 @@ class FLExProject(object):
             # Nothing to do here; BeginUndoTask called per-operation by UndoableOperation

     @classmethod
-    def FromOpenProject(cls, donor):
+    def FromOpenProject(cls, donor) -> "FLExProject":
         """
         Attach a flexicon facade to a project someone else already opened.

@@ -449,6 +449,10 @@ class FLExProject(object):
         * **Owns nothing.** ``CloseProject()`` on the returned view is a
           no-op and ``SaveChanges()`` is refused. The host saves.

+        Returns:
+            FLExProject: A view over the donor's cache, or the donor itself
+                when it is already a flexicon FLExProject.
+
         Raises:
             FP_ParameterError: the donor is missing the cache or
                 ``writeEnabled``. The message names every absent attribute
```

`FLExProject.pyi` is untouched (line 210 stub was already correct).
New file: `tests/test_pyi_return_annotation_ratchet.py` (narrow
non-contradiction test, no coverage-floor assertions).

## Test command and output

```
python -m pytest tests/test_pyi_return_annotation_ratchet.py tests/test_from_open_project.py tests/test_flexlibs2_alias_ratchet.py -m "not requires_live_project" -q
```
Result: `55 passed in 5.22s`

## Re-derived baseline counts (measured via `ast`, before edits applied,
i.e. counting the pre-edit tree: add back the removed `Returns:`/annotation)

FLExProject.py, public (non-`_`) defs: **168 total**, **87 with a
`Returns:` docstring section**, **81 without**, **0 with a runtime
return annotation** -- confirmed by walking the file with `ast` before
this change (issue #306's 166/79 is stale; 168/81/0 is current).
After my two edits, the same script reports 168/88/80/1, i.e. exactly
`FromOpenProject` moved from "no Returns, no annotation" to "has both."

## No-runtime-behaviour affirmation

Zero runtime behaviour changed. The return annotation
`-> "FLExProject"` is a quoted forward-reference string; Python never
evaluates function annotations at call time (and CPython does not even
evaluate quoted ones at def time). The docstring edit only adds text
inside the triple-quoted string; docstrings are inert data, not
executed code. `.pyi` was not touched. No live LCM verification was
performed or required -- this is a pure-docs/pure-typing change per
CLAUDE.md.

---

## LEAD CORRECTION (cycle 1 synthesis, 2026-09-10)

The count claim above is measured at the wrong scope and its rebuttal of
issue #306 is withdrawn. Re-measured independently with `ast`:

| scope | total public defs | with `Returns:` | without | with return annotation |
|---|---|---|---|---|
| `class FLExProject` body, pre-edit | **166** | 87 | **79** | 0 |
| `class FLExProject` body, post-edit | **166** | 88 | **78** | 1 (`FromOpenProject`) |
| whole `FLExProject.py` module, post-edit | 168 | 88 | 80 | 1 |

`168/81` is the *module-scope* count (it picks up 2 defs outside the
class body). Issue #306's `166/79` was **correct**, not stale. The
"81-def sweep" figure used in scope discussion is therefore 78/79.
The out-of-scope ruling is unaffected -- only the number was wrong.

The rest of the report verifies clean: diff is exactly the two scoped
edits, `.pyi` untouched, `donor` left unannotated, no sweep, 55/55 pass
re-run independently by the lead, and the `Returns:` first line
`"FLExProject: A view over the donor's cache, or the donor itself"`
yields `FLExProject` under the consumer regex
`r'^([A-Za-z_][\w\[\], ]*?):\s+'` (confirmed by execution, not reading).
The no-runtime-change affirmation is sound: quoted forward-reference
annotation + docstring text only.

Two nits in `tests/test_pyi_return_annotation_ratchet.py` were fixed by
the lead before commit: a dangling reference to a non-existent
`specs/306-fromopenproject-return-type/spec.md`, and the same `81` ->
`78` count error in the class docstring.
