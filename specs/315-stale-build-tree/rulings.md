# Issue #315 -- lex-lead ruling

**Date:** 2026-09-24  
**Issue:** [#315](https://github.com/MattGyverLee/flexicon/issues/315) (P3)

## Diagnosis

A full duplicate package tree under `build/lib/flexicon/` (from legacy
`setup.py build` / packaging) can sit beside the editable-install source.
Imports on this machine resolve through the live tree, but editors, grep, and
future path tweaks can prefer the stale copy -- a hygiene trap, not a runtime
defect today.

## RULING (binding)

1. **`build/` must remain gitignored** and must **never** be tracked in git.
   There is no supported workflow that commits packaging artifacts under
   `build/lib/`.
2. **No code change** to import paths or MCP tooling -- verified behaviour stays
   as-is; this issue is repo hygiene plus a ratchet.
3. **Close #315** when an offline ratchet proves (a) `.gitignore` excludes
   `build/` and (b) `git ls-files build/` is empty.

## Verification

- Offline: `python -m pytest tests/test_issue315_build_hygiene.py -m "not requires_live_project" -q`
- Live LCM: **N/A** (filesystem / git hygiene only).
