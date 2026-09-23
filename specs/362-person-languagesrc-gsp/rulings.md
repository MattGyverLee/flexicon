# Issue #362 -- lex-lead ruling

**Date:** 2026-09-23  
**HEAD:** fix/362-person-languagesrc-gsp from origin/main

## RULING (binding)

Live reflection and `liblcm_baseline.json` agree: **`ICmPerson` has no
`LanguagesRC`**. Person language links are not stored on the person object in
LCM (confirmed absent in issue #352 live person face and
`specs/lcm-member-truth-sweep/evidence/live-T2.5-siblings.md`).

**Correct behaviour (issue #362 scope):**

1. **GetSyncableProperties** -- Do not guard on or read `LanguagesRC`. Emit
   `Positions` and `PlacesOfResidence` from the real RC members only. Do not
   emit a `Languages` key from a phantom guard (it was always dead at runtime).

**Out of scope:** `GetLanguages` / `AddLanguage` still reference `LanguagesRC`
and need a separate issue if those APIs are to be retired or re-based;
`GetLanguages`-style discovery is not part of this sync-payload fix.

## Verification plan

- Offline: source ratchet on `GetSyncableProperties`; register
  `PersonOperations` in the #325 member ratchet map (`ICmPerson`).
- Live: read-only `GetSyncableProperties` over people in a populated project
  when LCM is available (`requires_live_project`).
