# Live evidence -- Checkpoint 3, T1+T2 (paragraph/segment whitespace fix)

Feature: `specs/242-paragraph-whitespace`
Baseline commit before this task's code edits: `558654efec797e65d383e3b6b53ad7aa4c2071f8`
Fixtures used: `target_sandbox` / `target_sandbox_path` ONLY (never the
real Target, never `scripts/restore_*.py`).

## Change under test

Four sites patched per the binding `/lex-lead` ruling (C28: this file is
committed BEFORE the live run, RESULTS added in a second commit after):

- `flexicon/code/TextsWords/ParagraphOperations.py` -- `Create`
- `flexicon/code/TextsWords/ParagraphOperations.py` -- `SetText`
- `flexicon/code/TextsWords/ParagraphOperations.py` -- `InsertAt`
- `flexicon/code/TextsWords/SegmentOperations.py` -- `AppendSentence`

Shape at all four: `.strip()` becomes a THROWAWAY used only for the
emptiness test; the caller's ORIGINAL payload reaches
`TsStringUtils.MakeString`. Non-str branch is `str(x)` with NO trailing
`.strip()` (including at `SegmentOperations.py`, where the ruling
explicitly authorises removing the pre-fix trailing `.strip()` on the
non-str branch, resolving the C6 asymmetry).

`SegmentOperations.py:604-617`'s terminator branch logic is UNTOUCHED --
this task measures it (P8) but does not modify it.

`git diff --stat -- flexicon/` (recorded before the live run):
```
 flexicon/code/TextsWords/ParagraphOperations.py | 24 ++++++++++++++++++------
 flexicon/code/TextsWords/SegmentOperations.py   |  9 +++++++--
 2 files changed, 25 insertions(+), 8 deletions(-)
```

Exactly the two authorised files -- no other file under `flexicon/` is
touched.

## Tests

`tests/operations/test_issue242_whitespace_probe.py` EXTENDED in place
(no parallel probe file created): `test_p1`-`test_p5` flipped from
asserting/observing "stripped" (pre-fix) to asserting "preserved"
(post-fix), pre-fix behaviour retained in comments for the historical
record. `test_p7` (whitespace-only still raises) and `test_p8` (terminator
branch measurement) are new.

`--collect-only` count (paste, not trusted by filename):
```
python -m pytest tests/operations/test_issue242_whitespace_probe.py --collect-only -q -m requires_live_project
```
Result: **7 tests collected** -- test_p1, test_p2, test_p3, test_p4,
test_p5, test_p7, test_p8.

## PREDICTIONS (committed BEFORE the live run)

- **P6**: each of the 8 cycle-1 payloads (`trailing_space`,
  `leading_space`, `trailing_tab`, `trailing_newline`, `trailing_nbsp`,
  `internal_double_space`, `null_marker_bare`, `null_marker_padded`) now
  round-trips BYTE-FOR-BYTE through all four methods (Create, SetText,
  InsertAt, AppendSentence) and survives the layer-B bypass and the
  in-memory/on-disk round trip (test_p1, test_p2, test_p3, test_p4). No
  payload is expected to fail this prediction; the fix removes this
  library's own stripping, and C3(i) already showed the LCM/FLEx layer
  does not normalise whitespace on its own.
- **P7**: whitespace-only input (`"   "`) still raises
  `FP_ParameterError` at all four sites (Create, SetText, InsertAt,
  AppendSentence), because the `.strip()` emptiness check is retained as
  a throwaway -- only what gets PERSISTED changed, not the emptiness
  gate. Predicted: no site silently accepts whitespace-only input, and no
  site writes a value before raising.
- **P8** (the new one): append `"bar"` via `AppendSentence` to a
  paragraph created via `Paragraphs.Create(text, "foo ")` (trailing
  space, now preserved by the fix instead of stripped). The terminator
  branch at `SegmentOperations.py:604-617` (untouched by this fix) reads
  the RAW last character of `para.Contents`, which is now `" "`, not in
  `(".", "!", "?")`. Predicted: it takes the "insert '. ' as sentence
  terminator" branch, producing `"foo . bar"` -- a space BEFORE the
  period. This is a state that was UNREACHABLE before this fix, because
  `Contents` could never end in a raw, unstripped space. This is
  MEASURED and REPORTED only; the terminator logic itself is not changed
  by this task. `/lex-lead` rules on whether it needs a follow-up fix.

## RESULTS

Command:
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue242_whitespace_probe.py -m requires_live_project -q -s
```

`tests/live_status.json` -> `"run_mode": "live"` (confirmed, line 140).

Result: **7 passed** (`test_p1`, `test_p2`, `test_p3`, `test_p4`,
`test_p5`, `test_p7`, `test_p8`), 0 failed. Fixtures used:
`target_sandbox` / `target_sandbox_path` only.

- **P6 -- CONFIRMED for all 8 payloads, all four methods.** Every
  `raw` value re-read from the LCM equalled the raw payload byte-for-byte
  after Create/SetText/InsertAt/AppendSentence, the layer-B bypass, and
  the in-memory/on-disk round trip. Example rows (re-read from the LCM,
  not the value passed in):
  - `trailing_space` (`'ka '`): Create -> `'ka '`, InsertAt -> `'ka '`,
    SetText -> `'ka '`; AppendSentence full_contents ->
    `'Seed. ka '`; bypass reread -> `'ka '`; on-disk after
    close+reopen -> `'ka '`.
  - `internal_double_space` (`'ka  ba'`): all sites ->
    `'ka  ba'` (double space preserved, not collapsed).
  - `null_marker_padded` (`' *** '`): all sites -> `' *** '`
    (leading/trailing space around the literal `***` preserved; no
    FLEx null-marker semantics interfered, confirming `GetText()` does
    not itself normalize this string).
  - P3 (layer-B bypass): all 8 payloads `EXACT_MATCH=True`, 0 `lost`.
  - P4 (in-memory vs on-disk): agreement `True` for all 8 payloads after
    `CloseProject()` + reopen.
  - P5 (non-str branch): both `ParagraphOperations.Create` and
    `SegmentOperations.AppendSentence` preserved the non-str trailing
    space (`'ka '`) -- the pre-fix C6 asymmetry (Paragraph preserved,
    Segment stripped) is CONFIRMED RESOLVED; `[VERDICT][P5] NO
    divergence measured`.
  **P6 VERDICT: CONFIRMED, no exceptions.**

- **P7 -- CONFIRMED for all four sites.** Whitespace-only input
  (`"   "`) raised `FP_ParameterError` at every site, with each site's
  pre-existing message VERBATIM:
  - Create -> `FP_ParameterError: Content cannot be empty`
  - SetText -> `FP_ParameterError: Content cannot be empty` (seed
    paragraph's content re-read afterward: unchanged at `'Seed.'`,
    confirming the raise happens before any write)
  - InsertAt -> `FP_ParameterError: Content cannot be empty`
  - AppendSentence -> `FP_ParameterError: text cannot be empty` (seed2
    paragraph's content re-read afterward: unchanged at `'Seed2.'`)
  **P7 VERDICT: CONFIRMED, no exceptions.**

- **P8 -- CONFIRMED, the predicted anomaly is real.** Created a
  paragraph via `Paragraphs.Create(text, "foo ")`; re-read Contents
  BEFORE the append: `'foo '` (trailing space preserved, proving the
  precondition -- this state was unreachable pre-fix). Called
  `Segments.AppendSentence(para, "bar")`. Re-read Contents AFTER the
  append: `'foo . bar'` -- exactly the predicted value. The
  (untouched) terminator branch at `SegmentOperations.py:604-617` read
  the raw last character (`" "`), found it not in `(".", "!", "?")`,
  and inserted `". "` as a sentence terminator, producing a space
  BEFORE the period. **P8 VERDICT: CONFIRMED. NOT FIXED here, per the
  ruling -- reported for `/lex-lead` to rule on next cycle.** No file
  under `SegmentOperations.py`'s terminator logic (lines 604-617,
  post-fix line numbers 607-620 after the 3-line comment insertion) was
  modified by this task.

## Offline baseline

`python -m pytest tests -m "not requires_live_project" -q` ->
**1292 passed, 482 deselected** both before and after this task's code
edits (re-run after the live probe above). Unchanged from the stated
baseline; the new `test_p7`/`test_p8` land in `deselected`, not
`passed`, when run offline (as do all `requires_live_project` tests in
this file).

## Scope confirmation

`git diff --stat -- flexicon/` (re-confirmed after the live run):
```
 flexicon/code/TextsWords/ParagraphOperations.py | 24 ++++++++++++++++++------
 flexicon/code/TextsWords/SegmentOperations.py   |  9 +++++++--
 2 files changed, 25 insertions(+), 8 deletions(-)
```
Exactly the two authorised files. `CheckOperations.py`, `TextOperations.py`,
`DiscourseOperations.py`, `AnthropologyOperations.py`, and the other
sibling sites are untouched, per scope.
