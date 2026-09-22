#
#   test_text_genres.py
#
#   Class: TestTextGetGenres / TestTextGetGenresEmptyContract
#          Offline unit coverage for TextOperations.GetGenres -- the
#          "read ALL genres, not just the first" accessor.
#
#          This closes one of the three read gaps left untested by CP2a
#          (parser-check R-08, FR-007). The method shipped with CP2a and
#          had no test anywhere in either repository. It is a precondition
#          of CP2b's morph resolver work, and it is being tested now rather
#          than later because a refusal is only as trustworthy as the
#          accessor underneath it.
#
#          WHAT IS ACTUALLY AT RISK HERE. GetGenres reads GenresRC, an
#          ILcmReferenceCollection, and returns `list(...)` of it. The
#          singular GetGenre reads only the first and is deliberately left
#          alone. So the defect this file exists to catch is the easy one:
#          a future "simplification" that routes GetGenres back through
#          GetGenre, or that returns the raw C# collection instead of a
#          materialized list, or that answers None for the empty case.
#
#          THE EMPTY CONTRACT IS THE POINT. The docstring promises an
#          empty list and states "never None", so `if not genres:` is the
#          documented empty check and there is no None branch to handle.
#          That promise is load-bearing for callers and is pinned here
#          explicitly -- an accessor that answered None would satisfy a
#          careless `if not genres:` test while breaking every caller that
#          does `len(genres)` or iterates.
#
#          ORDER IS DELIBERATELY NOT ASSERTED. GenresRC is a reference
#          COLLECTION, which carries no positional guarantee the way a
#          reference sequence does. The docstring says so. Asserting an
#          order here would pin behavior the data model does not promise
#          and would make this file fail for a correct reason it could not
#          act on, so membership is asserted as a set.
#
#          NO SOURCE-INTROSPECTION GUARDS HERE, DELIBERATELY. An earlier
#          draft asserted over inspect.getsource(GetGenres) to pin that
#          it reads GenresRC and does not delegate to GetGenre. Both
#          claims are already covered behaviorally -- delegation to the
#          singular accessor fails the two-genre test, and reading any
#          other property fails against the stand-in, which has none.
#          The introspection added nothing and was brittle: GetGenres is
#          decorated with @wrap_enumerable, which does not use
#          functools.wraps, so getsource() returns the decorator body and
#          inspect.unwrap() cannot follow it. A guard that goes red for a
#          reason it is not about is a guard that gets deleted.
#
#          These tests use plain Python stand-ins; no FieldWorks is
#          required and no project is opened.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import inspect
import os
import sys


_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.TextsWords.TextOperations import TextOperations


# ---------------------------------------------------------------------------
# Minimal LCM stand-ins -- no FieldWorks required
# ---------------------------------------------------------------------------


class _FakeGenre:
    """Stand-in for an ICmPossibility in the 'Text Genres' list."""

    ClassName = "CmPossibility"

    def __init__(self, hvo, name):
        self.Hvo = hvo
        self.Name = name

    def __repr__(self):  # pragma: no cover - diagnostic only
        return f"<_FakeGenre {self.Name}>"


class _FakeReferenceCollection:
    """
    Stand-in for ILcmReferenceCollection.

    Deliberately iterable-but-not-a-list: it supports iteration and len()
    the way the CLR collection does, but it is NOT a Python list. That is
    what makes `test_returns_a_real_list_not_the_raw_collection` meaningful
    -- if GetGenres ever stopped materializing, the return value would be
    this object and the assertion would catch it.
    """

    def __init__(self, items):
        self._items = list(items)

    def __iter__(self):
        return iter(self._items)

    def __len__(self):
        return len(self._items)


class _FakeText:
    """Stand-in for IText."""

    ClassName = "Text"

    def __init__(self, hvo=1, genres=()):
        self.Hvo = hvo
        self.GenresRC = _FakeReferenceCollection(genres)


class _Ops(TextOperations):
    """
    TextOperations with object resolution stubbed out.

    GetGenres' only collaborator is the private __GetTextObject resolver,
    which is what turns an IText-or-HVO into an IText. Replacing it keeps
    these tests on GetGenres' own behavior rather than on resolution, which
    has its own coverage elsewhere.
    """

    def __init__(self, text):
        self._text = text

    # Name-mangled to match the private resolver GetGenres calls.
    def _TextOperations__GetTextObject(self, text_or_hvo):
        if text_or_hvo is None:
            raise AssertionError(
                "GetGenres passed None through to the resolver; the null "
                "guard is the resolver's job and must not be bypassed."
            )
        return self._text


# ---------------------------------------------------------------------------


class TestTextGetGenres:
    """The plural read -- every genre, not only the first."""

    def test_returns_every_genre_not_only_the_first(self):
        """The whole reason this accessor exists (FR-007)."""
        narrative = _FakeGenre(11, "Narrative")
        procedural = _FakeGenre(12, "Procedural")
        text = _FakeText(genres=[narrative, procedural])

        genres = _Ops(text).GetGenres(text)

        assert len(genres) == 2, (
            f"GetGenres reported {len(genres)} genre(s) for a text carrying "
            f"two. Reporting only the first is exactly the defect FR-007 "
            f"exists to fix -- GetGenre is the singular accessor and is "
            f"deliberately unchanged."
        )
        # Membership, not order: GenresRC is a reference COLLECTION and
        # carries no positional guarantee (see module header).
        assert {g.Name for g in genres} == {"Narrative", "Procedural"}

    def test_single_genre_still_reads_as_a_one_item_list(self):
        """The common case must not be special-cased into a bare object."""
        text = _FakeText(genres=[_FakeGenre(11, "Narrative")])

        genres = _Ops(text).GetGenres(text)

        assert isinstance(genres, list)
        assert len(genres) == 1
        assert genres[0].Name == "Narrative"

    def test_returns_a_real_list_not_the_raw_collection(self):
        """
        The return value must be materialized.

        A raw ILcmReferenceCollection is a live view: it has no stable
        indexing contract in Python, and the docstring promises a snapshot
        taken at call time. `list(...)` is what delivers that promise.
        """
        text = _FakeText(genres=[_FakeGenre(11, "Narrative")])

        genres = _Ops(text).GetGenres(text)

        assert type(genres) is list, (
            f"GetGenres returned {type(genres).__name__}, not a list. The "
            f"documented contract is a materialized snapshot; returning the "
            f"raw reference collection would make a later SetGenre mutate a "
            f"list the caller already holds."
        )

    def test_result_is_a_snapshot_unaffected_by_later_mutation(self):
        """A later change to the collection must not alter a returned list."""
        text = _FakeText(genres=[_FakeGenre(11, "Narrative")])

        genres = _Ops(text).GetGenres(text)
        text.GenresRC._items.append(_FakeGenre(12, "Procedural"))

        assert len(genres) == 1, (
            "The list returned by GetGenres changed when the underlying "
            "collection changed. The docstring promises a snapshot taken at "
            "call time."
        )


class TestTextGetGenresEmptyContract:
    """The empty case, which the docstring makes a hard promise about."""

    def test_no_genre_assigned_returns_empty_list_never_none(self):
        """
        `if not genres:` must be the whole empty check.

        An accessor that answered None here would still satisfy a careless
        `if not genres:` assertion while breaking every caller that calls
        len() or iterates. So None is ruled out explicitly, ahead of the
        emptiness assertion.
        """
        text = _FakeText(genres=[])

        genres = _Ops(text).GetGenres(text)

        assert genres is not None, (
            "GetGenres answered None for a text with no genre. The "
            "documented contract is an empty list and 'never None' -- there "
            "is no None branch for callers to handle, and introducing one "
            "silently breaks len()/iteration at every call site."
        )
        assert isinstance(genres, list)
        assert genres == []
        assert not genres  # the documented empty check

    def test_empty_result_supports_len_and_iteration(self):
        """The two operations a None return would break."""
        text = _FakeText(genres=[])

        genres = _Ops(text).GetGenres(text)

        assert len(genres) == 0
        assert list(genres) == []
