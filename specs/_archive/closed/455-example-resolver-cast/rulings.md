# Issue #455 -- lex-lead ruling

**Date:** 2026-09-24  
**Issue:** #455 (P2) -- ExampleOperations HVO resolvers uncast  
**Parent triage:** #284 Class A promotion

## RULING (binding)

Cast both private resolvers through `cast_to_concrete` on every path:

- `__GetExampleObject` -- callers touch `ILexExampleSentence` members
  (`DoNotPublishInRC`, multilingual fields, publication helpers).
- `__GetSenseObject` -- callers touch `ILexSense` members when creating or
  listing examples from an HVO.

Do **not** add a ClassName guard that returns uncast objects on miss; match
`WfiMorphBundleOperations.__GetBundleObject` (issue #268 family).

## Pattern audit

Two helpers in one file, same defect. No other ExampleOperations resolver
returns bare `project.Object(hvo)` after this change.

## Verification plan

- Offline: source ratchet + mock test that HVO resolution uses
  `cast_to_concrete`.
- Live: `target_sandbox` gate calling a publication helper with an example HVO
  only (`requires_live_project`).
