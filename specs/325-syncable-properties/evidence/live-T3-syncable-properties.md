# Live verification -- issue #325 T3 syncable-properties

## (a) languages_seeded

Languages list empty in Target sandbox; seeded 0

## (a) GetSyncableProperties language_rs

[]

## (a) LanguageNotesRA absent

True

## (a) LanguageRS after Apply (re-read)

Skipped (no languages seeded; list was empty)

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

## (c) Name in payload (R8)

PASS

## (c) Name dict keys

['en']

## (c) media_uris (R4)

FAIL: unverified -- no project with MediaFilesOA populated found. needs_human: provide a project with actual media files to verify R4.

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

2026-09-22T21:59:00.402122+00:00

