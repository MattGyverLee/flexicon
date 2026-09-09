# Cycle 4 -- Archivist report: close #270/#278, commit test fix + evidence, prepare (unfiled) follow-up issues

**Date:** 2026-09-09
**Repo:** MattGyverLee/flexicon (`gh repo set-default MattGyverLee/flexicon` run first)
**Action:** Issue close x2, commit, two unfiled issue drafts.

## 1. Close comment posted on #270 (verbatim)

Posted via `gh issue comment 270`, then `gh issue close 270` (no additional
comment on close). URL: https://github.com/MattGyverLee/flexicon/issues/270#issuecomment-5605101851

> Live verification for the collection-cast sweep in this issue is now complete across four evidence files under `specs/269-272-casting-and-factory-seam/evidence/`, and the record needs to be read as a chronological correction, not a single clean run:
>
> - `live-269-270-272.md` (2026-09-08) -- Tiers 1-2.
> - `live-270-tier34.md` (cycle 1) -- Tier 3 PASS (both the subtype-surface and recursion assertions, live). Tier 4 was reported as SKIPPED, attributed to "Sena 3 has no constituent charts." That attribution was wrong and has been retracted in a dated CORRECTION section appended to this file: the test read `sena3_sandbox.ConstChart` (singular), but `FLExProject` defines only `ConstCharts` (plural) with no `__getattr__` fallback, so that line raised `AttributeError` unconditionally and the `pytest.skip` two lines below it was unreachable dead code. The skip was never a genuine data-shape gap.
> - `live-270-tier4-target.md` (cycle 2) -- retargeted the Tier 4 test onto `target_sandbox` and reported it green (4 passed). That green was a false positive. Three compounding defects meant the Tier 4 assertion never actually executed: `rows.Create(chart, label=...)` raised `AttributeError` because `IConstChartRow.Label` is a bare `ITsString` with no `set_String`; a `return` misplaced inside the `for item in (marker, col):` loop of the test's own `finally:` block silently swallowed that exception (a `return` in `finally` suppresses an in-flight exception) and also leaked the second marker; and a trailing `pytest.skip` was unreachable dead code left over from the pre-fix Sena-3 version. This file documents all three defects, plus a disposable diagnostic that isolated and confirmed the underlying `ConstChartCellTagOperations.GetAll` fix is itself correct, independent of the test's own bugs.
> - `live-270-tier4-committed.md` (cycle 3) -- the three defects above were removed from the committed test (the `label=` kwarg dropped with an explanatory comment, the stray `return` removed so both markers are always deleted, the dead `pytest.skip` deleted), and the test now passes live on `target_sandbox` (`run_mode: live`, 4 passed). This time execution of the assertion itself was proven two independent ways: a transient print showing real re-queried HVOs (`expected=[10446, 10447] actual=[10446, 10447]`), and an assertion-inversion (`len(actual)==999 and actual==[]`) that genuinely FAILED (`assert (2 == 999)`), confirming the test is not vacuously green. All scratch edits used for this proof were reverted afterward; the file's sha256 matched before and after.
>
> A repo-wide AST scan for `return`/`break`/`continue` inside any `finally` body found exactly one hit -- the cycle-2 line described above, now repaired -- so no other recorded live evidence in this repo is devalued by the same mechanism.
>
> Net result: Tiers 1-4 are all now live-verified, but Tier 4 took two correction cycles to get there honestly; the first pass (cycle 2) was not a real verification and must not be cited as one.
>
> Deferrals that hold from the original scoping, each separately tracked and out of scope for this issue:
> - `GramCatOperations.GetAll` recursion is a data-model decision, not a casting defect -- #276 remains an open follow-up, pinned offline by `TestGramCatGetAllRecursionClaim` in `tests/operations/test_collection_cast_pattern.py`.
> - The two always-`[]` getters (`OverlayOperations.GetPossItems`, `EnvironmentOperations._GetSequence`) -- #277 remains an open follow-up.
> - The 4 unregistered cast-registry interfaces plus the `FLExProject` possibility-helper API decision -- #279 remains an open follow-up.

`gh issue close 270` confirmed: `Closed issue MattGyverLee/flexicon#270`.

## 2. Close comment posted on #278 (verbatim)

Posted via `gh issue comment 278`, then `gh issue close 278`. URL:
https://github.com/MattGyverLee/flexicon/issues/278#issuecomment-5605102296

> All three claims underlying this issue are now resolved, verified live:
>
> 1. Fixture presence: `tests/fixtures/Sena 3 2018-09-11 1145.fwbackup` (15.4 MB) is present on this workstation, and `sena3_sandbox` opens it successfully.
> 2. The 23 ERRORs are gone: re-running the 11 previously-erroring test files under `FLEXLIBS_REQUIRE_LIVE=1` now produces `74 passed, 3 skipped, 0 errors` (was 23 ERRORs, all "sena3_sandbox unavailable", in the 2026-09-08 #269/#272 evidence run). See `specs/269-272-casting-and-factory-seam/evidence/live-270-tier34.md` (the second command block, and the "#278 fixture verdict" section). The 3 remaining skips are documented data-shape skips (no pre-existing locations to delete beyond Phase B coverage; `PeopleOC` is unordered so reorder is inapplicable; the sandbox has no entries with `PronunciationsOS` items), not fixture-availability errors.
> 3. #270 Tiers 3 and 4 are live-verified: Tier 3 (subtype surface + recursion) passed live in the same run; Tier 4 passed live in `specs/269-272-casting-and-factory-seam/evidence/live-270-tier4-committed.md` after a test-repair cycle (see #270's close comment for the full narrative -- that pass required two correction rounds, the first of which was a false positive).
>
> Important caveat -- this unblocking is a workstation fact, not a repo change. The fixture file is gitignored and local-only:
>
> ```
> .gitignore:98  ->  tests/fixtures/*.fwbackup
> ```
>
> The file present here is `tests/fixtures/Sena 3 2018-09-11 1145.fwbackup`. A fresh clone of this repo does not get this fixture automatically; it must be provisioned locally before any `sena3_sandbox`-dependent test can run live. Nothing about this close changes that -- it only confirms that on a workstation where the fixture is already present, the previously-reported blocker (23 errors, Tiers 3/4 unverifiable) is resolved.
>
> Documentation note: `tests/conftest.py`'s `sena3_sandbox` fixture points to `scripts/restore_sena3.py` when the fixture is missing, and `tests/LIVE_TESTING.md` ("Sena 3 fixture and restoration") describes restoring FROM the fixture once it already exists, but neither document says where to obtain the `.fwbackup` file in the first place on a fresh checkout -- unlike the Target fixture, which has an explicit "known locations" list (`tests/LIVE_TESTING.md`, "The Target fixture backup" section). This gap is not part of what #278 reported, so it is not a reason to keep this issue open, but it is worth a small doc follow-up.

`gh issue close 278` confirmed: `Closed issue MattGyverLee/flexicon#278`.

### #278 provisioning-doc finding (flagged, not filed)

Checked `tests/conftest.py` (the `sena3_sandbox` fixture's `_unavailable`
message points to `scripts/restore_sena3.py`) and `tests/LIVE_TESTING.md`
("Sena 3 fixture and restoration", lines ~147-165). Both describe
restoring from the fixture once it exists; neither states where a
newcomer obtains `tests/fixtures/Sena 3 *.fwbackup` on a fresh clone.
Contrast with the Target fixture, which has an explicit "known
locations" list (`tests/LIVE_TESTING.md`, "The Target fixture backup",
lines ~43-63, with two concrete workstation paths). `LIVE_TESTING.md`
line 150 even says the Sena 3 fixture is "checked into
`tests/fixtures/Sena 3 *.fwbackup`" in the same breath as calling it
"gitignored" -- an internally contradictory sentence (a gitignored path
is by definition not checked into git). Recommend, as a small doc
follow-up (not filed by this agent): add a "known locations" list for
the Sena 3 backup to `LIVE_TESTING.md`, matching the Target section's
shape, and fix the "checked into ... gitignored" phrasing.

## 3. Commit

Staged exactly 12 files by name (verified with `git status --porcelain`
before and after; nothing else was swept in; `tests/fixtures/*` was not
touched):

```
M  tests/operations/test_collection_cast_pattern.py
A  specs/269-272-casting-and-factory-seam/evidence/live-270-tier34.md
A  specs/269-272-casting-and-factory-seam/evidence/live-270-tier4-committed.md
A  specs/269-272-casting-and-factory-seam/evidence/live-270-tier4-target.md
A  specs/269-272-casting-and-factory-seam/reviews/cycle1-archivist.md
A  specs/269-272-casting-and-factory-seam/reviews/cycle1-verification.md
A  specs/269-272-casting-and-factory-seam/reviews/cycle2-programmer.md
A  specs/269-272-casting-and-factory-seam/reviews/cycle2-verification.md
A  specs/269-272-casting-and-factory-seam/reviews/cycle3-domain.md
A  specs/269-272-casting-and-factory-seam/reviews/cycle3-programmer.md
A  specs/269-272-casting-and-factory-seam/reviews/cycle3-qc.md
A  specs/269-272-casting-and-factory-seam/reviews/cycle3-verification.md
```

The `.githooks` commit-msg guard (armed via `core.hooksPath`) accepted
the message without complaint -- no rejection to report.

Commit SHA: `dbd7af04d376a9946e4c61248f9e1f00e4de56e3`

Commit message (as committed):

```
test(270): repair the Tier 4 collection-cast test and record live evidence

The committed Tier 4 test could report green without ever executing
its assertion. rows.Create(chart, label=...) raised AttributeError
because IConstChartRow.Label is a bare ITsString with no
set_String, and a stray `return` inside the finally-block cleanup
loop swallowed that exception (while also leaking one marker).
Dropped the label= kwarg with an explanatory comment, removed the
return so both markers are always deleted, and deleted an
unreachable trailing pytest.skip.

Tier 4 now passes on the committed test under
FLEXLIBS_REQUIRE_LIVE=1 with run_mode: live, and execution of the
assertion was proven two independent ways: a transient print of the
re-queried HVOs, and an assertion inversion that genuinely failed.

Adds four live-evidence files and the crew review records for
cycles 1-3. Follow-ups #276, #277 and #279 remain open.

Refs #270, #278.

Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>
```

Note: the task briefs template quoted `Co-Authored-By: Claude Opus 5
(1M context)`, but the live system-reminder attribution instruction --
explicitly stated to replace any earlier attribution guidance --
requires `Claude Sonnet 5 <noreply@anthropic.com>`. Used the latter as
the binding instruction.

`git show --stat HEAD`:

```
commit dbd7af04d376a9946e4c61248f9e1f00e4de56e3
Author: Matthew Lee <matthew_lee@sil.org>
Date:   Wed Sep 9 11:19:51 2026 -0500

    test(270): repair the Tier 4 collection-cast test and record live evidence
    ...
    Refs #270, #278.

    Co-Authored-By: Claude Sonnet 5 <noreply@anthropic.com>

 .../evidence/live-270-tier34.md                    | 200 +++++++++++++++++++++
 .../evidence/live-270-tier4-committed.md           | 158 ++++++++++++++++
 .../evidence/live-270-tier4-target.md              | 196 ++++++++++++++++++++
 .../reviews/cycle1-archivist.md                    |  73 ++++++++
 .../reviews/cycle1-verification.md                 | 107 +++++++++++
 .../reviews/cycle2-programmer.md                   |  55 ++++++
 .../reviews/cycle2-verification.md                 |  80 +++++++++
 .../reviews/cycle3-domain.md                       | 101 +++++++++++
 .../reviews/cycle3-programmer.md                   |  30 ++++
 .../reviews/cycle3-qc.md                           |  76 ++++++++
 .../reviews/cycle3-verification.md                 |  70 ++++++++
 tests/operations/test_collection_cast_pattern.py   |  90 +++++++---
 12 files changed, 1209 insertions(+), 27 deletions(-)
```

`git status --porcelain` after the commit: empty (clean tree). Not
pushed -- commit is local only, per instructions.

## 4. Two issue drafts -- SINCE FILED (user approved, 2026-09-09)

These were prepared unfiled and put to the user, who approved them.
Both are now filed and OPEN:

- Issue A -> **#290** https://github.com/MattGyverLee/flexicon/issues/290
- Issue B -> **#291** https://github.com/MattGyverLee/flexicon/issues/291

Filed verbatim from the bodies below. Verified after filing that #276,
#277 and #279 remain OPEN and that nothing was auto-closed.

The original drafting note follows for the record: at the time this
report was written, `gh issue create` had NOT been run for either.

### Issue A -- ConstChartRow Label/Notes set_String/get_String family

Title:
```
ConstChartRowOperations.Create/SetLabel call set_String on IConstChartRow.Label, a bare ITsString (AttributeError); Notes/DiscourseOperations sites need a live reflection pass
```

Body:

```markdown
## Summary

A live run against target_sandbox, during verification work related to
#270, confirmed that ConstChartRowOperations.Create(chart, label=...)
crashes: IConstChartRow.Label is a bare ITsString, not an IMultiString,
and has no set_String. This is the same same-name/wrong-type trap
already catalogued in docs/API_ISSUES_CATEGORIZED.md "Category 8"
(Source, BaselineText).

## Confirmed live traceback

Recorded in
specs/269-272-casting-and-factory-seam/evidence/live-270-tier4-target.md:

```
AttributeError: ITsString object has no attribute set_String. Did you
mean: ToString.
  flexicon/code/Discourse/ConstChartRowOperations.py:132
```

## Site table

| Site | Call | Live evidence | Status |
|---|---|---|---|
| ConstChartRowOperations.py:132 (Create, label=) | new_row.Label.set_String(ws, mkstr) | Yes -- live traceback above | CONFIRMED BROKEN |
| ConstChartRowOperations.py:339 (SetLabel) | row.Label.set_String(ws, mkstr) | Same field/type as 132, not independently executed | CONFIRMED BROKEN (same root cause) |
| ConstChartRowOperations.py:137 (Create, notes=) | new_row.Notes.set_String(ws, mkstr) | None -- the live run crashed at 132 before reaching this line | UNDETERMINED -- presumed broken by analogy, needs its own isolating live hit (notes= with no label=) |
| ConstChartRowOperations.py:414 (SetNotes) | row.Notes.set_String(ws, mkstr) | None | UNDETERMINED -- same status as 137 |
| DiscourseOperations.py:888 (SetCellContent, hasattr(cell, "Label") branch) | cell.Label.set_String(ws, content_str) | None | UNDETERMINED -- reachability itself is unclear; see below |

Do not upgrade any UNDETERMINED row to confirmed without an independent
live hit. Sites 137 and 414, and the DiscourseOperations.py:888 branch,
were never reached in the run that produced the confirmed traceback --
that run crashed at 132 first.

Bonus finding, read side, same field: ConstChartRowOperations.py:299
(GetLabel) and :375 (GetNotes) call .get_String(ws) on the same
bare-ITsString field. Per Category 8's BaselineText entry, calling
.get_String(ws) on a bare ITsString raises AttributeError at runtime, so
the getters are equally suspect -- untested only because no live call
has reached them. Bundle GetLabel/GetNotes into the same investigation
and fix.

## Reachability of DiscourseOperations.py:888

SetCellContent's cell is documented as an element of GetCells(row) -- a
row.CellsOS element, hence one of the four concrete cell-part types
(ConstChartWordGroup, ConstChartTag, ConstChartClauseMarker,
ConstChartMovedTextMarker; see the cast_to_concrete comment at
DiscourseOperations.py:820-826). None of the four sibling Operations
classes for those types references a Label field -- they use TagRA,
WordGroupRA, DependentClausesRS. So the hasattr(cell, "Label") branch may
be unreachable for any real cell-part today, firing only if a caller
mistakenly passes an IConstChartRow (which does have Label), in which
case it hits the same confirmed bug. The mirrored read branch at
GetCellContent line 950 raises the same question. Settling this needs
live dir() reflection on instances of the four concrete cell-part types,
not on a row -- that reflection has not yet been run.

Warning -- do not touch this by a blanket edit: the sibling Comment
branch at DiscourseOperations.py:892 is believed genuinely correct -- an
annotation's Comment really is a multistring -- and must not be changed
alongside this fix.

## Proposed fix

Route the confirmed and confirmed-by-analogy Label/Notes accesses on
IConstChartRow through the existing BaseOperations house idiom for
bare-ITsString fields (_MakeTsString / _ReadTsString, already used for
ILexSense.Source) instead of TsStringUtils.MakeString plus
.set_String/.get_String. Leave DiscourseOperations.py:892 alone.

## Before any fix is written

This analysis was done without a live reflection pass on sites 137, 414,
and 888 (the analyst had no Bash tool available and could not run
type()/dir() against a live LCM instance). Confirm those three sites
live -- independently of the 132 traceback -- before writing or verifying
a fix, so the UNDETERMINED rows above get resolved on real evidence
rather than analogy.

## Write-path caveat

Per CLAUDE.md, this is write-path work: any fix needs its own live
verification under FLEXLIBS_REQUIRE_LIVE=1 against target_sandbox, with
pre/post state re-queried from the LCM (not asserted against the value
just written), recorded in its own evidence/live-<task>.md.

## Category 8 update

Add a new row for IConstChartRow.Label (confirmed bare ITsString)
alongside Source and BaselineText in docs/API_ISSUES_CATEGORIZED.md,
extended to Notes once independently confirmed live.

## Scope / provenance

Out of scope for #270 -- this is not a casting defect, it surfaced
incidentally while live-verifying #270's Tier 4 fix. Follow-ups #276,
#277 and #279 are unrelated and untouched by this finding.
```

Command to file it, if approved (NOT RUN):

```
gh issue create --repo MattGyverLee/flexicon \
  --title "ConstChartRowOperations.Create/SetLabel call set_String on IConstChartRow.Label, a bare ITsString (AttributeError); Notes/DiscourseOperations sites need a live reflection pass" \
  --body-file <path to the body above saved as a .md file>
```

### Issue B -- test_wfi_analysis.py:682 broad-except hazard

Title:
```
test_wfi_analysis.py:682 broad except-Exception can swallow a failing cascade-delete assertion
```

Body:

```markdown
## Summary

tests/operations/test_wfi_analysis.py:682, inside
TestWfiAnalysisDeleteWithMorphBundles.test_delete_analysis_with_morph_bundle_cascades
(cascade-delete coverage related to #99 and #32), has a broad except
Exception handler wrapped around an assert. Because AssertionError is
itself a subclass of Exception, a genuinely failing assertion is caught
and silently discarded rather than failing the test.

## The mechanism, lines 675-686

```python
try:
    leftover = writable_project.Object(bundle_hvo)
    assert leftover is None, (
        "WfiMorphBundle survived deletion of its owning "
        "analysis -- cascade delete did not fire. ..."
    )
except Exception:
    # Any exception from Object() also means the bundle is gone ...
    pass
```

The handler was clearly intended to absorb a lookup failure from
Object() on a deleted HVO (e.g. a pythonnet-specific exception type),
not to catch the assert beneath it. But except Exception catches both.
If the cascade delete genuinely fails to remove the WfiMorphBundle,
leftover is not None, the assert raises, and the handler swallows it --
the test then reports green with cascade delete broken. This defeats the
one claim the test exists to prove.

## No recorded live evidence rests on this site

A search of specs/*/evidence/ found no file referencing
test_delete_analysis_with_morph_bundle_cascades or "cascade delete" by
name. specs/write-path-transactions/evidence/live-def-default-flip.md:199
does list test_wfi_analysis.py in a harness-fix table, but cites a
different site (SetEvaluation x2, MorphBundlesOS.Add, an
UndoableOperation-wrapping fix around line 653), unrelated to the
swallowed assertion at 682. This is a pre-existing test-integrity defect,
unrelated to #270 and not blocking anything currently tracked there.

## Sibling sites triaged BENIGN (do not re-triage; no action needed)

Five other try/assert sites with a narrower except StopIteration: pass
handler were checked in the same sweep and are BENIGN, because
AssertionError is a different exception type from StopIteration and
propagates normally:

- tests/operations/test_allomorphs_live.py:138
- tests/operations/test_etymologies_live.py:176
- tests/operations/test_examples_live.py:136
- tests/operations/test_pronunciations_live.py:184
- tests/operations/test_variants_live.py:197

All five follow the shape except StopIteration: pass around assert first
is not None, where an empty project is a legitimate outcome the
StopIteration handler is meant to absorb. Only the
test_wfi_analysis.py:682 site uses the broader except Exception.

## Recommended fix shape (not implemented)

Restructure so the assert sits OUTSIDE the try: call Object() inside the
try, capture the result (or a sentinel / caught-exception flag), then
assert after the block. Alternatively, narrow the handler to the
specific exception type pythonnet actually raises for a deleted HVO.
Either approach is a test-integrity change to a write-path cascade
claim, so the corrected test warrants its own live verification -- at
minimum, confirming the corrected assertion still passes when the
cascade genuinely succeeds, per CLAUDE.md's live-verification
requirement.

## Scope / provenance

Not part of #270 -- none of the 6 sites reviewed for this hazard is in
the #270 file; this surfaced incidentally during that issue's QC sweep.
Relates to the cascade-delete coverage originally added for #99 and #32.
```

Command to file it, if approved (NOT RUN):

```
gh issue create --repo MattGyverLee/flexicon \
  --title "test_wfi_analysis.py:682 broad except-Exception can swallow a failing cascade-delete assertion" \
  --body-file <path to the body above saved as a .md file>
```

UPDATE 2026-09-09: both have since been filed with the user's approval,
as #290 (Issue A) and #291 (Issue B). Both are OPEN.

## Final verified issue-state table

| Issue | State (confirmed via `gh issue view --json state`) |
|---|---|
| #269 | CLOSED |
| #270 | CLOSED (this cycle) |
| #276 | OPEN |
| #277 | OPEN |
| #278 | CLOSED (this cycle) |
| #279 | OPEN |

## Cross-references

- Commit: `dbd7af04d376a9946e4c61248f9e1f00e4de56e3` (local, not pushed)
- Issues closed: #270, #278
- Issues referenced (Refs, kept open): #276, #277, #279
- Issue drafts prepared, not filed: "ConstChartRowOperations Label/Notes
  set_String/get_String family" (Issue A); "test_wfi_analysis.py:682
  broad-except hazard" (Issue B)
- Source reports read: cycle1-archivist.md, cycle3-verification.md,
  cycle3-programmer.md, cycle3-domain.md, cycle3-qc.md, plus all four
  evidence files under specs/269-272-casting-and-factory-seam/evidence/

## Doc handoff

- [ ] /lex-doc consulted before this commit -- NOT consulted this cycle;
  the task brief scoped this as an Archivist-only cycle (close two
  issues, commit an already-programmer-fixed test plus evidence, draft
  two unfiled issues). No CHANGELOG/migration-guide surface changed by
  this commit (it is test-only plus spec records).
- [ ] Doc patches staged -- none needed this cycle.
- [x] Justification for skipping: no public-API change; the only
  doc-adjacent finding (Sena 3 fixture provisioning is undocumented) is
  flagged above as a follow-up, not actioned, per the task brief's
  explicit instruction not to open an issue for it myself.

## Pending follow-ups

- #276, #277, #279 remain open (by design, per the brief).
- Issue A and Issue B were approved and filed as #290 and #291 (both OPEN).
- Small doc follow-up flagged: tests/LIVE_TESTING.md needs a "known
  locations" list for the Sena 3 .fwbackup, matching the Target section,
  and a fix to the self-contradictory "checked into ... gitignored"
  phrasing at line 150. Not filed as an issue per instructions.

---
**Archivist:** /lex-archivist
