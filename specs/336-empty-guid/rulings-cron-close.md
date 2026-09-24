# Issue #336 -- lex-lead close-out ruling (cron)

**Date:** 2026-09-24  
**HEAD:** fix/336-empty-guid-close-out from origin/main

## Status

Behaviour fix landed on `main` via PR #373 (`9296501`). Issue #336 remained
open because the merge commit did not carry a `closes #336` keyword. The
`[Unreleased]` CHANGELOG entry was added in that PR; this close-out adds the
formal lex-lead ruling file and closes the issue.

## RULING (binding, close-out only)

1. No further LCM behaviour change -- guard at `PhonFeatureOperations.py`
   `__ApplyValues` and `__CreateValueWithGuid` matches
   `specs/336-empty-guid/rulings.md`.
2. Close #336 with this PR.

## Verification

- Offline: `python -m pytest tests/operations/test_issue334_guid_parse_formatexception.py -m "not requires_live_project" -q`
- Live: **FAIL: unverified** on cloud agent (no FieldWorks / pythonnet runtime).
