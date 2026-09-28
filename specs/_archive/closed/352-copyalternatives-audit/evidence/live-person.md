# Live evidence -- #352 Person face (Gender/Email/Phone/Notes)

**Date:** 2026-09-21
**Project:** Target sandbox (tempdir copy -- nothing leaks)
**run_mode:** live (`tests/live_status.json` shows `"run_mode": "live"`)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_352_person_live.py -m requires_live_project -q
```

## Pre-fix live probe (member shapes on a fresh person, target_sandbox)

- `Gender` pytype=`int`, value=`0` -- Int32 (snapshot 5911 confirmed live).
- `hasattr Email`=False, `hasattr PlaceOfBirth`=False -- no such members.
- `PlaceOfBirthRA` exists (None when unset) -- ICmLocation reference.
- `Name`/`Alias` IMultiUnicode, `Abbreviation` IMultiUnicode,
  `Description` IMultiString, `PositionsRC`/`PlacesOfResidenceRC` ref
  collections -- all usable as before (not #352 sites).
- `Comment`=False, `LanguagesRC`=False -- sibling nonexistent members
  found live (same bug class; fixed in the same pass).
- `NotesOA` is ICmAgent-only: `ICmPerson` implements `ICmPossibility`,
  not `ICmAgent` (snapshot interfaces), so person notes have no backing
  field either -- GetNotes/AddNote retired, not retargeted.

## Fix (`flexicon/code/Notebook/PersonOperations.py`)

- `GetGender`/`SetGender` (was string multistring contract): now int --
  direct `person.Gender` read/assign; `SetGender` rejects non-int
  (incl. bool) with `FP_ParameterError`. Docstrings updated (no code
  meanings claimed).
- `GetEmail`/`SetEmail`/`GetPhone`/`SetPhone`/`GetNotes`/`AddNote`:
  no backing field (always raised `AttributeError`); now raise
  `FP_ParameterError` naming issue #352. Signatures kept.
- `Duplicate`: `Gender` direct int assign; dropped
  Email/PlaceOfBirth/Comment/LanguagesRC copies; added guarded
  `PlaceOfBirthRA` reference copy.
- `GetSyncableProperties`: `Gender` int; dropped Email/Comment keys;
  `PlaceOfBirthRA` GUID-or-None (was phone string off a missing member;
  the old method raised before returning anything).
- Docstrings updated (class usage, Create, Find, Duplicate, sync
  example); `FLExProject.Person` + 4 `AgentOperations` examples no
  longer teach the retired email API.

## Post-fix values read back from the LCM

- `Create` -> `GetGender` == 0; `SetGender(1)` -> `GetGender` == 1;
  `SetGender("Male")` raises `FP_ParameterError`.
- All six retired methods raise `FP_ParameterError` matching "352".
- `Duplicate` conserves int gender; `CompareTo(rec, dup)` clean;
  sync props carry int gender, no Email key, `PlaceOfBirthRA` None.

## Pass/fail

**PASS.** `4 passed` on the command above, live run_mode.
Related suites: `test_datanotebook_duplicate.py` (updated 2 tests that
pinned the old Title crash) + `test_352_datanotebook_live.py` all pass
(15 passed combined).
