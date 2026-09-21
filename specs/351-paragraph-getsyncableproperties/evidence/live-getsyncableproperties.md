# Live verification -- issue #351 (ParagraphOperations.GetSyncableProperties)

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue351_paragraph_sync_props_live.py -m requires_live_project -q
```

Result: `2 passed in 2.18s`

## run_mode

`tests/live_status.json` reports `"run_mode": "live"` (run_timestamp
2026-09-21T06:43:01Z). Both tests are recorded as `pass`, phase `read`,
operations class `ParagraphOperations`:

- `test_get_syncable_properties_on_real_paragraph`
- `test_no_paragraph_in_text_raises`

## Pre-state (the bug being fixed)

Issue #351, measured 2026-09-20 on `Ejagham Mini` (read-only),
`FLEXLIBS_REQUIRE_LIVE=1`: **205 of 205** `StTxtPara` objects raised

```
AttributeError: 'ITsString' object has no attribute 'get_WritingSystemAt'
```

at `ParagraphOperations.GetSyncableProperties`, because
`IStTxtPara.Contents` is a bare `ITsString` with no
`get_WritingSystemAt` accessor -- and the `Length > 0` guard guaranteed a
non-empty paragraph hit the broken call while an empty paragraph skipped
it (the inverse of the desired behaviour).

## Post-state (read back from the LCM)

Ran against a fresh tempdir copy of the Target `.fwbackup`
(`target_sandbox`), opened write-enabled. A `TEST_issue351_*` text was
created, paragraph content written through `Paragraphs.Create`, then the
paragraph re-read.

Live test 1 (`test_get_syncable_properties_on_real_paragraph`):

- written content: `TEST_issue351 paragraph with content.`
- default vernacular WS handle resolved from the LCM: `project.project.DefaultVernWs`
- default vernacular WS Id resolved from `WritingSystemOperations.GetAll()`
- paragraph text re-read from the LCM via `Paragraphs.GetText(para)` (reference value)
- `Paragraphs.GetSyncableProperties(para)` returned, **without raising**:
  `{"Contents": {<default_vern_ws_id>: <re-read paragraph text>}}`
  with `Contents[ws_id] == "TEST_issue351 paragraph with content."`

Live test 2 (`test_no_paragraph_in_text_raises`): created 3 non-empty
paragraphs in a `TEST_issue351_*` text and called
`GetSyncableProperties` on all 3. No `AttributeError`; each returned a
non-empty `Contents` dict whose values matched `Paragraphs.GetText` for
the same paragraph.

## Pass / Fail

**PASS.** The previously-raising call path
(`Contents.get_Properties(0).GetIntPropValues(1, 0)[0]` on a live
`IStTxtPara.Contents`) returns the paragraph text keyed by the real
vernacular writing-system Id for every non-empty paragraph exercised.

## Mock companion

`tests/operations/test_paragraph_sync_props.py` (8 tests, offline tier --
`python -m pytest -m "not requires_live_project"`): locks the new call
shape and asserts `get_WritingSystemAt` is never called again.