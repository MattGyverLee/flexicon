# Issue #359 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/359-anthropology-gsp from origin/main

## RULING (binding)

`liblcm_baseline.json` and module header agree: **`ICmAnthroItem` has no
`AnthroCode` or `CategoryRA`**. OCM codes are stored in the inherited
`Abbreviation` multilingual field (see `AnthropologyOperations.py` header).

**Correct behaviour (issue #359 scope -- GetSyncableProperties only):**

1. **`AnthroCode` sync key** -- Do not guard on `AnthroCode`. Emit the
   analysis-ws abbreviation text (the OCM storage field on `ICmAnthroItem`).
2. **`Category` sync key** -- Do not guard on `CategoryRA`. There is no
   category reference on `ICmAnthroItem`; emit `Category: None` without a
   phantom hasattr (the previous guard was always false).

**Out of scope:** `GetAnthroCode` / `SetAnthroCode`, `GetCategory` /
`SetCategory`, duplicate paths, and FindBy* helpers that still reference
phantom members -- separate issues if those APIs are retired or re-based.

## Verification plan

- Offline: extend `test_anthropology_get_syncable_properties.py` ratchets;
  `AnthropologyOperations` already registered in #325 member ratchet map.
- Live: read-only `GetSyncableProperties` on anthropology items when LCM is
  available (`requires_live_project`).
