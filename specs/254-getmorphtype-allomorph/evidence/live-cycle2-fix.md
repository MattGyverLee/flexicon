# Live verification -- issue #254 cycle 2 (fix implementation)

**Project:** Sena 3 | **Fixture:** sena3_sandbox (tempdir copy of
`tests/fixtures/Sena 3 2018-09-11 1145.fwbackup`, disposed on teardown)
**Command:**
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue254_live_cycle2.py -m requires_live_project -q -s
```
**run_mode:** live (`tests/live_status.json` -> `"run_mode": "live"`)
**Date:** 2026-09-06
**Result:** 8 passed

## Claim under test

Cycle-2 fix to `WfiMorphBundleOperations.py`: `GetMorphType` repaired to
read `bundle.MorphRA.MorphTypeRA` (bare, no cast); `SetMorphType` retired
unconditionally; new `GetMorph`/`SetMorph` pair added.

## Item 1 -- bare attribute access

Pre-state: bundle with `MorphRA.ClassName=MoStemAllomorph`.
Post-state (read from LCM): `morph.MorphTypeRA` (bare) = `root`;
`IMoForm(morph).MorphTypeRA` (cast) = `root`. Identical Hvo both paths.
**[PASS]** -- bare access resolves; no cast needed; shipped code is correct
as-is.

## Item 2 -- GetMorphType returns IMoMorphType, correct names

Walked live bundles until one example of each was found:
- prefix: ClassName=`MoAffixAllomorph`, `MorphTypeRA.ClassName`=`MoMorphType`, `Name`=`"prefix"`
- suffix: ClassName=`MoAffixAllomorph`, `MorphTypeRA.ClassName`=`MoMorphType`, `Name`=`"suffix"`
- stem: ClassName=`MoStemAllomorph`, `MorphTypeRA.ClassName`=`MoMorphType`, `Name`=`"root"`

Agrees with cycle-1 probe's recorded distribution
(`('MoStemAllomorph','root'):468`, `('MoAffixAllomorph','prefix'):819`,
`('MoAffixAllomorph','suffix'):323`). **[PASS]**

## Item 3 -- warning path, MorphRA is None

Pre-state: bundle Hvo=139620, `MorphRA is None`.
Action: `GetMorphType(bundle)` under `caplog.at_level(WARNING)`.
Post-state: returned `None`; captured log record:
`"GetMorphType: bundle Hvo=139620 has no linked allomorph (MorphRA is
None); cannot resolve a morph type"`. **[PASS]** -- None returned AND
warning fired naming the Hvo.

## Item 4 -- silent path, MorphRA set but MorphTypeRA is None

No naturally-occurring bundle with this state was found in Sena 3 (matches
cycle-1: every non-None `MorphRA` in the 1932-sample carried a MorphType).
Constructed one: created a new `MoStemAllomorph` via
`IMoStemAllomorphFactory`, added to a real entry's `AlternateFormsOS`.
**Discovery**: LCM auto-infers a default `MorphTypeRA` (`"root"`) as a
side effect of the `Add` committing -- the freshly-created form was NOT
typeless immediately after commit. Cleared it explicitly in a follow-up
transaction (`typeless_form.MorphTypeRA = None`), confirmed
`MorphTypeRA is None`, linked it via `SetMorph(bundle, typeless_form)`,
then called `GetMorphType(bundle)` under `caplog`.
Post-state: returned `None`; `caplog.records` at WARNING+ = empty.
**[PASS]** -- silent None, no warning. Restored the bundle's original
`MorphRA` in `finally:`, confirmed by re-read.

## Item 5 -- SetMorphType retired, both forms, both write modes

Pre-state: bundle `MorphRA.Hvo` captured; `ActionHandlerAccessor
.UndoableActionCount` captured.
Action: called `SetMorphType(bundle, <real IMoMorphType>)` and
`SetMorphType(bundle, None)`, each under `project.writeEnabled = True`
then `project.writeEnabled = False` (same live LCM cache/session; this
is what SetMorphType's "no _EnsureWriteEnabled call" guarantees --
identical behaviour regardless of the flag).
Post-state: all 4 calls raised `FP_ParameterError` with byte-identical
message text across write-enabled/simulated-read-only and non-None/None.
`UndoableActionCount` unchanged; `bundle.MorphRA.Hvo` unchanged (re-read
from the live object). **[PASS]**

## Item 6 -- GetMorph

`GetMorph(bundle_with_morph)` -> `IMoForm`, `ClassName=MoStemAllomorph`,
`Hvo` matches `bundle.MorphRA.Hvo`. `GetMorph(bundle_without_morph)` ->
`None`, `caplog` empty (no warning). **[PASS]**

## Item 7 -- SetMorph round-trip, clear, and IMoMorphType guard

Pre-state: `bundle_a.MorphRA.Hvo = X`.
Action 1: `SetMorph(bundle_a, other_morph)`. Post-state (re-fetched via
`IWfiMorphBundle(project.Object(bundle_a.Hvo))`, a fresh object, not the
in-memory reference): `MorphRA.Hvo == other_morph.Hvo`. **[PASS]**
Action 2: `SetMorph(bundle_a, None)`. Post-state (re-fetched): `MorphRA is
None`. **[PASS]** -- confirms this genuinely replaces the retired
`SetMorphType(bundle, None)` capability.
Action 3: `SetMorph(bundle_a, <real IMoMorphType, ClassName=MoMorphType>)`.
Raised `FP_ParameterError`: `"SetMorph: morph_or_hvo must resolve to an
IMoForm (e.g. MoStemAllomorph, MoAffixAllomorph); received an object with
ClassName='MoMorphType'"` -- NOT the raw pythonnet
`TypeError: ... cannot be converted to SIL.LCModel.IMoForm`. Re-read
confirmed `MorphRA` still `None` (the rejected call caused no mutation).
**[PASS]** -- the `isinstance(morph, IMoForm)` guard works unmodified
against a real LCM `IMoMorphType` object; no code change was needed.
Restored original `MorphRA` in `finally:`, confirmed by re-read.

## Item 8 -- InflClassRA existence (reflection only, no fix)

`hasattr(bundle, "InflClassRA")` -> `False`. Direct access
`bundle.InflClassRA` raised `AttributeError: 'IWfiMorphBundle' object has
no attribute 'InflClassRA'`.
**ANSWER: NO** -- `InflClassRA` does not exist on live `IWfiMorphBundle`.
`GetInflectionClass`/`SetInflectionClass` (:1113/:1166 -- read/written
unguarded) are reading/writing a field that does not exist on this
interface at all. This confirms the spec's "Out of scope" suspicion and
should be filed as its own issue (Category 8 shape: unguarded access to a
possibly-nonexistent field). Not fixed here per instructions.

## Cleanup

`sena3_sandbox` is a tempdir-scoped fixture; disposed automatically on
teardown. Both write tests (items 4, 5, 7) restored the bundle's original
`MorphRA` in a `finally:` block and re-read to confirm restoration before
the sandbox was discarded. The real Sena 3 project was never opened.

## Mock suite (regression, supplementary)

`python -m pytest -m "not requires_live_project" -q` -> 1480 passed, 0
failed (5 subtests passed).

## Result

[PASS] -- all 8 items confirmed live, `run_mode: live`, values re-queried
from the LCM after each write. No code change required in
`WfiMorphBundleOperations.py`: item 1's bare access and item 7's
`isinstance` guard both worked correctly unmodified against real LCM
objects. Item 8 answered NO (InflClassRA does not exist) and is flagged
for a separate issue, not fixed here.

## Re-stamp after cycle-3 cleanup

**Date:** 2026-09-07

**Commands:**
```
python -m pytest -m "not requires_live_project" -q
```
```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue254_live_cycle2.py -m requires_live_project -q
```

**run_mode:** live (`tests/live_status.json` -> `"run_mode": "live"`,
`run_timestamp: 2026-09-07T05:04:39Z`)

**Offline suite:** 1480 passed, 0 failed.
**Live suite:** 8 passed.

Cycle-3 diff-scope confirmed non-behavioural: `GetMorphType`'s return
statement (`return morph.MorphTypeRA if morph.MorphTypeRA else None`) is
byte-identical to the cycle-2-verified version; the only executable
changes were deletion of the zero-caller `__GetMorphTypeObject` and
removal of the now-unused `IMoMorphType` import (confirmed unreferenced
outside docstring prose). Cycle-2 verdict stands: PASS.
