# Live Verification: issue #298 fix live run

## Command

```powershell
$env:FLEXLIBS_REQUIRE_LIVE = "1"
"y" | python examples/grammar_pos_operations_demo.py
```

## run_mode

`live` -- FLEXLIBS_REQUIRE_LIVE=1 was set, so any silent degradation to mocks
would be a hard failure. OpenProject("Sena 3", writeEnabled=True) succeeded and
live LCM objects were read/written (no MOCK MODE warning emitted).

## Pre-state / Post-state read back from the LCM

- STEP 1 (READ): enumerated existing POS objects via `project.POS.GetAll()`.
- STEP 2 (CREATE): `project.POS.Create("crud_test_pos", "ct")` returned an
  object; `GetName` read back `crud_test_pos`; the CRUD test previously exited
  here ("may require special parameters") and never reached STEP 3.
- STEP 3 (READ): `Exists("crud_test_pos")` returned True; `Find` found it.
- STEP 4 (UPDATE): `SetName` to `crud_test_pos_modified`, then `GetName` read
  back `crud_test_pos_modified` (value re-read from the LCM, not the input).
- STEP 6 (DELETE): `Delete(test_obj)`; `Exists("crud_test_pos_modified")`
  read back False after deletion.
- Counts: baseline 37 (full count read during STEP 3/6), after create 38,
  after delete 37 -- net zero residue. CLEANUP block reported nothing to delete.

## Pass/fail

PASS -- all six STEP banners printed; STEP 2 no longer soft-fails; DELETE
verified via independent re-read (Exists=False). No TEST_/crud_test_pos object
left behind.