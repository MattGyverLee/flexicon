#
#   test_sphinx_conf_clr_skip.py
#
#   Regression guard for the Sphinx autodoc guard in docs/sphinx/conf.py.
#
#   Platform: Python (no FieldWorks required)
#
#   Copyright 2025
#

"""
Pin the ``autodoc-skip-member`` guard that keeps the docs build alive.

``HeadlessLcmUI`` subclasses an LCM interface and sets ``__namespace__``, so
pythonnet emits a real derived .NET type for it. pythonnet's IL emitter never
calls ``MethodBuilder.DefineParameter``, so the emitted ``Equals(System.Object)``
override has ``ParameterInfo.Name is None``. autodoc formats every member's
signature, which reads ``__signature__``; pythonnet answers that from
``MethodBinding.get_Signature()``, which feeds the null name to
``inspect.Parameter()`` and raises ``TypeError: name must be a str, not a
NoneType``. Because that raise happens inside the native ``tp_getattro`` slot it
escapes as an *unhandled CLR exception* and aborts the whole process -- no
traceback, no Sphinx warning, exit 127. That is why publish-docs.yml never
produced a site.

The guard in conf.py skips every member whose type lives in pythonnet's ``CLR``
pseudo-module. These tests exercise it with stand-ins so they run anywhere; the
end-to-end proof is a real ``sphinx-build`` on a FieldWorks machine.
"""

import os
import sys
import types

import pytest

_CONF = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    "docs",
    "sphinx",
    "conf.py",
)


def _load_conf():
    """Exec conf.py as a module without importing flexicon (or FieldWorks)."""
    import importlib.util

    spec = importlib.util.spec_from_file_location("_flexicon_sphinx_conf", _CONF)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def _obj_typed_in(module_name):
    """An instance whose type reports ``__module__ == module_name``."""
    cls = type("Stand_in", (), {})
    cls.__module__ = module_name
    return cls()


class TestSphinxCLRSkipGuard:
    def test_conf_py_is_importable(self):
        conf = _load_conf()
        assert conf.project == "flexicon"

    def test_setup_connects_the_skip_handler(self):
        conf = _load_conf()
        connected = []

        class FakeApp:
            def connect(self, event, handler):
                connected.append((event, handler))

        conf.setup(FakeApp())
        events = [e for e, _ in connected]
        assert "autodoc-skip-member" in events, (
            "conf.py must connect autodoc-skip-member; without it the docs "
            "build aborts on pythonnet MethodBinding members."
        )

    def test_clr_members_are_skipped(self):
        conf = _load_conf()
        clr_member = _obj_typed_in("CLR")
        assert conf._skip_clr_bindings(None, "method", "Equals", clr_member, False, {}) is True

    def test_plain_python_members_are_not_skipped(self):
        conf = _load_conf()

        def DisplayMessage(self):
            pass

        # Returning None defers to autodoc's own decision rather than forcing
        # the member in or out.
        assert (
            conf._skip_clr_bindings(None, "method", "DisplayMessage", DisplayMessage, False, {})
            is None
        )

    def test_the_clr_metatype_is_not_skipped(self):
        """
        HeadlessLcmUI itself has type clr._internal.CLRMetatype and MUST stay
        documented. Only members typed in the "CLR" pseudo-module are dropped.
        """
        conf = _load_conf()
        metatyped = _obj_typed_in("clr._internal")
        assert (
            conf._skip_clr_bindings(None, "class", "HeadlessLcmUI", metatyped, False, {}) is None
        )
