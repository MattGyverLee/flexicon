# Phase 0 Research: Issue #572 — phonological rule readers

Every unknown raised by the plan's Technical Context, resolved. Each entry
records the decision, why, and what was rejected. No entry remains open.

Scope note: most of the LCM surface was resolved during `/speckit-specify` and
is **not** repeated here — it is tabulated in [spec.md](spec.md) §2 with its
citations. This file covers the unknowns that surfaced while writing
[plan.md](plan.md): the control infrastructure to hook into, the helpers to
route text through, the precedence model for `C11`, and the test-data problem.

---

## R-1. Which text helper do the fixed string readers use?

**Decision**: `best_analysis_text()` from `flexicon/code/Shared/string_utils.py:160`,
with `best_vernacular_text()` (`:183`) and `best_text()` (`:205`) as the
house alternatives. All three take an `IMultiString`/`IMultiUnicode` and return
normalized text, or `""` when unset.

**Rationale**: `string_utils.py:160, 183, 205` already own exactly this
conversion, and `CLAUDE.md`'s "String handling" section names
`best_analysis_text()` / `best_vernacular_text()` as the required route for
language analysis. Writing `Name.BestAnalysisAlternative.Text` inline would
work and would be a second spelling of an existing rule — the kind of drift
`docs/API_DESIGN_PHILOSOPHY.md` rule 1 exists to prevent. The helper also
normalizes empty multilingual fields to `""`, which is precisely C7's
specified fallback.

**Rejected**:
- `Name.BestAnalysisAlternative.Text` inline — correct, but duplicates the
  helper and skips the empty-normalization the contract promises.
- `str(x.Name)` with a `hasattr` guard — the current code, and the bug.
- `x.Name.BestText` — not a member; invented.

**Applies to**: `context_name`, `description` (via `DescriptionOA`), the
`RuleFeature.name` and `RuleFeature.item_name` readers (C4), and the four
docstring examples in the plan's pattern audit.

---

## R-2. Does adding 7 methods to `PhonologicalRuleOperations` trip the published-surface ratchet?

**Decision**: Yes for the baseline; **no** for a `BREAKING CHANGE:` footer. The
surface baseline is regenerated in the same commit.

**Rationale**: `PhonologicalRuleOperations` is in `flexicon/__init__.py:167`
(imported) and `:505` (in `__all__`), and Constitution 2.1.0 defines
"published" as `__all__` **plus the public methods of the classes it exports**.
Its methods are therefore enumerated by
`tests/test_issue339_public_import_surface.py` and
`tests/test_operations_baseline.py`; both need a mechanical baseline edit when a
method is added. Adding is explicitly *growth*, which Principle VII leaves
unrestricted, so this is the "regenerated in the same commit, a mechanical diff
for additive work" path — not a gate to justify.

`PhonologicalContext`, `ContextCollection` and the new `RuleFeatureCollection`
are reachable only as `flexicon.code.*` and are absent from `__all__`, so under
2.1.0 they are **internal regardless of naming**. Retiring `boundary_type` and
`as_boundary_context` therefore needs no cause, no footer, and no
`MIGRATION_GUIDE.md` entry.

**Rejected**: treating the `boundary_type` retirement as a breaking change.
It would be, if the class were published; 2.1.0's amendment log exists
precisely to stop the baseline over-freezing internal helpers and "braking
ordinary refactors".

---

## R-3. Does adding `"Disabled"` to `GetSyncableProperties` trip the sync member ratchet?

**Decision**: No allowlist entry is needed, and no ratchet edit is required.

**Rationale**: `tests/test_syncable_properties_member_ratchet.py` fires only on
the pattern `hasattr(item, "<name>")` — its regex is
`_HASATTR_ITEM_RE = re.compile(r'hasattr\(item,\s*["\'](\w+)["\']\)')` (`:85`).
`PhonologicalRuleOperations.GetSyncableProperties` guards with
`hasattr(rule, prop_name)` and reads `rule.StratumRA` (`:1509-1526`), so the
receiver is never `item` and this class contributes **zero** fields to the
ratchet today. Adding a plain `props["Disabled"] = rule.Disabled` read changes
nothing about that.

The other direction was checked and is the real risk: the ratchet fails when a
field is guarded by `hasattr` but **absent from** `liblcm_baseline.json`, because
the guard is then always `False` and the key is a dead sync key. `Disabled` is
present in the baseline (spec §2.1, verified live on `IPhSegmentRule`), so a
`hasattr` guard would be *legal but pointless*. The plan therefore specifies a
direct read plus an explicit interface check, and `research.md` R-8 records why.

**Rejected**: adding an `_ALLOWLIST` entry speculatively. An allowlist entry
for a field the ratchet never sees is a hole opened for nothing, and this
ratchet already has a backward test that fails stale entries
(`test_allowlist_entries_are_still_needed`).

---

## R-4. What shape must the `PhBoundaryContext` ratchet take?

**Decision**: `tests/test_issue572_boundary_context_ratchet.py`, a four-pass
scanner modelled on `tests/test_flexlibs2_alias_ratchet.py`, asserting **zero**
occurrences — with **no frozen baseline**, and with a two-way guard of the
allowlist-honesty kind.

**Rationale**: The Constitution's Development Workflow says a sweep of more than
~20 sites ships with "a scanner, a frozen baseline, and a two-way guard", and
names `test_flexlibs2_alias_ratchet.py` as the model. C7 is 26 sites, so a
scanner is mandatory. But the *shape* of that rule assumes a sweep with
survivors — `flexlibs2` has ~295 legitimate references under
`PY_PROSE_ALLOWED` and needs a count to shrink. C7's target is **zero**: the
class does not exist, so no occurrence is legitimate anywhere outside the
evidence file recording its non-existence. `assert not offenders` is therefore
the frozen baseline — an exact count of 0, which is strictly stronger than a
count that must be edited down. The two-way guard is still required, because a
ratchet can be weakened by growing its allowlist; `test_flexlibs2_alias_ratchet.py:318`
(`test_every_allowlisted_path_still_earns_its_hole`) is that guard, and it is
copied: an allowlist entry for a file that no longer exists, or no longer
mentions the string, is a hole left open for nothing and fails.

The four passes, and why each is needed — copied from the model because the
model's own comment records the lesson:

1. **AST pass** (`:86-111`) — executable references. Catches a real
   `class_type == "PhBoundaryContext"` comparison.
2. **String-literal pass** (`:113-134`) — a dotted `PhBoundaryContext`-style
   name in a literal. Catches `by_type("PhBoundaryContext")`.
3. **Prose pass** (`:270-289`) — Markdown and reStructuredText. Catches the 8
   occurrences in `docs/USAGE_CONTEXTS.md`, which is the surface users copy.
4. **Comment+docstring pass** (`:291-314`) — `tokenize` plus
   `ast.get_docstring`. Catches the 13 in-code occurrences that never become a
   string node. Without this pass the ratchet is structurally blind to
   docstrings, which is exactly how the `flexlibs2` rename stayed green through
   ~100 doc references.

`_SKIP_DIR_NAMES` from the model is reused verbatim, and it already contains
`specs` — so this feature's own evidence file, which records that
`PhBoundaryContext` does not exist, is correctly outside the ratchet rather
than needing a bespoke allowlist entry.

**Rejected**:
- A count-based baseline of 26. It encodes a bug count as expected state and
  needs a manual edit to shrink; zero is the honest invariant.
- Ratcheting only the `.py` files. Docs are 8 of the 26 sites and are the
  surface a user copies.
- A bare `assert "PhBoundaryContext" not in text` per file. It has no
  backward guard, so the next agent widens it and nothing says so.

---

## R-5. How is C10 ("no `hasattr` on a raw collection element") made mechanical?

**Decision**: C10 ships as a **live test**, not as a lint rule, and the lint
direction is dropped.

**Rationale**: C10's failure mode is a `hasattr` check that returns `False` for
a member that does exist, because the object was never cast. That is not
detectable by static analysis — it is a property of what pythonnet returns at
runtime, which is why it had to be *measured* (spec §2.4: `RightHandSidesOS`
reads absent on the raw proxy and present after `cast_to_concrete`). So the
control has to execute against a live project: wrap a live `PhSimpleContextBdry`
and a live `PhSequenceContext` from `morphboundary` and assert each reports its
contents, and assert `has_environments` is `True` for all four of that
project's rules. If a future edit routes a read around the wrapper, the test
fails on a real value.

**Rejected**:
- An AST scanner for `hasattr` calls in the new readers. It would flag the
  *legitimate* `hasattr` guards the existing code uses defensively
  (`morphological_context.py:135`), producing a control that must be
  allowlisted rather than a control that catches anything.
- A unit test with fabricated fakes. A fake has whatever attributes the test
  author gave it, so it cannot reproduce the narrowing trap. Only a live object
  can.

**Note**: this is Principle III's escape hatch used honestly — the constraint
that *could* be made mechanical is; the one that cannot is stated as a reason
rather than pretended into a rule.

---

## R-6. How do C5 and C4 get verified when no project holds the data?

**Decision**: Two separate test files. Read-path tests use `morphboundary`
(4 rules, 7 pooled contexts, 2 of them `PhSimpleContextBdry`, plus a
`PhSequenceContext`) opened **read-only**. Write-path tests build an
`IPhIterationContext` and an `IPhPhonRuleFeat` on **Target** via the
`target_project` fixture, read them back through the new readers, and restore in
a `finally:` with the `TEST_` prefix.

**Rationale**: Measured across all five installed projects
(`evidence/live-instance-probe.json`): `PhonologicalDataOA` exists in all five,
but only `morphboundary` has any rules (4), and **no project has a single
`IPhIterationContext` or `IPhPhonRuleFeat`** — `PhonRuleFeatsOA.PossibilitiesOS`
is empty in all five. So iteration and rule-feature readers have no
pre-existing data to read anywhere on this machine. The alternative — reporting
them unverified — is a `FAIL` per Principle II, not a safe outcome.

**Rejected**:
- Mock-only tests for C5/C4. Explicitly the thing the constitution forbids.
- Copying a populated project to manufacture the data. `WireRule` can build
  iteration contexts, so the construction is already reachable; a project copy
  is a much larger side effect for the same coverage.
- Verifying C5 against a hand-built `PhIterationContext` in a sandbox only.
  Read-path readers are cheap to verify in place; splitting the file by data
  source is what the two-file split above does.

**Carried constraint**: C12's corollary that a live write test must
re-query the object after the write, not assert on the value just passed in.
The evidence file records pre-state and post-state.

---

## R-7. What is the recurrence scope of the IMultiString shape?

**Decision**: Seven sites, listed in [plan.md](plan.md) §"Pattern audit". Six
are in scope for this feature; one is not.

**Rationale**: Recurrence is not impossible by construction — an
`IMultiString` is reachable under a dozen different member names
(`Name`, `Description`, `Abbreviation`, `Comment`, `Label`, …) on dozens of
interfaces, and the coercion is invisible to the type checker. So Gate 3's
"impossible by construction" exemption is unavailable and the audit is
mandatory. The six in-tree sites are the same defect at the same confidence;
fixing five of six would leave a caller copying the neighbouring example still
receiving a type name, which Quality Gate 4 forbids.

The seventh, `inspect_rule_final.py:43`, is a **git-tracked scratch script at
the repo root** that no test imports. Editing it is a one-line change but
deleting a tracked file is not this feature's call; `tasks.md` surfaces it as a
decision with the evidence that nothing references it.

**Rejected**: widening the ratchet to all IMultiString shapes now. A
`best_analysis_text`-shaped ratchet across the whole tree would flag hundreds
of sites and demand a baseline the feature cannot honestly maintain; the
`PhBoundaryContext` ratchet is scoped to the string this feature actually
removes, and the audit records the wider family for a future issue.

---

## R-8. Is a `hasattr` guard needed on the new `Disabled` read?

**Decision**: No guard. Read `rule.Disabled` directly, after resolving the rule
the way every other reader on the class does.

**Rationale**: `Disabled` is declared on the **base** `IPhSegmentRule`
(spec §2.1), which both `IPhRegularRule` and `IPhMetathesisRule` implement, so
every rule the class can hand back has it. A guard would be dead weight — and
per `test_syncable_properties_member_ratchet.py`'s own message, a `hasattr`
guard on an absent member is exactly the "dead sync key" pattern that ratchet
exists to catch. The guard in `MorphRuleOperations.IsDisabled`
(`MorphRuleOperations.py:841-843`) is there because that class covers several
unrelated rule types; this one does not.

**Rejected**: copying the `MorphRuleOperations` guard verbatim for symmetry.
The mirror is in the *signature and return contract*, not in a check that can
never fire.

---

## R-9. What shape does `DescribeRule` take?

**Decision**: Mirror `InflectionFeatureOperations.DescribeFeatStruc`
(`InflectionFeatureOperations.py:1015`) as closely as the domain allows: a
read-only, display-only, total method on the Operations class that accepts a
rule *or* an HVO *or* a wrapper, accepts `None`, never raises, and returns a
short human-readable string.

**Rationale**: `DescribeFeatStruc` is the direct precedent — issue #557 built
the same "render a linguistic object for a human" method in this same codebase,
read-only and display-only, with an explicit input-shape list and `None` among
the accepted shapes. C11's requirement that the method be total is the same
design constraint that method carries. Mirroring it means a reader who has used
one knows how the other behaves, which is the point of having a precedent.

`max_count is None` renders as `*` (unbounded), not `-1` — the C5 ruling
carried into the rendered form, so the string a caller sees matches the value
the property returns.

**Rejected**:
- A `__str__` on the wrapper. `PhonologicalRule.__str__` already exists
  (`phonological_rule.py:537`) and is a different, narrower thing; overloading
  it would change existing output for every caller who prints a rule, which is
  a published-behaviour change with no cause.
- Raising on a metathesis rule. Contradicts C2, and a display method that
  raises is useless in a logging call.
