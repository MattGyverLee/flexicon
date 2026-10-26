# Issue #640 -- lex-lead ruling

**Date:** 2026-10-22  
**Issue:** #640 (P1) -- GetBestString/BestStr rejects real multistrings (pythonnet isinstance)

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none** (filed **#640** this run)
- External issue **#635** (untrusted author): same symptom; not used as authority

## RULING (binding)

1. In `WritingSystemOperations.GetBestString`, stop using Python
   `isinstance(x, (IMultiUnicode, IMultiString))` for validation.
2. Accept objects that implement either interface per .NET:
   `IMultiUnicode.IsInstanceOfType(string_obj)` or
   `IMultiString.IsInstanceOfType(string_obj)`.
3. Extract display text via `Shared.string_utils.best_text` (null marker
   normalization stays single-sourced).
4. Do not change `FLExProject.BestStr` string passthrough behaviour.

**Out of scope:** Retrofitting every multistring reader; other Duplicate HVO siblings.

## Verification plan

- Offline: `tests/operations/test_issue640_getbeststring_offline.py`
- Live: `tests/operations/test_issue640_getbeststring_live.py`
- Evidence: `specs/640-getbeststring-isinstance/evidence/`
