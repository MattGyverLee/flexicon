# -*- coding: utf-8 -*-
#
#   flexicon.code.Shared.gendate_utils
#
#   Build SIL.LCModel.Core.Cellar.GenDate values from caller input.
#
#   IRnGenericRec.DateOfEvent and ICmPerson.DateOfBirth / DateOfDeath are
#   CLR-typed GenDate structs. pythonnet converts neither a Python str nor
#   a System.DateTime to GenDate, so assigning either raises TypeError
#   (live-proven 2026-09-23, issue #330). Callers must hand the setter a
#   constructed GenDate.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import System
from System import DateTime
from SIL.LCModel.Core.Cellar import GenDate

from ..FLExProject import FP_ParameterError


def empty_gendate():
    """Return the empty GenDate (IsEmpty is True), used to clear a field."""
    # GenDate has no parameterless ctor under pythonnet; encoded value 0
    # is the empty date.
    return GenDate(0)


def gendate_from_input(date, allow_empty=False):
    """
    Convert a date string or System.DateTime to an exact AD GenDate.

    Args:
        date: A ``System.DateTime``, a ``GenDate`` (returned unchanged), or
            a string that ``DateTime.Parse`` accepts ("YYYY-MM-DD",
            "YYYY-MM-DD HH:MM:SS", ...).
        allow_empty (bool): If True, "" (after stripping) returns the empty
            GenDate instead of raising.

    Returns:
        GenDate: Precision ``Exact``, AD. GenDate has no time component, so
        any time of day in the input is dropped.

    Raises:
        FP_ParameterError: If the string does not parse, or the type is
            unsupported.
    """
    if isinstance(date, GenDate):
        return date
    if isinstance(date, str):
        text = date.strip()
        if not text and allow_empty:
            return empty_gendate()
        try:
            parsed = DateTime.Parse(text)
        except (System.FormatException, ValueError, TypeError) as e:
            raise FP_ParameterError(
                f"Invalid date format: {date}. Use 'YYYY-MM-DD' or "
                f"'YYYY-MM-DD HH:MM:SS' - {e}"
            )
    elif isinstance(date, DateTime):
        parsed = date
    else:
        raise FP_ParameterError(
            f"Invalid date type: {type(date).__name__}. "
            "Use a System.DateTime or date string."
        )

    return GenDate(
        GenDate.PrecisionType.Exact, parsed.Month, parsed.Day, parsed.Year, True
    )
