# Cycle 3 verification (issues 630 / 631)

**Verdict:** PASS
**run_mode:** live (tests/live_status.json)

- Offline: `python -m pytest -m "not requires_live_project" -q` -> 3719 passed, 1174 deselected, 0 failed.
- Live: `FLEXLIBS_REQUIRE_LIVE=1 python -m pytest <630 live> <631 live> -m requires_live_project -q` -> 15 passed.
- New live tests re-query via p.Object(hvo) cast to IMoInflAffMsa / raw LCM FromProdRestrictRC / ToProdRestrictRC / MorphologicalDataOA.ProdRestrictOA; not asserting on inputs.
- ChangeAffixVariant: code snapshots From before creation, copies infl<->deriv; warns only for truly lost fields (deriv->infl: To; unclassified: From/To). Live tests assert To warned and From not; From carried.
- Docs: CHANGELOG.md [Unreleased] and docs/MIGRATION_GUIDE.md both have InflectionClassCreate entry.
- Commit messages 323009b, 21eba10, 1e5442f (subject+body): no close/fix/resolve directly before an issue number.

Issues: none.
