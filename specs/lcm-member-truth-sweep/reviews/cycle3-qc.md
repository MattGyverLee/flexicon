# QC Review: #283 EnvironmentOperations context duplication

**Campaign:** lcm-member-truth-sweep, cycle 3 (checkpoint 3)
**Issue:** #283
**Date:** 2026-09-18
**Status:** APPROVE — 96/100

> Provenance note: produced by the `lex-qc` subagent, which has no
> Write/Edit tools in its agent definition. Persisted to this path verbatim
> by the main session on its behalf. Content is unmodified.

# QC Report — Cycle 3, Issue #283 (EnvironmentOperations LeftContextOA/RightContextOA)

**Score: 96/100 — APPROVE**

## Pattern-Audit Gate: PASS
CHANGELOG.md #283 entry present, in #317 house style. No close/fix/resolve verb sits immediately before "#283" — text reads "...does not exist on `IPhEnvironment`** (#283)." Pattern audit is implicitly the campaign spec itself (specs/lcm-member-truth-sweep); acceptable given campaign context.

## Live-LCM Evidence Gate: N/A for this review
Out of scope for this pass (no evidence artifact requested/reviewed here); flagging only that final campaign sign-off must still confirm one exists per CLAUDE.md.

## Findings

**1. Bare `except Exception: pass` swallows — CONFIRMED GONE.** Full read of `EnvironmentOperations.py` (864 lines) shows zero `except` blocks in `Duplicate()` or anywhere in the file. CHANGELOG.md:53-54 explicitly notes the `clone_properties`/`ObjectRepository.NewObject(ClassID)` machinery and its two swallows were removed — corroborated by the diff. **PASS.**

**2. Unconditional assignment — CONFIRMED.** Lines 646-649: `if source.LeftContextRA is not None: duplicate.LeftContextRA = source.LeftContextRA` (same for Right) sits directly in the `with self._TransactionCM(...)` block, NOT inside an `if deep:` gate. Binding C7 satisfied. **PASS.**

**3. `deep` param retained + documented inert — CONFIRMED**, with one nit. `EnvironmentOperations.pyi:18` (not :19 as the docstring at py:565 and CHANGELOG:50 both claim) still carries `deep: bool = True`. The docstring Example at lines 587-590 was corrected — it now explicitly says "`deep` is INERT for context objects... this produces the same context references as the call above," not the old "shallow copy" claim. **P2**: off-by-one line reference in two places (docstring comment, CHANGELOG) pointing to `.pyi:19` when the actual line is 18 — cosmetic, doesn't affect correctness, but worth a one-line fix before merge.

**4. Stale OA references — ALL corrected.** Grep of the file for `LeftContextOA|RightContextOA` returns zero matches; every one of the eight cited sites (479, 535, 564-565, 591, 674-675, 746, plus code at 494/495/550/551/632-653) now reads `LeftContextRA`/`RightContextRA` with C7 spec-reference comments. **PASS.**

**5. Scope containment — CONFIRMED clean.** Git status snapshot shows only CHANGELOG.md, EnvironmentOperations.py, test_260_environment_resolver_gate.py, test_lcm_member_truth_sweep.py modified (plus two new untracked docs). `compound_rule.py`, `PhonologicalRuleOperations.py`, and `test_phon_rules.py` are untouched. **PASS — binding C9 respected.**

**6. Style/error handling — consistent.** Uses `_EnsureWriteEnabled`, `_ValidateParam`, `_TransactionCM`, `__ResolveObject`, factory `.Create()` — matches the pattern used by sibling Duplicate methods in PhonemeOperations.py, MorphRuleOperations.py, NaturalClassOperations.py (confirmed present, same shape). No anti-pattern reintroduced.

**7. CHANGELOG entry — present, correct house style, verb placement safe** (see Pattern-Audit Gate above).

## Recommendation: **APPROVE**
One outstanding **P2** (non-blocking): fix the `.pyi:19` → `.pyi:18` line-number references in the `Duplicate()` docstring (line ~565) and CHANGELOG.md (line ~50) before final merge — cosmetic only, does not block cycle progression.

**Files reviewed:**
- D:\Github\_Projects\_LEX\flexicon\flexicon\code\Grammar\EnvironmentOperations.py
- D:\Github\_Projects\_LEX\flexicon\flexicon\code\Grammar\EnvironmentOperations.pyi
- D:\Github\_Projects\_LEX\flexicon\CHANGELOG.md
