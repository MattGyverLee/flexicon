# Cycle 1 -- Programmer report -- issue #556

## Setup

Worktree created at `C:/Github/flexicon-556` off `origin/main` (commit
`76baa56`), branch `fix/556-morphrule-duplicate-deep-mock`. Hooks path
configured (`git config core.hooksPath .githooks`). Copied
`tests/fixtures/Sena 3 2026-06-09 1645.fwbackup`,
`tests/fixtures/Target 2026-07-06 0218.fwbackup`, and
`resources/__flexlibs_testing.fwbackup` from `C:/Github/flexicon` into the
same relative locations in the worktree so live sandbox fixtures resolve.
All edits, tests, and commits were done inside the worktree; the original
`release/4.10.0` checkout at `C:/Github/flexicon` was never touched.

## TASK 1 -- offline mock fix

Root cause confirmed: `#537` changed
`MorphRuleOperations.__DuplicateAffixTemplate` to do
`template_list = list(owner.AffixTemplatesOS)` (an HVO scan to find the
source's insert position), but the fixture in
`tests/operations/test_morphrule_duplicate_deep.py::_make_affix_template_fixture`
still built `owner.AffixTemplatesOS` as a bare `Mock()`, which is not
iterable.

Fix (test-only, `flexicon/code/` untouched):
- `source` now has a concrete `Hvo` (`1001`).
- `owner.AffixTemplatesOS` is now `_FakeAffixTemplatesOS`, a `list`
  subclass seeded with `[source]`, whose `IndexOf`/`Insert`/`Add` are
  `Mock`s with `side_effect` wired to the real list operations so both
  iteration and call-recording work.
- Confirmed the owner resolution path: `MorphRuleOperations.Duplicate` ->
  `__DuplicateAffixTemplate` -> `self._GetTypedOwner(source)`, which reads
  `source.Owner` (NOT `project.Object`) and passes it through
  `cast_to_concrete`. `source.Owner` is now wired to the same `owner`
  fixture object; `project.Object` is set for consistency/documentation
  but is not on this call path for an already-resolved `source` (confirmed
  by reading `MorphRuleOperations.__ResolveObject`, which only calls
  `project.Object` when the input is an `int`).
- Added `test_insert_after_inserts_at_source_index_plus_one`, asserting
  `owner.AffixTemplatesOS.Insert` is called with `(1, duplicate)` when
  `insert_after=True` (source seeded at index 0). The original bug-#203
  deep/shallow assertions (`test_deep_true_copies_slot_references`,
  `test_deep_false_does_not_copy_slot_references`, etc.) are unchanged in
  substance, only updated to unpack the fixture's new 4th return value
  (`owner`).

Result: `tests/operations/test_morphrule_duplicate_deep.py` -- 6 passed
(was 1 passed / 4 failed on origin/main).
Full offline suite: `2534 passed, 1050 deselected` (`-m "not
requires_live_project"`), no regressions.

## TASK 2 -- live check

Added `tests/operations/test_issue556_morphrule_duplicate_deep_live.py`,
structured after `test_target_live_smoke.py` and
`test_issue537_morphrule_duplicate_hvo_live.py`, marked
`requires_live_project`, using the `sena3_sandbox` fixture (function-scoped
-- each test gets an independent fresh sandbox).

Both tests:
1. Pick the first POS from `project.POS.GetAll()` in the sandbox.
2. Create 1-2 affix slots via `project.POS.CreateAffixSlot`.
3. Create a fresh `MoInflAffixTemplate` via
   `project.MorphRules.CreateAffixTemplate` and attach the slot(s) via
   `project.MorphRules.AddSlotToTemplate` (prefix and/or suffix side).
4. Read pre-state back from the LCM via `GetAllAffixTemplatesForPOS` (which
   returns `AffixTemplate` wrapper objects whose `.prefix_slots` /
   `.suffix_slots` / `.proclitic_slots` / `.enclitic_slots` are already
   cast to the concrete interface -- important, see note below).
5. Call `Duplicate(source, insert_after=True, deep=True|False)`.
6. Re-query via a fresh `GetAllAffixTemplatesForPOS` call (never asserting
   on the handle `Duplicate` returned) and assert slot-HVO-list equality
   (deep=True) or emptiness (deep=False), insert-after ordering (source
   index + 1), and owner template count (+1).
7. Clean up `TEST_556_`-prefixed templates in a `finally:` block.

**Both tests pass.** Live evidence, including the exact commands,
`run_mode` value, and full pre/post-state description, is in
`specs/_archive/closed/556-morphrule-duplicate-deep/evidence/live-duplicate-deep.md`.
`tests/live_status.json` shows `"run_mode": "live"` after the run.

### A note on the re-query helper (not a library bug)

The first draft of the live test called `project.Object(hvo)` to re-query
and hit `AttributeError: 'ICmObject' object has no attribute
'PrefixSlotsRS'` -- confirmed by live introspection that `project.Object()`
deliberately returns a bare, untyped `ICmObject` (documented behaviour;
see `lcm_casting.py` and CLAUDE.md's "Category 8" note). This was a bug in
my own test helper, not in the library: switched to
`GetAllAffixTemplatesForPOS()`, whose `AffixTemplate` wrapper already
handles the interface cast internally. After the switch both tests pass
cleanly.

### Real (pre-existing, out-of-scope) regression surfaced by the live run

The required combined invocation
(`test_issue556_..._live.py test_issue537_..._live.py -m
requires_live_project`) also runs the existing, untouched
`test_issue537_morphrule_duplicate_hvo_live.py`, which **fails** with:

```
duplicate.Name.CopyAlternatives(source.Name)
AttributeError: 'ICmObject' object has no attribute 'Name'
```

Root cause: that test deliberately passes a bare `ICmObject`
(`project.Object(tmpl1.Hvo)`) into `Duplicate` (that is the entire point of
#537's "raw Object view" coverage). Inside `Duplicate`,
`MorphRuleOperations.__ResolveObject` only casts to a concrete interface
when `ClassName == "PartOfSpeech"`:

```python
if getattr(obj, "ClassName", None) == "PartOfSpeech":
    return IPartOfSpeech(obj)
return obj
```

For `ClassName == "MoInflAffixTemplate"` the object is returned uncast, so
`source.Name` (used later in `Duplicate`'s shared MultiString-copy step)
raises. Confirmed via `git stash -u` + re-run that this fails identically
on unmodified `origin/main` -- this branch adds/modifies no file under
`flexicon/code/`, so it cannot be a regression from this change. Per the
task brief ("Do NOT change library code unless the live test in TASK 2
shows a real regression. If it does, stop and report that before fixing
anything"), I stopped and am reporting it rather than fixing it. It looks
like a distinct P1/P2-shaped bug (`__ResolveObject`'s cast table is missing
`MoInflAffixTemplate`/`MoEndoCompound`/`MoExoCompound`, matching the
"Same-name fields... casting" pattern class in CLAUDE.md) and belongs in
its own issue rather than folded into #556.

## Commit / PR

- Commit: `b22271f` -- "test(grammar): repair Duplicate deep-copy mocks
  after #537 HVO scan; add live check" (worktree branch
  `fix/556-morphrule-duplicate-deep-mock`), body contains `Closes #556` on
  its own line and a "Pattern audit" note about the pre-existing #537-test
  failure, ending with the Claude Opus 5.5 co-author line.
- Pushed to `origin/fix/556-morphrule-duplicate-deep-mock`.
- PR: https://github.com/MattGyverLee/flexicon/pull/560 (base `main`),
  body summarizes the fix, live evidence, and flags the pre-existing
  `test_issue537_...` failure for separate triage (grounds noted for a
  possible P3 downgrade of #556, not applied by me).

## Files touched

- `C:/Github/flexicon-556/tests/operations/test_morphrule_duplicate_deep.py`
  (fixture fix + new assertion, test-only)
- `C:/Github/flexicon-556/tests/operations/test_issue556_morphrule_duplicate_deep_live.py`
  (new live test file)
- `C:/Github/flexicon-556/specs/556-morphrule-duplicate-deep/evidence/live-duplicate-deep.md`
  (evidence)
- No file under `C:/Github/flexicon-556/flexicon/code/` was modified.
