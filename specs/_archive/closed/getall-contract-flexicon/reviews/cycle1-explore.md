# Cycle 1 — Explore: GetAll() / enumerable-return wrap audit (flexicon/code/)

> Written by main session on behalf of Explore (ran read-only, no Write tool).
> Content is the agent's verbatim audit.

## Headline
Total real methods audited: **79** (51 bare `GetAll` + 28 other `GetAll*`/enumerable-returning).
**MISMATCH (raw-shape + no @wrap_enumerable): 0.** Extra two-arg `ObjectsIn(` bugs beyond MediaOperations.py:179: **0.**

Contract recap (BaseOperations.py:120-167, `_needs_enumerable_wrap`): wrapped only if value exposes `GetEnumerator` OR has `__next__` without `__len__`+`__getitem__`. So **raw** = `ObjectsIn(...)`/`iter(...)`/`yield`-gen (NEEDS wrap); **list** = materialized list/dict (wrap is harmless no-op); **smart** = `SmartCollection` subtype (has len+getitem, no next/GetEnumerator → wrap is a *protected no-op*, never downgraded). Decorator order uniformly `@wrap_enumerable` outer / `@OperationsMethod` inner (correct).

## Key findings
- Every raw/generator/`ObjectsIn`-returning bare `GetAll` (and every raw `GetAll*` variant) **already carries `@wrap_enumerable`**. All unwrapped methods return list/dict/set/None (wrap unnecessary).
- Smart collections (`AllomorphCollection`, `RuleCollection`, `CompoundRuleCollection`, `AffixTemplateCollection`) all derive `SmartCollection` (smart_collection.py:71) → `_needs_enumerable_wrap` returns False → never downgraded.
- **Two-arg `ObjectsIn` sweep:** of 12 `ObjectsIn(` call sites, `MediaOperations.py:179` is the ONLY two-arg call. Zero additional arity bugs.

## Two NON-wrap consistency defects found (separate from the disease)
- **B1 — AgentOperations.GetAll (Lists/AgentOperations.py:84):** the only GetAll with neither `@wrap_enumerable` nor `@OperationsMethod`. It overrides the base because `AnalyzingAgentsOC` lacks `PossibilitiesOS`. Return is a materialized `list`, so missing wrap is harmless — BUT missing `@OperationsMethod` breaks the class-level call form (`AgentOperations.GetAll(project)`) every sibling supports. Consistency defect, not a wrap mismatch.
- **B2 — TranslationTypeOperations.GetSegmentsWithType (Lists/TranslationTypeOperations.py:320):** docstring promises `Yields: ISegment` but body's inner block is `pass` (lines 368-372), no yield/return → always returns `None`. Doc/impl mismatch; separate ticket.

## Reconciliation with cycle1-lex-domain.md (MCP index taxonomy)
That review audited the API-doc JSON and found 51 GetAll entities with Defect A = a prose-vs-`type` **documentation** contradiction. THIS code audit finds the *implementation* is correct on the wrap axis: all raw-shape GetAll carry `@wrap_enumerable`. **No code-level raw+unwrapped mismatch corresponds to the doc's "unsafe (c)" set — the doc defect is purely in the generated JSON descriptions (the MCP extractor), not in the Python.**

Membership reconciliation: doc set lists `PossibilityItemOperations` as one entity and omits per-subclass Scripture entries; code has the shared `possibility_item_base` base plus concrete Scripture classes. Headcount coincides at 51.

## Full table
(51 bare GetAll — all `@wrap?=yes` and correctly shaped except AgentOperations B1; 28 other GetAll* variants — unwrapped ones all return list/dict/set. See agent transcript for the per-method rows; summary above is the actionable content.)

Excluded as non-real defs: BaseOperations.py:188/259/1594 (docstring examples), possibility_item_base.py:66 (example), all `.pyi` stubs.
