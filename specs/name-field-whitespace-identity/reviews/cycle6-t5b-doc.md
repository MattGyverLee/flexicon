# Doc Agent Report -- Cycle 6 (T5b)

**Date:** 2026-09-07
**Trigger:** /lex-lead overturn of T5 scope decision on three `Raises` blocks

## Sites corrected (all verified against code before writing)

| File | Method | Change |
|---|---|---|
| `flexicon/code/Notebook/AnthropologyOperations.py` | `Create` (~:210) | `Raises` no longer claims empty name raises `FP_NullParameterError`; now states None-only, notes empty/whitespace-only persists literally (Q-242D/Q-242C), adds `AttributeError` for non-str (throwaway `.strip()`, C7(b)) |
| `flexicon/code/Notebook/AnthropologyOperations.py` | `CreateSubitem` (~:333) | Same correction for the `name` half; `parent_item` half of the line left untouched |
| `flexicon/code/TextsWords/TextOperations.py` | `SetName` (~:586) | Same correction for the `name` half; `text_or_hvo` half left untouched. Removed a duplicate `Note:` block (Args already states Q-242D there) to avoid triple-repeating the same fact |

Verified via code read at each site: `_ValidateParam` is None-check-only (C11(a)), followed by a throwaway, non-reassigning `name.strip()` (C11(a) Shape B / C7(b)) -- confirms `AttributeError` on non-str, no rejection of empty/whitespace-only.

## Scope discipline
- No behavior changed; no other method touched.
- `CHANGELOG.md` untouched (T5 entries already correct).
- No `docs/MANIFEST.md` created, no issues filed.
- No verification run or claimed (docs-only, zero executable lines).

## Open follow-ups
- None. Q-242C remains the pending harmonisation decision owning these three sites; not decided here.

---
**Doc Agent:** /lex-doc
