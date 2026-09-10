# Live verification -- issue #307

Fixture reach for `initialize_flex_for_tests` outside the `tests/` subtree.

## What was wrong

`tests/conftest.py` held the session-scoped autouse FLEx-init fixture, the
shared mock/sandbox fixtures, and the hooks that write
`tests/live_status.json`. A conftest.py registers all of that only for its
own directory subtree, so `flexicon/tests/` and `flexicon/sync/tests/` --
which sit outside `tests/` -- got none of it.

## Pre-state (reproduction on `main`, commit 3fbc922)

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest flexicon/tests/test_FLExProject.py -m requires_live_project -q
```

```
E  TypeError: Exception has been thrown by the target of an invocation.
   flexicon\code\FLExLCM.py:61: TypeError
       projectsPath = FwDirectoryFinder.ProjectsDirectory
3 failed in 0.59s
```

`tests/live_status.json` was **not written at all** -- the evidence file the
project's own verification gate depends on. FLEx was never initialized.

## The rejected fix

Issue #307's "Suggested fix" (and PR #308, which restated it) proposed
`pytest_plugins = ("tests.conftest",)` in each of the two directories.
That passes a narrow run but **breaks the full-suite run**, because
`pytest_plugins` is only legal in the top-level conftest:

```
python -m pytest -q --collect-only
ERROR flexicon/sync/tests - Failed: Defining 'pytest_plugins' in a non-top-level conftest is no longer supported
ERROR flexicon/tests   - Failed: Defining 'pytest_plugins' in a non-top-level conftest is no longer supported
!!! Interrupted: 2 errors during collection !!!
```

Declaring it in a root `conftest.py` while the machinery stayed in
`tests/conftest.py` fails differently -- the same module cannot be both a
conftest and a named plugin:

```
ValueError: Plugin already registered under a different name:
  C:\Github\flexicon\tests\conftest.py=<module 'tests.conftest'>
```

## The applied fix

- `tests/conftest.py` -> `tests/flex_plugin.py` (a real plugin module).
- New thin `tests/conftest.py` keeps only `collect_ignore`, which pytest
  resolves relative to its own conftest and so cannot move.
- New root `conftest.py` declares `pytest_plugins = ("tests.flex_plugin",)`.
- Folded the dead `pytest_configure` (the sys.path bootstrap at old
  line 35) into the surviving one at old line 286, which had silently
  shadowed it since both were defined in the same module.

## Post-state

Command:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest flexicon/tests/test_FLExProject.py tests/operations/test_target_live_smoke.py -m requires_live_project -q
```

```
......                                                    [100%]
6 passed in 2.51s
```

`tests/live_status.json` read back after the run:

```
run_mode: live
tests:    6
```

The literal command from #307 now initializes FLEx with no `-p tests.conftest`.

SLDR init path (#249 regression, same fixture):

```
python -m pytest tests/operations/test_249_sldr_init_live.py -m requires_live_project -q
3 passed in 0.83s
run_mode: live
```

## Regression coverage

`flexicon/tests/test_conftest_reach.py` and
`flexicon/sync/tests/test_conftest_reach.py` -- one per affected subtree,
since per-subtree reach is exactly what regressed. Each asserts the plugin
is registered, that `flex_plugin._LCM_MODE` moved off its `"unknown"`
initial value (which happens only if the fixture actually executed), and
that plugin-defined fixtures resolve from that directory.

Confirmed these fail without the fix -- with the root `conftest.py` moved
aside:

```
FAILED flexicon/tests/test_conftest_reach.py::...::test_root_conftest_registers_the_flex_plugin
FAILED flexicon/tests/test_conftest_reach.py::...::test_session_fixture_actually_ran
FAILED flexicon/tests/test_conftest_reach.py::...::test_shared_fixtures_are_available_here
3 failed in 0.53s
```

## Non-regression

| Check | Result |
|---|---|
| Full-root collection, `main` | 2575 collected |
| Full-root collection, fixed | 2581 collected (= 2575 + 6 new) |
| Offline suite (`-m "not requires_live_project"`) | 1833 passed, 2 failed |
| `flexicon/sync/tests/` targeted | 176 passed |
| `tests/` targeted | 1644 passed, 2 failed |

The 2 failures are `tests/test_docstring_example_ratchet.py`
(`test_no_new_broken_examples`, `test_baseline_has_no_stale_entries`).
Pre-existing and unrelated: their failure output was diffed against a clean
`main` checkout and is byte-identical.

## Verdict

PASS -- verified live, `run_mode: "live"`.
