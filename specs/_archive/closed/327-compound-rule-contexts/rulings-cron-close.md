# Issue #327 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-24  
**HEAD:** fix/327-compound-rule-changelog from origin/main

## Status

Code fix landed on `main` via PR #389 (`7fda4c0`, `ec35efa`). Issue #327
remained open because the merge commit did not carry a `closes #327` keyword
and the `[Unreleased]` CHANGELOG entry was never added.

## RULING (binding, close-out only)

1. Add a **Fixed** bullet under `[Unreleased]` documenting removal of phantom
   `CompoundRule` context properties and exposure of `head_last`,
   `overriding_msa`, and `to_msa`.
2. Close #327 with this PR; no further LCM behaviour change.

## Verification

- Offline: `python -m pytest tests/operations/test_issue327_compound_rule_contexts.py tests/test_compound_rule_wrappers.py -m "not requires_live_project" -q`
- Live: unchanged from PR #389 evidence (`specs/327-compound-rule-contexts/evidence/live-327.md`).
