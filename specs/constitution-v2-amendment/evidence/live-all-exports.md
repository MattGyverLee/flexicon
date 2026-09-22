# Live verification — spurt 1 (constitution v2.1.0 + `__all__`)

Date: 2026-09-22. Task: T2 (`__all__` added to `flexicon/__init__.py`).
Gate: constitution Principle II, Quality Gate 1.

## Change under verification

`flexicon/__init__.py` gains `__all__` (99 names). This is the only code change in
the spurt; the other 10 modified files are documentation and spec records. `__all__`
alters what `from flexicon import *` exposes and is evaluated at import time, so it
can break collection for the entire suite -- hence both halves of Gate 1 were run.

## Invocation 1 — offline suite

```
python -m pytest -m "not requires_live_project" -q
```

Result: **3 failed, 2033 passed, 893 deselected, 13 warnings in 29.63s**. Exit 0.

All three failures are PRE-EXISTING and unrelated to this change. None of the
implicated source files appears in `git diff --name-only HEAD`:

| test | reason | implicated file (unmodified) |
|---|---|---|
| `TestContractStability::test_no_new_type_dependencies` | new LCM deps `ICmDomainQ`, `ICmDomainQFactory` absent from contract baseline | `flexicon/code/Lexicon/SemanticDomainOperations.py` |
| `TestLiveRegressionCheck::test_no_regressions_from_baseline` | `IRnResearchNbkRepository` present in baseline, now missing from liblcm snapshot | liblcm reflection, no flexicon file |
| `TestUnbracketedMutationRatchet::test_no_new_unbracketed_mutations` | 4 new unbracketed LCM mutation sites vs the frozen baseline | `BaseOperations.py:3210`; `Notebook/DataNotebookOperations.py:224,248`; `Notebook/NoteOperations.py:829` |

The third is a standing write-path gap on `main` (decision D5 requires every LCM
mutator to run inside `_TransactionCM`). Recorded here as observed; out of scope for
this spurt and not addressed by it.

## Invocation 2 — live suite

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_target_live_smoke.py -m requires_live_project -q
```

(POSIX env-prefix form of the documented
`$env:FLEXLIBS_REQUIRE_LIVE = "1"`; the variable set is identical.)

Result: **3 passed in 6.35s**. Exit 0.

`tests/live_status.json` -> `"run_mode": "live"`, `"run_timestamp": "2026-09-22T15:55:55Z"`.
Not mock mode. `FLEXLIBS_REQUIRE_LIVE=1` was set, so a mock fallback, a locked Target
or a missing fixture would have been a hard failure rather than a silent pass.

### Live reads

- `TestTargetFixturesReachLiveLCM::test_target_project_opens_write_enabled` -- pass.
  Real Target opened write-enabled.
- `TestTargetFixturesReachLiveLCM::test_target_sandbox_opens_write_enabled` -- pass.
  Tempdir sandbox opened write-enabled.

Recorded in `live_status.json` under `FLExProject.read`, `last_verified 2026-09-22`.

### Live write — create/delete round trip

`TestTargetSandboxRoundTrip::test_create_and_delete_entry_in_sandbox` -- pass, 0.238s.
Recorded under `LexEntryOperations.add`, `last_verified 2026-09-22`.

- **Pre-state:** `before = len(list(target_sandbox.LexEntry.GetAll()))`, read from the
  LCM before the write.
- **Write:** `entries.Create(lexeme_form="TEST_smoke")`.
- **Post-state:** `after = len(list(entries.GetAll()))` -- **re-queried from the LCM
  after the write**, not asserted against the value passed in. Assertion
  `after == before + 1` passed, so the create reached the LCM.
- **Cleanup:** deletion in a `finally:`; target was a tempdir sandbox, so nothing
  could leak to the real Target.

## Scope and limits of this verification

This establishes that adding `__all__` did not break live project access, and that a
create/delete round trip still reaches and is visible in the LCM. It does **not**
verify each of the 99 exported names individually against a live object -- that is
the next spurt's work, where the surface baseline is built and its entries must be
confronted with the runtime rather than trusted from AST alone.

## Verdict

**PASS.** Both required invocations run, counts quoted in full, pre-existing failures
named and attributed, `run_mode` confirmed `live`, post-state re-queried from the LCM.
