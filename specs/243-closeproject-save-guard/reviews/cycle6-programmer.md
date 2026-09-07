# Cycle 6 -- Programmer report: T8a / P-10 SaveChanges() depth blast radius (measurement only)

## Headline verdict

**BLANKET GUARD SAFE.**

A blanket `CurrentDepth > 0` refusal on `SaveChanges()` sacrifices no
currently-working edit in any of the three measured cases. Full detail and
reasoning per case below; verbatim console transcript and the six-item
table are in
`evidence/live-t8a-savechanges-depth-blast-radius.md`.

## What was measured

Three cases were added to `tests/operations/test_issue243_closeproject_probe.py`
as a new matrix-style test, `test_p10_savechanges_depth_blast_radius`
(9 -> 10 live tests), each creating 25 `TEST_`-prefixed entries and calling
`SaveChanges()` from inside the named context manager:

| Case | Context | Mode | `CurrentDepth` before `SaveChanges()` | `SaveChanges()` raised? | In-memory survivors (still-open) | On-disk survivors (reopen) |
|---|---|---|---|---|---|---|
| A | `with project.UndoableOperation(...)` | undoable=True | 1 | YES -- `Commit at wrong place.` | 25/25 | 25/25 |
| B | `with project.Transaction(...)` | undoable=True | 0 | NO | 25/25 | 25/25 |
| C | `with project.Transaction(...)` | undoable=False | 1 | YES -- `Commit at wrong place.` | 0/25 | 0/25 |

**Case B** confirms by direct measurement (not by citing the frozen P-2/T1
table) that `Transaction()` never changes `CurrentDepth` in either mode --
under `undoable=True` it is depth-0 like the bare session, so a
`CurrentDepth > 0` guard would never even fire here. Not at risk.

**Case C** reproduces the already-understood destructive mechanism from
P-5/P-7 exactly: depth 1, `SaveChanges()` raises, and the change set is
gone before `CloseProject()` is ever entered. A guard here prevents active
damage.

**Case A -- the one unmeasured case named in the task brief -- turned out
to be a THIRD outcome, not either of the two named alternatives.**
`SaveChanges()` raises the identical `"Commit at wrong place."` exception
used by the destructive mechanism (so it never "succeeds" in any sense a
guard could be accused of blocking), **but the edit is not destroyed**:
25/25 survive in-memory (read before the block's own `__exit__`) and 25/25
survive a genuine close-and-reopen. The mechanism: no exception escapes the
`with project.UndoableOperation(...)` block (the harness's `_safe()`
wrapper isolates the `SaveChanges()` call specifically so this is true), so
`UndoableOperation()`'s own `__exit__` runs its normal, non-rollback path
and commits the pending edit onto the real undo stack regardless of what
the mid-block `SaveChanges()` call did; `CloseProject()`'s own later
`usm.Save()` at the now-collapsed depth 0 persists it for real, independent
of the failed mid-block call.

**Consequence for the guard's shape:** since `SaveChanges()` never actually
*succeeds* at `CurrentDepth > 0` in any of the three measured cases, a
blanket refusal changes nothing about whether the call itself "worked" --
it already fails today in both depth>0 cases (A and C). And since Case A's
edit survival does not depend on this specific `SaveChanges()` call one way
or the other, refusing it earlier (with the guard's own clearer message
instead of LCM's cryptic one) sacrifices nothing. **No case exists among
the three measured where the call currently succeeds at depth>0 and a
blanket guard would newly block it.**

## Scope confirmation

`git diff --stat -- flexicon/` is **empty**. `SaveChanges()` was not
modified. No guard was added. `CloseProject()` was not modified. Only
`tests/operations/test_issue243_closeproject_probe.py` was extended (+385
lines), plus this report and the evidence file.

`test_p5_save_before_forced_end`'s `assert surviving_count == 0` at its
original line (still pinning the bug) was left **untouched** -- not
flipped, not treated as a pass signal.

## Verification

- `--collect-only`: 9 -> 10 (the new +1 test covers sub-cases A/B/C
  matrix-style, like P-1/P-2).
- Live run: `python -m pytest tests/operations/test_issue243_closeproject_probe.py -m requires_live_project -q -s` with `FLEXLIBS_REQUIRE_LIVE=1` -- **10 passed**.
- `tests/live_status.json`: `"run_mode": "live"`.
- Offline baseline: `python -m pytest tests -m "not requires_live_project" -q` -- **1290 passed**, unchanged (deselected 473 -> 474, exactly +1).
- Fixture used: `target_sandbox_path` only. The real Target was never
  opened; no `scripts/restore_*.py` was run.

Full commands, verbatim `[PROBE]` lines, and the six-item table:
`specs/243-closeproject-save-guard/evidence/live-t8a-savechanges-depth-blast-radius.md`.

**PASS.**
