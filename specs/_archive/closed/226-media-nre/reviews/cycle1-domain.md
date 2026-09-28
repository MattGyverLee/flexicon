# Domain Expert Review — Issue #226 (MediaOperations)

Branch: msa-null-pos (uncommitted)
File: flexicon/code/Shared/MediaOperations.py

## Verdict: PASS (all 5 claims domain-correct, no blocking issues within #226 scope)

1. **Folder-before-InternalPath ordering — PASS.** LibLCM's `CmFile.InternalPath`
   setter (and `AbsoluteInternalPath`) resolves against the owning
   `CmFolder`/`LinkedFilesRootDir`; an unparented `ICmFile` has no owner chain to
   resolve against, so setting InternalPath first NREs. The fix's order (create
   file -> `folder.FilesOC.Add(new_media)` -> set `InternalPath`) matches the
   correct LCM object-graph lifecycle (parent ownership before dependent-property
   writes that touch owner state).

2. **Routing to PicturesOC/MediaOC — PASS.** `ILangProject.PicturesOC` and
   `.MediaOC` are the standard LibLCM owning collections of `ICmFolder`, and
   "Local Pictures"/"Local Media" are the conventional default folder names FLEx
   creates and displays. Image-extension-based routing to Pictures vs. everything
   else to Media matches how FLEx itself buckets linked files.

3. **LinkedFilesRootDir on ILangProject, not LcmCache — PASS (confirmed in-repo).**
   `FLExProject.py:222` sets `self.lp = self.project.LangProject`, and
   `FLExProject.py:2714-2717` accesses `LinkedFilesRootDir` via `self.lp`, matching
   the pattern now used in `MediaOperations.py`. The old bug (checking it on the
   cache) always found nothing since `LcmCache` has no such property.

4. **CopyToProject relative path (no doubled "LinkedFiles/") — PASS.** Since
   `linked_files_dir` already *is* the LinkedFiles root, prefixing "LinkedFiles/"
   again produced a path that `AbsoluteInternalPath` resolves to a nonexistent
   nested folder. Storing `internal_subdir/filename` relative to that root is the
   correct LCM convention.

5. **Image extension set `{.jpg,.jpeg,.png,.gif,.bmp,.tif,.tiff,.svg}` — PASS
   (minor note).** Reasonable, matches FLEx's typical CmPicture raster formats.
   `.svg` inclusion is slightly generous (FLEx vector support is limited) but
   harmless — it only affects which owning folder a reference lands in, not
   rendering. No materially-missing common types (e.g. `.webp`).

Overall: all five claims consistent with the LibLCM ownership/owning-collection
model and existing `LinkedFilesRootDir` usage elsewhere. No blocking issues.
