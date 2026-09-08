# cycle2-programmer.md -- issue #260, cycle 2 (T2-T5)

## Verified real line numbers (read first-hand before use)

`flexicon/code/Grammar/EnvironmentOperations.py` (pre-fix, unmodified):

- `__ResolveObject`: def at **:648**, body **:649-660** (`isinstance` at
  :658, `self.project.Object(...)` at :659, passthrough return at :660).
- `GetName` :222 (decorator)/:223 (def); read at **:258**
  (`env.Name.get_String(...)`).
- `SetName` :261/:262; write at **:304** (`env.Name.set_String(...)`).
- `GetStringRepresentation` :306/:307; read at **:365**
  (`env.StringRepresentation.Text`).
- `SetStringRepresentation` :368/:369; write at **:428**
  (`env.StringRepresentation = mkstr`).
- `GetSyncableProperties` :664/:665; `getattr(env, prop_name)` loop at
  **:700** (not :688 as cited in the briefing -- :688 is where
  `__ResolveObject` is called; the `getattr` loop itself is 12 lines
  later).
- **Method-name correction**: the briefing and predictions.md refer to
  `GetLeftContext`/`GetRightContext`. No such methods exist. The real
  methods are **`GetLeftContextPattern`** (def :430/:431, `hasattr`
  gate at :481) and **`GetRightContextPattern`** (def :486/:487,
  `hasattr` gate at :537). All P7 testing below targets the real names.

`flexicon/code/Lexicon/AllomorphOperations.py` (pre-fix, unmodified):

- `__GetEnvironmentObject`: def at **:1370**, body **:1371-1382**.
- `AddPhoneEnv`: def :1213/:1214; resolve at :1255, `PhoneEnvRC.Add` at
  :1258.
- `RemovePhoneEnv`: def :1260/:1261; resolve at :1297, membership test
  at :1301, `.Remove` at :1303.

`flexicon/code/Lexicon/MSAOperations.py`: the false claim spans
**:1122-1128** (not exactly :1126 as cited), the sentence "the sibling
`__GetNaturalClassObject`/`__GetPhonemeObject` C2 fix sites" landing at
:1126-1127 within that span.

## Per-prediction adjudication

**P6 -- HELD.** `GetName(env_hvo_int)` and
`GetStringRepresentation(env_hvo_int)` (plus `SetName`/
`SetStringRepresentation`, added for full P8 coverage) each raised
`AttributeError: 'ICmObject' object has no attribute 'Name'` /
`'StringRepresentation'` on unmodified source. RED verbatim in
`evidence/live-T2-red-p6-p6b-p7.md`. GREEN after the cast in
`evidence/live-T2-green-p6-p6b-p8.md` (4/4 pass).

**P6b -- HELD.** `GetSyncableProperties(env_hvo_int)` raised
`AttributeError: 'ICmObject' object has no attribute 'Name'` at
`EnvironmentOperations.py:700`, the first of Name/Description/
StringRepresentation reached, on unmodified source. GREEN after the
cast: `props["Name"]` contains the expected value via a genuine int
HVO.

**P7 -- FALSIFIED (but not the way anyone expected -- see below).** The
silent-`None` return is real and reproducible, but the guarded cast
does **not** fix it, and testing it exposed a **separate, more
fundamental, pre-existing bug**: `IPhEnvironment` and its sole concrete
implementation `PhEnvironment` declare **no** `LeftContextOA` /
`RightContextOA` property anywhere. Confirmed live via .NET reflection
(`clr.GetClrType(IPhEnvironment).GetProperties()`): the real members are
`LeftContextRA` / `RightContextRA` (Reference Atomic, not Owning
Atomic). Attempting to read the nonexistent name off a freshly-cast
object raises `AttributeError: 'IPhEnvironment' object has no attribute
'LeftContextOA'. Did you mean: 'LeftContextRA'?` -- pythonnet names the
fix itself.

Deciding observation, in order:
1. No naturally-populated example exists to read: Target has 0
   environments; Sena 3 has 44, **0** with a populated left/right
   context (measured live).
2. Building a synthetic fixture (factory-created `IPhSimpleContextSeg`,
   attached via `env.LeftContextOA = ctx` on the pre-cast concrete
   object) appeared to "work" -- but only because assigning an
   attribute name that is **not a real CLR member** on an un-narrowed
   pythonnet wrapper silently creates a **dynamic Python instance
   attribute**, not a real write. It is invisible to any fresh wrapper
   of the same underlying object.
3. Post-cast, `GetLeftContextPattern(env_hvo_int)` still returned
   `None` -- not because the cast failed, but because
   `IPhEnvironment(obj)`'s narrowed wrapper genuinely has no
   `LeftContextOA` member to find, cast or not.
4. Direct reflection confirmed there is nothing to find: `IPhEnvironment.
   GetProperties()` lists `LeftContextRA`/`RightContextRA`, never
   `LeftContextOA`/`RightContextOA`.

Per `standing_rule_empty_falsifier_set_is_not_a_pass`, I did not
manufacture a substitute pass. The RED-committed test class for P7 was
replaced with `TestP7DiscoveredWrongPropertyName` (still live,
`target_sandbox`), which locks the **discovery** (the real property
names, and that `GetLeftContextPattern` returns `None` unconditionally)
rather than asserting a fix that does not exist. This is a genuine,
separate, live-reproducible bug in `GetLeftContextPattern`/
`GetRightContextPattern`/`Duplicate`'s deep-copy block, out of scope for
this cast-only task. **Recommend filing a new issue**, not folding it
into #260. Full mechanism and both RED/GREEN transcripts are in
`evidence/live-T2-red-p6-p6b-p7.md` and
`evidence/live-T2-green-p6-p6b-p8.md`; the corrected narrative is also
written into `reviews/DRAFT-260-closure-comment.md` Part 3 (still marked
DO-NOT-POST).

**P8 -- PARTIALLY HELD.** GetName/SetName/GetStringRepresentation/
SetStringRepresentation and GetSyncableProperties all succeed through
the int-HVO path post-cast, re-read from fresh re-fetches. The
GetLeftContext leg does **not** hold -- see P7.

**P9 -- HELD.** Re-ran `tests/operations/test_260_env_resolver_hvo_gate.py`
live after BOTH T2's and T3's casts landed: all 4 tests (2 original + 2
new T4 both-int-HVO tests) stayed green and unchanged, including the
identity-hazard case (`RemovePhoneEnv`'s `if env in allomorph.PhoneEnvRC`
after casting mints a new wrapper) -- confirmed by a fresh `GetPhoneEnv`
re-fetch. Nothing flipped; cycle 1's falsification of P2 stands.
Evidence: `evidence/live-T3-p9-p10.md`.

**P10 -- HELD.** `hasattr(bare_allo, "PhoneEnvRC")` measured `False`
live. Disposition: added `TestHvoPathBothIntCastAddPhoneEnv` /
`TestHvoPathBothIntCastRemovePhoneEnv` to
`test_260_env_resolver_hvo_gate.py`, passing BOTH the allomorph and the
environment as genuine int HVOs (each preceded by the live `hasattr`
precondition). The flexicon#268 coverage claim for
AddPhoneEnv/RemovePhoneEnv is now genuinely true on both halves of the
call, not withdrawn.

**P11 -- HELD, arithmetically exact.** N = 8 (6 new methods in the new
file `test_260_environment_resolver_gate.py` + 2 appended to
`test_260_env_resolver_hvo_gate.py`), written into predictions.md before
running. Offline run:

```
python -m pytest tests/operations tests/contract -m "not requires_live_project" -q -p no:cacheprovider
2 failed, 439 passed, 536 deselected, 8 warnings in 4.87s
```

439 passed / 2 failed / 536 (528+8) deselected, exactly as predicted.
Failing set: exactly the two foreign
`tests/operations/test_transaction_rollback.py::TestPhase2JoinOrOpen::
test_rollback_flag_set_true_on_exception` /
`::test_depth_restored_on_exception`, pre-existing and unrelated.

## T2 -- the real defect, fixed

Wrote `tests/operations/test_260_environment_resolver_gate.py`
(live-marked, `target_sandbox` only). RED-first: ran against unmodified
`__ResolveObject`, captured 6/6 failures verbatim (5 AttributeError, 1
assertion mismatch on a wrongly-silent `None`) --
`evidence/live-T2-red-p6-p6b-p7.md`. Committed test + RED evidence
(`a28f3c68`) BEFORE any production change.

Landed the guarded, never-raising cast (merging int/object branches,
matching P1's "exactly one implementing type" finding):

```python
def __ResolveObject(self, env_or_hvo):
    if isinstance(env_or_hvo, int):
        obj = self.project.Object(env_or_hvo)
    else:
        obj = env_or_hvo
    class_name = getattr(obj, "ClassName", None)
    if class_name == "PhEnvironment":
        return IPhEnvironment(obj)
    return obj
```

Re-ran live: 6/6 green (`79d8dc34`, evidence in
`evidence/live-T2-green-p6-p6b-p8.md`), except the P7 test class was
replaced with the discovery-locking `TestP7DiscoveredWrongPropertyName`
per the P7 finding above (same commit, same evidence file).

## T3 -- contract-conformance cast landed in AllomorphOperations

Landed the identical guarded cast in
`AllomorphOperations.__GetEnvironmentObject` (`ef3bd4ef`), labelled in
both the docstring and the commit message as **contract conformance
with ZERO measured behavioural effect** -- explicitly not a verified bug
fix, per cycle 1's P2 falsification. Re-ran the identity-hazard-sensitive
gate tests LIVE (not just offline) after landing: P9 HELD, 4/4 green,
evidence in `evidence/live-T3-p9-p10.md`.

## T4 -- flexicon#268 coverage claim made true

Measured `hasattr(bare_allo, "PhoneEnvRC") == False` live (P10 HELD, in
the same session as the T2 RED run -- see
`evidence/live-T2-red-p6-p6b-p7.md`). Added
`TestHvoPathBothIntCastAddPhoneEnv` / `...Remove...` to
`test_260_env_resolver_hvo_gate.py`, passing both the allomorph and the
environment as genuine int HVOs. Updated
`reviews/DRAFT-260-closure-comment.md` (still marked DO-NOT-POST; no
GitHub action taken) to reflect the claim is TRUE, not withdrawn, and to
rewrite Part 2 from "will be fixed" to "fixed, GREEN, P9 verified live",
plus added a new Part 3 for the P7 discovery.

## T5 -- false docstring claim corrected

`Lexicon/MSAOperations.py` (`__GetMsaObject`, docstring spanning
:1109-1128) claimed `NaturalClassOperations.__GetNaturalClassObject`/
`__GetPhonemeObject` were "sibling C2 fix sites" (already cast).
Verified by reading `Grammar/NaturalClassOperations.py:106` and `:120`
directly: both are plain `isinstance(x, int)` resolvers, **no**
`ClassName` cast anywhere. Corrected the docstring (commit `86a9c9d0`)
to state this plainly and point at the Class-A re-triage in
`STATUS.md` that tracks them; did not touch
`NaturalClassOperations.py` itself (out of scope, belongs to the
re-triage).

## Commit SHAs, in order

1. `a28f3c68` -- `test(260-environment-resolver-cast): RED-first gate
   for EnvironmentOperations.__ResolveObject, P6/P6b/P7 confirmed RED`
   (new test file, predictions.md N=8, RED evidence). No production
   code changed.
2. `79d8dc34` -- `fix(260-environment-resolver-cast): guarded cast in
   EnvironmentOperations.__ResolveObject, P6/P6b GREEN` (production
   cast, P7 test-class correction, GREEN evidence).
3. `ef3bd4ef` -- `fix(260-environment-resolver-cast): land
   contract-conformance cast in AllomorphOperations.__GetEnvironmentObject,
   P9 HELD` (production cast, T3, P9 live evidence).
4. `86a9c9d0` -- `docs(260-environment-resolver-cast): T5 false-claim
   correction + T4 draft-closure update (still DO-NOT-POST)`.

RED-before-GREEN ordering is auditable from this sequence: commit 1 adds
the failing tests with zero production changes; commit 2 is the first
production change and turns them green.

## Offline regression numbers

`439 passed, 2 failed, 536 deselected` -- see P11 above. No new offline
failures introduced by any of T2/T3/T5's production changes.

## Blockers / items needing a lead ruling

None block closure of #260 itself. Two follow-on items, explicitly NOT
resolved in this cycle and NOT folded into #260:

1. **NEW bug, needs its own issue**: `EnvironmentOperations.
   GetLeftContextPattern`/`GetRightContextPattern`/`Duplicate`'s
   deep-copy block read `LeftContextOA`/`RightContextOA`, which do not
   exist anywhere in the LCM API (`LeftContextRA`/`RightContextRA` are
   the real names). Live-reproducible, unconditional (every environment,
   cast or not). Anchor test:
   `test_260_environment_resolver_gate.py::TestP7DiscoveredWrongPropertyName`.
2. **Deferred, as previously ruled**: the Class-A caller-usage re-triage
   (STATUS.md) -- unaffected by this cycle, scheduled separately.

`reviews/DRAFT-260-closure-comment.md` is updated but **still marked
DO-NOT-POST** -- posting to GitHub is a main-session/user decision, not
performed here. No GitHub action of any kind was taken on #260, #261,
#268, or anything else.
