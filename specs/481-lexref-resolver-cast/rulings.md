# Issue #481 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #481 (P2) -- LexReferenceOperations HVO resolvers uncast  
**Parent triage:** #284 Class A promotion (LexReferenceOperations rows)

## Triage (cron)

- Open **P0** bugs without an open PR: **none** (470-473 have PRs)
- Open **P1** bugs without an open PR: **none**
- Open **P2/P3** bugs without an open PR: **none** (467/476 and resolver promotions have PRs)
- **Filed and selected #481** this run from the #284 inventory (`__ResolveRefType` callers read `MappingType` at `LexReferenceOperations.py:605`)

## RULING (binding)

Cast all four private resolvers through `cast_to_concrete` on every path:

- `__ResolveRefType` -- callers read `ILexRefType` members (`MappingType`, name helpers).
- `__ResolveLexRef` -- callers read `ILexReference` members (`TargetsRS`, `Owner`, sync helpers).
- `__ResolveSenseOrEntry` -- callers need `ILexSense` / `ILexEntry` members on target attach paths.
- `__ResolveEntry` -- callers need `ILexEntry` members.

Replace `hasattr` gates that false-negative on bare `ICmObject` with `cast_to_concrete` plus `isinstance` / `ClassName` checks matching `LexSenseOperations` (#457 family). Do not return uncast objects on the HVO path.

## Verification plan

- Offline: source ratchet + live gate module existence.
- Live: `target_sandbox` gate calling `GetMappingType(ref_type.Hvo)` with precondition that `MappingType` is not reachable on the bare `Object(hvo)` view (`requires_live_project`).
