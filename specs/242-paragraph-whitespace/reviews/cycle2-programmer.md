# Cycle 2 -- Programmer report: T1+T2 (paragraph/segment whitespace fix)

## What changed

Applied the binding ruling's exact shape at all four sites:
```python
x = v if isinstance(v, str) else str(v)
if not x.strip():
    raise FP_ParameterError(...)  # verbatim per-site message kept
...
MakeString(v, ...)   # ORIGINAL payload persisted, not the stripped copy
```
- `flexicon/code/TextsWords/ParagraphOperations.py` -- `Create`, `SetText`, `InsertAt`
- `flexicon/code/TextsWords/SegmentOperations.py` -- `AppendSentence` (non-str branch's trailing `.strip()` removed, resolving the C6 asymmetry)

`SegmentOperations.py:604-617`'s terminator branch was NOT touched.

`git diff --stat -- flexicon/`:
```
 flexicon/code/TextsWords/ParagraphOperations.py | 24 ++++++++++++++++++------
 flexicon/code/TextsWords/SegmentOperations.py   |  9 +++++++--
 2 files changed, 25 insertions(+), 8 deletions(-)
```
Exactly the two authorised files.

## Tests

Extended `tests/operations/test_issue242_whitespace_probe.py` in place (no
parallel file). `test_p1`-`test_p5` flipped from "stripped" to "preserved"
assertions, pre-fix behaviour kept in comments. Added `test_p7`
(whitespace-only still raises, all four sites, verbatim messages) and
`test_p8` (terminator-branch measurement, NOT fixed).

`--collect-only`: **7 tests collected** (test_p1, p2, p3, p4, p5, p7, p8).

## Live verification

Command: `$env:FLEXLIBS_REQUIRE_LIVE=1; python -m pytest tests/operations/test_issue242_whitespace_probe.py -m requires_live_project -q -s`
Result: **7 passed**, `tests/live_status.json` `"run_mode": "live"`.
Fixtures: `target_sandbox`/`target_sandbox_path` only.

- P6: CONFIRMED -- all 8 payloads round-trip byte-for-byte through Create/SetText/InsertAt/AppendSentence, the layer-B bypass, and in-memory/on-disk.
- P7: CONFIRMED -- whitespace-only (`"   "`) raises `FP_ParameterError` at all four sites, verbatim messages, no write before raise.
- P8: CONFIRMED (the predicted anomaly). `Create(text, "foo ")` -> re-read `'foo '`; `AppendSentence(para, "bar")` -> re-read `'foo . bar'`. The untouched terminator branch reads the raw trailing space, inserts `". "`, producing a space before the period -- a state unreachable pre-fix. Reported, not fixed; `/lex-lead` to rule next cycle.

Offline baseline: `python -m pytest tests -m "not requires_live_project" -q` -> **1292 passed, 482 deselected** (unchanged), re-confirmed both before and after the live run.

## Evidence & commits

`specs/242-paragraph-whitespace/evidence/live-t1-t2-fix.md` -- PREDICTIONS committed first (`be42aaf`), RESULTS added in a second commit (`066bab0`) together with the code/test changes, matching cycle 1's `b28c864`/`558654e` pattern.

## Notes

Did not touch or commit unrelated pre-existing uncommitted changes found in the working tree (`specs/tier1-silent-data-loss/*`, `.claude/ralph-loop.local.md`, other `specs/242-paragraph-whitespace/*` artifacts already present from Checkpoint 2) -- out of scope for T1/T2.
