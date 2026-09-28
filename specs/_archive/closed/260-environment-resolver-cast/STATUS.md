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

## Ruling: the gate test stays (cycle-16/17 rule does not bite)

`tests/operations/test_260_env_resolver_hvo_gate.py` **stays.** The
cycle-16/17 precedent -- never pin a defect green as expected behaviour --
does not apply, because at these two call sites there is no defect to pin.
What the test pins is a correct behaviour: int-HVO write-through on
`AddPhoneEnv`/`RemovePhoneEnv`, verified by a fresh LCM re-fetch in both
directions, for two methods that previously had **zero** live coverage.
Deleting it would throw away the only artifact that makes the falsification
reproducible.

Its role is re-labelled: **regression fence, not cast gate.** The header
has been corrected in place (T1b) because it asserted P2 as fact -- the
same false-"already handled" marker hazard flagged above, sitting in the
file most likely to be cited as evidence. It now carries an explicit
PROVES / DOES NOT PROVE block: it proves the write-through, it does **not**
prove any cast is required, and if a cast later lands these two tests must
stay green and unchanged (that is P9).

## Class-A re-triage: the anchor is in #260's own body

The re-triage axis ruled above is not an invention of this spurt -- #260's
body already draws the distinction and then asks us to ignore it. It
reports `__GetAllomorphObject` as *directly observed failing* (with a log
line and a stack), and asks for `__GetEnvironmentObject` in the same pass
on the express basis that it is *"not directly observed failing this
window, but structurally the same defect."* Cycle 1 tested that inference
instead of trusting it, and it did not hold. Structural similarity is a
hypothesis; it is not a defect count.

So the re-triage requirement stands and hardens:

- **Evidence must be caller facts, not resolver facts.** Every helper
  promoted to "behavioural" must cite the caller `file:line` performing the
  Python attribute access, and the member name, and that the member is not
  on `ICmObject`. "Uncast + docstring promises an interface" promotes
  nothing.
- **The guarded/unguarded split is demoted to secondary**, inside the
  behavioural bucket only, where it means "also needs input validation".
- **No sweep issue may be filed on the ~55 figure.** It is an upper bound
  on contract mismatches. The archivist's per-module shape (Scripture,
  Discourse, Lexicon, Grammar remainder, combined Reversal/Lists/Notebook)
  survives as the right *packaging* for whatever the behavioural bucket
  turns out to be -- the PR-size argument is sound and unaffected by the
  falsification -- but it does not survive as a *scope*: the module split
  was drawn over contract mismatches, and re-triage will redraw the
  boundaries and probably shrink the count a lot. Re-scope after triage,
  do not pre-file. Contract-only leftovers batch into ONE housekeeping
  issue with no live gate.
- **flexicon#261 (Class D) is unaffected** by any of this and stays its own
  issue -- wrong lookup API, not a missing cast.

## Closure comment: drafted, NOT posted

`reviews/DRAFT-260-closure-comment.md`. No GitHub action taken. It is marked
do-not-post because its Part 2 speaks of the contract cast in the past tense
and that cast is still T3. Post only after T3 lands and P9 verifies live.

## Next pickup

Cycle 2 (T2-T5), then #260 closes. T2 is the priority -- it is the only
genuine defect in this feature, and P6/P6b/P7 are its falsifiers.
The Class-A caller-usage re-triage is a separate later spurt.
