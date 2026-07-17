# QC Report — Issue #226 (Media NullReferenceException)

**Status:** PASS (minor issues)
**Score:** 88/100

## P0 — None found.

## P1 Issues
1. **Stale docstring example** — `MediaOperations.py:1302-1303` (CopyToProject)
   still shows `GetInternalPath(media)` returning `"LinkedFiles/AudioVisual/audio.wav"`,
   but the #226 fix drops the `LinkedFiles/` prefix so `internal_path` is now
   `"AudioVisual/audio.wav"`. Example is now factually wrong; should read
   `AudioVisual/audio.wav`.
2. **No rollback on partial failure** — `Create()`: `folder.FilesOC.Add(new_media)`
   runs, then `new_media.InternalPath = file_path` is set separately. If the
   `InternalPath` setter (or the later `Description.set_String`) throws, `new_media`
   is left owned with no/empty path — an orphaned half-initialized CmFile with no
   cleanup. Not a regression (pre-existing pattern), but worth a try/except +
   `folder.FilesOC.Remove(new_media)` given #226 touched this path.

## P2 Issues
1. `Create()` docstring example still shows `Create("LinkedFiles/AudioVisual/audio.wav")`
   — could encourage the double-prefix bug if mimicked with CopyToProject-style
   usage. Worth a one-line note clarifying Create() stores path as-is vs.
   CopyToProject()'s auto-relative behavior.
2. `__GetOrCreateMediaFolder`: `for folder in owning_collection: return folder`
   is a non-obvious "first-or-none" idiom; `next(iter(owning_collection), None)`
   is clearer (functionally correct either way).
3. No-extension case falls through to MediaOC/"Local Media" by default (correct
   per docstring) but not explicitly unit-tested.

## Strengths
- `self.project.lp` / `self.lp` fix correct and consistent across all three call
  sites (GetExternalPath, CopyToProject, FLExProject.GetLinkedFilesDir), each with
  an inline #226 comment — good pattern-audit hygiene.
- Ownership-before-InternalPath sequencing correctly ordered and commented.
- `file_path.lower()` for extension detection avoids mutating the stored path and
  safely handles case and no-extension files.
- File header, logging, BaseOperations validation calls follow conventions.

## Recommendation
FIX-ISSUES (non-blocking): address P1-1 (stale docstring) before merge; P1-2 and
P2 items can be follow-ups.

**Pattern audit:** fix already touches three sibling `self.project` vs
`self.lp`/`self.project.lp` call sites in one pass — correct scope for this bug class.
