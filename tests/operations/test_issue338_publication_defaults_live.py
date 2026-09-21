#
#   test_issue338_publication_defaults_live.py
#
#   Live regression coverage for issue #338:
#   new entries, senses, subsenses, and examples must default to being
#   excluded from every publication on creation.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest


pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_issue338_"


def _all_publication_guids(project):
    return {str(pub.Guid) for pub in project.Publications.GetAll()}


def _excluded_publication_guids(item):
    return {str(pub.Guid) for pub in item.DoNotPublishInRC}


def _sense_by_gloss(project, entry, gloss):
    for sense in entry.AllSenses:
        if project.Senses.GetGloss(sense) == gloss:
            return sense
    return None


def _example_by_text(project, sense, text):
    for example in sense.ExamplesOS:
        if project.Examples.GetExample(example) == text:
            return example
    return None


class TestIssue338PublicationDefaults:
    @pytest.mark.live_phase("LexEntryOperations", "add")
    def test_create_entry_and_blank_sense_default_exclude_all_publications(
        self, target_sandbox
    ):
        all_publications = _all_publication_guids(target_sandbox)
        if not all_publications:
            pytest.skip("Target sandbox has no publications to verify")

        lexeme = f"{TEST_PREFIX}entry_defaults"
        entry = target_sandbox.LexEntry.Create(
            lexeme_form=lexeme,
            create_blank_sense=True,
        )
        try:
            reread = target_sandbox.LexEntry.Find(lexeme)
            assert reread is not None, "Created entry did not round-trip through Find()"
            assert _excluded_publication_guids(reread) == all_publications

            senses = list(reread.SensesOS)
            assert len(senses) == 1, "Create(..., create_blank_sense=True) should create one blank sense"
            assert _excluded_publication_guids(senses[0]) == all_publications
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexSenseOperations", "add")
    def test_create_sense_default_excludes_all_publications(self, target_sandbox):
        all_publications = _all_publication_guids(target_sandbox)
        if not all_publications:
            pytest.skip("Target sandbox has no publications to verify")

        lexeme = f"{TEST_PREFIX}sense_parent"
        gloss = f"{TEST_PREFIX}sense_gloss"
        entry = target_sandbox.LexEntry.Create(lexeme, create_blank_sense=False)
        try:
            created = target_sandbox.Senses.Create(entry, gloss)
            assert created is not None

            reread_entry = target_sandbox.LexEntry.Find(lexeme)
            reread_sense = _sense_by_gloss(target_sandbox, reread_entry, gloss)
            assert reread_sense is not None, "Created sense did not round-trip through the LCM"
            assert _excluded_publication_guids(reread_sense) == all_publications
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexEntryOperations", "add")
    def test_addsense_default_excludes_all_publications(self, target_sandbox):
        all_publications = _all_publication_guids(target_sandbox)
        if not all_publications:
            pytest.skip("Target sandbox has no publications to verify")

        lexeme = f"{TEST_PREFIX}addsense_parent"
        gloss = f"{TEST_PREFIX}addsense_gloss"
        entry = target_sandbox.LexEntry.Create(lexeme, create_blank_sense=False)
        try:
            created = target_sandbox.LexEntry.AddSense(entry, gloss)
            assert created is not None

            reread_entry = target_sandbox.LexEntry.Find(lexeme)
            reread_sense = _sense_by_gloss(target_sandbox, reread_entry, gloss)
            assert reread_sense is not None, "AddSense result did not round-trip through the LCM"
            assert _excluded_publication_guids(reread_sense) == all_publications
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("LexSenseOperations", "add")
    def test_create_subsense_default_excludes_all_publications(self, target_sandbox):
        all_publications = _all_publication_guids(target_sandbox)
        if not all_publications:
            pytest.skip("Target sandbox has no publications to verify")

        lexeme = f"{TEST_PREFIX}subsense_parent"
        parent_gloss = f"{TEST_PREFIX}parent_gloss"
        child_gloss = f"{TEST_PREFIX}child_gloss"
        entry = target_sandbox.LexEntry.Create(lexeme, create_blank_sense=False)
        try:
            parent = target_sandbox.Senses.Create(entry, parent_gloss)
            child = target_sandbox.Senses.CreateSubsense(parent, child_gloss)
            assert child is not None

            reread_entry = target_sandbox.LexEntry.Find(lexeme)
            reread_parent = _sense_by_gloss(target_sandbox, reread_entry, parent_gloss)
            assert reread_parent is not None
            reread_child = _sense_by_gloss(target_sandbox, reread_entry, child_gloss)
            assert reread_child is not None, "Created subsense did not round-trip through the LCM"
            assert _excluded_publication_guids(reread_child) == all_publications
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("ExampleOperations", "add")
    @pytest.mark.parametrize(
        ("creator_name", "example_text"),
        [
            ("Examples.Create", f"{TEST_PREFIX}example_via_examples"),
            ("Senses.AddExample", f"{TEST_PREFIX}example_via_senses"),
        ],
    )
    def test_example_creators_default_exclude_all_publications(
        self, target_sandbox, creator_name, example_text
    ):
        all_publications = _all_publication_guids(target_sandbox)
        if not all_publications:
            pytest.skip("Target sandbox has no publications to verify")

        lexeme = f"{TEST_PREFIX}example_parent_{creator_name.replace('.', '_')}"
        gloss = f"{TEST_PREFIX}example_gloss_{creator_name.replace('.', '_')}"
        entry = target_sandbox.LexEntry.Create(lexeme, create_blank_sense=False)
        try:
            sense = target_sandbox.Senses.Create(entry, gloss)
            if creator_name == "Examples.Create":
                created = target_sandbox.Examples.Create(sense, example_text)
            else:
                created = target_sandbox.Senses.AddExample(sense, example_text)
            assert created is not None

            reread_entry = target_sandbox.LexEntry.Find(lexeme)
            reread_sense = _sense_by_gloss(target_sandbox, reread_entry, gloss)
            assert reread_sense is not None
            reread_example = _example_by_text(target_sandbox, reread_sense, example_text)
            assert reread_example is not None, (
                f"{creator_name} result did not round-trip through the LCM"
            )
            assert _excluded_publication_guids(reread_example) == all_publications
        finally:
            target_sandbox.LexEntry.Delete(entry)
