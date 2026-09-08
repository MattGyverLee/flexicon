# Live evidence -- cycle 6, C16 discharge

**Date:** 2026-09-08. **Branch:** `spec/242-gate-and-name-field-identity`.
**Purpose:** discharge `spec.md` **C16** -- the live-evidence durability gap.
C16's remedy, as written, is a live run that pastes the `run_mode` AND
`run_timestamp` lines verbatim into an evidence file, because
`tests/live_status.json` is gitignored (`.gitignore:99`) and does not
survive the run.

This file is that remedy. It is the first evidence file in this feature to
satisfy C16's own standard.

## The exact command

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue242_whitespace_probe.py -m requires_live_project -q
```

Result:

```
........                                                                 [100%]
[OK] Wrote C:\Github\flexicon\tests\test_results.json (8 tests recorded)

8 passed in 4.00s
```

8 collected, 8 passed -- matching the 8 tests the probe has carried since
cycle 3 (`test_p1`..`test_p5`, `test_p7`, `test_p8`, `test_p8b`). Not a
zero.

## `tests/live_status.json`, pasted verbatim -- the C16 requirement

```
run_mode:        live
run_timestamp:   2026-09-08T15:25:51Z
```

Keys present in the artifact: `['by_class', 'by_test', 'run_mode',
'run_timestamp', 'uncategorized_live_tests']`.

**`run_mode` is `live`, not `mock`.** Per CLAUDE.md this is the
machine-checkable anchor a verification claim requires, and per C16 the
`run_timestamp` is what binds the claim to this specific run. Both are now
in a committed file. **C16 is DISCHARGED.**

## Fixture provenance -- read this before repeating the run

The first attempt FAILED, correctly and loudly:

```
Failed: FLEXLIBS_REQUIRE_LIVE=1 but the Target sandbox is unavailable:
No Target .fwbackup found in C:\Github\flexicon\tests\fixtures;
copy the golden backup in (see tests/LIVE_TESTING.md).
Refusing to skip a live write-path verification.
```

This is the fail-loud flag working exactly as designed -- it refused to
degrade into a skip. FLEx itself initialised fine (assemblies loaded,
`FLExInitialize()` complete); only the fixture data was absent, and
`tests/fixtures/` did not exist at all.

**`tests/LIVE_TESTING.md:47` has a STALE PATH.** It names the golden copy
as:

```
D:\Github\_Projects\_LEX\GramTrans\backups\Target 2026-07-06 0218.fwbackup
```

There is **no `D:` drive on this machine.** The same file -- byte-identical
filename and datestamp -- was found at:

```
C:\Github\GramTrans\backups\Target 2026-07-06 0218.fwbackup   (1320037 bytes)
```

It was copied to `tests/fixtures/`, which `.gitignore:98`
(`tests/fixtures/*.fwbackup`) excludes, so the 1.3 MB fixture is NOT
committed. Confirmed with `git check-ignore -v`.

**This is the canonical documented fixture, not a substitute.** Two other
Target-ish backups exist locally (`Ejagham W Target 2026-08-19 0830`,
`Ngoreme Target 2026-08-19 0831`) and were deliberately NOT used: neither
matches `conftest.py`'s `Target*.fwbackup` glob, and substituting a
different project's data into an evidential run is precisely the kind of
quiet swap C16 exists to prevent.

**Follow-up (not fixed here):** `tests/LIVE_TESTING.md:47`'s `D:` path
should be corrected to the `C:` location, or made drive-agnostic, so the
next person does not hit this. Left for the doc's owner.

## Safety constraints -- all honoured

- `target_sandbox` / `target_sandbox_path` fixtures ONLY. The probe's
  module-level fixtures are unchanged from cycle 3, and its own header
  comment (`:61-62`) records the constraint.
- **The real Target project was never opened.** The run unzips the
  `.fwbackup` into a tempdir (`conftest.py:1242-1263`) and works only
  there.
- **No `scripts/restore_*.py` was run.**
- **Never bare `pytest`.** Every invocation in this session carried either
  `-m requires_live_project` (this run, one file) or
  `-m "not requires_live_project"` (offline).
- Only the #242 probe file was executed live -- not the ~322-test live
  marker set.

## Offline suite at the same commit

Run serially, immediately before this live run:

```
python -m pytest tests -m "not requires_live_project" -q
1293 passed, 1 skipped, 483 deselected, 10 warnings in 4.39s
```

**Zero failures.** Up from cycle 6's initial 1291/2-failed after Q4
regenerated the liblcm contract baseline and Q5 repaired the alias
ratchet. Deselected is unchanged at 483.

Note for the record: an earlier full-suite run during this session showed
a Windows access violation in `FLExInit.py:64 FLExInitialize` on the
contract test. That was measured while two agents were initialising
FieldWorks/LCM in separate processes concurrently. Re-run serially, it does
not reproduce -- **the failure was contention, not a defect.** Live and
contract runs in this repo should be treated as serial-only.

## What this run does and does NOT establish

**Does:** the 8 probe assertions hold against a live LCM, `run_mode` is
`live`, and the claim is now durably recorded per C16.

**Does NOT:** this is the cycle-3 probe re-run unchanged. It re-confirms
the #242 and C12 fixes on live data; it measures nothing new, and it says
nothing about `specs/name-field-whitespace-identity/`, whose own harness
(`tests/operations/test_name_field_identity_probe.py`) still does not
exist. That feature's PN1-PN8 predictions remain UNMEASURED (see its NF8).
