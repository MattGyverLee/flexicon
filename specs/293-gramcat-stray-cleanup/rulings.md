# Issue #293 -- lex-lead ruling

**Date:** 2026-09-24  
**HEAD:** `fix/293-gramcat-stray-docs` from `origin/main`

## Triage context

Cron selection after repository scan:

| Priority | Open without open PR |
|----------|----------------------|
| P0 | none |
| P1 | none |
| P2 | none (each open P2 already has an in-flight cron PR) |
| **Selected** | **P3 #293** -- documentation-only follow-up from #276 |

## RULING (binding)

Issue #293 is **documentation only**. No auto-migration script, no new
Operations API, no LCM write path.

Parent ruling Q4 in `specs/276-gramcat-collection/evidence/domain-ruling.md`
stands: strays in `LangProject.MsFeatureSystemOA.TypesOC` cannot be
distinguished from legitimate `InflectionFeatures.TypeCreate` output and may
be referenced via `TypeRA`. Humans decide in FLEx.

**Deliverables for this PR:**

1. Expand `docs/MIGRATION_GUIDE.md` under the GramCat breaking-change
   section with an explicit hand-cleanup recipe matching the issue checklist
   (affected scripts, where to look in FLEx, pre-delete checks, UI deletion,
   forward API, no auto-migration statement).
2. Offline content ratchet:
   `tests/test_issue293_gramcat_stray_docs_ratchet.py` pins required phrases
   so the recipe cannot silently shrink.
3. Evidence file under `specs/293-gramcat-stray-cleanup/evidence/offline-293.md`.

**Out of scope:** orphan scans, population counts, flexicon code changes.

## Verification plan

```bash
python3 -m pytest tests/test_issue293_gramcat_stray_docs_ratchet.py \
  -m "not requires_live_project" -q
```

No live LCM verification required (docs-only).
