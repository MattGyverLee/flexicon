# Cycle 3 - lex-programmer report (issue #542)

## 1. Contract regression (blocker) -- FIXED

`tests/contract/test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies`
was failing: `IMoInflAffixSlot` (imported by `affix_slot.py` and
`POSOperations.py`) was missing from
`tests/contract/snapshots/expected_contract.json`.

- Regenerated with the sanctioned tool:
  `python -m tests.contract.extract_lcm_contract -o
  tests/contract/snapshots/expected_contract.json`.
- `git diff` on the result contains ONLY the additions this branch
  introduced:
  - `IMoInflAffixSlot` added to the `SIL.LCModel` per-file import list
    (twice: `affix_slot.py`'s own entry, and `POSOperations.py`'s entry)
    and to the top-level type-usage list.
  - A new `"code/Grammar/affix_slot.py"` file entry (its own imports:
    `IPartOfSpeech`, `PartOfSpeechTags`, `ITsString`).
  - Summary counts: `total_files_with_lcm_deps` 81->82,
    `total_unique_imports` 269->270, `total_interfaces` 112->113.
  - No unrelated drift.
- Confirmed `IMoInflAffixSlot` exists on the installed liblcm (Mode 2,
  live): regenerated `liblcm_baseline.json` wholesale first to verify
  (`found: true`, with `Name`/`Optional`/`Affixes` present -- matches
  `affix_slot.py`'s assumptions), but that wholesale regeneration pulled
  in ~1950 unrelated lines (installed liblcm moved from beta.161,
  2026-09-08, to beta.173, 2026-09-26, since the file was last
  committed). Discarded the wholesale regeneration; hand-inserted only
  the new `IMoInflAffixSlot` type entry into the existing
  `liblcm_baseline.json`, in the alphabetical position the tool would
  have placed it. `git diff --stat`: `1 file changed, 123 insertions(+)`
  -- exactly the one new entry.
- `python -m pytest tests/contract -q -m "not requires_live_project"`:
  **23 passed** (was 1 failed, 22 passed).

## 2. CreateAffixSlot returns AffixSlot -- DONE

`POSOperations.CreateAffixSlot` now returns `AffixSlot(slot)` instead of
the raw `IMoInflAffixSlot` (`flexicon/code/Grammar/POSOperations.py`).
Docstring Returns + example updated; `MorphRuleOperations.AddSlotToTemplate`'s
`slot` Args updated to mention the wrapper
(`flexicon/code/Grammar/MorphRuleOperations.py`).

**Callers checked -- all already wrapper-safe, no code change needed:**
- `POSOperations.__ResolveSlot` -- already unwraps via `_UnwrapLcmObject`
  before casting (existing code from the prior cycle).
- `MorphRuleOperations.AddSlotToTemplate` -> `__ResolveObject` -> calls
  `self._UnwrapLcm(obj)` (generic `BaseOperations` helper), which checks
  `isinstance(obj, LCMObjectWrapper)` and returns `.lcm_object` -- `AffixSlot`
  is an `LCMObjectWrapper` subclass, so this "just worked."
- `MSAOperations.SetInflAffMsaSlots` / `CreateInflAff(slots=...)` ->
  `__Resolve` -- checks `hasattr(obj_or_hvo, "_obj")` and returns `._obj`
  (equivalent to `.lcm_object`; also already worked).

**Docs-only touch-ups** at the other `CreateAffixSlot` docstring examples
(`GetSlotName`, `SetSlotName`, `IsSlotOptional`, `SetSlotOptional`,
`GetAffixesInSlot`) -- left unchanged; they only pass the returned
`slot` opaquely into another resolver-backed method, which already
handles the wrapper.

**Offline test fixed:** `tests/operations/test_issue255_affix_slot.py`
asserted `created is slot`; changed to `created.lcm_object is slot`
(one-line change, comment added explaining why).

**Live test files edited so they stay correct (NOT run this cycle,
target_sandbox, per binding directive):**
- `tests/operations/test_issue255_affix_slot_live.py`: three
  `IMoInflAffixSlot(item)` / `IMoInflAffixSlot(second)` casts now unwrap
  the `AffixSlot` wrapper first (`item.lcm_object`, `second.lcm_object`)
  before casting, since both `GetAffixSlots` (pre-existing) and now
  `CreateAffixSlot` return wrappers.
- `tests/operations/test_issue258_set_infl_aff_msa_slots_live.py`:
  reviewed, no change needed -- it only passes slots through resolver-backed
  methods and reads `.Hvo`, both wrapper-safe already.

**New live coverage added** to
`tests/operations/test_issue542_affix_slot_readers_live.py`
(`sena3_sandbox`): `test_create_affix_slot_returns_affixslot_wrapper` --
confirms `isinstance(slot, AffixSlot)`, `.name`/`.optional` on the fresh
wrapper, the wrapper passed directly into `AddSlotToTemplate` (read back
via a fresh `IPartOfSpeech`/`IMoInflAffixTemplate` re-fetch, not the value
passed in), and the wrapper passed directly into `SetInflAffMsaSlots`
(read back via the independent `GetInflAffMsaSlots`, #543's inverse
lookup).

## 3. Migration note -- DONE

- New section "Change: AffixSlot wrapper (issue #542)" appended to
  `docs/MIGRATION_GUIDE.md` (end of file, following its "append newest at
  the bottom" convention): covers `GetAffixSlots`,
  `AffixTemplate.*_slots`, and now `CreateAffixSlot`; what still passes
  through (`.Hvo`/`.Name`/`.Optional` proxy, passing the wrapper into
  other Operations methods); the new `.name`/`.optional`/`.affixes`
  reads; and what breaks (`IMoInflAffixSlot(slot)` casts, `isinstance`
  checks against the raw interface) with the fix (`slot.lcm_object`,
  confirmed as the real public unwrap property on
  `LCMObjectWrapper` -- not `._obj`, which is the same value but an
  internal name).
- `CHANGELOG.md`'s existing `[Unreleased]` entry for #542 updated to
  mention `CreateAffixSlot`'s new return type and point at the Migration
  Guide section.

## 4. GetAffixesInSlot / @wrap_enumerable -- DONE (trivial, matches convention)

Added `@wrap_enumerable` above `@OperationsMethod` on `GetAffixesInSlot`,
matching `GetAffixSlots`' decoration. Both return a plain Python `list`,
so the decorator's `_needs_enumerable_wrap` check is a no-op for both
(lists already support indexing and `len()`) -- this is purely
convention-matching for the "every list-returning reader gets the
behavioral-collection contract" rule the file otherwise follows
uniformly.

## Test counts

Offline (`python -m pytest -m "not requires_live_project" -q`):
**4 failed, 2507 passed, 1041 deselected** -- the 4 failures are the
pre-existing, expected `test_morphrule_duplicate_deep.py` failures (same
set before and after this cycle's changes; confirmed unchanged). No
regression.

Contract subset (`python -m pytest tests/contract -q -m "not
requires_live_project"`): **23 passed** (was 1 failed + 22 passed before
the snapshot fix).

Live (`FLEXLIBS_REQUIRE_LIVE=1 python -m pytest
tests/operations/test_issue542_affix_slot_readers_live.py -m
requires_live_project -q`): **5 passed** (4 carried over from cycle 2 +
1 new: `test_create_affix_slot_returns_affixslot_wrapper`).

`tests/live_status.json`: `"run_mode": "live"`,
`run_timestamp: "2026-09-26T23:11:18Z"`,
`by_class.POSOperations.add.status == "pass"`,
`by_class.POSOperations.read.status == "pass"`.

Evidence file regenerated:
`C:\Github\flexicon-542\specs\_archive\closed\542-affix-slot-readers\evidence\live-542.md`
(cycle 3, supersedes cycle 2's evidence in the same file).

**No writes to Target. `target_sandbox` tests (`test_issue255_affix_slot_live.py`,
`test_issue258_set_infl_aff_msa_slots_live.py`) were edited for
correctness but NOT run, per the binding user directive.**

## Commits (this worktree, branch `fix/542-affix-slot-readers`, not pushed)

1. `c16e8d7` -- `test(contract): regenerate LCM snapshot for IMoInflAffixSlot (#542)`
   -- `tests/contract/snapshots/expected_contract.json`,
   `tests/contract/snapshots/liblcm_baseline.json`.
2. `2d80ff1` -- `feat(grammar): CreateAffixSlot returns an AffixSlot wrapper (#542)`
   -- `flexicon/code/Grammar/POSOperations.py`,
   `flexicon/code/Grammar/MorphRuleOperations.py`,
   `tests/operations/test_issue255_affix_slot.py`,
   `tests/operations/test_issue255_affix_slot_live.py`,
   `tests/operations/test_issue542_affix_slot_readers_live.py`.
3. `48e394c` -- `docs: migration note for CreateAffixSlot's AffixSlot return (#542)`
   -- `CHANGELOG.md`, `docs/MIGRATION_GUIDE.md`.
4. `32f73f6` -- `test: live-verify #542's contract fix and CreateAffixSlot wrapper return`
   -- `specs/_archive/closed/542-affix-slot-readers/evidence/live-542.md` plus the
   previously-uncommitted cycle-2 review artifacts
   (`specs/_archive/closed/542-affix-slot-readers/reviews/cycle1-lex-programmer.md`,
   `cycle2-lex-domain.md`, `cycle2-lex-programmer.md`, `cycle2-lex-qc.md`,
   `cycle2-lex-verification.md`, `cycle2-target-audit.md`).

All four commits end with
`Co-Authored-By: Claude Opus 5.5 (1M context) <noreply@anthropic.com>`.
None uses `close`/`fix`/`resolve` directly before `#542` (verified with
`git log -4 --format="%B" | grep -iE "close|fix(es)? #|resolve"`, only a
benign "code change" false-positive match, no hazard hit). Branch not
pushed (`git status`: "ahead of 'origin/main' by 8 commits").
