# Issue #468 -- lex-lead ruling

**Date:** 2026-09-25  
**Issue:** #468 (P3) -- LCMObjectWrapper missing `__eq__` / `__hash__`  
**Follow-on from:** #449 domain review (Q2)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs without an open PR: **none** (#459 fix merged as PR #460 but issue still open; not re-selected)
- Open **P3** bugs without an open PR: **#468** (selected; #284 is re-triage tracking only)

## RULING (binding)

1. Add **`__eq__` and `__hash__` to `LCMObjectWrapper`** keyed on the wrapped
   object's **`Hvo`**, comparing equal to:
   - another `LCMObjectWrapper` around the same Hvo,
   - a `PythonicWrapper` around the same Hvo,
   - a raw LCM object with the same Hvo.
2. Centralize Hvo extraction in **`lcm_identity_hvo()`** in
   `wrapper_base.py` so Operations and wrappers share one definition.
3. Align **`PythonicWrapper.__eq__` / `__hash__`** with the same Hvo
   semantics (replace identity-based `hash(obj)` / reference equality).
4. **Out of scope:** changing `_UnwrapLcm` behaviour, resolver casts, or
   dict/set uses that intentionally key on wrapper object id.

## Verification plan

- Offline: `tests/operations/test_issue468_wrapper_eq_hash_offline.py`
  (fake LCM stand-ins, no FieldWorks).
- Live: not required (no Operations write path or LCM factory change).
