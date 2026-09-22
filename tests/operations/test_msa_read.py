#
#   test_msa_read.py
#
#   Class: TestMSAGetAllPerEntry / TestMSAGetAllProjectWide /
#          TestMSAGetAllCollectionContract
#          Offline unit coverage for MSAOperations.GetAll -- reading
#          morpho-syntactic analyses without dropping to raw data-model
#          access.
#
#          This closes the last of the three read gaps left untested by
#          CP2a (parser-check R-08, FR-009), and it is the one with a
#          dependent: GetAll is the MORPH RESOLVER'S TERMINAL ACCESSOR.
#          CP2b's resolver turns a caller's headword-shaped decomposition
#          into MSA identifiers, and FR-019 says an unresolvable piece is
#          refused by name with no parse run. That refusal is only as
#          trustworthy as this read. Hence D-B8: this test lands BEFORE
#          the resolver is written.
#
#          WHAT IS AT RISK.
#
#          (1) THE COLLECTION CONTRACT. GetAll is deliberately NOT
#          decorated with @wrap_enumerable, unlike most GetAll methods in
#          this library. The reasoning in the docstring is that
#          MSACollection already supplies __len__, __getitem__ (including
#          slicing) and __iter__ through SmartCollection, so the decorator
#          would be an inert no-op that falsely implied the result needed
#          adapting. That reasoning is sound and it is also fragile: it
#          depends on a promise made by a DIFFERENT class. If MSACollection
#          ever loses one of those methods, the absent decorator stops
#          being a considered choice and becomes a bug, silently. So the
#          behavioral contract -- loop it, len() it, index it, slice it,
#          RE-ITERATE it -- is asserted here directly rather than inferred
#          from the decorator's absence.
#
#          Re-iteration is called out because it is the one a generator
#          would fail. A GetAll that returned a generator satisfies a
#          single `for` loop and nothing else, and the resolver iterates
#          its candidates more than once.
#
#          (2) THE EMPTY CASE. An entry owning no MSAs must yield an empty
#          collection, not None and not a raised error. The resolver's
#          `no_msa` outcome is a distinct, reportable state (FR-019 keeps
#          `none` / `ambiguous` / `no_msa` apart precisely so a caller can
#          tell whether to fix a spelling, pick a homograph, or conclude
#          the entry has no analysis). If this read raised or answered
#          None for the empty case, `no_msa` could not be distinguished
#          from a lookup failure.
#
#          (3) ORPHANS ARE NOT FILTERED. The docstring states GetAll
#          reports what the entry OWNS and does not filter MSAs that no
#          sense points at. That is load-bearing for the resolver: an MSA
#          reachable from the entry is a legitimate restriction target
#          even when no sense currently references it. A future "tidy-up"
#          that filtered orphans here would silently narrow the resolver's
#          candidate set, which is the exact class of silent narrowing
#          FR-023 forbids elsewhere.
#
#          These tests use plain Python stand-ins; no FieldWorks is
#          required and no project is opened.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import os
import sys


_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)

from flexicon.code.Lexicon.MSAOperations import MSAOperations


# ---------------------------------------------------------------------------
# Minimal LCM stand-ins -- no FieldWorks required
# ---------------------------------------------------------------------------


class _FakeMsa:
    """Stand-in for an IMoMorphSynAnalysis of one of the four subtypes."""

    def __init__(self, hvo, class_name="MoStemMsa"):
        self.Hvo = hvo
        self.ClassName = class_name
        self.ClassID = 5001

    def __repr__(self):  # pragma: no cover - diagnostic only
        return f"<_FakeMsa {self.ClassName} hvo={self.Hvo}>"


class _FakeEntry:
    """Stand-in for ILexEntry with an owning collection of MSAs."""

    ClassName = "LexEntry"

    def __init__(self, hvo=1, msas=()):
        self.Hvo = hvo
        self.MorphoSyntaxAnalysesOC = list(msas)


class _FakeProject:
    """Stand-in for the project's repository sweep."""

    def __init__(self, entries=()):
        self._entries = list(entries)
        self.objects_in_calls = []

    def ObjectsIn(self, repository):
        self.objects_in_calls.append(repository)
        return list(self._entries)


class _Ops(MSAOperations):
    """MSAOperations with entry resolution stubbed out."""

    def __init__(self, project=None, resolved_entry=None):
        self._project = project
        self._resolved_entry = resolved_entry
        self.resolve_calls = []

    @property
    def project(self):
        return self._project

    def _MSAOperations__ResolveEntry(self, entry_or_hvo):
        self.resolve_calls.append(entry_or_hvo)
        return self._resolved_entry


# ---------------------------------------------------------------------------


class TestMSAGetAllPerEntry:
    """Reading one entry's analyses -- the resolver's actual call shape."""

    def test_returns_every_msa_the_entry_owns(self):
        """FR-009: reachable without raw data-model access."""
        msas = [_FakeMsa(101), _FakeMsa(102, "MoDerivAffMsa")]
        entry = _FakeEntry(hvo=1, msas=msas)

        result = _Ops(resolved_entry=entry).GetAll(entry)

        assert len(result) == 2
        assert [m.Hvo for m in result] == [101, 102]

    def test_wraps_each_msa_rather_than_returning_raw_lcm_objects(self):
        """
        The point of the accessor: the caller never casts.

        Each item must be a MorphosyntaxAnalysis wrapper exposing the
        is_* / as_* / pos_* families, not the raw IMoMorphSynAnalysis.
        A caller forced to test ClassName is a caller still dropping to
        raw data-model access, which is what FR-009 exists to remove.
        """
        entry = _FakeEntry(hvo=1, msas=[_FakeMsa(101)])

        result = _Ops(resolved_entry=entry).GetAll(entry)

        first = result[0]
        assert type(first).__name__ == "MorphosyntaxAnalysis", (
            f"GetAll yielded {type(first).__name__}, not a "
            f"MorphosyntaxAnalysis wrapper. Returning raw LCM objects puts "
            f"the ClassName test and the cast back on the caller."
        )

    def test_resolves_the_entry_exactly_once(self):
        """One resolution per call."""
        entry = _FakeEntry(hvo=1, msas=[_FakeMsa(101)])
        ops = _Ops(resolved_entry=entry)

        ops.GetAll(entry)

        assert len(ops.resolve_calls) == 1

    def test_does_not_filter_orphaned_analyses(self):
        """
        GetAll reports what the entry OWNS.

        An MSA no sense points at is still owned and still a legitimate
        restriction target for the resolver. Filtering orphans here would
        silently narrow the candidate set -- the class of silent narrowing
        the parser-check requirements forbid elsewhere. RemoveOrphaned is
        the method for pruning; this one reports.
        """
        entry = _FakeEntry(hvo=1, msas=[_FakeMsa(101), _FakeMsa(999)])

        result = _Ops(resolved_entry=entry).GetAll(entry)

        assert len(result) == 2, (
            "GetAll dropped an analysis. It must report every MSA the "
            "entry owns, orphans included."
        )


class TestMSAGetAllProjectWide:
    """The None-argument sweep."""

    def test_none_sweeps_every_entry(self):
        """Project-wide read visits each entry and appends in turn."""
        project = _FakeProject(
            entries=[
                _FakeEntry(hvo=1, msas=[_FakeMsa(101)]),
                _FakeEntry(hvo=2, msas=[_FakeMsa(201), _FakeMsa(202)]),
            ]
        )

        result = _Ops(project=project).GetAll()

        assert len(result) == 3
        assert [m.Hvo for m in result] == [101, 201, 202]

    def test_project_wide_sweep_does_not_resolve_an_entry(self):
        """The None path must not go through entry resolution at all."""
        project = _FakeProject(entries=[_FakeEntry(hvo=1, msas=[_FakeMsa(101)])])
        ops = _Ops(project=project)

        ops.GetAll()

        assert ops.resolve_calls == []
        assert len(project.objects_in_calls) == 1

    def test_entry_owning_nothing_contributes_nothing(self):
        """An empty entry is skipped, not an error."""
        project = _FakeProject(
            entries=[
                _FakeEntry(hvo=1, msas=[]),
                _FakeEntry(hvo=2, msas=[_FakeMsa(201)]),
            ]
        )

        result = _Ops(project=project).GetAll()

        assert len(result) == 1
        assert result[0].Hvo == 201


class TestMSAGetAllCollectionContract:
    """
    The behavioral collection contract, asserted directly.

    GetAll is deliberately undecorated because MSACollection is claimed to
    already satisfy these. That claim is made by a different class and is
    pinned here so it cannot quietly stop being true.
    """

    def test_empty_entry_yields_an_empty_collection_not_none(self):
        """
        The `no_msa` outcome depends on this.

        FR-019 keeps `none` / `ambiguous` / `no_msa` distinct so a caller
        can tell whether to fix a spelling, pick a homograph, or conclude
        the entry has no analysis. If this read answered None or raised,
        `no_msa` would be indistinguishable from a lookup failure.
        """
        entry = _FakeEntry(hvo=1, msas=[])

        result = _Ops(resolved_entry=entry).GetAll(entry)

        assert result is not None, (
            "GetAll answered None for an entry owning no MSAs. The "
            "resolver's `no_msa` outcome cannot then be distinguished from "
            "a failed lookup."
        )
        assert len(result) == 0
        assert list(result) == []
        assert not result

    def test_supports_len_indexing_and_slicing(self):
        """The three SmartCollection promises the absent decorator relies on."""
        entry = _FakeEntry(hvo=1, msas=[_FakeMsa(101), _FakeMsa(102), _FakeMsa(103)])

        result = _Ops(resolved_entry=entry).GetAll(entry)

        assert len(result) == 3
        assert result[0].Hvo == 101
        assert [m.Hvo for m in result[1:]] == [102, 103]

    def test_is_re_iterable(self):
        """
        The promise a generator would break.

        The resolver walks its candidate set more than once. A GetAll that
        returned a generator would satisfy the first loop and silently
        yield nothing on the second -- producing an empty candidate set,
        which the resolver would report as an unresolvable morph. A wrong
        refusal is worse than a crash here, because it looks like an answer.
        """
        entry = _FakeEntry(hvo=1, msas=[_FakeMsa(101), _FakeMsa(102)])

        result = _Ops(resolved_entry=entry).GetAll(entry)

        first_pass = [m.Hvo for m in result]
        second_pass = [m.Hvo for m in result]

        assert first_pass == second_pass == [101, 102], (
            f"GetAll's result is not re-iterable: first pass {first_pass}, "
            f"second pass {second_pass}. A single-use iterator would make "
            f"the resolver report a spurious unresolvable morph."
        )
