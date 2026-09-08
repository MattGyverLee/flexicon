# Q4 -- liblcm contract baseline drift: full inventory and decision

Spec reference: `specs/242-paragraph-whitespace/spec.md` section 6, Q4.
Date: 2026-09-08. Branch: `spec/242-gate-and-name-field-identity`.
Decision authority: delegated (Q4 decided and acted on in this pass).

---

## Headline

**There is no hidden drift.** The complete delta between the checked-in
2026-08-13 baseline and the live reflection of the installed liblcm is
**exactly three items**, machine-verified across *every* field the snapshot
records -- not just the two (`properties`, `methods`) that
`compare_snapshots()` actually diffs:

| # | Kind | Item | Origin |
|---|------|------|--------|
| 1 | method removed | `ILexEntryRepository.CorrectHomographNumbers(ILexEntry)` | upstream liblcm change |
| 2 | type added | `IFsComplexValue` | flexicon-side: new entry in `expected_contract.json` |
| 3 | type added | `IFsComplexValueFactory` | flexicon-side: added by commit `4aca74a` |

Zero changes to `constructors`, `interfaces`, `implements_idisposable`,
`reflected_properties`, or `member_checks` across all 255 types shared
between the two snapshots. `member_checks` compares **equal** as a whole
dict. `types_missing` stays 0; `types_with_member_mismatches` stays 11.

This matters because `compare_snapshots()` (`tests/contract/compare_contracts.py`)
diffs only the `properties` and `methods` name lists. The deep-reflection
fields added by `_introspect_signatures()` -- which
`TestTransactionLayerContract` asserts on directly (issues #233/#235/#236)
-- are **invisible to the regression test**, so regenerating the baseline
could in principle have silently rewritten `method_signatures`,
`constructors` or `reflected_properties` underneath those assertions. The
deep diff below was run specifically to rule that out. It did.

---

## What the baseline is FOR, and how it is regenerated

`tests/contract/snapshots/liblcm_baseline.json` serves two distinct roles:

1. **Regression tripwire** (Mode 2, needs liblcm):
   `TestLiveRegressionCheck::test_no_regressions_from_baseline` regenerates a
   live snapshot and calls `compare_snapshots(baseline, live)`, failing on any
   type or member that *disappeared*. Additions are reported but never fail.
2. **Offline shape oracle** (Mode 1, no liblcm needed):
   `TestTransactionLayerContract` (6 tests) and
   `tests/test_b1t_action_handler_double.py` read the checked-in JSON directly
   and assert on `method_signatures`, `constructors`, `reflected_properties`
   and `implements_idisposable` for `IActionHandler`,
   `UndoableUnitOfWorkHelper`, `NonUndoableUnitOfWorkHelper`, `ILcmUI`.
   Role 2 is why hand-editing the JSON is the wrong move: those assertions
   are only meaningful if the file is a faithful reflection dump.

**Documented regeneration procedure.** There is no make target and no
dedicated script entry point. The procedure is the generator's own CLI,
documented in its module docstring (`generate_lcm_snapshot.py:22-29`) and
used in this exact form in
`specs/write-path-transactions/reviews/cycle1-programmer-contract.md:30`:

```
python -m tests.contract.generate_lcm_snapshot -c tests/contract/snapshots/expected_contract.json -o tests/contract/snapshots/liblcm_baseline.json
```

`test_save_snapshot_for_regression` additionally drops a per-version dump at
`snapshots/liblcm_<version>.json` on every Mode-2 run; that artifact is
gitignored and is *not* the baseline.

---

## Commands run (verbatim)

Fresh snapshot to a TEMP path (never over the baseline). Pure CLR
reflection on the installed assemblies -- no FLEx project is opened, no
`FLEXLIBS_REQUIRE_LIVE`, no `scripts/restore_*.py`, no live test:

```
$ python -m tests.contract.generate_lcm_snapshot -c tests/contract/snapshots/expected_contract.json -o $SCRATCH/liblcm_fresh.json
[DONE] Snapshot written to .../scratchpad/liblcm_fresh.json
  LibLCM version: unknown
  Types checked: 257
  Types found:   257
  Types missing: 0
  Member mismatches: 11
```

The harness's own diff engine, baseline vs. fresh:

```
$ python -m tests.contract.compare_contracts diff --old tests/contract/snapshots/liblcm_baseline.json --new $SCRATCH/liblcm_fresh.json --verbose
LibLCM Contract Test: [FAIL]
==================================================
Old version: unknown
New version: unknown
Regressions: 1
Additions:   2

REGRESSIONS:
  [WARN] ILexEntryRepository.CorrectHomographNumbers() removed

ADDITIONS:
  [INFO] Type IFsComplexValue is now available
  [INFO] Type IFsComplexValueFactory is now available
```

Custom deep diff over the fields `compare_snapshots()` ignores
(`constructors`, `method_signatures`, `interfaces`,
`implements_idisposable`, `reflected_properties`, `member_checks`, `found`,
`error`):

```
$ python $SCRATCH/deepdiff.py tests/contract/snapshots/liblcm_baseline.json $SCRATCH/liblcm_fresh.json
== TYPE SET ==
only in baseline: []
only in fresh   : ['IFsComplexValue', 'IFsComplexValueFactory']
[sig-removed] ILexEntryRepository.CorrectHomographNumbers [('ILexEntry',)]
== DEEP-FIELD CHANGE COUNTS == {'sig_removed': 1}
== member_checks ==
types only in baseline member_checks: []
types only in fresh member_checks: []
== summary == {'total_types_checked': 255, 'types_found': 255, 'types_missing': 0, 'types_with_member_mismatches': 11} -> {'total_types_checked': 257, 'types_found': 257, 'types_missing': 0, 'types_with_member_mismatches': 11}
```

A change-count of `{'sig_removed': 1}` is the entire deep-field delta. No
`ctor`, no `iface`, no `refprop_*`, no `sig_changed`, no `sig_added`, no
`found`/`error` flips.

Interpreter cross-check: the baseline was taken under **Python 3.12.7**
(Anaconda), the fresh snapshot under **Python 3.14.5**. The two agree on
255 of 255 shared type entries in every field but the one removed method,
which independently corroborates that the removal is a real liblcm change
and not a pythonnet/interpreter artifact.

---

## Usage cross-check of every drifted member

### 1. `ILexEntryRepository.CorrectHomographNumbers` -- removed, zero impact

```
$ grep -rn "CorrectHomographNumbers" .        # excluding .git/
./specs/242-paragraph-whitespace/.crew-handoff.json:31: (prose)
./specs/242-paragraph-whitespace/spec.md:961:   (prose)
./specs/242-paragraph-whitespace/STATUS.md:214: (prose)
./tests/contract/snapshots/liblcm_baseline.json:11357: "CorrectHomographNumbers",
./tests/contract/snapshots/liblcm_baseline.json:11414: "CorrectHomographNumbers": [
./tests/test_results.json:205: (the failure traceback itself)
```

No hit in `flexicon/` and no hit in any test *body* -- only prose in this
feature's own spec/STATUS/handoff, the baseline dump, and the recorded
traceback.

A stronger check than grep: `expected_contract.json`'s `type_usage` entry
for `ILexEntryRepository` is `{}` -- flexicon imports the repository type but
the contract extractor finds **no member of it used at all**. So the removal
cannot move the compatibility score, and `test_no_missing_members` /
`test_compatibility_score` passed both before and after.

What flexicon actually uses for homographs is the *instance* property
`ILexEntry.HomographNumber` (`LexEntryOperations.py:1308` in
`GetHomographNumber`, `:1311` `SetHomographNumber`, `:557-558` property
capture), which is untouched. The surviving repository-level homograph
surface, from the fresh reflection, is `CollectHomographs(String,
IMoMorphType)`, `GetHomographs(String)`, `HomographMorphOrder(LcmCache,
IMoMorphType)`, `ResetHomographs(IProgress)` -- 10 non-inherited methods
total, no `CorrectHomographNumbers`.

**Verdict: harmless. No code to adapt.**

### 2-3. `IFsComplexValue`, `IFsComplexValueFactory` -- additions, actively used

These are **not** liblcm gaining types; they are flexicon gaining
dependencies after the baseline was taken. `IFsComplexValueFactory` was
added to `expected_contract.json` by `4aca74a` ("Refreshes
tests/contract/snapshots/expected_contract.json (new IFsComplexValueFactory
dependency, needed for C4 complex-value creation)"); `IFsComplexValue`
entered the contract between 2026-08-13 and that commit. Both resolve in
live liblcm (`found: true`).

Both are load-bearing in shipped code:

```
flexicon/code/BaseOperations.py:1866  from SIL.LCModel import IFsFeatStruc, IFsComplexValue, IFsClosedValue
flexicon/code/BaseOperations.py:1891  complex_value = IFsComplexValue(spec)
flexicon/code/BaseOperations.py:1997  return IFsComplexValue(obj)          # _CastFsComplexValue
flexicon/code/BaseOperations.py:2278  IFsComplexValueFactory,
flexicon/code/BaseOperations.py:2337  IFsComplexValueFactory
flexicon/code/lcm_casting.py:267      IFsComplexValue,
flexicon/code/lcm_casting.py:401      _interface_cache["FsComplexValue"] = IFsComplexValue
```

Adding them to the baseline is a strict **increase** in tripwire coverage:
two types the library writes against are now protected against future
removal. Note `flexicon/code/lcm_casting.py:262` explicitly calls the
absence of these entries "a documented P2 snapshot gap" -- this
regeneration closes that gap.

---

## Decision

**Option (b): regenerate the baseline via the project's own documented
command, and record every accepted delta explicitly.**

Reasoning:

* The drift is fully enumerated and each of the three items is
  independently justified above. Regenerating accepts a known, three-item
  set -- not an unexamined "everything since August."
* Option (c), xfail-ing `test_no_regressions_from_baseline`, is strictly
  worse: it would blind the tripwire to *all future* removals, including
  ones that do hit callers, in exchange for tolerating one removal that
  hits none. It also leaves the baseline permanently mis-describing the
  installed liblcm, degrading role 2 (the offline shape oracle that
  `TestTransactionLayerContract` and `test_b1t_action_handler_double.py`
  read, and that several specs cite as a source of truth for field types).
* Option (a), regenerate silently, is what the spec rightly warned against.
  The mitigation is this document plus the spec update, not inaction.
* Regenerating also *improves* coverage (the two `IFsComplexValue*` types,
  closing the gap noted at `lcm_casting.py:262`) and finally makes the
  snapshot traceable to a liblcm build (below).

Rejected as out of scope: filing an upstream question about *why*
`CorrectHomographNumbers` went away. With zero callers and an intact
`ResetHomographs(IProgress)`, it costs this library nothing.

---

## Metadata honesty fix (in scope, small)

The old baseline recorded `"liblcm_version": "unknown"`, which is why no one
could tell which liblcm build it described. That was a **bug in the
generator**, not a limitation: `_get_lcm_version()` scanned
`clr.ListAssemblies()`, which under pythonnet 3.x returns *short* names
(`"SIL.LCModel"`), so its `"SIL.LCModel,"` substring test never matched.

Fixed in `tests/contract/generate_lcm_snapshot.py`:

* `_get_lcm_version()` now walks
  `System.AppDomain.CurrentDomain.GetAssemblies()` and reads the real
  `FullName` `Version=` field. Returns `"11.0.0.0"`. Kept filename-safe
  because `test_save_snapshot_for_regression` interpolates it into
  `liblcm_<version>.json`.
* New `_get_lcm_informational_version()` records the NuGet-style build
  string in a new, additive `metadata.liblcm_informational_version`.
* `datetime.utcnow()` -> `datetime.now(timezone.utc)`, silencing the
  DeprecationWarning the generator emitted on every run under 3.14. The
  output format is unchanged (trailing `Z`).

Independently confirmed by direct reflection:

```
SIL.LCModel, Version=11.0.0.0, Culture=neutral, PublicKeyToken=null
FileVersion: 11.0.0.55161 | ProductVersion: 11.0.0-beta.161+Branch.master.Sha.b87d9f972f472624dfafeabdfd397be3f481436a
SIL.LCModel.dll mtime: 2026-05-04T22:14:34Z
FieldWorks.exe FileVersion: 9.3.9.1439  mtime: 2026-06-12T02:29:46Z
```

The FieldWorks 9.3.9 install postdating the 2026-08-13 baseline is the
"FieldWorks has evidently been updated" that the spec inferred.

Consequence for `.gitignore`: the per-run artifact is no longer always named
`liblcm_unknown.json` (the single filename that was ignored). The ignore was
generalised to `tests/contract/snapshots/liblcm_*.json` with an explicit
`!tests/contract/snapshots/liblcm_baseline.json` negation, so the baseline
stays tracked and per-version dumps stay ignored.

---

## Regeneration command and resulting metadata

```
$ python -m tests.contract.generate_lcm_snapshot -c tests/contract/snapshots/expected_contract.json -o tests/contract/snapshots/liblcm_baseline.json
[DONE] Snapshot written to tests/contract/snapshots/liblcm_baseline.json
  LibLCM version: 11.0.0.0
  LibLCM build:   11.0.0-beta.161+Branch.master.Sha.b87d9f972f472624dfafeabdfd397be3f481436a
  Types checked: 257
  Types found:   257
  Types missing: 0
  Member mismatches: 11
```

New `metadata` block:

```json
{
  "liblcm_version": "11.0.0.0",
  "liblcm_informational_version": "11.0.0-beta.161+Branch.master.Sha.b87d9f972f472624dfafeabdfd397be3f481436a",
  "generated_at": "2026-09-08T15:18:18.627100Z",
  "python_version": "3.14.5 (tags/v3.14.5:5607950, May 10 2026, 10:43:50) [MSC v.1944 64 bit (AMD64)]",
  "platform": "win32"
}
```

Date and interpreter are recorded by the generator itself from the live run;
neither was hand-written.

## Verification that the regenerated file contains ONLY the accepted deltas

Structural diff of the committed baseline at `HEAD` against the regenerated
file (not a line diff -- a parsed, per-field comparison):

```
types only in new: ['IFsComplexValue', 'IFsComplexValueFactory']
types only in old: []
shared types whose entry changed: ['ILexEntryRepository']
  ILexEntryRepository.method_signatures: removed keys ['CorrectHomographNumbers'] added keys []
  ILexEntryRepository.methods: -['CorrectHomographNumbers'] +[]
member_checks equal: True
missing_types: []
```

Every deleted line in the JSON, exhaustively
(`git diff -U0 -- tests/contract/snapshots/liblcm_baseline.json | grep -E "^-[^-]"`):

```
-    "liblcm_version": "unknown",
-    "generated_at": "2026-08-13T23:07:39.805656Z",
-    "python_version": "3.12.7 | packaged by Anaconda, Inc. | (main, Oct  4 2024, 13:17:27) [MSC v.1929 64 bit (AMD64)]",
-        "CorrectHomographNumbers",
-        "CorrectHomographNumbers": [
-          [
-            "ILexEntry"
-          ]
-        ],
-    "total_types_checked": 255,
-    "types_found": 255,
```

Eleven removed lines: three metadata, six for the removed method (its name
in `methods`, plus the five lines of its `method_signatures` entry), two
summary counts. Nothing else was lost. Total churn in the file is 149
changed lines, of which 138 are the two new type blocks.

---

## Test result: before and after

Both runs offline, always with the marker filter. No bare `pytest`.

**Before** (`HEAD` baseline):

```
$ python -m pytest tests/contract/test_lcm_contract.py -m "not requires_live_project" -q
E           Failed: 1 regressions from baseline:
E             - ILexEntryRepository.CorrectHomographNumbers() removed
tests\contract\test_lcm_contract.py:343: Failed
FAILED tests/contract/test_lcm_contract.py::TestLiveRegressionCheck::test_no_regressions_from_baseline
1 failed, 21 passed, 4 warnings in 1.37s
```

**After** (regenerated baseline):

```
$ python -m pytest tests/contract/test_lcm_contract.py -m "not requires_live_project" -q
22 passed, 2 warnings in 1.11s

$ python -m pytest tests/contract -m "not requires_live_project" -q
22 passed, 2 warnings in 1.11s
```

The two remaining warnings are pre-existing pytest deprecations
(class-scoped fixture defined as instance method); the two
`datetime.utcnow()` DeprecationWarnings are gone, since the generator no
longer calls it.

The other consumer of the baseline JSON, re-run to confirm the regeneration
did not disturb the offline shape assertions:

```
$ python -m pytest tests/test_b1t_action_handler_double.py -m "not requires_live_project" -q
32 passed in 0.52s
```

`TestTransactionLayerContract`'s 6 shape tests are inside the 22 above and
pass, consistent with the deep diff showing zero change to `IActionHandler`,
`UndoableUnitOfWorkHelper`, `NonUndoableUnitOfWorkHelper` or `ILcmUI`.

Note on markers: the failing test is gated by a module-level
`pytest.mark.skipif` named `requires_liblcm`, **not** by
`requires_live_project`. It therefore runs under
`-m "not requires_live_project"`. That is safe -- Mode 2 does pure CLR
reflection on the installed assemblies and never opens, locks, or writes a
FLEx project.

---

## Files changed

| File | Change |
|------|--------|
| `tests/contract/snapshots/liblcm_baseline.json` | Regenerated (255 -> 257 types; `CorrectHomographNumbers` dropped; real version metadata) |
| `tests/contract/generate_lcm_snapshot.py` | `_get_lcm_version()` bug fix; new `_get_lcm_informational_version()`; tz-aware timestamp; extra CLI print line |
| `.gitignore` | `liblcm_unknown.json` -> `liblcm_*.json` with a `!liblcm_baseline.json` negation |
| `specs/242-paragraph-whitespace/spec.md` | Q4 marked RESOLVED with the accepted-delta table |
| `specs/242-paragraph-whitespace/evidence/q4-contract-baseline.md` | This file |

Not committed and not pushed; left in the working tree per instructions.

---

## What could NOT be determined

1. **Which liblcm/FieldWorks version the 2026-08-13 baseline was taken
   against.** Its `liblcm_version` is `"unknown"` because of the
   `_get_lcm_version()` bug described above, and the raw member lists carry
   no version marker. So the *upstream* change can be dated only as "at some
   point at or before the FieldWorks 9.3.9 / liblcm 11.0.0-beta.161 install
   now on this machine"; it cannot be attributed to a specific liblcm release
   from artifacts in this repo. Future baselines will not have this problem.
2. **Why `CorrectHomographNumbers` was removed upstream, and whether liblcm
   considers it renamed rather than deleted.** Determining that needs the
   liblcm source history, which is not vendored here. It does not affect this
   library (zero callers, empty `type_usage`).
3. **Whether any drift exists in liblcm surface that flexicon does not yet
   import.** By construction the snapshot only reflects types listed in
   `expected_contract.json` (257 of them). A removal on a type flexicon never
   imports would be invisible to both the baseline and this analysis. That is
   the tripwire's designed scope, not a gap introduced here.
4. **`types_with_member_mismatches: 11` is unchanged and was not
   investigated.** It is identical in both snapshots (`member_checks` compares
   equal), so it is pre-existing and orthogonal to Q4. It is
   `extra_*`/`missing_*` bookkeeping already tolerated by the passing
   `test_no_missing_members`.
