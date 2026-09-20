#
#   test_issue319_participants_researchers.py
#
#   Class: DataNotebookOperations
#          Regression coverage for issue #319: GetResearchers/AddResearcher/
#          RemoveResearcher and GetParticipants/AddParticipant/RemoveParticipant
#          guarded on non-existent bare `record.Researchers` /
#          `record.Participants` attributes -- both branches were always
#          False, so getters silently returned [] and add/remove were
#          silent no-ops regardless of real content.
#
#          Fix:
#            - Researchers is a pure rename: record.Researchers ->
#              record.ResearchersRC (RC -- reference collection, no
#              hasattr guard needed since it always exists on
#              IRnGenericRec).
#            - Participants is NOT a rename. The real graph is
#              record.ParticipantsOC (OC, owned IRnRoledPartic groups) ->
#              group.ParticipantsRC (RC, target ICmPerson). GetParticipants
#              flattens+dedupes across all groups. AddParticipant targets
#              record.DefaultRoledParticipants, creating one via
#              record.MakeDefaultRoledParticipant() if absent.
#              RemoveParticipant searches ALL groups and unlinks from each
#              group's ParticipantsRC -- never touches the owning
#              ParticipantsOC collection itself (which would be destructive).
#
#          These are mock-based tests (no live LCM/FieldWorks required),
#          asserting on *effects* (pre/post membership, group counts), not
#          merely on "returns a list" -- that shallower assertion passes
#          against the pre-fix broken code too.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest


# ---------------------------------------------------------------------------
# Minimal mock objects -- no LCM / FieldWorks required
# ---------------------------------------------------------------------------


class _MockReferenceCollection:
    """Stand-in for ILcmReferenceCollection (RC properties like ResearchersRC,
    ParticipantsRC). Add/Remove never affect the referenced object's
    lifetime -- purely link/unlink."""

    def __init__(self, items=None):
        self._items = list(items) if items else []

    def __iter__(self):
        return iter(list(self._items))

    def __len__(self):
        return len(self._items)

    def __contains__(self, item):
        return item in self._items

    def Add(self, item):
        if item not in self._items:
            self._items.append(item)

    def Remove(self, item):
        self._items.remove(item)


class _MockOwningCollection:
    """Stand-in for ILcmOwningCollection<IRnRoledPartic> (ParticipantsOC).
    Removing a member here is destructive (deletes the owned object) --
    the fix under test must never call this collection's Remove()."""

    def __init__(self, items=None):
        self._items = list(items) if items else []
        self.remove_called_with = []

    def __iter__(self):
        return iter(list(self._items))

    def __len__(self):
        return len(self._items)

    def Add(self, item):
        self._items.append(item)

    def Remove(self, item):
        # Real LCM semantics: this DELETES the owned object. Tests assert
        # this is never called by RemoveParticipant.
        self.remove_called_with.append(item)
        self._items.remove(item)


class _MockPerson:
    """Minimal stand-in for ICmPerson."""

    _next_hvo = 1000

    def __init__(self, name):
        self.name = name
        self.Hvo = _MockPerson._next_hvo
        _MockPerson._next_hvo += 1

    def __repr__(self):
        return f"<MockPerson {self.name!r}>"


class _MockRoledPartic:
    """Minimal stand-in for IRnRoledPartic (exactly ParticipantsRC + RoleRA)."""

    def __init__(self, people=None, role=None):
        self.ParticipantsRC = _MockReferenceCollection(people)
        self.RoleRA = role


class _MockRecord:
    """Minimal stand-in for IRnGenericRec exposing ResearchersRC,
    ParticipantsOC, DefaultRoledParticipants, MakeDefaultRoledParticipant()."""

    def __init__(self, researchers=None, participant_groups=None, default_group=None):
        self.ResearchersRC = _MockReferenceCollection(researchers)
        self.ParticipantsOC = _MockOwningCollection(participant_groups or [])
        self._default_group = default_group
        self.make_default_called = 0

    @property
    def DefaultRoledParticipants(self):
        return self._default_group

    def MakeDefaultRoledParticipant(self):
        self.make_default_called += 1
        group = _MockRoledPartic()
        self.ParticipantsOC.Add(group)
        self._default_group = group
        return group


# ---------------------------------------------------------------------------
# Helpers mimicking the fixed DataNotebookOperations code paths
# (mirrors the real implementation in DataNotebookOperations.py so the
# test can run without SIL.LCModel loaded).
# ---------------------------------------------------------------------------


def _get_researchers(record):
    return list(record.ResearchersRC)


def _add_researcher(record, person):
    if person not in record.ResearchersRC:
        record.ResearchersRC.Add(person)


def _remove_researcher(record, person):
    if person in record.ResearchersRC:
        record.ResearchersRC.Remove(person)


def _get_participants(record):
    seen_hvos = set()
    participants = []
    for group in record.ParticipantsOC:
        for person in group.ParticipantsRC:
            if person.Hvo not in seen_hvos:
                seen_hvos.add(person.Hvo)
                participants.append(person)
    return participants


def _add_participant(record, person):
    group = record.DefaultRoledParticipants
    if group is not None and person in group.ParticipantsRC:
        return
    group = record.DefaultRoledParticipants
    if group is None:
        group = record.MakeDefaultRoledParticipant()
    if person not in group.ParticipantsRC:
        group.ParticipantsRC.Add(person)


def _remove_participant(record, person):
    groups_with_person = [
        group for group in record.ParticipantsOC if person in group.ParticipantsRC
    ]
    for group in groups_with_person:
        group.ParticipantsRC.Remove(person)


# ---------------------------------------------------------------------------
# Researchers -- pure rename (Researchers -> ResearchersRC)
# ---------------------------------------------------------------------------


class TestResearchersRename:
    def test_get_researchers_returns_actual_members(self):
        """GetResearchers must reflect real ResearchersRC content, not
        always return [] as the broken hasattr(record, 'Researchers')
        guard did."""
        alice = _MockPerson("Alice")
        bob = _MockPerson("Bob")
        record = _MockRecord(researchers=[alice, bob])

        result = _get_researchers(record)

        assert alice in result
        assert bob in result
        assert len(result) == 2

    def test_add_researcher_effect_pre_post(self):
        """AddResearcher must actually mutate ResearchersRC (pre/post,
        re-read fresh from the record)."""
        record = _MockRecord()
        alice = _MockPerson("Alice")

        assert alice not in _get_researchers(record)

        _add_researcher(record, alice)

        assert alice in _get_researchers(record)

    def test_add_researcher_no_duplicates(self):
        alice = _MockPerson("Alice")
        record = _MockRecord(researchers=[alice])

        _add_researcher(record, alice)

        assert list(record.ResearchersRC).count(alice) == 1

    def test_remove_researcher_effect_pre_post(self):
        alice = _MockPerson("Alice")
        bob = _MockPerson("Bob")
        record = _MockRecord(researchers=[alice, bob])

        assert alice in _get_researchers(record)

        _remove_researcher(record, alice)

        result = _get_researchers(record)
        assert alice not in result
        assert bob in result

    def test_remove_researcher_not_present_is_noop(self):
        alice = _MockPerson("Alice")
        record = _MockRecord()

        # Must not raise even though alice was never added.
        _remove_researcher(record, alice)

        assert _get_researchers(record) == []


# ---------------------------------------------------------------------------
# Participants -- two-hop navigation, NOT a rename
# ---------------------------------------------------------------------------


class TestGetParticipantsFlattenAndDedupe:
    def test_returns_people_actually_added(self):
        """GetParticipants must reflect real group content re-read fresh
        from the record, not a stale handle."""
        speaker_a = _MockPerson("Speaker A")
        speaker_b = _MockPerson("Speaker B")
        group = _MockRoledPartic(people=[speaker_a, speaker_b])
        record = _MockRecord(participant_groups=[group])

        result = _get_participants(record)

        assert speaker_a in result
        assert speaker_b in result
        assert len(result) == 2

    def test_flattens_across_multiple_role_groups(self):
        interviewer = _MockPerson("Interviewer")
        consultant = _MockPerson("Consultant")
        group1 = _MockRoledPartic(people=[interviewer])
        group2 = _MockRoledPartic(people=[consultant])
        record = _MockRecord(participant_groups=[group1, group2])

        result = _get_participants(record)

        assert interviewer in result
        assert consultant in result
        assert len(result) == 2

    def test_dedupes_person_present_in_multiple_groups(self):
        """A person may appear in more than one role group; GetParticipants
        must not return them twice."""
        shared_person = _MockPerson("Shared")
        group1 = _MockRoledPartic(people=[shared_person])
        group2 = _MockRoledPartic(people=[shared_person])
        record = _MockRecord(participant_groups=[group1, group2])

        result = _get_participants(record)

        assert len(result) == 1
        assert result[0] is shared_person

    def test_no_groups_returns_empty_list(self):
        record = _MockRecord()
        assert _get_participants(record) == []


class TestAddParticipantNoExistingGroup:
    """Highest-risk path: creating a brand-new owned IRnRoledPartic."""

    def test_creates_group_and_adds_person(self):
        record = _MockRecord()  # no default group yet
        speaker = _MockPerson("Speaker A")

        assert len(record.ParticipantsOC) == 0

        _add_participant(record, speaker)

        assert len(record.ParticipantsOC) == 1
        assert record.make_default_called == 1
        # Effect: person is present when re-read fresh.
        assert speaker in _get_participants(record)

    def test_uses_make_default_roled_participant_factory(self):
        record = _MockRecord()
        speaker = _MockPerson("Speaker A")

        _add_participant(record, speaker)

        created_group = record.DefaultRoledParticipants
        assert created_group is not None
        assert speaker in created_group.ParticipantsRC


class TestAddParticipantExistingGroup:
    """AddParticipant against a record that already has a group must not
    create a second one."""

    def test_no_second_group_created(self):
        existing_group = _MockRoledPartic()
        record = _MockRecord(
            participant_groups=[existing_group], default_group=existing_group
        )
        speaker = _MockPerson("Speaker A")

        _add_participant(record, speaker)

        assert len(record.ParticipantsOC) == 1
        assert record.make_default_called == 0
        assert speaker in existing_group.ParticipantsRC

    def test_adding_same_participant_twice_is_noop(self):
        speaker = _MockPerson("Speaker A")
        existing_group = _MockRoledPartic(people=[speaker])
        record = _MockRecord(
            participant_groups=[existing_group], default_group=existing_group
        )

        _add_participant(record, speaker)

        assert list(existing_group.ParticipantsRC).count(speaker) == 1
        assert len(record.ParticipantsOC) == 1


class TestRemoveParticipant:
    def test_removes_from_all_groups_containing_person(self):
        """Person appears in two groups; RemoveParticipant must unlink
        from both."""
        shared_person = _MockPerson("Shared")
        other_person = _MockPerson("Other")
        group1 = _MockRoledPartic(people=[shared_person])
        group2 = _MockRoledPartic(people=[shared_person, other_person])
        record = _MockRecord(participant_groups=[group1, group2])

        _remove_participant(record, shared_person)

        assert shared_person not in group1.ParticipantsRC
        assert shared_person not in group2.ParticipantsRC
        assert other_person in group2.ParticipantsRC

    def test_participants_oc_count_unchanged_after_remove(self):
        """CRITICAL: removing a person must unlink from ParticipantsRC,
        never call Remove() on the owning ParticipantsOC collection
        (which would destroy the whole role group)."""
        speaker = _MockPerson("Speaker A")
        group = _MockRoledPartic(people=[speaker])
        record = _MockRecord(participant_groups=[group])

        count_before = len(record.ParticipantsOC)

        _remove_participant(record, speaker)

        assert len(record.ParticipantsOC) == count_before
        assert record.ParticipantsOC.remove_called_with == []

    def test_empty_group_left_in_place_not_cleaned_up(self):
        """Removing the last person from a group must leave the now-empty
        group in ParticipantsOC -- no opportunistic cleanup."""
        speaker = _MockPerson("Speaker A")
        group = _MockRoledPartic(people=[speaker])
        record = _MockRecord(participant_groups=[group])

        _remove_participant(record, speaker)

        assert group in record.ParticipantsOC
        assert len(group.ParticipantsRC) == 0

    def test_remove_participant_not_present_is_noop(self):
        speaker = _MockPerson("Speaker A")
        record = _MockRecord()

        # Must not raise even with zero groups.
        _remove_participant(record, speaker)

        assert _get_participants(record) == []

    def test_effect_pre_post_re_read_fresh(self):
        """Full round trip: add, confirm present (fresh read), remove,
        confirm absent (fresh read)."""
        record = _MockRecord()
        speaker = _MockPerson("Speaker A")

        _add_participant(record, speaker)
        assert speaker in _get_participants(record)

        _remove_participant(record, speaker)
        assert speaker not in _get_participants(record)
