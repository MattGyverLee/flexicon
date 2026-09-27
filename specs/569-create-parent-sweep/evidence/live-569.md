# Issue #569 -- live evidence (Target sandbox)

## Design (lex-lead ruling)

`Create` is canonical with `parent=None` in Anthropology, Location
and DataNotebook; `CreateSubitem` / `CreateSublocation` /
`CreateSubRecord` are thin delegating wrappers. Restructure only --
no semantic change. Frozen constraints preserved exactly:
Anthropology PN13 (sub path persists padded bytes verbatim, NO dedup
check -- duplicate subitem names succeed) and PN14 (non-str raises
AttributeError at both sites via the throwaway strip, C7b, kept ahead
of parent resolution); per-path transaction labels preserved
("Create Anthropology Item" vs "Create Anthropology Subitem", etc.).
Precedents: POS Create(parent=None) (#547), Senses.Create (#567),
SemanticDomains.Create(parent=None).

## Commands

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_569_create_parent_sweep_live.py -m requires_live_project -q
python -m pytest tests/operations/test_name_field_identity_probe.py tests/operations/test_352_datanotebook_live.py tests/operations/test_datanotebook_duplicate.py -m requires_live_project -q
python -m pytest -m "not requires_live_project" -q
```

Worktree: `C:/Github/flexicon-547`, branch `fix/569-create-parent-sweep`.

## Result

- 569 live file: `5 passed` (Create(parent=...) equivalence per
  domain incl. HVO parent for Location; whitespace/dedup/AttributeError
  pins for Anthropology).
- Pinned suites: `33 passed` (PN13/PN14 probe, datanotebook live +
  duplicate).
- Offline suite: `2575 passed` (includes the
  write-path-transaction ratchet; all three delegation sites carry
  their own `_TransactionCM` brackets per D5, B1 nesting).
- `tests/live_status.json` `run_mode`: `live`.

## Pre-state / post-state (read back from the LCM)

- Per domain, `Create(..., parent=...)` and `CreateSub*(parent, ...)`
  both yield children whose re-read parent (GetParent / GetRegion /
  GetParentRecord) is the parent and which appear in the parent's
  sub-collection; alias/content agree across paths.
- Anthropology padded subitem names read back byte-identical on both
  paths; duplicate subitem names succeed on both; non-str raises
  AttributeError on the canonical path.
- All created top-level items deleted (children cascade).

## Pass/fail

PASS -- live-verified on the Target sandbox.
