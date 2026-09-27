# Issue #547 -- live evidence (Target sandbox)

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_547_addsubcat_catalog_live.py -m requires_live_project -q
```

Worktree: `C:/Github/flexicon-547`, branch `fix/547-addsubcat-catalog`.

## Result

`3 passed` -- `tests/test_results.json` records 3 tests.
`tests/live_status.json` `run_mode`: `live`.

## Pre-state / post-state (read back from the LCM)

- Verbatim id: created `TEST_547_Parent` top-level, then
  `AddSubcategory(parent, TEST_547_Sub, ..., catalogSourceId="ProjectSpecific:547Foo")`.
  Re-read via `GetCatalogSourceId(sub)` == `"ProjectSpecific:547Foo"` and
  `sub.CatalogSourceId` verbatim; `GetParent(sub).Guid == parent.Guid`.
  Cleaned up via `RemoveSubcategory` + `Delete(parent)`.
- Default None: `AddSubcategory(parent, ...)` with no catalog id;
  re-read `GetCatalogSourceId(sub) == ""` (old behavior preserved).
- GOLD path: `AddSubcategory(parent, TEST_547_GoldSub, ..., catalogSourceId="GOLD:Adjective")`.
  Re-read `str(sub.Guid).lower() == "30d07580-5052-4d91-bc24-469b8b2d7df9"`
  (canonical Adjective GUID); default-analysis WS name/abbreviation overlaid
  with user values; when newly created, `GetParent(sub).Guid == parent.Guid`.
  New catalog item detached and deleted; parent deleted.

## Pass/fail

PASS -- live-verified on the Target sandbox.
