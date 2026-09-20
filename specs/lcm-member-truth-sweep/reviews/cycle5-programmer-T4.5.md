# Cycle 5 Programmer Report -- T4.5 (issue #259, checkpoint 4)

**Ruling implemented:** `specs/lcm-member-truth-sweep/reviews/cycle5-domain.md`
(`DECISION: warn`).

## 1. Fix the crash (mirror the getter's navigation)

**File:** `flexicon/code/lcm_casting.py`

Added `set_inflection_class_on_msa(msa, infl_class)` immediately after the
existing `get_inflection_class_from_msa()` (new function, ~65 lines,
inserted before `clone_properties`). It mirrors the getter's navigation
exactly: null check -> `hasattr(msa, "ClassName")` check -> membership in
`_MSA_INFLECTION_CLASS_PROPERTY` (i.e. `ClassName == "MoStemMsa"`) ->
`cast_to_concrete(msa)` -> `setattr(concrete, "InflectionClassRA", infl_class)`.
Returns `bool` (True = write happened, False = no writable target) rather
than raising, so the Operations layer builds its own diagnostic naming the
actual MSA state -- same division of labor as the getter returning `None`
silently and `GetInflectionClass` never raising.

Also exported `INFLECTION_CLASS_BEARING_MSA_CLASSES` was already public
from cycle 4's getter work (`frozenset(_MSA_INFLECTION_CLASS_PROPERTY)`,
line 757) -- reused it in the Operations-layer validity check instead of
duplicating the private dict.

**File:** `flexicon/code/TextsWords/WfiMorphBundleOperations.py`
`SetInflectionClass`, body (~line 1355 onward after the edit):

- Import line changed from a single-name `from ..lcm_casting import
  get_inflection_class_from_msa` to a 3-name import adding
  `set_inflection_class_on_msa` and `INFLECTION_CLASS_BEARING_MSA_CLASSES`.
- Final line changed from the crashing `bundle.InflClassRA = infl_class`
  to `set_inflection_class_on_msa(msa, infl_class)` inside the existing
  `with self._TransactionCM(...)` block. `bundle.InflClassRA` is never
  written anywhere in the file now (`grep -n "InflClassRA ="` returns
  nothing).

## 2. Raise FP_ParameterError for null MsaRA / non-stem MSA

Added a validation block placed OUTSIDE the transaction (same rationale as
the existing `infl_class` resolution just above it: an unresolvable
reference/unwritable target should raise before an undo task opens):

```python
msa = bundle.MsaRA
msa_class_name = getattr(msa, "ClassName", None)
if msa is None or msa_class_name not in INFLECTION_CLASS_BEARING_MSA_CLASSES:
    msa_desc = "null" if msa is None else f"ClassName={msa_class_name}"
    message = (
        f"Cannot set inflection class: bundle's MSA is {msa_desc}; "
        f"only MoStemMsa carries InflectionClassRA."
    )
    if msa_class_name == "MoDerivAffMsa":
        message += (
            " MoDerivAffMsa carries From/ToInflectionClassRA "
            "instead (a different pair of properties this method "
            "deliberately does not touch)."
        )
    raise FP_ParameterError(message)
```

Message shape matches the ruling verbatim (`"Cannot set inflection class:
bundle's MSA is <null | ClassName=X>; only MoStemMsa carries
InflectionClassRA."`), and appends the `MoDerivAffMsa`-specific note only
when that's the actual class, as the ruling specifies ("without implying a
new setter must be built" -- the appended sentence only *names* the
existing `From/ToInflectionClassRA` pair, doesn't propose building
anything). Docstring `Raises:` section updated to document
`FP_ParameterError`, and a new `Notes:` bullet spells out exactly which
three non-stem subtypes hit this path and why.

## 3. Warn via the print-style idiom (qualitative)

```python
print(
    "NOTE: inflection class is stored on the shared MSA, not the "
    "bundle; this change will be visible to every other morph "
    "bundle and sense referencing the same MSA."
)
```

Printed once per call, after validation succeeds and before the
transaction. I checked the codebase for an actual in-repo `print("WARNING"
...)` precedent (`validate_merge_compatibility`, `MergeObject` in
`LexSenseOperations.py`/`LexEntryOperations.py`) and found none -- those
methods use `raise FP_ParameterError(...)` for blocking, not a print-style
warning; the "print-style precedent" the ruling cites is the *illustrative*
pattern in `CLAUDE.md`'s "Warn on Type Mismatch, Don't Block" section
(`# WARNING: Merging different rule types` / "Continue? (y/n)"-style, minus
the interactive prompt, since this ruling is qualitative-warn not
block-and-ask). I implemented the qualitative half of that pattern:
`print()`, not `warnings.warn()`, no interactivity, no return-value
signaling. Text matches the ruling's suggested wording essentially
verbatim.

## 4. No per-call fan-out count

Confirmed: no `AllInstances()` scan, no bundle/sense count computation
anywhere in the new code. The warning text is entirely qualitative (`"...
visible to every other morph bundle and sense referencing the same
MSA."` -- no number). Docstring's new `IMPORTANT` note explains the
per-MSA/per-lexeme grain in prose without computing anything.

## 5. Docstring grain update

`SetInflectionClass`'s docstring gained:
- A `Raises: FP_ParameterError` line.
- A `Notes:` bullet explaining the true LCM navigation
  (`MsaRA -> cast_to_concrete() -> IMoStemMsa -> InflectionClassRA`),
  cross-referencing `set_inflection_class_on_msa()` and `GetInflectionClass`.
- An `IMPORTANT` bullet stating the write is per-MSA/per-lexeme, not
  per-bundle: `MoStemMsa` is owned by `ILexEntry` and is what
  `LexSense.MorphoSyntaxAnalysisRA` points to as "Grammatical Info";
  `WfiMorphBundle.MsaRA` is a reference into the *same* object, so the new
  value becomes visible to every other bundle and sense sharing that MSA,
  matching FLEx's own UI (editing Inflection Class on a sense's
  Grammatical Info Details is a lexicon-level edit).
- A bullet enumerating exactly which non-stem cases raise and why.

The old "BLOCKED (issue #259 ... open question Q2)" note is gone, replaced
by the above -- the method is no longer blocked.

## Anchor flip

**Status: DONE.** The parallel verifier (T4.7) had already landed
`TestPart8InflClassLive` in `tests/operations/test_lcm_member_truth_sweep.py`
by the time I read the working tree, including the pre-fix pin in item 5 of
`test_8c_planted_class_read_syncable_duplicate_and_blocked_write`:

```python
try:
    bundle_ops.SetInflectionClass(source_bundle_hvo, new_cls_hvo)
except AttributeError as exc:
    raised = True
assert raised, "SetInflectionClass no longer raises AttributeError -- ..."
```

I inverted it honestly, per binding C8:

- Renamed the test method to
  `test_8c_planted_class_read_syncable_duplicate_and_setter_write` (only
  reference to the old name in the repo was the `def` line itself --
  confirmed via grep before renaming).
- Replaced item 5's body with three sub-cases, each re-reading state from
  the LCM by HVO (not from the in-scope local variable) afterward:
  - **5a (positive path):** plants a *second* `IMoInflClass` via raw LCM
    factory (kept separate from the item-3 planted class so cleanup stays
    independent), then calls `bundle_ops.SetInflectionClass(source_bundle_hvo,
    new_cls_2_hvo)` for real. Re-reads the stem MSA by HVO
    (`IMoStemMsa(project.Object(source_msa_hvo))`) and asserts
    `InflectionClassRA.Hvo == new_cls_2_hvo`, and separately re-reads via
    `bundle_ops.GetInflectionClass(source_bundle_hvo)` and asserts the GUID
    matches -- proving the write is visible through the production read
    path too, not just the raw LCM.
  - **5b (null MsaRA):** locates a bundle with `MsaRA is None` from the
    already-collected `bundles` list (94 such bundles exist per T4.4/the
    ruling), asserts `pytest.raises(FP_ParameterError)` around the call.
  - **5c (non-stem MSA):** locates a bundle whose `cast_to_concrete(MsaRA)`
    is not `IMoStemMsa` (1144 such bundles exist), asserts
    `pytest.raises(FP_ParameterError)`, and re-reads that MSA's HVO
    afterward to confirm it's unchanged (no partial/incidental mutation).
  - Added a best-effort `try/except` cleanup block for the second planted
    class (resets the MSA's `InflectionClassRA` back to the item-3 class,
    removes the second class from `pos.InflectionClassesOC`), following the
    existing cleanup style used later in the `finally:` block for the first
    planted class.
- Added a local `from flexicon.code.FLExProject import FP_ParameterError`
  import alongside the existing `cast_to_concrete, get_pos_from_msa`
  import in the same method (matches the in-repo convention of local
  imports inside test methods used throughout this file).
- Updated the `TestPart8InflClassLive` class docstring and the
  `test_8c...` method docstring to describe the new item-5 behavior in
  past/present tense instead of "still-BLOCKED," while keeping the
  narrative framing of items 1-4 (T4.1-T4.4 read-path verification)
  untouched, per instructions not to rewrite `TestPart7MsaSharingQ2` or the
  surrounding narrative.
- Did **not** touch `TestPart7MsaSharingQ2` (confirmed via `grep -n` before
  and after -- zero lines in that class changed).

This test class is under `pytestmark = pytest.mark.requires_live_project`
(module-level, confirmed via grep) and is gated behind `sena3_sandbox`, so
it did not execute in my offline check; a live pass (T4.7's own scope, or
a follow-up) needs to confirm items 5a/5b/5c actually pass against a real
Sena 3 sandbox copy. I did not run it live myself (out of scope per the
brief -- "You are NOT doing live verification; a separate live pass
follows").

## Offline check

```
python -m pytest -m "not requires_live_project" -q
```

Result: **1878 passed, 809 deselected, 0 failed** -- matches the stated
baseline (1878 / 0) exactly, with **no delta**. This makes sense: every
line I added to the test file lives inside `TestPart8InflClassLive`, which
is entirely under the module-level `requires_live_project` marker, so none
of item 5's new assertions execute in the offline run; only collection
(import-time parsing) is exercised, which the `ast.parse()` sanity check
and the successful pytest collection both confirm succeeded.

Command used: the required full-suite form (not `pytest tests/ -m ...`),
confirmed collecting `flexicon/tests/` and `flexicon/sync/tests/` as well
via the "1878 passed" count matching the documented full baseline.

## Left undone / handed off

- **Live verification of T4.5 itself** (the new `SetInflectionClass`
  crash fix, the `FP_ParameterError` paths, and the new item 5a/5b/5c
  assertions against a real `sena3_sandbox`/`target_sandbox`) is explicitly
  out of scope for this task per the brief and is left for the next live
  pass.
- I did not rename or otherwise touch `TestPart7MsaSharingQ2`.
- No production code outside `lcm_casting.py` and
  `WfiMorphBundleOperations.py` was touched for T4.5 itself (the other
  diffs visible in `git diff --stat` --
  `WfiAnalysisOperations.py`, `WordformOperations.py`,
  `.crew-handoff.json`, `HANDOFF-main-session.md` -- are pre-existing
  uncommitted cycle-4 output, untouched by me).
- Did not commit or push, per hard constraints.
