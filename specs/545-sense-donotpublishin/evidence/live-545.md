# Live evidence -- #545 sense DoNotPublishIn; back out the #338 default

Date: 2026-09-26
Branch: `fix/545-sense-donotpublishin` (worktree `C:\Github\flexicon-545`, based on `origin/main` 5b2631a)
Fixture: `target_sandbox` (tempdir copy of `Target 2026-07-06 0218.fwbackup`; one publication, "Main Dictionary")

## Commands

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue545_sense_donotpublishin_live.py tests/operations/test_issue338_publication_defaults_live.py -m requires_live_project -q
```

Result: `8 passed in 3.64s`. `tests/live_status.json`: `"run_mode": "live"`.

```
python -m pytest -m "not requires_live_project" -q
```

Result: `4 failed, 2493 passed, 1038 deselected`. All 4 failures are in
`tests/operations/test_morphrule_duplicate_deep.py` and fail the same way on clean
`origin/main` with this change stashed. They were already failing and are unrelated.

## Pre/post values read back from the LCM

Each value was re-queried after the write (`LexEntry.Find` / `cast_to_concrete(project.Object(hvo))`).

Defaults (`test_issue338_publication_defaults_live.py`): after creation, the re-read
`DoNotPublishInRC` is `set()` for `LexEntry.Create` (entry and blank sense),
`LexEntry.AddSense`, `Senses.Create`, `Senses.CreateSubsense` (parent and child),
`Examples.Create` and `Senses.AddExample`. Under the #338 default, entries and
examples re-read as `{Main Dictionary}`.

Sense methods (probe run earlier in this session on the same fixture):

| Step | Re-read `DoNotPublishInRC` |
|------|----------------------------|
| `Senses.Create(entry, gloss)` | `[]` |
| `Senses.AddDoNotPublishIn(hvo, "Main Dictionary")` | `['Main Dictionary']`; `GetDoNotPublishIn(hvo)` -> `['Main Dictionary']` |
| `Senses.RemoveDoNotPublishIn(hvo, pub_obj)` | `[]` |

Adding again by object and removing again by name are no-ops, and an unknown
publication name raises `FP_ParameterError`. Both are asserted in
`test_issue545_sense_donotpublishin_live.py`.

PASS
