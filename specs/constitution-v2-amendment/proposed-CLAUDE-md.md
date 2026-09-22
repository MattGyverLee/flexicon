# Proposed `flexicon/CLAUDE.md` edit — MERGED, awaiting user approval

Date: 2026-09-22. Status: NOT APPLIED.

Two cycle-2 reviews converged on the same nine lines from different directions:
`cycle2-propagation.md` rewrites the section for the WRITE rule; `cycle2-read-scope.md`
found the same section is ALSO a read-confinement defect. This is the single merged
diff lex-lead asked for — do not apply either source version separately.

## Hunk 1 — lines ~124-132

### BEFORE

    ### The two live projects

    | Project | Contents | Use for | Restore |
    |---------|----------|---------|---------|
    | **Target** | Mostly blank scratch | **Write-path work**: create / modify / delete against a clean slate | `python scripts/restore_target.py` |
    | **Sena 3** | Fully populated example | Read-path coverage, modify-pre-existing-data | `python scripts/restore_sena3.py` |

    Default to **Target** for anything that writes. Reach for Sena 3 only when
    the test genuinely needs pre-existing data to read or modify.

### AFTER

    ### The two live write projects

    **Reads are unrestricted.** Any project on the machine may be opened
    read-only, at any time, with no gate -- which project holds a given element
    is not knowable without looking. The table below allocates the two projects
    that are safe to **write** to; it is not a list of what may be read.

    | Project | Contents | Use for | Restore |
    |---------|----------|---------|---------|
    | **Target** | Mostly blank scratch | **Write-path work**: create / modify / delete against a clean slate; the default when a test creates its own data | `python scripts/restore_target.py` |
    | **Sena 3** | Fully populated example | Safe for reads and edits **in place, at any time**; the right choice when a test needs pre-existing data to modify rather than data it created itself | `python scripts/restore_sena3.py` |

    Target is the default for write-path work, not a mandate -- Sena 3 is
    equally sanctioned for in-place writes whenever the test needs existing
    data. Where a test needs data that does not exist, add it to Target or copy
    an existing project; never repurpose or destroy data another test reads.

## Hunk 2 — lines ~146-151

### BEFORE

    ### The required invocation

    ```
    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    python -m pytest <your live test file> -m requires_live_project -q
    ```

### AFTER

    ### The two required invocations

    ```
    python -m pytest -m "not requires_live_project" -q
    $env:FLEXLIBS_REQUIRE_LIVE = "1"
    python -m pytest <your live test file> -m requires_live_project -q
    ```

    Both are required and every brief quotes them explicitly. The offline run is
    the gate for non-write-path work; the live run is REQUIRED and performed
    unattended -- no human gate -- for any change touching an Operations class, a
    factory call, a property setter, `FLExProject`, or the transaction/write
    path.

## Also awaiting approval — user global config, outside this repo

`C:\Users\thoua\.claude\agents\lex-verification.md`

- `:39-44` — same "The two live projects" heading and table. Add one line: reads may
  target any project; the table bounds writes. Keep `:44`'s write content intact.
- `:197-199` — "The change requires a destructive write a human must authorize" and
  "Per the LEX crew protocol this is a needs_human handoff." Both now void; scope
  needs_human to locked-project / FieldWorks-absent only.

`C:\Users\thoua\.claude\agents\lex-lead.md`

- `:167` — needs_human defined as "a human decision OR a DESTRUCTIVE live-LCM write".
  Drop the second arm.
- `:169` — "Never perform a destructive live write unattended". Replace: writes to
  Target / Sena 3 / sandbox are performed unattended.
- `:211` — "the fix needs a human decision / destructive live write". Strike the
  second arm.

`C:\Users\thoua\.claude\CLAUDE.md`

- `:96-97` — the ralph-loop halt. Keep STOP for genuine decisions; remove "Never let
  the loop perform a destructive live-LCM write unattended", which currently prevents
  the unattended live testing the owner has asked for.
