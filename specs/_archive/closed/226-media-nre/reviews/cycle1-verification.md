# Verification Report — #226 Media NRE Regression Test

**Scope:** tests/operations/test_media_add_picture_owned_cmfile.py only.

## 1. Exercises the fix path?

Yes. `AddPicture` -> `Media.CopyToProject(image_path, "Pictures")` -> `Create()` ->
`__GetOrCreateMediaFolder` -> `folder.FilesOC.Add(new_media)` -> `InternalPath` set.
Confirmed by reading `LexSenseOperations.AddPicture` (calls `CopyToProject` then wires
`PictureFileRA`) and the diff in `MediaOperations.py`. Against pre-fix code, `Create` set
`InternalPath` on an unowned `ICmFile` before any `FilesOC.Add` — this test's call to
`AddPicture` would have hit exactly that line and raised the .NET NRE. **Would have failed
on old code: yes.**

## 2. Asserts reported outcomes?

- No NRE: implicit (call would raise, uncaught, if reintroduced) — sufficient.
- `PictureFileRA` wired: asserted (`pic.PictureFileRA is not None`).
- CmFile owned by a folder: asserted (`cf.Owner is not None`), though not asserted to be a
  `CmFolder` specifically (P2 — could check `cf.Owner.ClassName == "CmFolder"` or similar).
- File copied: asserted via `os.path.exists(cf.AbsoluteInternalPath)`.
- `AbsoluteInternalPath` resolves: covered by the same assertion, which depends on the
  `LinkedFilesRootDir`-from-`lp` fix and the de-doubled relative path fix in `CopyToProject`.

## 3. Coverage gaps (P2)

- **MediaOC branch untested.** Only the image/`PicturesOC` branch of
  `__GetOrCreateMediaFolder` is exercised (test uses a `.png`). The audio/video ->
  `MediaOC` branch, and `Create()` called directly with a non-image extension, are not
  covered.
- Folder-reuse branch (`for folder in owning_collection: return folder`) vs.
  folder-creation branch not independently verified.
- `CopyToProject`'s "no `LinkedFilesRootDir`" fallback (reference-only, no copy) not tested.
- `ExampleOperations`/`PronunciationOperations.AddMediaFile`, mentioned in the docstring as
  also funneling into `Create`, are not exercised by any test here.
- Owner class-type not asserted precisely (`CmFolder` vs. any owner).

## Live-pass claim plausibility

Plausible. `requires_live_project` is an established marker already used by ~10+ existing
live tests (`tests/conftest.py`, `test_allomorphs_live.py`, etc.), so the skip/fixture
mechanism is proven, not novel. The test's assertions are simple, direct object-model
checks (no mocking) matching the diff exactly — nothing here looks fragile or likely to
false-pass. Cannot execute live LCM in this environment to confirm directly.

**Verdict: Fix path covered for the image/PicturesOC branch; MediaOC (audio/video) branch
and a couple of secondary paths are untested (P2, not blocking for #226).**
