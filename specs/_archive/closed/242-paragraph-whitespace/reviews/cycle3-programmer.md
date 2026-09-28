# Cycle 3 -- Programmer report: T5 (AppendSentence join-boundary fix, C12)

## Diff shape

`SegmentOperations.py`'s `AppendSentence` `current_length > 0` branch only.
Old logic read the raw last character of `para.Contents` to decide
terminator vs separator. New logic computes `raw = Contents.Text or ""`,
`anchor = len(raw.rstrip())` (index only, never written), `trail =
current_length - anchor`, then branches: empty-Text degenerate case
(unchanged), `anchor == 0` (all-whitespace, no terminator/separator),
already-terminated (trail>0: insert nothing; trail==0: unchanged " "),
needs-terminator (trail>0: insert "." only at anchor; trail==0: unchanged
". "). Zero characters removed in any branch -- `rstrip()`'s output is
never passed to `MakeString`. The C12 NOTE comment is in place at the
branch, matching the register of the existing #242 THROWAWAY comment.

`git diff --stat -- flexicon/` (this commit only, `608200c2`):
```
 flexicon/code/TextsWords/SegmentOperations.py | 60 +++++++++++++++++++-----
```
(ParagraphOperations.py not touched by this commit; its working-tree
docstring diff is the doc agent's pre-existing, uncommitted work, left
as-is. SegmentOperations.py's own doc-agent docstring hunk was likewise
kept out of this commit and restored to the working tree afterward,
verified via `git diff` to be the doc agent's original hunk unchanged.)

## Tests

`test_issue242_whitespace_probe.py` extended in place: `test_p8` renamed
`test_p8_terminator_branch_join_boundary_fixed` and converted from
measuring the anomaly to asserting the fix (pre-fix behaviour kept in the
docstring); new `test_p8b` covers the whitespace-only-Contents row via a
layer-B LCM bypass (unreachable through the public API; raise NOT relaxed).
`--collect-only -q -m requires_live_project`: **8 tests collected**
(was 7 in cycle 2).

## Live result

`$env:FLEXLIBS_REQUIRE_LIVE="1"; python -m pytest
tests/operations/test_issue242_whitespace_probe.py -m requires_live_project
-q -s` -> **8 passed**. `tests/live_status.json` `"run_mode": "live"`.
`target_sandbox`/`target_sandbox_path` only; real Target untouched.

## Offline baseline

`python -m pytest tests -m "not requires_live_project" -q` -> **1292
passed, 483 deselected** (cycle 2: 482; +1 explained by new live test
`test_p8b`).

## Predictions vs results (all 9 rows, all re-read from LCM)

| Contents | predicted | measured | match |
|---|---|---|---|
| `''` | `bar` | `bar` | MATCH |
| `foo` | `foo. bar` | `foo. bar` | MATCH |
| `foo.` | `foo. bar` | `foo. bar` | MATCH |
| `foo!` | `foo! bar` | `foo! bar` | MATCH |
| `foo ` | `foo. bar` | `foo. bar` | MATCH (P8 fixed) |
| `foo   ` | `foo.   bar` | `foo.   bar` | MATCH |
| `foo.  ` | `foo.  bar` | `foo.  bar` | MATCH |
| `foo\t` | `foo.\tbar` | `foo.\tbar` | MATCH |
| `   ` (bypass) | `   bar` | `   bar` | MATCH |

No MISS. C12.4 inertness proof (first 4 rows, trail==0) held unchanged --
ruling not falsified.

## Commits

Predictions: `a580f7b`. Results + code + tests:
`608200c2` (`fix(segment-operations): AppendSentence join boundary may
insert, never delete`).
