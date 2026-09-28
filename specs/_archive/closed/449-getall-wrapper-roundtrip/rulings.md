# Issue #449 -- lex-lead ruling (cron)

**Date:** 2026-09-24  
**HEAD:** `fix/449-getall-wrapper-unwrap` from `origin/main`

## Triage (cron)

- Open **P0** bugs without an open PR: **#448**, **#449**
- Selected **#449** (wrapper round-trip crash on every `GetAll()` item passed
  back into Operations resolvers; broader user impact than #448's
  `MoveItem` niche)

## RULING (binding)

1. Add **`BaseOperations._UnwrapLcmObject`** -- single peel for
   `LCMObjectWrapper.lcm_object` / `._obj` before any pythonnet
   `I<Interface>(obj)` cast (same shape as
   `InflectionFeatureOperations.__Unwrap`, issue #120).
2. Route **`AllomorphOperations.__GetAllomorphObject`** and
   **`POSOperations.__ResolveObject`** through `_UnwrapLcmObject` on the
   non-HVO branch. **`MSAOperations.__GetMsaObject`** already unwraps
   `._obj`; no behaviour change required there.
3. **Live gate:** for Sena 3 (or sandbox), iterate `Allomorphs.GetAll(entry)`
   and assert `GetForm(item)` succeeds for every item; same for
   `MSA.GetAll(entry)` with a read that uses `__GetMsaObject`
   (`GetPartOfSpeech` or equivalent).
4. **Out of scope:** full #268 resolver sweep, #284 inventory, caller-side
   `ICmObject(wrapper)` documentation pass (wrapper_base already documents
   `.lcm_object`).

## Verification plan

- Offline: `tests/operations/test_issue449_wrapper_unwrap_offline.py`
- Live: `tests/operations/test_issue449_getall_roundtrip_live.py` with
  `FLEXLIBS_REQUIRE_LIVE=1`
- Evidence: `specs/449-getall-wrapper-roundtrip/evidence/offline-449.md`
