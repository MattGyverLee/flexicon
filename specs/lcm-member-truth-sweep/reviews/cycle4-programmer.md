# Cycle 4 -- Programmer report (T4.1, T4.2, T4.3, T4.6)

Campaign: `lcm-member-truth-sweep`, checkpoint 4, issue #259.
Scope executed: T4.1, T4.2, T4.3, T4.6. T4.4, T4.5, T4.7 explicitly NOT done
(T4.4/T4.5 are the `SetInflectionClass` write path, blocked by ruling C11 /
open question Q2; T4.7 is live verification, deferred to next cycle per the
brief).

## T4.1 -- Navigation helper: location, signature, routing

**Home chosen:** `flexicon/code/lcm_casting.py`, immediately after the
existing `get_pos_from_msa()` function, which is the in-repo precedent for
"dispatch an MSA-subtype-specific property read through a ClassName ->
property-name map, narrowed via the existing `_interface_cache`." This
keeps the single source of truth next to its sibling instead of introducing
a second navigation idiom.

New code (`flexicon/code/lcm_casting.py`, ~line 645 onward):

```python
_MSA_INFLECTION_CLASS_PROPERTY = {
    "MoStemMsa": "InflectionClassRA",
}

INFLECTION_CLASS_BEARING_MSA_CLASSES = frozenset(_MSA_INFLECTION_CLASS_PROPERTY)


def get_inflection_class_from_msa(msa):
    """Get the inflection class (IMoInflClass) from an MSA, if any."""
    if msa is None:
        return None
    _ensure_interfaces()
    if not hasattr(msa, "ClassName"):
        return None
    class_name = msa.ClassName
    infl_class_property = _MSA_INFLECTION_CLASS_PROPERTY.get(class_name)
    if infl_class_property is None:
        return None
    try:
        interface_type = _interface_cache.get(class_name)
        if interface_type:
            concrete = interface_type(msa)
            return getattr(concrete, infl_class_property)
    except Exception:
        pass
    return None
```

**Signature:** `get_inflection_class_from_msa(msa) -> IMoInflClass | None`.
Takes the MSA directly (not the bundle), mirroring `get_pos_from_msa(msa)`,
so it composes cleanly at every call site: `get_inflection_class_from_msa(bundle.MsaRA)`.

**Guards satisfied (per C10):**
- Null MSA -> `None` (explicit `if msa is None` at the top, so callers don't
  even need their own null check on `bundle.MsaRA` before calling it).
- Narrowed to `IMoStemMsa` specifically, via the `_MSA_INFLECTION_CLASS_PROPERTY`
  dict keyed on `ClassName == "MoStemMsa"` -- `MoDerivAffMsa`,
  `MoInflAffMsa`, `MoUnclassifiedAffixMsa` all fall through to `None` because
  they are not in the dict. This is the "narrow to IMoStemMsa" requirement,
  done by ClassName dispatch (equivalent to, and no weaker than, a
  `cast_to_concrete()` + `hasattr` check, since `InflectionClassRA` is only
  declared on `MoStemMsa` among the four MSA subtypes -- confirmed by the
  cycle-1 reflection dump in `specs/lcm-member-truth-sweep/evidence/live-cycle1-reflection.md`).
- Never raises: `hasattr(msa, "ClassName")` guard, dict `.get()` returning
  `None` for unrecognized/non-stem ClassNames, and a `try/except Exception:
  pass` around the actual property read (covers a failed CLR cast or a
  property read that errors for an unexpected reason).

**Routed call site (T4.1 proper):**
`flexicon/code/TextsWords/WfiMorphBundleOperations.py`, `GetInflectionClass`
(now at line 1298, was line 1261 pre-edit):

```python
bundle = self.__GetBundleObject(bundle_or_hvo)
# IWfiMorphBundle has no InflClassRA member of its own (issue #259
# / lcm-member-truth-sweep C10). The inflection class lives on the
# bundle's MSA (IMoStemMsa.InflectionClassRA); get_inflection_class_from_msa()
# navigates MsaRA -> cast -> narrow to IMoStemMsa -> InflectionClassRA,
# returning None for a null MsaRA or a non-stem MSA subtype without
# ever raising.
return get_inflection_class_from_msa(bundle.MsaRA)
```

Import added at module top of `WfiMorphBundleOperations.py`:
`from ..lcm_casting import get_inflection_class_from_msa` (module-level
import, matching the existing style of `POSOperations.py:28`,
`LexSenseOperations.py:52`, `morphosyntax_analysis.py:71`, which all import
`get_pos_from_msa` the same way, rather than the lazy in-function
`from ..lcm_casting import cast_to_concrete` idiom used elsewhere for
one-off casts).

## T4.2 -- The three silent copy loops: case (a)/(b) finding

**Verdict: all three sites are case (a) -- MsaRA is already copied by
reference in every one of them, immediately before the dead InflClassRA
line.** No sibling-mutation write (case b) is needed or implemented
anywhere. Evidence, file:line, pre-edit:

1. `flexicon/code/TextsWords/WfiMorphBundleOperations.py` (`Duplicate`):
   `if hasattr(source, "MsaRA") and source.MsaRA: duplicate.MsaRA = source.MsaRA`
   at (pre-edit) lines 331-332, immediately followed by the dead
   `if hasattr(source, "InflClassRA") and source.InflClassRA: duplicate.InflClassRA = source.InflClassRA`
   at lines 335-336.
2. `flexicon/code/TextsWords/WfiAnalysisOperations.py` (`Duplicate`, deep
   morph-bundle copy loop): `if hasattr(bundle, "MsaRA") and bundle.MsaRA:
   new_bundle.MsaRA = bundle.MsaRA` at (pre-edit) lines 585-586, immediately
   followed by the dead InflClassRA pair at lines 589-590.
3. `flexicon/code/TextsWords/WordformOperations.py` (`Duplicate`, nested
   analysis/morph-bundle deep copy loop): `if hasattr(bundle, "MsaRA") and
   bundle.MsaRA: new_bundle.MsaRA = bundle.MsaRA` at (pre-edit) lines
   874-875, immediately followed by the dead InflClassRA pair at lines
   878-879.

In all three, `MsaRA` is a Reference Atomic assignment
(`new_bundle.MsaRA = bundle.MsaRA`), which assigns the SAME MSA object --
it is not cloned. Since `InflectionClassRA` is a property read off that
same MSA object (per T4.1), the duplicate bundle already sees the
identical inflection class as its source the moment `MsaRA` is copied,
with zero extra code. There is no scenario here requiring a write to
`msa.InflectionClassRA` (the case-(b) / C11-blocked shape) -- deleting the
dead `hasattr(..., "InflClassRA")` guard and its dead body is the complete
and correct fix.

**Fix applied at all three sites:** the two dead lines
(`hasattr(..., "InflClassRA")` guard + `... .InflClassRA = ...` body) were
deleted and replaced with an explanatory comment citing the MsaRA-reference
mechanism and pointing at `get_inflection_class_from_msa()` for the read
path. No behavior changes for any caller: the dead code never ran (the
`hasattr` guard was always `False` since `InflClassRA` does not exist on
`IWfiMorphBundle`), so removing it changes nothing observable except
deleting an always-false branch.

Since all three sites resolved to case (a), none of them needed to import
the T4.1 helper -- there is no navigation logic left at these sites to
duplicate or share. The brief's "other two files must import it, not
duplicate the logic" contingency was for a case-(b) outcome that did not
materialize.

## T4.3 -- `GetSyncableProperties` key-name decision

`flexicon/code/TextsWords/WfiMorphBundleOperations.py`, `GetSyncableProperties`
(now ~line 393-407, was 385-386 pre-edit dead block):

```python
infl_class = get_inflection_class_from_msa(getattr(item, "MsaRA", None))
if infl_class is not None:
    props["InflClassRA"] = str(infl_class.Guid)
```

**Key name decision: KEPT as `"InflClassRA"`** (did not rename to e.g.
`"MsaRA.InflectionClassRA"` or `"InflectionClassRA"`). Justification:

- This is a sync/diff payload key, not an LCM member name -- its contract
  is with external sync consumers and `CompareTo()`'s diff dict, not with
  pythonnet attribute resolution. Nothing reads `props["InflClassRA"]` by
  reflecting it back onto a live LCM object; it flows through
  `GetMultiStringDict`-style comparison and (de)serialization.
- Renaming it would be a breaking change to any existing sync snapshot,
  diff, or persisted payload keyed on `"InflClassRA"`, for zero semantic
  gain: the *meaning* of the field to a sync consumer -- "the bundle's
  effective inflection class GUID" -- has not changed, only the internal
  LCM navigation path used to compute the value.
- This mirrors the precedent already in this same file for `Gloss`: the
  bundle's syncable surface documents that `Form` is the only MultiString
  even though the *displayed* gloss is sourced from `SenseRA.Gloss` --
  i.e., this codebase already accepts "syncable key name reflects the
  logical field, not the literal LCM navigation path" as the norm.

Docstring `Notes:` updated accordingly (see T4.6).

## T4.6 -- Docstring / Notes / See-Also truth updates

All edits are in the three touched Python files; none of the edits alter
behavior, only documentation.

**`flexicon/code/TextsWords/WfiMorphBundleOperations.py`:**
- `Duplicate` docstring `Notes:` (was line ~289-290): replaced
  `Reference properties copied: SenseRA, MsaRA, MorphRA, InflClassRA` with
  a split bullet: `SenseRA, MsaRA, MorphRA` copied, plus a new bullet
  explaining `InflClassRA` is not a real member and rides along via the
  shared MSA, pointing to `GetInflectionClass`.
- `GetSyncableProperties` docstring `Notes:` (was line ~378): replaced the
  blanket `Reference Atomic properties: SenseRA, MsaRA, MorphRA, InflClassRA
  (GUIDs)` bullet with `SenseRA, MsaRA, MorphRA` plus a dedicated bullet
  explaining the `InflClassRA` key's MSA-derived value and the
  stability-of-key-name decision (T4.3).
- `GetInflectionClass` docstring `Notes:` (was lines ~1247-1252, now
  ~1278-1291): added two new leading bullets stating plainly that
  `IWfiMorphBundle` has no `InflClassRA` member, spelling out the
  `MsaRA -> cast_to_concrete() -> IMoStemMsa -> InflectionClassRA` route
  and the three `None`-producing conditions (null MsaRA, non-stem MSA,
  unset class on a stem MSA).
- `SetInflectionClass` docstring `Notes:` (was lines ~1286-1290, now
  ~1326-1339): added a leading `BLOCKED` bullet documenting that the
  method currently writes `bundle.InflClassRA` directly, which raises
  `AttributeError` on every call, that the correct target is the MSA, and
  that the write is withheld pending a domain ruling on the
  shared-MSA/sibling-mutation risk (C11/Q2). **The code itself
  (`bundle.InflClassRA = infl_class`) was NOT touched**, per the hard
  constraint -- only the docstring was corrected to stop implying the
  method works.
- `GetInflType`/`SetInflType` `See Also:` lines (originally cited as 1157,
  1200 in the brief) were inspected and left unchanged: they only name the
  sibling method `GetInflectionClass`/`SetInflectionClass`, they do not
  themselves claim `InflClassRA` is a bundle member, so there was nothing
  false to correct there.

**`flexicon/code/TextsWords/WordformOperations.py`:**
- `Duplicate` docstring, "Analysis Deep Copy" section (was line 785): split
  `Morph bundle references: SenseRA, MsaRA, MorphRA, InflClassRA` into
  `SenseRA, MsaRA, MorphRA` plus an explanatory parenthetical mirroring the
  `WfiMorphBundleOperations.Duplicate` fix.

**`docs/FUNCTION_REFERENCE.md:57-58` -- NO CHANGE, with reasoning:**
I checked this cited range and it documents
`project.POS.GetInflectionClasses(pos_or_hvo)` / `IPartOfSpeech.InflectionClassesOC`
-- i.e. the **`POSOperations`** surface, not `WfiMorphBundleOperations`.
`InflectionClassesOC` on `IPartOfSpeech` is the real, live member the brief
itself says to leave alone ("LEAVE `POSOperations.py:783-854` ALONE --
`InflectionClassesOC` is a real member there"). I grepped the whole doc for
`GetInflectionClass`/`SetInflectionClass`/`InflClassRA` and confirmed
`WfiMorphBundleOperations.GetInflectionClass`/`SetInflectionClass` have no
entry in `FUNCTION_REFERENCE.md` at all to correct. I made no edit to this
file -- editing the cited lines would have meant changing accurate
documentation of an unrelated, legitimate member, which the brief itself
forbids. Flagging this as a likely stale/mismatched line reference in the
brief rather than silently skipping it.

## Files changed (full list, file:line is post-edit unless noted)

- `flexicon/code/lcm_casting.py` -- added `_MSA_INFLECTION_CLASS_PROPERTY`,
  `INFLECTION_CLASS_BEARING_MSA_CLASSES`, `get_inflection_class_from_msa()`
  (new, ~75 lines, inserted after `get_pos_from_msa`, before `clone_properties`).
- `flexicon/code/TextsWords/WfiMorphBundleOperations.py`:
  - added import `from ..lcm_casting import get_inflection_class_from_msa`
  - `Duplicate`: deleted dead `InflClassRA` copy lines, added explanatory
    comment; updated docstring `Notes:`
  - `GetSyncableProperties`: routed `InflClassRA` key through the helper;
    updated docstring `Notes:`
  - `GetInflectionClass`: routed body through the helper; updated docstring
    `Notes:`
  - `SetInflectionClass`: docstring `Notes:` only (added `BLOCKED` bullet);
    **code untouched**, per hard constraint
- `flexicon/code/TextsWords/WfiAnalysisOperations.py`: deleted dead
  `InflClassRA` copy lines in the `Duplicate` deep-copy loop, added
  explanatory comment (no docstring claim existed here to fix)
- `flexicon/code/TextsWords/WordformOperations.py`: deleted dead
  `InflClassRA` copy lines in the `Duplicate` nested deep-copy loop, added
  explanatory comment; updated `Duplicate` docstring "Analysis Deep Copy"
  section

## Regression check (offline)

```
python -m pytest -m "not requires_live_project" -q
```

Result: **1878 passed, 805 deselected, 0 failed** (12 warnings, all
pre-existing/unrelated -- `PytestUnknownMarkWarning` for `integration` mark,
a `PytestCollectionWarning` for two helper classes with `__init__`, a
`PytestReturnNotNoneWarning`, and `DeprecationWarning`s for the pre-existing
`GramCatOperations` alias). Matches the expected 1878/0 exactly. Ran the
non-path-scoped form as instructed (not `pytest tests/ -m ...`). Did not run
bare `pytest`.

I also verified with `python -m py_compile` on all four touched `.py` files
before running the suite; all compiled cleanly.

## Left undone (deliberately, per scope)

- **T4.4 / T4.5** (the `SetInflectionClass` write-path fix): not touched.
  `bundle.InflClassRA = infl_class` at the tail of `SetInflectionClass`
  remains exactly as it was -- still raises `AttributeError` on every
  call, per ruling C11. Only its docstring now says so.
- **T4.7** (live verification): not run this cycle, per the brief. The
  `get_inflection_class_from_msa()` helper and its three routed call sites
  (`GetInflectionClass`, `GetSyncableProperties`, and the confirmed-dead
  deletions in the three `Duplicate` copy loops) are unverified against a
  live LCM database as of this report. This is a **FAIL: unverified**
  status for live-LCM purposes per CLAUDE.md's Live LCM Verification
  section, not a clean pass -- flagging explicitly so checkpoint 5/T4.7
  picks it up rather than it being mistaken for already-verified.
- Two existing live-only reflection test files
  (`tests/operations/test_lcm_member_truth_sweep.py`,
  `tests/operations/test_issue254_live_cycle2.py`) reference `InflClassRA`
  but only via `hasattr`/reflection probes against raw LCM objects -- they
  do not exercise the production code changed here, so no anchor flip was
  needed or made in this cycle's offline pass. Worth a quick look during
  T4.7 to confirm they still pass live and cite the resolved C10 status.
- Did not touch `flexicon/code/Grammar/POSOperations.py:783-854` or
  `docs/FUNCTION_REFERENCE.md:57-58`, per the brief / the finding above.
- No commit made (per instruction; the lead commits at T4.8).
