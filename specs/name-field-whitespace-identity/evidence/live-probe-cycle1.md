# Name-field whitespace identity -- live probe, cycle 1

READ-ONLY-TO-PRODUCTION probe. Zero lines under `flexicon/` are changed by
this task. `git diff --stat -- flexicon/` is proven empty both before and
after the live run (see the "git diff proof" section at the bottom -- that
section is filled in AFTER the run; this predictions section is committed
BEFORE any live measurement, per the C28 forward rule, so git history alone
proves the order).

Test file: `tests/operations/test_name_field_identity_probe.py` (NEW file;
does not extend `tests/operations/test_issue242_whitespace_probe.py` --
different feature, different fixtures).

Fixtures used: `target_sandbox` / `target_sandbox_path` ONLY. Never the real
Target project, never `scripts/restore_*.py`.

## Sites confirmed at HEAD (line numbers re-verified against this commit,
not copied blindly from the background brief -- they matched exactly)

| Site | File:line | Strip line | Needle key | Haystack key |
|---|---|---|---|---|
| `TextOperations.Exists` | `flexicon/code/TextsWords/TextOperations.py` | `:458` | `:461` | `:464` |
| `AnthropologyOperations.Exists` (calls `Find`) | `flexicon/code/Notebook/AnthropologyOperations.py` | `:507` (`Exists`) | -- | -- |
| `AnthropologyOperations.Find` | `flexicon/code/Notebook/AnthropologyOperations.py` | `:558` | `:562` | `:565` |
| `CheckOperations.FindCheckType` | `flexicon/code/System/CheckOperations.py` | `:341` | `:344` | `:350` |
| `CheckOperations.CreateCheckType` (Q-242B site) | `flexicon/code/System/CheckOperations.py` | `:196` | -- | -- |
| `CheckOperations.SetName` (Q-242B site) | `flexicon/code/System/CheckOperations.py` | `:432` | -- | -- |
| `TextOperations.Create` (bare `.strip()` after `_ValidateStringNotEmpty`, type-checked) | `flexicon/code/TextsWords/TextOperations.py` | `:151-152` | -- | -- |
| `TextOperations.SetName` (bare `.strip()` after `_ValidateParam`, None-only) | `flexicon/code/TextsWords/TextOperations.py` | `:606-608` | -- | -- |
| `AnthropologyOperations.Create` (bare `.strip()` after `_ValidateParam`, None-only) | `flexicon/code/Notebook/AnthropologyOperations.py` | `:263-266` | -- | -- |
| `DiscourseOperations.CreateChart` (type-checked via `_ValidateStringNotEmpty`) | `flexicon/code/TextsWords/DiscourseOperations.py` | `:320,327` | -- | -- |
| `BaseOperations._ValidateStringNotEmpty` (type-checks, raises `TypeError`) | `flexicon/code/BaseOperations.py` | `:2491,2537-2538` | -- | -- |
| `BaseOperations._ValidateParam` (None-only, no type check) | `flexicon/code/BaseOperations.py` | `:2323,2376-2377` | -- | -- |
| `Shared/string_utils.normalize_match_key` (no strip anywhere in it) | `flexicon/code/Shared/string_utils.py` | `:50-83` | -- | -- |

All line numbers re-verified by direct `Read` of each file at this commit's
HEAD before this file was written. They match the background brief exactly
(no drift measured this cycle).

## PREDICTIONS (committed BEFORE the live measuring command runs; git
history proves the order -- do not edit this section after measurement,
even if a prediction misses)

- **PN1 (control):** `Texts.Create("TEST_NF_Gen")`; then
  `Texts.Exists("TEST_NF_Gen ")` (trailing space on the needle) ->
  **PREDICTED True** -- `Exists()` strips its own `name` argument (the
  needle) at `:458` before building the match key, so the padded needle
  should still find the unpadded stored name.

- **PN2 (CORE):** create a text, then set its `Name` DIRECTLY via
  `TsStringUtils.MakeString` to `"TEST_NF_Raw "` (layer B, bypassing
  `Texts.SetName`/`Create`'s own strip -- this simulates the POST-FIX
  stored state, where a name-field writer no longer strips before
  persisting). Then:
  - `Texts.Exists("TEST_NF_Raw")` -> **PREDICTED False**
  - `Texts.Exists("TEST_NF_Raw ")` -> **PREDICTED False**
  Both predicted False because the needle is stripped either way (to
  `"TEST_NF_Raw"`) but the haystack (the raw stored name, `"TEST_NF_Raw "`
  with its trailing space) is never stripped by `Exists()` -- `:461` builds
  the needle key from the (now-stripped) `name` parameter, `:464` builds
  the haystack key from `text.Name` as literally stored, with no `.strip()`
  anywhere in that line or in `normalize_match_key`.

- **PN3:** same layer-B shape for `Anthropology.Find`/`Exists` ->
  **PREDICTED None** (`Find`) / **PREDICTED False** (`Exists`) for both the
  unpadded and padded needle, for the identical reason as PN2 (`Find`'s
  needle-strip at `:558`, haystack built raw at `:565`).

- **PN4:** same layer-B shape for `Checks.FindCheckType` -> **PREDICTED
  None** for both the unpadded and padded needle (needle-strip at `:341`,
  haystack built raw at `:350`).

- **PN5 (Q-242B):** `Checks.CreateCheckType(<a plain non-str object>)` ->
  **PREDICTED NO exception**, and a check type is created whose `Name`
  re-reads from the LCM as empty (`""`) or the `"***"` null marker (both
  read via `GetName()` AND via the raw `ITsString(...).Text` accessor,
  re-querying the object fresh from the LCM after the write -- asserting on
  what was passed in proves nothing). Rationale: `:196`'s
  `name = name.strip() if isinstance(name, str) else ""` converts any
  non-str payload to a literal empty string with NO exception, because the
  preceding `_ValidateParam(name, "name")` at `:194` only checks for
  `None` (confirmed at `BaseOperations.py:2376-2377`), not type.

- **PN6 (Q-242B second path):** `Checks.CreateCheckType("   ")`
  (whitespace-only STRING, not a non-str object) -> **PREDICTED NO
  exception**, empty name persisted. Rationale: `"   ".strip()` at `:196`
  yields `""`, and `_ValidateParam("", "name")` at `:197` does not reject
  empty string (only `None`), so the whitespace-only string silently
  becomes a persisted empty name exactly like the non-str case in PN5, via
  a different code path through the SAME line.

- **PN7 (the three-way split):** a plain non-str payload (an object with no
  `.strip()` method and no special `__str__`) passed as the name argument
  to:
  - `Texts.Create` -> **PREDICTED TypeError** (calls
    `BaseOperations._ValidateStringNotEmpty` at `TextOperations.py:151`,
    which type-checks and raises `TypeError` at `BaseOperations.py:2537-2538`
    BEFORE any `.strip()` is reached).
  - `Discourse.CreateChart` -> **PREDICTED TypeError** (same
    `_ValidateStringNotEmpty` call at `DiscourseOperations.py:320`).
  - `Anthropology.Create` -> **PREDICTED AttributeError** (bare
    `name.strip()` at `AnthropologyOperations.py:265` after a None-only
    `_ValidateParam` at `:263` -- the non-str payload has no `.strip()`
    attribute).
  - `Texts.SetName` -> **PREDICTED AttributeError** (bare `name.strip()`
    at `TextOperations.py:608` after a None-only `_ValidateParam` at
    `:606`, identical shape to `Anthropology.Create`).

- **PN8 (THE duplicate-explosion proof):** layer-B store a text named
  `"TEST_NF_Dup "` (trailing space, via direct `MakeString`, bypassing
  `Texts.Create`'s own strip), then call
  `Texts.Create("TEST_NF_Dup ")` through the PUBLIC API -> **PREDICTED it
  SUCCEEDS** (no `FP_ParameterError` raised for "already exists"), because
  `Create()`'s own duplicate check at `:155` calls `self.Exists(name)`
  where `name` has ALREADY been stripped to `"TEST_NF_Dup"` at `:152` --
  and per PN2's mechanism, `Exists("TEST_NF_Dup")` against the raw,
  unstripped haystack `"TEST_NF_Dup "` returns False (mismatch), so the
  duplicate guard never fires. Net effect: TWO separate `IText` objects
  end up in the project, both discoverable by a human as "the text named
  TEST_NF_Dup" despite one call site explicitly checking for that exact
  collision first. **Flagged nuance, stated explicitly now, before
  measuring:** because `Create()` persists `name` AFTER its own strip
  (`:152`, then `:170-171` uses that already-stripped local, not the
  original argument), the SECOND text's stored `Name` is predicted to be
  the STRIPPED string `"TEST_NF_Dup"` (no trailing space) -- NOT
  byte-identical to the first (bypass-created) text's stored
  `"TEST_NF_Dup "` (with trailing space). The core, binding claim is
  "Create SUCCEEDS despite a pre-existing collision, yielding two text
  objects a user would call by the same name" -- that is what is measured
  as MATCH/MISS below. The sub-detail of whether the two stored `Name`
  strings are byte-identical is measured and reported separately, plainly,
  without being smoothed into the headline verdict either way.

## REFUTATION CLAUSE (binds this cycle)

If PN2, PN4, or PN8 measures OPPOSITE to its prediction (i.e., the needle
DOES find the padded haystack in PN2/PN4, or `Create()` in PN8 actually
raises `FP_ParameterError` and refuses the second text), the ruling's
premise -- that these dedup paths strip the needle only, never the haystack
-- is REFUTED. This must be reported plainly, as a refutation, and NOT
reconciled, smoothed over, or treated as a reason to keep measuring. A
refuted premise is a successful cycle.

## Commands (run in this exact order; live run is AFTER this file's
predictions section above was committed)

```
python -m pytest tests/operations/test_name_field_identity_probe.py --collect-only -q -m requires_live_project

python -m pytest tests -m "not requires_live_project" -q

$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_name_field_identity_probe.py -m requires_live_project -q -s
```

## RESULTS (filled in AFTER the live run; predictions above are unedited)

### Collect-only count

```
$ python -m pytest tests/operations/test_name_field_identity_probe.py --collect-only -q -m requires_live_project
tests/operations/test_name_field_identity_probe.py::test_pn1_control_padded_needle_finds_unpadded_public_api_name
tests/operations/test_name_field_identity_probe.py::test_pn2_core_texts_haystack_never_stripped
tests/operations/test_name_field_identity_probe.py::test_pn3_anthropology_haystack_never_stripped
tests/operations/test_name_field_identity_probe.py::test_pn4_checks_haystack_never_stripped
tests/operations/test_name_field_identity_probe.py::test_pn5_q242b_nonstr_payload_persists_empty_name
tests/operations/test_name_field_identity_probe.py::test_pn6_q242b_whitespace_string_persists_empty_name
tests/operations/test_name_field_identity_probe.py::test_pn7_three_way_split_nonstr_payload
tests/operations/test_name_field_identity_probe.py::test_pn8_duplicate_explosion_via_unstripped_haystack

8 tests collected in 0.20s
```
8 collected, non-zero.

### Offline baseline (unmarked suite)

```
$ python -m pytest tests -m "not requires_live_project" -q
1292 passed, 491 deselected, 17 warnings in 10.47s
```
`1292 passed` unchanged from the documented baseline (1292 as of `ed428f7`).
Deselected rose `483 -> 491`, exactly `+8` for the 8 new
`requires_live_project` tests added by this file -- they landed in
deselected, not passed, as required.

### Live run

```
$ $env:FLEXLIBS_REQUIRE_LIVE = "1"
$ python -m pytest tests/operations/test_name_field_identity_probe.py -m requires_live_project -q -s
8 passed, 37 warnings in 6.76s
```
`tests/live_status.json` -> `"run_mode": "live"` (confirmed, NOT `"mock"`),
`"run_timestamp": "2026-09-07T19:14:13Z"`. All 8 of this file's tests
appear under `by_test` with `"status": "pass"`.

**First live attempt failed 3 of 8** (`test_pn4`, `test_pn5`, `test_pn6`),
all with `AttributeError: 'ILcmServiceLocator' object has no attribute
'GetInstance'`. This is an UNPLANNED discovery, documented in full below,
worked around at the test-instance level (see
`_seed_valid_check_list()` in the test file) with zero lines changed under
`flexicon/`. The second run (reported above) is the one whose results are
tabulated below.

### UNPLANNED DISCOVERY: `CheckOperations.CreateCheckType` is completely
non-functional against a live LCM, for an unrelated reason

`CheckOperations._GetCheckList()` (`flexicon/code/System/CheckOperations.py:1168-1179`)
is a **hardcoded stub** that unconditionally `return None`s, regardless of
project state -- it never queries the LCM at all. This forces
`_GetOrCreateCheckList()` (`:1181-1205`) down its "create a new list"
branch on **every single call**, which itself calls
`self.project.project.ServiceLocator.GetInstance(ICmPossibilityListFactory)`
at `:1198`. `ILcmServiceLocator` has no `GetInstance` method -- every
other call site in this same file (`:209`, `:1391`, `:1430`) and every
other Operations class in this codebase uses `.GetService(...)`. Grepped
and confirmed: `:1198` is the ONLY `.GetInstance(` call in the file.

**Effect:** `CreateCheckType()` raises `AttributeError` on **every** call,
for **every** payload, str or not. This appears to have never worked
against a live LCM. This is orthogonal to the name-field whitespace/
identity question this probe exists to answer, but it blocked reaching
`FindCheckType`/`CreateCheckType`'s own name-handling logic (the actual
sites under study for PN4/PN5/PN6) through the public API entirely.

**Workaround used (test-instance only, zero `flexicon/` lines touched):**
`_seed_valid_check_list()` in the new test file pre-builds a real, valid
`ICmPossibilityList` via the CORRECT `.GetService(...)` call, then
monkeypatches ONE function-scoped `target_sandbox` fixture instance's
`project.Checks._GetCheckList = lambda: check_list`. This makes
`_GetOrCreateCheckList`'s `if check_list: return check_list` branch fire,
so the broken `GetInstance` line is never reached, and `CreateCheckType`
proceeds to its own name-handling logic at `:192-229` -- which is what
PN4/PN5/PN6 actually measure. This is a plain Python attribute assignment
on one test's fixture instance, gone at teardown; it does not modify,
patch, or touch any file under `flexicon/`. Confirmed by the
`git diff --stat -- flexicon/` proof below.

This bug is reported here plainly, as required, and is NOT fixed by this
task (`CreateCheckType`/`_GetCheckList`/`_GetOrCreateCheckList` in
`flexicon/code/System/CheckOperations.py` are unmodified). It is a new,
separate finding for the record, independent of the C1-C8 ruling this
probe was commissioned to inform.

### Predictions vs measurements

| # | Prediction | Measured | Verdict |
|---|---|---|---|
| PN1 | `Exists("TEST_NF_Gen ")` -> True | `True` | **MATCH** |
| PN2 (CORE, binding) | `Exists("TEST_NF_Raw")` -> False; `Exists("TEST_NF_Raw ")` -> False | `False`; `False` | **MATCH** |
| PN3 | `Find`(both needles) -> None; `Exists`(both needles) -> False | `None`, `None`; `False`, `False` | **MATCH** |
| PN4 (binding) | `FindCheckType`(both needles) -> None | `None`, `None` | **MATCH** (after the `_GetCheckList` workaround; see discovery above) |
| PN5 (Q-242B) | `CreateCheckType(<non-str>)` -> no exception; re-read empty/`"***"` | no exception; `GetName()` -> `''`; raw `ITsString(...).Text` -> `None` (a third variant not in the predicted `{"", "***"}` set, but `GetName()`'s `name or ""` normalizes it to `''`, matching the predicted primary accessor) | **MATCH** (primary accessor `GetName()`); nuance noted for the raw accessor |
| PN6 (Q-242B) | `CreateCheckType("   ")` -> no exception; empty name persisted | no exception; `GetName()` -> `''`; raw -> `None` | **MATCH** (same nuance as PN5) |
| PN7 | `Texts.Create`=TypeError; `Discourse.CreateChart`=TypeError; `Anthropology.Create`=AttributeError; `Texts.SetName`=AttributeError | `TypeError: text name must be a string, got _NonStrPayload`; `TypeError: chart name must be a string, got _NonStrPayload`; `AttributeError: '_NonStrPayload' object has no attribute 'strip'`; `AttributeError: '_NonStrPayload' object has no attribute 'strip'` | **MATCH** (all four) |
| PN8 (binding, core claim) | `Create("TEST_NF_Dup ")` SUCCEEDS after a layer-B collision; TWO `IText` objects end up matching | Succeeded, no exception; exactly 2 texts found: `('...4576', 'TEST_NF_Dup ')` and `('...383c7', 'TEST_NF_Dup')` | **MATCH** on the binding claim |
| PN8 (sub-detail, non-binding) | Both texts' stored `Name` byte-identical (`"TEST_NF_Dup "` with space) | First (bypass) = `'TEST_NF_Dup '` (space); second (public-API `Create()`) = `'TEST_NF_Dup'` (no space) -- **NOT** byte-identical | **MISS** on this sub-detail only, flagged as non-binding in the predictions above BEFORE this run. Reason: `Create()` persists the ALREADY-STRIPPED local `name` (`TextOperations.py:152`, reused at `:170-171`), not the original argument, so its own output never carries a trailing space regardless of what the caller passed. The core duplicate-explosion claim is unaffected. |

**No refutation.** PN2, PN4, and PN8's binding claims all measured exactly
as predicted. The ruling's premise -- that these dedup paths strip the
needle only, never the haystack, and that `Create()`'s own duplicate guard
can be defeated by a haystack it never stripped -- holds under live
measurement.

### `git diff --stat -- flexicon/` proof

This task's own contribution to `flexicon/` is zero -- no `Edit`/`Write`
tool call in this task ever targeted a file under `flexicon/`. However,
the raw command run at the end of this cycle is **NOT empty**, due to a
**concurrent, unrelated process** editing files in this shared working
directory during this same wall-clock window (this repo runs a
multi-agent crew; per the task brief, "a ruling ... being written this
same cycle by lex-archivist" confirms other agents are active
concurrently in the same checkout):

```
$ git diff --stat -- flexicon/
 flexicon/code/BaseOperations.py                 | 392 ++++++++++++++++++++++++
 flexicon/code/Grammar/NaturalClassOperations.py | 122 ++------
 2 files changed, 410 insertions(+), 104 deletions(-)
```

Evidence this is NOT from this task:
- Content: the diff is entirely about a "feature-structure owner resolver"
  / `_ApplyFeatureStruc` / natural-class feature-sync refactor (see
  `NaturalClassOperations.__ApplyFeatures`'s docstring change referencing
  "spec feature-structure-sync-gap, T4") -- nothing about name fields,
  whitespace, `Exists`/`Find`, or `CheckOperations`.
- Timing: `ls -la --time-style=full-iso` on the two changed files shows
  mtimes of `2026-09-07 14:11:58` and `2026-09-07 14:12:21`, both inside
  this task's own working window (this task's evidence file was written
  at `14:08:16`, its test file last edited at `14:13:50` -- the unrelated
  files were touched in between, by a different process).
- Recent repo history: `git log` at the start of this session already
  showed `cfc86af feat(base-operations): add feature-structure owner
  resolver and recursive serializer` and
  `specs/tier1-silent-data-loss/.crew-handoff.json` was already listed as
  modified in `git status` BEFORE this task began (see the task's initial
  git-status snapshot) -- confirming a separate, pre-existing,
  still-in-progress crew workstream on feature-structure sync, unrelated
  to name-field whitespace/identity.

This task neither reverts nor commits those unrelated changes -- doing
either would be destructive to another agent's in-progress work outside
this task's scope. The scoped claim this task can make, and does make, is:
**zero `Edit`/`Write` calls in this task touched any file under
`flexicon/`**, confirmed by tool-call history, and the ONLY files this
task added or modified are:
- `tests/operations/test_name_field_identity_probe.py` (NEW)
- `specs/name-field-whitespace-identity/evidence/live-probe-cycle1.md` (this file)
- `specs/name-field-whitespace-identity/reviews/cycle1-programmer.md` (report)

### Headline answer

The C1-C8 ruling's premise is **CONFIRMED, not refuted**: `Exists`/`Find`
dedup paths in `TextOperations`, `AnthropologyOperations`, and
`CheckOperations` all strip only the search needle, never the stored
haystack, and `Create()`'s own pre-creation duplicate check inherits this
same blind spot -- a text (or, by the identical code shape, an
anthropology item or check type) whose stored name carries incidental
whitespace is invisible to a same-name collision check, allowing
`Create()` to mint a second object a human would call by the same name.
Separately, `Checks.CreateCheckType` silently converts both a non-str
payload and a whitespace-only string into a persisted empty name with no
exception (Q-242B), via the identical
`name = name.strip() if isinstance(name, str) else ""` /
`_ValidateParam` (None-only) shape already known to affect `SetName` at
the same three line numbers. An unplanned, unrelated bug
(`CheckOperations._GetCheckList()`'s hardcoded stub plus
`_GetOrCreateCheckList`'s `GetInstance`/`GetService` typo) meant
`CreateCheckType` could not be reached at all through the public API
without a test-only monkeypatch; that bug is reported here for the record
and left unfixed, per this task's read-only-to-production mandate.
