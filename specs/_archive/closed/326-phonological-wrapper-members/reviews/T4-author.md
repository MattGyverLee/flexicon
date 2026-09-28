# T4 lex-author review: API breakage and upstream parity, issue #326

Scope: `flexicon/code/Grammar/rule_collection.py`, `flexicon/code/Grammar/phonological_rule.py`,
`flexicon/code/lcm_casting.py` (redup/metathesis surfaces named in the issue). Read-only; no
production code touched; no commits made.

## Q1 -- Public API surface / upstream inheritance?

**Upstream (`cdfarrow/flexlibs`) check:** `git fetch upstream; git ls-tree -r upstream/main
--name-only | grep -i "phonolog|redup|metathesis"` returns **zero files**. Confirmed further by
`git log --all --diff-filter=A -- flexicon/code/Grammar/phonological_rule.py
flexicon/code/Grammar/rule_collection.py` -- both introduced in flexicon-only history
(`8afaef0 Phase 2: Implement phonological rule wrappers and smart collections`, released as
`60d9eb7 Release v2.2.0`). **None of this is inherited from upstream. There is no parity
obligation -- upstream has no phonological-rule wrapper layer at all**, so nothing here can
diverge from or break an upstream contract; the only compatibility surface at risk is
flexicon's own prior releases (v2.2.0 through current ~v4.9.0, published as `pyflexicon`).

**Public-surface check**, per `docs/API_DESIGN_PHILOSOPHY.md` Rule 1: wrapper objects returned
from a documented public Operations method (`PhonologicalRuleOperations.GetAll()` ->
`RuleCollection` of `PhonologicalRule`) **are** the public API -- that is the whole point of the
wrapper/collection pattern, not an implementation detail. Neither class has a `.pyi` stub or a
`flexicon/__init__.py` top-level export, but reachability doesn't require one; `GetAll()`'s
return-value contract is the documented surface (`docs/ARCHITECTURE_WRAPPERS.md`,
`docs/ARCHITECTURE_COLLECTIONS.md`). By contrast, `lcm_casting.py` internals other than
`cast_to_concrete` (itself confirmed exported at `flexicon/__init__.py:425,528`) are explicitly
scoped internal-only by `API_DESIGN_PHILOSOPHY.md` ("Casting is mostly an implementation
detail"). `cast_phonological_rule()` and the module-local `IPhReduplicationRule` slot are
**not** exported and are internal.

## Q2 -- Remove vs. deprecate-then-remove, per symbol

| Symbol | Public? | Upstream? | Verdict | Rationale |
|---|---|---|---|---|
| `RuleCollection.redup_rules()` | Yes (public method on public collection) | No | **Deprecate now, remove at v5.0.0** | Never raises, never populates (T1 Finding 3/4: 0/335 live rules, `PhReduplicationRule` unimportable). Same shape as the `flexlibs2` alias and `_op_aliases.py`/`GramCatOperations` precedent: warn, then hard-remove on the existing v5.0.0 boundary already committed to in `CLAUDE.md`. Removing outright now would be a name-level break (`AttributeError`) for any caller, however unlikely, that calls it; docs-only `reduplication_rules` name (T2: one hit, `ARCHITECTURE_COLLECTIONS.md:393`) is not code and can be deleted outright. |
| `PhonologicalRule.has_redup_parts` | Yes (public property) | No | **Deprecate now, remove at v5.0.0** | Always `False` on every live build (no `PhReduplicationRule` class exists to match `class_type`). Same reasoning as `redup_rules()`. |
| `PhonologicalRule.redup_parts` | Yes (public property) | No | **Deprecate now, remove at v5.0.0** | Gated by `has_redup_parts`, always `([], [])`. No real field to repair against (unlike metathesis) -- there is nothing to fix it *into*, only to warn on and later remove. |
| `PhonologicalRule.as_reduplication_rule()` | Yes (public method) | No | **Deprecate now, remove at v5.0.0** | Always returns `None` (`class_type == "PhReduplicationRule"` never true). Same as above. |
| `PhonologicalRule.has_metathesis_parts` | Yes (public property) | No | **Fix in place (repair, not remove/deprecate)** | `PhMetathesisRule` **is real** (T1 Finding 2/3: 4 live instances observed). The property checks invented members (`LeftPartOfMetathesisOS`/`RightPartOfMetathesisOS`); the real fields are `StrucDescOS` + switch/env/middle index ints. Ships as a **`BREAKING (behavioural)`** minor-version fix per the house convention already used repeatedly in `CHANGELOG.md` (e.g. the `[Unreleased]` and `4.8.0`/`4.7.0`/`4.6.0`/`4.4.0` entries: no signature change, corrected return value) -- **not** a name removal, so the deprecate/remove-at-v5.0.0 track doesn't apply. |
| `PhonologicalRule.metathesis_parts` | Yes (public property) | No | **Fix in place (repair, not remove/deprecate)** | Same as `has_metathesis_parts`: reimplement against `StrucDescOS`/index fields, keep the name and shape (`(left, right)` tuple of context-like data), same `BREAKING (behavioural)` minor-bump track. |
| `PhonologicalRule.as_metathesis_rule()` | Yes (public method) | No | **No action** | Casts on `class_type == "PhMetathesisRule"` only; does not touch the invented `*PartOfMetathesisOS` members. Already correct against the live LCM. Out of scope for this fix. |
| `lcm_casting.py` `IPhReduplicationRule = None` slot (module-local var feeding `_interface_cache`) | **No** (internal; not exported, no public class/method exposes this name) | No | **Remove outright, no deprecation** | Confirmed inert: `if IPhReduplicationRule is not None:` at line ~327 never fires; `cast_to_concrete()`'s public "unrecognised `ClassName` returns object unchanged" contract (`API_DESIGN_PHILOSOPHY.md`) is identical whether the slot exists or not. `API_DESIGN_PHILOSOPHY.md` scopes everything in `lcm_casting.py` except `cast_to_concrete` as internal-only, so no deprecation cycle is owed to any caller. Same reasoning applies to the `PhReduplicationRule` entries in `_get_factory_for_class`'s comment and `cast_phonological_rule()`'s docstring (also unexported, internal) -- correct the prose in place. |
| `PhonologicalRuleOperations.Duplicate()` error message naming `PhReduplicationRule` as a "known concrete type" (line ~1383) | Yes (public method), but this is a **message string**, not a symbol | No | **Fix message wording, not an API-surface question** | The method itself is correct (raises `FP_ParameterError` for any class with no bindable factory); only the listed type names are stale. Update the message to list `PhRegularRule, PhMetathesisRule` only. Not a removal/deprecation decision -- flag for lex-programmer as a docstring/message accuracy fix, no signature or behavior change. |

## Q3 -- API_DESIGN_PHILOSOPHY Rules 1 and 4 compliance of the intended fix

- **Rule 1 (hide interface/ClassName/casting complexity):** The metathesis repair
  (`has_metathesis_parts`/`metathesis_parts` reading `StrucDescOS` + index ints instead of
  inventing `*PartOfMetathesisOS`) keeps casting internal to the wrapper -- callers still never
  see `IPhMetathesisRule`, `ClassName`, or the index-int plumbing. Compliant, provided the
  reimplementation stays inside the wrapper property and doesn't leak the raw index fields
  unwrapped.
- **Rule 4 (smart properties / capability checks, not `ClassName` tests):** `has_output_specs`,
  `has_metathesis_parts` (post-fix), and the deprecated-then-removed `has_redup_parts` are all
  exactly this pattern already -- capability checks callers branch on instead of comparing
  `ClassName` strings. Removing the redup trio does not violate Rule 4; it removes a capability
  check that can never report `True`, which is not "smart," it's dead. Deprecating first (warn,
  keep returning the same always-empty/False/None value for one cycle) preserves Rule 4's
  contract shape for existing callers during the deprecation window, then removes it cleanly at
  v5.0.0 alongside the other scheduled removal (`flexlibs2`).
- No proposed fix reintroduces a `ClassName ==` check at the call site or a caller-visible cast;
  all corrections stay inside the wrapper/collection layer. Compliant with both rules as scoped.

## Notes / out of scope for this review

- `IPhSimpleContextSeg`/`IPhSimpleContextNC`'s invented `SegmentRA`/`NaturalClassRA`
  (`phonological_context.py`) and the real `FeatureStructureRA` link are in scope for issue #326
  overall (T1 Finding 1, T2 sweep) but were not in this task's symbol list (rule_collection.py /
  phonological_rule.py / lcm_casting.py comments) and are not re-litigated here.
- No project was opened; no write path exercised; this is a static/history review only, per the
  "Do not write production code" / "work only in the worktree" mandate.
