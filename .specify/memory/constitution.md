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

### II. Live verification is mandatory; the blast radius is bounded (NON-NEGOTIABLE)

Any change touching an Operations class, a factory call, a property setter,
`FLExProject`, or the transaction/write path is verified with live LCM reads **and
writes** before it is reported done. Agents perform those writes unattended; no human
gate is required to run one. A mock-only pass is never verification — it is reported
as `FAIL: unverified`, never as a clean result, and "no live testing was performed"
is a failed gate rather than a safety feature.

**Reads are unrestricted.** Any project on the machine may be opened read-only, at
any time, without a gate. Discovery requires it: which project contains a given
element is not knowable without looking, and a rule that confined reads to two known
projects would make the library untestable against the data it exists to serve. A
read-only open is not a risk to be managed.

What is gated is the **write**, and specifically its **target**. A live write goes
only to a project that is expendable and restorable:

- **Target** (`scripts/restore_target.py`) — blank scratch, the default for write-path
  work, where objects are created rather than found.
- **Sena 3** (`scripts/restore_sena3.py`) — the populated example project. Safe for
  reads and edits in place, at any time; it is the right choice whenever a test needs
  pre-existing data to modify rather than data it created itself.
- a **sandbox** — `target_sandbox` / `sena3_sandbox` (`tests/flex_plugin.py:1439`,
  `:1285`), write-enabled on a fresh tempdir copy of a `.fwbackup`. Use for
  destructive tests, or whenever the real project is locked by an open FieldWorks.

**No other project is a valid write target.** A project may be read freely and still
not be writable: a linguist's real field data is opened read-only and never written
to, and a fixture that opens one write-enabled is a defect in the fixture. That
asymmetry is the whole of the blast-radius rule — read anywhere, write to these three,
and within these three write freely.

Objects created in place are prefixed `TEST_` and removed in a `finally:`; a test that
cannot guarantee its own cleanup uses a sandbox instead. Where a test needs data that
does not exist, add it to Target or copy an existing project — never repurpose or
destroy data that another test reads.

Both invocations are required, and every brief quotes them explicitly:

```
python -m pytest -m "not requires_live_project" -q
$env:FLEXLIBS_REQUIRE_LIVE = "1"; python -m pytest <live test file> -m requires_live_project -q
```

`FLEXLIBS_REQUIRE_LIVE=1` converts every silent degradation — mock fallback, a locked
Target, a missing fixture — into a hard failure. Without it `tests/flex_plugin.py`
prints `[WARN] MOCK MODE` and the session still passes green, which is exactly how
unverified write-path changes get reported as done. Evidence is
`tests/live_status.json` showing `"run_mode": "live"`, plus
`specs/<feature>/evidence/live-<task>.md` recording the command, the pre-state, and
the post-state **re-queried from the LCM after the write** — asserting on the value
just passed in proves nothing.

Bare `pytest` and `pytest --ignore=tests/contract` remain **prohibited**. Neither
applies an `-m` filter, so both collect and execute all 322 `requires_live_project`
tests in place — per `tests/flex_plugin.py:1217`, Phases A-D of those run against the
real Sena 3. The prohibition is about scope, not about writing: an unscoped command
that writes wherever the fixtures happen to point is uncontrolled, whoever is
watching.

*Why:* the predecessor rule forbade live writes outright, which put this principle in
direct conflict with the verification gate in `CLAUDE.md` and left write-path changes
shipping on mock passes — the failure it was written to prevent. Fidelity to real LCM
behavior cannot be established against a mock; it can only be established against a
project that is expendable.

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

### VII. Expand freely; change the published surface only for cause

Growth is not churn. **Adding** to the public surface is unrestricted and needs no
gate: new Operations classes, methods, properties, wrappers, and collections; new
keyword arguments whose defaults preserve current behavior; widened input types; new
exception types subclassing an existing one. Working user code must survive any of
these untouched. One exception: a new keyword argument whose default reproduces
behavior Principle V would call a defect is not additive growth — it is a defect
preserved behind a flag. Such an argument defaults to the corrected behavior, with
the old path reachable only by explicit opt-in
(`docs/API_DESIGN_PHILOSOPHY.md` rule 5).

**Published** means a name bound in `flexicon/__init__.py`'s namespace — enumerated
explicitly in its `__all__`, which is the single source of truth — together with the
public methods of the classes so exported. A name reachable only as `flexicon.code.*`
is internal regardless of whether it begins with an underscore, and may be renamed or
removed freely.

**Altering or withdrawing** what is already published is gated — renaming or removing
a public name, reordering parameters or making one required, changing a default,
changing a return's type or shape, changing which exception is raised, or moving a
name between modules. Such a change ships only with one of three causes, named in the
commit body under a `BREAKING CHANGE:` footer:

1. **liblcm changed** — cite the delta against the contract baseline.
2. **The surface was wrong** — it named a guarantee it did not deliver, contradicted
   LCM behavior, or preserved a defect behind a default (Principle V). Cite the issue.
3. **An announced deprecation matured** — warned for at least one minor release, with
   a working shim for the interim.

"Cleaner", "more consistent", and "we would do it differently now" are not causes.

*Why:* renaming the package `flexlibs2` -> `flexicon` was a single, defensible,
correctly-executed change. It bought a whole compatibility shim package, a ratchet
test to keep internal code out of it (#240), a migration-guide entry, and a removal
deadline at v5.0.0 that is still outstanding. That is the true unit cost of touching
one published name, and it is paid by every FlexTools script on a linguist's disk.
The gate exists because the cost is real even when the change is right — not to
forbid the change, but to make its price visible before it is paid.

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

**The published surface is snapshotted.** Principle VII is inert as prose (Principle
III), so it carries a control: a ratchet freezing the exported names, signatures, and
default values of the public API against a baseline. New entries fail *forward* — the
baseline is regenerated in the same commit, a mechanical diff for additive work.
Changed or removed entries fail *backward* until the commit body carries a
`BREAKING CHANGE:` footer naming one of Principle VII's three causes. The baseline
covers statically declared names only. Attributes forwarded at runtime through a
wrapper's `__getattr__` (`flexicon/code/Shared/wrapper_base.py`,
`flexicon/code/PythonicWrapper.py`) do not exist as Python names in the source and
cannot be enumerated from it; they are governed instead by the liblcm contract
baseline and Principle VII's cause 1. The baseline tracks the `flexicon` package
only — the `flexlibs2` shim's removal at v5.0.0 is governed by `CLAUDE.md` and
`tests/test_flexlibs2_alias_ratchet.py`, not by this baseline.
`docs/API_SURFACE.md` maps what flexicon *consumes* from LCM; this baseline maps what
flexicon *publishes*. They are different artifacts and neither substitutes for the
other.

**Windows is the target platform.** No emoji or non-ASCII in console output —
`[OK]`, `[FAIL]`, `[WARN]`, `[INFO]`. Invoke Python as `python`, not `python3`.

## Quality Gates

A change may not be reported complete until:

1. Both required invocations (Principle II) have been run and their full counts
   quoted, with any delta against the prior baseline explained. For a write-path
   change, `tests/live_status.json` reads `"run_mode": "live"` and an evidence file
   records the re-queried post-state. A mock-mode run satisfies neither.
2. Every LCM claim it relies on carries a source citation (Principle I).
3. Shaped bugs — those with a repeatable form, such as typed-attribute access or
   `ITsString`/`IMultiString` confusion — carry a pattern-audit section listing
   sibling occurrences, or an explicit statement that recurrence is impossible by
   construction.
4. Guarantees stated in docs and docstrings match what the merged code delivers, in
   one place and one voice.
5. Any change to a published name, signature, default, return shape, or raised
   exception carries a `BREAKING CHANGE:` footer stating one of Principle VII's three
   causes, and `docs/MIGRATION_GUIDE.md` gains a corresponding entry. Purely additive
   changes are exempt and need only a regenerated surface baseline; the forward pass
   never blocks a commit, only changed or removed entries can.

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

### Amendment log

**2.1.0** (2026-09-22) — Clarified Principle VII. A new keyword argument whose
default preserves a defect is excluded from additive growth, resolving a conflict
with API_DESIGN_PHILOSOPHY rule 5 under which an agent could add the exact
anti-pattern rule 5 forbids and cite VII to skip the gate. "Published" is now
defined as `flexicon/__init__.py`'s `__all__` plus the public methods of the classes
it exports, so the surface baseline cannot over-freeze internal `flexicon.code.*`
helpers and brake ordinary refactors. The snapshot control now states its two real
limits: it cannot see `__getattr__`-forwarded wrapper attributes, and it does not
track the `flexlibs2` shim. Prompted by a cycle-1 domain review
(specs/constitution-v2-amendment/reviews/cycle1-domain.md), not by a breach. Minor
bump: clarifying and additive; no principle reverses.

**2.0.0** (2026-09-22) — Reversed Principle II. The prior text forbade any agent live
write and routed such tasks to `needs_human`; it now *requires* live read/write
verification, performed unattended, and gates the target rather than the act. Prompted
by a standing conflict: `CLAUDE.md` has always mandated live verification with
`FLEXLIBS_REQUIRE_LIVE=1` and treats a mock-only pass as `FAIL: unverified`, so under
v1.x the two documents gave opposite instructions and the constitution's reading let
write-path changes ship on mocks. Amending rather than waiving, per the
NON-NEGOTIABLE clause below. The safety property is preserved where it actually lives
— writes reach only a project that is expendable and restorable (Target, Sena 3, or a
tempdir sandbox), never a linguist's real field data. Per the project owner: reads are
unrestricted and may touch any project, since which project holds a given element is
not knowable without looking; Sena 3 is safe for reads and edits in place at any time;
and where a test needs data that does not exist, it is added to Target or an existing
project is copied. Major bump: this reverses a NON-NEGOTIABLE principle and invalidates
any brief that quoted the old single offline invocation.

**1.1.0** (2026-09-22) — Added Principle VII (expand freely; change the published
surface only for cause), the surface-snapshot control under Development Workflow, and
Quality Gate 5. Prompted not by a specific breach but by a gap: the document governed
whether the surface was *honest* (V) and *well-abstracted* (VI) while saying nothing
about whether it was *stable*. Under v1.0.0 an agent could rename a method or flip a
default every cycle and pass every gate. Distinguishing additive growth from
alteration keeps expansion unconstrained while pricing the changes that break
downstream callers.

**Version**: 2.1.0 | **Ratified**: 2026-08-14 | **Last Amended**: 2026-09-22
