# Live verification -- issue #270 Tiers 3 and 4

**Project:** Sena 3 | **Fixture:** sena3_sandbox (tempdir copy of
`tests/fixtures/Sena 3 2018-09-11 1145.fwbackup`, 15.4 MB)
**Date:** 2026-09-09
**FieldWorks:** C:\Program Files\SIL\FieldWorks 9
**LibLCM:** 11.0.0.55173 (SIL.LCModel.dll FileVersion)

## Commands run

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_collection_cast_pattern.py -m requires_live_project -q -rs
```

Result: `3 passed, 1 skipped, 68 deselected` (verbose collection: 4 items
selected from the `TestCollectionCastLive` class).

`tests/live_status.json` -> `"run_mode": "live"`,
`"run_timestamp": "2026-09-09T15:41:07Z"` -- requirement satisfied.

Second (separate) run, for issue #278 (missing-fixture blocker, 23 tests):

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_allomorphs_live.py tests/operations/test_etymologies_live.py `
  tests/operations/test_examples_live.py tests/operations/test_feature_struc_resolver.py `
  tests/operations/test_issue254_live_cycle2.py tests/operations/test_issue254_morphra_probe.py `
  tests/operations/test_lexentry_resolve_object_live.py tests/operations/test_locations_live.py `
  tests/operations/test_persons_live.py tests/operations/test_pronunciations_live.py `
  tests/operations/test_variants_live.py -m requires_live_project -q -rs
```

Result: `74 passed, 3 skipped, 13 deselected` -- **zero errors** (was 23
ERRORs in the #269/#272 evidence run of 2026-09-08, all "sena3_sandbox
unavailable"). `tests/live_status.json` -> `"run_mode": "live"`,
`"run_timestamp": "2026-09-09T15:43:50Z"`.

## Claim under test (issue #270)

Tier 3: `PossibilityListOperations.GetItems()` elements from a
subtype-backed list (e.g. Parts of Speech) must be cast to their concrete
LCM type, exposing subtype-only members (`DefaultInflectionClassRA` on
`IPartOfSpeech`), not left as bare `ICmPossibility`.

Tier 3 (recursion): `PossibilityListOperations.GetSubitems(recursive=True)`
must actually recurse into grandchildren, not silently no-op at one level.

Tier 4: `ConstChartCellTagOperations.GetAll(row)` must return the
`ConstChartTag` objects actually present in `row.CellsOS`, not `[]` (the
pre-fix isinstance filter matched nothing).

## Test 1 -- test_possibility_items_expose_subtype_surface

**Verdict: PASS** (assertions executed, not skipped)

Pre-state (read from LCM): `project.lp.PartsOfSpeechOA` is present; the
Parts of Speech list contains 11 items.

Post-state (re-queried from LCM via `PossibilityLists.GetItems(pos_list,
recursive=False)`, not from any value passed in):

| hvo | ClassName | has DefaultInflectionClassRA |
|-----|-----------|-------------------------------|
| 42183 | PartOfSpeech | True |
| 100407 | PartOfSpeech | True |
| 69519 | PartOfSpeech | True |
| 119927 | PartOfSpeech | True |
| 50512 | PartOfSpeech | True |
| 65501 | PartOfSpeech | True |
| ... (11 total) | PartOfSpeech | True |

All 11 items answered `ClassName == "PartOfSpeech"` and exposed
`DefaultInflectionClassRA` (value `None` for these items, but the
attribute itself is the IPartOfSpeech-only surface under test -- a bare
`ICmPossibility` element does not have this attribute at all, which is
what the pre-fix code returned).

## Test 2 -- test_subitem_recursion_reaches_grandchildren

**Verdict: PASS** (assertions executed, not skipped)

Pre-state (read from LCM): `project.lp.SemanticDomainListOA` is present;
9 top-level semantic domains.

Post-state (re-queried from LCM): top-level domain hvo=58915 --
`GetSubitems(recursive=False)` -> 7 items; `GetSubitems(recursive=True)`
-> 105 items. `105 > 7` (strictly more), and the direct-children Hvo set
is a subset of the recursive Hvo set (`direct_hvos <= deep_hvos` == True).
This is the exact assertion in the test body, confirmed with real hvo
counts rather than inferred from the boolean pass alone.

## Test 3 -- test_chart_cell_tag_getall_is_not_empty_when_tags_exist

**Verdict: FAIL: unverified (SKIPPED -- no fixture data, not a code
failure)**

pytest output: `SKIPPED [1] tests/operations/test_collection_cast_pattern.py:1005:
Sena 3 has no constituent charts`

### Data shape found (probe run against the same sena3_sandbox, same
session, via a disposable pytest file deleted immediately after --
`tests/operations/test_zzz_probe_270_scratch.py`, not committed):

```
Chart count: 0
```

`project.ConstChart.GetAll()` returns an empty list for this Sena 3
backup (`Sena 3 2018-09-11 1145.fwbackup`). There is no constituent chart
of any kind in this snapshot, therefore no chart row, therefore no
`row.CellsOS` to contain a `ConstChartTag`. The skip is genuine: the
Tier 4 `ConstChartCellTagOperations.GetAll` mechanism could not be
exercised because the fixture data does not contain the precondition, not
because of a fixture-availability problem (the sandbox itself opened and
served the rest of the file's tests without error) and not because of any
code defect.

**What a follow-up cycle needs:** this Sena 3 snapshot has zero
constituent charts. Retargeting this test requires either (a) a different
Sena 3 backup/version known to contain a Discourse Chart, or (b) a
Target-sandbox-based test that first creates a chart, a row, and a
`ConstChartTag` cell (mirroring how Tier 1's
`test_complex_form_component_round_trip` builds its own precondition data
on a Target sandbox rather than relying on Sena 3 to already contain it).
Option (b) is consistent with this repo's default-to-Target-for-anything-
that-needs-created-data convention and does not depend on Sena 3 content
at all.

## #278 fixture verdict (separate gate)

11 sena3-dependent test files (23 previously-erroring tests plus their
siblings in the same files) run cleanly against the new `sena3_sandbox`
fixture: **74 passed, 3 skipped, 0 errors**. The three skips are
data-shape skips with their own documented rationale (no pre-existing
locations to delete beyond Phase B coverage; `PeopleOC` is unordered so
reorder is inapplicable; sandbox has no entries with `PronunciationsOS`
items) -- none is a "sandbox unavailable" error, so the #278 fixture gate
is **CLEAR**.

## Cleanup

Both pytest runs used `sena3_sandbox`, which opens a tempdir-unzipped
COPY of the `.fwbackup` and deletes the tempdir in the fixture's
`finally:` block; the user's real Sena 3 project
(`C:\ProgramData\SIL\FieldWorks\Projects\Sena 3`) was never opened or
touched. The probe script used for Test 3's data-shape investigation was
a disposable pytest file (`test_zzz_probe_270_scratch.py`) created,
executed once, and deleted before this evidence file was written;
`git status` on the repo shows no production or test-suite files
modified as a byproduct of this verification.

## Result

- Tier 3 (subtype surface): **[PASS]**
- Tier 3 (recursion to grandchildren): **[PASS]**
- Tier 4 (ConstChartCellTagOperations.GetAll): **[FAIL: unverified]** --
  genuinely skipped; no ConstChartTag data exists in this Sena 3 snapshot
  to exercise the assertion. Mechanism remains proven only offline
  (unit/mock level), per the original #270 spec.
- #278 fixture (missing Sena 3 backup blocker): **[CLEAR]** -- 0 errors
  across all 11 previously-blocked files.

---

## CORRECTION (2026-09-09, cycle 3 verification)

The "Test 3" causal claim above -- that the Tier 4 skip was because "Sena 3
has no constituent charts" -- **cannot be correct as described** and is
retracted. The pre-fix line this test ran was
`charts = list(sena3_sandbox.ConstChart.GetAll())`, using `ConstChart`
(singular). `FLExProject` (`flexicon/code/FLExProject.py`) defines only
`ConstCharts` (plural, line 2820); it has no `ConstChart` singular
accessor and no `__getattr__`/`__getattribute__` override. Accessing
`sena3_sandbox.ConstChart` therefore raises `AttributeError`
unconditionally, regardless of what Sena 3 contains, so execution could
never reach the `pytest.skip("No chart row with a ConstChartTag found in
Sena 3")` call two lines later. The genuine cause was an **accessor typo**
in the test, not a data-shape gap in the fixture.

This was first identified in cycle 2's diagnosis
(`specs/269-272-casting-and-factory-seam/reviews/` and
`evidence/live-270-tier4-target.md`, "Corrected diagnosis of the cycle-1
Tier 4 skip" section) and is independently re-confirmed here in cycle 3.

Tiers 1-3 are **not** invalidated by this correction -- Test 1
(`test_possibility_items_expose_subtype_surface`) and Test 2
(`test_subitem_recursion_reaches_grandchildren`) above ran to completion
and their PASS verdicts stand as originally recorded. But going forward,
Tiers 1-3's live status should be cited from cycle 2's and cycle 3's live
runs (`evidence/live-270-tier4-target.md` and
`evidence/live-270-tier4-committed.md`), not solely from this file, since
this file's own account of why Tier 4 was skipped was wrong and calls its
narrative reliability into question independent of its raw pytest output.

Tier 4 itself is no longer a skip as of cycle 3: the committed test now
targets `target_sandbox` and constructs its own chart/row/tag data rather
than depending on Sena 3 content, and passed live with its assertion
proven to have executed (see
`evidence/live-270-tier4-committed.md`).
