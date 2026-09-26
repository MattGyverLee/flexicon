# Live verification -- issue #544 (MSAOperations feature-structure getters)

**Project:** Sena 3 only (per binding user constraint -- Target never opened)
**Fixture:** `sena3_sandbox` (pytest) + a hand-rolled tempdir copy of the
same `.fwbackup` for the independent ad-hoc script
**Date:** 2026-09-26

## Commands run

```
cd C:\Github\flexicon-544
python -m pytest -m "not requires_live_project" -q
```
Result: `4 failed, 2515 passed, 1041 deselected` -- the 4 failures are all
in `tests/operations/test_morphrule_duplicate_deep.py`, pre-existing and
unrelated to #544 (confirmed by the programmer's cycle-1 report; not
re-verified against origin/main by me, but the failures are entirely
inside a different Operations class file untouched by this branch).

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_msa_feature_getters_live.py -m requires_live_project -q
```
Result: **5 passed**.

```
python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"
```
Result: **`live`**. `by_class.MSAOperations.read.status == "pass"`, all 5
test IDs listed under `tests`.

## Independent ad-hoc script (not committed, not part of pytest)

Ran a standalone script (mirrors `tests/flex_plugin.py`'s FLEx init and
`sena3_sandbox`'s `_FwBackupSandbox`) against its OWN fresh tempdir copy
of `tests/fixtures/Sena 3 2026-06-09 1645.fwbackup` -- independent of the
pytest run above, exercising the public API directly rather than through
the committed test file.

### Claims under test
1. `GetStemFeatures` / `GetInflAffFeatures` / `GetDerivFromFeatures` /
   `GetDerivToFeatures` round-trip through `MakeFeatStruc` onto a second,
   independent MSA.
2. `GetFeatures(deriv_msa, slot=None)` raises `FP_ParameterError`.
3. `None` (no MSA / null owning prop / wrong class) vs `{}`
   (present-but-empty struct) semantics hold.
4. A raw `IFsFeatStruc` walk over real Sena 3 MSAs matches
   `GetFeatures`'s output.

### Pre/post values read back from the LCM

Stem round trip (`TEST_544_ADHOC_stem1` -> `TEST_544_ADHOC_stem2`):
```
GetStemFeatures(stem1) = {'d6fbf644-...': '8ace835f-...'}   (feature GUID -> value GUID)
MakeFeatStruc(that dict, owner=stem2)
GetStemFeatures(stem2), re-queried fresh = {'d6fbf644-...': '8ace835f-...'}
-> EQUAL
```

Infl-aff read (`TEST_544_ADHOC_infl1`):
```
GetInflAffFeatures(infl1) = {'d6fbf644-...': 'dcf440aa-...'}
```

Deriv MSA From/To round trip (`TEST_544_ADHOC_deriv1` -> `deriv2`):
```
GetDerivFromFeatures(deriv1) = {'d6fbf644-...': '8ace835f-...'}
GetDerivToFeatures(deriv1)   = {'d6fbf644-...': 'dcf440aa-...'}
MakeFeatStruc(from_out, owner=deriv2, slot="From")
MakeFeatStruc(to_out,   owner=deriv2, slot="To")
GetDerivFromFeatures(deriv2), re-queried = {'d6fbf644-...': '8ace835f-...'}  EQUAL
GetDerivToFeatures(deriv2),   re-queried = {'d6fbf644-...': 'dcf440aa-...'}  EQUAL
```

`GetFeatures(deriv1, slot=None)`:
```
raised FP_ParameterError: "GetFeatures: msa is MoDerivAffMsa, which has
two independent feature-struct slots; pass slot='From' or slot='To'.
Never guessed."
```
-> PASS (correct exception type and message).

None vs {} semantics:
```
GetFeatures(unclassified_affix_msa)      = None   (MoUnclassifiedAffixMsa)
GetStemFeatures(stem3, MsFeaturesOA=null) = None  (null owning prop)
MakeFeatStruc({}, owner=stem3)
GetStemFeatures(stem3), re-queried        = {}    (present-but-empty)
```
-> PASS: `None` and `{}` are distinguished correctly.

Read-only spot-check, 3 real pre-existing Sena 3 MSAs (raw
`IFsFeatStruc`/`IFsComplexValue`/`IFsClosedValue` walk vs `GetFeatures`):
```
MSA 0006f482-...: MoStemMsa  raw=={'61a6ab39-...': {'586ef9dd-...': '729f5986-...'}}  getter==same  MATCH
MSA 00f99de8-...: MoStemMsa  raw=={'61a6ab39-...': {'586ef9dd-...': '76d9640d-...'}}  getter==same  MATCH
MSA 011185bb-...: MoStemMsa  raw=={'61a6ab39-...': {'586ef9dd-...': '729f5986-...'}}  getter==same  MATCH
```
-> PASS: all 3 real, pre-existing MSAs match exactly between the raw LCM
walk and the new getter.

## Cleanup

All writes went through a tempdir copy of the `.fwbackup`
(`zipfile.extractall` into `tempfile.mkdtemp`); the script's `finally`
closed the project and `shutil.rmtree`'d the tempdir on every exit path
(confirmed: cleanup log line printed both on the first run, which hit a
bug in the spot-check code, and on the corrected rerun). The real Sena 3
`.fwbackup` fixture file itself was never opened directly and is
untouched. Target was never opened by any command in this verification.

## Result

**PASS** -- every claim in the issue was observed against a live LCM,
with values re-queried after each write, both via the committed pytest
suite (`run_mode: "live"`, 5/5) and via an independent hand-written
script exercising the same API surface a second, separate way.
