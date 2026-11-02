# Cycle 4 - lex-doc report

Edited (not committed; no code/tests touched):
- CHANGELOG.md [4.13.1] Fixed: two entries, #828 (ICmMedia; AddMediaFile returns ICmMedia, .MediaFileRA for ICmFile; Remove/Move accept ICmFile or HVO) and #829 (LexReferences.GetAll project-wide, per sense, per entry).
- RELEASE_NOTES_v4.13.1.md: matching lines in "What changed for you"; return-type change stated plainly.
- docs/API_ISSUES_CATEGORIZED.md Category 8: new subsection with two rows (MediaFilesOS holds ICmMedia; ReferringLexReferences does not exist).

Notes:
- Wording is "(#828)" / "(#829)" with no close/fix/resolve before the number.
- Rest of the 4.13.1 verification wording and Known gaps left untouched.
- Open: contract snapshot needs ICmMediaFactory (already modified in tree).
