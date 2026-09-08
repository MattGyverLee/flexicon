#
#   test_normalize_match_key.py
#
#   Class: TestNormalizeMatchKey
#          Unit tests for `normalize_match_key()` in
#          flexicon.code.Shared.string_utils. The helper produces an
#          NFD-(optionally casefolded)-key suitable for matching a
#          Python-side string (typically NFC) against an FLEx-stored
#          multilingual value (always NFD). It is the Phase 3 fix for
#          MattGyverLee/flexlibs issues #9 and #10, where Find()/Exists()
#          silently failed on combined diacritics (ö, ç, ş, ü, ğ, ...).
#
#          These tests are pure Python — no SIL.LCModel / FieldWorks
#          dependency — so they run in any environment.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#
import unicodedata

import pytest

from flexicon.code.Shared.string_utils import (
    FLEX_NULL_MARKER,
    normalize_match_key,
)


class TestNormalizeMatchKey:
    """
    Coverage for the NFD-normalizing match-key helper that backstops
    Find()/Exists() against FLEx's NFD storage convention.

    All tests are pure-Python; no live LCM required.
    """

    # ---- 1. NFC vs NFD round-trip ---------------------------------------

    def test_nfc_input_matches_nfd_storage(self):
        """
        Issue #10 core invariant: Python NFC input (``'\\u00f6'``, single
        codepoint) must hash-equal the NFD form (``'o' + '\\u0308'``) the
        same way after the helper runs. Without this, every Find('ö')
        against an NFD-stored phoneme silently misses.
        """
        nfc = "ö"          # precomposed 'ö' (1 codepoint)
        nfd = "ö"         # decomposed 'o' + COMBINING DIAERESIS

        # Sanity-check the test inputs really are different byte sequences.
        assert nfc != nfd, (
            "Test setup error: NFC and NFD forms accidentally identical"
        )

        assert normalize_match_key(nfc) == normalize_match_key(nfd)

    # ---- 2. Turkish dotted I + casefold ---------------------------------

    def test_casefold_handles_turkish_dotted_i(self):
        """
        ``'İ'`` (LATIN CAPITAL LETTER I WITH DOT ABOVE, U+0130) casefolds
        in Python to ``'i' + COMBINING DOT ABOVE`` (``'i\\u0307'``), NOT to
        plain ``'i'``. This is the point of casefold() over lower() — it
        preserves the linguistic distinction between Turkish dotted-I and
        ASCII I.

        So after normalize_match_key():
          * ``normalize_match_key('İ')`` ends up as ``'i\\u0307'`` (NFD
            then casefold leaves the combining mark in place).
          * ``normalize_match_key('I')`` ends up as ``'i'``.
        They must NOT compare equal. This guards against future "fixes"
        that switch the helper to ``.lower()`` and silently collapse
        Turkish I-variants.
        """
        dotted = normalize_match_key("İ", casefold=True)   # 'İ'
        plain = normalize_match_key("I", casefold=True)

        assert dotted != plain, (
            "casefold() must preserve Turkish dotted-I distinction; "
            "helper appears to be using lower() instead"
        )

        # And confirm the precise bytes we expect.
        assert dotted == "i̇"
        assert plain == "i"

    # ---- 3. casefold=False preserves case -------------------------------

    def test_casefold_false_preserves_case(self):
        """
        With casefold=False, NFD normalization runs but case is preserved.
        ``Ö`` and ``ö`` share the same diaeresis but differ on the base
        letter, so their keys must remain distinct.
        """
        upper_key = normalize_match_key("Ö", casefold=False)  # 'Ö'
        lower_key = normalize_match_key("ö", casefold=False)  # 'ö'

        assert upper_key != lower_key, (
            "casefold=False must preserve case; got identical keys for "
            "'Ö' and 'ö'"
        )

        # NFD form: base letter first, then combining diaeresis.
        assert upper_key == "Ö"
        assert lower_key == "ö"

    # ---- 4. None handling -----------------------------------------------

    def test_none_returns_empty_string(self):
        """
        None must yield ``""`` — never raise, never return None. Callers
        downstream do string comparisons, so a None leak would TypeError.
        """
        assert normalize_match_key(None) == ""
        assert normalize_match_key(None, casefold=False) == ""

    # ---- 5. FLEx null marker --------------------------------------------

    def test_flex_null_marker_returns_empty_string(self):
        """
        FLEx stores ``'***'`` for unset multilingual fields. The helper
        normalizes that to ``""`` so Find('***') doesn't accidentally
        "match" every empty field in the project.
        """
        assert normalize_match_key(FLEX_NULL_MARKER) == ""
        assert normalize_match_key("***") == ""
        assert normalize_match_key("***", casefold=False) == ""

    # ---- 6. Empty string -------------------------------------------------

    def test_empty_string_returns_empty_string(self):
        """Empty input round-trips to empty output."""
        assert normalize_match_key("") == ""
        assert normalize_match_key("", casefold=False) == ""

    # ---- 7. Turkish-phoneme diacritic battery ---------------------------

    @pytest.mark.parametrize(
        "nfc_char",
        [
            "ö",  # ö  o + diaeresis
            "ü",  # ü  u + diaeresis
            "ç",  # ç  c + cedilla
            "ş",  # ş  s + cedilla
            "ğ",  # ğ  g + breve
        ],
        ids=["o-umlaut", "u-umlaut", "c-cedilla", "s-cedilla", "g-breve"],
    )
    def test_diacritic_battery(self, nfc_char):
        """
        Issue #10 reproducer set: all five Turkish-phoneme inputs from
        the bug report must NFC<->NFD round-trip through the helper such
        that the precomposed and decomposed forms produce identical keys.

        Also confirms the helper actually emits NFD (the form FLEx
        stores), not NFC.
        """
        nfc = nfc_char
        nfd = unicodedata.normalize("NFD", nfc_char)

        # The two forms ARE different at the codepoint level.
        assert nfc != nfd, (
            f"Test setup: {nfc_char!r} does not have distinct NFC/NFD "
            f"forms; pick a different sentinel"
        )

        # ...but must compare equal after the helper.
        assert normalize_match_key(nfc) == normalize_match_key(nfd)

        # And the helper output must itself be NFD (it's what FLEx
        # stores; matching against an NFC needle would re-introduce the
        # bug on the other side).
        key = normalize_match_key(nfc, casefold=False)
        assert key == unicodedata.normalize("NFD", key), (
            f"Helper output for {nfc_char!r} is not NFD"
        )


class TestNormalizeMatchKeyWhitespaceIdentity:
    """
    Whitespace-identity coverage for `normalize_match_key`
    (GitHub #274 / spec `name-field-whitespace-identity`).

    THE C4 FENCE (owner decision, 2026-09-08 -- "Extend C4's inline fix").
    An earlier draft of this class asserted the REJECTED NF5 central-strip
    locus: that `normalize_match_key(" x ")` should itself return `"x"`.
    That plan is DEAD. The frozen contract C4
    (`specs/name-field-whitespace-identity/spec.md:250`) forbids adding
    `.strip()` to `normalize_match_key`, forbids a shared helper, and fences
    `Shared/string_utils.py` off entirely. The whitespace-insensitivity is
    achieved by an INLINE `.strip()` on BOTH sides at each comparison site
    -- `normalize_match_key(x, casefold=...).strip()` -- NOT inside the
    helper. These tests pin exactly that split: the helper DOES NOT strip,
    and the inline both-sides pattern IS whitespace-insensitive.

    All pure-Python; no live LCM required.
    """

    # ---- the helper deliberately does NOT strip (C4 fence) --------------

    def test_helper_does_not_strip_whitespace(self):
        """
        C4 (owner decision 2026-09-08): `normalize_match_key` must NOT strip
        edge whitespace. It applies normalize_text -> NFD -> optional
        casefold and nothing else, so a padded input keys to its own padded
        NFD/casefold form -- byte-for-byte, whitespace intact. This is what
        keeps `Shared/string_utils.py` untouched by #274.
        """
        assert normalize_match_key(" x ") == " x "
        assert normalize_match_key(" x ", casefold=False) == " x "
        assert normalize_match_key("\tx\r\n") == "\tx\r\n"
        assert normalize_match_key("   ") == "   "
        assert normalize_match_key("   ", casefold=False) == "   "

    def test_helper_does_not_collapse_padded_null_marker(self):
        """
        `normalize_text` maps ONLY the bare ``"***"`` to ``""`` by exact
        equality; a padded ``" *** "`` is not equal to ``"***"`` and so is
        preserved by the helper (no stripping inside it, per C4).
        """
        assert normalize_match_key(" *** ") == " *** "
        assert normalize_match_key("***") == ""

    # ---- the INLINE both-sides pattern IS whitespace-insensitive --------

    def test_inline_pattern_is_whitespace_insensitive(self):
        """
        The fix shape actually applied at the 7 bucket-A sites is
        `normalize_match_key(x, casefold=...).strip()` on BOTH needle and
        haystack. Under that pattern a padded value on EITHER side keys
        equal to the bare form, so a padded stored name is findable with an
        unpadded needle and vice versa.
        """
        def key(x, casefold=True):
            return normalize_match_key(x, casefold=casefold).strip()

        bare = key("x")
        assert key(" x ") == bare       # both
        assert key("x ") == bare        # trailing (haystack)
        assert key(" x") == bare        # leading  (needle)
        assert key("\tx\r\n") == bare
        assert key("x ") == key(" x")
        # case-sensitive sites (FilterOperations) behave the same way.
        assert key(" x ", casefold=False) == key("x", casefold=False)

    def test_inline_pattern_whitespace_only_reduces_to_empty(self):
        """
        A whitespace-only needle (``"   "`` / ``"\\t\\r\\n"``) reduces to
        ``""`` under the inline pattern -- which is exactly why the
        Find/Exists guards (``if not name or not name.strip(): return None``)
        reject it before it can degenerate into a promiscuous empty-key
        match.

        Note the C4-faithful non-collapse of the PADDED null marker: because
        `normalize_match_key` maps only the BARE ``"***"`` to ``""`` and does
        NOT strip (C4 fence), ``" *** "`` keys to ``"***"``, not ``""``. It
        is therefore a legitimate truthy needle that survives the guard
        (``"***".strip()`` is truthy) and matches an item literally named
        ``"***"`` -- it does NOT collapse into the empty-field bucket. Only
        genuine whitespace-only input reduces to the empty key.
        """
        def key(x):
            return normalize_match_key(x).strip()

        assert key("   ") == ""
        assert key("\t\r\n") == ""
        assert key(" *** ") == "***"          # padded marker != empty bucket
        assert key(" *** ") != key("***")     # bare marker DOES empty out


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
