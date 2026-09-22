# Cycle 2 Propagation Report

**Date:** 2026-09-22 | Source: cycle1-audit.md Bucket A + constitution.md Principle II

Note: the reporting agent (lex-doc) applied the edits below but did not write this
file despite reporting that it had; the main session persisted it from the agent's
returned text. The file edits themselves were verified present in `git status`.

## Files edited

- `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md` (~line 37): replaced single offline "required
  invocation" with both required invocations per Principle II.
- `docs/FLEXTOOLSMCP_WRITE_CONTRACT.md` (~line 56/67, now one paragraph): reworded the
  `--ignore=tests/contract` prohibition's reason from "performs live LCM writes against
  a real project" to "unscoped collection" (Sena 3 in-place writes are now sanctioned;
  the hazard is running unscoped rather than against a chosen `-m`-selected live file).
- `docs/RELEASING.md` (~line 232): added a line under the offline-suite checklist item
  cross-referencing the live invocation as the required second half per Principle II,
  and reworded the `--ignore=tests/contract` hazard to "unscoped" rather than implying
  writing itself is the danger.

## Files given a superseding note (text preserved below, unedited)

- `specs/write-path-transactions/plan.md`
- `specs/write-path-transactions/spec.md`
- `specs/lcm-member-truth-sweep/STATUS.md`
- `specs/lcm-member-truth-sweep/spec.md`
- `specs/242-paragraph-whitespace/tasks.md`
- `specs/243-closeproject-save-guard/tasks.md`

Each got a blockquote immediately above its title line, dated 2026-09-22, naming the
constitution amendment, summarizing what the frozen text below it got wrong by today's
rule, and stating the original text is retained as historical record. No other line in
these six files was touched.

## Proposed CLAUDE.md diff (NOT applied -- awaiting user approval)

File: `D:\Github\_Projects\_LEX\flexicon\CLAUDE.md`, lines ~124-151.

BEFORE:

    ### The two live projects

    | Project | Contents | Use for | Restore |
    |---------|----------|---------|---------|
    | **Target** | Mostly blank scratch | **Write-path work**: create / modify / delete against a clean slate | `python scripts/restore_target.py` |
    | **Sena 3** | Fully populated example | Read-path coverage, modify-pre-existing-data | `python scripts/restore_sena3.py` |

    Default to **Target** for anything that writes. Reach for Sena 3 only when
    the test genuinely needs pre-existing data to read or modify.

    ### The required invocation

    ```
    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    python -m pytest <your live test file> -m requires_live_project -q
    ```

AFTER:

    ### The two live projects

    Reads are unrestricted: any project on the machine may be opened read-only,
    at any time, with no gate. What is gated is the **write target** -- writes
    land only on a project that is expendable and restorable.

    | Project | Contents | Use for | Restore |
    |---------|----------|---------|---------|
    | **Target** | Mostly blank scratch | **Write-path work**: create / modify / delete against a clean slate; the default when a test creates its own data | `python scripts/restore_target.py` |
    | **Sena 3** | Fully populated example | Safe for reads and edits **in place, at any time**; the right choice when a test needs pre-existing data to modify rather than data it created itself | `python scripts/restore_sena3.py` |

    Target is the default for write-path work, not a mandate -- Sena 3 is
    equally sanctioned for in-place writes whenever the test needs existing
    data.

    ### The two required invocations

    ```
    python -m pytest -m "not requires_live_project" -q
    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    python -m pytest <your live test file> -m requires_live_project -q
    ```

    Both are required and every brief quotes them explicitly. The offline run
    is the fast/default gate for non-write-path work; the live run is REQUIRED,
    performed unattended (no human gate), for any change touching an Operations
    class, a factory call, a property setter, `FLExProject`, or the
    transaction/write path.

Reason not applied: CLAUDE.md is the user's binding runtime contract per the LEX crew
protocol and is amended only on the user's own instruction, not a specialist report.

NOTE (added by main session): the cycle-2 read-scope sweep independently found the same
`### The two live projects` section is ALSO a read-confinement defect, and proposes
retitling it "The two live **write** projects". Merge that with the diff above before
applying -- see `cycle2-read-scope.md`.

## Bucket A rows declined / not applicable to this brief

None declined -- all rows assigned to this brief's scope
(FLEXTOOLSMCP_WRITE_CONTRACT.md, RELEASING.md, and the six superseding-note files) were
applied. Rows targeting `C:\Users\thoua\.claude\*` and `flexicon\CLAUDE.md` were out of
scope per explicit instruction (escalated / proposed-diff-only respectively).

## Files touched

- docs\FLEXTOOLSMCP_WRITE_CONTRACT.md
- docs\RELEASING.md
- specs\write-path-transactions\plan.md
- specs\write-path-transactions\spec.md
- specs\lcm-member-truth-sweep\STATUS.md
- specs\lcm-member-truth-sweep\spec.md
- specs\242-paragraph-whitespace\tasks.md
- specs\243-closeproject-save-guard\tasks.md

No commit was made (per instruction).
