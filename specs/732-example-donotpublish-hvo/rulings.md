# Issue #732 -- lex-lead ruling

## Diagnosis

`ExampleOperations.AddDoNotPublishIn` and `RemoveDoNotPublishIn` used Python
membership (`publication in example.DoNotPublishInRC`) on an LCM reference
collection. pythonnet can surface the same LCM object as multiple Python
wrappers (concrete vs bare interface, or `project.Object(hvo)` vs the instance
held by the caller). Identity-based `in` then misreports membership: add may
attempt a duplicate link; remove may no-op while the publication remains
excluded.

## Resolution

Compare members by `Hvo` when testing membership. On remove, iterate
`DoNotPublishInRC`, find the linked member whose `Hvo` matches, and pass that
collection member to `Remove`. Factor publication name resolution into
`__ResolvePublication` (same shape as LexSense #726).

## Scope

`AddDoNotPublishIn` / `RemoveDoNotPublishIn` only. LexEntry/LexSense siblings
are tracked separately (#726–#730).

## Verification

- Offline ratchet: `tests/operations/test_issue732_example_donotpublish_hvo_offline.py`
- Live (Target sandbox): `tests/operations/test_issue732_example_donotpublish_hvo_live.py`
