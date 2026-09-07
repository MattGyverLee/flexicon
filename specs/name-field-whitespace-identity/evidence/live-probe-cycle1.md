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

(pending -- filled in below after the live command completes)
