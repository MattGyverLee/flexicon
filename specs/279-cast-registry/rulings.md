# Issue #279 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** fix/279-cast-registry-remainder from origin/main

## RULING (binding)

Issue #279 tracks two leftovers from the #270 collection-cast sweep. This PR
closes **gap 1 only**.

**In scope (this PR):**

Register the four ClassNames that #270 deliberately omitted because they were
absent from `tests/contract/snapshots/expected_contract.json`:

1. `LexEntryInflType` -> `ILexEntryInflType`
2. `CmCustomItem` -> `ICmCustomItem`
3. `ChkTerm` -> `IChkTerm`
4. `ConstituentChartCellPart` -> `IConstituentChartCellPart`

Mechanical steps:

- Extend `lcm_casting._ensure_interfaces()` with the four imports and cache
  entries (same pattern as the eleven #270 possibility/cell subtypes).
- Regenerate `expected_contract.json` via `extract_lcm_contract.py` so
  `test_no_new_type_dependencies` stays honest.
- Offline source ratchets pinning the four `_interface_cache[...]` assignments.

**Out of scope:**

- **Gap 2** (`FLExProject` possibility helpers at `:4173` / `:4184`) -- API
  decision (live collection vs cast list). Issue #279 stays open for that item.
- Full `liblcm_baseline.json` regeneration on FieldWorks (Mode 2 contract suite).
  Cloud agent: not available; offline contract ratchet is the gate here.

## Verification plan

- Offline: `tests/operations/test_issue279_cast_registry_offline.py` +
  `pytest tests/contract/test_lcm_contract.py -m "not requires_liblcm" -q`
- Live: optional `cast_to_concrete` read-back on instances of the four types when
  LCM is available. Cloud: **FAIL: unverified** (no FieldWorks on Linux pod).
