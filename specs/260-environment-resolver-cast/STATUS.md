# STATUS -- 260-environment-resolver-cast

## Where this stands after cycle 1

Cycle 1 asked a narrow question -- does the missing cast in
`AllomorphOperations.__GetEnvironmentObject` break anything? -- and got a
clean, well-instrumented **no**. P2, the load-bearing prediction, was
falsified live. That is a good outcome, not a wasted spurt: it stopped an
unnecessary three-line cast from shipping dressed as a bug fix, and it
established the mechanism that makes this whole defect family tractable.

### The mechanism (the reusable result of this spurt)

An uncast resolver is only a **behavioural** defect where a caller performs
**Python attribute access** on the resolved object. pythonnet's Python-side
wrapper exposes only members declared on the static interface it was built
against (`ICmObject`), so `env.Name` / `hasattr(env, "LeftContextOA")` fail
or silently answer `False`.

Passing that same bare wrapper as an **argument to a strongly-typed .NET
method** is a different path entirely: the CLR binds on the object's runtime
type, which does implement the concrete interface, so it just works. No cast
needed.

Both of `__GetEnvironmentObject`'s callers do the second thing
(`PhoneEnvRC.Add`/`.Remove`). Hence: contract mismatch, zero behavioural
consequence.

### But IPhEnvironment is not cleared

`Grammar/EnvironmentOperations.py:648`, `__ResolveObject`, is the *same*
uncast shape for the *same* interface, with **9 call sites**, and unlike
AllomorphOperations its callers do exactly the thing that breaks:

- `GetName` (:258) `env.Name.get_String(...)`, `SetName` (:304)
- `GetStringRepresentation` (:365) `env.StringRepresentation.Text`,
  `SetStringRepresentation` (:428)
- `GetLeftContext` (:481) / `GetRightContext` (:537) --
  `hasattr(env, "LeftContextOA")` -> **silently returns `None`**
- `Duplicate` (:589), `GetSyncableProperties` (:688)

Cycle 1's own P3 already measured live that `hasattr(bare, "Name")` and
`hasattr(bare, "StringRepresentation")` are both `False`. The falsifier for
this defect therefore already exists in the evidence -- it was just pointed
at the wrong file. There is **zero test coverage** of any kind on these
methods.

The silent-`None` pair is the worst of the set: no exception, no traceback,
no red test, wrong answer. Log triage can never find those, which is why
this survived while #260's `AttributeError` twin got reported within a day.

## Coordination hazard seen twice this spurt

Two independent instances of "a site was believed handled but wasn't":

1. `MSAOperations.py` (~:1126) states `__GetNaturalClassObject` /
   `__GetPhonemeObject` are "C2 fix sites". They are uncast. False marker.
2. The archivist recorded `EnvironmentOperations.py:648-659` as
   "flexicon#260, in flight". It was not in flight and is not fixed. It was
   excluded from the inventory's detail on that belief.

A false "already fixed" claim is worse than no claim -- it makes the next
sweeper skip the site. Both get corrected in cycle 2.

## Ruling on the Class-A inventory (~55 helpers, 9 modules)

The main session's caveat is upheld: "~55 Class A" is a count of **contract
mismatches**, not defects, and the two are provably dissociable. This spurt
produced one of each, for the same interface, in the same shape:
`AllomorphOperations.__GetEnvironmentObject` (harmless) and
`EnvironmentOperations.__ResolveObject` (severe). The resolver does not tell
you which you have. **Class A needs re-triage before any of it is filed.**

The guarded/unguarded split is the **wrong primary axis**. Guarded-vs-
unguarded describes *input* validation; the defect is about *output* usage.
The inventory already half-knew this -- its evidence for GramCatOperations
being real is a caller fact ("callers read `cat.SubPossibilitiesOS` at
:122, :373"), not a guard fact, while `LexEntryOperations.__ResolveObject`
was demoted to MEDIUM purely for having an `isinstance` guard that says
nothing about what its 54 callers do.

Correct primary axis, per helper: **does at least one caller perform Python
attribute access (or `hasattr`) on the resolved object for a member not on
`ICmObject`?**

- **Yes** -> behavioural defect. Ranked: `hasattr`-gated silent-loss sites
  first (invisible to logs and tests), direct-access `AttributeError` sites
  second. Each needs a RED-first live gate.
- **No** -> contract-only. Return value only ever handed to a strongly-typed
  .NET method, or only `ICmObject` members touched (`.Hvo`, `.Guid`,
  `.ClassName`, `.Owner`). Batch into ONE housekeeping issue. No live gate,
  no per-module split.

Guarded/unguarded stays as a **secondary** axis inside the behavioural
bucket, where it correctly signals "also needs input validation".

Per-module sweep issues are the right *shape* for the behavioural bucket
(the PR-size argument is sound), but must not be filed yet: re-triage will
likely shrink that bucket substantially, and filing five module issues now
commits reviewers to work we have just proven we cannot size. Class B is
more defensible than the inventory allowed -- a helper promising only
"object" whose callers pass it to .NET methods is simply correct. Class C
needs nothing; `ParagraphOperations:101` (casts on both branches, with a
comment recording the bug it fixed) is the reference implementation.

## Next pickup

Cycle 2 (T2-T5), then #260 closes. The Class-A caller-usage re-triage is a
separate later spurt.
