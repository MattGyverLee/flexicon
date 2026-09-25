#
#   test_issue356_text_media_helpers.py
#
#   Issue #356: TextOperations.GetMediaFiles / AddMediaFile used the phantom
#   MediaFilesOC collection; live LCM uses MediaURIsOC on ICmMediaContainer.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

from pathlib import Path

import pytest

_TEST_PREFIX = "TEST_356_"
_TEXT_OPS = Path(__file__).resolve().parents[2] / "flexicon" / "code" / "TextsWords" / "TextOperations.py"

# Minimal valid 1x1 transparent PNG (CopyToProject accepts any file type).
_MINIMAL_PNG = bytes.fromhex(
    "89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4"
    "890000000d49444154789c62000100000500010d0a2db40000000049454e44ae"
    "426082"
)


class TestIssue356TextMediaHelpersOffline:
    """Static ratchet: helper APIs must not reference MediaFilesOC."""

    def test_text_operations_source_uses_media_uris_oc_only(self):
        source = _TEXT_OPS.read_text(encoding="utf-8")
        assert "MediaFilesOC" not in source, (
            "TextOperations must use MediaURIsOC (issue #356); "
            "MediaFilesOC is not on ICmMediaContainer."
        )


@pytest.mark.requires_live_project
class TestIssue356TextMediaHelpersLive:
    """Live read-back for GetMediaFiles / AddMediaFile on MediaURIsOC."""

    @pytest.mark.live_phase("TextOperations", "add")
    def test_add_media_file_roundtrip_via_get_media_files(self, target_sandbox, tmp_path):
        from flexicon.code.lcm_casting import cast_to_concrete

        project = target_sandbox
        text_ops = project.Texts
        media_path = tmp_path / f"{_TEST_PREFIX}probe.png"
        media_path.write_bytes(_MINIMAL_PNG)

        text = text_ops.Create(f"{_TEST_PREFIX}media_text")
        try:
            uri_obj = text_ops.AddMediaFile(text, str(media_path), label="356 probe")
            assert uri_obj is not None

            # Re-read from LCM via repository, not the returned handle alone.
            text_guid = str(text.Guid)
            from SIL.LCModel import ITextRepository

            repo = project.project.ServiceLocator.GetService(ITextRepository)
            refetched = None
            for t in repo.AllInstances():
                if str(t.Guid) == text_guid:
                    refetched = t
                    break
            assert refetched is not None

            media_list = text_ops.GetMediaFiles(refetched)
            assert len(media_list) >= 1, "GetMediaFiles returned empty after AddMediaFile"

            concrete = cast_to_concrete(refetched)
            lcm_count = concrete.MediaFilesOA.MediaURIsOC.Count
            assert lcm_count >= 1, f"LCM MediaURIsOC.Count={lcm_count}"

            props = text_ops.GetSyncableProperties(refetched)
            assert props.get("media_uris"), f"GSP missing media_uris: {props.keys()}"
            # ICmMediaURI exposes only MediaURI (live reflection, 2026-09-25);
            # there is no MediaFileRA, so file_guid is always None. Assert the
            # URI itself round-trips through the LCM instead.
            assert any(
                e.get("uri", "").endswith("TEST_356_probe.png")
                for e in props["media_uris"]
            ), props["media_uris"]
        finally:
            text_ops.Delete(text)
