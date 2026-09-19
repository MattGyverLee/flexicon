# Live evidence -- T2.8, checkpoint 2 (#302, #261)

**Task:** T2.8 -- independent live verification of the checkpoint-2 changes.
**Date:** 2026-09-18
**Campaign:** lcm-member-truth-sweep
**Baseline for comparison:** `03d82c6` (current `main` tip; see "Baseline
deviation" below for why not `598f41e`)

**Provenance note.** The dispatched `lex-verification` subagent for this task
terminated mid-run on an account spend limit (HTTP 429, request id
`req_011CfBfhXFd1RmrUNuwMSrvo`, model `claude-sonnet-5`) after completing its
regression runs but *before* writing any deliverable. Rather than leave the
checkpoint unverified, the **main session re-ran the verification itself** and
authored this file. The verification is still independent of the code under
test in the sense that matters -- the probe below was written fresh by the
verifying session, not reused from the fix author's test file -- but it is not
independent of the *orchestrating* session. Weigh it accordingly.

---

## 1. Live test suite

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_datanotebook_duplicate.py tests/operations/test_lcm_member_truth_sweep.py -m requires_live_project -q
```

- `--collect-only` first: **25 tests collected** (not a false-zero pass).
- Result: **25 passed in 22.43s**.
- `python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"`
  -> **`live`**.

## 2. Independent probe (written by the verifying session)

A separate probe file was written, run, and then removed; its source is
preserved at `scratchpad/t28_probe_source.py` for reproduction. It shares no
code with `tests/operations/test_datanotebook_duplicate.py`.

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_t28_independent_probe.py -m requires_live_project -q
```

- Result: **4 passed in 6.17s**, `run_mode` = **`live`**.
- Fixture: `target_sandbox` only (tempdir copy of the Target `.fwbackup`).
  The live Target and live Sena 3 were never opened. `scripts/restore_*.py`
  were never invoked.

### 2a. #302 -- ownership form, pre/post state re-read by HVO

All state below is obtained by **re-querying**
`project.lp.ResearchNotebookOA.RecordsOC` after the operation and comparing
HVO sets. No assertion is made against an in-hand object reference.

| Step | How observed | Result |
|---|---|---|
| Pre-state | re-read `RecordsOC` HVO set | baseline set `S` captured |
| Seed a top-level record | re-read `RecordsOC` | `S u {source_hvo}` -- record present |
| `Duplicate(source_hvo)` | re-read `RecordsOC` | exactly **one** new HVO appended |
| `Delete(dup_hvo)`, `Delete(source_hvo)` | re-read `RecordsOC` | set is back to `S` exactly |

`Delete()`'s top-level `else:` branch and `Duplicate()`'s placement both
operate on `ResearchNotebookOA.RecordsOC`. The repository has no `RecordsOC`
to land in, so a regression here would show up as a zero-delta or a raise, not
as a silent success.

### 2b. #302 -- PARTIAL result on `Duplicate()`, stated plainly

**`Duplicate()` cannot currently run to completion.** A few lines after the
#302 placement it reaches:

```
duplicate.Title.CopyAlternatives(source.Title)     # DataNotebookOperations.py:2541
-> AttributeError: 'ITsString' object has no attribute 'CopyAlternatives'
```

This is the separate, pre-existing, **out-of-scope** defect recorded as T2.4
finding 1 (`IRnGenericRec.Title` is a bare `ITsString`, not an `IMultiString`).
It is not #302 and not #261, and this checkpoint does not fix it.

What that means for the verification, precisely:

- The #302 line **does** execute, and its effect **is** directly observable
  from the LCM (the duplicate is appended to `ResearchNotebookOA.RecordsOC`
  before the crash). That much is verified.
- `Duplicate()` **as a whole method** is NOT verified end-to-end, because it
  still raises. It raised before this checkpoint too, for the same unrelated
  reason -- this is not a regression introduced here.
- The probe pins the crash to that specific defect (`"CopyAlternatives" in
  str(exc)`) and asserts the message contains neither `RecordsOC` nor
  `Insert`, so a genuine #302/#158 placement regression would fail the probe
  rather than hide behind the known crash.

The transaction layer logs `rolling back to mark None ... Changes from this
block are NOT reversed` on that raise. The partially-created duplicate
therefore persists in the sandbox. Harmless here (tempdir copy, discarded),
but worth knowing before anyone runs `Duplicate()` against a real project.

### 2c. #261 -- int-HVO entry path and the removed mask

| Assertion | Result |
|---|---|
| `GetSubRecords(int_hvo)` | returns `[]` -- resolves, does not raise |
| `GetParentRecord(int_hvo)` | returns `None` -- resolves, does not raise |
| `GetLocations(int_hvo)` | returns `[]` -- resolves, does not raise |
| `GetSubRecords(999999999)` | raises `FP_ParameterError` (invalid HVO still reported as such) |
| genuine `AttributeError` raised inside resolution | propagates as `AttributeError`, **not** relabelled `FP_ParameterError` |

The three routed methods are called with a bare Python `int` (`type(hvo) is
int` asserted). Before the fix, all 38 `__GetRecordObject`-routed methods
raised `FP_ParameterError` on this path, because `LcmCache` has no `GetObject`
and `AttributeError` was inside the `except` tuple.

`GetTitle`/`SetTitle`/`GetStatus`/`SetStatus`/`GetRecordType`/`SetDateOfEvent`
were deliberately **not** used as the three witnesses, despite being the
task's suggestion: T2.4 found each independently broken for out-of-scope
reasons (findings 1-3). Using them would have conflated a #261 pass/fail with
those defects.

## 3. Ruling C3 and out-of-scope files

| Check | Result |
|---|---|
| `GetService(IRnResearchNbkRepository)` + `AllInstances()` in the enumerable getter | **present and unmodified** at `:238` (was `:232`) |
| `IRnResearchNbkRepository` import | **survives** at `:22`, as C3 requires |
| `flexicon/code/Lexicon/LexSenseOperations.py:1376,1481,1488` | **untouched** (`git diff --stat` empty) |
| `flexicon/code/Grammar/compound_rule.py` | **untouched** (ruling C9) |

## 4. Working-tree scope

`git status --porcelain` shows only:

```
 M flexicon/code/Notebook/DataNotebookOperations.py
 M specs/lcm-member-truth-sweep/.crew-handoff.json
 M specs/lcm-member-truth-sweep/HANDOFF-main-session.md
 M tests/operations/test_datanotebook_duplicate.py
 M tests/operations/test_lcm_member_truth_sweep.py
?? .claude/ralph-loop.local.md
?? specs/lcm-member-truth-sweep/{catalogue2-siblings,proposed-issues}.md
?? specs/lcm-member-truth-sweep/evidence/live-T2.{1,5}-*.md
?? specs/lcm-member-truth-sweep/reviews/cycle2-*.md
```

No unrelated file was modified. The pre-existing sibling worktree
`D:/Github/_Projects/_LEX/flexicon-283-259-257` belongs to separate work and
was not touched.

## 5. Offline regression

Identical command on both trees: `python -m pytest -m "not requires_live_project" -q`

| Tree | passed | deselected |
|---|---|---|
| baseline `03d82c6` (throwaway worktree) | **1883** | 786 |
| working tree | **1876** | 806 |

**Zero failures on either tree.** The delta is fully accounted for, with no
residue:

- **-7 passed.** The old `tests/operations/test_datanotebook_duplicate.py`
  contributed exactly 7 offline (mock) tests. Ruling C4 deleted it; the
  replacement is entirely `requires_live_project`, so it contributes 0 offline
  tests. `7 - 0 = 7`. No other offline test changed status.
- **+20 deselected**, i.e. 20 new live tests:
  `test_datanotebook_duplicate.py` 0 -> 6 (+6);
  `test_lcm_member_truth_sweep.py` 9 -> 19 (+10, from T2.1's
  `TestPart4NotebookOwnerGate` and T2.5's Part 5/Part 6 classes);
  the temporary T2.8 probe (+4). `6 + 10 + 4 = 20`.

This is a net trade of 7 mock tests that could not fail for 20 live tests that
can -- which is the point of ruling C4.

### Baseline deviation, stated

`tasks.md` names `598f41e` as the campaign baseline. This comparison uses
`03d82c6` (current `main` tip) instead, because three commits have landed
since `598f41e` (including `3725d3e`, an unrelated examples fix that itself
changed test counts). Comparing against `main`'s tip isolates *this
checkpoint's* effect; comparing against `598f41e` would fold in three
unrelated commits and make the 7/20 accounting above impossible to close.

## 6. Verdict

**PASS**, with one scope limitation recorded above and not papered over:

- #302 -- the three `RecordsOC` sites are verified live against
  `ResearchNotebookOA.RecordsOC` with HVO re-reads. `Create()` and
  `Duplicate()` cannot be exercised end-to-end because of the separate
  out-of-scope `Title`/`Text` defect; the #302 line within each is verified by
  its observable effect on the collection.
- #261 -- the int-HVO entry path is verified live across three routed methods,
  the invalid-HVO error is preserved, and the `AttributeError` mask is
  confirmed removed.
- C3, C9 and the `LexSenseOperations` carve-out are all confirmed intact.
- Offline: 1876 passed, 0 failed, delta fully explained.

PASS
