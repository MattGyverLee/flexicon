# Issue #467 -- lex-lead ruling

## Diagnosis

`MorphRuleOperations.Delete` (MoInflAffixTemplate branch) and
`MorphRuleOperations.__DuplicateAffixTemplate` resolved the template owner
with `self._GetObject(rule.Owner.Hvo)`. HVO resolution returns the base
`ICmObject` view, which does not expose `AffixTemplatesOS`. The Delete path
guarded with `hasattr(owner, "AffixTemplatesOS")`, which is always False on
the base interface, so Delete silently no-opped. Duplicate accessed
`owner.AffixTemplatesOS` unguarded and raised `AttributeError`.

This is the same owner-cast bug class as issues #97/#98/#162: typed
collections live on concrete owner interfaces (`IPartOfSpeech`), not on
`ICmObject`.

## Resolution

Route the affix-template owner through `BaseOperations._GetTypedOwner()` in
both sites, matching `ExampleOperations.Delete` / `Duplicate` (#162).

## Verification

- Offline: `tests/operations/test_issue467_morphrule_owner_cast_offline.py`,
  `tests/operations/test_morphrule_duplicate_deep.py`.
- Live (required for write path): `tests/operations/test_issue467_morphrule_owner_cast_live.py`
  against `target_sandbox`, with LCM read-back after Delete and Duplicate.

## Priority

P2 confirmed: narrow surface (MoInflAffixTemplate only); raw LCM workaround
exists. Chosen because all open P0 issues already had in-flight PRs at pick
time and no open P1 bugs were filed.
