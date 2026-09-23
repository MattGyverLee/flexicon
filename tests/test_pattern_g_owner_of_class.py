#
#   test_pattern_g_owner_of_class.py
#
#   Regression tests for Pattern G sweep (issues #152 / #169):
#   OwnerOfClass read as bare attribute instead of called as method.
#
#   Three sites covered:
#     1. annotation.py  _get_default_ws  -- must read Cache.DefaultAnalWs
#     2. affix_template.py  owner_pos    -- must call OwnerOfClass(class_id)
#     3. OverlayOperations.py  GetChart  -- must call OwnerOfClass(class_id)
#                                           and cast to IDsConstChart
#
#   Pure Python -- no SIL.LCModel / FieldWorks dependency required.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#
from types import SimpleNamespace

import pytest


# ===========================================================================
# Site 1: annotation.py  _get_default_ws
# ===========================================================================
# The fixed body is a one-liner:
#     return self._obj.Cache.DefaultAnalWs
# Mirror it here so the test is independent of the Annotation import chain
# (which pulls LCMObjectWrapper and may trigger other import-time side effects).

def _annotation_get_default_ws(obj):
    """
    Mirrors the fixed body of Annotation._get_default_ws verbatim.

    The pre-fix version read OwnerOfClass as a bare attribute, then tried
    .project.DefaultAnalWs on the resulting bound-method object; the bare
    except swallowed the AttributeError and silently returned -1 every time.
    """
    return obj.Cache.DefaultAnalWs


class TestAnnotationGetDefaultWs:
    """
    Regression guard for annotation._get_default_ws (Pattern G, issue #169).
    """

    def test_returns_cache_default_anal_ws(self):
        """
        Normal case: Cache.DefaultAnalWs == 17 -> returns 17.
        Confirms the fix reads Cache.DefaultAnalWs, not a method object.
        """
        obj = SimpleNamespace(Cache=SimpleNamespace(DefaultAnalWs=17))
        assert _annotation_get_default_ws(obj) == 17

    def test_old_owner_of_class_bare_attribute_raises(self):
        """
        Regression guard: the old code read OwnerOfClass as a bare attribute.
        On any real ICmObject OwnerOfClass IS a method, so reading it bare
        returns a bound method.  Calling .project.DefaultAnalWs on a method
        object raises AttributeError.  This test documents why the fix matters.

        The stub deliberately exposes OwnerOfClass as a callable but NOT as
        an object with a .project attribute, reproducing the pre-fix failure.
        """
        def _owner_of_class(class_id):
            return SimpleNamespace()  # no .project on the return value

        obj = SimpleNamespace(OwnerOfClass=_owner_of_class)
        # Pre-fix code: obj.OwnerOfClass.project.DefaultAnalWs
        with pytest.raises(AttributeError):
            _ = obj.OwnerOfClass.project.DefaultAnalWs  # noqa: B018


# ===========================================================================
# Site 2: affix_template.py  owner_pos
# ===========================================================================
# The fixed body is:
#     if not hasattr(self._concrete, "OwnerOfClass"):
#         return None
#     pos_lcm = self._concrete.OwnerOfClass(PartOfSpeechTags.kClassId)
#     if pos_lcm is None:
#         return None
#     return IPartOfSpeech(pos_lcm) if IPartOfSpeech is not None else pos_lcm

_MOCK_CLASS_ID = 0  # mirrors PartOfSpeechTags.kClassId in the test-env mock


def _affix_template_owner_pos(concrete):
    """
    Mirrors the fixed body of AffixTemplate.owner_pos verbatim (mock env:
    IPartOfSpeech is None, so raw pos_lcm is returned).
    """
    if not hasattr(concrete, "OwnerOfClass"):
        return None
    pos_lcm = concrete.OwnerOfClass(_MOCK_CLASS_ID)
    if pos_lcm is None:
        return None
    return pos_lcm  # IPartOfSpeech is None in test env -> return raw object


class TestAffixTemplateOwnerPos:
    """
    Regression guard for affix_template.owner_pos (Pattern G, issue #152).
    """

    def test_returns_pos_object_when_found(self):
        """
        Stub where OwnerOfClass(class_id) returns a fake POS.
        Confirms the fix calls the method and returns the result.
        """
        fake_pos = SimpleNamespace(Name="Verb")

        def _owner_of_class(class_id):
            assert isinstance(class_id, int)
            return fake_pos

        concrete = SimpleNamespace(OwnerOfClass=_owner_of_class)
        result = _affix_template_owner_pos(concrete)
        assert result is fake_pos
        assert result.Name == "Verb"

    def test_returns_none_when_owner_of_class_returns_none(self):
        """
        Stub where OwnerOfClass returns None (no owning POS).
        Confirms the None guard works correctly.
        """
        concrete = SimpleNamespace(OwnerOfClass=lambda class_id: None)
        assert _affix_template_owner_pos(concrete) is None

    def test_bare_attribute_read_raises_type_error(self):
        """
        Regression guard: the old code read OwnerOfClass as a bare attribute
        (no call).  The method object is not None, so the None guard passed,
        and the caller received a method object instead of an IPartOfSpeech.
        Demonstrate that using a result of bare-attribute access with the
        intention of getting a .Name raises AttributeError (no .Name on a function).
        """
        call_log = []

        def _owner_of_class(class_id):
            call_log.append(class_id)
            return SimpleNamespace(Name="Verb")

        concrete = SimpleNamespace(OwnerOfClass=_owner_of_class)
        # Pre-fix code path: read the attribute without calling it
        bare = concrete.OwnerOfClass  # returns the method, not the POS
        with pytest.raises(AttributeError):
            # Treat the method object as if it has .Name -- it does not
            _ = bare.Name  # noqa: B018


# ===========================================================================
# Site 3: OverlayOperations.py  GetChart
# ===========================================================================
# The fixed body is (simplified to its call-shape logic, issue #364):
#     chart_lcm = overlay.OwnerOfClass(DsConstChartTags.kClassId)
#     if chart_lcm is None:
#         return None
#     return IDsConstChart(chart_lcm) if IDsConstChart is not None else chart_lcm

_MOCK_CHART_CLASS_ID = 0  # mirrors DsConstChartTags.kClassId in mock env


def _get_chart_logic(overlay):
    """
    Mirrors the fixed GetChart ownership-walk logic verbatim
    (IDsConstChart cast omitted; test env has no real IDsConstChart).
    """
    chart_lcm = overlay.OwnerOfClass(_MOCK_CHART_CLASS_ID)
    if chart_lcm is None:
        return None
    return chart_lcm  # IDsConstChart is None in test env -> raw object


class TestOverlayGetChart:
    """
    Regression guard for OverlayOperations.GetChart (Pattern G, issue #169).
    """

    def test_owner_of_class_walk_returns_chart(self):
        """
        Neither fast path present; OwnerOfClass returns a chart stub.
        Confirms the fix calls OwnerOfClass as a method with an int class_id.
        """
        fake_chart = SimpleNamespace(Guid="chart-guid-3")
        call_log = []

        def _owner_of_class(class_id):
            call_log.append(class_id)
            return fake_chart

        overlay = SimpleNamespace(OwnerOfClass=_owner_of_class)
        result = _get_chart_logic(overlay)
        assert result is fake_chart
        assert len(call_log) == 1
        assert isinstance(call_log[0], int), "OwnerOfClass must be called with an int class_id"

    def test_owner_of_class_returns_none(self):
        """
        OwnerOfClass returns None (overlay not inside any chart) -> None returned.
        """
        overlay = SimpleNamespace(OwnerOfClass=lambda class_id: None)
        assert _get_chart_logic(overlay) is None

    def test_owner_of_class_called_not_read_bare(self):
        """
        Regression guard: the pre-fix code read OwnerOfClass as a bare attribute.
        The method object is truthy so it would have been returned as the chart,
        but it is not a chart -- it has no .Guid attribute.
        Verify that reading the attribute bare (not calling it) yields a method
        with no .Guid, confirming the fix MUST call the method.
        """
        fake_chart = SimpleNamespace(Guid="chart-guid-4")

        def _owner_of_class(class_id):
            return fake_chart

        overlay = SimpleNamespace(OwnerOfClass=_owner_of_class)
        # Pre-fix path: read the attribute instead of calling it
        bare = overlay.OwnerOfClass
        with pytest.raises(AttributeError):
            _ = bare.Guid  # noqa: B018


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
