# The `GetAll` Behavioral Collection Contract

## The guarantee

Every `GetAll` (and `GetAll*` variant) method in flexicon returns a
**behavioral collection**. Regardless of which concrete Python type comes
back, you can always:

- **loop** it (`for item in result:`)
- **`len()`** it (`len(result)`)
- **index** it (`result[0]`, `result[1:3]`)
- **re-iterate** it (loop it more than once and get the same items again)

The concrete return type is an implementation detail. You never have to
inspect it, branch on it, or call `list(...)` defensively before using it.

## The three concrete shapes

| Shape | When it's used | Notes |
|---|---|---|
| `EnumerableWrapper` | Large or lazily-materialized results (e.g. `project.LexEntry.GetAll()`, anything backed by a raw C# `IEnumerable`, `ObjectsIn(...)`, or a Python generator) | Materializes to a list on first `len()`/indexing/iteration access, then caches it. Also exposes a `.Count` property for callers coming from C#-flavored code. |
| `list` | Small/bounded results that operations code already materializes directly (e.g. possibility-list walks, per-entry collections) | A `list` already satisfies the contract natively; wrapping would be a no-op, so these methods return the plain list. |
| `SmartCollection` subtype (`AllomorphCollection`, `RuleCollection`, `CompoundRuleCollection`, `AffixTemplateCollection`, etc.) | Collections with more than one concrete LCM type mixed together (e.g. `PhRegularRule`/`PhMetathesisRule`/`PhReduplicationRule` all coming back from `PhonologicalRuleOperations.GetAll()`) | Satisfies the same loop/len/index/re-iterate contract *and* adds `.filter()`, `.by_type()`, and a type-breakdown `__str__` on top. |

All three shapes are Python sequences in the behavioral sense: they support
`__iter__`, `__len__`, and `__getitem__`, and iterating them twice gives the
same result both times. None of them is a one-shot, single-use generator or
raw C# enumerator that a caller could accidentally exhaust.

## Why this matters

Before this contract was made explicit and enforced, a caller had no way to
know, without reading the operations source, whether a given `GetAll()` call
would:

- support `len(result)` before iterating,
- support `result[0]` for random access, or
- still have items left if they looped it a second time.

Mixing these behaviors silently (some `GetAll`s returning raw generators,
others returning lists) produced exactly the kind of bug this contract now
rules out by construction: `TypeError` on `len()`/indexing, or unexpectedly
empty second iterations.

## How it's enforced in code

The `@wrap_enumerable` decorator (see `flexicon/code/BaseOperations.py`) is
applied to every `GetAll`/`GetAll*` method that has a raw-shape return
(`ObjectsIn(...)`, `iter(...)`, or a `yield`-based generator body). It
inspects the actual returned value at call time
(`_needs_enumerable_wrap`) and only wraps it in `EnumerableWrapper` when the
value doesn't already behave like a sequence (i.e. it has `__next__` but
lacks the `__len__`/`__getitem__` pair). Values that are already lists,
tuples, or `SmartCollection` instances pass through untouched -- the
decorator is a safety net, not a re-wrap-everything step.

This means the decorator is always present on methods whose body can return
a raw enumerator/generator, but it's a documented no-op (not dead code) on
methods that already return a `list` or `SmartCollection` -- if the
implementation shape of one of those methods ever changes to a raw
enumerator in the future, the decorator will catch it automatically.

## What this means for your GetAll docstrings

Docstrings should describe the *return* type, not use `Yields:`
generator-style wording -- even for methods whose body is written with
`yield` internally, since `@wrap_enumerable` converts that generator into an
`EnumerableWrapper` before it ever reaches the caller. Use:

```
Returns:
    EnumerableWrapper[ILexEntry]: All lexical entries in the project
```

or, for methods that return a plain list or a `SmartCollection` subtype:

```
Returns:
    list[ICmSemanticDomain]: All semantic domains.
```

```
Returns:
    RuleCollection[PhonologicalRule]: Smart collection of PhonologicalRule wrapped objects.
```

## See also

- `flexicon/code/BaseOperations.py` -- `EnumerableWrapper`, `wrap_enumerable`,
  `_needs_enumerable_wrap`
- `docs/ARCHITECTURE_COLLECTIONS.md` -- the `SmartCollection` pattern in
  depth (type breakdown, `.filter()`, `.by_type()`)
- `docs/ARCHITECTURE_WRAPPERS.md` -- the per-item wrapper classes
  (`Allomorph`, `PhonologicalRule`, etc.) that `SmartCollection` subtypes
  hold
