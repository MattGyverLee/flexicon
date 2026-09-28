# Issue #202 -- offline evidence

## Lex-lead ruling

See `specs/202-basic-ipa-tones/rulings.md`.

## Commands

```
python -m pytest tests/operations/test_issue202_basic_ipa_skip_tones_offline.py tests/operations/test_basic_ipa.py::TestBasicIpaImportCatalog::test_import_catalog_signature_accepts_force_keyword tests/operations/test_basic_ipa.py::TestBasicIpaImportCatalog::test_import_catalog_signature_accepts_skip_tones_keyword -m "not requires_live_project" -q
```

## Result (cloud agent, Linux)

Recorded after run completes in this session.

**Live:** FAIL: unverified -- no FieldWorks / .NET runtime on this host.
