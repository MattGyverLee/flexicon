# Live verification evidence -- issue #267

`ExampleOperations.ApplySyncableProperties`'s `TranslationsOC` loop:
route the target writing-system lookup through the shared
`BaseOperations._resolve_ws_handle` helper without orphaning a zero-alt
`ICmTranslation` when resolution raises, and log the pre-existing silent
miss (matching `BaseOperations._apply_props_loop`'s own Defect 3 fix,
requested by the coordinator mid-task).

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue267_translations_live.py -m requires_live_project -q
```

(Bash-tool equivalent used in this environment: `export
FLEXLIBS_REQUIRE_LIVE=1 && python -m pytest
tests/operations/test_issue267_translations_live.py -m
requires_live_project -q` -- same variable, same effect.)

## `run_mode`

`tests/live_status.json` -> `"run_mode": "live"` for both runs below (the
unfixed/red run and the fixed/green run). Confirmed by inspecting the
file immediately after each run; reproduced here from the green run:

```json
"run_mode": "live",
"by_class": {
  "ExampleOperations": {
    "modify": {
      "status": "pass",
      "tests": [
        "tests/operations/test_issue267_translations_live.py::TestTranslationsOCWsCaseDivergenceLive::test_case_divergent_translation_alt_resolves_and_saves",
        "tests/operations/test_issue267_translations_live.py::TestTranslationsOCWsCaseDivergenceLive::test_exact_match_still_saves_unchanged",
        "tests/operations/test_issue267_translations_live.py::TestTranslationsOCWsCaseDivergenceLive::test_genuine_miss_still_skips_but_now_logs_a_warning"
      ]
    }
  }
}
```

## Project

`target_sandbox` (fresh tempdir copy of `tests/fixtures/Target 2026-07-06
0218.fwbackup`), `undoable=False`, per the task's fixture requirement.
Every created object is prefixed `TEST_267_` and deleted in the fixture's
`finally:` block (`project.LexEntry.Delete(entry)`, which cascades the
owned sense/example/translations).

Live WS inventory (identical to #266's own disclosure): `en` (analysis,
handle 999000001), `etu` (vernacular, handle 999000002). Neither contains
`-` or `_`.

## Red run (unfixed code, byte-verified against HEAD)

```
git hash-object flexicon/code/Lexicon/ExampleOperations.py
c503aa3bbf12285b6278a44949d9c0d856fb12f3
git rev-parse HEAD:flexicon/code/Lexicon/ExampleOperations.py
c503aa3bbf12285b6278a44949d9c0d856fb12f3
```
Identical hashes confirm the file under test was byte-for-byte the
committed pre-#267 state (the working tree's other in-flight changes
were restored to HEAD for `ExampleOperations.py` only, via a scratch
backup/restore, never `git checkout`/`stash`/`clean` on the shared tree).

Result:
```
2 failed, 1 passed in 6.19s
```
- `test_case_divergent_translation_alt_resolves_and_saves` -- FAILED.
  Source spelled `EN` (the target's real analysis ws.Id is `en`); the
  saved text read back `None` instead of `TEST_267_trans_case` -- the
  alt was silently dropped, reproducing the issue exactly.
- `test_genuine_miss_still_skips_but_now_logs_a_warning` -- FAILED. No
  warning naming `de-DE` was logged (the pre-fix code has no warning
  call on this path at all).
- `test_exact_match_still_saves_unchanged` -- PASSED (zero-regression
  control; exact-case spellings always worked, before and after).

## Green run (fixed code)

```
git hash-object flexicon/code/Lexicon/ExampleOperations.py
17c82a2c7654aaf14efdf85326493c8c1a23271d
```
(the working-tree file as left by this task, including both the
pre-resolve-before-attach restructure and the added miss-case warning).

Result:
```
3 passed in 5.57s
```
(second confirmation run after restoring the fixed blob post-red-run:
`3 passed in 5.61s`, same outcome.)

- `test_case_divergent_translation_alt_resolves_and_saves` -- PASSED.
  Source `EN` resolves to handle 999000001 (`en`) via
  `_resolve_ws_handle`'s normalized fallback; re-fetched
  `ICmTranslation.Translation.get_String(999000001).Text ==
  "TEST_267_trans_case"`.
- `test_exact_match_still_saves_unchanged` -- PASSED (unchanged).
- `test_genuine_miss_still_skips_but_now_logs_a_warning` -- PASSED. The
  `de-DE` alt is still absent from the saved translation (Defect 3,
  unchanged), but `caplog` now captures a warning naming both `de-DE` and
  `ICmTranslation.Translation`.

Live-observed warning line for the miss case (captured during the
initial exploratory run against the fixed code, same message shape the
green pytest run asserts on):

```
WARNING flexicon.code.Lexicon.ExampleOperations:ExampleOperations.py:594
ApplySyncableProperties: dropping ICmTranslation.Translation alt for
writing system 'de-DE' (resolved target id 'de-DE') on
ILexExampleSentence Hvo=10445 -- target project has no such writing
system, active or in its LDML store. Call
WritingSystemOperations.Ensure(tgt_ws_id, ...) first to activate or
create it if this text should be kept.
```

## Pre/post state, re-read from the LCM after re-fetching the object

For the case-divergent scenario (green run):
- Pre-state: `_refetch_example(project, hvo).TranslationsOC.Count == 0`
  (asserted before `ApplySyncableProperties` is called).
- Post-state: a **fresh** `_refetch_example(project, hvo)` (new
  `project.Object(hvo)` call, not the pre-write reference) shows
  `TranslationsOC.Count == 1` and
  `TranslationsOC[0].Translation.get_String(999000001).Text ==
  "TEST_267_trans_case"`.

## C-D4-6 carryover: writing-system store never widened

Every test in the file calls `_assert_ws_store_unchanged`, which
re-reads `WritingSystems.GetAll()` count, `lp.CurVernWss`, and
`lp.CurAnalysisWss` after the write and asserts byte/count identity with
the pre-run baseline. All three tests passed this assertion in the green
run.

## The orphan-prevention mechanism itself: live vs offline split

This live suite proves the **positive** path (a case-divergent alt now
resolves and saves) and the **miss** path (a genuine absence still skips,
now with a warning) against a real LCM project. It does **not** attempt
to construct a live ambiguity raise: `target_sandbox`'s only two active
writing systems (`en`, `etu`) cannot be coaxed into two DISTINCT active
writing systems that normalize to the same form -- BCP-47 tags are
case-normalized by FieldWorks on creation, so there is no supported way
to stand up a second active WS whose Id differs from `en` only by case.
This is the same disclosed limitation #266 already stated for separator
divergence; extended here to cover the ambiguity/orphan-prevention
mechanics specifically.

**The orphan regression test itself (`ICmTranslationFactory.Create` is
never called before an ambiguous spelling raises) is therefore proven
OFFLINE ONLY**, in
`tests/operations/test_issue267_translations_ws_resolution.py::TestApplyTranslationsOCOrphanRegression`.
That file's own red/green proof (documented in
`specs/250-writingsystem-activation/reviews/issue267-implementation.md`)
additionally red/green-tests against a **naive one-line substitution**
(not just the fully-unfixed baseline) to confirm the orphan test
specifically catches the shape issue #267 warns about, not merely "any
bug in this loop."

## Verdict

**PASS: live-verified.** Both sides measured (red against a
byte-verified pre-fix blob, green against the fixed blob), `run_mode`
confirmed `"live"`, post-state re-read from a freshly re-fetched LCM
object, C-D4-6 store-unchanged assertions held. The one disclosed gap
(ambiguity/orphan-prevention proven offline only, not live) matches the
pre-existing, already-documented limitation of `target_sandbox`'s WS
inventory and is not a new limitation introduced by this task.
