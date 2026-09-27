# Live evidence -- issue #556 (MorphRuleOperations.Duplicate deep-copy mocks)

## Commands run

Offline (all tests, not just the target file):

```
cd C:/Github/flexicon-556
python -m pytest -m "not requires_live_project" -q
```

Result: `2534 passed, 1048 deselected` (16 unrelated pre-existing warnings, no
failures).

Target file alone, offline:

```
python -m pytest tests/operations/test_morphrule_duplicate_deep.py -q -m "not requires_live_project"
```

Result: `6 passed` (was 1 passed / 4 failed / -- actually 4 of 5 originally
failing per the task brief -- on origin/main before the fixture fix; a
6th test, `test_insert_after_inserts_at_source_index_plus_one`, was added).

Live (both files named in the task):

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"          # PowerShell
export FLEXLIBS_REQUIRE_LIVE=1            # bash equivalent used here
python -m pytest tests/operations/test_issue556_morphrule_duplicate_deep_live.py tests/operations/test_issue537_morphrule_duplicate_hvo_live.py -m requires_live_project -q
```

Result: `1 failed, 2 passed` -- the 2 passes are both new #556 tests; the 1
failure is the pre-existing `test_issue537_morphrule_duplicate_hvo_live.py`
test, and is **not** caused by anything in this change (see "Pre-existing
failure" section below).

`tests/live_status.json` -> `"run_mode": "live"` (confirmed after every live
invocation above; never `"mock"`).

## Test A -- deep=True (`test_deep_true_copies_slot_references`)

Sandbox: `sena3_sandbox` (fresh tempdir copy of `tests/fixtures/Sena 3
2026-06-09 1645.fwbackup`, write-enabled, `undoable=False`).

Setup:
- POS: first POS returned by `project.POS.GetAll()` in the Sena 3 sandbox.
- Created 2 affix slots on that POS: `TEST_556_pfx`, `TEST_556_sfx`.
- Created affix template `TEST_556_src_deep` on the POS via
  `project.MorphRules.CreateAffixTemplate`.
- Attached `TEST_556_pfx` to the prefix side and `TEST_556_sfx` to the
  suffix side via `AddSlotToTemplate`.

Pre-state (read back from the LCM via `GetAllAffixTemplatesForPOS` + the
`AffixTemplate` wrapper's `.prefix_slots`/`.suffix_slots`/etc, all cast to
the concrete `IMoInflAffixTemplate`/`IMoInflAffixSlot` interfaces):
- Source template HVO: real HVO assigned by the LCM on create (varies per
  run; captured as `source_hvo` in the test, not printed to console).
- Source index in `owner.AffixTemplatesOS` (as scanned by
  `GetAllAffixTemplatesForPOS`): `source_index` (last position, since the
  template was just appended).
- Owner template count before Duplicate: `pre_count`.
- Slot HVO lists on source: `pre_prefix` = [prefix_slot.Hvo] (1 entry),
  `pre_suffix` = [suffix_slot.Hvo] (1 entry), `pre_proclitic` = [],
  `pre_enclitic` = [].
- Both `pre_prefix` and `pre_suffix` were asserted non-empty before
  proceeding (guards against a broken fixture silently passing).

Action: `project.MorphRules.Duplicate(source, insert_after=True, deep=True)`.

Post-state, re-queried from the LCM (fresh call to
`GetAllAffixTemplatesForPOS`, NOT the object handle returned by
`Duplicate`):
- Duplicate template found at HVO `dup_hvo`, located via a fresh scan.
- `dup_prefix == pre_prefix` -- PASS (the slot-ref HVO list on the
  duplicate's `PrefixSlotsRS` matches the source's exactly).
- `dup_suffix == pre_suffix` -- PASS.
- `dup_proclitic == pre_proclitic == []` -- PASS.
- `dup_enclitic == pre_enclitic == []` -- PASS.
- `post_order.index(dup_hvo) == source_index + 1` -- PASS (duplicate sits
  immediately after the source in `owner.AffixTemplatesOS`).
- `len(post_order) == pre_count + 1` -- PASS (owner's template count went
  up by exactly one).

**Result: PASS** (all assertions above hold; see pytest output,
`test_deep_true_copies_slot_references` in the 2-passed count).

## Test B -- deep=False (`test_deep_false_does_not_copy_slot_references`)

Same sandbox pattern, fresh sandbox instance (fixture is function-scoped).

Setup:
- Same POS-discovery pattern.
- Created 1 affix slot `TEST_556_pfx2` on the POS.
- Created affix template `TEST_556_src_shallow`, attached `TEST_556_pfx2`
  to its prefix side.

Pre-state:
- `pre_prefix` = [prefix_slot.Hvo] (1 entry, asserted non-empty).
- `pre_suffix` = `pre_proclitic` = `pre_enclitic` = [].
- `source_index`, `pre_count` as above.

Action: `project.MorphRules.Duplicate(source, insert_after=True, deep=False)`.

Post-state, re-queried from the LCM:
- `dup_prefix == []` -- PASS (deep=False must NOT copy slot references).
- `dup_suffix == []` -- PASS.
- `dup_proclitic == []` -- PASS.
- `dup_enclitic == []` -- PASS.
- Source re-queried again after the Duplicate call: `post_source_prefix ==
  pre_prefix` -- PASS (source's own slot list is untouched by the
  duplication).
- `post_source_suffix == pre_suffix == []` -- PASS.
- `post_order.index(dup_hvo) == source_index + 1` -- PASS.
- `len(post_order) == pre_count + 1` -- PASS.

**Result: PASS**.

## Pre-existing failure -- NOT part of this change

`tests/operations/test_issue537_morphrule_duplicate_hvo_live.py::TestIssue537MorphRuleDuplicateHvoLive::test_duplicate_affix_template_insert_after_raw_object_view`
fails on this branch with:

```
duplicate.Name.CopyAlternatives(source.Name)
AttributeError: 'ICmObject' object has no attribute 'Name'
```

Root cause (confirmed by live introspection, not guesswork): that test
calls `Duplicate(project.Object(hvo), ...)` -- i.e. it deliberately passes
a **bare `ICmObject`** (issue #537's whole point). Inside `Duplicate`,
`MorphRuleOperations.__ResolveObject` only casts the object to a concrete
interface when `ClassName == "PartOfSpeech"`:

```python
if getattr(obj, "ClassName", None) == "PartOfSpeech":
    return IPartOfSpeech(obj)
return obj
```

For `ClassName == "MoInflAffixTemplate"`, the bare `ICmObject` is returned
unchanged as `source`, so the later line `duplicate.Name.CopyAlternatives
(source.Name)` fails: `source.Name` does not exist on the base interface.

**This is reproducible on unmodified `origin/main`** with zero files from
this change present:

```
git stash -u
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue537_morphrule_duplicate_hvo_live.py -m requires_live_project -q
# => same AttributeError, 1 failed
git stash pop
```

This branch touches only:
- `tests/operations/test_morphrule_duplicate_deep.py` (fixture-only edit)
- `tests/operations/test_issue556_morphrule_duplicate_deep_live.py` (new
  file)

No file under `flexicon/code/` was modified, so this failure cannot be a
regression introduced here. Per the task brief ("Do NOT change library
code unless the live test in TASK 2 shows a real regression. If it does,
stop and report that before fixing anything"), this is reported and left
unfixed. It is a distinct, pre-existing gap in `__ResolveObject`'s cast
table (only `PartOfSpeech` is special-cased; `MoInflAffixTemplate` /
`MoEndoCompound` / `MoExoCompound` are not) and belongs in its own P-level
issue, not folded into #556's scope.

## Pass/fail summary

| Item | Result |
|---|---|
| Offline, full suite | PASS (2534 passed, 0 failed) |
| Offline, target file | PASS (6 passed) |
| Live, `test_issue556_morphrule_duplicate_deep_live.py` (Test A, deep=True) | PASS |
| Live, `test_issue556_morphrule_duplicate_deep_live.py` (Test B, deep=False) | PASS |
| Live, `test_issue537_morphrule_duplicate_hvo_live.py` | FAIL -- pre-existing, reproduced on unmodified origin/main, out of scope for #556 |
| `tests/live_status.json` `run_mode` | `"live"` |
