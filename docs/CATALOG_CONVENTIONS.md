# Catalog Conventions

## Overview

Flexicon wraps six SIL/FieldWorks catalogs. Each catalog populates a
distinct LCM domain (POS, phonological features, inflection features,
semantic domains, anthropology items, IPA phonemes), and each one
follows a different convention for the value written to the LCM
`CatalogSourceId` field on items created from the catalog.

This document captures the three prefix policies in use, the reasoning
behind each, and where the policy is configured in code. It exists
because the policies are not interchangeable: the value written to
`CatalogSourceId` has to round-trip against the catalog's own id scheme
or `FixGuidsAgainstCatalog` cannot rebind drifted GUIDs back to the
catalog entry.

---

## The policy table

| Catalog                 | Operations class                | Prefix policy                                                              | Example written to LCM                 |
| ----------------------- | ------------------------------- | -------------------------------------------------------------------------- | -------------------------------------- |
| GOLDEtic (POS)          | `POSOperations`                 | `"GOLD:"` prefix on `entry.id`                                             | `"GOLD:Adjective"`                     |
| PhonFeats               | `PhonFeatureOperations`         | bare `entry.id` (no prefix)                                                | `"fPAConsonantal"`                     |
| EticGlossList           | `InflectionFeatureOperations`   | bare `entry.id` (no prefix)                                                | `"fDeg"`                               |
| SemDom                  | `SemanticDomainOperations`      | LCM-native (`XmlList.ImportList` writes whatever it writes)                | (no flexicon policy applied)          |
| OCM                     | `AnthropologyOperations`        | LCM-native (`XmlList.ImportList` writes whatever it writes)                | (no flexicon policy applied)          |
| BasicIPAInfo            | `PhonemeOperations`             | synthetic `"BasicIPA:"` prefix used for in-memory dedup ONLY               | `"BasicIPA:u0061"` (never written)     |

---

## Reasoning

The six catalogs split into three groups by how `CatalogSourceId` is
handled.

### 1. Etic catalog with explicit prefix (POS / GOLDEtic)

FieldWorks itself writes `"GOLD:<id>"` to `CatalogSourceId` for parts of
speech imported from `GOLDEtic.xml`. The `GOLD:` prefix identifies the
catalog source (the GOLD ontology, used by SIL) so that downstream tools
can disambiguate which catalog the id belongs to.

Flexicon follows the FW convention: `POSOperations` sets
`CATALOG_PREFIX_WRITE = "GOLD"`, and `CatalogBackedMixin._create_from_entry`
writes `CatalogSourceId = f"{CATALOG_PREFIX_WRITE}:{entry.id}"`.

### 2. Etic gloss-list catalogs with bare ids (PhonFeats, InflectionFeatures)

FieldWorks writes bare ids (no catalog prefix) for items imported from
the etic gloss-list catalogs. `PhonFeatsEticGlossList.xml` items land in
`PhFeatureSystemOA` with `CatalogSourceId = "fPAConsonantal"` (etc.);
`EticGlossList.xml` items land in `MsFeatureSystemOA` similarly. Whether
FW omits the prefix because the catalog id is unambiguous on its own
(the `f`/`v`/`g` prefixes in the entry ids already encode the category)
or for historical reasons is irrelevant to flexicon: we follow the FW
convention exactly so round-trips work.

`PhonFeatureOperations` and `InflectionFeatureOperations` both set
`CATALOG_PREFIX_WRITE = None`. The mixin sees `None` and writes
`CatalogSourceId = entry.id` directly (no `"{prefix}:"`).

### 3. LCM-native catalogs (SemDom, OCM)

`SemDom.xml` (semantic domains) and `OCM.xml` (anthropology items) ship
in LCM's own `<LangProject><...List><CmPossibilityList>...` XML shape
and are consumed by `SIL.LCModel.Application.ApplicationServices.XmlList.ImportList`
directly. Flexicon does NOT parse these catalogs and does NOT set
`CatalogSourceId` for the imported items; whatever LCM writes is what
ends up in the field. (Empirically, LCM leaves the field empty for most
items in these two catalogs.)

`SemanticDomainOperations` and `AnthropologyOperations` use
`_LCMNativeCatalogImportMixin` (a separate mixin from
`CatalogBackedMixin`). The `CATALOG_PREFIX_WRITE` attribute does not
apply to these classes because no entry-by-entry write happens in
flexicon.

### 4. Synthetic prefix for BasicIPAInfo

`BasicIPAInfo.xml` is a different shape again: ~245 IPA segments that
become `IPhPhoneme` objects under `PhonologicalDataOA.PhonemeSetsOS[0]`.
Two things make it special:

1. The catalog has no per-segment GUIDs. Entries are identified by the
   IPA code point alone.
2. `IPhPhoneme` has no `CatalogSourceId` field. There is nowhere on the
   LCM object to write a catalog tag at all.

So the `"BasicIPA:"` prefix in `PhonemeOperations.ImportCatalog` is
purely in-process: each created phoneme appears in the returned
`CatalogImportResult.created_guids` list as `"BasicIPA:<code_point_id>"`
(or `"BasicIPA:<representation>"` as a fallback). This lets the caller
dedup-by-id within a single import run, but the tag is never persisted.
Subsequent runs of `ImportCatalog` cannot detect already-imported
phonemes from the catalog tag; they detect them via the non-empty
phoneme-set guard (refuse-on-non-empty pattern shared with SemDom /
OCM).

---

## Where the policy lives in code

### Class-attribute configuration

| Class                          | File                                                                | Lines        | `CATALOG_PREFIX_WRITE` |
| ------------------------------ | ------------------------------------------------------------------- | ------------ | ---------------------- |
| `POSOperations`                | `flexicon/code/Grammar/POSOperations.py`                           | 76-80        | `"GOLD"`               |
| `PhonFeatureOperations`        | `flexicon/code/Grammar/PhonFeatureOperations.py`                   | 119-122      | `None`                 |
| `InflectionFeatureOperations`  | `flexicon/code/Grammar/InflectionFeatureOperations.py`             | 122-125      | `None`                 |
| `SemanticDomainOperations`     | `flexicon/code/Lexicon/SemanticDomainOperations.py`                | (uses `_LCMNativeCatalogImportMixin`; no `CATALOG_PREFIX_WRITE`) | n/a |
| `AnthropologyOperations`       | `flexicon/code/Notebook/AnthropologyOperations.py`                 | (uses `_LCMNativeCatalogImportMixin`; no `CATALOG_PREFIX_WRITE`) | n/a |
| `PhonemeOperations`            | `flexicon/code/Grammar/PhonemeOperations.py`                       | ~1641-1645   | n/a (synthetic in-memory) |

### Where the prefix is applied

The bare-vs-prefixed write in `CatalogBackedMixin._create_from_entry`
(file `flexicon/code/Shared/catalog_backed.py`, lines ~501-505):

```python
if self.CATALOG_PREFIX_WRITE is None:
    new_obj.CatalogSourceId = entry.id
else:
    new_obj.CatalogSourceId = f"{self.CATALOG_PREFIX_WRITE}:{entry.id}"
```

The synthetic BasicIPA tag in `PhonemeOperations.ImportCatalog`
(file `flexicon/code/Grammar/PhonemeOperations.py`, lines ~1641-1645):

```python
# Synthetic catalog tag (BasicIPAInfo has no real GUIDs).
synthetic_tag = (
    f"BasicIPA:{seg.code_point_id}" if seg.code_point_id else
    f"BasicIPA:{seg.representation}"
)
```

The LCM-native catalogs (SemDom / OCM) write `CatalogSourceId` via
`SIL.LCModel.Application.ApplicationServices.XmlList.ImportList`
internally; the call site in flexicon lives in
`_LCMNativeCatalogImportMixin._import_lcm_native_catalog` in
`flexicon/code/Shared/catalog_backed.py`. flexicon does not set the
field directly for these catalogs.

---

## Consequences for `FixGuidsAgainstCatalog`

`CatalogBackedMixin.FixGuidsAgainstCatalog` reads `CatalogSourceId` from
each existing item and looks up the matching catalog entry by id. It
calls `find_catalog_entry(entries, source_id)`, which knows how to
strip a known catalog prefix (`"GOLD:"`, `"PHON:"`) before matching.
This means:

- POS items survive the round-trip: written as `"GOLD:Adjective"`, read
  back, matched against `entry.id == "Adjective"`.
- PhonFeats / InflectionFeatures items survive trivially: bare id in,
  bare id out, direct match.
- SemDom / OCM items are not handled by `FixGuidsAgainstCatalog` at all
  (`_LCMNativeCatalogImportMixin` does not provide that method).
- BasicIPAInfo phonemes have no `CatalogSourceId` to read, so there is
  no fix-against-catalog support; recovery from drift would have to use
  representation matching instead.

---

## When adding a new catalog

1. Identify which group the catalog belongs to (etic-with-prefix,
   etic-bare, LCM-native, or synthetic).
2. If etic: subclass `CatalogBackedMixin` and set `CATALOG_PREFIX_WRITE`
   to either the prefix string (matching the FW convention for that
   catalog) or `None`.
3. If LCM-native: subclass `_LCMNativeCatalogImportMixin` and set
   `LCM_LIST_FIELD_NAME` + `LANG_PROJECT_LIST_ATTR`. `CatalogSourceId`
   policy is determined by LCM, not by flexicon.
4. If the catalog has no per-entry GUIDs and the LCM target has no
   `CatalogSourceId` field (the BasicIPAInfo shape), follow the
   refuse-on-non-empty pattern and use a synthetic prefix only for
   in-process dedup. Document the unusual case in the importer's
   docstring.
5. Update the policy table in this document.

---

## See also

- `docs/ARCHITECTURE_WRAPPERS.md` -- wrapper-class pattern used by some
  of these Operations classes.
- `docs/ARCHITECTURE_COLLECTIONS.md` -- smart-collection pattern.
- `flexicon/code/Shared/catalog.py` -- catalog XML parsing helpers and
  `find_catalog_entry` (which is prefix-aware).
- `flexicon/code/Shared/catalog_backed.py` -- both `CatalogBackedMixin`
  (etic catalogs) and `_LCMNativeCatalogImportMixin` (LCM-native
  catalogs).
