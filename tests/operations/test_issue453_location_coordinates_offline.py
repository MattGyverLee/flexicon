#
#   test_issue453_location_coordinates_offline.py
#
#   Offline regression for issue #453: LocationOperations geo helpers
#   targeted phantom LCM members (DateOfEvent / Elevation) and silently
#   no-opped on write.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import sys
from unittest.mock import MagicMock, Mock

import pytest

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

try:
    import clr  # noqa: F401
except RuntimeError:
    pytest.skip(
        "pythonnet/.NET runtime unavailable on this host",
        allow_module_level=True,
    )

from flexicon.code.FLExProject import FP_ParameterError
from flexicon.code.Notebook.LocationOperations import (
    LocationOperations,
    _LCM_LOCATION_GEO_UNSUPPORTED,
)


class TestIssue453LocationGeoUnsupportedOffline:
    def _ops(self):
        project = Mock()
        project.writeEnabled = True
        ops = LocationOperations(project)
        ops._TransactionCM = MagicMock()
        ops._TransactionCM.return_value.__enter__ = Mock(return_value=None)
        ops._TransactionCM.return_value.__exit__ = Mock(return_value=False)
        location = Mock()
        location.ClassName = "CmLocation"
        # Name-mangled private resolver; a bare ``ops.__ResolveObject`` inside
        # this class would bind ``_TestIssue453...__ResolveObject`` instead.
        ops._LocationOperations__ResolveObject = Mock(return_value=location)
        return ops, location

    def test_set_coordinates_raises_with_lcm_truth_message(self):
        ops, _ = self._ops()
        with pytest.raises(FP_ParameterError, match="issue #453"):
            ops.SetCoordinates(Mock(), -1.23, -70.45)
        ops._TransactionCM.assert_not_called()

    def test_set_elevation_raises_with_lcm_truth_message(self):
        ops, _ = self._ops()
        with pytest.raises(FP_ParameterError, match="issue #453"):
            ops.SetElevation(Mock(), 150)
        ops._TransactionCM.assert_not_called()

    def test_get_coordinates_returns_none_without_dateofevent_probe(self):
        ops, location = self._ops()
        assert ops.GetCoordinates(location) is None
        # A Mock auto-creates any attribute read, so "never probed" means the
        # attribute never appeared among the Mock's accessed children.
        assert "DateOfEvent" not in location._mock_children
        assert "Elevation" not in location._mock_children

    def test_constant_documents_unsupported_shape(self):
        assert "DateOfEvent" in _LCM_LOCATION_GEO_UNSUPPORTED
        assert "Elevation" in _LCM_LOCATION_GEO_UNSUPPORTED
