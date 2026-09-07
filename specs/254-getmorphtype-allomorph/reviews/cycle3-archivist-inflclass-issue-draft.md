# Draft GitHub Issue (NOT FILED -- awaiting user authorisation)

## Title
`InflClassRA` does not exist on `IWfiMorphBundle` -- GetInflectionClass/SetInflectionClass are dead-on-arrival

## Body

**Confirmed:** live reflection against Sena 3, 2026-09-06. `hasattr(bundle,
"InflClassRA")` -> `False`; direct access raises `AttributeError:
'IWfiMorphBundle' object has no attribute 'InflClassRA'`. See
`specs/254-getmorphtype-allomorph/evidence/live-cycle2-fix.md`, Item 8
(found incidentally while fixing #254 in the same class, which had zero
test coverage before that work).

### Affected sites -- `flexicon/code/TextsWords/WfiMorphBundleOperations.py`

| Line | Site | Effect |
|---|---|---|
| L1255 | `GetInflectionClass` | unguarded `bundle.InflClassRA` -- raises `AttributeError` on every call |
| L1308 | `SetInflectionClass` | unguarded `bundle.InflClassRA = infl_class` -- raises on every call |
| L331-332 | `Duplicate` | `hasattr`-guarded -- permanently-false dead branch, never copies anything |
| L381-382 | `GetSyncableProperties` | same dead-branch shape |
| L285 | `Duplicate` docstring | claims `InflClassRA` is a copied reference property -- never true |
| L363 | `GetSyncableProperties` docstring | same false claim |

**Additional occurrences found by grep** (same copied dead-branch shape,
not in original six but same root cause): `WfiAnalysisOperations.py`
L561-562 and `WordformOperations.py` L878-879, both inside bundle-copy
loops guarding `InflClassRA` the same way.

### Root cause -- Category 8 (see CLAUDE.md)

`InflTypeRA` genuinely exists on `IWfiMorphBundle` and works (L1155,
L1212 -- confirmed live in the same evidence file, Items unrelated to
this one). `InflClassRA` is not a typo for it; it's a distinct field name
copied from an interface that actually owns it. Per the repo's contract
snapshot (`tests/contract/snapshots/liblcm_baseline.json`), the field
exists as:
- `IMoStemMsa.InflectionClassRA`
- `IMoDerivAffMsa.FromInflectionClassRA` / `ToInflectionClassRA`
- `IPartOfSpeech.DefaultInflectionClassRA`

All are on MSA/POS types, not on `IWfiMorphBundle`. The bug entered at
project inception (`4ff6344`, "Add comprehensive CRUD operations for FLEx
data (v2.0.0)") and has shipped unguarded ever since -- likely a
copy-paste from `MSAOperations.py`-style inflection-class handling onto
the morph-bundle class, dropping the `MsaRA.` indirection.

### Precedent

This repo has already fixed this exact shape twice: f424f99 (removed a
hasattr gate that was dead code) and 8a6c3ab (stopped silently dropping a
field on sync). 74bc997 cut a release explicitly for "two broken public
methods and a lying stub set" -- this issue is the same category, on the
same class, found by the same kind of live reflection.

### Severity

High for the two public methods (guaranteed `AttributeError` on any
caller, no test coverage caught it); low for the dead branches (silent
no-op, wrong docs, no crash).

### Open question for maintainer

Fix shape is undetermined -- propose one of:
1. Retire `GetInflectionClass`/`SetInflectionClass` outright, the way
   #254 retired `SetMorphType` (raise `FP_ParameterError` unconditionally,
   remove the false docstring claims and dead branches).
2. Redirect both methods to the correct owning object -- likely via
   `bundle.MsaRA` when it casts to `IMoStemMsa`/`IMoDerivAffMsa`, exposing
   `InflectionClassRA` through that indirection instead of directly on the
   bundle.

Recommend dispatching to `/lex-programmer` for the fix once direction is
chosen.
