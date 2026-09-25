# Issue #449 -- cycle 1, lex-programmer report

## Fix

Added `BaseOperations._UnwrapLcm` (isinstance-based: `LCMObjectWrapper` ->
`.lcm_object`, `PythonicWrapper` -> `unwrap()`, else passthrough).
Applied at: `BaseOperations._GetObject`, `MoveUp`/`MoveDown`/`MoveToIndex`
(unwrap `item`), `MoveBefore`/`MoveAfter`/`Swap` (unwrap both items),
`_FindCommonSequence` (defensive unwrap of both items);
`AllomorphOperations.__GetAllomorphObject`; `MSAOperations.__GetMsaObject`
(replaced ad-hoc `._obj` branch) and `ChangeAffixVariant`;
`MorphRuleOperations.__ResolveObject` (covers `Delete`/`Duplicate`/
`SetStratum`/`SetDisabled`/`GetName`/etc.);
`PhonologicalRuleOperations.__ResolveObject` (replaced ad-hoc
`hasattr(_obj)`/`hasattr(_concrete)` duck-typing, which missed
`PythonicWrapper`); `WfiMorphBundleOperations.__GetMorphObject` /
`__GetMSAObject`; `LexSenseOperations.SetGrammaticalInfo`.
`FLExProject.LexiconGetAllomorphForms` needed no direct change -- it now
works because `Allomorphs.GetForm` is fixed.

Docstrings updated: `AllomorphOperations.GetAll`, `MSAOperations.GetAll`,
`MorphRuleOperations.GetAll`/`GetAllCompoundRules`/
`GetAllAffixTemplates`/`GetAllAffixTemplatesForPOS` (also fixed the wrong
`Returns` line claiming raw `IMoCompoundRule`/`IMoInflAffixTemplate`),
`PhonologicalRuleOperations.GetAll`. Added
`docs/API_ISSUES_CATEGORIZED.md` Category 13.

## Out of scope, confirmed and left alone

`MorphRuleOperations.Delete`'s `MoInflAffixTemplate` branch and
`__DuplicateAffixTemplate` both resolve the owner via
`self._GetObject(rule.Owner.Hvo)` / `source.Owner.Hvo`, returning a bare
`ICmObject` lacking `AffixTemplatesOS`. This bug occurs with or without a
wrapper and needs a typed-owner resolver, not `_UnwrapLcm`; noted in the
docs Category 13 entry for a follow-up issue.

## Tests

Offline: `tests/operations/test_449_wrapper_resolver_unwrap.py`, 23
tests -- `_UnwrapLcm` unit tests plus one test per fixed resolver using
fake LCM objects + monkeypatched cast recorders. **23/23 pass** against
the fix; **21/23 fail** against unmodified origin/main code (verified by
stashing the production changes and re-running).

Full offline suite: `python -m pytest -m "not requires_live_project" -q`
-> 148 failed, 2109 passed, 39 skipped, 48 errors. Confirmed via the same
stash test that all 148 failures/48 errors are pre-existing on
unmodified main (baseline: 168 failed, 2089 passed, 48 errors -- the
20-ish delta is exactly this fix's new offline test file). No new
offline failure introduced.

Live: `tests/operations/test_449_getall_roundtrip_live.py`
(`requires_live_project`, `sena3_sandbox`), run with
`FLEXLIBS_REQUIRE_LIVE=1` -> **6/6 pass**. `tests/live_status.json` shows
`"run_mode": "live"`. Per-`ClassName` counts read back from the LCM:
Allomorphs `{'MoStemAllomorph': 1485, 'MoAffixAllomorph': 145}`; MSAs
`{'MoStemMsa': 1405, 'MoInflAffMsa': 115, 'MoDerivAffMsa': 11,
'MoUnclassifiedAffixMsa': 4}` (all four subtypes present and asserted
non-zero); MorphRules `{'MoExoCompound': 4, 'MoInflAffixTemplate': 25}`;
PhonologicalRules `{}` (none defined in Sena 3 -- not hard-failed,
dataset-dependent). A `MoveToIndex` reorder call on a wrapper item
(moved to its own current index) also passed. Full detail, exact
commands, and sample values in
`specs/449-wrapper-resolver-unwrap/evidence/live-T6.md`.

Note: this worktree's `tests/fixtures/` did not contain the Sena 3
`.fwbackup`; it was copied in (read-only) from the sibling
`C:/Github/flexicon` checkout to run the live gate, without modifying
that other worktree.

## Commits (branch fix/449-wrapper-resolver-unwrap)

- `b8e4b92` fix(operations): unwrap GetAll() wrapper items before
  resolver casts
- `bb95a1a` test(#449): offline regression for wrapper-resolver unwrap
- `af45c41` test(#449): live GetAll() wrapper roundtrip against Sena 3
  sandbox (also updates tasks.md T1-T7 and STATUS.md)

Not pushed. `tasks.md` T1-T7 checked; T8 (QC + domain review, PR) left
for the next step.
