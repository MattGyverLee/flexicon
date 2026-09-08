# 260-environment-resolver-cast

## The defect

`flexicon/code/Lexicon/AllomorphOperations.py:1371-1383`,
`__GetEnvironmentObject`, promises "Returns: IPhEnvironment" in its
docstring but never casts. `FLExProject.Object(hvo)` returns a bare
`ICmObject`, so subtype-only members (e.g. `StringRepresentation`,
`Name`) are silently lost on the HVO entry path. This mirrors the T8
sibling defect fixed in `__GetAllomorphObject` (commit `df37e35`),
but on the *environment* side of the two allomorph<->environment
resolvers.

## The two call sites (both mutate)

- `AddPhoneEnv` (:1255-1256) -- `allomorph.PhoneEnvRC.Add(env)`
- `RemovePhoneEnv` (:1297-1298) -- `allomorph.PhoneEnvRC.Remove(env)`

Both resolve `env_or_hvo` through `__GetEnvironmentObject` immediately
before using the result as the argument to a `PhoneEnvRC` reference
collection method.

## Issue #260 part 1 / part 2 split

Part 1 (sibling resolver `__GetAllomorphObject`) already landed as T8
in commit `df37e35` -- **not touched by this spurt**. This spurt is
part 2: the twin resolver on the environment side,
`__GetEnvironmentObject`, which has the identical shape defect but was
carved out as a separate half because #260's actually-observed failure
came from an OBJECT input (`obj = project.Object(guid);
allomorphs.GetForm(obj)`), not an int -- so the fix here MUST merge the
int and object branches (mirroring the sibling's :1359-1369 shape)
rather than adding an int-only cast, or the reported defect stays live.

## The three-birds convergence

One HVO-entry live test exercising `AddPhoneEnv`/`RemovePhoneEnv`
simultaneously:

1. proves the new cast in `__GetEnvironmentObject` (this spurt's
   defect fix),
2. closes #260's part 2 (the environment-side resolver, mirroring
   part 1's already-landed `__GetAllomorphObject` fix), and
3. satisfies exactly the narrow close condition flexicon#268 proposes
   for its allomorph half -- `AddPhoneEnv` and `RemovePhoneEnv` are
   both in #268's 7-of-11 zero-live-coverage set.

No GitHub comments, closes, or labels are applied to #260 or #268 from
this spurt -- closure is drafted for review and routed through the
main session.
