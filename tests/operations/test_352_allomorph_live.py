#
#   test_352_allomorph_live.py
#
#   Live regression coverage for issue #352 (allomorph face):
#   IMoStemAllomorph has StemNameRA (not StemName); IMoAffixAllomorph has
#   MorphTypeRA (not AffixType).
#
#   Runs against target_sandbox (tempdir copy of the Target .fwbackup),
#   so nothing can leak into a real project.
#
#   Platform: Python.NET, FieldWorks 9+
#

import pytest

from flexicon.code.Lexicon.allomorph import Allomorph

pytestmark = pytest.mark.requires_live_project


class Test352AllomorphRAProperties:
    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_stem_name_unset_returns_empty(self, target_sandbox):
        entry = target_sandbox.LexEntry.Create(lexeme_form="TEST_352stem")
        try:
            allo = target_sandbox.Allomorphs.Create(entry, "TEST_352stem", morphType="stem")
            wrapped = Allomorph(allo)
            assert wrapped.is_stem_allomorph
            # StemNameRA is None on a fresh allomorph: must be "" --
            # the old StemName.get_String path raised (swallowed to "").
            assert wrapped.stem_name == ""
        finally:
            target_sandbox.LexEntry.Delete(entry)

    @pytest.mark.live_phase("AllomorphOperations", "read")
    def test_affix_type_returns_morph_type(self, target_sandbox):
        entry = target_sandbox.LexEntry.Create(lexeme_form="TEST_352affix")
        try:
            allo = target_sandbox.Allomorphs.Create(entry, "TEST_352ing", morphType="suffix")
            wrapped = Allomorph(allo)
            assert wrapped.is_affix_allomorph
            # Old AffixType member never existed (always None); the
            # MorphTypeRA retarget resolves the created suffix type.
            assert wrapped.affix_type is not None
        finally:
            target_sandbox.LexEntry.Delete(entry)
