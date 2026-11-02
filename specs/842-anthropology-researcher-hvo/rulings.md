# Issue #842 -- lex-lead ruling

**Date:** 2026-11-02  
**HEAD:** fix/842-anthropology-researcher-hvo from origin/main

## Triage (cron)

- Open **P0** bugs without an open PR: **none**
- Open **P1** bugs without an open PR: **none**
- Open **P2** bugs #833, #834, #836, #840 each have open non-draft PRs (#837–#839, #841).
- Open **P3** bugs without an open PR: **none**
- **#776** / **#826** remain open but fixes already landed on main via PR #827; no unfixed code path selected.
- Selected **#842**: `AnthropologyOperations.AddResearcher` / `RemoveResearcher` still use `ResearchersRC.Contains` / bare `.Remove` on main -- sibling gap from #708 DataNotebook ResearchersRC family.

Untrusted open issues (#633 upstream-watch, etc.) ignored per automation policy.

## RULING (binding)

1. In `AddResearcher`, treat the person as already linked when any member of
   `item.ResearchersRC` has the same `Hvo` as the caller's person object; do
   not use `ResearchersRC.Contains`.
2. In `RemoveResearcher`, iterate `ResearchersRC`, find the member whose `Hvo`
   matches, and pass that member reference to `Remove`; raise `FP_ParameterError`
   when no member matches.
3. Tag both lookups with `issue #842` in comments.
4. Do not refactor unrelated AnthropologyOperations paths in this PR.

**Out of scope:** Other RC/OS membership sites; live proof in cloud (document `FAIL: unverified` when FieldWorks absent).

## Verification plan

- Offline: `python -m pytest tests/operations/test_issue842_anthropology_researcher_hvo_offline.py -m "not requires_live_project" -q`
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest tests/operations/test_issue842_anthropology_researcher_hvo_live.py -m requires_live_project -q` on `target_sandbox`.
