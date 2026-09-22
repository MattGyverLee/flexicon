# Cycle 1 design: outbound API surface ratchet (Principle VII / Gate 5)

## 1. Scope of "public"

Frozen surface = union of three AST-decidable sets, rooted at
`flexicon/__init__.py` (verified: 97 names bound via `from .code.X import
(...)`, incl. `version`, `CAPABILITIES`):

- **Set A -- top-level exports.** Every name bound in `__init__.py`:
  classes, functions, exceptions, constants. Existence+kind frozen for
  all; functions get a full signature record.
- **Set B -- exported classes' own public methods.** For each of the 66
  classes in Set A, every non-underscore method defined **directly in that
  class's body** -- the same "walk the body, don't touch the MRO" rule
  `test_pyi_return_annotation_ratchet.py` already uses for `FLExProject`.
- **Set B' -- `BaseOperations`'s own public methods** (`Count`, `Sort`,
  `MoveUp`, `MoveDown`, `MoveToIndex`, `MoveBefore`, `MoveAfter`, `Swap`,
  `GetSyncableProperties`, `ApplySyncableProperties`, `CompareTo` -- 11,
  confirmed by grep), frozen once under `BaseOperations.<method>`, not
  duplicated per subclass. `BaseOperations` is never imported at top
  level, but every Operations class inherits these without redefining
  them; omitting Set B' would leave the shared CRUD-adjacent surface
  unratcheted everywhere at once.

**Excluded:** private/underscore names; `flexicon.code.*` internals not
re-exported; `flexlibs2` (separate, already-ratcheted surface, see
collision note); `PythonicWrapper`'s dynamic `__getattr__` surface (AST
can't see it, named rather than silently skipped); test files; docstring
prose (`test_docstring_example_ratchet.py`'s job).

## 2. Signature capture

AST-based, no import, matching the repo's pattern. For each callable:
find its `FunctionDef`/`AsyncFunctionDef` and render params (name, kind --
POSITIONAL_ONLY / POSITIONAL_OR_KEYWORD / KEYWORD_ONLY / VAR_POSITIONAL /
VAR_KEYWORD -- and default as `ast.unparse(default_node)` **text, never
eval'd**, so `undoable=True` stays a diffable string, not a runtime
object). Returns: `ast.unparse(node.returns)` if annotated, else `null`
(non-contradiction only, same stance as #306's ratchet).

**Limitations:**
- `*args`/`**kwargs` capture presence, not the types callers actually
  pass.
- Decorators are recorded as unparsed text but not interpreted; a
  signature-rewriting decorator freezes the undecorated shape (same blind
  spot the pyi-ratchet already accepts).
- `@property` freezes as `kind: "property"`; flipping property<->method
  reads as a remove+add.
- Overloads: only the last same-named def survives the dict-lookup
  pattern borrowed from the pyi-ratchet -- known gap, not solved now.
- `PythonicWrapper.__getattr__` surface: not frozen at all, by
  construction (stated in Scope, repeated here for signature-capture
  context).

## 3. Baseline format

JSON, `tests/api_surface_baseline.json`, mirroring
`docstring_example_baseline.json`'s `_comment`/regeneration-pointer
convention, but with structured records (this ratchet diffs individual
fields, not just counts):

```json
{
  "_comment": ["Frozen outbound surface (Principle VII). Regenerate with",
    "python tests/test_api_surface_ratchet.py --baseline after an ADDITIVE",
    "change. Changed/removed entries need a BREAKING CHANGE: footer --",
    "see .githooks/api_surface_guard.py."],
  "scope_version": 1,
  "entries": {
    "normalize_text": {"kind": "function", "owner": null,
      "module": "flexicon.code.Shared.string_utils",
      "params": [{"name": "text", "kind": "POSITIONAL_OR_KEYWORD", "default": null}],
      "returns": null},
    "LexEntryOperations": {"kind": "class", "owner": null,
      "module": "flexicon.code.Lexicon.LexEntryOperations",
      "params": null, "returns": null},
    "LexEntryOperations.Create": {"kind": "method", "owner": "LexEntryOperations",
      "module": "flexicon.code.Lexicon.LexEntryOperations",
      "params": [
        {"name": "self", "kind": "POSITIONAL_OR_KEYWORD", "default": null},
        {"name": "lexeme_form", "kind": "POSITIONAL_OR_KEYWORD", "default": null},
        {"name": "gloss", "kind": "KEYWORD_ONLY", "default": "None"}],
      "returns": null}
  }
}
```

**Measured entry count** (run against the current tree, not guessed): Set
A = 97, Set B = 1354, Set B' = 11 -> **1462 entries**. Under the ~2000
ceiling; no narrowing needed.

## 4. The footer problem

**Chosen: a `.githooks` hook**, sharing the seam `commit_msg_guard.py`
already occupies. New `.githooks/api_surface_guard.py`, invoked as a
second step from the existing `.githooks/commit-msg` (same
`core.hooksPath` opt-in, no new per-clone step). At commit-msg time the
index is final, so the hook re-scans the **staged blobs**
(`git show :path`, not the working tree, so partial staging is handled
correctly), diffs against the committed baseline, and:
- additions only -> requires the staged baseline diff to already include
  them (mechanical, no message inspection);
- any existing entry changed/removed -> requires `BREAKING CHANGE:` in
  the commit message body (the file the hook already receives as `$1`)
  naming one of the three causes; blocks otherwise.

**What this does NOT catch:** opt-in per clone, bypassable with
`--no-verify` (same exposure the close-keyword guard accepts); doesn't run
in CI unless mirrored, so an unconfigured clone or a squash/rebase can
still land a breaking change unblocked -- flagged as the residual gap,
deferred below. Option (a), a pytest test reading `git log -1`, was
rejected as primary: it can only inspect a commit that already exists, so
it cannot block the commit it's gating -- CI-side value only, same
deferred item.

## 5. Regeneration UX

```
python tests/test_api_surface_ratchet.py --baseline
```

Matches `test_docstring_example_ratchet.py`'s convention exactly: the same
file that runs the pytest checks doubles as the regen entry point under
`if "--baseline" in sys.argv`. An agent making an additive change runs
this, stages the updated baseline, commits -- the hook's mechanical-diff
branch passes without a footer.

## 6. File manifest + effort

| File | Purpose | Size |
|---|---|---|
| `flexicon/code/Shared/_api_surface_scan.py` | Shared AST scanner (Set A/B/B' resolution + signature capture), used by both the pytest test and the hook. | ~250 lines |
| `tests/api_surface_baseline.json` | The frozen baseline (generated, not hand-written). | ~1462 entries |
| `tests/test_api_surface_ratchet.py` | Ratchet test (scanned-now == baseline) + `--baseline` regen entry point. | ~200 lines |
| `.githooks/api_surface_guard.py` | Commit-msg-time gate: diffs staged vs. committed baseline, requires footer for changed/removed entries. | ~180 lines |
| `.githooks/commit-msg` | One added invocation line, same pattern as the existing guard call. | +6 lines |
| `.githooks/README.md` | New section, same shape as the close-keyword section. | +~40 lines |
| `tests/test_api_surface_guard.py` | Unit tests for the hook's diff/footer logic. | ~150 lines |

### Out of scope (deliberately deferred)

- CI mirror of the hook (the residual Q4 gap).
- Inherited-and-unoverridden methods beyond the one-off `BaseOperations`
  carve-out (a second base class later needs its own carve-out).
- Freezing `PythonicWrapper`'s dynamic attribute surface.
- Overload-aware signature capture; decorator-aware rewriting.
- Auto-stubbing `docs/MIGRATION_GUIDE.md` entries from the footer (Gate 5
  requires the entry; this cycle only gates the footer's presence).

### `flexlibs2` v5.0.0 removal -- collision check

**No collision.** Set A is rooted at `flexicon/__init__.py` only;
`flexlibs2/` is ratcheted separately (`test_flexlibs2_alias_ratchet.py`,
a different property -- nothing internal imports it) and out of this
scope entirely. Deleting `flexlibs2/` at v5.0.0 changes no entry in
`api_surface_baseline.json`, since none was ever derived from
`flexlibs2/__init__.py`. Had this ratchet also scoped `flexlibs2`, the
removal would still be clean under Principle VII cause 3 (an announced
deprecation maturing) -- the question just doesn't arise under the chosen
scope.

## Task breakdown (for `tasks.md`)

1. Write `_api_surface_scan.py` (Set A/B/B' resolution + signatures).
2. Write `test_api_surface_ratchet.py` incl. `--baseline` regen path; run
   once to generate the initial 1462-entry baseline (separate commit --
   this cycle is design-only, per instructions).
3. Write `api_surface_guard.py`; wire into `.githooks/commit-msg`.
4. Write `test_api_surface_guard.py` unit tests for the hook.
5. Update `.githooks/README.md`.
6. Confirm no further constitution/`CLAUDE.md` wording change is needed
   (Gate 5 already names this control abstractly).
