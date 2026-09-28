# Issue #336 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/336-empty-guid-sync from origin/main

## RULING (binding)

When `ApplySyncableProperties` processes `props["Values"][i]` and the dict
**includes** a `"Guid"` key whose value is the empty string, raise
`FP_ParameterError` with a message that tells callers to omit the key to mint
a GUID or supply a well-formed string.

When the `"Guid"` key is **absent**, behaviour is unchanged: `__CreateValueWithGuid`
may mint a random GUID via the last-resort factory path.

**Rationale:** Explicit `""` is indistinguishable from a truncated or lost
identity in upstream serialization. Silent random GUID assignment breaks sync
round-trips (tier-1 silent-data-loss class; see #317/#318 and
`specs/tier1-silent-data-loss/`).

**Out of scope:** Changing mint behaviour when the key is absent; malformed
non-empty GUID strings (#334 / `FP_ParameterError` with CLR cause).

## Verification plan

- Offline: `tests/operations/test_issue334_guid_parse_formatexception.py` (empty
  string case); guard also in `__ApplyValues` loop before `__CreateValueWithGuid`.
- Live: phonological feature value sync round-trip when LCM available
  (`requires_live_project`).
