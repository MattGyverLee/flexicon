# Issue #547 -- live evidence (Target sandbox)

## Design (lex-lead ruling, follow-up)

`Create` is canonical with `parent=None`; `AddSubcategory` is a thin
wrapper delegating to `Create(..., parent=pos_or_hvo)`. All creation
logic (factory attach, GOLD catalog path, verbatim CatalogSourceId)
lives in one place. Precedent: `SemanticDomainOperations.Create(name,
number, parent=None)`. The `parent=` rejection pinned by #276 lives on
the deprecated `GramCatOperations.Create` alias only and is untouched.

Preserved behaviours: GOLD path bypasses the Exists check (catalog
idempotency); the Exists check applies to top-level creates only
(subcategories keep AddSubcategory's no-uniqueness-check behaviour);
a pre-existing catalog GUID is returned with name/abbreviation
overlaid, not re-parented.

## Command

```
$env:FLEXLIBS_REQUIRE_LIVE = "1"
python -m pytest tests/operations/test_547_addsubcat_catalog_live.py -m requires_live_project -q
python -m pytest tests/operations/test_276_gramcat_pos_alias.py tests/operations/test_276_pos_getparent.py -m requires_live_project -q
python -m pytest -m "not requires_live_project" -q
```

Worktree: `C:/Github/flexicon-547`, branch `fix/547-addsubcat-catalog`.

## Result

- 547 live file: `5 passed` (verbatim id + parent, default None,
  GOLD canonical GUID + overlay, Create(parent=...) equivalence,
  Create with HVO parent).
- 276 live files: `8 passed` (GramCat alias behaviour unchanged).
- Offline suite: `2446 passed` (includes the write-path-transaction
  ratchet; the AddSubcategory delegation site carries its own
  `_TransactionCM` bracket per D5, joining Create's inner transaction
  via B1 nesting -- house pattern from Filter/MediaOperations).
- `tests/live_status.json` `run_mode`: `live`.

## Pre-state / post-state (read back from the LCM)

- Verbatim id: created `TEST_547_Parent` top-level, then
  `AddSubcategory(parent, TEST_547_Sub, ..., catalogSourceId="ProjectSpecific:547Foo")`.
  Re-read via `GetCatalogSourceId(sub)` == `"ProjectSpecific:547Foo"` and
  `sub.CatalogSourceId` verbatim; `GetParent(sub).Guid == parent.Guid`.
- Default None: `AddSubcategory(parent, ...)` with no catalog id;
  re-read `GetCatalogSourceId(sub) == ""`.
- GOLD path: `AddSubcategory(parent, TEST_547_GoldSub, ..., catalogSourceId="GOLD:Adjective")`.
  Re-read `str(sub.Guid).lower() == "30d07580-5052-4d91-bc24-469b8b2d7df9"`
  (canonical Adjective GUID); default-analysis WS name/abbreviation
  overlaid with user values; when newly created,
  `GetParent(sub).Guid == parent.Guid`.
- Canonical equivalence: `Create(..., parent=parent)` and
  `AddSubcategory(parent, ...)` both yield children whose re-read
  `GetParent` is the parent and whose `GetCatalogSourceId` is verbatim;
  HVO parent resolves identically.
- All created objects detached/deleted; parents deleted.

## Pass/fail

PASS -- live-verified on the Target sandbox.
