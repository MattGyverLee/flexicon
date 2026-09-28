# Domain Expert Review -- Issue #449 (wrapper resolver unwrap), cycle 2

Source: lex-domain agent (read-only), saved by the main session.

## (1) FAIL (partial) -- round-trip contract documented only in an issues log
`_UnwrapLcm` is applied at every resolver the cycle-1 sweep found, and offline/live tests back it, so "every GetAll() item can be passed straight back" is now true for the four wrapper-returning families. But it is documented only in `docs/API_ISSUES_CATEGORIZED.md` Category 13 and code docstrings. `docs/ARCHITECTURE_WRAPPERS.md` and `docs/API_DESIGN_PHILOSOPHY.md` say nothing about `_UnwrapLcm` or the round-trip guarantee, and the "Creating a new wrapper" checklist in ARCHITECTURE_WRAPPERS.md doesn't tell future authors to route resolvers through it. Recommend a short "round-trip contract" paragraph in both docs before merge (or immediate follow-up).

## (2) PASS, follow-up recommended
`.lcm_object` matches the `cast_to_concrete()` escape-hatch precedent (Rule 1). But `LCMObjectWrapper` has no `__eq__`/`__hash__`, so `raw == wrapper` is False and `item in raw_sequence` / set/dict usage fails outside Operations calls. Recommend `__eq__`/`__hash__` by Hvo as a follow-up issue, not this PR (broader identity/hash semantics).

## (3) PASS
Reorder semantics (index 0 = top/primary, clamping) unchanged; the fix only repairs item lookup so wrapped items are found. Matches FLEx UI ordering.

## (4) Does not block; recommend P2, not P1
Affix-template owner bug is pre-existing and wrapper-independent, already flagged out of scope. It affects one MorphRule subtype (MoInflAffixTemplate) with a workaround -- closer to the P2 calibration (#329) than P1.
