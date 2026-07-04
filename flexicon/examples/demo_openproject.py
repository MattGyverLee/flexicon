# -*- coding: cp1252 -*-

#   demo_openproject.py
#
#   Tests and demonstrates access to a FieldWorks project.
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
TEST_PROJECT = r"__flexlibs_testing"


def reportBasicInfo(project):
    # Global things in the Language Project

    print("Information on project %s:" % project.ProjectName())

    # ============ General Settings =======
    print("Last modified:", project.GetDateLastModified())

    posList = project.GetPartsOfSpeech()
    print("There are %i Parts of Speech in this project:" % len(posList))
    for i in posList:
        print("\t", i)
    print()

    # ============ Writing Systems ============

    # The names of WS associated with this DB. Sorted and with no duplicates.

    wsList = project.GetWritingSystems()
    print("There are %i writing Systems in this project: (Language Tag, Handle)" % len(wsList))
    print()
    for x in wsList:
        name, langTag, handle, isVern = x
        print("\t", name)
        print("\t\t", langTag, handle)
        print("\t\t", "(Vernacular)" if isVern else "(Analysis)")
    print()

    # A tuple of (language-tag, display-name)
    print("\tDefault vernacular WS = %s; %s" % project.GetDefaultVernacularWS())
    print("\tDefault analysis WS   = %s; %s" % project.GetDefaultAnalysisWS())
    print()

    # ============= Lexicon ================
    print("Custom Fields:")
    print("\tEntry level:")
    for cf in project.LexiconGetEntryCustomFields():
        # Tuple of flid and user-defined name:
        print("\t\t%s (%s)" % (cf[1], cf[0]))
    print()

    print("\tSense level:")
    for cf in project.LexiconGetSenseCustomFields():
        print("\t\t%s (%s)" % (cf[1], cf[0]))
    print()

    print("The lexicon contains %d entries" % project.LexiconNumberOfEntries())

    print("The text corpus contains %d texts" % project.TextsNumberOfTexts())


# -------------------------------------------------------------------
if __name__ == "__main__":

    FLExInitialize()

    project = FLExProject()

    try:
        project.OpenProject(projectName=TEST_PROJECT, writeEnabled=False)
    except FP_ProjectError as e:
        print("OpenProject failed!")
        print(e.message)
        FLExCleanup()
        sys.exit(1)

    reportBasicInfo(project)

    # Clean-up
    project.CloseProject()

    FLExCleanup()
