# -*- coding: utf-8 -*-
#
#   flexlibs2.code.Shared.string_utils
#
#   String utility functions for FlexLibs2.
#
#   FLEx/LCM uses '***' as a placeholder when multilingual string fields
#   have no value set. This module provides utilities to normalize these
#   values to empty strings, matching the behavior of FlexLibs stable.
#

import unicodedata

# FLEx's null marker for empty multilingual string fields
FLEX_NULL_MARKER = "***"


def normalize_text(text):
    """
    Normalize a text value from LCM, converting FLEx's null marker to empty string.

    FLEx/LCM uses '***' as a placeholder when multilingual string fields
    (IMultiString, IMultiUnicode) have no value set. This function normalizes
    such values to empty strings for consistent handling.

    Args:
        text: A string value from an LCM text field, or None

    Returns:
        The original text if it has content, or "" if None/empty/'***'

    Example:
        >>> from flexlibs2.code.Shared.string_utils import normalize_text
        >>> normalize_text("***")
        ''
        >>> normalize_text(None)
        ''
        >>> normalize_text("hello")
        'hello'
        >>> normalize_text("")
        ''
    """
    if text is None:
        return ""
    if text == FLEX_NULL_MARKER:
        return ""
    return text


def normalize_match_key(text, casefold=True):
    """
    Produce a key suitable for matching a Python-side string against an
    FLEx-stored multilingual string value.

    FLEx stores all IMultiString/IMultiUnicode values in NFD; Python source
    is typically NFC. Without normalization, any string containing combined
    diacritics will silently fail to match. Apply this to BOTH sides of any
    Find/Exists comparison.

    Args:
        text: Input string (may be None, '', or '***').
        casefold: If True (default), apply str.casefold() after NFD
                  normalization. Pass False for case-sensitive Find methods.
                  Use casefold (not lower) for correct handling of Turkish
                  dotted/dotless I, German ess-zett, etc.

    Returns:
        Normalized string. Empty string for None/empty/'***' inputs.

    Example:
        >>> needle = normalize_match_key("oo", casefold=False)
        >>> haystack = normalize_match_key(ITsString(p.Name.get_String(ws)).Text,
        ...                                casefold=False)
        >>> needle == haystack  # True even when Python NFC differs from LCM NFD
        True
    """
    text = normalize_text(text)
    if not text:
        return ""
    text = unicodedata.normalize("NFD", text)
    if casefold:
        text = text.casefold()
    return text


def normalize_ws_handle(ws):
    """
    Normalize a writing-system argument to an integer handle.

    LCM methods such as ``ITsMultiString.get_String`` require a plain
    ``int`` handle.  Users naturally obtain writing-system objects from
    ``project.WritingSystems`` (``CoreWritingSystemDefinition``) or pass
    an int they already have.  This helper smooths over both cases so
    wrappers don't expose a confusing pythonnet ``TypeError`` when the
    caller passes an object instead of a raw handle.

    Args:
        ws: An ``int`` handle, a ``CoreWritingSystemDefinition`` (or any
            object that exposes a ``.Handle`` attribute returning an
            ``int``), or ``None``.

    Returns:
        ``int`` handle, or ``None`` if ``ws`` is ``None``.

    Raises:
        TypeError: If ``ws`` is not ``None``, not an ``int``, and has no
            ``.Handle`` attribute.

    Example:
        >>> from flexlibs2.code.Shared.string_utils import normalize_ws_handle
        >>> normalize_ws_handle(123)
        123
        >>> normalize_ws_handle(None) is None
        True
        >>> # CoreWritingSystemDefinition object with .Handle == 1
        >>> normalize_ws_handle(ws_def)
        1
    """
    if ws is None:
        return None
    if isinstance(ws, int):
        return ws
    handle = getattr(ws, "Handle", None)
    if handle is not None:
        return int(handle)
    raise TypeError(
        f"Unsupported writing-system argument type: {type(ws).__name__}. "
        "Pass an int handle or a CoreWritingSystemDefinition object."
    )


def is_empty_text(text):
    """
    Check if a text value from LCM is empty (None, empty string, or '***').

    Args:
        text: A string value from an LCM text field, or None

    Returns:
        True if the text represents an empty/unset value

    Example:
        >>> from flexlibs2.code.Shared.string_utils import is_empty_text
        >>> is_empty_text("***")
        True
        >>> is_empty_text(None)
        True
        >>> is_empty_text("")
        True
        >>> is_empty_text("hello")
        False
    """
    if text is None:
        return True
    if not text or text == FLEX_NULL_MARKER:
        return True
    return False


def best_analysis_text(multi_obj):
    """
    Get the best analysis alternative text from an IMultiString/IMultiUnicode,
    normalized to empty string if unset.

    This combines accessing .BestAnalysisAlternative.Text with null marker handling.

    Args:
        multi_obj: An IMultiString or IMultiUnicode object, or None

    Returns:
        The text content, or "" if None/empty/'***'

    Example:
        >>> text = best_analysis_text(sense.Definition)
        >>> text = best_analysis_text(pos.Name)
    """
    if multi_obj is None:
        return ""
    text = multi_obj.BestAnalysisAlternative.Text
    return normalize_text(text)


def best_vernacular_text(multi_obj):
    """
    Get the best vernacular alternative text from an IMultiString/IMultiUnicode,
    normalized to empty string if unset.

    This combines accessing .BestVernacularAlternative.Text with null marker handling.

    Args:
        multi_obj: An IMultiString or IMultiUnicode object, or None

    Returns:
        The text content, or "" if None/empty/'***'

    Example:
        >>> text = best_vernacular_text(entry.LexemeFormOA.Form)
    """
    if multi_obj is None:
        return ""
    text = multi_obj.BestVernacularAlternative.Text
    return normalize_text(text)


def best_text(multi_obj):
    """
    Get the best analysis-or-vernacular alternative text from an IMultiString/IMultiUnicode,
    normalized to empty string if unset.

    This combines accessing .BestAnalysisVernacularAlternative.Text with null marker handling.
    Prefers analysis writing system, falls back to vernacular.

    Args:
        multi_obj: An IMultiString or IMultiUnicode object, or None

    Returns:
        The text content, or "" if None/empty/'***'

    Example:
        >>> text = best_text(sense.Gloss)
    """
    if multi_obj is None:
        return ""
    text = multi_obj.BestAnalysisVernacularAlternative.Text
    return normalize_text(text)
