# Issue #264 cycle1 audit — how widespread is each pattern?

## Q1: unguarded init calls outside FLExInit.py
Searched tests/, flexicon/, scripts/, examples/, all conftest.py for
`Sldr.Initialize`, `Sldr.Cleanup`, `FwUtils.InitializeIcu`,
`FwRegistryHelper.Initialize` in executable code (docs/CHANGELOG/md excluded).

- `tests/conftest.py:116` `FwRegistryHelper.Initialize()` — unguarded, single caller.
- `tests/conftest.py:130` `FwUtils.InitializeIcu()` — unguarded, single caller.
- `tests/conftest.py:134-142` — the line the issue cites (`Sldr.Initialize(True)` at
  135) is now a **comment**, not an executable call ("issue #264: do NOT call
  Sldr.Initialize() here..."). No live `Sldr.Initialize` call remains at this line —
  re-verify against current HEAD before treating the fix as still needed here.
- `flexicon/code/FLExInit.py:90` `Sldr.Initialize(True)` — sole guarded call
  (IsInitialized probe, lines 85-90).
- `flexicon/code/FLExInit.py:121` `Sldr.Cleanup()` — sole guarded call (117-121).
- No other hits under tests/, flexicon/, scripts/, examples/; all remaining matches
  are docs/*.md, CHANGELOG.md, RELEASE_NOTES*.md, specs/**/*.md.

**Not widespread.** FLExInit.py is the only executable owner of these calls; the
conftest.py raw call the issue names appears already neutralized (now a comment).

## Q2: missing `requires_live_project` marker — complete list
No `pytest_collection_modifyitems` hook exists anywhere (0 hits) — markers are never
auto-applied by path; every application is a manual `pytestmark =` or
`@pytest.mark.requires_live_project`.

**True positives (missing marker, real live-project access):**
1. `flexicon/tests/test_FLExInit.py:26,34` — calls `FLExInitialize()`/`FLExCleanup()`
   directly; no marker anywhere in file.
2. `flexicon/tests/test_FLExProject.py:36,46` — `fp.OpenProject(projectName,...)`
   against the first real project from `AllProjectNames()`; no marker in file.
3. `tests/test_pattern_writing_systems_enumeration.py:111` —
   `TestWritingSystemsLiveSmoke.test_getsyncableproperties_calls_succeed(self,
   sena3_sandbox)` uses the write-enabled `sena3_sandbox` fixture; no `pytestmark`,
   no decorator (rest of file, lines 1-102, is a pure static scanner, correctly
   unmarked — only this class needs it).

**Already fixed (issue's own named example, contra the issue text):**
- `flexicon/sync/tests/test_base_operations.py:38` — `pytestmark =
  pytest.mark.requires_live_project` IS present, comment cites issue #264 by number.
  `setUpModule()` (line 55) opens "Sena 3" write-enabled. No longer an example of the
  oversight — issue may have been filed against a stale revision.
- `flexicon/sync/tests/test_duplicate_operations.py:38` — also already marked.

**Borderline, not counted:** `tests/test_headless_lcm_ui.py:245,269,300` opens a
nonexistent project name (tests failure path only); `tests/operations/
test_issue272_service_locator_seam.py:461` calls guarded `FLExInitialize()` only for
type imports, opens no project.

**False positives eliminated by inspection** (grep hit, verified mock-only):
`flexicon/sync/tests/{test_match_strategies,test_merge_ops,test_selective_import,
test_sync_engine,test_validation}.py` (Mock()-based; `target_project`/`sena3_sandbox`
are Mock attribute names, not fixtures); `tests/operations/test_transaction_rollback.py`;
`tests/test_249_sldr_init_guard.py`; `tests/test_custom_field_create_refusal.py`;
`tests/test_from_open_project.py` (substring match on `FromOpenProject`);
`tests/test_transaction_honesty.py`; `tests/test_undo_redo.py`;
`tests/write_path_transactions/test_a3_abort_session.py` (comment-only mentions).

**Deliverable: 3 confirmed missing-marker files/classes**, not 1. The issue's named
file is already fixed; two others plus one live-smoke class are unmentioned by the
issue and remain unmarked.

## Q3: all conftest.py files
Exactly two in the repo:
- `tests/conftest.py` — owns FLEx/SLDR init (`initialize_flex_for_tests`, 64-281),
  registers `requires_live_project`/`live_phase` markers (286-306), defines
  `sena3_sandbox`/`target_project`/`target_sandbox`/`target_sandbox_undoable`/
  `target_sandbox_path` fixtures (1284-1619).
- `tests/contract/conftest.py` — overrides `initialize_flex_for_tests` as a no-op
  (14-21); performs no init itself.

No conftest.py exists under `flexicon/tests/`, `flexicon/sync/tests/`, or elsewhere —
those dirs rely on `tests/conftest.py` plus pyproject.toml's globally-registered
marker (pyproject.toml:83-92 explains why: conftest.py marker registration is
subtree-scoped, so out-of-tree dirs needed the global declaration).

## Q4: collection-order randomization
No `pytest-randomly`/`pytest-random-order` in requirements.txt or installed (`pip
show` → "Package(s) not found" for both). No `pytest.ini`/`setup.cfg`/`tox.ini`.
`pyproject.toml`'s `[tool.pytest.ini_options]` (83-92) sets only `markers`; **no
`addopts` key exists at all** — default pytest collection order applies
(filesystem/alphabetical per directory; deterministic on one machine, not guaranteed
stable across OS/filesystem).

To reproduce two orders: no shuffle flag exists today. Either pass explicit differing
file-order args on the CLI, or temporarily `pip install pytest-randomly` (not
currently a dependency) for `-p randomly --randomly-seed=N`. Since no randomization
plugin is configured, the order-dependence issue #264 describes is latent (depends on
which unmarked live test collects first), not actively exercised by CI today.
