# Live verification -- issue #561

`MorphRuleOperations.__ResolveObject` cast a resolved `ICmObject` to a
concrete interface only when `ClassName == "PartOfSpeech"`. The other
three types this class resolves -- `MoInflAffixTemplate`,
`MoEndoCompound`, `MoExoCompound` -- were returned as a bare `ICmObject`,
so a documented input shape (HVO / raw object) raised on every call.

## Commands

Offline gate:

```
python -m pytest -m "not requires_live_project" -q
```

Result: `2575 passed, 1078 deselected, 16 warnings in 13.45s`

Live gate (`FLEXLIBS_REQUIRE_LIVE=1` converts any silent degradation to a
hard failure):

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue561_morphrule_resolver_cast_live.py tests/operations/test_issue467_morphrule_owner_cast_live.py -m requires_live_project -q
```

Result: `6 passed in 3.54s`

`tests/live_status.json` -> `"run_mode": "live"`. Not mock mode.

## Base

Branched from `origin/main` at `6f65cf2`. `__ResolveObject` on main is
byte-identical to the version fixed here, so the defect is still live on
the default branch (the file does carry 31 lines of unrelated change
between `release/4.10.0` and main; both gates were re-run against main).

## Pre-fix state (fix reverted, same live run)

With `flexicon/code/Grammar/MorphRuleOperations.py` restored to its
pre-fix state (the POS-gated cast), the same live command gives:

```
3 failed, 1 passed in 3.05s
```

```
E  AttributeError: 'ICmObject' object has no attribute 'Name'
flexicon\code\Grammar\MorphRuleOperations.py:948: AttributeError
```

at `duplicate.Name.CopyAlternatives(source.Name)`, reached from
`Duplicate(project.Object(hvo), ...)` -- the exact failure reported in
the issue body.

The fourth test, `test_part_of_speech_hvo_still_casts`, passes both
before and after. It is the non-regression guard for the pre-existing POS
cast, which `AddSlotToTemplate` depends on (`AllAffixSlots` is only
reachable on `IPartOfSpeech`).

## Read-back from the LCM

Assertions are on values re-queried out of the LCM, not on the objects
returned by the write call:

- affix template -- `_template_still_on_pos()` re-walks
  `IPartOfSpeech.AffixTemplatesOS` looking for the duplicate's HVO, and
  asserts non-`None`; the POS's template count is read back before and
  after (`before + 2`).
- compound rule -- `_compound_rule_by_hvo()` re-walks
  `MoMorphData.CompoundRulesOS`; count read back as `before + 1`.
- `GetName(hvo)` is called on the HVO form, which only resolves if the
  cast happened, and is checked to equal the source name.
- the duplicate's HVO is asserted different from the source's, and the
  duplicate is cleaned up in a `finally:` under the `TEST_561_` prefix.

## Note on the issue's cited evidence

The issue cites
`tests/operations/test_issue537_morphrule_duplicate_hvo_live.py::test_duplicate_affix_template_insert_after_raw_object_view`
as its reproduction. That file and that test name do not exist anywhere
in the repository (checked by filename glob and by grepping the whole
`tests/` tree). The reproduction above was written from scratch for this
change; the defect and the failing call site match the issue report
exactly, but the cited test itself could not be run.
