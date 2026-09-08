# CYCLE-5 VERIFICATION -- five-verifier independent swarm

**Date:** 2026-09-08. **HEAD:** `3d357d8`. **Dispatched by:** main session,
acting as lead (the `/lex-lead` and `/lex-doc` crew roles have no agent or
skill definition in this repo -- no `.claude/agents/`, no
`.claude/commands/` -- so the gate was run and ruled on directly).

**Posture:** five independent verifiers, adversarial, no numbers taken from
prior reports. Four read-only; the regression verifier was restricted to
`python -m pytest tests -m "not requires_live_project" -q`.

**Occasion:** `.crew-handoff.json` and `STATUS.md` both named the "cycle-3
independent verification gate" as this feature's sole remaining item. That
was **stale** -- `reviews/cycle3-verification.md:66` had already returned
`GATE: GREEN`, and the campaign record had already recorded
`feature_complete APPROVED by lex-lead`. This pass is therefore a SECOND,
independent gate over an already-green feature, not the first one.

## Per-verifier verdicts

| Verifier | Verdict | Substance |
|---|---|---|
| Code conformance (C8/C12/C10) | **PASS** | No divergence found |
| Live evidence (C28, fixtures, read-back) | **FAIL** | Evidence durability, not correctness |
| Docs (C9/C12/T3/T6) | **PASS** | 4 non-blocking gaps |
| Regression (offline baseline) | **FAIL** | Environmental blocker, not a regression |
| Scope discipline (C10/C11, no-touch) | **FAIL** | Record only; substance clean |

## What the code-conformance pass established (PASS)

All four sites match C8's binding shape; the non-`str` branch carries no
`.strip()` at any of them; `preserve_whitespace` appears in zero `.py`
files. C12's four-case algorithm is implemented exactly, and its no-strip
guarantee is **structurally** sound, not merely observed: `raw.rstrip()`
occurs once, wrapped in `len(...)`, so its string result is never bound to
a name and is unreachable; every `ReplaceTsString(n, n, ...)` is zero-width,
so deletion at the join boundary is not expressible. The `trail == 0`
inertness claim was hand-diffed against the pre-C12 source (`608200c^`)
case by case and holds. C10's 8 sibling sites are untouched and still
bug-shaped, with the `Exists()` co-location that justified the deferral
still factually present.

C1's HEAD line-number table is now stale at all four sites (up to +21
lines), from the fix's own inserted comments. Cosmetic; see C17.

## NEW findings this pass raised that the cycle-3 gate did not

### N1 -- `tests/live_status.json` is not a durable artifact (HIGH, record)

The file does not exist on disk, is gitignored (`.gitignore:99`), and has
never been committed. CLAUDE.md requires a verification claim to cite it
showing `"run_mode": "live"`; no evidence file quotes the JSON, and none
records the `run_timestamp` that would bind a claim to a specific run.

**This is a documentation-durability failure, NOT evidence of a mock run.**
Three independent things argue the runs were genuinely live: the
offline/live split is internally coherent (483 deselected offline vs 8
collected live, verified this pass by `--collect-only`); the LCM read-backs
are real re-queries, not echoes of the input (`test_p8` re-reads via
`project.Paragraphs.GetText(para)` after the write, and `test_p4` closes
and reopens the project first); and `reviews/cycle3-verification.md`'s own
pass reports reading the file's `by_test` map while it still existed. The
defect is that the claim cannot be re-derived from the repo today.
Recorded as **C16**.

### N2 -- C12's inertness claim is overstated (MEDIUM, record)

C12 and `evidence/live-t5-joinfix.md` assert all four `trail == 0` rows are
"byte-for-byte identical to cycle 2's post-T1/T2 behaviour." Cycle 2
measured only `"foo "` (`test_p8`) and `"Seed."` (`test_p2`). Three of the
four rows -- `''`, `'foo'`, `'foo!'` -- have no cycle-2 measurement to be
identical to. They are legitimate a-priori predictions that matched, but
1 of 4 rows is an actual byte-for-byte regression check, not 4 of 4.
The inertness conclusion still stands -- it is now carried by the
code-conformance hand-diff (above), which is a stronger proof than the
measurement anyway. Narrowed by **C15**.

### N3 -- the offline baseline is no longer reproducible (BLOCKING, environmental)

The machine's only interpreter is Python 3.14.5. `pyproject.toml` declares
`requires-python = ">=3.8,<3.14"` and pins `pythonnet >=3.0.3,<3.1`; only
pythonnet 3.1.0 has a 3.14 wheel. `import clr` therefore fails at
`flexicon/__init__.py:70`, 15 modules fail collection, and the suite never
reaches execution:

```
384 deselected, 7 warnings, 15 errors in 1.78s
Interrupted: 15 errors during collection
```

The 1292/483 baseline is **neither confirmed nor refuted** by this pass,
and zero tests ran against the changed code. Not attributable to #242: the
failure is an interpreter-level import at package `__init__`, hitting all
15 modules regardless of subject. The interpreter was replaced after the
baseline was recorded. Recorded as **C18**; this is a `needs_human`
handoff.

### N4 -- C14 was a phantom contract item (P1, record -- now fixed)

Commit `ed428f7`'s body claims "records C12/C13/C14 in the spec" and the
campaign record claims "Contract C1-C14 frozen", but `grep -n C14 spec.md`
returned **zero hits**. The underlying work had landed and is verified
(4/4 docstring notes present at HEAD); only the contract entry was
missing. An unwritten item cannot be cited or overturned by number, which
is the whole mechanism this feature's freeze discipline rests on. Written
as **C14** by this pass.

### N5 -- `tasks.md` stated the opposite of the truth (P1, record -- now fixed)

`tasks.md:6-9` read, in bold at the top of the file, `NO BEHAVIOUR CHANGE
UNDER flexicon/code/ HAS BEEN MADE YET -- git diff --stat -- flexicon/ is
empty`, refuted 160 lines below in the same file and by `STATUS.md:11-14`.
A reader after a context reset who trusted the top of the file could have
concluded the fix was unstarted and re-implemented it. Corrected.

### N6 -- `ed428f7` breached two no-touch constraints (P2, closed as spilt milk)

That commit edits `specs/tier1-silent-data-loss/.crew-handoff.json` (95
lines) against the prohibition at this feature's `.crew-handoff.json`, and
rewrites the campaign queue's `index: 3` / `index: 4` note fields against
`STATUS.md`'s hard constraints. Mitigating: the content self-attributes to
the main session and the closure itself was split into `249863d`, so this
reads as commit hygiene rather than an authorship breach, and it is
bookkeeping only -- no work on items 3 or 4 was started. Not repairable
without rewriting history; recorded, not remediated.

### N7 -- `066bab0` carries the auto-close keyword `closes #242` (P2, open)

This contradicts the campaign record's own "flexicon#242 left as-is. The
crew files and closes nothing." The no-*filing* rule held
(`github_issues_filed: []`, verified empty); the no-*closing* discipline
did not. `gh issue view 242` could not resolve the issue from this session,
so **whether #242 is actually closed on GitHub is UNVERIFIED here** and
needs a human check.

### N8 -- `AppendSentence`'s docstring summary contradicted its own Note (fixed)

`SegmentOperations.py:559-562` still stated the pre-C12 rule as current
(`'. '` always inserted; raw-last-character terminator test), contradicting
the `Note:` at :593-599. Pure-docs, no live verification required per
CLAUDE.md. Corrected by this pass.

## Verifier claims this pass did NOT accept

- The scope brief's `git diff --stat b28c8640^ HEAD -- flexicon/` is a
  **false-positive trap**: HEAD is a merge carrying the
  `flexlibs2 -> flexicon` rename (`ec54432`) and an unrelated
  `BaseOperations` refactor (`4aca74a`), so it reports ~82 changed files.
  Scope must be checked per-commit. Both affected verifiers were corrected
  mid-flight and re-derived the commit set independently; `4aca74a` was
  confirmed NOT a 242 commit.
- `.crew-handoff.json` recorded the cycle-3 fix as `608200c2`; git resolves
  the short SHA to `608200c`. Corrected in the handoff.

## Verdict

**Substance: GREEN.** Correct fix shape at all four sites, correct C12
algorithm with a structural no-strip guarantee, correct routing (Q-242A/B/C
appended with 49 insertions and ZERO deletions -- preceding entries
byte-identical), correct declines and deletions, C28 temporal order
provable from history at all three cycles, fixture safety absolute.

**Record: was RED, repaired by this pass** (C14-C18, `tasks.md`,
`STATUS.md`, `.crew-handoff.json`).

**Two items remain open and are NOT this pass's to close:**

1. **C18 / N3 -- the environment.** A human must restore a 3.8-3.13
   interpreter with `pythonnet >=3.0.3,<3.1`, or rule on relaxing the pin
   to 3.1.0 for 3.14 (an API-surface decision, not a verifier's).
2. **C16 / N1 -- the live-evidence durability gap.** Its remedy is a fresh
   live run that pastes `run_mode` + `run_timestamp` verbatim into the
   evidence file. That is **blocked by C18** -- the two findings compound.

**GATE: GREEN ON SUBSTANCE, needs_human ON ENVIRONMENT.**

Neither open item is evidence against the #242 fix, and neither was
introduced by it. This pass does not set `feature_complete`; the campaign
record already carries that ruling from cycle 4.
