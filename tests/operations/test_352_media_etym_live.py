#
#   test_352_media_etym_live.py
#
#   Live regression coverage for issue #352 (Media + etymology faces):
#   - MediaOperations handles ICmFile, whose Description/Copyright ARE
#     IMultiString (the audit row checked ICmMedia by mistake) -- this
#     test locks in the correct behaviour live.
#   - LexEntryOperations.Duplicate copied a nonexistent etymology Source;
#     it now copies LanguageNotes like EtymologyOperations.Duplicate.
#
#   Runs against target_sandbox (tempdir copy of the Target .fwbackup),
#   so nothing can leak into a real project.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

pytestmark = pytest.mark.requires_live_project


class Test352MediaFileDescriptionRoundTrip:
    @pytest.mark.live_phase("MediaOperations", "add")
    def test_label_duplicate_sync(self, target_sandbox):
        op = target_sandbox.Media
        media = op.Create("LinkedFiles/AudioVisual/TEST_352.wav", label="TEST_352 label")
        try:
            # Locks the audit correction: files HAVE Description/Copyright
            # (the issue checked ICmMedia by mistake).
            assert hasattr(media, "Description")
            assert hasattr(media, "Copyright")
            assert op.GetLabel(media) == "TEST_352 label"
            op.SetLabel(media, "TEST_352 relabel")
            assert op.GetLabel(media) == "TEST_352 relabel"
            dup = op.Duplicate(media)
            try:
                assert op.GetLabel(dup) == "TEST_352 relabel (copy)"
                props = op.GetSyncableProperties(dup)
                # LCM normalises the separator to backslashes on write.
                assert props["InternalPath"].replace("\\", "/") == (
                    "LinkedFiles/AudioVisual/TEST_352.wav"
                )
                assert "TEST_352 relabel (copy)" in props["Description"].values()
                is_diff, _ = op.CompareTo(media, media)
                assert not is_diff
            finally:
                op.Delete(dup)
        finally:
            op.Delete(media)


class Test352LexEntryEtymologyDuplicate:
    @pytest.mark.live_phase("LexEntryOperations", "add")
    def test_duplicate_conserves_etymology(self, target_sandbox):
        lex = target_sandbox.LexEntry
        etym = target_sandbox.Etymology
        entry = lex.Create(lexeme_form="TEST_352etym")
        try:
            new_etym = etym.Create(entry, source="TEST_352 Greek", form="tele", gloss="far")
            # Locks the audit: no Source member; LanguageNotes is real.
            assert not hasattr(new_etym, "Source")
            assert hasattr(new_etym, "LanguageNotes")
            dup = lex.Duplicate(entry)
            try:
                dup_etyms = list(dup.EtymologyOS)
                assert len(dup_etyms) == 1
                assert etym.GetSource(dup_etyms[0]) == "TEST_352 Greek"
                assert etym.GetForm(dup_etyms[0]) == "tele"
            finally:
                lex.Delete(dup)
        finally:
            lex.Delete(entry)
