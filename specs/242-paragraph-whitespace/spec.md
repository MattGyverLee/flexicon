# SPEC -- 242-paragraph-whitespace

**Repo:** flexicon, branch `main`
**Issue:** #242 (Paragraph/Segment text writers silently strip
leading/trailing whitespace)
**Campaign:** `tier1-silent-data-loss`, queue item 2 of 4

**Status: COMPLETE ON SUBSTANCE, 2026-09-08 (cycle 5). Two items OPEN --
C16 and C18 -- neither of them substance.** Contract items **C1-C18** are
FROZEN.

The paragraph that stood here read `No behaviour change under flexicon/code/
has been authorised yet -- git diff --stat -- flexicon/ is empty`. That was
written at Checkpoint 1 and **was already false for a year of cycles**; it
is corrected rather than deleted so the record shows the error. The fix
HAS landed (C8, `066bab0`; C12, `608200c`; C14, `ed428f7`), and R1/R2/R3
plus the coercion question are all RULED (C8-C11) -- they are no longer
"RECOMMENDATIONS awaiting a ruling", and section 3 below is retained only
as the historical record of what was recommended before section 3a ruled.

The independent verification gate **has run twice, both green**:
`reviews/cycle3-verification.md` (`GATE: GREEN`) and
`reviews/cycle5-verification-swarm.md` (five adversarial verifiers, green
on substance). **Read C16 and C18 before making any verification claim
about this feature** -- the live-evidence anchor is not durable, and the
offline baseline is not currently reproducible.

**Cycle-1 inputs (read these before implementing):**
- `specs/242-paragraph-whitespace/evidence/live-probe-cycle1.md` (live,
  `run_mode: live`, 5/5 passing, `target_sandbox`/`target_sandbox_path`
  fixtures only, real Target untouched)
- `specs/242-paragraph-whitespace/reviews/cycle1-programmer.md`
- `specs/242-paragraph-whitespace/reviews/cycle1-explore.md`
- `specs/242-paragraph-whitespace/reviews/cycle1-domain.md`
- `tests/operations/test_issue242_whitespace_probe.py` (the probe harness --
  EXTEND, do not duplicate; see `tasks.md`)

---

## 1. Problem statement (from the GitHub issue #242 body, fetched verbatim)

Four text-writing methods strip leading/trailing whitespace from the
caller's string before persisting it to `IStTxtPara.Contents`. The strip is
only needed for the "is it empty?" emptiness guard; the *stripped* value is
what actually gets persisted, so whitespace that is genuinely part of the
source baseline is lost silently -- no error, no warning.

---

## 2. Contract items (FROZEN findings of fact)

### C1 -- The four sites: dual line-numbering, and the exact offending expression

The issue was filed against line numbers 171/576/716/589. **Those are the
`_ValidateParam` call lines at the time of filing, not the transform lines**
(`reviews/cycle1-explore.md` line 24). At current HEAD the `_ValidateParam`
lines have drifted further (178/583/724/593, independently re-verified by
this Archivist pass), and the transform itself sits 9-10 lines below the
issue's originally-cited numbers, at **180/585/726/595**. A future reader
comparing the issue text to the file will see neither of those exact
numbers reproduced verbatim -- both are correct, for different points in the
codebase's history; use the table below, not the issue text, for current
work.

| Site | Method | `_ValidateParam` (HEAD) | Transform line (HEAD) | `MakeString(...)` call (HEAD) | `Contents =` assignment (HEAD) |
|---|---|---|---|---|---|
| `flexicon/code/TextsWords/ParagraphOperations.py` | `Create` | 178 | 180 | 202 | 203 |
| `flexicon/code/TextsWords/ParagraphOperations.py` | `SetText` | 583 | 585 | 593 | 595 |
| `flexicon/code/TextsWords/ParagraphOperations.py` | `InsertAt` | 724 | 726 | 753 | 754 |
| `flexicon/code/TextsWords/SegmentOperations.py` | `AppendSentence` | 593 | 595 | 624 or 628 (branch-dependent) | 633 |

All verified directly against HEAD by this pass (`awk`/`grep` line dumps,
2026-09-07). The dispatch brief's persist-line numbers (202/593/753/624)
match this table's **`MakeString(...)` call** column, not the final
`Contents =` assignment column -- i.e. "persist" in the campaign's shorthand
means "the point where the stripped variable is baked into an `ITsString`,"
one or two lines before the actual property write. Both are given above so
neither reading is ambiguous.

The exact offending expression, identical in shape at all three
`ParagraphOperations.py` sites:

```python
content_str = content.strip() if isinstance(content, str) else str(content)
if not content_str:
    raise FP_ParameterError("Content cannot be empty")
...
mkstr = TsStringUtils.MakeString(content_str, wsHandle)   # <-- writes the STRIPPED value
para.Contents = mkstr
```

`SegmentOperations.py:595`'s variant (note it strips the non-str branch too,
see C6):

```python
text_str = text.strip() if isinstance(text, str) else str(text).strip()
if not text_str:
    raise FP_ParameterError("text cannot be empty")
```

### C2 -- Owner's field evidence, verbatim, and the #239 `guid=` irony

Source: GitHub issue #242 body (fetched via `gh issue view 242`, not
previously quoted in any cycle-1 report). Found while verifying GramTrans
feature 033 (GUID preservation) against `pyflexicon 4.3.1`, transferring
`Ejagham Mini -> Target`. A read-only comparison of every reproduced
paragraph and segment baseline:

```
paragraph contents identical : 60
paragraph contents DIFFERING : 44
segment baselines identical  : 45
segment baselines DIFFERING  : 41
```

Every single difference is lost trailing whitespace, e.g.:

```
source: 'ká '                                  target: 'ká'
source: '1 nnat nnyó nnat ányo nnat ńnyô '     target: '1 nnat nnyó nnat ányo nnat ńnyô'
```

The owner confirmed this is pre-existing and independent of anything
client-side, by an A/B where two Moves differing only in an unrelated
segment-identity change scored identically on this metric.

**The #239 irony:** `ParagraphOperations.Create` and
`SegmentOperations.AppendSentence` are two of the methods that gained
`guid=` in #239 precisely so objects could be reproduced faithfully. They
now preserve object *identity* perfectly but still cannot preserve the
*text*.

Note the segment-baseline figure (45 identical / 41 differing, total 86)
is the same figure `reviews/cycle1-programmer.md` line 48 and
`evidence/live-probe-cycle1.md` line 255 cite in the shorthand "41/86" --
consistent, not a second data point.

### C3 -- What the probe MEASURED, separated from what it did not

Source: `evidence/live-probe-cycle1.md`. Predictions were committed
(`b28c8640`) BEFORE the live measuring command ran; results were added in a
second commit (`558654e`) after -- the C28 forward rule (named for
`specs/243-closeproject-save-guard/spec.md` C28, this campaign's first use
of "predict, commit, then measure").

Three findings are decision-relevant:

**(i) Whitespace SURVIVES a raw `MakeString` write (layer B) -- the fix is
REAL, NOT COSMETIC.** Every payload in the matrix (including the padded
null marker `' *** '`) survived byte-for-byte when written via
`TsStringUtils.MakeString(raw, ws)` directly, bypassing this library
entirely (`test_p3`, evidence lines 184-204). Layer A (the shipped writers)
loses it entirely, and only because of this library's own `.strip()`
calls -- the loss does not originate deeper in LCM/FLEx.

**(ii) In-memory agrees with on-disk for every payload measured.**
`test_p4`'s full open -> write -> close -> reopen -> read cycle, using
layer-B values, showed agreement on all 8 payloads (evidence lines
206-222) -- unlike campaign item 1 (`243-closeproject-save-guard`), which
was decided by exactly this kind of divergence. This probe found none.

**(iii) The segment baseline behaves like the paragraph Contents for this
probe's payloads.** `GetBaselineText()` was a clean tail-match of the
paragraph Contents for every payload immediately after `AppendSentence`,
with no measurable reparse lag (evidence lines 176-182, 250-257). This was
flagged going in as an uncertain, non-confident prediction (the source
comment at `SegmentOperations.py:639-640` says offsets are set "when the
paragraph is re-parsed," and it was unmeasured whether that happens
synchronously) -- it held for this probe's fresh-scratch-paragraph payloads.

**What the probe did NOT measure:** it did not reproduce the owner's field
report of 41/86 differing baselines in a populated corpus (C2) -- this
probe used a fresh scratch paragraph per payload, a different shape of
input than the owner's reproduced-project comparison. Reproducing that
specific shape would need a separate, targeted follow-up against a
populated corpus, not this scratch-sandbox probe.

### C4 -- Null-marker ruling: DISCHARGED WITH NEGATIVE EVIDENCE

Source: `reviews/cycle1-domain.md` Q1. This was the campaign's stated entry
condition for this item (`specs/tier1-silent-data-loss/QUEUE.md` section
2: "it may be load-bearing for the FLEx null-marker path -- check
`Shared/string_utils.normalize_text` before changing behaviour").

**Ruling: NOT load-bearing.** The null-marker mechanism
(`normalize_text`/`FLEX_NULL_MARKER`, `flexicon/code/Shared/string_utils.py`,
`FLEX_NULL_MARKER = "***"` at line 15, `normalize_text()` at lines 18-46) is
entirely absent from these four write sites and their read counterparts:

- `ParagraphOperations.py` and `SegmentOperations.py` contain **zero**
  matches for `normalize_text`, `FLEX_NULL_MARKER`, or `string_utils`
  (grep-confirmed).
- The read paths never normalize: `GetText`
  (`ParagraphOperations.py:541-542`) does
  `text = para_obj.Contents.Text if para_obj.Contents else ""; return text or ""`;
  `GetBaselineText` (`SegmentOperations.py:337`) does
  `return segment_obj.BaselineText.Text or ""`. Neither calls
  `normalize_text` nor checks for `"***"` (both re-verified directly against
  HEAD by this pass).
- `IStTxtPara.Contents` and `ISegment.BaselineText` are plain `ITsString`,
  not `IMultiString`/`IMultiUnicode` -- the type the null-marker mechanism
  applies to per `string_utils.py`'s own module header (lines 7-9).

The specific delta the campaign brief flagged (`' *** '` -> strip ->
`'***'` -> read-back as the FLEx empty marker) does not occur here, because
the read path never calls `normalize_text` on this data. A literal `"***"`
written to `Contents` reads back as literal `"***"`. This is a
**pathological-input-only curiosity, NOT a load-bearing dependency** -- a
user typing three padded asterisks gets exactly what they typed back
(after the fix) or a collapsed `'***'` (before it), but neither behaviour
touches the null-marker semantics at all, because those semantics never
run on paragraph/segment data under either the current code or the fix.

### C5 -- Domain's Q2 finding: `AppendSentence` itself inserts trailing-whitespace-bearing structure, and the file is internally inconsistent

Source: `reviews/cycle1-domain.md` Q2. This is recorded as the strongest
argument in the record and must not be lost in any future summarisation.

`AppendSentence` (`SegmentOperations.py:614,617`, domain's report cites
`:612-617`; re-verified against HEAD by this pass at 614/617) explicitly
builds multi-sentence paragraphs by inserting `". "` -- **period PLUS A
TRAILING SPACE** -- as the sentence terminator
(`terminator = TsStringUtils.MakeString(". ", ws)`, line 614), then
computes the next insertion point as `current_length + 2` (line 617) to
land after that space. **The same file** then strips trailing whitespace
from the *next* `AppendSentence` call's input at line 595
(`text_str = text.strip() if isinstance(text, str) else str(text).strip()`).

This demonstrates the file is internally inconsistent: it manufactures
paragraph content containing trailing whitespace as part of its own
sentence-boundary representation, then refuses to accept equivalent
trailing whitespace from a caller. **Trailing whitespace is structural in
FLEx paragraph data, not corruption.** So the fix under consideration is
**FAITHFUL REPRODUCTION of valid structure, not cleanup of messy data** --
a materially different framing than "trimming noise."

### C6 -- The str()-coercion branch asymmetry, as a finding in its own right

Three distinct variants exist across the codebase for handling a non-`str`
input on the emptiness-guard branch, confirmed by direct source read:

1. **`ParagraphOperations.py` (all three sites)** -- does NOT strip the
   non-str branch: `str(content)`, verbatim, never stripped. Confirmed live
   by `test_p5`: a non-str payload whose `__str__()` returns `'ka '`
   (trailing space) is preserved by `Create` (evidence lines 224-233).
2. **`SegmentOperations.py:595`** -- DOES strip the non-str branch:
   `str(text).strip()`. The same non-str payload is silently truncated to
   `'ka'` by `AppendSentence` (same evidence block). Two writer families
   disagree on logically-identical input purely because of the
   `isinstance(..., str)` branch shape of their respective stripping lines.
3. **`CheckOperations.py:196/341/432` -- a THIRD, worse variant.**
   `name = name.strip() if isinstance(name, str) else ""` (re-verified at
   all three line numbers). Because `BaseOperations._ValidateParam`
   (`BaseOperations.py:2377`, `if param is None: raise
   FP_NullParameterError()`) is a **None-check only**, that `""` passes
   validation, and an empty name is silently persisted with no exception --
   worse than the paragraph/segment bug shape, because it is a total data
   loss (empty string) rather than a partial one (lost whitespace), and it
   fires on any non-`str`, non-`None` input, not only on padding.

### C7 -- Sibling-sweep result

Source: `reviews/cycle1-explore.md`, persisted by the main session (Explore
has no Write tool).

**Bucket 1 (bug shape: transform -> validate -> persist the transform) is
12 sites: the 4 known plus 8 NEW.**

| site | method | transform line | persist (`MakeString`) line | IN/OUT OF SCOPE for this feature |
|---|---|---|---|---|
| `ParagraphOperations.py:180` | `Create` | 180 | 202 | **IN SCOPE** (named site) |
| `ParagraphOperations.py:585` | `SetText` | 585 | 593 | **IN SCOPE** (named site) |
| `ParagraphOperations.py:726` | `InsertAt` | 726 | 753 | **IN SCOPE** (named site) |
| `SegmentOperations.py:595` | `AppendSentence` | 595 | 624 | **IN SCOPE** (named site) |
| `System/CheckOperations.py:196` | `CreateCheckType` | 196 | 218 | **NEW -- OUT OF SCOPE, awaiting /lex-lead ruling** |
| `System/CheckOperations.py:432` | `SetName` | 432 | 439 | **NEW -- OUT OF SCOPE, awaiting /lex-lead ruling** |
| `TextsWords/TextOperations.py:152` | `Create` | 152 | 170 | **NEW -- OUT OF SCOPE, awaiting /lex-lead ruling** |
| `TextsWords/TextOperations.py:608` | `SetName` | 608 | 616 | **NEW -- OUT OF SCOPE, awaiting /lex-lead ruling** |
| `TextsWords/DiscourseOperations.py:327` | `CreateChart` | 327 | 351 | **NEW -- OUT OF SCOPE, awaiting /lex-lead ruling** |
| `TextsWords/DiscourseOperations.py:482` | `SetChartName` | 482 | 492 | **NEW -- OUT OF SCOPE, awaiting /lex-lead ruling** |
| `Notebook/AnthropologyOperations.py:265` | `Create` | 265 | 301 | **NEW -- OUT OF SCOPE, awaiting /lex-lead ruling** |
| `Notebook/AnthropologyOperations.py:374` | `CreateSubitem` | 374 | 391 | **NEW -- OUT OF SCOPE, awaiting /lex-lead ruling** |

**Do NOT silently widen this feature's scope to the 8 NEW sites.** They are
proposed here as candidates, not accepted as tasks -- see "Recommendations
awaiting ruling" below.

**Bucket 2 (correct shape: throwaway validation, original persisted) --
COUNT 82 writer sites** (71 use `if not x or not x.strip():` /
`if not x.strip():` then `MakeString(x)`; 11 more delegate the same
throwaway check to `BaseOperations._ValidateStringNotEmpty`). Counting
*all* writers that persist the caller's original unmodified, including
those with only a `_ValidateParam` None-check: **390**.

**Verdict: 82 vs 12 -- the four #242 sites (and the 8 newly-found ones) are
OUTLIERS. The direct-fix shape is the house convention, not a departure
from it.**

**Clean sweep results, explicitly requested and confirmed:**

- `normalize_text()`-then-persist: **NONE.** All 44 call sites are
  read/compare (getters, comparisons, filter predicates).
- `normalize_match_key()`-then-persist: **NONE.** All 80 uses land in a
  compare-only local.
- `ScrTxtParaOperations.py`: **CLEAN.** `Create:153`/`SetText:374` persist
  raw `text` after only a `_ValidateParam` None-check; no emptiness check
  at all, so it does not share the bug shape.
- `WordformOperations.py`: **CLEAN.** `176`/`379` persist raw `form`;
  `246`/`278` are throwaway guards in `Find`/`Exists`.
- `BaseOperations.py` shared code: **CLEAN.** `.strip()` only appears inside
  `fill_gaps` emptiness guards in `_apply_syncable_properties_to_item`
  (`~:366`, `~:393`); `text`/`value` are persisted untouched. No wide blast
  radius from shared code.

---

## 3. Recommendations awaiting a `/lex-lead` ruling (NOT frozen contract)

Per the dispatch brief, the fix-shape ruling, the breaking-change/CHANGELOG
ruling, and the scope ruling on the 8 NEW sites are `/lex-lead`'s to make,
not this Archivist pass's. The domain agent's recommendations are recorded
below verbatim in substance, each marked RECOMMENDED, AWAITING /LEX-LEAD
RULING.

### R1 -- Fix shape: direct fix (a), RECOMMENDED -- DISCHARGED by C8 (2026-09-07)

Source: `reviews/cycle1-domain.md` Q3. Domain recommends candidate (a) --
validate on a stripped copy, persist the caller's original -- unambiguously,
for two reasons:

1. It already matches the codebase's *actual* dominant idiom, not just its
   style: `POSOperations.py:190-206` (and 60+ similarly-shaped sites) check
   `if not name or not name.strip():` but persist the un-mutated `name`.
   The paragraph/segment bug is that `content_str`/`text_str` -- the
   *stripped* copy -- is what reaches `MakeString`, diverging from the
   codebase's own convention.
2. Candidate (b), a `preserve_whitespace=False` kwarg, is named in CLAUDE.md
   as the anti-pattern "do not make the caller manage a flag to get correct
   data," and would make these four methods the only ones in the library
   with an opt-in flag for behaviour every other CRUD method gives for
   free. Domain recommends REJECTING (b).

### R2 -- Breaking-change / CHANGELOG classification: `### Changed`, no `BREAKING` prefix, RECOMMENDED -- DISCHARGED (AND OVERTURNED) by C9 (2026-09-07)

Source: `reviews/cycle1-domain.md` Q4. Domain recommends: yes, worth a
CHANGELOG entry (this changes persisted output for existing callers who
relied on the strip, e.g. interactive scripts building text via
`f"{sentence} "` loops expecting the library to absorb the padding), but
classified `### Changed`, not `BREAKING`, because unlike #254's
`GetMorphType` this involves no signature change and no exception-type
change. Domain also recommends a one-line `Note:` (not `Warning:`) added to
each of the four docstrings' `Args` section for `content`/`text`, since
none currently document the stripping behaviour at all -- the silence is a
documentation gap independent of which way this is fixed.

### R3 -- Scope: the 8 NEW sibling sites -- DISCHARGED by C10 (2026-09-07)

C7's bucket 1 found 8 additional sites sharing the exact bug shape, ranked
by severity in `reviews/cycle1-explore.md`:

1. `System/CheckOperations.py:196`/`:432` -- highest severity: non-`str` ->
   `""` -> empty name persisted, entire payload lost, no exception (C6).
2. `TextsWords/TextOperations.py:152`/`:608` -- text titles re-whitespaced;
   `Create` also dedups against the *stripped* name, so `"Genesis "`
   collides with `"Genesis"`.
3. `Notebook/AnthropologyOperations.py:265`/`:374` -- OCM item names;
   `Exists()` at line 269 uses the stripped form, same silent-collision
   effect.
4. `TextsWords/DiscourseOperations.py:327`/`:482` -- chart names, lower
   blast radius (metadata only).

This spec does **not** propose fixing these 8 sites as part of #242's own
task list. They are recorded here so a future reader does not rediscover
them, and so `/lex-lead` can decide whether to fold them into this
feature, spin them into their own issue(s), or route them to the campaign
QUEUE.md "Awaiting user approval" section. `tasks.md` treats them as
explicitly out of scope pending that ruling.

---

## 3a. `/lex-lead` rulings on R1/R2/R3 and the coercion question (FROZEN, 2026-09-07)

**Cycle-3 addendum, 2026-09-07:** two further rulings, C12 and C13, are
appended to this section below C11 rather than in a new section, to keep
all `/lex-lead` rulings on this feature in one contiguous FROZEN block.

### C8 -- R1 ruling: direct fix ACCEPTED, `preserve_whitespace=` kwarg REJECTED

**Ruling, 2026-09-07:** the domain-recommended direct fix (candidate (a)) is
ACCEPTED. The `preserve_whitespace=` kwarg (candidate (b)) is REJECTED, as
the CLAUDE.md-named caller-managed-flag anti-pattern -- these four methods
do not get an opt-in flag for behaviour every other CRUD method in the
library already gives for free (`spec.md` C7's 82-vs-12 verdict).

**Binding shape**, at all four sites named in C1:

```python
x = v if isinstance(v, str) else str(v)
if not x.strip():
    raise FP_ParameterError(...)
...
MakeString(v, ...)   # the ORIGINAL, unstripped value is what gets persisted
```

The non-`str` branch is **NOT** stripped at any of the four sites. This
deletes `SegmentOperations.py:595`'s `str(text).strip()` (C6 item 2),
bringing `AppendSentence` into line with the three `ParagraphOperations.py`
sites' existing (never-stripped) non-str behaviour (C6 item 1) -- see C11
for why this is the full extent of the coercion-asymmetry work done here,
not a first step toward harmonising it further.

Whitespace-only input still raises `FP_ParameterError` -- emptiness
semantics are unchanged by this ruling; only what gets persisted for
*non-empty, whitespace-bearing* input changes.

### C9 -- R2 ruling: CHANGELOG entry is `### Changed` with a `**BREAKING (behavioural): ...**` lead

**Ruling, 2026-09-07:** the CHANGELOG entry for this fix is classified
`### Changed`, with a `**BREAKING (behavioural): ...**` lead sentence.

**This OVERTURNS cycle-1 domain's Q4 recommendation** (`spec.md` R2 as
originally recorded: `### Changed`, no `BREAKING` prefix). Domain's stated
reasoning was that a `BREAKING` prefix requires a signature change or an
exception-type change, and this fix has neither. **The repository's own
CHANGELOG refutes that premise.** `grep -n BREAKING CHANGELOG.md` returns
exactly three hits, independently re-run by this pass:

```
15:- **BREAKING (behavioural): `WfiMorphBundleOperations.GetMorphType` now
63:- **BREAKING (behavioural): `FLExProject.SaveChanges()` now raises
431:- **BREAKING (behavioural): `OpenProject(..., undoable=...)` now defaults to
```

`CHANGELOG.md:431` applies the `**BREAKING (behavioural):**` label to
`OpenProject(..., undoable=...)` -- a pure silent-default flip, with no
signature break at all (this is campaign item 1's own #243 CHANGELOG
entry). `CHANGELOG.md:15` (the #254 `GetMorphType` entry) and `:63` (the
#243 `SaveChanges()` guard entry) are the other two hits. The convention in
this codebase is `**BREAKING (behavioural):**` for any change to
*persisted or observable output*, not only for signature/exception-type
breaks -- so this fix qualifies on the same basis as `CHANGELOG.md:431`.

This overturn is recorded explicitly, with the three line numbers above,
so the campaign record shows a specialist recommendation being overruled
on file evidence, not on preference. `/lex-doc` authors the actual
CHANGELOG prose per the Archivist/Doc-Agent division of labour; this
contract item fixes only the classification, not the wording.

### C10 -- R3 ruling: the 4 filed sites are fixed in this feature; the 8 sibling sites are NOT

**Ruling, 2026-09-07:** this feature's task list fixes only the 4 sites
named in the original issue (`spec.md` C1's table). The 8 sibling sites
found by the cycle-1 sibling sweep (`spec.md` C7) are **routed to
`specs/tier1-silent-data-loss/QUEUE.md` "Awaiting user approval"**
(Q-242A, appended by this pass) rather than folded into this feature or
spun into a follow-on feature.

**Rationale (load-bearing; record in full):** the four filed sites write
**CONTENT fields** -- `IStTxtPara.Contents`, `ISegment.BaselineText` --
where domain's Q2 structural-whitespace argument holds (`spec.md` C5:
`AppendSentence` itself manufactures trailing-whitespace-bearing structure
as part of its own sentence-boundary representation, so preserving
caller-supplied trailing whitespace is faithful reproduction, not
cleanup). All 8 new sites write **NAME fields** -- check type, text title,
OCM item, chart -- where that argument does not hold: a name is not
built out of structural whitespace the way a sentence-terminated paragraph
is.

Independently verified at HEAD by `/lex-lead`: **three of the four new
site families feed the STRIPPED value into a uniqueness check AND the
persist**, not merely into the persist:

- `CheckOperations.py:196` (`CreateCheckType`'s transform) -> `FindCheckType`
  at `:200` uses the same stripped value to test uniqueness before create.
- `TextOperations.py:152` (`Create`'s transform) -> `Exists` at `:155` does
  the same.
- `AnthropologyOperations.py:265` (`Create`'s transform) -> `Exists` at
  `:269` does the same.

Preserving the unstripped payload at these three families would leave an
unanswered field-identity question this feature is not positioned to
answer: is `"Genesis "` the same text as `"Genesis"` for dedup purposes?
Changing what gets persisted without also settling what counts as a
duplicate risks silently allowing `"Genesis "` and `"Genesis"` to coexist
as two distinct records where today there can only be one.

The four filed sites have **no name-uniqueness check** at all --
`SegmentOperations.Exists` is hvo (object-identity) membership, not name
dedup -- which is exactly why the direct fix is safe to ship there
unconditionally, and unproven at the 8 sibling sites without a separate
dedup-semantics ruling. This also disposes of Q3 (`spec.md` C6 item 3):
the `CheckOperations.py` third variant travels with the R3/Q-242A bundle
for the *whitespace* question, but see Q-242B in the campaign QUEUE.md --
its non-str-input total-data-loss defect is filed as its own, more severe
item precisely so it is not triaged at whitespace severity.

### C11 -- coercion ruling: harmonising str()-coercion across the codebase is OUT of scope

**Ruling, 2026-09-07:** within the four filed sites, both branches of the
one expression are fixed together as a unit (C8) -- this is in scope and
done. The broader question of whether the library should *coerce*
non-`str` payloads via `str(v)` at all, versus *reject* them outright, is
**OUT of scope for this feature**.

`BaseOperations._ValidateParam` (`BaseOperations.py:2377`) is a
`None`-check plus a stale-LCM guard ONLY -- it performs no type check, so
`str(obj)` can silently persist a value like `"<Foo object at 0x...>"` for
any non-`str`, non-`None` caller input, at any of the 12+ sites sharing
this shape across the codebase. Deciding whether to coerce or reject is a
shared-code / API-surface change to `_ValidateParam` itself, which
CLAUDE.md requires be consulted on before changing (see "When to Consult
Claude" -- "BaseOperations validation methods (affects all operations)").
This question is **queued** as Q-242C in
`specs/tier1-silent-data-loss/QUEUE.md` "Awaiting user approval", not
answered here and not implemented incidentally as a side effect of C8.

### C12 -- the AppendSentence join-boundary ruling (cycle 3, 2026-09-07)

**Invariant, quoted verbatim:** "AppendSentence may INSERT at the join
boundary. It may never DELETE at the join boundary."

**Background:** cycle 2's T1/T2 evidence (`evidence/live-t1-t2-fix.md`,
prediction P8) proved that once `Create`/`SetText`/`InsertAt` stop
stripping (C8), `para.Contents` can legitimately end in whitespace --
a state unreachable before this feature. `AppendSentence`'s
(pre-existing, untouched) terminator branch reads the RAW last character
to decide "already terminated?", so `'foo '` followed by
`AppendSentence(para, "bar")` measured as `'foo . bar'` -- a space
BEFORE the period. Cycle-2 doc recorded this as a "Known interaction, not
yet resolved" CHANGELOG sub-paragraph, unfixed, awaiting this ruling.

**Three options considered, and the ruling:**

1. **The cycle-1 candidate: rstrip-anchor that discards the trailing
   space.** REJECTED. Anchoring the terminator by rstripping and writing
   the rstripped string back would delete the caller's existing trailing
   whitespace at the join boundary -- exactly what the invariant above
   forbids, and a direct regression of C8's "the original, unstripped
   value is what gets persisted" ruling.
2. **The document-only option** (leave the terminator branch as-is;
   keep the "Known interaction, not yet resolved" CHANGELOG note as the
   permanent record). REJECTED. This leaves a live, reachable data-loss
   shape unfixed indefinitely with no code remedy in view, for a defect
   this campaign exists to fix.
3. **The chosen shape: anchor the terminator at the last non-whitespace
   character, and REUSE the caller's existing trailing whitespace as the
   separator.** ACCEPTED. This is the only one of the three that deletes
   nothing at the join boundary: it needs no exception to #242's no-strip
   principle, because `rstrip()` is used to compute an index only -- its
   result (`anchor`) is never itself written or passed to `MakeString`.
   This is the C11 durability lesson applied one level deeper: C11 kept
   the no-strip principle intact by refusing to widen scope into
   coercion harmonisation; C12 keeps it intact by refusing a fix shape
   that would silently reintroduce a strip under a different name.

**The four-case algorithm** (binding shape, `SegmentOperations.py`'s
`AppendSentence`, `current_length > 0` branch; `raw = para.Contents.Text
or ""`, `anchor = len(raw.rstrip())`, `trail = current_length - anchor`):

1. **`raw == "" and current_length > 0`** (degenerate: `Contents.Text` is
   `None`/empty while `Length > 0`) -- **preserve today's behaviour
   exactly**: insert `". "` as terminator. Not routed through the new
   logic below.
2. **`anchor == 0`** (Contents is non-empty but entirely whitespace) --
   no sentence to terminate; insert no terminator and no separator, place
   the new text at the end.
3. **Already terminated** (`raw[anchor - 1] in (".", "!", "?")`):
   - `trail > 0` -- the existing trailing whitespace IS the separator;
     insert nothing.
   - `trail == 0` -- **preserve today's behaviour exactly**: insert a
     single space `" "` as separator.
4. **Not yet terminated:**
   - `trail > 0` -- insert `"."` ONLY (one character, not `". "`) at
     `anchor`; the existing trailing whitespace becomes the separator
     after it.
   - `trail == 0` -- **preserve today's behaviour exactly**: insert
     `". "` as terminator.

Two of the four cases (3's `trail == 0` branch and 4's `trail == 0`
branch) are the two **preserve-today's-behaviour** cases named above,
alongside case 1's degenerate preservation.

**Inertness claim** (NARROWED by C15, 2026-09-08 -- read C15 before
citing the byte-for-byte characterisation below)**:** the change is
provably inert whenever `trail == 0`
-- i.e. on every input reachable before #242 landed, since pre-fix,
`Create`/`SetText`/`InsertAt` always stripped trailing whitespace, so
`trail` could never be `> 0` on any paragraph built through the public
API before this feature shipped. It therefore cannot regress
pre-existing data. `evidence/live-t5-joinfix.md` proves this directly:
the four `trail == 0` prediction rows (`''`, `'foo'`, `'foo.'`,
`'foo!'`) are required to match cycle 2's post-T1/T2 behaviour
byte-for-byte, and did (9/9 rows matched, 0 MISS, `run_mode: live`).

**Classification: PRE-EXISTING and NEWLY VISIBLE, not introduced by
the whitespace fix.** The terminator branch reads the raw last character
of whatever wrote `Contents` -- it does not care how that trailing
whitespace got there. FLEx itself, imports, or a direct LCM write could
always have produced a `Contents` value ending in whitespace; this
library's own `Create`/`SetText`/`InsertAt` simply could not, before C8,
because they stripped it away first. #242's fix did not create the
defect; it removed the one thing that had been accidentally masking it
for calls made through this library's own writers. **Consequence:** the
CHANGELOG entry for this fix is a **standalone `### Fixed` entry**
(dispatched to `/lex-doc`, not authored here), and cycle-2's "Known
interaction, not yet resolved" sub-paragraph is **DELETED, not amended**
-- it described an open defect that no longer exists, not a caveat to
soften.

**Miniature of the same point:** an all-whitespace paragraph (case 2,
`anchor == 0`) is still unreachable through all four public writers
today -- `Create`/`SetText`/`InsertAt` raise on whitespace-only input,
and so would a hypothetical `AppendSentence`-only construction path --
yet the branch must handle it, because `AppendSentence` cannot assume
its caller-supplied `para` was built exclusively through this library
(direct LCM writes, imports, or a future writer could produce it). This
is the pre-existing/newly-visible point from the paragraph above,
recurring in miniature at the code-branch level rather than the
feature level.

**Verification:** `reviews/cycle3-programmer.md` and
`evidence/live-t5-joinfix.md` -- 9 prediction rows, all `MATCH`,
`run_mode: live`, `target_sandbox`/`target_sandbox_path` only,
committed `a580f7b` (predictions) then `608200c2` (results + code +
tests, C28 forward rule). Offline baseline **1292 passed, 483
deselected** (+1 explained by the new `test_p8b`, not absorbed).

### C13 -- Checkpoint 4 / Q2 ruling: DECLINED, not deferred (cycle 3, 2026-09-07)

**Ruling:** Checkpoint 4 (the optional corpus-shaped reproduction of the
owner's field figures, `spec.md` C2: 60 identical/44 differing
paragraphs, total 104; 45 identical/41 differing segment baselines,
total 86) is **DECLINED**, not deferred.

**Rationale:** the owner's 44/104 and 41/86 field figures were
diagnostic, not a target this feature is obligated to reproduce
numerically. The mechanism they describe is already proven directly at
unit level by P6 (`evidence/live-t1-t2-fix.md`): 8 distinct payloads,
byte-for-byte round-trip, through all four writers, through the layer-B
LCM bypass, and through the in-memory/on-disk cycle. Reproducing the
owner's exact corpus number would re-prove a mechanism already proven,
at higher cost (building or sourcing a populated multi-paragraph,
multi-segment sandbox corpus) and at lower resolution (a corpus count is
an aggregate signal; P6 already isolates the mechanism payload-by-payload
and writer-by-writer).

**Explicit negative claim, recorded so no future reader assumes
otherwise: WE DO NOT CLAIM TO HAVE REPRODUCED THE OWNER'S 41/86 FIGURE.**
The fix is justified by the proven mechanism (C3(i), P6), not by a
corpus-scale replication of the field report.

**Q2 is marked DISCHARGED** by this ruling (see section 4 below).

---

## 3b. Cycle-4 and cycle-5 contract items (FROZEN, 2026-09-08)

### C14 -- the `ParagraphOperations.Create` docstring note (cycle 4, 2026-09-07)

**Recorded retroactively by the cycle-5 gate, 2026-09-08.** The cycle-3
independent gate (`reviews/cycle3-verification.md`) raised one P1: of the
four sites named in C1, only three carried the whitespace-preservation
docstring note required by Checkpoint 3's T3 --
`ParagraphOperations.Create` had none, so the change was documented at 3 of
4 sites. Commit `ed428f7` added it, discharging that P1.

**Binding text**, byte-identical at all four sites:

```
Note: leading/trailing whitespace in the value is preserved
verbatim (#242); a value that is entirely whitespace still
raises FP_ParameterError.
```

Present at `ParagraphOperations.py` `Create`, `SetText`, `InsertAt` and
`SegmentOperations.py` `AppendSentence` (the `text` param). Verified 4/4 at
HEAD by the cycle-5 code-conformance and docs verifiers independently.

**Why this item is being written now rather than at cycle 4:** commit
`ed428f7`'s message claims "records C12/C13/C14 in the spec", and the
campaign record claims "Contract C1-C14 frozen", but **C14 was never
written into this file** -- `grep -n C14 spec.md` returned zero hits until
this edit. The work had landed and was correct; only the contract entry
was missing. Recorded because an item that exists only in a commit message
cannot be cited or overturned by number, which is the mechanism this
feature's freeze discipline depends on. See
`reviews/cycle5-verification-swarm.md` N4.

### C15 -- C12's inertness claim, NARROWED (cycle 5, 2026-09-08)

**This item narrows C12; it does not overturn it.** C12's "Inertness
claim" paragraph and `evidence/live-t5-joinfix.md`'s "C12.4 inertness
proof" both state that the four `trail == 0` prediction rows are required
to match cycle 2's post-T1/T2 behaviour **byte-for-byte**. That
characterisation is too strong on the evidence:

- Cycle 2 measured only two seeds: `"foo "` (`test_p8`) and `"Seed."`
  (`test_p2`, which seeded every payload with that one fixed string).
- Of C12's four `trail == 0` rows, only the `'foo.'`-shaped
  (already-terminated, `trail == 0`) row has a recorded cycle-2
  counterpart. `''`, `'foo'` and `'foo!'` were **first measured at cycle
  3**, against predictions derived by reading C12's algorithm.

So **1 of the 4 rows is a byte-for-byte regression check against recorded
cycle-2 output; 3 of the 4 are a-priori predictions that matched.** Both are
legitimate under the C28 forward rule -- the predictions were committed
before the measuring run (`a580f7b` before `608200c`) -- but they are not
the same kind of evidence, and C12 conflated them.

**The inertness CONCLUSION is unaffected, and is now carried by a stronger
proof than the measurement.** The cycle-5 code-conformance verifier
hand-diffed the `trail == 0` paths against the pre-C12 source
(`608200c^`) case by case and established that every behavioural
divergence from pre-C12 is gated behind `trail > 0` or
`anchor == 0 and raw != ""`, so no `trail == 0` input can reach a changed
line. That is an exhaustive argument over the code, where the 9-row table
is a sample. C12's claim is therefore RIGHT in substance and imprecise in
its citation; this item fixes the citation.

### C16 -- the live-evidence durability gap (cycle 5, 2026-09-08) -- OPEN

`tests/live_status.json`, which CLAUDE.md makes the machine-checkable
anchor of every live-verification claim, **is gitignored
(`.gitignore:99`), absent from disk, and has never been committed.** No
evidence file in this feature quotes the JSON, and none records the
`run_timestamp` that would bind a claim to a specific run. Every
`run_mode: live` claim across cycles 1-3 is therefore prose that cannot be
re-derived from the repository.

**Explicit negative claim, recorded so no future reader over-reads this
item: THIS IS NOT EVIDENCE THAT ANY RUN WAS MOCKED.** Three things argue
the opposite, and are recorded here as the substitute evidence:

1. The offline/live split is internally coherent -- 483 deselected offline
   against 8 tests collected live, the 8 re-verified by `--collect-only`
   at cycle 5.
2. The LCM read-backs are genuine re-queries, not echoes of the input:
   `test_p8` re-reads through `project.Paragraphs.GetText(para)` after the
   write, and `test_p4` closes and reopens the project before re-reading.
3. `reviews/cycle3-verification.md`'s independent pass reports having read
   the file's `by_test` map while it still existed.

**Remedy (NOT performed -- blocked):** a future live run must paste the
`run_mode` AND `run_timestamp` lines verbatim into its evidence file, or
commit a redacted per-cycle snapshot. **This is blocked by C18** -- no live
run is possible until the interpreter is restored. The two items compound,
and C16 cannot be discharged before C18 is.

This is a gap in the project's evidence CONVENTION as applied here, not a
defect in the #242 fix. See `reviews/cycle5-verification-swarm.md` N1.

### C17 -- C1's line-number table is stale at HEAD (cycle 5, informational)

C1's HEAD column has drifted at all four sites, by up to +21 lines, from
the comments and the C12 four-case block the fix itself inserted. Actual
values at `3d357d8`, independently derived:

| Site | Method | `_ValidateParam` | Transform | `MakeString` | `Contents =` |
|---|---|---|---|---|---|
| `ParagraphOperations.py` | `Create` | 180 | 187 | 209 | 210 |
| `ParagraphOperations.py` | `SetText` | 593 | 599 | 607 | 609 |
| `ParagraphOperations.py` | `InsertAt` | 741 | 747 | 774 | 775 |
| `SegmentOperations.py` | `AppendSentence` | 603 | 610 | 643/659/668/673 (now 4-way) | 686 |

C1's own warning applies recursively: **use the code, not any table, for
current work.** Recorded so the drift is a known quantity rather than a
surprise. C9's cited `CHANGELOG.md:431` is likewise now `:500`, displaced
+69 lines by this feature's own entry; lines 15 and 63 are unmoved, and a
fourth `BREAKING` hit at `:95` is #242's own -- expected, not a defect.

### C18 -- the offline baseline is not reproducible in the current environment (cycle 5) -- **RESOLVED 2026-09-08, see C19**

The machine's only Python is **3.14.5**. `pyproject.toml` declares
`requires-python = ">=3.8,<3.14"` and pins `pythonnet >=3.0.3,<3.1`; only
pythonnet **3.1.0** ships a 3.14-compatible wheel. `import clr` therefore
fails at `flexicon/__init__.py:70`, 15 test modules fail collection, and
`python -m pytest tests -m "not requires_live_project" -q` is interrupted
before executing anything:

```
384 deselected, 7 warnings, 15 errors in 1.78s
Interrupted: 15 errors during collection
```

**Consequences, stated precisely:**

- The **1292 passed / 483 deselected** baseline that STATUS.md and
  `.crew-handoff.json` make a hard constraint is **neither confirmed nor
  refuted** as of 2026-09-08. It was last verified at cycle 3
  (`reviews/cycle3-verification.md` check 6, an independent run).
- **Zero tests ran against the changed code** at cycle 5. Per this
  feature's own rule, that is a ZERO, never a pass.
- The interpreter was replaced **after** the baseline was recorded; the
  evidence files' bare `python` invocations resolved to a supported
  interpreter at the time they ran.

**This is NOT attributable to the #242 change.** The failure is an
interpreter-level import at package `__init__`, hitting all 15 modules
regardless of subject matter; the two changed files are not implicated by
any of the 15 errors.

**Remedy (a human decision, not a verifier's):** restore a 3.8-3.13
interpreter with `pythonnet >=3.0.3,<3.1`, **or** rule on relaxing the pin
to allow `pythonnet 3.1.0` on 3.14 -- an API-surface decision affecting the
whole library, explicitly out of this feature's scope. Per CLAUDE.md this
is a `needs_human` handoff. Do not read C18 as evidence against the fix,
and do not discharge C16 until C18 is resolved.

---

### C19 -- C18 RESOLVED: newer Python allowed; the suite runs again (cycle 6, 2026-09-08)

**Ruling (user decision):** allow newer Python. C18's alternative -- relaxing
the pin rather than downgrading the interpreter -- is TAKEN.

**Change applied** (`pyproject.toml`):

| | before | after |
|---|---|---|
| `requires-python` | `>=3.8,<3.14` | `>=3.8,<3.15` |
| `pythonnet` | `>= 3.0.3, <3.1` | `>= 3.0.3, <3.2` |
| classifiers | ...3.13 | ...3.13, **3.14** |

The `<3.1` pin carried **no documented rationale** -- `git log -S` shows it
arrived with the `flexlibs2 -> flexicon` rename (`9b82ffa`) as an
undocumented known-good upper bound, not as a recorded compatibility
finding.

**Verified working:** `pythonnet 3.1.0` installs a real
`cp310.cp311.cp312.cp313.cp314` wheel on Python 3.14.5, `import clr`
succeeds, and the offline suite executes for the first time since C18 was
raised.

**Result: 1291 passed, 2 failed, 1 skipped, 483 deselected.** Deselected
matches the recorded baseline exactly.

**The 1292 figure is no longer the right comparator**, and this item
retires it as the binding baseline. Five commits landed after `b0e3d14`
(where 1292 was recorded) -- `ec54432` (the rename, which also ADDED
`tests/test_flexlibs2_alias_ratchet.py`), `4aca74a`, `a26d39c`, `bdbce02`
and the `3d357d8` merge -- so the collected total legitimately differs.
**New binding baseline: 1291 passed / 483 deselected at cycle 6**, with the
two failures below named and diagnosed rather than absorbed.

**NOT attributable to the upgrade:** all four failures seen on the first
run were diagnosed to root cause, and **none was caused by Python 3.14 or
pythonnet 3.1.** Two were repaired (C20); two remain, both pre-existing and
both needing a human decision (see section 4, Q4 and Q5).

### C20 -- Two tests were broken by the rename commit, not by the upgrade (cycle 6)

`tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen` had
two failing tests. The pythonnet exception they surfaced
(`'_FakeActionHandler' value cannot be converted to
SIL.LCModel.Core.KernelInterfaces.IActionHandler`) was a **symptom, not the
cause**.

**Root cause: commit `ec54432` (the `flexlibs2 -> flexicon` rename, PR
#241) split one coherent test into two broken ones.** It landed AFTER the
1292 baseline, which is why the breakage went unnoticed -- the environment
broke around the same time, so the suite was never run again until now.

The original single test (present at `b0e3d14`, `@patch`-decorated) did
`pytest.raises(RuntimeError)` and asserted on the fake helper's
`disposed` / `rollback_value_at_dispose`. The rename produced:

1. `test_rollback_flag_set_true_on_exception` -- kept the `@patch` and the
   exception docstring, but its body was replaced with assertions on
   `project._transaction_depth`. **That attribute does not exist**: it was
   DELETED by design under issue #234, and `FLExProject.py:274` records it
   as "formerly `self._transaction_depth`". On a `Mock` project the
   attribute auto-creates, so `assert project._transaction_depth == 1`
   compared a `Mock` to `1` and could never pass.
2. `test_depth_restored_on_exception` -- NEW, received the original body but
   **lost the `@patch` decorator**, so the REAL
   `UndoableUnitOfWorkHelper` was handed a `_FakeActionHandler`. It was
   doubly broken: an autouse fixture resets
   `_FakeUndoableUnitOfWorkHelper.instances = []` before every test, so its
   `instances[0]` would raise `IndexError` even if the .NET call had
   succeeded.

**Repair:** the two were merged back into the single coherent
`@patch`-decorated test that stood at the baseline, with a comment
recording the split so it is not "tidied" back. The bogus
`_transaction_depth` assertions are deleted, not adapted -- they assert a
reverted design. Depth is now observed through the action handler's
`CurrentDepth`, already covered by a sibling test in the same class.

**This is a test-only change** (no `flexicon/` code touched), so per
CLAUDE.md it needs no live verification. Verified by execution: the two
failures are gone and the merged test passes.

## 4. Open questions

**Q1 -- Should the 8 NEW sibling sites be fixed in this feature, a
follow-on feature, or filed as a separate issue?** See R3. **RESOLVED by
C10 (2026-09-07):** routed to `specs/tier1-silent-data-loss/QUEUE.md`
"Awaiting user approval" as Q-242A, not fixed in this feature.

**Q2 -- Should the owner's field-report shape (41/86 differing baselines
in a populated, reproduced-from-another-project corpus) be reproduced by a
targeted follow-up probe, given the cycle-1 probe used fresh scratch
paragraphs and did not reproduce it (C3)?** **DISCHARGED by C13 (cycle 3,
2026-09-07): DECLINED, not deferred.** The mechanism is already proven at
unit level by P6; reproducing the corpus number would re-prove it at
higher cost and lower resolution. Explicit negative claim recorded at
C13: this feature does NOT claim to have reproduced the owner's 41/86
figure.

**Q3 -- Does `CheckOperations.py`'s third variant (C6, item 3) belong in
this feature, in the 8-sites scope ruling (R3), or as its own separate
issue given its qualitatively different severity (total data loss on
non-`str` input, not merely lost whitespace)?** Explore's ranking placed it
first by severity; this spec does not pre-judge whether it should be
bundled with the other 7 or filed alone. **RESOLVED by C10 (2026-09-07):**
filed separately, at greater severity, as Q-242B in
`specs/tier1-silent-data-loss/QUEUE.md` "Awaiting user approval" --
deliberately NOT bundled with Q-242A so it is not triaged at whitespace
severity.

---

## 5. Contradictions checked for -- none found requiring side-by-side preservation

**Scope note (added cycle 5, 2026-09-08):** the check recorded below covers
**cycle 1 only**, as its own opening sentence says. `STATUS.md`'s bare
"Contradictions found and preserved / **None.**" reads more globally than
that. The cycle-5 gate swept all twelve review files across cycles 1-4 and
**also found no two asserting incompatible facts** -- the near-misses
(cycle-1 domain's Q4 vs C9, the three line-numbering conventions, the
480 -> 482 -> 483 deselected progression) all resolve, each already
recorded as an explicit overturn or a convention difference rather than a
concealed conflict. The one real imprecision found was not between reports
but inside a contract item: C12's inertness citation, now narrowed by
C15.

The three cycle-1 reports (programmer, explore, domain) and the evidence
file were checked against each other and against re-verification of the
live source at HEAD (this pass, 2026-09-07). No two reports assert
incompatible facts. The one place where numbers looked inconsistent at
first read -- Explore's "persist" line numbers (202/593/753/624) vs. this
pass's independently re-verified `Contents =` assignment lines
(203/595/754/633) -- is not a contradiction: Explore's convention counts
the `MakeString(...)` call as "persist," this pass's C1 table also gives
the final assignment line, and both are shown together in C1 so neither
reading is lost. The owner's field-report numbers (C2, from the GitHub
issue body) and the probe's "41/86" shorthand (`reviews/cycle1-programmer.md`,
`evidence/live-probe-cycle1.md`) are the same figure (45 identical + 41
differing = 86 total segment baselines) cited two different ways, not two
different measurements.

---

## 6. Open questions raised at cycle 6 (2026-09-08)

**Q4 -- The liblcm contract baseline is stale, by one genuine upstream
removal.** `tests/contract/test_lcm_contract.py::TestLiveRegressionCheck::
test_no_regressions_from_baseline` reports exactly one regression:

```
ILexEntryRepository.CorrectHomographNumbers() removed
```

**This is a REAL upstream API change, not a pythonnet artifact** --
confirmed by direct reflection on the installed liblcm, via both
`dir(ILexEntryRepository)` and raw `clr.GetClrType(...).GetMethods()`
(10 methods; the homograph-ish ones are `CollectHomographs`,
`GetHomographs`, `HomographMorphOrder`, `ResetHomographs` -- no
`CorrectHomographNumbers`).

**Severity: LOW. Zero callers.** `grep -rn CorrectHomographNumbers` over
`flexicon/` and `tests/` returns nothing outside
`tests/contract/snapshots/liblcm_baseline.json` itself. Nothing in this
library calls the removed method, so there is no code to adapt.

The baseline snapshot was generated **2026-08-13 under Python 3.12.7**; the
installed FieldWorks has evidently been updated since. `total_types_checked`
also moved 255 -> 257, which is explained by `4aca74a` touching
`tests/contract/snapshots/expected_contract.json`.

**Not decided here, deliberately:** regenerating `liblcm_baseline.json`
would accept ALL drift since August wholesale, and that snapshot is the
regression tripwire -- absorbing it silently is exactly what it exists to
prevent. A human should regenerate it as a deliberate, reviewed act.

**Q5 -- The rename left `flexlibs2` imports in the test tree, and one of
them is deliberate.**
`tests/test_flexlibs2_alias_ratchet.py::TestFlexlibs2AliasIsInboundOnly::
test_no_executable_flexlibs2_imports_outside_alias_package` -- itself added
by `ec54432` to prevent exactly this -- reports 9 offenders:
`tests/conftest.py:1392` and `:1451`,
`tests/operations/test_issue251_252_256_feature_struct_probe.py:36`,
`tests/operations/test_natural_classes.py:917` and `:954`,
`tests/operations/test_natural_class_feature_sync.py:721`,
`tests/operations/test_owner_cast_pattern.py:71` and `:630`,
`tests/write_path_transactions/test_capabilities.py:96`.

**This is #241's unfinished rename, entirely unrelated to the interpreter**
-- the check is a static AST scan with no runtime component, so it fails
identically on any Python version.

**Why it was NOT fixed here, and why it is a policy question rather than a
cleanup:** eight are incidental leftovers that should simply become
`flexicon`, but **`tests/write_path_transactions/test_capabilities.py:96`
is DELIBERATE** -- it wraps `import flexlibs2` in
`warnings.catch_warnings()` suppressing `DeprecationWarning`, i.e. it
exists to exercise the alias. The ratchet's own docstring exempts "the
alias package and its own tests", so that site either needs an explicit
exemption or needs to move into the alias's own tests. Deciding that is
#240/#241's call, and the eight mechanical edits span four other features'
test files including `tests/conftest.py`. Left for its owner.
