# HANDOFF -- follow-ups from the 24h live re-verification (PRs #354-#389)

**Date:** 2026-09-23
**Source:** main-session re-run of every live FLEx verification cited by the
26 PRs merged 2026-09-22/23. Full per-PR results:
`specs/issue-289-headless-progress/evidence/live-import-regression.md`.

## TL;DR for the next session

17 of 18 runnable live groups pass (`run_mode: live`). This file lists what
is still open: 2 PRs merged with no live test, 1 live FAIL needing a
sync-contract decision, 1 newly found setter bug, 13 offline tests red on
`main`, and 1 stale evidence citation.

**Read first -- working-tree state.** When this was written, these fixes were
on the `main` working tree, **uncommitted**:

- `flexicon/code/headless_ui.py` -- `import flexicon` was broken on `main` by
  #375 (pythonnet cannot implement `IProgress.Canceling`); the fix compiles a
  C# `HeadlessThreadedProgress` in memory
- `flexicon/code/Lists/OverlayOperations.py` -- `GetName(hvo)` got an uncast
  `ICmObject`
- `flexicon/code/Grammar/NaturalClassOperations.py` -- same failure shape in
  the type-mismatch guard
- `tests/test_headless_threaded_progress.py`,
  `tests/operations/test_352_annodef_live.py`,
  `tests/operations/test_issue340_natural_class_kind_discoverability.py`

Run `git status` first. If those edits have not landed, nothing below can
be reproduced, because `import flexicon` fails.

Required invocations for every item (CLAUDE.md, "Live LCM Verification"):

```
python -m pytest -m "not requires_live_project" -q
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest <your live test file> -m requires_live_project -q
```

Never run bare `pytest`.

---

## 1. #369 -- `TextOperations` media `file_guid` is always None (live FAIL)

**Status:** FAIL, needs a human decision. Suggested label: **P2**.

**Evidence (live reflection, 2026-09-23):** the public properties on
`ICmMediaURI` are `MediaURI`, `OwnOrd`, `OwnedObjects`, the sort keys, and
`ChooserNameTS`/`DeletionTextTSS`. **There is no `MediaFileRA`.** An
`ICmMediaURI` is linked to its file only through the `MediaURI` path string.

**Consequences:**

- `AddMediaFile` runs `media_uri.MediaFileRA = cm_file`. That sets a Python
  attribute on the wrapper and never reaches the LCM.
- `GetSyncableProperties` reads `getattr(uri_obj, "MediaFileRA", None)`, which
  is always None, so every `media_uris[i]["file_guid"]` is None.
- `tests/operations/test_issue356_text_media_helpers.py::...::test_add_media_file_roundtrip_via_get_media_files`
  asserts a non-None `file_guid` and fails live.

This is the #36/#39/#40 phantom-member class (CLAUDE.md, "Same-name fields").

**Decision needed (sync contract):**

- (a) Drop `file_guid` from the `media_uris` payload and remove the phantom
  assignment. This is honest and smallest, but a breaking change for sync
  consumers.
- (b) Derive `file_guid` by resolving the `ICmFile` whose internal or absolute
  path matches `MediaURI`. This keeps the contract, but a path match can fail
  or be ambiguous, and the apply side would need the reverse resolution.

**Done when:** the decision is recorded in `specs/issue-356-text-media-helpers/`,
the phantom `MediaFileRA` write is gone either way, the test asserts the
chosen contract, `docs/API_ISSUES_CATEGORIZED.md` Category 8 lists
`ICmMediaURI.MediaFileRA` as nonexistent, and the live run passes.

## 2. `AnnotationDefOperations.GetMultiple` / `SetMultiple` use a phantom member (new)

**Status:** not fixed, no issue filed yet. Suggested label: **P2** (a silent
no-op setter with a wrong-value getter; the calibration match is #329).

**Evidence (live, `target_sandbox`, 2026-09-23):**

| Step | LCM `ICmAnnotationDefn.Multi` | `GetMultiple()` |
|---|---|---|
| fresh `Create(...)` | `False` | `True` |
| after `SetMultiple(d, True)` | `False` (no-op) | `True` |
| after raw `Multi = True` | `True` | `True` |

Reflection shows `Multi` exists and `AllowsMultiple` does not. #361 (PR #374)
moved `GetSyncableProperties` to `Multi` but left behind these sites, all in
`flexicon/code/System/AnnotationDefOperations.py`:

- `GetMultiple` (~l.740): `hasattr(anno_def, "AllowsMultiple")` is always
  False, so it falls through to `return True`
- `SetMultiple` (~l.783): the guard is always False, so the setter never writes
- `Duplicate` (~l.1149) and the copy block (~l.1177): copy a phantom, so the
  flag is never duplicated

**Fix shape:** cast to `ICmAnnotationDefn`, then read and write `Multi`. Run
the `sweep-pattern` skill over the file first; #361 already found three
phantoms here (`InstanceOf`, `AllowsMultiple`, `AnnotationType`).

**Done when:** a live test in `target_sandbox` shows the value read back from
LCM tracking `SetMultiple` both ways, and `Duplicate` preserves `Multi`.
Evidence goes in `specs/<feature>/evidence/live-<task>.md`.

## 3. PRs merged with no live test at all

Both PRs record "FAIL: unverified" (cloud agent, no FieldWorks). No
`requires_live_project` test exists for either change.

### 3a. #376 -- `DataNotebookOperations.SetDateOfEvent` GenDate (issue #330)

The PR claims `IRnGenericRec.DateOfEvent` is `GenDate`, so the old
`DateTime` assignment raised `TypeError` on every call, and the fix assigns
a string. That is a write-path change with no live proof.

**Needed:** a live test in `target_sandbox` that:

1. creates a `TEST_` notebook record
2. calls `SetDateOfEvent` with a `datetime` and with a string
3. re-reads `DateOfEvent` from the LCM (re-query the record by GUID)
4. asserts on the GenDate components, not on the value passed in

The offline tests in `tests/operations/test_issue330_setdateofevent_gendate.py`
are also red (see section 4).

### 3b. #389 -- `CompoundRule` contexts for `IMoEndoCompound` / `IMoExoCompound` (issue #327)

This is a read path: `left_context` / `right_context` / `contexts` were always
None because they probed phantom `LeftContextOA`/`RightContextOA`.

**Needed:** a live read test against a project that has compound rules (Sena
3 or `sena3_sandbox`; check which one has endo and exo compounds). It should
assert the wrapper returns the same objects as the raw LCM members the PR
identified, for both compound types.

## 4. 13 offline tests red on `main`

All 13 fail identically on `HEAD ec35efa` + the `headless_ui.py` import fix
alone, so none are caused by the uncommitted fixes. (Plain `HEAD` cannot be
tested because `import flexicon` fails there.)

| # | Test | Failure | Likely source |
|---|---|---|---|
| 1 | `tests/contract/test_lcm_contract.py::TestContractStability::test_no_new_type_dependencies` | new deps: `ICmDomainQ`, `ICmDomainQFactory`, `ICmOverlayFactory`, `IMoInflAffixSlotFactory`, `IThreadedProgress` (+ `ICmOverlay` from the uncommitted Overlay fix) | 198f082 (semdom), 0d04f40 (#303), bd11a87 (#255), #375 |
| 2 | `.../test_lcm_contract.py::TestLiveRegressionCheck::test_no_regressions_from_baseline` | removed: `ICmMedia`, `ICmMediaFactory`, `IRnResearchNbkRepository`, `IWfiGlossRepository` | 07778bf (#356), 18dc9b4 (#352), e40dc5c (#363) |
| 3 | `tests/write_path_transactions/test_unbracketed_mutations.py::...::test_no_new_unbracketed_mutations` | 4 new unbracketed mutators: `BaseOperations._DefaultExcludeFromAllPublications` (l.3210), `DataNotebookOperations._SetRecordContent` (l.224), `_CopyRecordContent` (l.248), `NoteOperations.SetAuthor` (l.829) | a7e8286, 18dc9b4; the `SetAuthor` entry may be a line-shift of an existing baseline entry, so check before wrapping |
| 4 | `tests/operations/test_issue324_clause_markers_cellsos.py::...Offline::test_create_adds_to_cellsos_not_clausemarkersos` | `FP_ParameterError: word_group must be an IConstChartWordGroup object`: the fake word group fails the new type guard | #371 (test double out of date) |
| 5-6 | `tests/operations/test_issue330_setdateofevent_gendate.py` (2 tests) | `'DataNotebookOperations' object has no attribute 'project'`: the test builds ops via `__new__` and never sets `project` | #376 (test bug) |
| 7 | `tests/operations/test_issue334_guid_parse_formatexception.py::...::test_malformed_guid_preserves_clr_exception_as_cause[]` | `assert None is not None` (no `__cause__` on the empty-string case) | #373 (confirmed): `__CreateValueWithGuid` now raises `FP_ParameterError` on `guid_str == ""` before any CLR parse, so there is no `__cause__`. The test's `MALFORMED_GUIDS_TRUTHY` (l.56) still lists `""`, which is misnamed since `""` is falsy. Move `""` to its own case asserting the #336 message |
| 8 | `tests/test_264_sldr_single_init_path.py::...::test_every_live_project_test_carries_the_marker` | flags `tests/test_headless_threaded_progress.py` (touches FLEx, has no `requires_live_project` marker) | #375 |
| 9 | `tests/test_297_init_stub_parity.py::...::test_every_runtime_public_name_is_in_stub_all` | `HeadlessThreadedProgress` exported but missing from `flexicon/__init__.pyi` `__all__` | #375 |
| 10 | `tests/test_docstring_example_ratchet.py::...::test_no_new_broken_examples` | internal-leak `FLExProject.Overlays` (FLExProject.py ~l.3043) | 66d9ef6 (#309) |
| 11 | `tests/test_transaction_honesty.py::TestOneShotWarningAtOpenProject::test_openproject_source_contains_single_warning_call_for_no_rollback_mode` | `ValueError: substring not found`: the source-text ratchet no longer finds its anchor in `OpenProject` | #375 rewrote the `OpenProject` progress/docstring area; confirm with blame |
| 12 | `tests/operations/test_issue266_phoneme_ws_resolution.py::TestApplyBasicIPASymbolSharedIndexCache::test_fresh_index_cache_per_apply_call` | `_index_cache` built once, not per call (`1 == 2`) | not attributed (test last touched 2026-09-10); bisect |
| 13 | `tests/operations/test_issue267_translations_ws_resolution.py::TestTranslationsOCSharedIndexCache::test_fresh_index_cache_per_apply_call` | `_ws_resolve_cache` built once, not per call (`1 == 2`) | same as 12, probably one cause |

Rows 1-3 are ratchets. Where a new dependency or unbracketed site is
intentional, update the baseline in the same commit and say so; do not
regenerate baselines wholesale. Rows 12-13 are possible real defects (a
cache leaking across apply calls) and should be bisected before anyone
touches the tests.

**Done when:** `python -m pytest -m "not requires_live_project" -q` is fully
green on `main`.

## 5. #355 -- evidence cites a test file that was never committed

`specs/326-phonological-wrapper-members/evidence/live-T8.md` gives
`tests/operations/test_issue326_t8_verification_live.py` as its live command,
but the file is not in the repo and never was. `reviews/T11-archivist.md:55`
and `reviews/T8-verification.md:25,55` record it as "evidence-only T8
scratch; intentionally not committed".

So this is not a missing test: the evidence file cannot be re-run as
written. The other live file cited there,
`tests/operations/test_phonological_wrappers_live.py`, passes live (3/3).

**Next step:** add a note to `live-T8.md` saying the T8 scratch file was
intentionally not committed and naming the committed file that re-verifies
the change. Or, if T8's assertions are not covered there, commit them as a
proper `requires_live_project` test.

---

## Related context (not action items)

- **Sena 3 was restored on 2026-09-23.** The live `Sena 3.fwdata` and
  `Sena 3.bak` had been zero-filled (mtime 2026-09-20 14:37-14:38). Per the
  flextoolsmcp-40 session, that lines up with an unclean reboot (Kernel-Power
  41 at 14:38:45). It was restored with `scripts/restore_sena3.py` from
  `tests/fixtures/Sena 3 2026-06-09 1645.fwbackup`, which also enables
  `sena3_sandbox`.
- **Priority labels:** every bug issue filed from this list needs exactly one
  P0-P3 label at creation. Use `gh ... --repo MattGyverLee/flexicon`, and
  avoid `close`/`fix`/`resolve` + `#N` in prose (see CLAUDE.md, "Git
  Conventions").
