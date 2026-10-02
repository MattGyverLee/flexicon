# -*- coding: utf-8 -*-
#
#   flexicon.code.Shared.arg_checks
#
#   Argument-type checks shared by the Operations "resolver" helpers
#   (the private ``__Resolve*`` / ``__Get*Object`` methods and
#   ``BaseOperations._GetObject``).
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#

from ..exceptions import FP_ParameterError

# Python types that can never be an LCM object. A ``str`` is the realistic
# trap (callers pass a name/form where an object or HVO is expected); the
# rest are the other shapes seen from agent callers. ``int`` is deliberately
# absent: ints are HVOs and are handled by the resolvers before this check.
_NON_LCM_TYPES = (
    str, bytes, bytearray, float, complex, bool, list, tuple, dict, set,
    frozenset,
)


def is_non_lcm_value(value):
    """
    True if ``value`` is ``None`` or a builtin scalar/container that can
    never be an LCM object (see ``require_lcm_object``).

    Lets a caller that wants its own method-specific error message (e.g.
    ``DescribeFeatStruc``) test for the wrong-type shape *before* invoking
    a resolver, whose generic message would otherwise pre-empt it.
    """
    return value is None or isinstance(value, _NON_LCM_TYPES)


def require_lcm_object(value, expected):
    """
    Return ``value`` if it looks like an LCM object, else raise.

    Resolvers accept an int HVO or an LCM object (wrappers are unwrapped
    before the resolver reaches this check). Anything else used to be
    returned unchanged and then failed deep inside the calling method with
    a raw ``AttributeError`` (issue #618; the same shape as #600). This
    turns that into a typed ``FP_ParameterError`` naming the expected type.

    The test is deliberately a blacklist: ``None`` and the obviously-not-LCM
    Python builtins are rejected; everything else (raw pythonnet objects,
    wrappers that proxy attribute access, test doubles) is passed through
    untouched so object identity and whatever cast the resolver already
    applied are preserved. A ``hasattr(value, "Hvo")`` requirement was
    tried and rejected: it breaks legitimate duck-typed stand-ins and
    wrapper objects, and the builtin-type check already covers the failure
    shape reported in #618 (a ``str`` where an object/HVO belongs).

    Args:
        value: The resolver's remaining (non-int) argument.
        expected: Human-readable expected type, e.g. ``"IConstChartRow"``.

    Returns:
        ``value``, unchanged.

    Raises:
        FP_ParameterError: If ``value`` is None or a builtin scalar/
            container (str, bytes, float, bool, list, tuple, dict, ...).
    """
    if not is_non_lcm_value(value):
        return value
    raise FP_ParameterError(
        f"Expected {expected} object or an int HVO, got "
        f"{type(value).__name__}."
    )
