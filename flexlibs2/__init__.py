# ----------------------------------------------------------------------------
# Name:         flexlibs2  (compatibility alias)
# Purpose:      Backward-compatibility shim. The library formerly published as
#               `flexlibs2` is now `flexicon` (distribution name: pyflexicon).
#
#               This package aliases the whole `flexlibs2` namespace onto
#               `flexicon` so that existing code -- including FlexTools /
#               FlexTrans scripts on disk -- keeps working unchanged:
#
#                   import flexlibs2
#                   from flexlibs2 import FLExProject, LexEntryOperations
#                   from flexlibs2.code.lcm_casting import cast_to_concrete
#
#               all resolve to the SAME `flexicon` objects. A meta-path finder
#               guarantees identity for arbitrarily deep submodules (so
#               `flexlibs2.code.X.Y is flexicon.code.X.Y`), which matters for
#               isinstance / casting checks that compare classes by identity.
#
#   DEPRECATED:  The `flexlibs2` alias will be REMOVED in flexicon v5.0.0.
#                Update imports to `flexicon` before then.
# ----------------------------------------------------------------------------

import importlib
import importlib.abc
import importlib.util
import sys
import warnings

import flexicon

_SELF = "flexlibs2"
_TARGET = "flexicon"


class _FlexiconAliasFinder(importlib.abc.MetaPathFinder, importlib.abc.Loader):
    """Redirect every `flexlibs2.<sub>` import to the already-imported
    `flexicon.<sub>` module object, preserving identity (no re-execution)."""

    _prefix = _SELF + "."

    def find_spec(self, fullname, path=None, target=None):
        if fullname != _SELF and not fullname.startswith(self._prefix):
            return None
        return importlib.util.spec_from_loader(fullname, self)

    def create_module(self, spec):
        if spec.name == _SELF:
            return flexicon
        target = _TARGET + spec.name[len(_SELF):]
        module = importlib.import_module(target)
        sys.modules[spec.name] = module
        return module

    def exec_module(self, module):
        # Module is fully initialised by flexicon; nothing to execute here.
        pass


# Point the top-level name at flexicon, and install the finder so deep
# submodule imports resolve to the identical flexicon objects.
sys.modules[_SELF] = flexicon
if not any(isinstance(f, _FlexiconAliasFinder) for f in sys.meta_path):
    sys.meta_path.insert(0, _FlexiconAliasFinder())

warnings.warn(
    "The 'flexlibs2' package has been renamed to 'flexicon' "
    "(pip install pyflexicon). The 'flexlibs2' import alias still works but is "
    "deprecated and will be removed in flexicon v5.0.0; update your imports to "
    "'flexicon'.",
    DeprecationWarning,
    stacklevel=2,
)
