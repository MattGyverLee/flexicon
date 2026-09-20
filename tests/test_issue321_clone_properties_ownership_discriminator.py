#
#   test_issue321_clone_properties_ownership_discriminator.py
#
#   Class: TestOwnershipSuffixDiscriminator / TestClonePropertiesBehaviour
#
#          Regression coverage for the ownership-suffix hardening of
#          `clone_properties` (issue #321, suspect 2).
#
#   Bug class:
#     `clone_properties` (lcm_casting.py) decided "this attribute is a
#     mutable collection I should Clear()+clone" purely by duck-typing:
#     `hasattr(attr_value, "Count") and hasattr(attr_value, "Add")`.
#
#     Live testing on a Sena 3 sandbox copy (see
#     specs/318-321-nonexistent-member-mutations/evidence/
#     live-321-derived-lists.md) proved that six DERIVED, rebuilt-per-access
#     ILexEntry/ICmObject members -- AllSenses, MorphTypes, PublishIn,
#     ShowMainEntryIn, MinimalLexReferences, ReferringObjects -- also
#     satisfy that predicate. Calling `.Clear()` on any of them "succeeds"
#     (raises nothing) yet leaves Count unchanged on a fresh re-fetch: the
#     #317 silent-no-op failure class, now proven on the clone_properties
#     code path itself. A genuine owned collection (EtymologyOS) cleared
#     and stayed cleared under the identical probe.
#
#   The fix keys the collection-clone branch on the LCM ownership-suffix
#   naming convention (OS/OC/OA owned, RS/RC/RA reference) IN ADDITION TO
#   the existing Count/Add check, so derived/computed members are
#   structurally excluded rather than accidentally duck-typed in.
#
#   These tests lock the PATTERN (the discriminator itself), not just one
#   instance, and include a regression assertion that is proven, in a code
#   comment, to fail against the pre-fix duck-typed predicate.
#
#   Platform: Python (pure Python fakes -- no live FieldWorks project is
#             opened; ClassName is deliberately unrecognised so
#             cast_to_concrete() is a no-op passthrough).
#
#   Copyright 2026
#

import pytest

from flexicon.code import lcm_casting
from flexicon.code.lcm_casting import clone_properties


# The six members proven live (see module docstring) to be derived/
# rebuilt-per-access, where .Clear() is a silent no-op.
DERIVED_NOOP_MEMBERS = [
    "AllSenses",
    "MorphTypes",
    "PublishIn",
    "ShowMainEntryIn",
    "MinimalLexReferences",
    "ReferringObjects",
]

# A genuine owned collection (OS suffix), confirmed live to clear and stay
# cleared.
OWNED_MEMBER = "EtymologyOS"

# A genuine reference collection (RS suffix) that matched the predicate
# both before and after this fix -- the hardening must NOT narrow this away
# (mandatory safety constraint: don't drop legitimate OS/OC/RS/RC members).
REFERENCE_MEMBER = "DialectLabelsRS"


class FakeCollection:
    """Stands in for an LCM `ILcmOwningSequence`/`ILcmReferenceSequence`.

    Exposes exactly the duck-typed surface (`Count`, `Add`) the old
    predicate checked, plus `Clear()`/iteration, so it satisfies the OLD
    predicate regardless of whether the member is genuinely owned.
    """

    def __init__(self, items=None):
        self.items = list(items) if items else []
        self.clear_calls = 0
        self.added = []

    @property
    def Count(self):
        return len(self.items)

    def Add(self, item):
        self.added.append(item)
        self.items.append(item)

    def Clear(self):
        self.clear_calls += 1
        self.items = []

    def __iter__(self):
        return iter(list(self.items))


class FakeLexEntry:
    """Minimal stand-in for a cast ILexEntry.

    `ClassName` is deliberately not a real LCM class name, so
    `cast_to_concrete()` (called at the top of `clone_properties`) returns
    this object unchanged -- no SIL.LCModel interface lookup is required
    to reach the code path under test.
    """

    ClassName = "NotARealLcmClass_Issue321"

    def __init__(self):
        for name in DERIVED_NOOP_MEMBERS:
            setattr(self, name, FakeCollection())
        setattr(self, OWNED_MEMBER, FakeCollection())
        setattr(self, REFERENCE_MEMBER, FakeCollection())
        self.Hvo = 1
        self.Guid = "fake-guid-321"


def old_duck_typed_predicate(attr_value):
    """The exact pre-fix predicate, kept here only to demonstrate the gap.

    `lcm_casting.clone_properties` no longer contains this expression --
    it now also requires `attr_name.endswith(_OWNED_OR_REFERENCE_SUFFIXES)`.
    """
    return hasattr(attr_value, "Count") and hasattr(attr_value, "Add")


class TestOwnershipSuffixDiscriminator:
    """Static comparison of old vs. new member-matching, per the live
    evidence's before/after table."""

    def test_old_predicate_matched_all_derived_members_too(self):
        """Sanity-check the bug: the OLD predicate does not discriminate.

        FakeCollection satisfies Count/Add for every member below,
        including the six proven-derived ones -- exactly reproducing the
        duck-typing gap the live evidence found.
        """
        entry = FakeLexEntry()
        for name in DERIVED_NOOP_MEMBERS + [OWNED_MEMBER, REFERENCE_MEMBER]:
            assert old_duck_typed_predicate(getattr(entry, name)) is True

    def test_new_discriminator_excludes_only_the_derived_members(self):
        """The NEW suffix gate excludes exactly the six derived members
        and nothing else -- the mandatory "no narrowing" comparison."""
        for name in DERIVED_NOOP_MEMBERS:
            assert not name.endswith(lcm_casting._OWNED_OR_REFERENCE_SUFFIXES), (
                f"{name} unexpectedly classified as owned/reference"
            )
        assert OWNED_MEMBER.endswith(lcm_casting._OWNED_OR_REFERENCE_SUFFIXES)
        assert REFERENCE_MEMBER.endswith(lcm_casting._OWNED_OR_REFERENCE_SUFFIXES)


class TestClonePropertiesBehaviour:
    """Effect-level assertions on the real `clone_properties` function."""

    def test_derived_members_are_not_cleared_or_touched(self):
        """AllSenses/MorphTypes/PublishIn/ShowMainEntryIn/
        MinimalLexReferences/ReferringObjects must NOT be routed through
        the Clear()+Add() collection-clone branch.

        REGRESSION: this assertion fails against the pre-fix duck-typed
        predicate. Under the old code, `hasattr(attr_value, "Count") and
        hasattr(attr_value, "Add")` is True for every FakeCollection here
        (see test_old_predicate_matched_all_derived_members_too), so
        `dest_collection.Clear()` would have been called on each of these
        members, making `clear_calls == 1` instead of the `== 0` asserted
        below. The `assert getattr(dest, name).clear_calls == 0` line is
        the one that catches a regression back to the old predicate.
        """
        source = FakeLexEntry()
        dest = FakeLexEntry()

        clone_properties(source, dest, project=None)

        for name in DERIVED_NOOP_MEMBERS:
            dest_member = getattr(dest, name)
            assert dest_member.clear_calls == 0, (
                f"{name} was routed through the collection-clone branch; "
                "the ownership-suffix gate should have excluded it"
            )
            assert dest_member.added == []

    def test_owned_collection_is_still_cleared_and_cloned(self):
        """A genuine OS member (EtymologyOS) must still go through the
        existing Clear()+Add() path -- the mandatory "no narrowing" check
        at the behavioural level."""
        source = FakeLexEntry()
        dest = FakeLexEntry()

        clone_properties(source, dest, project=None)

        assert getattr(dest, OWNED_MEMBER).clear_calls == 1

    def test_reference_collection_member_is_still_cleared(self):
        """A genuine RS member (DialectLabelsRS) is unchanged by this fix:
        it matched the predicate before and still matches it now, so the
        hardening does not narrow this legitimate case away."""
        source = FakeLexEntry()
        dest = FakeLexEntry()

        clone_properties(source, dest, project=None)

        assert getattr(dest, REFERENCE_MEMBER).clear_calls == 1
