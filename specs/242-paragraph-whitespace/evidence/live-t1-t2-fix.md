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

(added in a second commit after the live run -- see below)
