# Live verification -- issue #325 T3 syncable-properties

## (a) languages_seeded

2 GUIDs: ['67ca994e-5514-4319-851e-98cc1c8adcdc', '924ff1a7-c6aa-4a2f-94fb-0b04b108f9d7']

## (a) GetSyncableProperties language_rs

['67ca994e-5514-4319-851e-98cc1c8adcdc', '924ff1a7-c6aa-4a2f-94fb-0b04b108f9d7']

## (a) LanguageNotesRA absent

True

## (a) LanguageRS after Apply (re-read)

['67ca994e-5514-4319-851e-98cc1c8adcdc', '924ff1a7-c6aa-4a2f-94fb-0b04b108f9d7']

## (a) Duplicate LanguageNotes preserved

T3_source_note

## (a) Duplicate LanguageRS count (expect 0)

0

## (a) GetLanguage/SetLanguage warn

[WARN] emitted for both deprecated methods

## (a) RESULT

PASS

## (b) owner_guid

70906d23-7535-4134-b79e-01681015bd4d

## (b) targets_rs count

2

## (b) ReferenceTypeRA absent

True

## (b) RESULT

PASS

## (b) ApplySyncableProperties (idempotent, no raise)

PASS

## (b) owner_guid stable after Apply

70906d23-7535-4134-b79e-01681015bd4d

## (b) targets_rs before

['9fb1606b-9db1-427d-b68f-dea0a2618c44', 'b9769a9c-a44e-411f-8a8a-cc9a43d6bd4e', 'ce75c167-9bd8-4258-9ff2-3561e4332754']

## (b) targets_rs after mutating Apply (re-read)

['ce75c167-9bd8-4258-9ff2-3561e4332754', 'b9769a9c-a44e-411f-8a8a-cc9a43d6bd4e', '9fb1606b-9db1-427d-b68f-dea0a2618c44']

## (b) targets_rs mutating Apply

PASS

## (c) Name in payload (R8)

PASS

## (c) Name dict keys

['en']

## (c) media_uris GSP

[{'uri': 'file:///TEST_325_media_roundtrip.mp3', 'file_guid': None}]

## (c) media_uris after Apply (re-read)

['file:///TEST_325_media_roundtrip.mp3']

## (c) media_uris (R4)

PASS -- GSP+Apply round-trip uri='file:///TEST_325_media_roundtrip.mp3'

## (d) Create no NRE

PASS

## (d) row.CellsOS contains marker

PASS

## (d) WordGroupRA == word group

PASS

## (d) Preposed re-read

True

## (d) Find

PASS

## (d) GetAll

PASS (1 total)

## (d) GetWordGroup

PASS

## (d) SetPreposed round-trip

PASS

## (d) Delete removes from CellsOS

PASS

## (d) RESULT

PASS (target_sandbox, built from scratch)

## (e) DoNotShowMainEntryInRC absent

PASS

## (e) DoNotPublishInRC present

PASS

## (e) RESULT

PASS

## commands

python -m pytest -m "not requires_live_project" -q; $env:FLEXLIBS_REQUIRE_LIVE = "1"; python -m pytest tests/operations/test_325_syncable_properties_live.py -m requires_live_project -q

## run_mode

live

## run_timestamp

2026-09-22T22:45:44.027422+00:00

