# Cycle 4 - #829 LexReferences.GetAll (programmer)

Files changed:
- flexicon/code/Lexicon/LexReferenceOperations.py (GetAll rewritten + docstring Notes)
- NEW tests/operations/test_issue829_lexreference_getall_offline.py (2 tests)
- NEW tests/operations/test_issue829_lexreference_getall_live.py (3 tests)

Implementation: None -> walk ReferencesOA.PossibilitiesOS (recursing SubPossibilitiesOS),
yield MembersOC; sense -> LexSenseReferences; entry -> LexEntryReferences + LexSenseReferences
over entry.AllSenses (subsenses included). All deduped by Hvo; still lazy.

Offline: 3962 passed, 2 failed, 1288 deselected. The 2 failures are
test_issue686_pronunciation_movemedia_hvo_offline.py (both tests) - Pronunciation file,
owned by the other programmer; not touched or investigated by me.

Live (exact command, FLEXLIBS_REQUIRE_LIVE=1): 8 passed (829 x3, 814, 742, 744, 481).
tests/live_status.json run_mode = "live".
Sena 3 sandbox: GetAll() = 26, independent MembersOC walk = 26 (sets equal).
Entry-level reference (entry targets) via Create works; asserted in GetAll(entry) and GetAll().

Other checks: no other backreference-property calls in LexReferenceOperations.py (grep for
ReferringLexReferences/Referring/BackRef is clean). test_issue814 helper already uses
MembersOC; 742/744 call only LexEntry.GetAll, not LexReferences.GetAll.

Proposed CHANGELOG line:
- Fixed #829: LexReferenceOperations.GetAll read the non-existent ReferringLexReferences and
  raised on every call; it now uses LexSenseReferences / LexEntryReferences / ReferencesOA.MembersOC.
