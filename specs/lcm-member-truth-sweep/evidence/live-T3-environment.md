# Live verification -- T3.7, environment contexts survive Duplicate (#283)

**Project:** Sena 3 | **Fixture:** `sena3_sandbox` (tempdir copy of the
`.fwbackup`; nothing leaks to the real Sena 3 or Target)
**Commands:**
```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_lcm_member_truth_sweep.py -m requires_live_project -q
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_260_environment_resolver_gate.py -m requires_live_project -q
```
**run_mode:** `live` (confirmed via `tests/live_status.json` after every
invocation below)
**Date:** 2026-09-18

## Testbed deviation from tasks.md, recorded explicitly

`tasks.md` T3.7 nominally says `target_sandbox`. Target is "mostly blank
scratch" (CLAUDE.md) with no guaranteed phoneme inventory, and a legal
`IPhSimpleContextSeg` requires an existing `IPhPhoneme` assigned to
`FeatureStructureRA` -- an illegal (phonemeless) context object would prove
nothing. `sena3_sandbox` is the populated project and is the fixture the
programmer's own `test_2d` and the new
`test_left_context_returns_seeded_context_by_reference` already use
successfully for this exact seeding pattern. This deviation was authorized
by the dispatching agent for this campaign. Both live projects were used
exclusively through their sandbox (tempdir-copy) fixtures; the real Target
and real Sena 3 `.fwdata` files were never opened or written by this
verification pass.

## Claim under test

`EnvironmentOperations.Duplicate` now copies `LeftContextRA`/`RightContextRA`
by unconditional reference assignment (spec.md C7), so a duplicated
environment points at the SAME `IPhPhonContext` objects as its source --
proven by HVO identity after both objects are re-read fresh from the LCM,
not by comparing in-memory Python references.

## Run 1 -- test_lcm_member_truth_sweep.py::test_2d_seed_and_observe_duplicate_reference_semantics

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_lcm_member_truth_sweep.py -m requires_live_project -k test_2d -v -s
```
Result: **1 passed**. `tests/live_status.json` `run_mode`: `live`.

Captured LCM output (verbatim from the run):
```
[2d] source env hvo=152222
[2d] source LeftContextRA hvo=152223 ClassName=PhSimpleContextSeg
[2d] source RightContextRA hvo=152224 ClassName=PhSimpleContextSeg
[2d] duplicate env hvo=152225
[2d] duplicate LeftContextRA hvo=152223
[2d] duplicate RightContextRA hvo=152224
[2d] left same HVO (reference semantics): True
[2d] right same HVO (reference semantics): True
```

| Field | Pre-state (source, re-read) | Post-state (duplicate, re-read by its own HVO) | Equal? |
|---|---|---|---|
| env | hvo=152222 | hvo=152225 (new object, as expected) | n/a |
| LeftContextRA | hvo=152223 | hvo=152223 | YES |
| RightContextRA | hvo=152224 | hvo=152224 | YES |

Both LeftContextRA and RightContextRA on the duplicate are non-null and
HVO-identical to the source's, confirming reference (not clone) semantics.
The full file run (-m requires_live_project -q, no -k filter):
**19 passed**, run_mode: live.

## Run 2 -- test_260_environment_resolver_gate.py::TestP7DiscoveredWrongPropertyName

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_260_environment_resolver_gate.py -m requires_live_project -k TestP7DiscoveredWrongPropertyName -v -s
```
Result: **2 passed** (test_left_and_right_context_are_reference_atomic_not_owning_atomic
-- genuine no-context case, still None; and the new
test_left_context_returns_seeded_context_by_reference). run_mode: live.

This class's new test asserts result.Hvo == left_ctx.Hvo after a fresh
IPhEnvironment(project.Object(env_hvo)) re-read and a call to
GetLeftContextPattern, but (correctly, per its narrower scope) does not
itself exercise Duplicate. To close that specific gap -- proving
GetLeftContextPattern/GetRightContextPattern return the seeded context
AND that Duplicate propagates it, re-read by the duplicate's own HVO
-- I wrote a scratch test reproducing the identical seeding pattern plus a
Duplicate call, ran it live, and deleted it immediately after (no trace
left in the working tree; confirmed by git status --porcelain showing the
same 4 modified files before and after). Full command and captured output:

```
FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_zzz_scratch_evidence_T3.py -m requires_live_project -v -s
```
```
[scratch] env hvo=152222
[scratch] seeded left_ctx hvo=152223
[scratch] re-read GetLeftContextPattern hvo=152223
[scratch] HVO EQUAL: True
[scratch] duplicate env hvo=152224
[scratch] duplicate LeftContextRA hvo=152223
[scratch] duplicate == source LeftContextRA HVO: True
PASSED
```
run_mode: live (checked immediately after this run too).

| Field | Pre-state (source env, re-read by HVO) | Post-state (duplicate env, re-read by ITS OWN HVO) | Equal? |
|---|---|---|---|
| env | hvo=152222 | hvo=152224 (new object) | n/a |
| LeftContextRA (via GetLeftContextPattern) | hvo=152223 | hvo=152223 | YES, non-null |

The full gate file run (-m requires_live_project -q, no -k filter):
**7 passed**, run_mode: live.

## Action (exact API calls)

```python
env = envs.Create("TEST_...")
with envs._TransactionCM(...):
    left_ctx = ctx_factory.Create()          # IPhSimpleContextSegFactory
    phon_data.ContextsOS.Add(left_ctx)       # owned-object guard
    left_ctx.FeatureStructureRA = phoneme    # from IPhPhonemeRepository
    env.LeftContextRA = left_ctx
reread = IPhEnvironment(project.Object(env.Hvo))
result = envs.GetLeftContextPattern(reread)         # -> left_ctx, by HVO
dup = envs.Duplicate(reread)
dup_reread = IPhEnvironment(project.Object(dup.Hvo))
dup_left = envs.GetLeftContextPattern(dup_reread)   # -> SAME left_ctx, by HVO
```

## T3.6 confirmation (scope discipline, re-verified independently)

```
git diff --name-only | grep -E "compound_rule|PhonologicalRuleOperations"
```
returns nothing (exit code 1, no match). flexicon/code/Grammar/compound_rule.py
and flexicon/code/Grammar/PhonologicalRuleOperations.py are absent from
the diff, matching the programmer's T3.6 claim in cycle3-programmer.md.

## Cleanup

- test_2d's own finally: block ran unmodified (byte-for-byte per the
  programmer's T3.5(b) note) and removed both context objects and the
  duplicate/source environments from the sena3_sandbox tempdir copy.
- The new gate-file test's finally: block removed its seeded context and
  deleted its environment from the same tempdir copy.
- The scratch evidence test (test_zzz_scratch_evidence_T3.py) ran its own
  finally: cleanup (removed the seeded context, deleted both the
  duplicate and source environments) and the file itself was deleted
  immediately after the run. git status --porcelain before and after
  this verification pass shows the identical 4 modified tracked files
  (CHANGELOG.md, EnvironmentOperations.py,
  test_260_environment_resolver_gate.py,
  test_lcm_member_truth_sweep.py) plus the same pre-existing untracked
  files -- no residue.
- sena3_sandbox is a tempdir copy of the .fwbackup; its teardown
  deletes the tempdir outright. The real Sena 3 and Target projects were
  never opened or written.

## Offline regression cross-check (see cycle3-verification.md for full detail)

python -m pytest -m "not requires_live_project" -q (unrestricted, matching
the campaign's own convention in live-T2-notebook.md):
- Clean 994f2ee (via git worktree add, no destructive stash): **1878
  passed, 803 deselected, 0 failed**.
- Working tree (T3 changes applied): **1878 passed, 804 deselected, 0
  failed**. The +1 deselected is exactly the one new live test added in
  T3.5(a) (test_left_context_returns_seeded_context_by_reference); zero
  passed-count regression.

## Result

**[PASS]** -- run_mode: live on every invocation; environment contexts
(LeftContextRA/RightContextRA) are proven, by HVO re-read after
Duplicate and after a fresh IPhEnvironment(project.Object(hvo)) cast,
to be the SAME objects as the source's, non-null in both directions, and
GetLeftContextPattern/GetRightContextPattern return the seeded context
rather than None. Zero regressions in the offline suite.
