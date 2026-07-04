# -*- coding: cp1252 -*-

#   demo_lexicon.py
#
#   Tests and demonstrates working with the FieldWorks lexicon.
#
#   Platforms: Python .NET and IronPython
#
#   Copyright Craig Farrow, 2008 - 2022
#

import sys

from flexlibs2 import FLExInitialize, FLExCleanup
from flexlibs2 import FLExProject, FP_ProjectError

# ============ Configurables ===============

# Project to use
TEST_PROJECT = "__flexlibs_testing"

# Maximum number of entries to print out; use
# a very big number for the whole lexicon.
LexiconMaxEntries = 20

# Enable writing tests
WriteTests = False

# Custom field name
CUSTOM_FIELD = r"SenseFlags"


# --------------------------------------------------------------------
def reportLexicalEntries(project):

    ftflagsFlid = project.LexiconGetSenseCustomFieldNamed(CUSTOM_FIELD)

    print("Opened project %s." % project.ProjectName())

    print("Listing up to %d lexical entries:" % LexiconMaxEntries)
    print()

    # Scan the lexicon (unordered), printing some of the data
    # using Standard Format markers.
    # (Uses a slice to only print a portion.)
    for e in list(project.LexiconAllEntries())[:LexiconMaxEntries]:
        print(r"\lx", project.LexiconGetLexemeForm(e))
        print(r"\lc", project.LexiconGetCitationForm(e))
        for sense in e.SensesOS:
            print(r"\ge", project.LexiconGetSenseGloss(sense))
            print(r"\pos", project.LexiconGetSensePOS(sense))
            print(r"\def", project.LexiconGetSenseDefinition(sense))
            if WriteTests and ftflagsFlid:
                flags = project.LexiconGetFieldText(sense, ftflagsFlid)
                print("FTFlags", flags)
                # CHANGES the project
                if flags:
                    project.LexiconAddTagToField(sense, ftflagsFlid, "tag-1")
                else:
                    project.LexiconSetFieldText(sense, ftflagsFlid, "FLAG!")
                flags = project.LexiconGetFieldText(sense, ftflagsFlid)
                print("New FTFlags", flags)
            if WriteTests:
                if project.LexiconGetSenseGloss(sense) == "Example Gloss":
                    # CHANGES the project
                    project.LexiconSetSenseGloss(sense, "Changed Gloss")
                    print("New Gloss", project.LexiconGetSenseGloss(sense))

            for example in sense.ExamplesOS:
                ex = project.LexiconGetExample(example)
                print(r"\ex", ex)
                if WriteTests and not ex:
                    # CHANGES the project
                    print("Setting example")
                    project.LexiconSetExample(example, "You should have an example sentence")

        print()


# --------------------------------------------------------------------


if __name__ == "__main__":

    FLExInitialize()

    project = FLExProject()

    try:
        project.OpenProject(projectName=TEST_PROJECT, writeEnabled=WriteTests)
    except FP_ProjectError as e:
        print("OpenProject failed!")
        print(e.message)
        FLExCleanup()
        sys.exit(1)

    reportLexicalEntries(project)

    # Clean-up
    project.CloseProject()

    FLExCleanup()
