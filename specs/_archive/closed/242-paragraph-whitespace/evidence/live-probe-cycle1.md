# Issue #242 -- whitespace write-read-cycle probe, cycle 1

Test file: `tests/operations/test_issue242_whitespace_probe.py`
Fixtures used: `target_sandbox`, `target_sandbox_path` ONLY. Never the real
Target, never `scripts/restore_*.py`.

## `git diff --stat -- flexicon/` proof (measuring, not fixing)

Run before any measurement, and re-run after, to prove no file under
`flexicon/code/` was ever touched by this task:

```
$ git diff --stat -- flexicon/
(no output)
```

## Sites under study

| Site | File:line | Strips non-str branch? |
|---|---|---|
| `Create` | `flexicon/code/TextsWords/ParagraphOperations.py:171` | No -- `str(content)` |
| `SetText` | `flexicon/code/TextsWords/ParagraphOperations.py:576` | No -- `str(content)` |
| `InsertAt` | `flexicon/code/TextsWords/ParagraphOperations.py:716` | No -- `str(content)` |
| `AppendSentence` | `flexicon/code/TextsWords/SegmentOperations.py:589` | Yes -- `str(text).strip()` |

## Payload matrix

| label | raw (`repr`) |
|---|---|
| trailing_space | `'ka '` |
| leading_space | `' ka'` |
| trailing_tab | `'ka\t'` |
| trailing_newline | `'ka\n'` |
| trailing_nbsp | `'ka\xa0'` |
| internal_double_space | `'ka  ba'` |
| null_marker_bare | `'***'` |
| null_marker_padded | `' *** '` |

## PREDICTIONS (written and committed BEFORE the live measuring command runs;
git history proves the order -- do not edit this section after measurement,
even if a prediction misses)

### Layer A (test_p1, test_p2) -- current shipped writers

All four sites call `.strip()` on the str-branch input before the
emptiness check, then persist the STRIPPED value. Python's `str.strip()`
treats `\xa0` (NBSP) as whitespace (`'\xa0'.isspace() is True`), and
`.strip()` trims BOTH ends, not just trailing.

- `'ka '` (trailing space) -> PREDICTED LOST -> reads back `'ka'` on all
  four writers. This is the owner's originally-reported case.
- `' ka'` (leading space) -> PREDICTED LOST -> reads back `'ka'` on all
  four writers. UNTESTED to date; predicted to behave IDENTICALLY to the
  trailing case because `.strip()` is symmetric -- this is new
  information, not an assumption carried from the trailing report.
- `'ka\t'` (trailing tab) -> PREDICTED LOST -> `'ka'`.
- `'ka\n'` (trailing newline) -> PREDICTED LOST -> `'ka'`.
- `'ka\xa0'` (trailing NBSP) -> PREDICTED LOST -> `'ka'`. NBSP is
  `str.isspace()`-true in Python 3, so `.strip()` removes it exactly like
  ASCII space.
- `'ka  ba'` (internal double space) -> PREDICTED PRESERVED UNCHANGED --
  `.strip()` only trims the ends, never touches interior whitespace.
- `'***'` (bare null marker) -> PREDICTED PRESERVED AS `'***'` --
  `.strip()` is a no-op on a string with no leading/trailing whitespace,
  and none of the four writers raise on a non-empty stripped value, so it
  is persisted literally.
- `' *** '` (padded null marker) -> PREDICTED COLLAPSES to exactly `'***'`
  after `.strip()` -- i.e. indistinguishable on read-back from the bare
  null-marker case above. This is the load-bearing null-marker question:
  `Shared/string_utils.FLEX_NULL_MARKER = "***"` and
  `normalize_text()`/`is_empty_text()` do an EXACT string comparison
  against `"***"`. A user who typed `' *** '` meaning literal padded
  asterisks will, after this write path, have their paragraph collapse
  to the exact string any downstream `normalize_text()`/`is_empty_text()`
  consumer treats as "no content" -- this is a stronger claim than plain
  whitespace loss (semantic reclassification to empty), and is predicted
  to occur at every one of the four sites identically.
- `test_p1` (Create/SetText/InsertAt) is predicted to show all three
  writers agreeing on every payload (they share one source line).
  `test_p2` (AppendSentence) is measured separately because its stripping
  line differs syntactically (though not, for str inputs, semantically);
  predicted to show the SAME losses as test_p1 for every payload, since
  for `isinstance(text, str)` both lines reduce to `text.strip()`.
- Segment baseline (`GetBaselineText`) immediately after `AppendSentence`:
  the source comment at `SegmentOperations.py:639-640` says
  `BeginOffset`/`EndOffset` are set by `AnalysisAdjuster`
  "when the paragraph is re-parsed" -- it is UNMEASURED whether this
  happens synchronously inside the `Contents` setter or requires an
  explicit reparse call. PREDICTION (uncertain, flagged as a real risk,
  not a confident claim): the baseline text is a clean tail-match of the
  full paragraph Contents for every payload, i.e. offsets ARE computed
  synchronously. If this prediction misses (baseline is empty or
  stale), that is reported as the finding, not smoothed over.

### Layer B (test_p3) -- bypass, raw MakeString direct to `para.Contents`

PREDICTION: every payload in the matrix survives EXACTLY, byte-for-byte,
when written via `TsStringUtils.MakeString(raw, ws)` directly with no
`.strip()` anywhere in the path. Rationale: an `ITsString` is a plain rich
text run container over a Unicode text buffer; there is no known LCM-level
normalisation pass over paragraph `Contents` on assignment. If this
prediction holds, #242's fix (removing/adjusting the `.strip()` calls in
the four sites) is a REAL fix -- the loss measured at layer A originates
entirely in this library's own code, not deeper in LCM/FLEx. If ANY
payload is altered at layer B, that specific payload's #242 fix is
COSMETIC and must be reported in those exact words.

### In-memory vs on-disk (test_p4)

PREDICTION: in-memory and on-disk values AGREE for every payload measured
here (all via the layer-B bypass). Ordinary Unicode whitespace characters
in a string buffer are not expected to be treated specially by the
`.fwdata` XML/DB serialization path. This prediction is explicitly flagged
as NOT a foregone conclusion -- item 1 of this campaign was decided by
in-memory and on-disk DIFFERING, so a miss here would not be a surprise
and will be reported verbatim, not retuned.

### Non-str branch divergence (test_p5)

PREDICTION: `ParagraphOperations.Create` preserves the trailing space from
`str(_NonStrPayload())` == `'ka '` (non-str branch is NOT stripped), while
`SegmentOperations.AppendSentence` strips it to `'ka'` (non-str branch IS
stripped via `str(text).strip()`). PREDICTED DIVERGENCE: TRUE -- the two
writer families disagree on logically-identical input purely because of
the `isinstance(..., str)` branch shape of their respective stripping
lines.

## Commands (run in this exact order; live run is AFTER this file's
predictions section above was committed)

```
python -m pytest tests/operations/test_issue242_whitespace_probe.py --collect-only -q -m requires_live_project
# 5 tests collected

python -m pytest tests -m "not requires_live_project" -q
# 1292 passed, 480 deselected, 17 warnings  (baseline 1292 passed unchanged;
# deselected rose 475 -> 480, exactly +5 for the 5 new live-marked tests --
# they landed in deselected, not passed)

$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue242_whitespace_probe.py -m requires_live_project -q -s
```

## RESULTS (filled in AFTER the live run; predictions above are unedited)

`run_mode` in `tests/live_status.json`: **`"live"`** (confirmed, not `"mock"`).
Full run: `5 passed, 163 warnings in 7.42s`. `FLEXLIBS_REQUIRE_LIVE=1` was set
for the whole run. `git diff --stat -- flexicon/` re-run after the live
command: still empty (pasted above and reconfirmed after the run).

### test_p1 / test_p2 -- Layer A (current shipped writers), payload table

Column headers: `Create` / `InsertAt` / `SetText` are from `test_p1`;
`AppendSentence full` is the whole paragraph Contents after append (`"Seed. " + text`)
and `AppendSentence baseline` is `Segments.GetBaselineText()` on the new
segment, both from `test_p2`.

| payload | raw | Create | InsertAt | SetText | AppendSentence full | AppendSentence baseline |
|---|---|---|---|---|---|---|
| trailing_space | `'ka '` | `'ka'` | `'ka'` | `'ka'` | `'Seed. ka'` | `'Seed. ka'` |
| leading_space | `' ka'` | `'ka'` | `'ka'` | `'ka'` | `'Seed. ka'` | `'Seed. ka'` |
| trailing_tab | `'ka\t'` | `'ka'` | `'ka'` | `'ka'` | `'Seed. ka'` | `'Seed. ka'` |
| trailing_newline | `'ka\n'` | `'ka'` | `'ka'` | `'ka'` | `'Seed. ka'` | `'Seed. ka'` |
| trailing_nbsp | `'ka\xa0'` | `'ka'` | `'ka'` | `'ka'` | `'Seed. ka'` | `'Seed. ka'` |
| internal_double_space | `'ka  ba'` | `'ka  ba'` | `'ka  ba'` | `'ka  ba'` | `'Seed. ka  ba'` | `'Seed. ka  ba'` |
| null_marker_bare | `'***'` | `'***'` | `'***'` | `'***'` | `'Seed. ***'` | `'Seed. ***'` |
| null_marker_padded | `' *** '` | `'***'` | `'***'` | `'***'` | `'Seed. ***'` | `'Seed. ***'` |

**PREDICTIONS MATCHED, no misses.** All four sites lose leading/trailing
space, tab, newline, and NBSP identically (`.strip()` is symmetric and
NBSP is Python-whitespace); all four preserve internal double spaces
unchanged; all four collapse `' *** '` to exactly `'***'` -- confirming
the padded null marker becomes byte-identical to the real FLEx empty
marker after this write path, which is a semantic reclassification to
"empty" for any `normalize_text()`/`is_empty_text()` consumer, not just a
whitespace trim. Create/InsertAt/SetText agreed on every payload as
predicted (one shared source line). The segment baseline was ALSO a
clean tail-match of paragraph Contents for every payload -- offsets ARE
computed synchronously inside the `Contents` setter; the "will set ...
when re-parsed" comment at `SegmentOperations.py:639-640` did NOT
manifest as a lag in this probe. This was flagged as an uncertain,
non-confident prediction going in; it held.

### test_p3 -- Layer B (bypass, raw `MakeString` direct to `para.Contents`)

| payload | raw | bypass reread | exact match |
|---|---|---|---|
| trailing_space | `'ka '` | `'ka '` | **True** |
| leading_space | `' ka'` | `' ka'` | **True** |
| trailing_tab | `'ka\t'` | `'ka\t'` | **True** |
| trailing_newline | `'ka\n'` | `'ka\n'` | **True** |
| trailing_nbsp | `'ka\xa0'` | `'ka\xa0'` | **True** |
| internal_double_space | `'ka  ba'` | `'ka  ba'` | **True** |
| null_marker_bare | `'***'` | `'***'` | **True** |
| null_marker_padded | `' *** '` | `' *** '` | **True** |

**PREDICTION MATCHED, no misses.** Every payload in the matrix survives
the LCM bypass byte-for-byte, with zero `.strip()` anywhere in the path.

**HEADLINE ANSWER TO THE DECISION-RELEVANT QUESTION:** whitespace SURVIVES
layer B for every payload measured. The loss measured at layer A is
caused ENTIRELY by this library's own `.strip()` calls in the four sites
under study. **A fix that removes/adjusts those `.strip()` calls would be
a REAL fix, not cosmetic.**

### test_p4 -- in-memory vs on-disk (layer-B bypass values, open -> write -> close -> reopen -> read)

| payload | raw | in-memory | on-disk (after reopen) | agree |
|---|---|---|---|---|
| trailing_space | `'ka '` | `'ka '` | `'ka '` | **True** |
| leading_space | `' ka'` | `' ka'` | `' ka'` | **True** |
| trailing_tab | `'ka\t'` | `'ka\t'` | `'ka\t'` | **True** |
| trailing_newline | `'ka\n'` | `'ka\n'` | `'ka\n'` | **True** |
| trailing_nbsp | `'ka\xa0'` | `'ka\xa0'` | `'ka\xa0'` | **True** |
| internal_double_space | `'ka  ba'` | `'ka  ba'` | `'ka  ba'` | **True** |
| null_marker_bare | `'***'` | `'***'` | `'***'` | **True** |
| null_marker_padded | `' *** '` | `' *** '` | `' *** '` | **True** |

**PREDICTION MATCHED, no misses.** In-memory and on-disk AGREE for every
payload measured here -- unlike item 1 of this campaign, this particular
question (raw-whitespace persistence through `CloseProject()` + reopen)
showed no in-memory/on-disk divergence.

### test_p5 -- non-str branch divergence

`_NonStrPayload().__str__() == 'ka '` (trailing space) passed to both
writer families:

- `ParagraphOperations.Create(text, payload)` -> `'ka '` -- trailing space
  **PRESERVED** (non-str branch is `str(content)`, never stripped).
- `SegmentOperations.AppendSentence(seed, payload)` -> full contents
  `'Seed. ka'` (segment tail `'ka'`, no trailing space) -- trailing space
  **LOST** (non-str branch is `str(text).strip()`, always stripped).

**PREDICTION MATCHED, no misses. CONFIRMED DIVERGENCE**: the two writer
families disagree on logically-identical non-str input purely because of
the `isinstance(..., str)` branch shape of their respective stripping
lines.

### Headline answers (one sentence each, as required by the dispatch brief)

- **Does whitespace survive layer B?** Yes -- every payload in the matrix
  (including the padded null marker) survives the LCM bypass unchanged,
  so the loss is entirely this library's own `.strip()` calls and a real
  fix is possible, not merely cosmetic.
- **Does in-memory agree with on-disk?** Yes, for every payload measured
  here (`test_p4`, layer-B bypass values) -- in-memory and on-disk agreed
  in all 8 cases, no CloseProject()/reopen divergence was found for raw
  whitespace persistence.
- **Does the segment baseline behave like the paragraph Contents?** Yes --
  `Segments.GetBaselineText()` was a clean tail-match of the paragraph
  Contents for every payload immediately after `AppendSentence`, with no
  measurable reparse lag, so the segment path shows the identical
  loss/preservation pattern as the paragraph Contents for this probe's
  payloads (the owner's field report of 41/86 differing baselines is not
  reproduced by this specific test shape and would need a targeted
  follow-up against a populated corpus, not this scratch-sandbox probe).
