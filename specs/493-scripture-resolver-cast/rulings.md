# Issue #493 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #493 (P2) -- four Scripture HVO resolvers return uncast `ICmObject`  
**Parent triage:** #284 Class A promotion

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **#493** (#492 has open fix PR #496)
- Open **P3** bugs without an open PR: **#494** (contract-only batch; not selected)
- **Selected #493** this run

## RULING (binding)

Cast each private resolver through `cast_to_concrete` on every path:

| File | Helper | Subtype members callers need |
|------|--------|------------------------------|
| `ScrSectionOperations.py` | `__ResolveBook` | `SectionsOS` |
| `ScrTxtParaOperations.py` | `__ResolveSection` | `ContentOA` |
| `ScrNoteOperations.py` | `__ResolveBook` | `FootnotesOS` |
| `ScrAnnotationsOperations.py` | `__ResolveBook` | `FootnotesOS` |

On the HVO path, keep the **union** of `isinstance` and `ClassName` validation
(match #269 / #492 family). Do not return uncast objects on the HVO or
pass-through branches.

## Verification plan

- Offline: `tests/operations/test_issue493_scripture_resolver_cast_offline.py`
- Live: `tests/operations/test_issue493_scripture_resolver_cast_live.py`
  (`sena3_sandbox`; Scripture module; genuine book/section HVO ints only).
