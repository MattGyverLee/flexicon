# Live verification -- issue #348 `OcmCodes` scalar + `QuestionsOS` duplicate blocker

Live-LCM evidence for the fixes on branch `fix/348-ocmcodes-none`:

1. `ICmSemanticDomain.OcmCodes` is a scalar Unicode / `System.String`,
   not an `IMultiString`: `GetSyncableProperties`, `GetOcmCodes()` and
   `Duplicate()` no longer call `.get_String()` / `.CopyAlternatives()`
   on it.
2. The `Duplicate()` `QuestionsOS` blocker (issue #352 item A) is fixed:
   `duplicate.Questions.CopyAlternatives(source.Questions)` raised on a
   nonexistent member before the `OcmCodes` copy could run.

## Exact command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue348_ocmcodes_scalar_live.py -m requires_live_project -q
```

Result: `8 passed in 4.29s` (all `target_sandbox`).

Count probe, run separately with `-s`:

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_issue348_ocmcodes_scalar_live.py::TestOcmCodesLiveType::test_get_syncable_properties_never_raises_across_all_domains -m requires_live_project -q -s
```

## run_mode

`tests/live_status.json` after the run:

- `"run_mode": "live"`
- `"run_timestamp": "2026-09-21T06:53:03Z"`
- `SemanticDomainOperations` `modify` and `read` phases: `"status": "pass"`,
  `"last_verified": "2026-09-21"`.

## Pre-state and post-state (read back from the LCM)

| Probe | Pre-state (pre-fix, from issue #348 + live sandbox) | Post-state (post-fix, read back live) |
|---|---|---|
| 1. Type across every domain | `.get_String()` on `None` raised `AttributeError` for **1792/1792** domains (issue #348) | `type(domain.OcmCodes)` is `NoneType` or `str` for every domain; `GetSyncableProperties` returned `props["OcmCodes"] == ""` for every unset domain. Count probe: **`[issue #348] GetSyncableProperties: 1792/1792 domains passed`** (`1 passed in 2.11s`) |
| 2. Populated read-back | n/a (population was impossible through the raising accessors) | `domain.OcmCodes = "TEST_484"` -> `GetSyncableProperties(domain)["OcmCodes"] == "TEST_484"`; `domain.OcmCodes = "TEST_271"` -> `GetOcmCodes(domain) == "TEST_271"` |
| 3. `Duplicate()` unset | raised `AttributeError` (`duplicate.Questions.CopyAlternatives` first, or `None.get_String` / `None.CopyAlternatives`) | unset source -> duplicate has `OcmCodes in (None, "")`, `len(duplicate.QuestionsOS) == len(source.QuestionsOS)`, no raise |
| 3. `Duplicate()` populated + seeded questions | same raised path | `TEST_117` copied verbatim; seeded CmDomainQ question `TEST_What words refer to walking?` (via `ICmDomainQFactory` + `Question.set_String`) appears in the duplicate's own `QuestionsOS` texts, count matches source, entries are fresh objects |
| 4. Apply/get round-trip | n/a | `source.OcmCodes = "TEST_648"`; `GetSyncableProperties(source)["OcmCodes"] == "TEST_648"`; `ApplySyncableProperties(target, props)`; re-querying **from the LCM**: `GetSyncableProperties(target)["OcmCodes"] == "TEST_648"` and `target.OcmCodes == "TEST_648"` |

Evidence provenance note (probes 2-4): the Target sandbox's semantic
domains come mostly unset out of the box, so the populated cases were
seeded by **direct assignment / factory-created CmDomainQ**, a
materially different provenance from reading pre-existing data. The
seeded-question probe also exercises a genuinely pre-existing data path:
the first Target domain already carries a catalog-imported `CmDomainQ`,
and `Duplicate()` copied it along with the newly seeded one (count 2 ==
source count 2), which is exactly the read-path through pre-existing
data the probe intended to cover.

## Pass/fail line

`8 passed in 4.29s` -- `FAILED: none`. Run mode `live` confirmed above.