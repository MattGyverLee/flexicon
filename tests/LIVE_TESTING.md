# Live FieldWorks Testing Workflow

This suite ships a parallel "live-DB" testing track that exercises the
operations classes against a real `.fwdata` project on the developer's
machine. Live tests need FieldWorks installed and the project reachable
on disk -- they are skipped automatically in CI / mock-only environments,
unless `FLEXLIBS_REQUIRE_LIVE=1` is set (see below).

**Live LCM verification is REQUIRED for any change written against the
LCM.** A mock-only pass is not verification. See CLAUDE.md, "Live LCM
Verification (REQUIRED)", for the policy; this file is the mechanics.

## The two live projects

| Project | Contents | Use for | Restore |
|---------|----------|---------|---------|
| **Target** | Mostly blank scratch | **Write-path work**: create / modify / delete against a clean slate | `python scripts/restore_target.py` |
| **Sena 3** | Fully populated example | Read-path coverage, modify-pre-existing-data | `python scripts/restore_sena3.py` |

Default to **Target** for anything that writes: a leaked `TEST_` object is
obvious in a blank project, and its backup is ~1.3 MB against Sena 3's
~15 MB, so restores are cheap. Reach for Sena 3 only when the test needs
pre-existing data to read or modify.

`Test`, `SampleLexicon`, and `SampleLexicon3` remain as fallback candidates
in older per-module `writable_project` fixtures, but new live tests should
use the Target or Sena 3 fixtures below.

### Target fixtures

- `target_project` -- module-scoped, write-enabled, **in-place on the real
  Target**. Capture-and-restore in a `finally:`; prefix created objects
  `TEST_`.
- `target_sandbox` -- write-enabled on a fresh tempdir copy of the Target
  `.fwbackup`. Nothing can leak into a real project. Use it for
  destructive tests, and whenever an open FieldWorks holds the file lock
  on Target.

Both fail loudly rather than skipping when `FLEXLIBS_REQUIRE_LIVE=1`.

The canonical template is `tests/operations/test_target_live_smoke.py`.

### The Target fixture backup

`tests/fixtures/Target *.fwbackup` is gitignored (same convention as the
Sena 3 fixture). The golden copy lives at
`D:\Github\_Projects\_LEX\GramTrans\backups\Target 2026-07-06 0218.fwbackup`;
copy it into `tests/fixtures/` on a fresh checkout.

## Running the live suite

To run only the live tests:

    pytest -m requires_live_project

To run everything EXCEPT live tests (mock-only fast suite):

    pytest -m "not requires_live_project"

The unfiltered `pytest` invocation still collects both buckets, so the
existing CI behaviour is preserved.

## Fail-loud on mock fallback (REQUIRED for verification)

The session fixture in `tests/conftest.py` silently falls back to mock
mode when FieldWorks initialization fails (e.g. on a CI runner with no
FW install), printing `[WARN] MOCK MODE` and letting the session pass
green. That green wall is how unverified write-path changes have been
reported as done.

Any run whose purpose is to VERIFY a change must set:

    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    pytest -m requires_live_project

With it set, every silent degradation becomes a hard failure:

- FLEx initialization falling back to mocks -> `pytest.UsageError`
- Target locked by an open FieldWorks -> `pytest.fail` with the remedy
- Missing `.fwbackup` fixture -> `pytest.fail`, not a skip

## Confirming a run was actually live

`tests/live_status.json` records `run_mode`:

    python -c "import json;print(json.load(open('tests/live_status.json'))['run_mode'])"

`live` means the session reached a real LCM. `mock` means it degraded and
proved nothing. A verification claim must cite `run_mode: live`; anything
else is `FAIL: unverified`.

## Never run bare `pytest`

Neither bare `pytest` nor `pytest --ignore=tests/contract` applies an `-m`
filter, so both collect and EXECUTE the ~322 `requires_live_project`
tests -- Phases A-D of which run in-place against real projects. This has
happened twice in this repo's history. Always pass an explicit `-m`.

## Ledger and Markdown summary

After each run that actually executes one or more live tests,
`tests/conftest.py` writes `tests/live_status.json` -- a per-test and
per-class summary of pass / fail / skip outcomes. Pure mock runs do NOT
touch the file, so a CI run never overwrites a developer's live ledger.

Render the JSON as a human-readable Markdown table with:

    python scripts/render_live_status.py

The renderer also produces a "no data yet" stub if the JSON is missing
or empty, so the Markdown file is always present and well-formed.

## The two-marker pattern

There are two distinct markers:

* `requires_live_project` -- the **selector**. Every test that opens a
  real project is tagged with this so `pytest -m requires_live_project`
  / `pytest -m "not requires_live_project"` work as expected.

* `live_phase(operations_class, phase)` -- the **ledger metadata**.
  Records which Operations class and CRUD phase the test exercises.
  Valid phases: `read`, `add`, `reorder`, `modify`, `delete`. The
  session-finish hook aggregates per-(class, phase) status from these
  markers.

`live_phase` markers are populated incrementally. Existing tests do
**not** carry `live_phase` yet -- they appear under
"Uncategorized live tests" in `LIVE_STATUS.md` until they are
backfilled. This is expected for Cycle 1 of the rollout.

## Sena 3 fixture and restoration

The canonical live-test project is **Sena 3**. The golden fixture is
checked into `tests/fixtures/Sena 3 *.fwbackup` (gitignored, ~15 MB) and
is the source of truth between sessions. Phases B--D mutate the
in-place project; the restoration script wipes accumulated churn:

    # Restore Sena 3 from tests/fixtures/ into the FieldWorks projects dir
    python scripts/restore_sena3.py

    # Check current state without restoring
    python scripts/restore_sena3.py --check

    # Override target name / projects dir if needed
    python scripts/restore_sena3.py --target "Sena 3 Test" \
        --projects-dir "C:\Path\To\Projects"

Run this before every live session for a clean baseline. Re-run after
any session to discard test-induced timestamp / object churn.

## The five-phase stabilization model

Each operations class earns "stabilized" by passing every phase that
meaningfully applies to it:

| Phase | Pattern | Risk | Where it runs |
|-------|---------|------|---------------|
| A. Read | `writeEnabled=False`, call getters | None | In-place on real Sena 3 |
| B. Add | Create with `TEST_` prefix, verify, delete in `finally:` | Low | In-place on real Sena 3 |
| C. Reorder | Capture order, swap, restore | Medium | In-place on real Sena 3 |
| D. Modify | Capture value, set new, assert, restore captured | Medium | In-place on real Sena 3 |
| E. Delete pre-existing | Snapshot real project data, delete it, verify | High | **Sandbox copy via `sena3_sandbox`** |

### Philosophy: prefer self-cleaning in-place tests

Tests should leave the database in the same state they found it. The
default pattern in every phase is **capture-and-restore inside a
`try/finally`** -- create what you delete, capture what you mutate, undo
what you did. Mutations to the real Sena 3 are acceptable only when the
test removes them before exiting; LCM's auto-bump of `DateModified` is
the only residue, and `scripts/restore_sena3.py` wipes that between
sessions.

The `sena3_sandbox` fixture is the **exception**, not the rule. Use it
only when the test genuinely needs to do something that can't be
self-restored:

- Phase E (delete a pre-existing project object that the user wants
  preserved) -- the only common case.
- A regression test that must verify persistence across a project close
  and re-open in a state that would corrupt the real fixture.

If you find yourself reaching for `sena3_sandbox` to run a Phase B-style
create-and-delete test, the sandbox is buying you nothing -- write it
in-place against `writable_project` instead.

### When Phase E is N/A

If the operations class has zero pre-existing instances in Sena 3 (or
only items that other tests depend on), Phase E for that class has no
target. Mark the placeholder test `@pytest.mark.skip("N/A: ...")` with a
reason rather than fabricating a sandbox-only create-and-delete; the
Phase B coverage already proves Delete's behaviour. `LocationOperations`
is the canonical example (Sena 3 ships with zero locations).

## Canonical template

The canonical end-to-end template is
`tests/operations/test_locations_live.py`. Replicate its structure
(one class per phase, `live_phase` markers, `TEST_` prefix, finally
cleanup, optional `sena3_sandbox` fixture) when adding live coverage
for new operations classes.
