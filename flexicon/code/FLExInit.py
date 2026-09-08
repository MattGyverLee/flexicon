#
#   FLExInit.py
#
#   Module: Fieldworks Language Explorer initialisation.
#
#   Note:   This module needs to be imported before importing or
#           using any Fieldworks Assemblies as it sets up the
#           path, and other low-level things.
#
#   Usage:  Call FLExInitialize() and FLExCleanup() as the first and
#           last actions from the main application.
#
#   Platform: Python.NET & IRONPython
#             FieldWorks Version 9
#
#   Copyright Craig Farrow, 2011 - 2022
#

import sys
import os
import glob
import shutil

import logging

logger = logging.getLogger(__name__)

# Defer version import to avoid circular dependency during initialization
try:
    from .. import version

    logger.info("flexlibs version: %s" % version)
except ImportError:
    # Version module not yet available during initialization
    version = None

logger.info("Python version: %s" % sys.version)

import clr
import System

# Configure the path for accessing the FW DLLs
from . import FLExGlobals

FLExGlobals.InitialiseFWGlobals()

clr.AddReference("FwUtils")
from SIL.FieldWorks.Common.FwUtils import FwRegistryHelper, FwUtils

clr.AddReference("SIL.WritingSystems")
from SIL.WritingSystems import Sldr

# -------------------------------------------------------------------


def FLExInitialize():
    """
    Initialize the Fieldworks libraries. An application should call
    this as the first thing it does.
    """
    # [FW9] These 3 inits copied from LCMBrowser::Main()
    logger.debug("Calling RegistryHelper.Initialize()")
    FwRegistryHelper.Initialize()
    logger.debug("Calling InitializeIcu()")
    FwUtils.InitializeIcu()
    # No need to access the online SLDR: Offline mode = True
    #
    # [#249] Sldr.Initialize() must NOT be wrapped in a bare `except
    # Exception`. If it fails for a real reason the SLDR stays down for the
    # whole process; every subsequent LDML read inside
    # CoreLdmlInFolderWritingSystemRepository then throws "The SLDR has not
    # been initialized", and liblcm responds by renaming the project's
    # .ldml files to .ldml.bad and re-synthesizing the writing systems from
    # defaults. That cycle repeats on every open and never terminates, so a
    # genuine failure has to reach the caller instead of being downgraded to
    # a warning that misattributes it as "already initialized?".
    #
    # Sldr exposes a public static IsInitialized probe (verified by live
    # reflection against SIL.WritingSystems 18.0.0.0 / FieldWorks 9.3.10),
    # which is safe to read before any init and mirrors the guard that
    # Initialize() itself uses. Probing it means the benign
    # already-initialized case never raises at all, which keeps repeated
    # FLExInitialize() calls a no-op -- examples and per-test setUp rely on
    # that.
    if Sldr.IsInitialized:
        logger.debug("Sldr already initialized; skipping Sldr.Initialize()")
    else:
        logger.debug("Calling Sldr.Initialize()")
        try:
            Sldr.Initialize(True)  # offlineTestMode=True
        except System.InvalidOperationException as e:
            # Retained only as a backstop for the check-then-act race:
            # Initialize()/Cleanup() serialize on a private lock, so another
            # thread can win between the probe and the call. Anything that is
            # not that exact benign message is a real failure and must
            # propagate.
            if "already been initialized" not in e.Message:
                raise
            logger.debug(
                "Sldr was initialized concurrently by another caller; continuing"
            )
    # Sldr.Initialize() can fail silently. If it doesn't return,
    # then it is likely a dll issue.
    logger.debug("FLExInit.Initialize complete")


def FLExCleanup():
    """
    Close up the Fieldworks libraries. An application should call this
    before exiting.
    """
    # [#249] Sldr.Cleanup() throws System.InvalidOperationException("The SLDR
    # has not been initialized.") when the SLDR is down -- so an unguarded
    # call made FLExCleanup() raise whenever FLExInitialize() was never run or
    # cleanup ran twice (several shipped examples call it twice by design).
    # Cleanup is a teardown step and must be tolerant of already being done.
    if not Sldr.IsInitialized:
        logger.debug("Sldr not initialized; skipping Sldr.Cleanup()")
        return
    logger.debug("Calling Sldr.Cleanup()")
    Sldr.Cleanup()
