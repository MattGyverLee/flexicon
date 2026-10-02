# -*- coding: utf-8 -*-
#
#   flexicon.code.Shared.ws_text
#
#   Writing-system-aware read/match helpers for possibility-list style
#   Operations classes (issues #183, #604, #624).
#
#   Reading a MultiString through ``DefaultAnalWs`` alone returns "" on a
#   project whose default analysis WS holds no text for the object (e.g.
#   Sena 3: default analysis 'pt', list text only in 'en'). These helpers
#   centralise the fix: no explicit WS -> best alternative; lookups match the
#   best alternative plus every current writing system of the right kind.
#
#   Platform: Python.NET, FieldWorks 9+
#

from SIL.LCModel.Core.KernelInterfaces import ITsString

from .string_utils import (
    best_analysis_text,
    best_vernacular_text,
    normalize_match_key,
    normalize_text,
)


def _best(multi_obj, prefer):
    if prefer == "vernacular":
        return best_vernacular_text(multi_obj) or best_analysis_text(multi_obj)
    return best_analysis_text(multi_obj)


def read_text(multi_obj, wsHandle=None, prefer="analysis"):
    """Read a MultiString.

    With ``wsHandle=None`` return the best alternative (analysis, or
    vernacular-then-analysis when ``prefer="vernacular"``). With an explicit
    handle return exactly that alternative ("" if unset).
    """
    if wsHandle is None:
        return _best(multi_obj, prefer)
    return ITsString(multi_obj.get_String(wsHandle)).Text or ""


def candidate_texts(multi_obj, lp, prefer="analysis"):
    """Texts to match a name against when no explicit WS was requested:
    the best alternative first, then each current analysis WS (and each
    current vernacular WS when ``prefer="vernacular"``)."""
    candidates = [_best(multi_obj, prefer)]
    systems = list(lp.CurrentAnalysisWritingSystems)
    if prefer == "vernacular":
        systems = list(lp.CurrentVernacularWritingSystems) + systems
    for ws in systems:
        text = normalize_text(ITsString(multi_obj.get_String(ws.Handle)).Text)
        if text and text not in candidates:
            candidates.append(text)
    return candidates


def name_matches(multi_obj, target, lp, explicit_ws=None, casefold=True, prefer="analysis"):
    """True if ``multi_obj`` matches ``target`` (already normalized with
    ``normalize_match_key(..., casefold=casefold).strip()``-style key).

    ``explicit_ws`` (a resolved handle) restricts the comparison to that one
    alternative; otherwise see :func:`candidate_texts`.
    """
    if explicit_ws is not None:
        candidates = [ITsString(multi_obj.get_String(explicit_ws)).Text]
    else:
        candidates = candidate_texts(multi_obj, lp, prefer)
    for candidate in candidates:
        if candidate and normalize_match_key(candidate, casefold=casefold).strip() == target:
            return True
    return False
