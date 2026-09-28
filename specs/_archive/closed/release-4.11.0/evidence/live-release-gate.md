# 4.11.0 release gate -- live verification evidence

**Date:** 2026-09-27
**Branch:** `main` @ `11ebfea` (merge of #571 / fix/issue-561) plus
uncommitted gate fixes (chart-ownership rewrite, ReplaceAnalysis
robustness, DsDiscourseData cast registration, test corrections for
#523/#552/PN9, ratchet updates for #515/#528)
**Host:** Windows 11, FieldWorks 9 (same machine as the 4.10.0 gate)

## Commands

```
python -m pytest -m "not requires_live_project" -q
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest -m requires_live_project -q
```

## Results

| Run | Result | `run_mode` |
|---|---|---|
| Offline, pre-gate (main) | 2575 passed, 1078 deselected | n/a |
| Live, baseline (main, pre-fix) | **7 failed**, 1032 passed, 37 skipped, 2 xfailed | `live` |
| Live, final (main + gate fixes) | **1040 passed, 0 failed**, 37 skipped, 2 xfailed, 5 subtests passed | **`live`** |
| Offline, final (main + gate fixes) | **2575 passed, 0 failed** | n/a |

`tests/live_status.json` shows `"run_mode": "live"` for the final run.
Destructive work ran on `target_sandbox` / `sena3_sandbox` copies; the
live runs rewrote random-GUID probe artifacts under
`specs/262-...`, `specs/299-300-290-...`, and `specs/325-.../evidence/`,
which were restored with `git checkout` afterwards (verified clean).

## Baseline failures (all live-only; offline was green throughout)

1. `test_issue515_get_owning_text_live` -- `NameError:
   IConstChartFactory` in `DiscourseOperations.CreateChart`.
2. `test_issue523_segment_exists_hvo_live` (2 tests) --
   `Texts.Create(name, content)` passes content as `genre` (2nd
   positional is `genre=None`); test bug.
3. `test_issue552_example_duplicate_hvo_live` --
   `LexiconAllEntries().__next__()`; `GetAll()` returns an
   `EnumerableWrapper` (iterable, not iterator). Test bug; Target is
   additionally entry-less, so the entry must be created (#550 pattern).
4. `TestSegmentAnalysesRSWriteMethods` ReplaceAnalysis x3 --
   `token.Hvo` on HVO-less mock fillers; code assumed every element has
   `.Hvo`.

## Read-back evidence for the gate fixes

- **Chart ownership is project-level with a BasedOnRA text link**
  (live probes on `target_sandbox`, thrown away after reading):
  `IText`/`IStText` expose zero `*hart*`/`*iscourse*` members;
  `lp.DiscourseDataOA.ChartsOC` is the container;
  `DsConstChart.BasedOnRA` round-trips an `IStText`
  (`StText : 10443`, `BasedOnRA.Hvo == ContentsOA.Hvo` True,
  `BasedOnRA.Owner.Hvo == text.Hvo` True);
  assigning an `IText` raises `TypeError: ... cannot be converted to
  SIL.LCModel.IStText`;
  owner chain reads `DsConstChart -> DsDiscourseData -> LangProject`;
  `ChartsOC` enumeration yields a limited view with no `BasedOnRA`
  until cast by ClassName (`__CastChartView`).
  Post-fix `test_issue515_get_owning_text_live` (create + HVO/raw
  `GetOwningText` + `GetAllCharts` + HVO `Duplicate` preserving the
  link + HVO `DeleteChart` round-trip): pass, live.
- **`Duplicate` orphan crash**: `_GetTypedOwner(chart)` returned the
  `DsDiscourseData` owner uncast (not in `cast_to_concrete`), so
  `hasattr(parent, "ChartsOC")` was False, the `Add` was skipped, and
  `Name.CopyAlternatives` died with `NullReferenceException` on the
  unowned duplicate. Registering `DsDiscourseData -> IDsDiscourseData`
  plus an explicit raise when the parent has no chart collection:
  duplicate-then-delete round-trip passes, live.
- **`chart_type="discourse"`**: no DsChart factory exists in
  `SIL.LCModel` (enumerated chart factories:
  `IDsConstChartFactory` only, plus row/cell/marker/tag factories), so
  `CreateChart` raises `FP_ParameterError` for anything but
  `"constituent"`.
- **PN9 (name probe)**: `CreateChart` with padded/unpadded names now
  succeeds and both names re-read byte-identical via `ITsString`
  (`TEST_NF_Chart_Raw ` with trailing space preserved); PN7/PN10/PN11
  unchanged and passing.
- **#523 / #552 test corrections**: text-then-paragraph creation and
  created-entry patterns; pass, live.
- **ReplaceAnalysis `getattr(token, "Hvo", None)`**: real-LCM no-op
  (every `AnalysesRS` token has an HVO); the 3 mock-filler tests pass.

**Result: PASS (live).**
