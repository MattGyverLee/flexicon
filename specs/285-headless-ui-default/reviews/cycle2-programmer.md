# Cycle 2 -- programmer: three follow-ups on fix/285-headless-ui-default

## Step 1 -- cycle-1 artifacts committed
`2d7356a2` `docs(285): record cycle-1 spec artifacts for headless UI default
fix` -- added only:
- `specs/285-headless-ui-default/reviews/cycle1-domain.md`
- `specs/285-headless-ui-default/reviews/cycle1-verification.md`
- `specs/285-headless-ui-default/evidence/` (whole dir)

No other untracked/modified entries from `git status` (`.vscode/`, the
243/duplicate-signature/getall-contract items, the deleted
`.claude/ralph-loop.local.md`) were touched.

## Step 2 -- merge of main
`git fetch origin && git merge origin/main` produced merge commit
`d2ff8ff`. `main`'s tip was `068571d` (PR #286, issue #249). Git resolved
`CHANGELOG.md` cleanly with **no conflict markers** -- the #285 entry
(lines ~130-193) and the #249 entry (lines ~405+) sit in disjoint regions
of the file (#285 under `### Changed`, #249 further down under its own
heading), so the three-way merge auto-merged both in without a manual
conflict-resolution step. Verified afterward that both `#285`/
`HeadlessLcmUI` and `#249`/`Sldr.Initialize` text are present intact and
neither entry was dropped, reordered, or reworded.

## Step 3 -- the two domain follow-ups
Both from `specs/285-headless-ui-default/reviews/cycle1-domain.md`
"Follow-ups for the implementer".

**3a/3c -- CHANGELOG.md** (`CHANGELOG.md:139-169` after edit):
- Added a new paragraph, "**Second disclosed behaviour change --
  `OfferToRestore`**", documenting that a corrupt `.fwdata` with a
  sibling `.bak` now raises `LcmInitializationException` (via
  `XMLBackendProvider.OfferToRestore()`, `XMLBackendProvider.cs:272/279/285`)
  instead of `FwLcmUI`'s silent auto-restore, and stating the same
  polarity/hang rationale as `ConflictingSave`.
- Strengthened "**The hazard this closes**" with the cycle-1
  measurement from `specs/285-headless-ui-default/evidence/live-prefix-conflict.md`:
  the pre-fix default produced BOTH a silent discard (bare-script,
  confirmed by fresh third-session re-read) and a reproducible >105s
  block (under `FLEXLIBS_REQUIRE_LIVE=1 pytest -m requires_live_project`),
  not merely one or the other.

**3b -- `flexicon/code/headless_ui.py:100-118`** (`SynchronizeInvoke`
property docstring): added a "CONTINGENCY" note citing the two liblcm
call sites that dereference `None` unguarded --
`UnitOfWorkService.SendPropChangedNotifications` (`UnitOfWorkService.cs:537`,
via `UnitOfWork.cs:307/422`, `UndoStack.cs:343`) and
`UndoStack.DoTasksForEndOfPropChanged` (`UndoStack.cs:383`) -- and the two
preconditions that currently keep them no-ops (no `IVwNotifyChange`
subscriber via `AddNotification`, no `Scripture` access), so a future
change-watcher feature is warned to re-check before relying on `None`.

Commit: `49f22b2d` `docs(285): disclose OfferToRestore change and pin
SynchronizeInvoke contingency` (2 files changed: `CHANGELOG.md`,
`flexicon/code/headless_ui.py`).

## Step 4 -- offline suite
```
python -m pytest -m "not requires_live_project" -q
```
Result: **1728 passed, 693 deselected, 8 warnings, 5 subtests passed**,
0 failed, 28.31s. (Cycle 1 measured 1716 passed/690 deselected before the
#249 merge; the rise -- +12 passed, +3 deselected -- matches #249's added
test files landing via the merge.)

## Commit SHAs (this cycle, in order)
- `2d7356a2` -- docs(285): record cycle-1 spec artifacts
- `d2ff8ff` -- Merge remote-tracking branch 'origin/main' (PR #286 / #249)
- `49f22b2d` -- docs(285): disclose OfferToRestore change and pin
  SynchronizeInvoke contingency

Branch confirmed as `fix/285-headless-ui-default` throughout; no commit
was made to `main`.
