# Live verification -- issue #249 (SLDR Initialize failure swallowed)

Branch: `fix/249-sldr-initialize-swallowed`
Date: 2026-09-08
Machine: Windows 11 Pro, FieldWorks 9.3.10, SIL.WritingSystems 18.0.0.0, Python 3.14

Subject under test: `flexicon/code/FLExInit.py` -- `FLExInitialize()` /
`FLExCleanup()` SLDR guards. The fix was pre-applied; this file records its
verification, not its authoring.

## Files added

- `tests/test_249_sldr_init_guard.py` -- offline unit coverage of the
  exception discriminator (12 tests, no FieldWorks work performed).
- `tests/operations/test_249_sldr_init_live.py` -- live coverage against the
  real `SIL.WritingSystems.Sldr` singleton (3 tests,
  `requires_live_project`).

## Commands run, verbatim

### 1. Offline unit tests

```
python -m pytest tests/test_249_sldr_init_guard.py -q
```

```
............                                                             [100%]
[OK] Wrote C:\Github\flexicon\tests\test_results.json (12 tests recorded)

12 passed in 0.60s
```

### 2. Live verification (mandated fail-loud flag)

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_249_sldr_init_live.py -m requires_live_project -q -s
```

```
[INFO] [SESSION FIXTURE] Initializing FieldWorks for tests...
[OK] FieldWorks path added: C:\Program Files\SIL\FieldWorks 9\
[OK] SIL assemblies loaded
[OK] FLEx services initialized
[OK] FLExInitialize() complete
[OK] flexicon imported successfully
[OK] Loaded 59/59 operations classes
..[INFO] pre-state:  IsInitialized=True  LanguageTags.Count=9596
[INFO] mid-state:  IsInitialized=False after two FLExCleanup() calls, neither raised
[INFO] post-state: IsInitialized=True  LanguageTags.Count=9596
.
3 passed in 0.88s
```

### 3. Regression checks

```
python -m pytest flexicon/tests/test_FLExInit.py -q
-> 1 passed in 0.47s
   (stderr carried the known benign ICU faulthandler trace, issue #35)

python -m pytest tests/test_flexlibs2_alias_ratchet.py -q
-> 2 passed in 1.77s

$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/test_249_sldr_init_guard.py tests/operations/test_249_sldr_init_live.py -q
-> 15 passed in 0.83s
   (confirms the offline monkeypatched module globals do not leak into the
   live module in a shared session)
```

No bare `pytest` invocation was made at any point.

## run_mode from tests/live_status.json

```
run_mode: live
uncategorized_live_tests: []
by_class["FLExInit"]["read"]: status=pass, last_verified=2026-09-08
```

All three live tests recorded `status: pass` under
`operations_class: FLExInit`, `phase: read`.

## State read back from the CLR

Every value below was obtained by re-querying `SIL.WritingSystems.Sldr`
*after* the call under test, never by restating an argument passed in. The
`Sldr` binding in the live test is imported independently of
`FLExInit`'s own module global.

| Point in the cycle | `Sldr.IsInitialized` | `Sldr.LanguageTags.Count` |
|---|---|---|
| Process start, before any init (separate cold process) | `False` | n/a |
| After `FLExInitialize()` | `True` | 9596 |
| After a 2nd `FLExInitialize()` (must be a no-op, must not raise) | `True` | 9596 |
| After `FLExCleanup()` | `False` | n/a |
| After a 2nd `FLExCleanup()` (the new guard; this raised before the fix) | `False` | n/a |
| After `FLExInitialize()` again | `True` | 9596 |

Cold-process confirmation of the `FLExCleanup()` guard, run outside pytest
so the SLDR was genuinely down:

```
cold IsInitialized = False
FLExCleanup() on cold SLDR: no raise; IsInitialized = False
after FLExInitialize: IsInitialized = True LanguageTags.Count = 9596
```

`LanguageTags.Count == 9596` before and after the teardown/re-init cycle is
the load-bearing number: it shows the re-initialized SLDR is genuinely
functional, not merely a flipped flag. A dead-but-flagged SLDR is what
causes liblcm to rename a project's `.ldml` files to `.ldml.bad` and
re-synthesize writing systems from defaults, which is the failure mode #249
was filed for.

## Regression pin for the original bug

`tests/test_249_sldr_init_guard.py::TestFLExInitializeExceptionDiscrimination::test_real_invalid_operation_failure_propagates`
is the assertion that would have caught the original defect: an
`InvalidOperationException` whose `Message` is *not* "already been
initialized" now propagates out of `FLExInitialize()` with object identity
preserved, where the previous bare `except Exception` downgraded it to a
warning misattributed as "already initialized?". The benign
check-then-act race message is still swallowed
(`test_race_with_already_initialized_message_is_swallowed`), and three
non-`InvalidOperationException` types are pinned as propagating.

## Session hygiene

The live module tears the SLDR down on purpose, so it restores it in a
`finally:` and again in an autouse fixture, matching
`flexicon/tests/test_FLExInit.py:34`. Verified: `IsInitialized` is `True`
at the end of the live session, and the 15-test mixed run confirms later
tests in the same session are unaffected.

## Result

PASS: verified live. `run_mode == "live"`; 12 offline + 3 live tests pass;
pre- and post-state read back from the CLR; no regression in
`flexicon/tests/test_FLExInit.py` or the `flexlibs2` alias ratchet.

## Addendum -- pre-fix / post-fix differential (added by the integrating session)

The offline suite's `patched_flexinit` fixture originally patched
`FLExInit.System` with `monkeypatch.setattr(..., raising=True)`. Run against
the pre-fix `FLExInit.py` (which has no `import System`) all 12 tests raised
`AttributeError` during **setup**, i.e. they reported 12 ERRORS about a
missing attribute and said nothing whatsoever about behaviour. A suite that
errors on scaffolding is not a regression pin: it proves the module changed,
not that the defect is gone.

The fixture now passes `raising=False`, so the tests execute against the old
code and fail on the actual swallowed exception. Differential, same suite:

```
git stash push flexicon/code/FLExInit.py     # revert to the pre-fix module
python -m pytest tests/test_249_sldr_init_guard.py -q
    -> 8 failed, 4 passed in 0.57s
       FAILED ...::test_already_initialized_sldr_is_not_reinitialized
       FAILED ...::test_repeated_calls_initialize_only_once
       FAILED ...::test_real_invalid_operation_failure_propagates   <-- #249 pin
       FAILED ...::test_non_invalid_operation_failure_propagates[runtime]
       FAILED ...::test_non_invalid_operation_failure_propagates[os]
       FAILED ...::test_non_invalid_operation_failure_propagates[value]
       FAILED ...::test_cold_sldr_skips_cleanup_without_raising
       FAILED ...::test_double_cleanup_does_not_raise

git stash pop                                 # restore the fix
python -m pytest tests/test_249_sldr_init_guard.py -q
    -> 12 passed in 0.53s
```

`test_real_invalid_operation_failure_propagates` fails pre-fix with
DID NOT RAISE -- the bare `except Exception` swallowed the genuine failure,
which is exactly the #249 defect. That transition (8 behavioural failures ->
0) is the load-bearing evidence that the fix changes behaviour and that the
suite would catch a reintroduction.

Re-verification after the fixture change:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_249_sldr_init_live.py -m requires_live_project -q
    -> 3 passed in 0.83s
    -> tests/live_status.json  "run_mode": "live"

python -m pytest flexicon/tests/test_FLExInit.py tests/test_flexlibs2_alias_ratchet.py tests/test_commit_msg_guard.py -q
    -> 26 passed in 1.83s
```

PASS: live verified, run_mode live, differential pin confirmed.
