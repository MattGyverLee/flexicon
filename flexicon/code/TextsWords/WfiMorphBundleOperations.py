#
#   WfiMorphBundleOperations.py
#
#   Class: WfiMorphBundleOperations
#          Morpheme bundle operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import FLEx LCM types
from SIL.LCModel import (
    IWfiMorphBundle,
    IWfiMorphBundleFactory,
    IWfiAnalysis,
    ILexSense,
    IMoMorphSynAnalysis,
    IMoMorphType,
    IMoInflClass,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable


class WfiMorphBundleOperations(BaseOperations):
    """
    This class provides operations for managing morpheme bundles in a FieldWorks project.

    Morpheme bundles (IWfiMorphBundle) represent individual morphemes within a wordform
    analysis. Each bundle contains the morpheme's form, gloss, and links to lexical
    information (sense, MSA, morph type, inflection class).

    In FLEx's interlinear text system, a wordform analysis consists of multiple
    morph bundles that break down the word into its constituent morphemes. For example,
    the word "running" might have two bundles: "run" (stem) + "-ing" (suffix).

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get a wordform and its analysis
        wordform = project.Wordforms.Find("running")
        analyses = project.Wordforms.GetAnalyses(wordform)
        if analyses:
            analysis = analyses[0]

            # Get all morph bundles for the analysis
            bundles = project.MorphBundles.GetAll(analysis)
            for bundle in bundles:
                form = project.MorphBundles.GetForm(bundle)
                gloss = project.MorphBundles.GetGloss(bundle)
                print(f"{form} - {gloss}")

            # Create a new morph bundle
            bundle = project.MorphBundles.Create(analysis)
            project.MorphBundles.SetForm(bundle, "run")
            project.MorphBundles.SetGloss(bundle, "run")

            # Link to lexicon
            sense = project.LexiconAllSenses()[0]
            project.MorphBundles.SetSense(bundle, sense)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize WfiMorphBundleOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """Specify which sequence to reorder for morph bundles."""
        return parent.MorphsOS

    # ==================== CORE CRUD OPERATIONS ====================

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, analysis_or_hvo):
        """
        Get all morph bundles for a wordform analysis.

        Args:
            analysis_or_hvo: The IWfiAnalysis object or HVO.

        Yields:
            IWfiMorphBundle: Each morph bundle in the analysis.

        Raises:
            FP_NullParameterError: If analysis_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> analysis = analyses[0]
            >>> for bundle in morphBundleOps.GetAll(analysis):
            ...     form = morphBundleOps.GetForm(bundle)
            ...     gloss = morphBundleOps.GetGloss(bundle)
            ...     print(f"{form} - {gloss}")
            run - run
            -ing - PROG

        Notes:
            - Returns bundles in the order they appear in the analysis
            - Order represents left-to-right morpheme sequence
            - Returns empty generator if analysis has no morph bundles
            - Each bundle represents a single morpheme in the word

        See Also:
            Create, Delete, Reorder
        """
        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Yield all morph bundles in sequence
        for bundle in analysis.MorphBundlesOS:
            yield bundle

    @OperationsMethod
    def Create(self, analysis_or_hvo):
        """
        Create a new morph bundle for a wordform analysis.

        Args:
            analysis_or_hvo: The IWfiAnalysis object or HVO.

        Returns:
            IWfiMorphBundle: The newly created morph bundle object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If analysis_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> analysis = analyses[0]
            >>> bundle = morphBundleOps.Create(analysis)
            >>> morphBundleOps.SetForm(bundle, "run")
            >>> morphBundleOps.SetGloss(bundle, "run")

            >>> # Create multiple bundles for complex morphology
            >>> stem_bundle = morphBundleOps.Create(analysis)
            >>> morphBundleOps.SetForm(stem_bundle, "walk")
            >>> affix_bundle = morphBundleOps.Create(analysis)
            >>> morphBundleOps.SetForm(affix_bundle, "-ed")

        Notes:
            - The bundle is added to the end of the analysis's bundle sequence
            - New bundles have no form, gloss, or lexical links by default
            - Use SetForm(), SetGloss(), SetSense(), etc. to populate
            - Use Reorder() to change the sequence if needed

        See Also:
            Delete, GetAll, SetForm, SetGloss
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        with self._TransactionCM("Create morph bundle"):
            # Create the new morph bundle using the factory
            factory = self.project.project.ServiceLocator.GetService(IWfiMorphBundleFactory)
            bundle = factory.Create()

            # Add to analysis's morph bundles collection
            analysis.MorphBundlesOS.Add(bundle)

            return bundle

    @OperationsMethod
    def Delete(self, bundle_or_hvo):
        """
        Delete a morph bundle from its analysis.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> analysis = analyses[0]
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if len(bundles) > 1:
            ...     # Delete the last bundle
            ...     morphBundleOps.Delete(bundles[-1])

        Warning:
            - Deletion is permanent and cannot be undone
            - Deleting a bundle changes the morphological analysis
            - May affect concordance and interlinear text displays
            - Consider whether analysis should be modified or replaced

        Notes:
            - Removes the bundle from the owning analysis
            - Other bundles in the analysis are not affected
            - The bundle is removed from the database

        See Also:
            Create, GetAll, Reorder
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)

        # Cast owner to its concrete IWfiAnalysis so MorphBundlesOS is
        # reachable. Raw bundle.Owner is typed as ICmObject and
        # hasattr(...,"MorphBundlesOS") returns False there, which is why
        # the prior implementation silently no-opped.
        owner = self._GetTypedOwner(bundle)
        if owner is None:
            raise FP_ParameterError("Morph bundle has no owning analysis")
        owner.MorphBundlesOS.Remove(bundle)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True):
        """
        Duplicate a morph bundle, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The IWfiMorphBundle object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source bundle.
                                If False, insert at end of analysis's bundle sequence.
            deep (bool): If True, also duplicate owned objects (if any exist).
                        If False (default), only copy simple properties and references.
                        Note: WfiMorphBundle has no owned objects, so deep has no effect.

        Returns:
            IWfiMorphBundle: The newly created duplicate bundle with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> analysis = analyses[0]
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     # Duplicate bundle
            ...     dup = morphBundleOps.Duplicate(bundles[0])
            ...     print(f"Original: {morphBundleOps.GetGuid(bundles[0])}")
            ...     print(f"Duplicate: {morphBundleOps.GetGuid(dup)}")
            Original: 12345678-1234-1234-1234-123456789abc
            Duplicate: 87654321-4321-4321-4321-cba987654321
            ...
            ...     # Verify content was copied
            ...     print(f"Form: {morphBundleOps.GetForm(dup)}")
            ...     print(f"Gloss: {morphBundleOps.GetGloss(dup)}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original bundle's position in sequence
            - Simple properties copied: Form, Gloss (MultiStrings)
            - Reference properties copied: SenseRA, MsaRA, MorphRA, InflClassRA
            - WfiMorphBundle has no owned objects, so deep parameter has no effect
            - Useful for creating similar morpheme analyses or templates

        See Also:
            Create, Delete, GetGuid
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source bundle and parent; MorphBundlesOS is declared on IWfiAnalysis
        # so cast directly instead of doing a wasteful Hvo round-trip.
        source = self.__GetBundleObject(item_or_hvo)
        parent = IWfiAnalysis(source.Owner)

        with self._TransactionCM("Duplicate morph bundle"):
            # Create new bundle using factory (auto-generates new GUID)
            factory = self.project.project.ServiceLocator.GetService(IWfiMorphBundleFactory)
            duplicate = factory.Create()

            # Determine insertion position
            if insert_after:
                # Insert after source bundle
                source_index = list(parent.MorphBundlesOS).index(source)
                parent.MorphBundlesOS.Insert(source_index + 1, duplicate)
            else:
                # Insert at end
                parent.MorphBundlesOS.Add(duplicate)

            # Copy MultiString properties. IWfiMorphBundle has Form but
            # NOT Gloss -- the displayed gloss comes from SenseRA.Gloss,
            # which the SenseRA assignment below preserves automatically.
            # The previous duplicate.Gloss.CopyAlternatives line raised
            # AttributeError on every call (same root bug as #16 / #108);
            # 4319886 fixed GetGloss/SetGloss but missed this site.
            # (issue #107)
            duplicate.Form.CopyAlternatives(source.Form)

            # Copy Reference Atomic (RA) properties
            if hasattr(source, "SenseRA") and source.SenseRA:
                duplicate.SenseRA = source.SenseRA
            if hasattr(source, "MsaRA") and source.MsaRA:
                duplicate.MsaRA = source.MsaRA
            if hasattr(source, "MorphRA") and source.MorphRA:
                duplicate.MorphRA = source.MorphRA
            if hasattr(source, "InflClassRA") and source.InflClassRA:
                duplicate.InflClassRA = source.InflClassRA

            # Note: WfiMorphBundle has no owned objects (OS collections), so deep has no effect

            return duplicate

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a morpheme bundle.

        Args:
            item: The IWfiMorphBundle object.

        Returns:
            dict: Dictionary of syncable properties with their values.

        Example:
            >>> props = project.MorphBundles.GetSyncableProperties(bundle)
            >>> print(props['Form'])
            {'en': 'run'}
            >>> print(props['SenseRA'])
            'abc123...'  # GUID of linked sense

        Notes:
            - MultiString properties: Form
              (IWfiMorphBundle has no Gloss field of its own; the
              displayed gloss is derived from SenseRA.Gloss -- see
              GetGloss for the read path.)
            - Reference Atomic properties: SenseRA, MsaRA, MorphRA, InflClassRA (GUIDs)
        """
        props = {}

        # MultiString properties
        if hasattr(item, "Form") and item.Form:
            props["Form"] = self.project.GetMultiStringDict(item.Form)

        # Reference Atomic properties (return GUIDs)
        if hasattr(item, "SenseRA") and item.SenseRA:
            props["SenseRA"] = str(item.SenseRA.Guid)

        if hasattr(item, "MsaRA") and item.MsaRA:
            props["MsaRA"] = str(item.MsaRA.Guid)

        if hasattr(item, "MorphRA") and item.MorphRA:
            props["MorphRA"] = str(item.MorphRA.Guid)

        if hasattr(item, "InflClassRA") and item.InflClassRA:
            props["InflClassRA"] = str(item.InflClassRA.Guid)

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two morpheme bundles for differences.

        Args:
            item1: First bundle object (from project 1)
            item2: Second bundle object (from project 2)
            ops1: Optional WfiMorphBundleOperations instance for project 1 (defaults to self)
            ops2: Optional WfiMorphBundleOperations instance for project 2 (defaults to self)

        Returns:
            tuple: (is_different, differences_dict)
                - is_different (bool): True if bundles differ, False if identical
                - differences_dict (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> is_diff, diffs = ops1.CompareTo(bundle1, bundle2, ops1, ops2)
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} != {val2}")

        Notes:
            - Compares the Form MultiString (IWfiMorphBundle has no
              Gloss field of its own; see GetSyncableProperties)
            - Compares reference properties by GUID
            - Empty/null values are treated as equivalent
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        differences = {}

        # Get all property keys from both items
        all_keys = set(props1.keys()) | set(props2.keys())

        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)

            # Compare values
            if self.project._CompareValues(val1, val2):
                # Values are different
                differences[key] = (val1, val2)

        is_different = len(differences) > 0
        return (is_different, differences)

    @OperationsMethod
    def Reorder(self, analysis_or_hvo, bundle_list):
        """
        Reorder morph bundles within an analysis.

        Args:
            analysis_or_hvo: The IWfiAnalysis object or HVO.
            bundle_list: List of IWfiMorphBundle objects in the desired order.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If analysis_or_hvo or bundle_list is None.
            FP_ParameterError: If bundle_list is invalid.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> analysis = analyses[0]
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> # Reverse the order
            >>> morphBundleOps.Reorder(analysis, bundles[::-1])

            >>> # Move a specific bundle to the front
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> affix = bundles[1]
            >>> stem = bundles[0]
            >>> morphBundleOps.Reorder(analysis, [affix, stem])

        Notes:
            - The bundle_list must contain all bundles from the analysis
            - Bundles from other analyses cannot be added this way
            - Order affects morpheme sequence in interlinear displays
            - Use carefully - incorrect ordering affects linguistic analysis

        See Also:
            GetAll, Create, Delete
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(analysis_or_hvo, "analysis_or_hvo")

        self._ValidateParam(bundle_list, "bundle_list")

        analysis = self.__GetAnalysisObject(analysis_or_hvo)

        # Validate that all bundles belong to this analysis
        current_bundles = set(analysis.MorphBundlesOS)
        new_bundles = set(bundle_list)

        if current_bundles != new_bundles:
            raise FP_ParameterError("Bundle list must contain exactly the same bundles as the analysis")

        with self._TransactionCM("Reorder morph bundles"):
            # Clear and re-add in new order
            analysis.MorphBundlesOS.Clear()
            for bundle in bundle_list:
                analysis.MorphBundlesOS.Add(bundle)

    # ==================== FORM & GLOSS OPERATIONS ====================

    @OperationsMethod
    def GetForm(self, bundle_or_hvo, wsHandle=None):
        """
        Get the morpheme form of a bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            str: The morpheme form, or empty string if not set.

        Raises:
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     form = morphBundleOps.GetForm(bundles[0])
            ...     print(form)
            run

            >>> # Get form in specific writing system
            >>> form_ipa = morphBundleOps.GetForm(bundles[0],
            ...                                     project.WSHandle('en-fonipa'))
            >>> print(form_ipa)
            rʌn

        Notes:
            - Form represents the surface morpheme as it appears in text
            - Returns empty string if form not set in specified writing system
            - Typically uses vernacular writing system
            - May include affixation markers like "-", "pre-", etc.

        See Also:
            SetForm, GetGloss, GetAll
        """
        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)
        wsHandle = self.__WSHandleVern(wsHandle)

        form = ITsString(bundle.Form.get_String(wsHandle)).Text
        return form or ""

    @OperationsMethod
    def SetForm(self, bundle_or_hvo, text, wsHandle=None):
        """
        Set the morpheme form of a bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.
            text: The morpheme form text to set.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If bundle_or_hvo or text is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     morphBundleOps.SetForm(bundles[0], "walk")
            ...     print(morphBundleOps.GetForm(bundles[0]))
            walk

            >>> # Set IPA pronunciation form
            >>> morphBundleOps.SetForm(bundles[0], "wɔk",
            ...                         project.WSHandle('en-fonipa'))

        Notes:
            - Form represents how the morpheme appears in the text
            - Can include affix markers (-, pre-, etc.)
            - Should match actual text tokens or morpheme segmentation
            - Use different writing systems for pronunciation variants

        See Also:
            GetForm, SetGloss, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        self._ValidateParam(text, "text")

        bundle = self.__GetBundleObject(bundle_or_hvo)
        wsHandle = self.__WSHandleVern(wsHandle)

        mkstr = TsStringUtils.MakeString(text, wsHandle)
        bundle.Form.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetGloss(self, bundle_or_hvo, wsHandle=None):
        """
        Get the morpheme gloss of a bundle.

        Read-only convenience: a morpheme bundle has no free-standing
        gloss field on IWfiMorphBundle itself. The displayed gloss
        comes from the bundle's linked lexical sense
        (``bundle.SenseRA.Gloss``). This method forwards to that path
        and, if no sense gloss is found, falls back to the MSA-level
        ``InterlinearAbbr`` (``bundle.MsaRA.InterlinearAbbr``) which
        covers grammatical morphemes whose gloss lives on the MSA.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The linked sense's gloss in the chosen WS; if the sense
            gloss is empty or absent, the MSA InterlinearAbbr; or an
            empty string if neither is available.

        Raises:
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     gloss = morphBundleOps.GetGloss(bundles[0])
            ...     print(gloss)
            run

        Notes:
            - Returns "" only when neither a sense gloss nor an MSA
              InterlinearAbbr is available.
            - Uses the analysis writing system by default (sense gloss
              only; InterlinearAbbr is WS-independent).
            - The sense-gloss path honours the wsHandle; the MSA fallback
              returns the LCM-computed abbreviation string directly.

        See Also:
            GetForm, GetSense
        """
        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)
        wsHandle = self.__WSHandleAnal(wsHandle)

        # IWfiMorphBundle has no Gloss field; the displayed gloss comes
        # from the linked sense's MultiUnicode Gloss. (issue #16)
        sense = bundle.SenseRA
        if sense is not None:
            gloss = ITsString(sense.Gloss.get_String(wsHandle)).Text
            if gloss:
                return gloss

        # Fallback for grammatical morphemes (issue #110): if the bundle has
        # an MsaRA, use InterlinearAbbr which is defined on IMoMorphSynAnalysis
        # and covers all four concrete MSA types (MoStemMsa, MoDerivAffMsa,
        # MoInflAffMsa, MoUnclassifiedAffixMsa).
        msa = bundle.MsaRA
        if msa is not None:
            abbr = msa.InterlinearAbbr
            if abbr:
                return abbr

        return ""

    @OperationsMethod
    def SetGloss(self, bundle_or_hvo, text, wsHandle=None):
        """
        Setting a gloss on a morpheme bundle is not supported.

        IWfiMorphBundle has no Gloss field of its own; the displayed
        gloss is derived from the bundle's linked sense
        (``bundle.SenseRA.Gloss``). Writing to that path would mutate
        the lexical sense for every wordform/analysis that references
        it, which is a surprising side effect to attach to a
        per-bundle setter. This method therefore refuses with a clear
        redirect rather than performing a hidden write.

        To change the gloss seen on a bundle, locate the linked sense
        and update its gloss directly:

            sense = morphBundleOps.GetSense(bundle)
            if sense is not None:
                project.Senses.SetGloss(sense, text, wsHandle=wsHandle)

        Raises:
            NotImplementedError: Always, with a message pointing at the
                LexSense path. The exception class signals an unsupported
                operation (capability refusal), not a bad argument.
        """
        raise NotImplementedError(
            "WfiMorphBundleOperations.SetGloss is not supported: "
            "IWfiMorphBundle has no Gloss field, and writing through "
            "SenseRA.Gloss would mutate the shared lexical sense. "
            "Use LexSenseOperations.SetGloss on bundle.SenseRA "
            "(see GetSense) when you really intend to change the sense's "
            "gloss for all bundles that reference it."
        )

    # ==================== LEXICAL LINK OPERATIONS ====================

    @OperationsMethod
    def GetSense(self, bundle_or_hvo):
        """
        Get the linked lexical sense for a morph bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.

        Returns:
            ILexSense or None: The linked sense object, or None if not linked.

        Raises:
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     sense = morphBundleOps.GetSense(bundles[0])
            ...     if sense:
            ...         # Get sense gloss
            ...         wsHandle = project.project.DefaultAnalWs
            ...         sense_gloss = ITsString(sense.Gloss.get_String(wsHandle)).Text
            ...         print(f"Linked to sense: {sense_gloss}")
            Linked to sense: run

        Notes:
            - Returns None if bundle is not linked to lexicon
            - Linking provides richer lexical information
            - Linked sense can provide definition, part of speech, etc.
            - Bundle gloss may derive from sense gloss
            - Important for concordance and lexical queries

        See Also:
            SetSense, GetMSA, GetGloss
        """
        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)
        return bundle.SenseRA if bundle.SenseRA else None

    @OperationsMethod
    def SetSense(self, bundle_or_hvo, sense_or_hvo):
        """
        Link a morph bundle to a lexical sense.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.
            sense_or_hvo: The ILexSense object or HVO to link, or None to unlink.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     # Link to a lexical sense
            ...     senses = list(project.LexiconAllSenses())
            ...     if senses:
            ...         morphBundleOps.SetSense(bundles[0], senses[0])

            >>> # Unlink from sense
            >>> morphBundleOps.SetSense(bundles[0], None)

        Notes:
            - Linking integrates text analysis with lexicon
            - Linked sense provides definition, POS, and other information
            - Setting to None breaks the lexical link
            - Consider also setting MSA when linking sense
            - Link is used in concordance views and lexical queries

        See Also:
            GetSense, SetMSA, SetGloss
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)

        if sense_or_hvo is None:
            bundle.SenseRA = None
        else:
            sense = self.__GetSenseObject(sense_or_hvo)
            bundle.SenseRA = sense

    @OperationsMethod
    def GetMorphType(self, bundle_or_hvo):
        """
        Get the morpheme type of a bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.

        Returns:
            IMoMorphType or None: The morpheme type (stem, prefix, suffix, etc.),
                                  or None if not set.

        Raises:
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     morphType = morphBundleOps.GetMorphType(bundles[0])
            ...     if morphType:
            ...         # Get type name
            ...         wsHandle = project.project.DefaultAnalWs
            ...         type_name = ITsString(morphType.Name.get_String(wsHandle)).Text
            ...         print(type_name)
            stem

        Notes:
            - Returns None if morph type not set
            - Morpheme types include: stem, root, prefix, suffix, infix,
              circumfix, clitic, proclitic, enclitic, simulfix, etc.
            - Type indicates the morphological category
            - May be inherited from linked sense/MSA
            - Important for morphological analysis and parsing

        See Also:
            SetMorphType, GetSense, GetMSA
        """
        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)
        return bundle.MorphRA if bundle.MorphRA else None

    @OperationsMethod
    def SetMorphType(self, bundle_or_hvo, morph_type_or_hvo):
        """
        Set the morpheme type of a bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.
            morph_type_or_hvo: The IMoMorphType object or HVO, or None to unset.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     # Get a morph type
            ...     morphTypes = project.lp.MorphTypesOA.PossibilitiesOS
            ...     suffix_type = [mt for mt in morphTypes
            ...                    if "suffix" in str(mt).lower()][0]
            ...     morphBundleOps.SetMorphType(bundles[1], suffix_type)

            >>> # Clear morph type
            >>> morphBundleOps.SetMorphType(bundles[1], None)

        Notes:
            - Morph type categorizes the morpheme structurally
            - Setting to None clears the type reference
            - Type should match the morpheme's linguistic function
            - May be automatically set when linking to sense
            - Affects morphological analysis and display

        See Also:
            GetMorphType, SetSense, SetMSA
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)

        if morph_type_or_hvo is None:
            bundle.MorphRA = None
        else:
            morph_type = self.__GetMorphTypeObject(morph_type_or_hvo)
            bundle.MorphRA = morph_type

    # ==================== MSA OPERATIONS ====================

    @OperationsMethod
    def GetMSA(self, bundle_or_hvo):
        """
        Get the Morpho-Syntactic Analysis (MSA) of a bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.

        Returns:
            IMoMorphSynAnalysis or None: The MSA object, or None if not set.

        Raises:
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     msa = morphBundleOps.GetMSA(bundles[0])
            ...     if msa:
            ...         print(f"MSA type: {msa.ClassName}")
            MSA type: MoStemMsa

        Notes:
            - Returns None if MSA not set
            - MSA provides morpho-syntactic information
            - Types include: MoStemMsa, MoInflAffMsa, MoDerivAffMsa, etc.
            - Contains information like part of speech, features, etc.
            - Usually comes from linked lexical entry/sense
            - Critical for grammatical analysis

        See Also:
            SetMSA, GetSense, GetMorphType
        """
        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)
        return bundle.MsaRA if bundle.MsaRA else None

    @OperationsMethod
    def SetMSA(self, bundle_or_hvo, msa_or_hvo):
        """
        Set the Morpho-Syntactic Analysis (MSA) of a bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.
            msa_or_hvo: The IMoMorphSynAnalysis object or HVO, or None to unset.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     # Get MSA from a lexical sense
            ...     sense = morphBundleOps.GetSense(bundles[0])
            ...     if sense:
            ...         entry = sense.Owner.Owner  # Get owning entry
            ...         if entry.MorphoSyntaxAnalysesOC.Count > 0:
            ...             msa = entry.MorphoSyntaxAnalysesOC[0]
            ...             morphBundleOps.SetMSA(bundles[0], msa)

            >>> # Clear MSA
            >>> morphBundleOps.SetMSA(bundles[0], None)

        Notes:
            - MSA provides grammatical category and features
            - Setting to None clears the MSA reference
            - MSA should be compatible with morpheme type
            - Usually set in conjunction with sense
            - Affects grammatical parsing and concordance

        See Also:
            GetMSA, SetSense, SetMorphType
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)

        if msa_or_hvo is None:
            bundle.MsaRA = None
        else:
            msa = self.__GetMSAObject(msa_or_hvo)
            bundle.MsaRA = msa

    # ==================== INFLECTION OPERATIONS ====================

    @OperationsMethod
    def GetInflType(self, bundle_or_hvo):
        """
        Get the inflection type of a bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.

        Returns:
            ICmPossibility or None: The inflection type object, or None if not set.

        Raises:
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     inflType = morphBundleOps.GetInflType(bundles[0])
            ...     if inflType:
            ...         wsHandle = project.project.DefaultAnalWs
            ...         type_name = ITsString(inflType.Name.get_String(wsHandle)).Text
            ...         print(f"Inflection type: {type_name}")
            Inflection type: past tense

        Notes:
            - Returns None if inflection type not set
            - Inflection type specifies the grammatical category
            - Examples: past tense, plural, comparative, etc.
            - References an ICmPossibility from the inflection type list
            - Used in morphological analysis and parsing
            - Complements the inflection class information

        See Also:
            SetInflType, GetInflectionClass, GetMSA
        """
        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)
        return bundle.InflTypeRA if bundle.InflTypeRA else None

    @OperationsMethod
    def SetInflType(self, bundle_or_hvo, infl_type_or_hvo):
        """
        Set the inflection type of a bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.
            infl_type_or_hvo: The ICmPossibility inflection type object or HVO, or None to unset.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     # Get an inflection type from the list
            ...     if project.lp.MorphologicalDataOA:
            ...         inflTypes = project.lp.MorphologicalDataOA.InflectionTypesOA
            ...         if inflTypes and inflTypes.PossibilitiesOS.Count > 0:
            ...             past_tense = inflTypes.PossibilitiesOS[0]
            ...             morphBundleOps.SetInflType(bundles[0], past_tense)

            >>> # Clear inflection type
            >>> morphBundleOps.SetInflType(bundles[0], None)

        Notes:
            - Inflection type specifies the grammatical inflection
            - Setting to None clears the type reference
            - Type should match the morpheme's grammatical function
            - May be automatically set when linking to lexical entry
            - Affects morphological analysis and display

        See Also:
            GetInflType, SetInflectionClass, SetMSA
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)

        if infl_type_or_hvo is None:
            bundle.InflTypeRA = None
        else:
            # Resolve to ICmPossibility object
            if isinstance(infl_type_or_hvo, int):
                infl_type = self.project.Object(infl_type_or_hvo)
            else:
                infl_type = infl_type_or_hvo
            bundle.InflTypeRA = infl_type

    @OperationsMethod
    def GetInflectionClass(self, bundle_or_hvo):
        """
        Get the inflection class of a bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.

        Returns:
            IMoInflClass or None: The inflection class object, or None if not set.

        Raises:
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     inflClass = morphBundleOps.GetInflectionClass(bundles[0])
            ...     if inflClass:
            ...         wsHandle = project.project.DefaultAnalWs
            ...         class_name = ITsString(inflClass.Name.get_String(wsHandle)).Text
            ...         print(f"Inflection class: {class_name}")
            Inflection class: strong verb

        Notes:
            - Returns None if inflection class not set
            - Inflection classes categorize inflectional paradigms
            - Examples: strong verb, weak verb, irregular, etc.
            - Relevant mainly for inflectional morphology
            - May affect paradigm generation and analysis
            - Not applicable to all morpheme types

        See Also:
            SetInflectionClass, GetMSA, GetMorphType
        """
        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)
        return bundle.InflClassRA if bundle.InflClassRA else None

    @OperationsMethod
    def SetInflectionClass(self, bundle_or_hvo, infl_class_or_hvo):
        """
        Set the inflection class of a bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.
            infl_class_or_hvo: The IMoInflClass object or HVO, or None to unset.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     # Get an inflection class
            ...     if project.lp.MorphologicalDataOA:
            ...         inflClasses = project.lp.MorphologicalDataOA.InflectionClassesOC
            ...         if inflClasses.Count > 0:
            ...             inflClass = inflClasses[0]
            ...             morphBundleOps.SetInflectionClass(bundles[0], inflClass)

            >>> # Clear inflection class
            >>> morphBundleOps.SetInflectionClass(bundles[0], None)

        Notes:
            - Inflection class specifies paradigm membership
            - Setting to None clears the class reference
            - Relevant for stems with inflectional variants
            - May be inherited from lexical entry
            - Affects paradigm generation and validation

        See Also:
            GetInflectionClass, SetMSA, SetMorphType
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)

        if infl_class_or_hvo is None:
            bundle.InflClassRA = None
        else:
            infl_class = self.__GetInflectionClassObject(infl_class_or_hvo)
            bundle.InflClassRA = infl_class

    # ==================== UTILITY OPERATIONS ====================

    @OperationsMethod
    def GetOwningAnalysis(self, bundle_or_hvo):
        """
        Get the wordform analysis that owns a morph bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.

        Returns:
            IWfiAnalysis: The owning analysis object.

        Raises:
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     owner = morphBundleOps.GetOwningAnalysis(bundles[0])
            ...     print(f"Owner HVO: {owner.Hvo}")
            Owner HVO: 12345

        Notes:
            - Every morph bundle belongs to exactly one analysis
            - The owner is always an IWfiAnalysis object
            - Useful for navigating from bundle back to analysis
            - Owner relationship is fundamental to data structure

        See Also:
            GetAll, Create, Delete
        """
        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)
        # Cast to declared return type IWfiAnalysis. Raw bundle.Owner is typed
        # as ICmObject in LCM; pythonnet only surfaces IWfiAnalysis properties
        # (e.g. MorphBundlesOS) after the explicit interface cast.
        return IWfiAnalysis(bundle.Owner)

    @OperationsMethod
    def GetGuid(self, bundle_or_hvo):
        """
        Get the GUID (Globally Unique Identifier) of a morph bundle.

        Args:
            bundle_or_hvo: The IWfiMorphBundle object or HVO.

        Returns:
            str: The GUID as a string.

        Raises:
            FP_NullParameterError: If bundle_or_hvo is None.

        Example:
            >>> morphBundleOps = WfiMorphBundleOperations(project)
            >>> bundles = list(morphBundleOps.GetAll(analysis))
            >>> if bundles:
            ...     guid = morphBundleOps.GetGuid(bundles[0])
            ...     print(f"Bundle GUID: {guid}")
            Bundle GUID: 12345678-1234-1234-1234-123456789abc

        Notes:
            - GUID is a unique identifier for the bundle
            - Remains constant even if bundle is modified
            - Useful for tracking and referencing across sessions
            - Format is standard GUID (128-bit value)
            - Used in synchronization and external references

        See Also:
            GetOwningAnalysis, GetAll
        """
        self._ValidateParam(bundle_or_hvo, "bundle_or_hvo")

        bundle = self.__GetBundleObject(bundle_or_hvo)
        return str(bundle.Guid)

    # ==================== PRIVATE HELPER METHODS ====================

    def __GetBundleObject(self, bundle_or_hvo):
        """
        Resolve HVO or object to IWfiMorphBundle.

        Args:
            bundle_or_hvo: Either an IWfiMorphBundle object or an HVO (int).

        Returns:
            IWfiMorphBundle: The resolved bundle object.
        """
        if isinstance(bundle_or_hvo, int):
            return self.project.Object(bundle_or_hvo)
        return bundle_or_hvo

    def __GetAnalysisObject(self, analysis_or_hvo):
        """
        Resolve HVO or object to IWfiAnalysis.

        Args:
            analysis_or_hvo: Either an IWfiAnalysis object or an HVO (int).

        Returns:
            IWfiAnalysis: The resolved analysis object.
        """
        if isinstance(analysis_or_hvo, int):
            return self.project.Object(analysis_or_hvo)
        return analysis_or_hvo

    def __GetSenseObject(self, sense_or_hvo):
        """
        Resolve HVO or object to ILexSense.

        Args:
            sense_or_hvo: Either an ILexSense object or an HVO (int).

        Returns:
            ILexSense: The resolved sense object.
        """
        if isinstance(sense_or_hvo, int):
            return self.project.Object(sense_or_hvo)
        return sense_or_hvo

    def __GetMorphTypeObject(self, morph_type_or_hvo):
        """
        Resolve HVO or object to IMoMorphType.

        Args:
            morph_type_or_hvo: Either an IMoMorphType object or an HVO (int).

        Returns:
            IMoMorphType: The resolved morph type object.
        """
        if isinstance(morph_type_or_hvo, int):
            return self.project.Object(morph_type_or_hvo)
        return morph_type_or_hvo

    def __GetMSAObject(self, msa_or_hvo):
        """
        Resolve HVO or object to IMoMorphSynAnalysis.

        Args:
            msa_or_hvo: Either an IMoMorphSynAnalysis object or an HVO (int).

        Returns:
            IMoMorphSynAnalysis: The resolved MSA object.
        """
        if isinstance(msa_or_hvo, int):
            return self.project.Object(msa_or_hvo)
        return msa_or_hvo

    def __GetInflectionClassObject(self, infl_class_or_hvo):
        """
        Resolve HVO or object to IMoInflClass.

        Args:
            infl_class_or_hvo: Either an IMoInflClass object or an HVO (int).

        Returns:
            IMoInflClass: The resolved inflection class object.
        """
        if isinstance(infl_class_or_hvo, int):
            return self.project.Object(infl_class_or_hvo)
        return infl_class_or_hvo

    def __WSHandleVern(self, wsHandle):
        """
        Get writing system handle, defaulting to vernacular WS for morpheme forms.

        Args:
            wsHandle: Optional writing system handle.

        Returns:
            int: The writing system handle.
        """
        if wsHandle is None:
            return self.project.project.DefaultVernWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultVernWs)

    def __WSHandleAnal(self, wsHandle):
        """
        Get writing system handle, defaulting to analysis WS for glosses.

        Args:
            wsHandle: Optional writing system handle.

        Returns:
            int: The writing system handle.
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)
