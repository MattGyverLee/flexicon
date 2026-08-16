# Flexicon Constitution

Flexicon is a Python library that mediates between user code and the SIL Language
and Culture Model (LCM) — a large, sparsely-documented .NET API reached through
pythonnet, backed by real linguists' irreplaceable field data. Every principle
below exists because violating it has already cost this project something
specific, cited inline.

## Core Principles

### I. Verify the LCM surface before building on it (NON-NEGOTIABLE)

No design may assume an LCM type, method, property, or arity exists. Confirm it
first against one of:

- liblcm source, cited by file and line (e.g. `UndoStack.cs:731-734`);
- `tests/contract/snapshots/liblcm_baseline.json`, the reflected contract baseline;
- a live pythonnet probe whose transcript is recorded in the feature's `reviews/`.

Same-name fields may carry different LCM types across object types — `Source` is
`ITsString` on `ILexSense` but `IMultiString` on `ILexEtymology`. Copying a working
pattern from one Operations class to another without re-checking the field's type
on the *target* interface is the documented root cause of issues #36, #39, and #40.

*Why:* `_GetTransactionAPI` shipped a three-candidate discovery routine for
`RollbackToMark`, an API that does not exist in liblcm (#236). The docstring
described its fallback behavior in detail. All of it was fiction, and it advertised
a rollback guarantee to callers who had none.

### II. No live FLEx write without a human gate (NON-NEGOTIABLE)

No agent may open a FLEx project for writing or execute a live LCM write. Tasks
requiring one are marked `needs_human` and stop for a person.

The required test invocation, which every brief must quote explicitly:

```
python -m pytest -m "not requires_live_project" -q
```

`pytest --ignore=tests/contract` is **prohibited**. It applies no `-m` filter, so
it collects and executes all 322 `requires_live_project` tests; per
`tests/conftest.py:1221` Phases A-D of those run in-place against the real Sena 3
project. It is a live-write command wearing the costume of a scoping flag.

*Why:* the prose rule "no live writes" was in force and was breached twice in one
feature — once undetected in a cycle-2 verification pass, once self-disclosed in
cycle 3. Both times by an agent that believed it was complying.

### III. Controls, not prohibitions

A rule an agent must infer, remember, or choose to honor is not a control. Where a
constraint matters, encode it as something that fails loudly: a ratchet test with a
frozen baseline, a contract-baseline snapshot, a required and quotable command.

*Why:* Principle II was prose for two cycles and was breached twice. B2g exists
because "bracket all 294 sites" as an instruction is a promise; as an AST scanner
with a frozen 295-entry baseline and a two-way ratchet, it is a control.

### IV. Report the measurement, not the impression

State test results with the exact invocation that produced them and the full
counts, including failures. When two measurements disagree, reconcile them
arithmetically and publish the reconciliation rather than choosing the flattering
one. Pre-existing failures are named as pre-existing and attributed to their issue;
they are never rounded to "green".

*Why:* "139 failed / 1638 passed" and "117 failed / 1424 passed" were both true and
both circulated, measuring disjoint scopes. Neither hid a regression, but nobody
could tell that until the pools were reconciled (1861 - 22 = 1839 = 139+1663+20+17).

### V. Honest API surface

An API must not name, document, or imply a guarantee it does not deliver. Where a
guarantee is mode-dependent, state the mode dependence plainly at the call site's
docstring and warn once at the boundary where the mode is chosen. Prefer a warning
that shows consequences and lets the user decide over a hard error that crashes;
prefer both over silence.

*Why:* `Transaction()` promised rollback under `undoable=False`, where the atomicity
unit is the whole session and a mid-operation exception leaves prior mutations
applied (#236). The name was defensible; the silence about the mode was not.

### VI. Hide LCM complexity, not LCM behavior

Users think in linguistic objects, not interfaces. They must never need to see
`IPhSegmentRule`, `ClassName`, or a cast. But quirks that change what happens to
their data — the `'***'` null marker, session-granularity atomicity, in-process-only
undo — are behavior, not implementation, and must surface in documentation and
return values rather than being smoothed away.

## Development Workflow

**Feature structure.** Each feature owns `specs/<feature>/` containing `spec.md`
(problem, verified surface, settled decisions), `plan.md` (technical context and
constitution gates), `tasks.md` (authoritative ordering), `reviews/` (dated
specialist evidence), and `issues/` (defect writeups). Evidence lives in `reviews/`
and is cited by path; it is not duplicated into planning artifacts.

**Decisions are recorded where they bind.** A decision that reverses an earlier one
is added to `tasks.md` with its evidence path and the reason the earlier reading
lost — not silently edited over. Superseded reasoning stays legible.

**Sweeps are ratcheted, not promised.** Any change applied across more than ~20
sites ships with a scanner, a frozen baseline, and a two-way guard: new occurrences
fail forward, and disappearing baseline entries fail backward until the baseline is
edited down in the same commit.

**Windows is the target platform.** No emoji or non-ASCII in console output —
`[OK]`, `[FAIL]`, `[WARN]`, `[INFO]`. Invoke Python as `python`, not `python3`.

## Quality Gates

A change may not be reported complete until:

1. The required offline invocation (Principle II) has been run and its full counts
   quoted, with any delta against the prior baseline explained.
2. Every LCM claim it relies on carries a source citation (Principle I).
3. Shaped bugs — those with a repeatable form, such as typed-attribute access or
   `ITsString`/`IMultiString` confusion — carry a pattern-audit section listing
   sibling occurrences, or an explicit statement that recurrence is impossible by
   construction.
4. Guarantees stated in docs and docstrings match what the merged code delivers, in
   one place and one voice.

## Governance

This constitution supersedes convenience, precedent, and agent preference. Where a
principle blocks a task, the task stops and a human decides; agents do not grant
themselves exemptions.

Amendments require a new version, an entry naming what changed and which failure
prompted it, and an update to any gate the change affects. Principles I and II are
NON-NEGOTIABLE: they may be amended but never waived for a single task.

`CLAUDE.md` remains the runtime development guidance for code style, module layout,
and API design philosophy. Where the two disagree on a matter of principle, this
document governs; where CLAUDE.md is more specific about mechanics, it governs.

**Version**: 1.0.0 | **Ratified**: 2026-08-14 | **Last Amended**: 2026-08-14
