# Live evidence -- #352 allomorph face (StemName/AffixType)

**Date:** 2026-09-21
**Project:** Target sandbox (tempdir copy -- nothing leaks)
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_352_allomorph_live.py -m requires_live_project -q
```

## Pre-fix classification (snapshot + live probe)

- Snapshot: `IMoStemAllomorph` declares `StemNameRA` only (15751);
  `IMoAffixAllomorph` declares no `AffixType` (`MorphTypeRA` lives on
  `IMoForm`).
- Live probe (target_sandbox): fresh stem allomorph has
  `hasattr StemName`=False, `StemNameRA`=None; Target has zero
  `IMoStemName` instances, so a set-valued round-trip is not provable
  here (needs Sena 3). `morphType="suffix"` create sets `MorphTypeRA`.

## Fix (`flexicon/code/Lexicon/allomorph.py`)

- `stem_name`: reads `StemNameRA` reference's best-analysis `Name`
  ("" when unset) instead of `StemName.get_String` (was a permanent
  swallowed ""; `except Exception: return ""` retained as backstop).
- `affix_type` (sibling, same bug class, not in the issue table):
  returns `MorphTypeRA` instead of the nonexistent `AffixType`
  (was permanent None).
- Docstrings/examples updated (`StemNameRA`/`MorphTypeRA`).

## Post-fix values read back from the LCM

- Fresh stem allomorph: `stem_name == ""`, no exception.
- Fresh suffix allomorph: `affix_type` resolves the created morph type.

## Pass/fail

**PASS.** `2 passed` on the command above, live run_mode.
Open: set-valued `stem_name` round-trip needs a project with
`IMoStemName` instances (Sena 3 backup missing in this env).
