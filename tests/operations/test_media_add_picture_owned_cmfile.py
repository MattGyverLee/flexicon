#
#   test_media_add_picture_owned_cmfile.py
#
#   Regression test for issue #226:
#   MediaOperations.Create used to set ICmFile.InternalPath on a freshly
#   created, *unowned* CmFile. In LibLCM CmFile.set_InternalPath resolves
#   the path against its owning CmFolder / LangProject.LinkedFilesRootDir,
#   so on an unowned object the setter dereferenced null and threw a .NET
#   System.NullReferenceException. Every path that funnels into Create
#   (LexSenseOperations.AddPicture, MediaOperations.CopyToProject,
#   ExampleOperations/PronunciationOperations.AddMediaFile) was therefore
#   unusable.
#
#   A second defect in CopyToProject tested `LinkedFilesRootDir` on the
#   LcmCache (self.project.project) instead of ILangProject, so the guard
#   was always False and the file was never copied.
#
#   After the fix:
#     - Create owns the CmFile in the appropriate CmFolder
#       (LangProject.PicturesOC for images, MediaOC otherwise) *before*
#       setting InternalPath -- no NRE.
#     - CopyToProject reads LinkedFilesRootDir from LangProject and stores
#       an InternalPath relative to it, so AbsoluteInternalPath resolves to
#       the copied file.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import sys

import pytest


# This test writes to a real .fwdata project (creates a probe entry and
# adds a picture to one of its senses). It requires a write-enabled live
# project; it skips cleanly when none is available.
pytestmark = pytest.mark.requires_live_project


_CANDIDATE_PROJECTS = ("Test", "SampleLexicon", "SampleLexicon3", "Sena 3")

# A minimal, valid 1x1 transparent PNG.
_MINIMAL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c62000100000500010d0a2db40000000049454e44ae"
    "426082"
)


def _try_open_writable_project():
    try:
        from flexlibs2.code.FLExProject import FLExProject
    except Exception:
        return None
    for name in _CANDIDATE_PROJECTS:
        project = FLExProject()
        try:
            project.OpenProject(name, writeEnabled=True)
            return project
        except Exception:
            try:
                project.CloseProject()
            except Exception:
                pass
            continue
    return None


@pytest.fixture(scope="module")
def writable_project():
    if "SIL.LCModel" not in sys.modules:
        pytest.skip("Requires SIL.LCModel (FieldWorks installed)")
    project = _try_open_writable_project()
    if project is None:
        pytest.skip(
            "No write-enabled FieldWorks project available "
            f"(tried: {', '.join(_CANDIDATE_PROJECTS)})"
        )
    yield project
    try:
        project.CloseProject()
    except Exception:
        pass


class TestAddPictureOwnedCmFile:
    """
    Regression coverage for issue #226: adding a picture must create an
    owned ICmFile, set InternalPath without raising a NullReferenceException,
    copy the source file into LinkedFiles/, and wire it to the sense's
    picture via PictureFileRA.
    """

    def test_add_picture_copies_and_wires_cmfile(self, tmp_path, writable_project):
        img = tmp_path / "dog.png"
        img.write_bytes(_MINIMAL_PNG)

        entry = writable_project.LexEntry.Create("probe226", "stem")
        try:
            senses = list(writable_project.Senses.GetAll(entry))
            assert senses, "probe entry should have at least one sense"
            sense = senses[0]

            # Before the fix this raised System.NullReferenceException at
            # CmFile.set_InternalPath.
            pic = writable_project.Senses.AddPicture(sense, str(img), "a dog")

            cf = pic.PictureFileRA
            assert cf is not None, "PictureFileRA must be wired to a CmFile"

            # InternalPath must be set (no NRE) and owned by a folder.
            assert cf.InternalPath, "CmFile.InternalPath must be set"
            assert cf.Owner is not None, "CmFile must be owned by a CmFolder"

            # The file must actually have been copied into LinkedFiles/.
            assert os.path.exists(cf.AbsoluteInternalPath), (
                "CopyToProject must copy the source into LinkedFiles and "
                f"AbsoluteInternalPath must resolve to it; got "
                f"{cf.AbsoluteInternalPath!r}"
            )
        finally:
            try:
                writable_project.LexEntry.Delete(entry)
            except Exception:
                pass
