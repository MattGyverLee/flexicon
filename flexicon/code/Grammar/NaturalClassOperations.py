#
#   NaturalClassOperations.py
#
#   Class: NaturalClassOperations
#          Natural class operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# Import FLEx LCM types
from SIL.LCModel import (
    IPhNaturalClass,
    IPhNCSegments,
    IPhNCSegmentsFactory,
    IPhNCFeatures,
    IPhNCFeaturesFactory,
    IPhPhoneme,
    IFsClosedValue,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# Import string utilities
from ..Shared.string_utils import normalize_match_key


class NaturalClassOperations(BaseOperations):
    """
    This class provides operations for managing natural classes in a
    FieldWorks project.

    Natural classes are groups of phonemes that share common phonological
    features and pattern together in phonological rules. For example,
    voiceless stops {/p/, /t/, /k/} or vowels {/a/, /e/, /i/, /o/, /u/}.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all natural classes
        for nc in project.NaturalClasses.GetAll():
            name = project.NaturalClasses.GetName(nc)
            abbr = project.NaturalClasses.GetAbbreviation(nc)
            phonemes = project.NaturalClasses.GetPhonemes(nc)
            print(f"{name} ({abbr}): {len(phonemes)} phonemes")

        # Create a new natural class
        stops = project.NaturalClasses.Create("Voiceless Stops", "VLS")

        # Add phonemes to the class
        p_phoneme = project.Phonemes.Find("/p/")
        if p_phoneme:
            project.NaturalClasses.AddPhoneme(stops, p_phoneme)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize NaturalClassOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for natural classes.
        For NaturalClass, we reorder parent.SubPossibilitiesOS
        """
        return parent.SubPossibilitiesOS

    def __WSHandle(self, wsHandle):
        """
        Internal helper for writing system handles (analysis).

        Args:
            wsHandle: Writing system handle or None for default analysis WS.

        Returns:
            int: The writing system handle to use.
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

    def __GetNaturalClassObject(self, nc_or_hvo):
        """
        Internal helper to get natural class object from HVO or object.

        Args:
            nc_or_hvo: IPhNaturalClass object or HVO integer.

        Returns:
            IPhNaturalClass: The natural class object.
        """
        if isinstance(nc_or_hvo, int):
            return self.project.Object(nc_or_hvo)
        return nc_or_hvo

    def __GetPhonemeObject(self, phoneme_or_hvo):
        """
        Internal helper to get phoneme object from HVO or object.

        Args:
            phoneme_or_hvo: IPhPhoneme object or HVO integer.

        Returns:
            IPhPhoneme: The phoneme object.
        """
        if isinstance(phoneme_or_hvo, int):
            return self.project.Object(phoneme_or_hvo)
        return phoneme_or_hvo

    def __SetNameAndAbbreviation(self, nc, name, abbreviation):
        """
        Internal helper to set Name and Abbreviation on a natural class.

        Writes to the default analysis writing system. The natural class must
        already be owned (attached to PhonologicalDataOA.NaturalClassesOS)
        before calling this -- LCM MultiString setters can NPE on free-floating
        objects.

        Args:
            nc: The IPhNaturalClass object (segment- or feature-based).
            name (str): Name to write (caller is responsible for validation).
            abbreviation (str or None): Abbreviation to write. If None, no
                abbreviation alternative is set.
        """
        wsHandle = self.project.project.DefaultAnalWs

        mkstr_name = TsStringUtils.MakeString(name, wsHandle)
        nc.Name.set_String(wsHandle, mkstr_name)

        if abbreviation:
            mkstr_abbr = TsStringUtils.MakeString(abbreviation, wsHandle)
            nc.Abbreviation.set_String(wsHandle, mkstr_abbr)

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all natural classes in the phonological inventory.

        Yields:
            IPhNaturalClass: Each natural class in the project.

        Example:
            >>> for nc in project.NaturalClasses.GetAll():
            ...     name = project.NaturalClasses.GetName(nc)
            ...     abbr = project.NaturalClasses.GetAbbreviation(nc)
            ...     phonemes = project.NaturalClasses.GetPhonemes(nc)
            ...     print(f"{name} ({abbr}): {len(phonemes)} phonemes")
            Voiceless Stops (VLS): 3 phonemes
            Voiced Stops (VCD): 3 phonemes
            Nasals (N): 3 phonemes
            Vowels (V): 5 phonemes

        Notes:
            - Returns natural classes in their defined order
            - Includes both segment-based and feature-based classes
            - Empty if no natural classes defined

        See Also:
            Create, GetName, GetPhonemes
        """
        phon_data = self.project.lp.PhonologicalDataOA
        if phon_data is not None:
            natural_classes = list(phon_data.NaturalClassesOS)
            for nc in natural_classes:
                yield nc

    @OperationsMethod
    def Find(self, name, wsHandle=None):
        """
        Find a natural class by name.

        Args:
            name (str): The name to search for. Compared via NFD-normalised
                        casefold match against each natural class's Name in
                        the chosen WS.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            IPhNaturalClass or None: First match, or None.

        Notes:
            - Mirrors POSOperations.Find / PhonFeatureOperations.Find.
            - Searches both IPhNCSegments and IPhNCFeatures variants
              (both inherit from IPhNaturalClass).
            - Does NOT search by abbreviation; use a manual GetAbbreviation
              loop for that.

        Example:
            >>> vowels = project.NaturalClasses.Find("Vowels")
            >>> if vowels is not None:
            ...     print(project.NaturalClasses.GetAbbreviation(vowels))
            V
        """
        self._ValidateParam(name, "name")
        target = normalize_match_key(name, casefold=True)
        if not target:
            return None
        wsHandle = self.__WSHandle(wsHandle)

        for nc in self.GetAll():
            nc_name = ITsString(nc.Name.get_String(wsHandle)).Text
            if nc_name and normalize_match_key(nc_name, casefold=True) == target:
                return nc
        return None

    @OperationsMethod
    def Exists(self, name, wsHandle=None):
        """
        Check whether a natural class with the given name exists.

        Args:
            name (str): Name to look up.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            bool: True if found.
        """
        self._ValidateParam(name, "name")
        return self.Find(name, wsHandle=wsHandle) is not None

    @OperationsMethod
    def Create(self, name, abbreviation=None):
        """
        Create a new natural class.

        Args:
            name (str): The name of the natural class (e.g., "Voiceless Stops").
            abbreviation (str, optional): Short abbreviation (e.g., "VLS", "V", "C").
                If None, defaults to empty string.

        Returns:
            IPhNCSegments: The newly created natural class object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> # Create basic consonant classes
            >>> stops = project.NaturalClasses.Create("Stops", "P")
            >>> fricatives = project.NaturalClasses.Create("Fricatives", "F")
            >>> nasals = project.NaturalClasses.Create("Nasals", "N")

            >>> # Create vowel classes
            >>> vowels = project.NaturalClasses.Create("Vowels", "V")
            >>> high_vowels = project.NaturalClasses.Create("High Vowels", "HV")

            >>> # Create without abbreviation
            >>> custom_class = project.NaturalClasses.Create("Custom Class")

        Notes:
            - Name should be descriptive of the phonological property
            - Abbreviation is used in rule notation (e.g., V → Ø / _C#)
            - After creation, use AddPhoneme() to add members
            - Creates a segment-based natural class (IPhNCSegments)

        See Also:
            Delete, AddPhoneme, SetName, SetAbbreviation
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        # Create the new natural class using the factory
        factory = self.project.project.ServiceLocator.GetService(IPhNCSegmentsFactory)

        with self._TransactionCM("Create natural class"):
            nc = factory.Create()

            # Add to the natural classes collection (must be done before setting properties)
            phon_data = self.project.lp.PhonologicalDataOA
            phon_data.NaturalClassesOS.Add(nc)

            # Set Name + Abbreviation (default analysis WS)
            self.__SetNameAndAbbreviation(nc, name, abbreviation)

            return nc

    @OperationsMethod
    def Delete(self, nc_or_hvo):
        """
        Delete a natural class.

        Args:
            nc_or_hvo: The IPhNaturalClass object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If nc_or_hvo is None.

        Example:
            >>> obsolete = project.NaturalClasses.Create("Obsolete", "OBS")
            >>> # ... realize it's not needed
            >>> project.NaturalClasses.Delete(obsolete)

        Warning:
            - Deleting a natural class that is in use may cause errors
            - This includes natural classes used in:
              - Phonological rules
              - Phonological environments
              - Other natural class definitions
            - Deletion is permanent and cannot be undone
            - Does not delete the phonemes in the class, only the class itself

        See Also:
            Create, GetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(nc_or_hvo, "nc_or_hvo")

        # Resolve to natural class object
        nc = self.__GetNaturalClassObject(nc_or_hvo)

        # Remove from the natural classes collection
        phon_data = self.project.lp.PhonologicalDataOA
        phon_data.NaturalClassesOS.Remove(nc)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True):
        """
        Duplicate a natural class, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The IPhNaturalClass object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source natural class.
                                If False, insert at end of natural classes list.
            deep (bool): If True, also duplicate owned objects (if any exist).
                        If False (default), only copy simple properties and references.
                        Note: NaturalClass has no owned objects, so deep has no effect.

        Returns:
            IPhNaturalClass: The newly created duplicate. Returns
            IPhNCSegments for a segment-based source, IPhNCFeatures for
            a feature-based source.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> ncOps = NaturalClassOperations(project)
            >>> stops = ncOps.Create("Voiceless Stops", "VLS")
            >>> # Add some phonemes...
            >>> # Now duplicate it to create "Voiced Stops"
            >>> voiced = ncOps.Duplicate(stops)
            >>> ncOps.SetName(voiced, "Voiced Stops")
            >>> ncOps.SetAbbreviation(voiced, "VCD")

            >>> # Feature-based duplication also works:
            >>> back = project.NaturalClasses.CreateFeatureBased(
            ...     "Back vowels", "Vb", specs=[(back_feat, plus)]
            ... )
            >>> high_back = ncOps.Duplicate(back)
            >>> ncOps.GetType(high_back)
            'features'

        Notes:
            - Factory.Create() automatically generates a new GUID.
            - insert_after=True preserves the original class's position.
            - Simple properties copied: Name, Abbreviation, Description.
            - Concrete-type dispatch (issue #27):
                - Segments-based source -> IPhNCSegmentsFactory; copy
                  SegmentsRC (phoneme members, shallow copy).
                - Features-based source -> IPhNCFeaturesFactory; clone
                  FeaturesOA's (feature, value) specs into a new
                  IFsFeatStruc via PhonFeatures.MakeFeatStruc.

        See Also:
            Create, CreateFeatureBased, GetType, GetGuid, AddPhoneme
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source natural class.
        source = self.__GetNaturalClassObject(item_or_hvo)
        phon_data = self.project.lp.PhonologicalDataOA

        # Single source of truth for concrete-NC discrimination: route
        # through GetType() so future subtype additions or defensive
        # fallback changes propagate here automatically. Hardcoding
        # IPhNCSegmentsFactory (the original #27 bug) silently produced
        # wrong-type clones from feature-based sources; the inline
        # `hasattr(source, "FeaturesOA")` duplicate was the same rule
        # as GetType but shipped a second copy that could drift.
        # (issue #96)
        nc_type = self.GetType(source)
        is_features = (nc_type == "features")

        if is_features:
            factory = self.project.project.ServiceLocator.GetService(
                IPhNCFeaturesFactory
            )
        else:
            factory = self.project.project.ServiceLocator.GetService(
                IPhNCSegmentsFactory
            )

        with self._TransactionCM("Duplicate natural class"):
            duplicate = factory.Create()

            # Determine insertion position.
            if insert_after:
                source_index = list(phon_data.NaturalClassesOS).index(source)
                phon_data.NaturalClassesOS.Insert(source_index + 1, duplicate)
            else:
                phon_data.NaturalClassesOS.Add(duplicate)

            # Copy simple MultiString properties.
            duplicate.Name.CopyAlternatives(source.Name)
            duplicate.Abbreviation.CopyAlternatives(source.Abbreviation)
            duplicate.Description.CopyAlternatives(source.Description)

            # Copy the type-specific membership data.
            if is_features:
                # Extract source feature specs and rebuild via MakeFeatStruc.
                # MakeFeatStruc attaches the new struct to duplicate.FeaturesOA
                # BEFORE populating FeatureSpecsOC (Phase 2 ownership rule).
                specs = []
                source_struct = source.FeaturesOA
                if source_struct is not None:
                    for raw in source_struct.FeatureSpecsOC:
                        cv = IFsClosedValue(raw)
                        specs.append((cv.FeatureRA, cv.ValueRA))
                if specs:
                    self.project.PhonFeatures.MakeFeatStruc(specs, owner=duplicate)
            else:
                # Reference-collection copy of phoneme members (shallow:
                # both classes reference the same IPhPhoneme objects).
                for phoneme in source.SegmentsRC:
                    duplicate.SegmentsRC.Add(phoneme)

            return duplicate

    @OperationsMethod
    def GetName(self, nc_or_hvo, wsHandle=None):
        """
        Get the name of a natural class.

        Args:
            nc_or_hvo: The IPhNaturalClass object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The natural class name, or empty string if not set.

        Raises:
            FP_NullParameterError: If nc_or_hvo is None.

        Example:
            >>> for nc in project.NaturalClasses.GetAll():
            ...     name = project.NaturalClasses.GetName(nc)
            ...     print(name)
            Voiceless Stops
            Voiced Stops
            Fricatives
            Nasals
            Vowels

        See Also:
            SetName, GetAbbreviation
        """
        self._ValidateParam(nc_or_hvo, "nc_or_hvo")

        nc = self.__GetNaturalClassObject(nc_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name = ITsString(nc.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetName(self, nc_or_hvo, name, wsHandle=None):
        """
        Set the name of a natural class.

        Args:
            nc_or_hvo: The IPhNaturalClass object or HVO.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If nc_or_hvo or name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> nc = project.NaturalClasses.Create("Plosives", "P")
            >>> # Prefer linguistic standard terminology
            >>> project.NaturalClasses.SetName(nc, "Stops")

        Notes:
            - Use standard phonological terminology
            - Name should reflect the shared phonological property

        See Also:
            GetName, SetAbbreviation
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(nc_or_hvo, "nc_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        nc = self.__GetNaturalClassObject(nc_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        nc.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetAbbreviation(self, nc_or_hvo, wsHandle=None):
        """
        Get the abbreviation of a natural class.

        Args:
            nc_or_hvo: The IPhNaturalClass object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The natural class abbreviation, or empty string if not set.

        Raises:
            FP_NullParameterError: If nc_or_hvo is None.

        Example:
            >>> nc = project.NaturalClasses.Create("Voiceless Stops", "VLS")
            >>> abbr = project.NaturalClasses.GetAbbreviation(nc)
            >>> print(abbr)
            VLS

            >>> # Print rule using abbreviations
            >>> # Rule: VLS → VCD / V_V (voicing between vowels)
            >>> vls = project.NaturalClasses.Find("Voiceless Stops")
            >>> vcd = project.NaturalClasses.Find("Voiced Stops")
            >>> v = project.NaturalClasses.Find("Vowels")
            >>> if vls and vcd and v:
            ...     vls_abbr = project.NaturalClasses.GetAbbreviation(vls)
            ...     vcd_abbr = project.NaturalClasses.GetAbbreviation(vcd)
            ...     v_abbr = project.NaturalClasses.GetAbbreviation(v)
            ...     print(f"{vls_abbr} → {vcd_abbr} / {v_abbr}_{v_abbr}")
            VLS → VCD / V_V

        Notes:
            - Abbreviations are used in phonological rule notation
            - Standard abbreviations: V (vowel), C (consonant), N (nasal), etc.
            - Keep abbreviations short and mnemonic

        See Also:
            GetName, SetAbbreviation
        """
        self._ValidateParam(nc_or_hvo, "nc_or_hvo")

        nc = self.__GetNaturalClassObject(nc_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        abbr = ITsString(nc.Abbreviation.get_String(wsHandle)).Text
        return abbr or ""

    @OperationsMethod
    def GetPhonemes(self, nc_or_hvo):
        """
        Get all phonemes in a natural class.

        Args:
            nc_or_hvo: The IPhNaturalClass object or HVO.

        Returns:
            list: List of IPhPhoneme objects in the class (empty list if none).

        Raises:
            FP_NullParameterError: If nc_or_hvo is None.

        Example:
            >>> # Get members of voiceless stops
            >>> for nc in project.NaturalClasses.GetAll():
            ...     name = project.NaturalClasses.GetName(nc)
            ...     if name == "Voiceless Stops":
            ...         phonemes = project.NaturalClasses.GetPhonemes(nc)
            ...         for phoneme in phonemes:
            ...             print(project.Phonemes.GetRepresentation(phoneme))
            /p/
            /t/
            /k/

            >>> # Print all natural classes with their members
            >>> for nc in project.NaturalClasses.GetAll():
            ...     name = project.NaturalClasses.GetName(nc)
            ...     phonemes = project.NaturalClasses.GetPhonemes(nc)
            ...     count = len(phonemes)
            ...     print(f"{name}: {count} phonemes")
            Voiceless Stops: 3 phonemes
            Voiced Stops: 3 phonemes
            Nasals: 3 phonemes

        Notes:
            - Returns empty list if class is feature-based without explicit segments
            - For segment-based classes (IPhNCSegments), returns SegmentsRC
            - Order is as defined in the natural class
            - Changes to returned list do not affect the natural class

        See Also:
            AddPhoneme, RemovePhoneme
        """
        self._ValidateParam(nc_or_hvo, "nc_or_hvo")

        nc = self.__GetNaturalClassObject(nc_or_hvo)

        # Check if it's a segment-based natural class
        if hasattr(nc, "SegmentsRC"):
            return list(nc.SegmentsRC)
        return []

    @OperationsMethod
    def AddPhoneme(self, nc_or_hvo, phoneme_or_hvo):
        """
        Add a phoneme to a natural class.

        Args:
            nc_or_hvo: The IPhNaturalClass object or HVO.
            phoneme_or_hvo: The IPhPhoneme object or HVO to add.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If nc_or_hvo or phoneme_or_hvo is None.
            FP_ParameterError: If the natural class is feature-based (cannot add segments).

        Example:
            >>> # Create voiceless stops class
            >>> nc = project.NaturalClasses.Create("Voiceless Stops", "VLS")
            >>> p = project.Phonemes.Find("/p/")
            >>> t = project.Phonemes.Find("/t/")
            >>> k = project.Phonemes.Find("/k/")
            >>> if p:
            ...     project.NaturalClasses.AddPhoneme(nc, p)
            >>> if t:
            ...     project.NaturalClasses.AddPhoneme(nc, t)
            >>> if k:
            ...     project.NaturalClasses.AddPhoneme(nc, k)

            >>> # Create vowel class
            >>> vowels = project.NaturalClasses.Create("Vowels", "V")
            >>> for repr in ["/a/", "/e/", "/i/", "/o/", "/u/"]:
            ...     phoneme = project.Phonemes.Find(repr)
            ...     if phoneme:
            ...         project.NaturalClasses.AddPhoneme(vowels, phoneme)

        Notes:
            - Only works with segment-based natural classes (IPhNCSegments)
            - A phoneme can belong to multiple natural classes
            - Duplicate additions are typically ignored
            - For feature-based classes, define features instead

        See Also:
            RemovePhoneme, GetPhonemes, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(nc_or_hvo, "nc_or_hvo")
        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")

        nc = self.__GetNaturalClassObject(nc_or_hvo)
        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)

        # Check if it's a segment-based natural class
        if not hasattr(nc, "SegmentsRC"):
            raise FP_ParameterError("Cannot add phoneme to feature-based natural class")

        # Add the phoneme if not already present
        if phoneme not in nc.SegmentsRC:
            nc.SegmentsRC.Add(phoneme)

    @OperationsMethod
    def RemovePhoneme(self, nc_or_hvo, phoneme_or_hvo):
        """
        Remove a phoneme from a natural class.

        Args:
            nc_or_hvo: The IPhNaturalClass object or HVO.
            phoneme_or_hvo: The IPhPhoneme object or HVO to remove.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If nc_or_hvo or phoneme_or_hvo is None.
            FP_ParameterError: If the natural class is feature-based or if
                the phoneme is not in the natural class.

        Example:
            >>> # Remove /q/ from uvular stops if reclassified
            >>> for nc in project.NaturalClasses.GetAll():
            ...     if project.NaturalClasses.GetName(nc) == "Uvular Stops":
            ...         q_phoneme = project.Phonemes.Find("/q/")
            ...         if q_phoneme and q_phoneme in project.NaturalClasses.GetPhonemes(nc):
            ...             project.NaturalClasses.RemovePhoneme(nc, q_phoneme)

            >>> # Clean up natural class
            >>> for nc in project.NaturalClasses.GetAll():
            ...     if project.NaturalClasses.GetName(nc) == "Obsolete Phonemes":
            ...         phonemes = project.NaturalClasses.GetPhonemes(nc)
            ...         for phoneme in phonemes:
            ...             project.NaturalClasses.RemovePhoneme(nc, phoneme)

        Notes:
            - Only works with segment-based natural classes
            - Phoneme must be in the class's SegmentsRC collection
            - Use GetPhonemes() to check membership first

        See Also:
            AddPhoneme, GetPhonemes
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(nc_or_hvo, "nc_or_hvo")
        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")

        nc = self.__GetNaturalClassObject(nc_or_hvo)
        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)

        # Check if it's a segment-based natural class
        if not hasattr(nc, "SegmentsRC"):
            raise FP_ParameterError("Cannot remove phoneme from feature-based natural class")

        # Check if phoneme is in the collection
        if phoneme not in nc.SegmentsRC:
            raise FP_ParameterError("Phoneme not found in natural class")

        # Remove the phoneme
        nc.SegmentsRC.Remove(phoneme)

    # ========== FEATURE-BASED NATURAL CLASSES ==========

    @OperationsMethod
    def CreateFeatureBased(self, name, abbreviation=None, specs=None):
        """
        Create a feature-based natural class (IPhNCFeatures).

        Feature-based natural classes define membership by phonological
        feature constraints (e.g. [+syllabic, +back]) rather than by an
        explicit list of phonemes. Any phoneme whose features satisfy the
        constraint is treated as a member; adding a phoneme that matches
        the constraints brings it into the class automatically.

        Use this for generative phonology where you want natural classes
        like "back vowels" or "voiced obstruents" expressed as feature
        bundles. Use ``Create`` instead for segment-based classes that
        enumerate their phonemes.

        Note: LCM natural-class objects are immutable in their concrete
        type after creation -- there is no in-place switch between
        segment-based and feature-based. To "convert" between types,
        Delete the old class and Create a new one.

        Args:
            name (str): The name of the natural class (analysis WS).
            abbreviation (str, optional): Short abbreviation. If None,
                no abbreviation alternative is written.
            specs (list[tuple], optional): A list of ``(feature, value)``
                tuples used to populate the natural class's feature
                struct. Each side may be an LCM object (IFsClosedFeature,
                IFsSymFeatVal), a wrapper, or an HVO. If provided, the
                resulting NC has a populated ``FeaturesOA``. If omitted,
                ``FeaturesOA`` remains unset and the caller can use
                ``SetFeatures`` later.

        Returns:
            IPhNCFeatures: The newly created feature-based natural class.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name is None.
            FP_ParameterError: If name is empty or specs is malformed.

        Example:
            >>> # Build "back vowels" as [+back]
            >>> back = project.PhonFeatures.Find("back")
            >>> back_plus = project.PhonFeatures.GetValues(back)[0]
            >>> nc = project.NaturalClasses.CreateFeatureBased(
            ...     "Back vowels", "Vb", specs=[(back, back_plus)]
            ... )
            >>> project.NaturalClasses.GetType(nc)
            'features'

            >>> # Create empty, populate later
            >>> nc = project.NaturalClasses.CreateFeatureBased("High vowels", "Vh")
            >>> high = project.PhonFeatures.Find("high")
            >>> high_plus = project.PhonFeatures.GetValues(high)[0]
            >>> project.NaturalClasses.SetFeatures(nc, [(high, high_plus)])

        See Also:
            Create, GetType, GetFeatures, SetFeatures
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        # Create the new feature-based natural class using its factory
        factory = self.project.project.ServiceLocator.GetService(
            IPhNCFeaturesFactory
        )

        with self._TransactionCM("Create feature-based natural class"):
            nc = factory.Create()

            # Add to the natural classes collection (must be done before
            # setting properties -- LCM property setters can NPE on
            # free-floating objects)
            phon_data = self.project.lp.PhonologicalDataOA
            phon_data.NaturalClassesOS.Add(nc)

            # Set Name + Abbreviation (default analysis WS)
            self.__SetNameAndAbbreviation(nc, name, abbreviation)

            # Populate FeaturesOA via the Phase 5b primitive, which attaches the
            # struct to nc.FeaturesOA BEFORE populating FeatureSpecsOC (Phase 2
            # ownership rule).
            if specs:
                self.project.PhonFeatures.MakeFeatStruc(specs, owner=nc)

            return nc

    @OperationsMethod
    def GetType(self, nc_or_hvo):
        """
        Return the concrete type of a natural class as a short string.

        Args:
            nc_or_hvo: The IPhNaturalClass object or HVO.

        Returns:
            str: ``"segments"`` for IPhNCSegments (enumerated phoneme
            members), ``"features"`` for IPhNCFeatures (feature-based
            membership), or the LCM ClassName as a defensive fallback
            for unknown subtypes.

        Raises:
            FP_NullParameterError: If nc_or_hvo is None.

        Example:
            >>> stops = project.NaturalClasses.Create("Stops", "P")
            >>> project.NaturalClasses.GetType(stops)
            'segments'
            >>> vb = project.NaturalClasses.CreateFeatureBased("Back vowels", "Vb")
            >>> project.NaturalClasses.GetType(vb)
            'features'

        Notes:
            Use this to decide which mutators are valid for a given
            natural class. ``GetPhonemes``/``AddPhoneme``/``RemovePhoneme``
            require segments-type; ``GetFeatures``/``SetFeatures`` require
            features-type.

        See Also:
            Create, CreateFeatureBased, GetPhonemes, GetFeatures
        """
        self._ValidateParam(nc_or_hvo, "nc_or_hvo")

        nc = self.__GetNaturalClassObject(nc_or_hvo)

        # Prefer concrete-type detection via the owning/reference property.
        # IPhNCFeatures has FeaturesOA; IPhNCSegments has SegmentsRC.
        if hasattr(nc, "FeaturesOA"):
            return "features"
        if hasattr(nc, "SegmentsRC"):
            return "segments"
        # Defensive fallback for unknown subtypes
        return nc.ClassName

    @OperationsMethod
    def GetFeatures(self, nc_or_hvo):
        """
        Get the feature struct holding a feature-based natural class's
        constraints.

        Args:
            nc_or_hvo: The IPhNaturalClass object or HVO. Must be a
                feature-based natural class (IPhNCFeatures).

        Returns:
            IFsFeatStruc or None: The owned feature structure (with its
            ``FeatureSpecsOC`` of IFsClosedValue specs), or ``None`` if
            ``FeaturesOA`` is unset (e.g. a feature-based class created
            with no initial specs that hasn't yet called ``SetFeatures``).

        Raises:
            FP_NullParameterError: If nc_or_hvo is None.
            FP_ParameterError: If the natural class is not feature-based
                (i.e. it is a segment-based IPhNCSegments).

        Example:
            >>> back = project.PhonFeatures.Find("back")
            >>> back_plus = project.PhonFeatures.GetValues(back)[0]
            >>> nc = project.NaturalClasses.CreateFeatureBased(
            ...     "Back vowels", "Vb", specs=[(back, back_plus)]
            ... )
            >>> fs = project.NaturalClasses.GetFeatures(nc)
            >>> for spec in fs.FeatureSpecsOC:
            ...     print(spec)

        See Also:
            SetFeatures, GetType, CreateFeatureBased
        """
        self._ValidateParam(nc_or_hvo, "nc_or_hvo")

        nc = self.__GetNaturalClassObject(nc_or_hvo)

        if not hasattr(nc, "FeaturesOA"):
            name_text = ITsString(
                nc.Name.get_String(self.project.project.DefaultAnalWs)
            ).Text or "(unnamed)"
            raise FP_ParameterError(
                f"Natural class '{name_text}' is not feature-based "
                f"(class={nc.ClassName}); GetFeatures only works on "
                f"IPhNCFeatures."
            )

        return nc.FeaturesOA

    @OperationsMethod
    def SetFeatures(self, nc_or_hvo, specs):
        """
        Replace a feature-based natural class's constraints with a new
        feature struct built from ``specs``.

        Any existing ``FeaturesOA`` is discarded -- assigning to an
        atomic-owning property in LCM disowns and deletes the previous
        owned object, so callers do not need to release it manually.

        Args:
            nc_or_hvo: The IPhNaturalClass object or HVO. Must be a
                feature-based natural class (IPhNCFeatures).
            specs (list[tuple]): A list of ``(feature, value)`` tuples
                describing the new constraints. Same shape as
                ``PhonFeatures.MakeFeatStruc`` accepts; each side may be
                an LCM object, a wrapper, or an HVO.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If nc_or_hvo or specs is None.
            FP_ParameterError: If the natural class is not feature-based
                or if specs is malformed.

        Example:
            >>> nc = project.NaturalClasses.CreateFeatureBased("Back vowels", "Vb")
            >>> back = project.PhonFeatures.Find("back")
            >>> back_plus = project.PhonFeatures.GetValues(back)[0]
            >>> project.NaturalClasses.SetFeatures(nc, [(back, back_plus)])

            >>> # Replace constraints (previous FeaturesOA is discarded)
            >>> high = project.PhonFeatures.Find("high")
            >>> high_plus = project.PhonFeatures.GetValues(high)[0]
            >>> project.NaturalClasses.SetFeatures(
            ...     nc, [(back, back_plus), (high, high_plus)]
            ... )

        Notes:
            ``MakeFeatStruc`` attaches the new struct to ``nc.FeaturesOA``
            and populates ``FeatureSpecsOC`` atomically, following the
            Phase 2 ownership rule. The LCM owning-atomic assignment
            inside that helper discards the previous ``FeaturesOA``.

        See Also:
            GetFeatures, CreateFeatureBased, GetType
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(nc_or_hvo, "nc_or_hvo")
        self._ValidateParam(specs, "specs")

        nc = self.__GetNaturalClassObject(nc_or_hvo)

        if not hasattr(nc, "FeaturesOA"):
            name_text = ITsString(
                nc.Name.get_String(self.project.project.DefaultAnalWs)
            ).Text or "(unnamed)"
            raise FP_ParameterError(
                f"Natural class '{name_text}' is not feature-based "
                f"(class={nc.ClassName}); SetFeatures only works on "
                f"IPhNCFeatures."
            )

        # MakeFeatStruc attaches the new struct to nc.FeaturesOA BEFORE
        # populating FeatureSpecsOC. LCM owning-atomic assignment inside
        # MakeFeatStruc discards the previous FeaturesOA.
        self.project.PhonFeatures.MakeFeatStruc(specs, owner=nc)

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project synchronization.

        Args:
            item: The IPhNaturalClass object.

        Returns:
            dict: Dictionary mapping property names to their values.
                Keys are property names, values are the property values.

        Example:
            >>> ncOps = NaturalClassOperations(project)
            >>> nc = list(ncOps.GetAll())[0]
            >>> props = ncOps.GetSyncableProperties(nc)
            >>> print(props.keys())
            dict_keys(['Name', 'Abbreviation', 'Description', 'PhonemeGuids'])

        Notes:
            - Returns all MultiString properties (all writing systems)
            - Returns PhonemeGuids as list of GUID strings (SegmentsRC members)
            - Does not include GUID or HVO of the natural class itself
        """
        nc = self.__GetNaturalClassObject(item)

        # Get all writing systems for MultiString properties
        # Fix: ILgWritingSystemFactory does not expose a .WritingSystems
        # property; enumerate via the wrapper's WritingSystemOperations.GetAll(),
        # which returns CoreWritingSystemDefinition objects with .Id / .Handle.
        all_ws = {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()}

        props = {}

        # MultiString properties
        for prop_name in ["Name", "Abbreviation", "Description"]:
            if hasattr(nc, prop_name):
                prop_obj = getattr(nc, prop_name)
                ws_values = {}
                for ws_id, ws_handle in all_ws.items():
                    text = ITsString(prop_obj.get_String(ws_handle)).Text
                    if text:  # Only include non-empty values
                        ws_values[ws_id] = text
                if ws_values:  # Only include property if it has values
                    props[prop_name] = ws_values

        # Reference Collection (RC) properties - return list of GUIDs
        if hasattr(nc, "SegmentsRC"):
            phoneme_guids = [str(phoneme.Guid) for phoneme in nc.SegmentsRC]
            if phoneme_guids:
                props["PhonemeGuids"] = phoneme_guids

        return props

    @OperationsMethod
    def ApplySyncableProperties(self, item, props, ws_map=None, fill_gaps=False):
        """Apply syncable properties (from GetSyncableProperties) onto an item.

        Inherited from BaseOperations; declared on the concrete class so static
        API indexers see it. The base implementation handles every property
        shape this class's GetSyncableProperties emits.
        """
        return super().ApplySyncableProperties(item, props, ws_map, fill_gaps=fill_gaps)

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two natural classes and return detailed differences.

        Args:
            item1: First natural class to compare (from source project).
            item2: Second natural class to compare (from target project).
            ops1: Optional NaturalClassOperations instance for item1's project.
                 Defaults to self.
            ops2: Optional NaturalClassOperations instance for item2's project.
                 Defaults to self.

        Returns:
            tuple: (is_different, differences) where:
                - is_different (bool): True if items differ
                - differences (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> nc1 = project1_ncOps.Find("Voiceless Stops")
            >>> nc2 = project2_ncOps.Find("Voiceless Stops")
            >>> is_diff, diffs = project1_ncOps.CompareTo(
            ...     nc1, nc2,
            ...     ops1=project1_ncOps,
            ...     ops2=project2_ncOps
            ... )
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} -> {val2}")

        Notes:
            - Compares all MultiString properties across all writing systems
            - Compares phoneme membership by GUID
            - Returns empty dict if items are identical
            - Handles cross-project comparison via ops1/ops2
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        # Get syncable properties from both items
        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        is_different = False
        differences = {}

        # Compare each property
        all_keys = set(props1.keys()) | set(props2.keys())
        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)

            # For PhonemeGuids, compare as sets (order doesn't matter)
            if key == "PhonemeGuids":
                set1 = set(val1) if val1 else set()
                set2 = set(val2) if val2 else set()
                if set1 != set2:
                    is_different = True
                    differences[key] = (val1, val2)
            else:
                # For other properties, direct comparison
                if val1 != val2:
                    is_different = True
                    differences[key] = (val1, val2)

        return (is_different, differences)
