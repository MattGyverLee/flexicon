#
#   test_pos_duplicate.py
#
#   Class: TestPOSDuplicateSubPossibilitiesOS,
#          TestPOSDuplicateTopLevelPossibilitiesOS,
#          TestPOSDuplicateDeepSubcategories
#
#          Regression coverage for issue #295 / #163:
#          POSOperations.Duplicate is the last library call site that
#          legitimately uses IndexOf() + Insert() on an owning **sequence**
#          (SubPossibilitiesOS / PossibilitiesOS). OC siblings must use Add()
#          only; this file pins that POS keeps meaningful insert_after on OS.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

# ---------------------------------------------------------------------------
# Minimal mock objects -- no LCM / FieldWorks required
# ---------------------------------------------------------------------------


class _MockOS:
    """
    Stand-in for ILcmOwningSequence<IPartOfSpeech> (SubPossibilitiesOS or
    PossibilitiesOS). Ordered sequences support IndexOf and Insert (#163).
    """

    def __init__(self, items=None):
        self._items = list(items) if items else []
        self.insert_calls = []
        self.add_calls = []

    def __iter__(self):
        return iter(list(self._items))

    def __len__(self):
        return len(self._items)

    @property
    def Count(self):
        return len(self._items)

    def Add(self, obj):
        self.add_calls.append(obj)
        self._items.append(obj)

    def IndexOf(self, obj):
        return self._items.index(obj)

    def Insert(self, index, obj):
        self.insert_calls.append((index, obj))
        self._items.insert(index, obj)


class _MockPOS:
    """Minimal stand-in for IPartOfSpeech."""

    def __init__(self, name, sub_possibilities=None, owner=None):
        self.name = name
        self.SubPossibilitiesOS = _MockOS(sub_possibilities or [])
        self.Owner = owner
        self.Name = name
        self.Abbreviation = None
        self.Description = None
        self.CatalogSourceId = None

    def __repr__(self):
        return f"<MockPOS {self.name!r}>"


class _MockPartsOfSpeechOA:
    def __init__(self, top_level=None):
        self.PossibilitiesOS = _MockOS(top_level or [])


class _MockLangProject:
    def __init__(self, top_level=None):
        self.PartsOfSpeechOA = _MockPartsOfSpeechOA(top_level)


# ---------------------------------------------------------------------------
# Helpers mirroring placement logic in POSOperations.Duplicate
# ---------------------------------------------------------------------------


def _simulate_subcategory_duplicate(source, parent, duplicate, insert_after):
    """
    Subcategory branch: parent_pos.SubPossibilitiesOS is OS -- Insert is valid
    when insert_after=True (#163 contrast with OC siblings).
    """
    if insert_after:
        source_index = parent.SubPossibilitiesOS.IndexOf(source)
        parent.SubPossibilitiesOS.Insert(source_index + 1, duplicate)
    else:
        parent.SubPossibilitiesOS.Add(duplicate)


def _simulate_top_level_duplicate(source, pos_list, duplicate, insert_after):
    """Top-level branch uses PartsOfSpeechOA.PossibilitiesOS (also OS)."""
    if insert_after:
        source_index = pos_list.PossibilitiesOS.IndexOf(source)
        pos_list.PossibilitiesOS.Insert(source_index + 1, duplicate)
    else:
        pos_list.PossibilitiesOS.Add(duplicate)


def _simulate_deep_duplicate_subcategories(source, parent_duplicate, created):
    """
    Mirrors __DuplicateSubcategory: each source sub is appended to the
    duplicate parent's SubPossibilitiesOS, then nested subs recurse.
    """

    def _dup_one(source_sub, parent_dup):
        sub_duplicate = _MockPOS(source_sub.name + "_copy")
        created.append(sub_duplicate)
        parent_dup.SubPossibilitiesOS.Add(sub_duplicate)
        if source_sub.SubPossibilitiesOS.Count > 0:
            for nested in source_sub.SubPossibilitiesOS:
                _dup_one(nested, sub_duplicate)

    for sub in source.SubPossibilitiesOS:
        _dup_one(sub, parent_duplicate)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


class TestPOSDuplicateSubPossibilitiesOS:
    """Subcategory path: SubPossibilitiesOS is OS; insert_after is meaningful."""

    def test_insert_after_uses_insert_at_source_index_plus_one(self):
        parent = _MockPOS("Noun")
        noun = _MockPOS("Common Noun", owner=parent)
        parent.SubPossibilitiesOS.Add(noun)
        proper = _MockPOS("Proper Noun", owner=parent)
        parent.SubPossibilitiesOS.Add(proper)

        duplicate = _MockPOS("Common Noun_copy")
        _simulate_subcategory_duplicate(noun, parent, duplicate, insert_after=True)

        assert parent.SubPossibilitiesOS.insert_calls == [(1, duplicate)]
        assert list(parent.SubPossibilitiesOS) == [noun, duplicate, proper]

    def test_insert_after_false_appends_via_add(self):
        parent = _MockPOS("Verb")
        verb = _MockPOS("Intransitive", owner=parent)
        parent.SubPossibilitiesOS.Add(verb)
        duplicate = _MockPOS("Intransitive_copy")

        _simulate_subcategory_duplicate(verb, parent, duplicate, insert_after=False)

        assert parent.SubPossibilitiesOS.add_calls == [verb, duplicate]
        assert parent.SubPossibilitiesOS.insert_calls == []
        assert list(parent.SubPossibilitiesOS) == [verb, duplicate]


class TestPOSDuplicateTopLevelPossibilitiesOS:
    """Top-level POS uses PossibilitiesOS on PartsOfSpeechOA (OS, not OC)."""

    def test_top_level_insert_after_uses_possibilities_os_insert(self):
        lp = _MockLangProject()
        noun = _MockPOS("Noun")
        verb = _MockPOS("Verb")
        lp.PartsOfSpeechOA.PossibilitiesOS.Add(noun)
        lp.PartsOfSpeechOA.PossibilitiesOS.Add(verb)

        duplicate = _MockPOS("Noun_copy")
        _simulate_top_level_duplicate(
            noun, lp.PartsOfSpeechOA, duplicate, insert_after=True
        )

        assert lp.PartsOfSpeechOA.PossibilitiesOS.insert_calls == [(1, duplicate)]
        assert list(lp.PartsOfSpeechOA.PossibilitiesOS) == [noun, duplicate, verb]

    def test_top_level_insert_after_false_appends_via_add(self):
        lp = _MockLangProject([_MockPOS("Adjective")])
        source = lp.PartsOfSpeechOA.PossibilitiesOS._items[0]
        duplicate = _MockPOS("Adjective_copy")

        _simulate_top_level_duplicate(
            source, lp.PartsOfSpeechOA, duplicate, insert_after=False
        )

        assert lp.PartsOfSpeechOA.PossibilitiesOS.add_calls[-1] is duplicate
        assert lp.PartsOfSpeechOA.PossibilitiesOS.insert_calls == []


class TestPOSDuplicateDeepSubcategories:
    """deep=True recurses SubPossibilitiesOS hierarchy via Add on each level."""

    def test_deep_recursion_duplicates_nested_subpossibilities(self):
        root = _MockPOS("Verb")
        trans = _MockPOS("Transitive", owner=root)
        ditrans = _MockPOS("Ditransitive", owner=trans)
        trans.SubPossibilitiesOS.Add(ditrans)
        root.SubPossibilitiesOS.Add(trans)

        root_copy = _MockPOS("Verb_copy")
        created = []
        _simulate_deep_duplicate_subcategories(root, root_copy, created)

        assert len(created) == 2
        assert {c.name for c in created} == {"Transitive_copy", "Ditransitive_copy"}
        assert len(root_copy.SubPossibilitiesOS) == 1
        trans_copy = root_copy.SubPossibilitiesOS._items[0]
        assert trans_copy.name == "Transitive_copy"
        assert len(trans_copy.SubPossibilitiesOS) == 1
        assert trans_copy.SubPossibilitiesOS._items[0].name == "Ditransitive_copy"
