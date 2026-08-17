# Live evidence — Cycle 2: guid-preserving Create() on Agent/Reversal ops

Feature: #236 (`specs/236-guid-create-agent-reversals/`).
Date: 2026-08-17
Branch: `write-path-transactions-b1-b3`
Change under test: `AgentOperations.Create()`, `ReversalIndexOperations.Create()`,
`ReversalIndexEntryOperations.Create()` all gain a trailing `guid=None`
parameter that routes through the existing `BaseOperations._CreateWithGuid()`
helper (already used by 8 other `Create()` methods).

Project: **Target**, via the `target_sandbox` fixture (fresh tempdir copy of
`tests/fixtures/Target*.fwbackup` per test) — nothing here touches the user's
real Target.

---

## 1. Commands

```powershell
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_guid_create_agent_reversals_live.py -m requires_live_project -q
```

Result: `14 passed, 1 skipped in 9.68s`.

```powershell
python -m pytest tests/operations -m "not requires_live_project" -q
```

Result: `1 failed, 294 passed`. The one failure
(`test_lexsense_operations.py::TestGetComplexFormsNotSubentries::test_uses_kclassid_not_type_for_ownerofclass`,
`FileNotFoundError` against a sibling `flexlibs2` checkout's copy of the same
test file) is **pre-existing and unrelated**: reproduced identically on
`git stash` (this feature's changes fully removed) before restoring the
working tree. Confirmed no other file in this diff touches
`test_lexsense_operations.py` or `LexSenseOperations.py`.

## 2. `run_mode` check

`tests/live_status.json` →

```json
"run_mode": "live",
```

Not `"mock"`. The three operations classes (`AgentOperations`,
`ReversalIndexOperations`, `ReversalIndexEntryOperations`) each show
`"add": {"status": "pass", "last_verified": "2026-08-17", ...}` in
`by_class`.

## 3. Pre-state / post-state, read back from the LCM

A standalone probe script opened its own fresh `target_sandbox`-style
tempdir copy of the Target `.fwbackup`, created one object of each type with
an explicit fresh GUID, and **re-queried the object from the LCM by that
GUID** via `FLExProject.Object(guid_str)` (`ServiceLocator.GetObject`) rather
than trusting the object reference `Create()` itself returned:

| Type | Requested GUID | Pre-state: `Object(guid)` before Create() | Post-state: `Object(guid).Guid` after Create() | Match |
|---|---|---|---|---|
| `ICmAgent` | `0e0578ed-5a9b-4197-a1dc-83467cfef8fc` | `KeyNotFoundException` (not in identity map) | `0e0578ed-5a9b-4197-a1dc-83467cfef8fc` | YES |
| `IReversalIndex` (ws=`en`) | `93bce337-45ac-4578-82a2-40d5d2313a16` | `KeyNotFoundException` | `93bce337-45ac-4578-82a2-40d5d2313a16` | YES |
| `IReversalIndexEntry` | `b550e7ca-34dc-4fb7-b85c-70d728af63e5` | `KeyNotFoundException` | `b550e7ca-34dc-4fb7-b85c-70d728af63e5` | YES |

## 4. Duplicate-GUID fallback, observed live (not just asserted)

Second `ICmAgent.Create()` call requesting a GUID already assigned to the
first, captured stderr from the actual LCM call:

```
ICmAgent: Create(Guid=b8d8c45e-07bd-4a5e-a57f-8ba8506fef5d) failed
(InvalidOperationException: Can not create more than one object with
identical GUIDs
   at SIL.LCModel.DomainImpl.CmAgentFactory.Create(Guid guid));
falling back to a new identity. The requested GUID was NOT preserved.
```

| | Requested | Actual (`.Guid` read back) |
|---|---|---|
| First create | `b8d8c45e-07bd-4a5e-a57f-8ba8506fef5d` | `b8d8c45e-07bd-4a5e-a57f-8ba8506fef5d` |
| Second create (same guid) | `b8d8c45e-07bd-4a5e-a57f-8ba8506fef5d` | `be8914fe-a8de-4746-a1b0-3fb94d8a3308` (fallback) |

No exception propagated to the caller; the fallback GUID differs from the
requested one, confirming `_CreateWithGuid`'s documented behaviour holds for
all three new call sites, not just the 8 pre-existing ones.

The equivalent duplicate-GUID case for `IReversalIndexOperations` is covered
by `TestGuidCreateReversalIndex::test_create_duplicate_guid_falls_back_without_raising`
in the pytest suite, but it **skipped** in this Target snapshot: only one
analysis writing system (`en`) currently has no reversal index, and the test
needs two free writing systems (each index requires its own WS). Every
other analysis WS already carries a reversal index. This is reported per the
task brief rather than deleting an existing index to manufacture a second
free WS.

## 5. Contract tests (guid does not weaken existing business rules)

- `TestGuidCreateReversalIndex::test_create_duplicate_writing_system_still_raises_with_guid`
  — PASS: a second `Create()` on an already-indexed WS raises
  `FP_ParameterError` even when `guid=` is supplied.
- `TestGuidCreateAgent::test_created_agent_present_in_analyzing_agents_oc` — PASS.
- `TestGuidCreateReversalIndexEntry::test_created_entry_present_in_index_entries_oc` — PASS.
- Malformed guid (`"not-a-guid"`) raises `FP_ParameterError` for all three
  types — PASS (3/3).
- `guid=None` (the default) mints a valid, non-null, re-readable GUID for
  all three types — PASS (3/3).

## 6. Pass/fail

**PASS.**

| gate | result |
|---|---|
| `test_guid_create_agent_reversals_live.py`, live | 14 passed / 1 skipped (explicit, reported) / 0 failed |
| `tests/live_status.json` | `"run_mode": "live"` |
| `tests/operations` offline regression | 294 passed / 1 pre-existing unrelated failure (reproduced identically without this change) |
| Pre-state/post-state GUID read-back (all 3 types) | match |
| Duplicate-GUID fallback (Agent) | observed live, no raise, fallback GUID distinct |
| WS-duplicate contract with guid supplied | still raises `FP_ParameterError` |
