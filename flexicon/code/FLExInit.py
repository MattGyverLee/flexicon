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
    logger.debug("Calling Sldr.Initialize()")
    try:
        Sldr.Initialize(True)
    except Exception as e:
        # SLDR may already be initialized in some test/startup scenarios
        logger.warning(f"Sldr.Initialize failed (already initialized?): {e}")
    # Sldr.Initialize() can fail silently. If it doesn't return,
    # then it is likely a dll issue.
    logger.debug("FLExInit.Initialize complete")


def FLExCleanup():
    """
    Close up the Fieldworks libraries. An application should call this
    before exiting.
    """
    Sldr.Cleanup()
