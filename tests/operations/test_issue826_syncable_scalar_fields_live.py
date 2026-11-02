#
#   test_issue826_syncable_scalar_fields_live.py
#
#   Issue #826: GetSyncableProperties omitted scalar/text fields
#   (AnthroNote, UsageNote, SummaryDefinition, Restrictions, Etymology
#   Note/PrecComment, Pronunciation CVPattern/Tone) and Texts had no
#   GetSource/SetSource. Verified on target_sandbox (tempdir copy only).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

TEST_PREFIX = "TEST_"
SRC_WS = "zz-src"  # fake source WS id, mapped onto the target analysis WS


def _analysis(project):
    handle = project.project.DefaultAnalWs
    for ws in project.WritingSystems.GetAll():
        if ws.Handle == handle:
            return ws.Id, handle
    raise AssertionError("no default analysis WS")


def _roundtrip_multi(ops, src, dst, name, ws_id):
    """Write via raw LCM on src, emit, apply to dst with ws_map, read back."""
    from SIL.LCModel.Core.Text import TsStringUtils
    from SIL.LCModel.Core.KernelInterfaces import ITsString

    handle = next(w.Handle for w in ops.project.WritingSystems.GetAll() if w.Id == ws_id)
    getattr(src, name).set_String(handle, TsStringUtils.MakeString(f"{TEST_PREFIX}{name}", handle))
    props = ops.GetSyncableProperties(src)
    assert props[name] == {ws_id: f"{TEST_PREFIX}{name}"}, props[name]
    # ws_map honoured: re-key under a fake source WS id.
    props2 = {name: {SRC_WS: props[name][ws_id]}}
    assert ITsString(getattr(dst, name).get_String(handle)).Text in (None, "")
    ops.ApplySyncableProperties(dst, props2, ws_map={SRC_WS: ws_id})
    got = ITsString(getattr(dst, name).get_String(handle)).Text  # read back
    assert got == f"{TEST_PREFIX}{name}", got


@pytest.mark.requires_live_project
class TestIssue826Live:

    def test_sense_anthro_usage_notes(self, target_sandbox):
        p = target_sandbox
        ws_id, _ = _analysis(p)
        e = p.LexEntry.Create(f"{TEST_PREFIX}e826a")
        s1 = p.Senses.Create(e, f"{TEST_PREFIX}s1")
        s2 = p.Senses.Create(e, f"{TEST_PREFIX}s2")
        for name in ("AnthroNote", "UsageNote"):
            _roundtrip_multi(p.Senses, s1, s2, name, ws_id)

    def test_entry_summary_restrictions(self, target_sandbox):
        p = target_sandbox
        ws_id, _ = _analysis(p)
        e1 = p.LexEntry.Create(f"{TEST_PREFIX}e826b1")
        e2 = p.LexEntry.Create(f"{TEST_PREFIX}e826b2")
        for name in ("SummaryDefinition", "Restrictions"):
            _roundtrip_multi(p.LexEntry, e1, e2, name, ws_id)

    def test_etymology_note_preccomment(self, target_sandbox):
        p = target_sandbox
        ws_id, _ = _analysis(p)
        e = p.LexEntry.Create(f"{TEST_PREFIX}e826c")
        y1 = p.Etymology.Create(e, form=f"{TEST_PREFIX}y1")
        y2 = p.Etymology.Create(e, form=f"{TEST_PREFIX}y2")
        for name in ("Note", "PrecComment"):
            if not hasattr(y1, name):
                pytest.fail(f"ILexEtymology has no {name} on this LCM")
            _roundtrip_multi(p.Etymology, y1, y2, name, ws_id)

    def test_pronunciation_cvpattern_tone(self, target_sandbox):
        from SIL.LCModel.Core.Text import TsStringUtils
        from SIL.LCModel.Core.KernelInterfaces import ITsString

        p = target_sandbox
        ws_id, handle = _analysis(p)
        e = p.LexEntry.Create(f"{TEST_PREFIX}e826d")
        p1 = p.Pronunciations.Create(e, f"{TEST_PREFIX}p1")
        p2 = p.Pronunciations.Create(e, f"{TEST_PREFIX}p2")
        for name, val in (("CVPattern", "CVC"), ("Tone", "HL")):
            setattr(p1, name, TsStringUtils.MakeString(val, handle))
        props = p.Pronunciations.GetSyncableProperties(p1)
        assert props["CVPattern"] == "CVC" and props["Tone"] == "HL", props
        p.Pronunciations.ApplySyncableProperties(
            p2, {"CVPattern": props["CVPattern"], "Tone": props["Tone"]})
        assert ITsString(p2.CVPattern).Text == "CVC"  # read back from LCM
        assert ITsString(p2.Tone).Text == "HL"

    def test_text_source_accessors_and_sync(self, target_sandbox):
        p = target_sandbox
        ws_id, handle = _analysis(p)
        t1 = p.Texts.Create(f"{TEST_PREFIX}t1")
        t2 = p.Texts.Create(f"{TEST_PREFIX}t2")
        assert p.Texts.GetSource(t1) == ""
        p.Texts.SetSource(t1, f"{TEST_PREFIX}src")
        assert p.Texts.GetSource(t1) == f"{TEST_PREFIX}src"
        props = p.Texts.GetSyncableProperties(t1)
        assert props["Source"] == {ws_id: f"{TEST_PREFIX}src"}, props.get("Source")
        p.Texts.ApplySyncableProperties(
            t2, {"Source": {SRC_WS: f"{TEST_PREFIX}src"}}, ws_map={SRC_WS: ws_id})
        assert p.Texts.GetSource(t2) == f"{TEST_PREFIX}src"


class TestIssue826Offline:
    def test_text_source_accessors_exist(self):
        from flexicon.code.TextsWords.TextOperations import TextOperations
        assert callable(TextOperations.SetSource)
        assert callable(TextOperations.GetSource)
