# Issue #276 -- STATUS

Feature: `276-gramcat-collection`
Issue: https://github.com/MattGyverLee/flexicon/issues/276
State: **COMPLETE -- implemented, live-verified, follow-ups filed**

## What shipped

`GramCatOperations` walked `lp.MsFeatureSystemOA.TypesOC`, whose elements
are `IFsFeatStrucType` -- not possibilities. Wrong collection. The ruling
(`evidence/domain-ruling.md`) established that a list-level "grammatical
category" IS a Part of Speech, so the fix was subtraction plus one
backfill rather than a rewrite.

- `POSOperations.GetParent(pos_or_hvo)` backfilled (T2) -- the one
  capability GramCat had that POS lacked.
- `GramCatOperations` reduced 796 -> 159 lines: a deprecated
  `POSOperations` subclass warning on construction, with 14 TypesOC
  members deleted and `Create` kept only as a raising override (T4/T5).
- `project.GramCat` returns a lazily-cached **distinct**
  `GramCatOperations` (T3, revised -- see below).
- Six false `project.GramCat.Find(...)` docstrings corrected (T6).
- Tests, contract snapshot, migration guide, changelog and the demo
  brought into line (T7-T10, T12).

## The one design decision taken during implementation

`spec.md` was internally contradictory: section 4 wanted
`GramCat.Create` to raise a helpful `FP_ParameterError` naming the
replacements, while sections 2/3 wanted `project.GramCat is project.POS`.
Live verification proved these mutually exclusive -- with the identity,
`project.GramCat.Create("Transitive")` reached `POSOperations.Create` and
raised a bare `TypeError`, so the migration signpost was unreachable on
the exact path FlexTools / FlexTrans callers take.

**Ruled by the repo owner: keep the raising override reachable; drop the
literal identity.** `project.GramCat is project.POS` is now `False`.
Section 3's two-CRUD-surfaces concern is not reintroduced --
`GramCatOperations.__dict__` contains exactly `['Create']`. Recorded in
`spec.md` section 4 under "RESOLVED 2026-09-09".

## Gates

- **Live LCM verification (T11): PASS.** Run twice -- the first pass is
  what exposed the design flaw above, the second re-established the gate
  under the final behaviour. `run_mode: live`, 8/8, Target sandbox plus
  Sena 3 sandbox. Full record in `evidence/live-T11.md`, with run 1
  retained under a SUPERSEDED banner.
- Full suite: 1748 passed, 710 deselected.

## Follow-ups filed (T13)

| Issue | Subject |
|-------|---------|
| #293 | Stray `IFsFeatStrucType` hand-cleanup guidance (docs only; ruling Q4 forbids auto-migration) |
| #294 | `DefaultFeaturesOA` / `InherFeatValOA` public surface (ruling Q5) |
| #295 | `POSOperations.Duplicate` OS/OC coverage gap |
| #296 | `expected_contract.json` accumulated drift (9 files) |
| #297 | `flexicon/__init__.pyi` omits all 43 Operations classes |
| #298 | `examples/grammar_pos_operations_demo.py:89` broken |
