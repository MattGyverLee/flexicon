# Issue #449 -- cycle 3, lex-programmer report

## Changes

1. `tests/operations/test_issue251_msa_feature_sync.py` --
   `test_get_msa_object_hasattr_calls_are_allowlisted` no longer requires
   "at least one hasattr()"; it now asserts (a) any hasattr() found in
   `__GetMsaObject` is allowlisted, and (b) `__GetMsaObject` routes its
   wrapper-unwrap through `self._UnwrapLcm(...)`. Comment block above it
   rewritten to describe cycle 1's replacement of the ad-hoc
   `hasattr(msa_or_hvo, "_obj")` unwrap. Grepped for
   `hasattr(msa_or_hvo` and `"_obj"` ratchets: the only other hit
   (`tests/operations/test_phon_features.py:603/607`) is the test's own
   local unwrap logic, not a ratchet on production resolver shape --
   left untouched.
2. `docs/ARCHITECTURE_WRAPPERS.md` -- new "The Round-Trip Contract"
   section (mechanism, `.lcm_object` caller-side cast, new-wrapper
   checklist item). `docs/API_DESIGN_PHILOSOPHY.md` -- cross-reference
   under Rule 1, plus a new numbered item in the "Creating a new
   wrapper" checklist. `docs/API_ISSUES_CATEGORIZED.md` Category 13
   already matched both -- left unchanged.
3. `specs/449-wrapper-resolver-unwrap/STATUS.md` -- added a cycle 3 line
   confirming the off-by-one was the stale ratchet, now fixed.

## Tests

`python -m pytest tests/operations/test_issue251_msa_feature_sync.py tests/operations/test_449_wrapper_resolver_unwrap.py -m "not requires_live_project" -q`
-> **48 passed, 8 deselected**. No live-touching code changed (docs +
one test-shape update), so no new live run required per CLAUDE.md scope.

## Commits (not pushed)

- `f1b9f5c` test: update the issue251 MSA hasattr ratchet
- `4ece234` docs: the wrapper round-trip contract
- `629eea5` docs: the untracked cycle 2 reviews and evidence

## Blockers

None. Two prior items are still explicitly waiting on the user per
STATUS.md: filing the affix-template owner bug (P2 vs P1) and the
wrapper `__eq__`/`__hash__`-by-Hvo follow-up -- untouched this cycle.
