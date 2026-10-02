#
#   test_issue618_resolver_type_check_live.py
#
#   Live verification for issue #618: Operations resolvers must reject a
#   wrong-type argument with FP_ParameterError (instead of a raw
#   AttributeError from deep inside the method) while real LCM objects,
#   HVOs and wrappers still resolve.
#
#   Representative resolvers across modules (Lexicon, TextsWords, Grammar,
#   Discourse, and the shared BaseOperations._GetObject) run against real
#   LCM objects in sandbox copies of the Sena 3 and Target .fwbackup
#   fixtures, so nothing can leak into a real project.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

from flexicon.code.FLExProject import FP_ParameterError

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"

WRONG_TYPES = ["not-an-object", ["a", "list"], 1.5]


def _first(iterable):
    for item in iterable:
        return item
    return None


def _raw(obj):
    """Unwrap a flexicon wrapper (if any) to the raw LCM object."""
    return getattr(obj, "lcm_object", obj)


class TestResolversAcceptRealObjectsSena3:
    """Real objects, HVOs and wrappers still resolve; wrong types raise."""

    @pytest.mark.live_phase("LexEntryOperations", "read")
    def test_lex_entry_resolver_object_hvo_and_wrong_types(self, sena3_sandbox):
        entries = sena3_sandbox.LexEntry
        entry = _first(entries.GetAll())
        assert entry is not None, "Sena 3 sandbox has no lexical entries"

        by_obj = entries.GetHeadword(entry)
        by_hvo = entries.GetHeadword(entry.Hvo)
        assert by_obj == by_hvo and by_obj, (by_obj, by_hvo)
        print(f"[EVIDENCE] entry hvo={entry.Hvo} headword(obj)={by_obj!r} headword(hvo)={by_hvo!r}")

        resolve = entries._LexEntryOperations__ResolveObject
        assert resolve(entry.Hvo).Hvo == entry.Hvo
        assert resolve(entry).ClassName == "LexEntry"

        for bad in WRONG_TYPES:
            with pytest.raises(FP_ParameterError, match="got "):
                entries.GetHeadword(bad)

    @pytest.mark.live_phase("LexSenseOperations", "read")
    def test_sense_resolver_object_hvo_and_wrong_types(self, sena3_sandbox):
        entries = sena3_sandbox.LexEntry
        senses = sena3_sandbox.Senses
        entry = next(e for e in entries.GetAll() if e.SensesOS.Count > 0)
        sense = entry.SensesOS[0]

        assert senses.GetGloss(sense) == senses.GetGloss(sense.Hvo)
        resolve = senses._LexSenseOperations__GetSenseObject
        assert resolve(sense.Hvo).Hvo == sense.Hvo

        for bad in WRONG_TYPES:
            with pytest.raises(FP_ParameterError, match="got "):
                senses.GetGloss(bad)

    @pytest.mark.live_phase("TextOperations", "read")
    def test_text_resolver_object_hvo_and_wrong_types(self, sena3_sandbox):
        texts = sena3_sandbox.Texts
        text = _first(texts.GetAll())
        assert text is not None, "Sena 3 sandbox has no texts"

        assert texts.GetName(text) == texts.GetName(text.Hvo)
        resolve = texts._TextOperations__GetTextObject
        assert resolve(text.Hvo).Hvo == text.Hvo
        for bad in WRONG_TYPES:
            with pytest.raises(FP_ParameterError, match="got "):
                texts.GetName(bad)

    @pytest.mark.live_phase("POSOperations", "read")
    def test_pos_resolver_wrong_types_via_public_api(self, sena3_sandbox):
        pos_ops = sena3_sandbox.POS
        pos = _first(pos_ops.GetAll())
        assert pos is not None
        pos = _raw(pos)
        assert pos_ops.GetName(pos) == pos_ops.GetName(pos.Hvo)
        # POSOperations resolvers pass wrong types through to a typed
        # error path of their own; the call must not raise a raw
        # AttributeError.
        for bad in WRONG_TYPES:
            with pytest.raises(FP_ParameterError):
                pos_ops.GetName(bad)

    @pytest.mark.live_phase("WfiAnalysisOperations", "read")
    def test_wfi_analysis_resolvers_real_objects_and_wrong_types(self, sena3_sandbox):
        analyses = sena3_sandbox.WfiAnalyses
        wordform = next(
            (w for w in sena3_sandbox.Wordforms.GetAll() if w.AnalysesOC.Count > 0),
            None,
        )
        assert wordform is not None, "Sena 3 sandbox has no analysed wordform"
        analysis = _first(wordform.AnalysesOC)

        get_wf = analyses._WfiAnalysisOperations__GetWordformObject
        get_an = analyses._WfiAnalysisOperations__GetAnalysisObject
        assert get_wf(wordform.Hvo).Hvo == wordform.Hvo
        assert get_wf(wordform).ClassName == "WfiWordform"
        assert get_an(analysis.Hvo).Hvo == analysis.Hvo
        assert get_an(analysis).ClassName == "WfiAnalysis"
        for bad in WRONG_TYPES:
            with pytest.raises(FP_ParameterError):
                get_wf(bad)
            with pytest.raises(FP_ParameterError):
                get_an(bad)

    @pytest.mark.live_phase("BaseOperations", "read")
    def test_shared_get_object_resolver(self, sena3_sandbox):
        """BaseOperations._GetObject: the shared root of #618."""
        senses = sena3_sandbox.Senses
        entry = next(
            e for e in sena3_sandbox.LexEntry.GetAll() if e.SensesOS.Count > 0
        )
        sense = entry.SensesOS[0]

        assert senses._GetObject(sense.Hvo).Hvo == sense.Hvo
        print(f"[EVIDENCE] _GetObject(hvo={sense.Hvo}) -> Hvo={senses._GetObject(sense.Hvo).Hvo} ClassName={senses._GetObject(sense.Hvo).ClassName}")
        for bad in WRONG_TYPES:
            try:
                senses._GetObject(bad)
            except FP_ParameterError as e:
                print(f"[EVIDENCE] _GetObject({bad!r}) -> FP_ParameterError: {e}")
        assert senses._GetObject(sense) is sense
        # Wrapper path: an Allomorph/MSA GetAll() item is an LCMObjectWrapper.
        for wrapped in sena3_sandbox.MSA.GetAll(entry):
            raw = senses._GetObject(wrapped)
            assert raw.Hvo == _raw(wrapped).Hvo
            break
        for bad in WRONG_TYPES + [None]:
            with pytest.raises(FP_ParameterError, match="Expected an LCM object"):
                senses._GetObject(bad)
        # Public entry point that routes through _GetObject.
        for bad in WRONG_TYPES:
            with pytest.raises(FP_ParameterError):
                senses.Sort(bad)


class TestResolversWriteSafetyTargetSandbox:
    """A rejected wrong-type argument must not mutate the project."""

    @pytest.mark.live_phase("ConstChartOperations", "update")
    def test_chart_rename_roundtrip_and_str_arg_changes_nothing(self, target_sandbox):
        charts = target_sandbox.ConstCharts
        chart = charts.Create(f"{TEST_PREFIX}618 chart")
        try:
            pre = charts.GetName(chart)
            print(f"[EVIDENCE] chart hvo={chart.Hvo} PRE name={pre!r}")
            assert pre == f"{TEST_PREFIX}618 chart"

            # Wrong type: typed error, no mutation.
            with pytest.raises(FP_ParameterError, match="got str"):
                charts.SetName("not-a-chart", "TEST_618 should not be written")
            assert charts.GetName(chart) == pre
            print(f"[EVIDENCE] after rejected str arg: name={charts.GetName(chart)!r} (unchanged)")

            # Real object and HVO both still write through.
            charts.SetName(chart, f"{TEST_PREFIX}618 by object")
            assert charts.GetName(chart.Hvo) == f"{TEST_PREFIX}618 by object"
            charts.SetName(chart.Hvo, f"{TEST_PREFIX}618 by hvo")
            assert charts.GetName(chart) == f"{TEST_PREFIX}618 by hvo"
            print(f"[EVIDENCE] POST (re-read via object) name={charts.GetName(chart)!r}")

            # Row resolver (ConstChartRowOperations.__ResolveChart / Row).
            rows = target_sandbox.ConstChartRows
            row = rows.Create(chart.Hvo, label=f"{TEST_PREFIX}618 row")
            try:
                assert rows.GetLabel(row) == rows.GetLabel(row.Hvo)
                with pytest.raises(FP_ParameterError, match="got "):
                    rows.GetLabel(["not", "a", "row"])
                with pytest.raises(FP_ParameterError, match="got str"):
                    rows.Create("not-a-chart", label="x")
            finally:
                rows.Delete(row)
        finally:
            charts.Delete(chart)
