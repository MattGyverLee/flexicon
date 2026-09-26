# Live verification evidence -- issue #544 (MSA feature-structure getters)

## Commands run

```
python -m pytest -m "not requires_live_project" -q
```
Result: 2514 passed, 4 pre-existing failures (unrelated to this change,
in `tests/operations/test_morphrule_duplicate_deep.py`; confirmed
present on a clean `origin/main` checkout via `git stash` before this
change was applied -- see cycle1 review for the reproduction).

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_msa_feature_getters_live.py -m requires_live_project -q
```
(run via `export FLEXLIBS_REQUIRE_LIVE=1` in the bash tool actually used)

Result: 5 errors -- every test in the live file failed at fixture setup
(`sena3_sandbox`), NOT at any assertion in the new code.

## Blocker (live verification genuinely impossible on this machine)

1. `import SIL.LCModel` fails with `ModuleNotFoundError: No module named
   'SIL'` -- FieldWorks / the LCM Python.NET bindings are not installed
   on this worktree's machine.
2. `tests/fixtures/` does not exist at all in this worktree, so no
   `Sena 3*.fwbackup` is present for `sena3_sandbox` to restore from
   even if LCM were available.

`sena3_sandbox`'s own `_unavailable()` path enforces
`FLEXLIBS_REQUIRE_LIVE=1` -> hard `pytest.fail`, exactly as CLAUDE.md
requires -- it did NOT silently skip or fall back to a mock pass. The
failure output above is that hard failure, not a false green run.

## tests/live_status.json

Not created by this run (`sena3_sandbox` failed before any project
opened), consistent with `run_mode` never reaching `"live"`.

## Pre-state / post-state read back from the LCM

None available -- no live project could be opened, so no write, no
read-back, and no round-trip could be exercised against a real LCM
cache in this environment.

## Verdict

**FAIL: unverified.** This is a `needs_human` handoff per the LEX crew
protocol: live verification requires a machine with FieldWorks
installed and a `Sena 3*.fwbackup` placed in `tests/fixtures/` (or
`scripts/restore_sena3.py` prerequisites satisfied). The offline suite
(21 new tests in `tests/operations/test_msa_feature_getters.py`, plus
the full non-live suite) passes and exercises the dispatch logic, the
None/{} semantics, and the C4-to-MakeFeatStruc-shape converter via
monkeypatched BaseOperations seams -- but that is NOT a substitute for
live verification and is not being presented as one.

The five live tests in
`tests/operations/test_msa_feature_getters_live.py` are written and
ready to run (round-trip MakeFeatStruc -> GetXFeatures -> MakeFeatStruc
-> re-read for all four owning properties, plus a read-only sweep over
real Sena 3 MSAs) as soon as a live-capable environment is available.
