# Live evidence -- sweep-doc follow-up to #352 (ScrBook face)

**Date:** 2026-09-21
**Projects:** Tlachichilco Tepehua-NT orthography (26 NT books; reads
read-only; write path creates a book under a free canonical number with
finally-cleanup and zero-residue assertion).
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_352_scrbook_live.py -m requires_live_project -q
```

## Classification

- Not in #352's tables; flagged only by the older sweep doc
  (`ScrBookOperations.py:185,324,405,446`): `IScrBook` exposes `TitleOA`
  (IStText), not `Title`.
- Live: `hasattr(book, 'Title')`=False; `Name`/`Abbrev` present
  (book 40 reads "Mateo"); snapshot agrees.

## Fix (`flexicon/code/Scripture/ScrBookOperations.py`, `FLExProject.py`)

- `Create`/`FindByName`/`GetTitle`/`SetTitle`: `Title` -> `Name`
  (MultiUnicode, same `get/set_String` call shape). The examples
  ("Genesis", "Matthew", find-by-name) always meant the book name, so
  no docstring semantics changed.
- Wired the missing `project.ScrBooks` accessor (+ `.pyi` stub), mirroring
  the `ScrDrafts` wiring in the same pass (both classes were orphaned).

## Post-fix values read back from the LCM

- Real book 40 reads a non-empty title; `FindByName` round-trips;
  unknown numbers miss.
- Created book under a free canonical number reads back, relabels, and
  deletes with zero residue.

## Pass/fail

**PASS.** `2 passed` on the command above, live run_mode.
