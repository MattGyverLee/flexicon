# Public API Contract: Issue #572 — phonological rule readers

flexicon is a **library**, so the contract is its public API: the exact
signatures, return types, and the silence each one is allowed to keep. Every
member below is additive except the two retirements in §5, which are internal.

Status: binding for implementation. Deviations need a spec amendment, not a
judgement call at the keyboard.

---

## 1. Published surface — `PhonologicalRuleOperations`

Exported in `flexicon/__init__.py:167, :505`. Eight additions, all growth
(Principle VII 2.1.0 — no cause, no `BREAKING CHANGE:` footer; regenerate the
surface baseline).

```python
@OperationsMethod
def GetLeftContext(self, rule_or_hvo, rhs_index=0) -> Optional["PhonologicalContext"]: ...

@OperationsMethod
def GetRightContext(self, rule_or_hvo, rhs_index=0) -> Optional["PhonologicalContext"]: ...

@OperationsMethod
def GetInputPOSes(self, rule_or_hvo, rhs_index=0) -> list: ...

@OperationsMethod
def GetRequiredRuleFeatures(self, rule_or_hvo, rhs_index=0) -> "RuleFeatureCollection": ...

@OperationsMethod
def GetExcludedRuleFeatures(self, rule_or_hvo, rhs_index=0) -> "RuleFeatureCollection": ...

@OperationsMethod
def IsDisabled(self, rule_or_hvo) -> bool: ...

@OperationsMethod
def SetDisabled(self, rule_or_hvo, disabled) -> None: ...

@OperationsMethod
def DescribeRule(self, rule_or_hvo) -> str: ...
```

### Argument handling — identical across all eight

| Input | Behaviour |
|---|---|
| `PhonologicalRule` wrapper | unwrapped, then read |
| `IPhSegmentRule` / `IPhRegularRule` | wrapped, then read |
| `int` HVO | resolved by the class's `__ResolveObject`, then read |
| `None` | raises `FP_NullParameterError` |

`rhs_index` defaults to `0`. Out of range raises `IndexError` — **not** a
silent `None`, because `None` already means "this rule has no environment here"
(C2) and conflating the two would make the absence undiagnosable.

### Return contracts

- `GetLeftContext` / `GetRightContext` → a `PhonologicalContext` wrapper, or
  `None`. **Never** a raw `IPhPhonContext`: `IPhSimpleContext` declares zero
  properties, so an uncast context is unusable and handing one out would defeat
  the wrapper (spec §3 C1).
- `GetInputPOSes` → `list[IPartOfSpeech]`, the LCM objects **uncast**,
  `[]` when `InputPOSesRC` is unset. The collection is already typed
  `ILcmReferenceCollection<IPartOfSpeech>`, so a cast would only cost the caller
  the object (spec §3 C3). Names are one attribute away:
  `best_analysis_text(p.Name)`.
- `GetRequiredRuleFeatures` / `GetExcludedRuleFeatures` → a
  `RuleFeatureCollection`, **always** — empty, never `None`, because "the rule
  requires nothing" and "this rule's features are unreadable" are different and
  only the first is true.
- `IsDisabled` → `bool`. Never raises for any rule type: `Disabled` is declared
  on the base `IPhSegmentRule`, which every rule this class returns implements.
- `SetDisabled` → `None`. Raises `FP_ReadOnlyError` when
  `project.writeEnabled` is falsy, `FP_NullParameterError` for a `None` rule or
  `disabled`.
- `DescribeRule` → `str`, **non-empty and never raising**. See §4.

### Documented silences (Principle V)

These are contracts, not accidents. Each is stated in the docstring at the call
site.

1. **A metathesis rule yields `None` from `GetLeftContext` /
   `GetRightContext`, silently.** `IPhMetathesisRule` has no `RightHandSidesOS`,
   hence no RHS, hence no environment. Per the Q2 ruling, no `warnings.warn` is
   emitted: a caller iterating `GetAll()` would get one per metathesis rule per
   call. `PhonologicalRule.has_environments` is the documented way to ask first,
   and `metathesis_parts` is where a metathesis rule's environment lives.
2. **`max_count` returns `None` for unbounded, not the LCM's `-1`.** One
   property, one meaning; the `-1` is an LCM encoding detail. The docstring
   states that `None` means unbounded and cites
   `RuleFormulaVcBase.cs:554`.
3. **No writer exists for any member added here.** `SetLeftContext` /
   `SetRightContext` remain refused with `NotImplementedError` (#142);
   `WireRule` remains the only composer. Callers building rules use
   `WireRule`, and this contract does not invite them to try otherwise.

---

## 2. Internal surface — `PhonologicalRule`

Reachable only as `flexicon.code.*`, so free to extend. Each property is the
**primitive**; the `Operations` reader in §1 delegates to it (Q4 ruling), so
there is one implementation and two entry points.

```python
@property
def has_environments(self) -> bool: ...
@property
def is_disabled(self) -> bool: ...

def left_context(self, rhs_index=0) -> Optional["PhonologicalContext"]: ...
def right_context(self, rhs_index=0) -> Optional["PhonologicalContext"]: ...
def input_poses(self, rhs_index=0) -> list: ...
def required_rule_features(self, rhs_index=0) -> "RuleFeatureCollection": ...
def excluded_rule_features(self, rhs_index=0) -> "RuleFeatureCollection": ...
def set_disabled(self, disabled) -> None: ...
```

`has_environments` has **no** `Operations` mirror (spec §5, C-Q4b): it is a
cheap boolean over an existing member, and `PhonologicalRuleOperations` stays
deliberately small.

**Universal invariant (C10, and the trap this feature exists to avoid):** every
read resolves through `self._concrete`, which `LCMObjectWrapper.__init__`
already produces via `cast_to_concrete`
(`flexicon/code/Shared/wrapper_base.py:149`). No capability check may run
`hasattr` against a raw collection element, because pythonnet narrows such an
object to its *collection's* interface and the member then reads as absent.
Measured: `PhonRulesOS[i]` has no `RightHandSidesOS` until cast; `StrucDescOS[i]`
has no `FeatureStructureRA`; `LeftContextOA` has no `FeatureStructureRA`.

---

## 3. Internal surface — `PhonologicalContext` and friends

`PhonologicalContext` (`flexicon/code/System/phonological_context.py`):

```python
# repaired
@property
def context_name(self) -> str: ...        # was: a .NET type name
@property
def description(self) -> str: ...         # was: "" always
@property
def is_boundary_context(self) -> bool: ... # was: always False
def as_boundary_context(self): ...         # was: always None

# new
@property
def boundary_marker(self): ...             # IPhBdryMarker or None
@property
def boundary_name(self) -> str: ...        # "" when unset
@property
def is_iteration_context(self) -> bool: ...
@property
def min_count(self) -> int: ...
@property
def max_count(self) -> Optional[int]: ...  # None == unbounded
@property
def member(self): ...
@property
def is_sequence_context(self) -> bool: ...
@property
def members(self) -> "ContextCollection": ...
```

`RuleFeature` / `RuleFeatureCollection` (new, `flexicon/code/System/rule_feature.py`):

```python
@property
def name(self) -> str: ...          # the IPhPhonRuleFeat's own name
@property
def item(self): ...                 # ItemRA, uncast -- may be IMoInflClass or ICmPossibility
@property
def item_name(self) -> str: ...

@property
def names(self) -> list: ...        # on the collection
@property
def items(self) -> list: ...        # on the collection, uncast
```

`ContextCollection` (`flexicon/code/System/context_collection.py`):

```python
def boundary_contexts(self) -> "ContextCollection": ...   # now filters PhSimpleContextBdry
```

`filter(name_contains=)` is **not edited** — it already reads `context_name`
correctly at `:151` and is dead only because `context_name` was broken. Fixing
`context_name` repairs it; changing `filter` too would double-count one fix.

**Text rule for every new string member:** read through
`best_analysis_text` (`flexicon/code/Shared/string_utils.py:160`), never
`str()` and never a raw `.BestAnalysisAlternative.Text` inline (research.md R-1).

---

## 4. `DescribeRule` — the total-function contract

```python
DescribeRule(rule_or_hvo) -> str
```

Mirrors `InflectionFeatureOperations.DescribeFeatStruc`
(`flexicon/code/Grammar/InflectionFeatureOperations.py:1015`) — read-only,
display-only, total (research.md R-9).

**Totality is the whole requirement.** It must return a non-empty string, and
must not raise, for all of:

- a `PhRegularRule` with populated left and right contexts;
- a `PhRegularRule` with `LeftContextOA is None` (real: `morphboundary`'s
  `t deletion`);
- a `PhRegularRule` with no RHS at all;
- a `PhMetathesisRule` (no environment exists — it renders from
  `metathesis_parts`);
- a rule whose contexts include `PhSequenceContext` or `PhIterationContext`.

Rendering: `input -> output / left _ right`.

- `max_count is None` renders `*`, never `-1` (C5).
- An absent context renders as `-` or is omitted; it never renders as a .NET
  type name or a Python `repr` of an LCM object.
- `DescribeRule(None)` returns a string, following the `DescribeFeatStruc`
  precedent that accepts `None` among its input shapes. It does **not** raise —
  a display method that raises is useless inside a logging call. (This is the
  one place a `None` argument is tolerated; the other seven readers raise
  `FP_NullParameterError`.)

**Not** a `__str__` override. `PhonologicalRule.__str__` already exists
(`phonological_rule.py:537`) and is a narrower thing; overloading it would
change output for every existing caller who prints a rule, with no cause under
Principle VII.

---

## 5. Retirements — internal only, no cause required

| Retired | Replacement | Why it is not a breaking change |
|---|---|---|
| `PhonologicalContext.boundary_type` | `boundary_marker` / `boundary_name` | `PhonologicalContext` is absent from `flexicon/__init__.py`'s `__all__`; under Constitution 2.1.0 a name reachable only as `flexicon.code.*` is internal regardless of naming, and may be removed freely. |

`boundary_type` is retired rather than repaired because its **name** is the
defect: it promised a discriminator (`0=word, 1=morpheme`, per its own
docstring) that `IPhSimpleContextBdry` does not have. The boundary's identity is
the `IPhBdryMarker` behind `FeatureStructureRA`. Per the Q3 ruling the
retirement is **silent** — no `DeprecationWarning`, because no importer can name
this class from `flexicon`'s `__all__`, and a warning would fire on a class
callers cannot reach through the public API.

`docs/USAGE_CONTEXTS.md` carries 8 `PhBoundaryContext` and 5 `boundary_type`
mentions and is updated **in the same commit** (Quality Gate 4).

---

## 6. The sync contract

`GetSyncableProperties` gains one key.

```python
props = ruleOps.GetSyncableProperties(rule)
# before: {"Name": {...}, "Description": {...}, "Direction": 1, "StratumGuid": "..."}
# after:  ... plus "Disabled": False
```

- `"Disabled"` is a **scalar bool**, matching the existing `"Direction"` int
  shape. `_apply_props_loop` handles `bool`/`int` scalars already — see its own
  docstring at `BaseOperations.py:442` — so `ApplySyncableProperties` applies it
  with **no base change** (spec §3 C9).
- With `fill_gaps=True` a stored `False` is **never** overwritten: a rule that is
  deliberately enabled in the target keeps being enabled. That is the existing
  bool/int contract, and this key inherits it.
- `test_syncable_properties_member_ratchet.py` does **not** scan this class — it
  matches `hasattr(item, ...)` and this class guards with `hasattr(rule, ...)`
  — so no allowlist entry is required (research.md R-3).

**Why this key ships with the reader.** Without it, `IsDisabled` reports `True`
in the source project and the synced copy parses with the rule still enabled:
the reader would be honest and the sync would not, which is the half-delivery
Quality Gate 4 exists to catch.

---

## 7. Explicitly out of contract

Stated so a later reader does not assume absence is an oversight:

- **No writers** for environment, rule features, POSes, or context contents.
  `WireRule` is the only composer (#142).
- **No `GetEnvironment()` record type** — rejected in the Q4 ruling as a third
  new name to maintain (spec §4, R2).
- **No `maximum_raw`** alongside `max_count` — rejected in the Q3/R3 ruling on
  Principle VI grounds (spec §3 C5).
- **No export** of `RuleFeature`, `RuleFeatureCollection`, or
  `PhonologicalContext` in `flexicon/__init__.py`'s `__all__` (spec §5, C-Q4a).
- **No `has_environments` mirror** on the Operations class (spec §5, C-Q4b).
- **No `warnings.warn`** on a metathesis rule (spec §3 C2, Q2 ruling).
- **No `IPhPhonRuleFeat.FeatureStructureRA`** — it does not exist (spec §2.2.1).
- **No `PhBoundaryContext` / `IPhBoundaryContext`** — it does not exist (spec
  §2.2.2). Enforced by `tests/test_issue572_boundary_context_ratchet.py`.
