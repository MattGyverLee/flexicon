# Live evidence -- #545 sense DoNotPublishIn

Date: 2026-09-26
Branch: `fix/545-sense-donotpublishin` (worktree `C:\Github\flexicon-545`, based on `origin/main` 5b2631a)
Fixture: `target_sandbox` (tempdir copy of `Target 2026-07-06 0218.fwbackup`; one publication, "Main Dictionary")

## Commands

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue545_sense_donotpublishin_live.py tests/operations/test_issue338_publication_defaults_live.py -m requires_live_project -q
```

Result: `9 passed in 3.89s`

`tests/live_status.json`: `"run_mode": "live"`

```
python -m pytest -m "not requires_live_project" -q
```

Result: `4 failed, 2493 passed, 1039 deselected`. The 4 failures are all in
`tests/operations/test_morphrule_duplicate_deep.py` and fail identically on
clean `origin/main` with this change stashed (`4 failed, 1 passed`): they were
already failing and are unrelated to this change.

## Pre/post values read back from the LCM

Each value re-queried after the write (`LexEntry.Find` / `cast_to_concrete(project.Object(hvo))`):

| Step | Re-read `DoNotPublishInRC` |
|------|----------------------------|
| `LexEntry.Create(..., create_blank_sense=True)` -- entry | `['Main Dictionary']` (#338 default kept) |
| same -- blank sense | `[]` (was `['Main Dictionary']` before this change) |
| `Senses.Create(entry, gloss)` | `[]` |
| `Senses.AddDoNotPublishIn(hvo, "Main Dictionary")` | `['Main Dictionary']`; `GetDoNotPublishIn(hvo)` -> `['Main Dictionary']` |
| `Senses.RemoveDoNotPublishIn(hvo, pub_obj)` | `[]` |
| `LexEntry.RemoveDoNotPublishIn(entry, pub)` (opt entry in) | entry `[]`, both senses `[]` |

## Negative control

With the `LexEntryOperations.py` part of the change reverted, the same live
run gives `3 failed, 6 passed`. The failures include
`test_opting_entry_into_publication_publishes_its_senses`: before this change,
opting an entry into a publication left its blank sense excluded there.

PASS
