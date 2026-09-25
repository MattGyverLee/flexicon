#
#   test_issue468_wrapper_eq_hash_offline.py
#
#   Offline regression for issue #468: LCMObjectWrapper and PythonicWrapper
#   compare and hash by LCM Hvo so membership and set/dict use works against
#   raw LCM objects.
#
#   Loads wrapper modules with a stub package tree so pytest can run without
#   FieldWorks / pythonnet (cloud agents).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import importlib.util
import os
import sys
import types
from pathlib import Path

_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


_STUBBED_MODULES = (
    "flexicon",
    "flexicon.code",
    "flexicon.code.Shared",
    "flexicon.code.lcm_casting",
    "flexicon.code.Shared.lcm_constants",
    "flexicon.code.Shared.wrapper_base",
    "flexicon.code.PythonicWrapper",
)


def _load_wrapper_modules():
    # Snapshot and restore every sys.modules key the stubs touch. Leaving the
    # stub lcm_casting in place broke collection of every later module that
    # imports the real one (same bug class as #476). The loaded modules keep
    # their import-time bindings, so restoring afterwards is safe.
    saved = {name: sys.modules.get(name) for name in _STUBBED_MODULES}
    try:
        return _load_wrapper_modules_stubbed()
    finally:
        for name, module in saved.items():
            if module is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = module


def _load_wrapper_modules_stubbed():
    for name in ("flexicon", "flexicon.code", "flexicon.code.Shared"):
        if name not in sys.modules:
            sys.modules[name] = types.ModuleType(name)

    lcm = types.ModuleType("flexicon.code.lcm_casting")
    lcm.cast_to_concrete = lambda obj: obj
    sys.modules["flexicon.code.lcm_casting"] = lcm

    constants = types.ModuleType("flexicon.code.Shared.lcm_constants")
    constants.SUFFIXES = ("OA", "OS", "OC", "RA", "RS", "RC")
    sys.modules["flexicon.code.Shared.lcm_constants"] = constants

    base_path = Path(_project_root) / "flexicon/code/Shared/wrapper_base.py"
    spec = importlib.util.spec_from_file_location(
        "flexicon.code.Shared.wrapper_base", base_path
    )
    wrapper_base = importlib.util.module_from_spec(spec)
    sys.modules["flexicon.code.Shared.wrapper_base"] = wrapper_base
    spec.loader.exec_module(wrapper_base)

    py_path = Path(_project_root) / "flexicon/code/PythonicWrapper.py"
    spec2 = importlib.util.spec_from_file_location(
        "flexicon.code.PythonicWrapper", py_path
    )
    py_mod = importlib.util.module_from_spec(spec2)
    sys.modules["flexicon.code.PythonicWrapper"] = py_mod
    spec2.loader.exec_module(py_mod)

    return wrapper_base, py_mod


_wrapper_base, _py_mod = _load_wrapper_modules()
LCMObjectWrapper = _wrapper_base.LCMObjectWrapper
lcm_identity_hvo = _wrapper_base.lcm_identity_hvo
PythonicWrapper = _py_mod.PythonicWrapper


class _FakeLcm:
    def __init__(self, hvo, class_name="MoStemAllomorph"):
        self.Hvo = hvo
        self.ClassName = class_name


class TestLcmIdentityHvo:
    def test_extracts_from_raw_and_wrappers(self):
        raw = _FakeLcm(42)
        wrapped = LCMObjectWrapper(raw)
        py = PythonicWrapper(raw)
        assert lcm_identity_hvo(raw) == 42
        assert lcm_identity_hvo(wrapped) == 42
        assert lcm_identity_hvo(py) == 42


class TestLCMObjectWrapperEqHash:
    def test_equals_raw_same_hvo(self):
        raw = _FakeLcm(100)
        wrapped = LCMObjectWrapper(raw)
        assert wrapped == raw
        # Raw LCM objects use .NET equality; wrapper-to-raw is the fixed direction.

    def test_equals_other_wrapper_same_hvo(self):
        raw = _FakeLcm(101)
        a = LCMObjectWrapper(raw)
        b = LCMObjectWrapper(_FakeLcm(101))
        assert a == b

    def test_not_equal_different_hvo(self):
        a = LCMObjectWrapper(_FakeLcm(1))
        b = LCMObjectWrapper(_FakeLcm(2))
        assert a != b

    def test_membership_in_fake_sequence(self):
        raw = _FakeLcm(200)
        wrapped = LCMObjectWrapper(raw)
        seq = [raw, _FakeLcm(201)]
        assert wrapped in seq

    def test_set_deduplicates_two_wrappers_same_hvo(self):
        a = LCMObjectWrapper(_FakeLcm(300))
        b = LCMObjectWrapper(_FakeLcm(300))
        assert len({a, b}) == 1

    def test_pythonic_wrapper_cross_equality(self):
        raw = _FakeLcm(400)
        lcm_wrap = LCMObjectWrapper(raw)
        py_wrap = PythonicWrapper(raw)
        assert lcm_wrap == py_wrap
        assert py_wrap == raw


class TestPythonicWrapperEqHash:
    def test_hash_matches_hvo(self):
        raw = _FakeLcm(500)
        py = PythonicWrapper(raw)
        assert hash(py) == hash(500)


def test_issue468_wrapper_base_defines_eq_hash():
    text = (Path(_project_root) / "flexicon/code/Shared/wrapper_base.py").read_text(
        encoding="utf-8"
    )
    assert "def __eq__(self, other):" in text
    assert "def __hash__(self):" in text
    assert "def lcm_identity_hvo(obj):" in text
