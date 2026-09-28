# Issue #350 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/350-agent-getsyncableproperties from origin/main

## RULING (binding)

`ICmAgent` is not an `ICmPossibility`. Baseline (`liblcm_baseline.json`) lists
`Name`, `Human`, `Guid`, and related fields but **no `Description`**.

**Correct behaviour (issue #350 scope):**

1. **GetSyncableProperties** -- Implement on `AgentOperations` (do not inherit
   the possibility-shaped reader). Emit `Guid`, multilingual `Name`, `Human`,
   and non-empty `Version` when set. Do **not** read `Description`.
2. **GetDescription / SetDescription** -- Override inherited methods:
   `GetDescription` returns `""`; `SetDescription` is a validated no-op so
   callers do not hit `AttributeError`.

**Out of scope:** Re-basing `AgentOperations` off a non-possibility base (#54),
sync payload design for agent evaluations, or changing `CompareTo`.

## Verification plan

- Offline: source ratchets on `GetSyncableProperties` / description overrides;
  register `AgentOperations` in the #325 member ratchet map.
- Live: read-only `GetSyncableProperties` over all agents in a populated project
  when LCM is available (`requires_live_project`).
