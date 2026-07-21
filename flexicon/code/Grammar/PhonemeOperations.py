#
#   PhonemeOperations.py
#
#   Class: PhonemeOperations
#          Phoneme operations for FieldWorks Language Explorer
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
    IPhPhoneme,
    IPhPhonemeFactory,
    IPhCode,
    IPhCodeFactory,
    IFsFeatStruc,
    IFsFeatStrucFactory,
    IFsClosedFeature,
    IFsClosedValue,
    IFsClosedValueFactory,
    ICmObjectRepository,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# .NET Guid for GUID-aligned FeaturesOA rewiring during sync.
import System


# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# Import string utilities
from ..Shared.string_utils import normalize_text, normalize_match_key

# Catalog parsing helpers (Phase 6d)
from ..Shared.catalog import (
    CatalogImportResult,
    find_catalog_file,
    parse_basic_ipa_info,
    parse_etic_gloss_list,
)


# Canonical relative subdir for the BasicIPAInfo catalog under FWCodeDir.
BASIC_IPA_CATALOG_FILENAME = "BasicIPAInfo.xml"
BASIC_IPA_CATALOG_SUBDIR = "Templates"

# PhonFeats catalog (BasicIPAInfo cross-references its feature/value ids).
PHON_FEATS_CATALOG_FILENAME = "PhonFeatsEticGlossList.xml"
PHON_FEATS_CATALOG_SUBDIR = "Language Explorer/MGA/GlossLists"


class PhonemeOperations(BaseOperations):
    """
    This class provides operations for managing Phonemes in a FieldWorks project.

    Phonemes are the minimal distinctive units of sound in a language. For example,
    in English, /p/ and /b/ are distinct phonemes because they distinguish words
    like "pat" and "bat".

    Usage::

        from flexlibs2 import FLExProject, PhonemeOperations

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        phonemeOps = PhonemeOperations(project)

        # Get all phonemes
        for phoneme in phonemeOps.GetAll():
            print(phonemeOps.GetRepresentation(phoneme))

        # Create a new phoneme
        p_phoneme = phonemeOps.Create("/p/")
        phonemeOps.SetDescription(p_phoneme, "voiceless bilabial stop")

        # Find and update
        b_phoneme = phonemeOps.Find("/b/")
        if b_phoneme:
            phonemeOps.SetDescription(b_phoneme, "voiced bilabial stop")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize PhonemeOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for phonemes.
        For Phoneme, we reorder parent.PhonemesOS
        """
        return parent.PhonemesOS

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all phonemes in the project.

        Returns:
            EnumerableWrapper[IPhPhoneme]: Each phoneme object in the project's phoneme inventory.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> for phoneme in phonemeOps.GetAll():
            ...     representation = phonemeOps.GetRepresentation(phoneme)
            ...     description = phonemeOps.GetDescription(phoneme)
            ...     print(f"{representation}: {description}")
            /p/: voiceless bilabial stop
            /b/: voiced bilabial stop
            /t/: voiceless alveolar stop
            /d/: voiced alveolar stop

        Notes:
            - Returns phonemes from the first phoneme set
            - Returns empty if no phoneme sets exist
            - Most projects have only one phoneme set
            - Phonemes include both consonants and vowels

        See Also:
            Find, GetRepresentation
        """
        phon_data = self.project.lp.PhonologicalDataOA
        if phon_data and phon_data.PhonemeSetsOS.Count > 0:
            phoneme_set = phon_data.PhonemeSetsOS[0]
            for phoneme in phoneme_set.PhonemesOC:
                yield phoneme

    @OperationsMethod
    def Create(self, representation, wsHandle=None):
        """
        Create a new phoneme.

        Args:
            representation (str): The phonemic representation (e.g., "/p/", "/a/").
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            IPhPhoneme: The newly created phoneme object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If representation is None.
            FP_ParameterError: If representation is empty, or if a phoneme
                with this representation already exists, or if no phoneme set exists.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> p_phoneme = phonemeOps.Create("/p/")
            >>> print(phonemeOps.GetRepresentation(p_phoneme))
            /p/

            >>> # Create with description
            >>> ch_phoneme = phonemeOps.Create("/tʃ/")
            >>> phonemeOps.SetDescription(ch_phoneme, "voiceless postalveolar affricate")

        Notes:
            - Representation should use IPA symbols
            - Standard convention is to enclose in slashes: /p/
            - Phoneme must be unique within the phoneme set
            - Requires at least one phoneme set to exist in the project

        See Also:
            Delete, Exists, Find
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(representation, "representation")

        if not representation or not representation.strip():
            raise FP_ParameterError("Representation cannot be empty")

        # Check if phoneme already exists
        if self.Exists(representation, wsHandle):
            raise FP_ParameterError(f"Phoneme '{representation}' already exists")

        # Get or create phoneme set
        phon_data = self.project.lp.PhonologicalDataOA
        if not phon_data:
            raise FP_ParameterError("No phonological data in project")

        if phon_data.PhonemeSetsOS.Count == 0:
            raise FP_ParameterError("No phoneme set exists in project")

        phoneme_set = phon_data.PhonemeSetsOS[0]

        # Get the writing system handle
        wsHandle = self.__WSHandle(wsHandle)

        # Create the new phoneme using the factory
        factory = self.project.project.ServiceLocator.GetService(IPhPhonemeFactory)

        with self._TransactionCM(f"Create phoneme {representation}"):
            new_phoneme = factory.Create()

            # Add to the phoneme set (must be done before setting properties)
            phoneme_set.PhonemesOC.Add(new_phoneme)

            # Set representation
            mkstr = TsStringUtils.MakeString(representation, wsHandle)
            new_phoneme.Name.set_String(wsHandle, mkstr)

            # The IPhPhoneme factory autocreates one IPhCode whose Representation
            # is the FLEx null marker ('***'). Clean it up here so that Create()
            # always returns a phoneme with no junk placeholder allophone.
            # AddCode reuses the placeholder slot on the first call, but if the
            # caller never calls AddCode the phoneme would otherwise carry a
            # spurious '***' code that breaks HermitCrab parser loading.
            # (issue #113 -- cleanup moved here from AddCode)
            existing_codes = list(new_phoneme.CodesOS)
            if len(existing_codes) == 1 and self.__is_placeholder_code(existing_codes[0]):
                new_phoneme.CodesOS.Remove(existing_codes[0])

            return new_phoneme

    @OperationsMethod
    def Delete(self, phoneme_or_hvo):
        """
        Delete a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If phoneme_or_hvo is None.
            FP_ParameterError: If the phoneme is in use and cannot be deleted.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> obsolete = phonemeOps.Find("/x/")
            >>> if obsolete:
            ...     phonemeOps.Delete(obsolete)

        Warning:
            - Deleting a phoneme that is in use may raise an error from FLEx
            - This includes phonemes used in:
              - Natural classes
              - Phonological rules
              - Allomorph environments
            - Deletion is permanent and cannot be undone
            - Consider updating references before deletion

        See Also:
            Create, Exists, Find
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")

        # Resolve to phoneme object
        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)

        # Get phoneme set and remove
        phon_data = self.project.lp.PhonologicalDataOA
        if phon_data and phon_data.PhonemeSetsOS.Count > 0:
            phoneme_set = phon_data.PhonemeSetsOS[0]
            phoneme_set.PhonemesOC.Remove(phoneme)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True, deep=True):
        """
        Duplicate a phoneme, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The IPhPhoneme object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source phoneme.
                                If False, insert at end of phoneme set.
            deep (bool): If True (default), also duplicate owned objects (codes/allophones).
                        If False, only copy simple properties and references.

        Returns:
            IPhPhoneme: The newly created duplicate phoneme with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.
            FP_ParameterError: If no phoneme set exists.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> p_phoneme = phonemeOps.Find("/p/")
            >>> if p_phoneme:
            ...     # Duplicate phoneme (deep - includes allophonic codes)
            ...     dup = phonemeOps.Duplicate(p_phoneme)
            ...     print(f"Original: {phonemeOps.GetGuid(dup)}")
            ...     print(f"Representation: {phonemeOps.GetRepresentation(dup)}")
            ...
            ...     # Shallow duplicate (no codes)
            ...     shallow_dup = phonemeOps.Duplicate(p_phoneme, deep=False)
            ...     codes = phonemeOps.GetCodes(deep_dup)
            ...     print(f"Codes: {len(codes)}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original phoneme's position
            - Simple properties copied: Name (representation), Description, BasicIPASymbol
            - Reference properties copied: FeaturesOA (feature structure reference)
            - Owned objects (deep=True): CodesOS (allophonic representations)
            - Useful for creating similar phonemes or phoneme variants

        See Also:
            Create, Delete, GetGuid, GetCodes
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source phoneme
        source = self.__GetPhonemeObject(item_or_hvo)

        # Get phoneme set
        phon_data = self.project.lp.PhonologicalDataOA
        if not phon_data or phon_data.PhonemeSetsOS.Count == 0:
            raise FP_ParameterError("No phoneme set exists in project")
        phoneme_set = phon_data.PhonemeSetsOS[0]

        # Create new phoneme using factory (auto-generates new GUID)
        factory = self.project.project.ServiceLocator.GetService(IPhPhonemeFactory)

        with self._TransactionCM("Duplicate phoneme"):
            duplicate = factory.Create()

            # Add to phoneme set (OC types use Add only, no Insert)
            phoneme_set.PhonemesOC.Add(duplicate)

            # Copy simple MultiString properties
            duplicate.Name.CopyAlternatives(source.Name)
            duplicate.Description.CopyAlternatives(source.Description)
            if hasattr(source, "BasicIPASymbol") and source.BasicIPASymbol:
                duplicate.BasicIPASymbol.CopyAlternatives(source.BasicIPASymbol)

            # Note: FeaturesOA is an owned atomic object (OA), NOT a reference.
            # Assigning it directly would TRANSFER ownership from source, corrupting it.
            # Feature structures are complex (recursive), so we skip them in shallow
            # copy and handle via deep copy below using LCM's SetCloneProperties.

            # Handle owned objects if deep=True
            if deep:
                from ..lcm_casting import clone_properties

                # Deep copy FeaturesOA (feature structure)
                if hasattr(source, "FeaturesOA") and source.FeaturesOA:
                    # Create new feature structure and copy all properties
                    try:
                        source_features = source.FeaturesOA
                        # Create new object of same type
                        new_features = self.project.project.ServiceLocator.ObjectRepository.NewObject(
                            source_features.ClassID
                        )

                        # Set as the feature structure for this phoneme
                        duplicate.FeaturesOA = new_features

                        # Deep clone all properties using clone_properties
                        clone_properties(source_features, new_features, self.project)
                    except Exception:
                        # Cannot copy complex feature structure - skip
                        pass

                # Duplicate codes (allophonic representations)
                if hasattr(source, "CodesOS") and source.CodesOS.Count > 0:
                    for code in source.CodesOS:
                        try:
                            code_factory = self.project.project.ServiceLocator.GetService(IPhCodeFactory)
                            new_code = code_factory.Create()
                            duplicate.CodesOS.Add(new_code)
                            # Deep clone code properties using clone_properties
                            clone_properties(code, new_code, self.project)
                        except Exception:
                            # Skip any code that fails to copy
                            pass

            return duplicate

    @OperationsMethod
    def Exists(self, representation, wsHandle=None):
        """
        Check if a phoneme with the given representation exists.

        Args:
            representation (str): The representation to search for (case-sensitive).
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            bool: True if phoneme exists, False otherwise.

        Raises:
            FP_NullParameterError: If representation is None.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> if not phonemeOps.Exists("/ŋ/"):
            ...     phonemeOps.Create("/ŋ/")
            ...     phonemeOps.SetDescription(phonemeOps.Find("/ŋ/"), "velar nasal")

        Notes:
            - Comparison is case-sensitive (IPA is case-sensitive)
            - Use Find() to get the actual object

        See Also:
            Find, Create
        """
        self._ValidateParam(representation, "representation")

        return self.Find(representation, wsHandle) is not None

    @OperationsMethod
    def Find(self, representation, wsHandle=None):
        """
        Find a phoneme by representation.

        Args:
            representation (str): The representation to search for (case-sensitive).
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            IPhPhoneme or None: The phoneme object if found, None otherwise.

        Raises:
            FP_NullParameterError: If representation is None.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> p_phoneme = phonemeOps.Find("/p/")
            >>> if p_phoneme:
            ...     desc = phonemeOps.GetDescription(p_phoneme)
            ...     print(f"/p/: {desc}")
            /p/: voiceless bilabial stop

        Notes:
            - Returns first match only
            - Search is case-sensitive (IPA is case-sensitive)
            - Returns None if not found (doesn't raise exception)

        See Also:
            Exists, GetRepresentation
        """
        self._ValidateParam(representation, "representation")

        wsHandle = self.__WSHandle(wsHandle)

        phon_data = self.project.lp.PhonologicalDataOA
        if not phon_data or phon_data.PhonemeSetsOS.Count == 0:
            return None

        phoneme_set = phon_data.PhonemeSetsOS[0]
        target = normalize_match_key(representation, casefold=False)
        for phoneme in phoneme_set.PhonemesOC:
            phoneme_repr = ITsString(phoneme.Name.get_String(wsHandle)).Text
            if normalize_match_key(phoneme_repr, casefold=False) == target:
                return phoneme

        return None

    @OperationsMethod
    def GetRepresentation(self, phoneme_or_hvo, wsHandle=None):
        """
        Get the representation of a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            str: The phoneme representation, or empty string if not set.

        Raises:
            FP_NullParameterError: If phoneme_or_hvo is None.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> p_phoneme = phonemeOps.Find("/p/")
            >>> representation = phonemeOps.GetRepresentation(p_phoneme)
            >>> print(representation)
            /p/

            >>> # Iterate and print all phonemes
            >>> for phoneme in phonemeOps.GetAll():
            ...     print(phonemeOps.GetRepresentation(phoneme))

        See Also:
            SetRepresentation, GetDescription
        """
        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        representation = normalize_text(ITsString(phoneme.Name.get_String(wsHandle)).Text)
        return representation or ""

    @OperationsMethod
    def SetRepresentation(self, phoneme_or_hvo, representation, wsHandle=None):
        """
        Set the representation of a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.
            representation (str): The new representation.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If phoneme_or_hvo or representation is None.
            FP_ParameterError: If representation is empty.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> phoneme = phonemeOps.Find("/ph/")  # non-standard notation
            >>> if phoneme:
            ...     phonemeOps.SetRepresentation(phoneme, "/pʰ/")  # fix to proper IPA

        Notes:
            - Use standard IPA symbols for cross-linguistic compatibility
            - Consider updating descriptions when changing representation

        See Also:
            GetRepresentation, SetDescription
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")
        self._ValidateParam(representation, "representation")

        if not representation or not representation.strip():
            raise FP_ParameterError("Representation cannot be empty")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(representation, wsHandle)
        phoneme.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetDescription(self, phoneme_or_hvo, wsHandle=None):
        """
        Get the description of a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The phoneme description, or empty string if not set.

        Raises:
            FP_NullParameterError: If phoneme_or_hvo is None.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> p_phoneme = phonemeOps.Find("/p/")
            >>> desc = phonemeOps.GetDescription(p_phoneme)
            >>> print(desc)
            voiceless bilabial stop

            >>> # Print phoneme inventory with descriptions
            >>> for phoneme in phonemeOps.GetAll():
            ...     repr = phonemeOps.GetRepresentation(phoneme)
            ...     desc = phonemeOps.GetDescription(phoneme)
            ...     print(f"{repr}: {desc}")
            /p/: voiceless bilabial stop
            /b/: voiced bilabial stop
            /t/: voiceless alveolar stop

        Notes:
            - Description typically includes articulatory features
            - Returns empty string if no description set
            - Uses analysis writing system by default (not vernacular)

        See Also:
            SetDescription, GetRepresentation
        """
        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)

        # Use analysis WS for description (not vernacular)
        if wsHandle is None:
            wsHandle = self.project.project.DefaultAnalWs
        else:
            wsHandle = self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

        desc_str = ITsString(phoneme.Description.get_String(wsHandle)).Text
        return desc_str or ""

    @OperationsMethod
    def SetDescription(self, phoneme_or_hvo, description, wsHandle=None):
        """
        Set the description of a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.
            description (str): The new description.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If phoneme_or_hvo or description is None.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> p_phoneme = phonemeOps.Create("/p/")
            >>> phonemeOps.SetDescription(p_phoneme, "voiceless bilabial stop")

            >>> # Add detailed articulatory description
            >>> tap = phonemeOps.Find("/ɾ/")
            >>> phonemeOps.SetDescription(
            ...     tap,
            ...     "voiced alveolar tap/flap - allophone of /r/ in intervocalic position"
            ... )

        Notes:
            - Description is optional but recommended for documentation
            - Use standard phonetic terminology
            - Can include information about allophones and distribution
            - Uses analysis writing system by default (not vernacular)
            - Description can be empty string to clear

        See Also:
            GetDescription, SetRepresentation
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")
        self._ValidateParam(description, "description")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)

        # Use analysis WS for description (not vernacular)
        if wsHandle is None:
            wsHandle = self.project.project.DefaultAnalWs
        else:
            wsHandle = self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

        mkstr = TsStringUtils.MakeString(description, wsHandle)
        phoneme.Description.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetFeatures(self, phoneme_or_hvo):
        """
        Get the feature structure of a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.

        Returns:
            IFsFeatStruc or None: The phoneme's feature structure, or None if not set.

        Raises:
            FP_NullParameterError: If phoneme_or_hvo is None.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> p_phoneme = phonemeOps.Find("/p/")
            >>> features = phonemeOps.GetFeatures(p_phoneme)
            >>> if features:
            ...     print(f"Feature structure: {features.Hvo}")
            ... else:
            ...     print("No features defined")

        Notes:
            - Feature structures define distinctive phonological properties
            - Used in phonological rules and natural class definitions
            - Feature system must be defined in project settings
            - Returns None if no features are set
            - Returns the IFsFeatStruc object for further manipulation

        See Also:
            GetRepresentation, GetDescription
        """
        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)
        return phoneme.FeaturesOA if phoneme.FeaturesOA else None

    # --- Advanced Operations ---

    @OperationsMethod
    def GetCodes(self, phoneme_or_hvo):
        """
        Get all codes (allophonic representations) for a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.

        Returns:
            list: List of IPhCode objects (empty list if none).

        Raises:
            FP_NullParameterError: If phoneme_or_hvo is None.

        Example:
            >>> # Get allophones of /t/
            >>> phoneme = project.Phonemes.Find("/t/")
            >>> if phoneme:
            ...     codes = project.Phonemes.GetCodes(phoneme)
            ...     for code in codes:
            ...         ws = project.project.DefaultVernWs
            ...         repr = ITsString(code.Representation.get_String(ws)).Text
            ...         print(repr)
            [t]   # plain voiceless alveolar stop
            [tʰ]  # aspirated (word-initial)
            [ɾ]   # flap (intervocalic)

            >>> # Get vowel allophones
            >>> phoneme = project.Phonemes.Find("/i/")
            >>> if phoneme:
            ...     codes = project.Phonemes.GetCodes(phoneme)
            ...     print(f"Phoneme /i/ has {len(codes)} allophonic codes")

        Notes:
            - Codes represent allophones or context-specific realizations
            - Convention is to use square brackets [p] for phones
            - Slashes /p/ for phonemes
            - Empty list if no codes defined

        See Also:
            AddCode, RemoveCode
        """
        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)
        return list(phoneme.CodesOS)

    @OperationsMethod
    def AddCode(self, phoneme_or_hvo, representation, wsHandle=None):
        """
        Add a code (allophonic representation) to a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.
            representation: The code representation (e.g., "[tʰ]", "[ɾ]").
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            IPhCode: The newly created code object.

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If phoneme_or_hvo or representation is None.
            FP_ParameterError: If representation is empty.

        Example:
            >>> # Add aspiration allophone
            >>> phoneme = project.Phonemes.Find("/p/")
            >>> if phoneme:
            ...     code = project.Phonemes.AddCode(phoneme, "[pʰ]")

            >>> # Add multiple allophones for /t/
            >>> phoneme = project.Phonemes.Find("/t/")
            >>> if phoneme:
            ...     project.Phonemes.AddCode(phoneme, "[t]")   # plain
            ...     project.Phonemes.AddCode(phoneme, "[tʰ]")  # aspirated
            ...     project.Phonemes.AddCode(phoneme, "[ɾ]")   # flap

            >>> # Add vowel allophones
            >>> phoneme = project.Phonemes.Find("/a/")
            >>> if phoneme:
            ...     project.Phonemes.AddCode(phoneme, "[a]")   # open front
            ...     project.Phonemes.AddCode(phoneme, "[ɑ]")   # open back

        Notes:
            - Use square brackets [p] for phones (allophones)
            - Each code can have its own feature specifications
            - Codes are used in phonological rule environments
            - Duplicates are allowed (same code can be added multiple times)

        See Also:
            GetCodes, RemoveCode
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")
        self._ValidateParam(representation, "representation")

        if not representation or not representation.strip():
            raise FP_ParameterError("Representation cannot be empty")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)
        mkstr = TsStringUtils.MakeString(representation, wsHandle)

        # Create + append a new IPhCode. The factory-autocreated placeholder
        # code ('***') is now removed by Create() before it returns, so
        # AddCode always operates on a clean CodesOS and can unconditionally
        # append. (issue #113 -- placeholder cleanup moved to Create)
        factory = self.project.project.ServiceLocator.GetService(IPhCodeFactory)

        with self._TransactionCM("Add phoneme code"):
            code = factory.Create()

            # Add to phoneme's codes (must be done before setting properties)
            phoneme.CodesOS.Add(code)

            # Set representation
            code.Representation.set_String(wsHandle, mkstr)

            return code

    @OperationsMethod
    def RemoveCode(self, phoneme_or_hvo, code_or_hvo):
        """
        Remove a code from a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.
            code_or_hvo: The IPhCode object or HVO to remove.

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If phoneme_or_hvo or code_or_hvo is None.
            FP_ParameterError: If the code is not in the phoneme's code list.

        Example:
            >>> phoneme = project.Phonemes.Find("/t/")
            >>> if phoneme:
            ...     codes = project.Phonemes.GetCodes(phoneme)
            ...     # Remove the flap allophone
            ...     for code in codes:
            ...         ws = project.project.DefaultVernWs
            ...         repr = ITsString(code.Representation.get_String(ws)).Text
            ...         if repr == "[ɾ]":
            ...             project.Phonemes.RemoveCode(phoneme, code)
            ...             break

            >>> # Remove by HVO
            >>> phoneme = project.Phonemes.Find("/p/")
            >>> if phoneme:
            ...     codes = project.Phonemes.GetCodes(phoneme)
            ...     if codes:
            ...         project.Phonemes.RemoveCode(phoneme, codes[0].Hvo)

        Notes:
            - Code object must be from the phoneme's CodesOS collection
            - Use GetCodes() to find codes to remove
            - Accepts either IPhCode object or HVO

        See Also:
            GetCodes, AddCode
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")
        self._ValidateParam(code_or_hvo, "code_or_hvo")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)
        code = self.__GetCodeObject(code_or_hvo)

        # Check if code is in the phoneme's codes
        if code not in phoneme.CodesOS:
            raise FP_ParameterError("Code not found in phoneme's code list")

        phoneme.CodesOS.Remove(code)

    @OperationsMethod
    def FindCode(self, phoneme_or_hvo, representation, wsHandle=None):
        """
        Find a code (allophonic representation) on a phoneme by its
        rendered representation string.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.
            representation (str): The code representation to look up,
                e.g. ``"[tʰ]"``. Compared via NFD-normalised match
                (no casefold; IPA distinctions are case-sensitive).
            wsHandle: Optional writing system handle. Defaults to
                vernacular WS.

        Returns:
            IPhCode or None: The matching code object, or None if no
            code on this phoneme renders to ``representation``.

        Raises:
            FP_NullParameterError: If phoneme_or_hvo or representation
                is None.

        Example:
            >>> phoneme = project.Phonemes.Find("/t/")
            >>> aspirated = project.Phonemes.FindCode(phoneme, "[tʰ]")
            >>> if aspirated is not None:
            ...     # safe to ReplaceCode or RemoveCode it
            ...     pass

        Notes:
            - Match is case-sensitive (IPA is case-sensitive) but
              NFD-normalised so combining-diacritic encoding doesn't
              cause false negatives.
            - Returns the first match; codes don't have to be unique by
              representation but typically are.

        See Also:
            AddCode, RemoveCode, ReplaceCode, GetCodes
        """
        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")
        self._ValidateParam(representation, "representation")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)
        ws = self.__WSHandle(wsHandle)

        target = normalize_match_key(representation, casefold=False)
        for code in phoneme.CodesOS:
            code_repr = ITsString(code.Representation.get_String(ws)).Text
            if code_repr is None:
                continue
            if normalize_match_key(code_repr, casefold=False) == target:
                return code
        return None

    @OperationsMethod
    def ReplaceCode(self, phoneme_or_hvo, old_code_or_repr, new_representation, wsHandle=None):
        """
        Replace one code's representation on a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.
            old_code_or_repr: Either an IPhCode object on this phoneme,
                an HVO, or a string representation to look up via
                FindCode().
            new_representation (str): The replacement representation,
                e.g. ``"[dʰ]"``.
            wsHandle: Optional writing system handle. Defaults to
                vernacular WS.

        Returns:
            IPhCode: The newly created code carrying ``new_representation``.

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If any required parameter is None.
            FP_ParameterError: If ``old_code_or_repr`` is a string and
                no matching code is found on the phoneme.

        Example:
            >>> phoneme = project.Phonemes.Find("/t/")
            >>> # Fix an encoding typo: replace "[ts]" with the proper
            >>> # affricate "[t͡s]".
            >>> project.Phonemes.ReplaceCode(phoneme, "[ts]", "[t͡s]")

        Notes:
            - Implementation is RemoveCode + AddCode: any references to
              the original IPhCode object are dropped. If you need to
              preserve references, mutate the Representation multistring
              directly instead.
            - Returns the new IPhCode (not the old one).

        See Also:
            AddCode, RemoveCode, FindCode, GetCodes
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")
        self._ValidateParam(old_code_or_repr, "old_code_or_repr")
        self._ValidateParam(new_representation, "new_representation")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)

        if isinstance(old_code_or_repr, str):
            target = self.FindCode(phoneme, old_code_or_repr, wsHandle)
            if target is None:
                raise FP_ParameterError(
                    f"No code matching '{old_code_or_repr}' found on phoneme"
                )
        else:
            target = old_code_or_repr

        with self._TransactionCM("Replace phoneme code"):
            self.RemoveCode(phoneme, target)
            return self.AddCode(phoneme, new_representation, wsHandle)

    @OperationsMethod
    def GetBasicIPASymbol(self, phoneme_or_hvo, wsHandle=None):
        """
        Get the basic IPA symbol for a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            str: The basic IPA symbol, or empty string if not set.

        Raises:
            FP_NullParameterError: If phoneme_or_hvo is None.

        Example:
            >>> phoneme = project.Phonemes.Find("/p/")
            >>> if phoneme:
            ...     symbol = project.Phonemes.GetBasicIPASymbol(phoneme)
            ...     print(symbol)
            p

            >>> # Compare representation with basic IPA
            >>> phoneme = project.Phonemes.Find("/tʃ/")
            >>> if phoneme:
            ...     repr = project.Phonemes.GetRepresentation(phoneme)
            ...     ipa = project.Phonemes.GetBasicIPASymbol(phoneme)
            ...     print(f"Representation: {repr}, IPA: {ipa}")
            Representation: /tʃ/, IPA: tʃ

        Notes:
            - Returns the IPA symbol without slashes or diacritics
            - May differ from representation which can include slashes
            - Used for cross-linguistic phoneme identification
            - May be empty if not set
            - ``BasicIPASymbol``'s LCM type varies: in some builds it is
              IMultiString (per-WS), in others a scalar ITsString. This
              getter tries the multistring ``get_String`` accessor first
              and falls back to reading the property directly as an
              ITsString (matching the defensive write pattern in
              SetBasicIPASymbol).
            - BasicIPASymbol property may not be available in all FLEx versions

        See Also:
            GetRepresentation
        """
        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)
        ws = self.__WSHandle(wsHandle)

        if not hasattr(phoneme, "BasicIPASymbol") or not phoneme.BasicIPASymbol:
            return ""

        target = phoneme.BasicIPASymbol
        if hasattr(target, "get_String"):
            # MultiString shape: per-WS read. Matches the write pattern
            # in SetBasicIPASymbol (which calls .set_String(ws, tss)).
            tss = target.get_String(ws)
        else:
            # Scalar ITsString shape: the property value IS the ITsString.
            tss = target
        ipa_str = ITsString(tss).Text
        return ipa_str or ""

    @OperationsMethod
    def SetBasicIPASymbol(self, phoneme_or_hvo, ipa, wsHandle=None):
        """
        Set the basic IPA symbol for a phoneme.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.
            ipa (str): The IPA symbol to set, e.g. ``"p"``, ``"tʃ"``.
            wsHandle: Optional writing system handle. Defaults to
                vernacular WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with writeEnabled=True.
            FP_NullParameterError: If phoneme_or_hvo or ipa is None.

        Example:
            >>> phoneme = project.Phonemes.Find("/p/")
            >>> project.Phonemes.SetBasicIPASymbol(phoneme, "p")
            >>> assert project.Phonemes.GetBasicIPASymbol(phoneme) == "p"

        Notes:
            - ``BasicIPASymbol`` is typed as IMultiUnicode / IMultiString
              in the LCM builds we ship against (matches the multistring
              read pattern in GetBasicIPASymbol). Older issue tracking
              describes it as ITsString-only, so this setter tries the
              standard multistring write first and falls back to a
              scalar set_BasicIPASymbol if the multistring API is not
              present.
            - Empty / whitespace-only strings are permitted: FW itself
              treats unset IPA as "" and round-trips correctly.

        See Also:
            GetBasicIPASymbol
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")
        self._ValidateParam(ipa, "ipa")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)
        ws = self.__WSHandle(wsHandle)

        tss = TsStringUtils.MakeString(ipa, ws)
        target = phoneme.BasicIPASymbol
        if hasattr(target, "set_String"):
            # MultiString shape: per-WS write. This matches the read
            # pattern in GetBasicIPASymbol (which calls .get_String(ws)).
            target.set_String(ws, tss)
        else:
            # Scalar ITsString shape: assign via the property setter on
            # the interface view. Cast to IPhPhoneme to surface the
            # explicit-interface setter if pythonnet hid it on the base.
            IPhPhoneme(phoneme).set_BasicIPASymbol(tss)

    @OperationsMethod
    def IsVowel(self, phoneme_or_hvo):
        """
        Check if a phoneme is classified as a vowel.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.

        Returns:
            bool: True if the phoneme is a vowel, False otherwise.

        Raises:
            FP_NullParameterError: If phoneme_or_hvo is None.

        Example:
            >>> # Filter vowels from phoneme inventory
            >>> vowels = []
            >>> for phoneme in project.Phonemes.GetAll():
            ...     if project.Phonemes.IsVowel(phoneme):
            ...         vowels.append(project.Phonemes.GetRepresentation(phoneme))
            >>> print("Vowels:", ", ".join(vowels))
            Vowels: /a/, /e/, /i/, /o/, /u/

            >>> # Count vowels vs consonants
            >>> vowel_count = 0
            >>> for phoneme in project.Phonemes.GetAll():
            ...     if project.Phonemes.IsVowel(phoneme):
            ...         vowel_count += 1
            >>> print(f"Total vowels: {vowel_count}")

        Notes:
            - Classification based on feature structure
            - Typically checks for [-consonantal, +sonorant] or [+syllabic] features
            - May return False if features not properly set
            - Feature analysis depends on project's feature system
            - Checks for common vowel feature indicators like 'syllabic', 'vocalic', 'vowel'

        See Also:
            IsConsonant, GetFeatures
        """
        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)

        # Check feature structure for vowel features
        if not hasattr(phoneme, "FeaturesOA") or not phoneme.FeaturesOA:
            return False

        features = phoneme.FeaturesOA

        # Check for typical vowel features
        # Feature system varies by project, but common vowel features include:
        # [-consonantal], [+sonorant], [+syllabic]
        if hasattr(features, "FeatureSpecsOC"):
            for spec in features.FeatureSpecsOC:
                if hasattr(spec, "FeatureRA") and spec.FeatureRA:
                    feature_name = ""
                    if hasattr(spec.FeatureRA, "Name"):
                        ws = self.project.project.DefaultAnalWs
                        feature_name = ITsString(spec.FeatureRA.Name.get_String(ws)).Text or ""

                    # Check for common vowel feature indicators
                    if feature_name.lower() in ["syllabic", "vocalic", "vowel"]:
                        # Check if feature value is positive
                        if hasattr(spec, "ValueRA") and spec.ValueRA:
                            return True

        return False

    @OperationsMethod
    def IsConsonant(self, phoneme_or_hvo):
        """
        Check if a phoneme is classified as a consonant.

        Args:
            phoneme_or_hvo: The IPhPhoneme object or HVO.

        Returns:
            bool: True if the phoneme is a consonant, False otherwise.

        Raises:
            FP_NullParameterError: If phoneme_or_hvo is None.

        Example:
            >>> # Filter consonants from phoneme inventory
            >>> consonants = []
            >>> for phoneme in project.Phonemes.GetAll():
            ...     if project.Phonemes.IsConsonant(phoneme):
            ...         consonants.append(project.Phonemes.GetRepresentation(phoneme))
            >>> print("Consonants:", ", ".join(consonants))
            Consonants: /p/, /t/, /k/, /b/, /d/, /g/, /m/, /n/

            >>> # Create consonant natural classes
            >>> for phoneme in project.Phonemes.GetAll():
            ...     if project.Phonemes.IsConsonant(phoneme):
            ...         desc = project.Phonemes.GetDescription(phoneme)
            ...         repr = project.Phonemes.GetRepresentation(phoneme)
            ...         print(f"{repr}: {desc}")

        Notes:
            - Classification based on feature structure
            - Typically checks for [+consonantal] or [-syllabic] features
            - May return False if features not properly set
            - Complementary to IsVowel() but not necessarily opposite
              (some sounds like glides may be neither or both)
            - Checks for common consonant feature indicators like 'consonantal', 'consonant'

        See Also:
            IsVowel, GetFeatures
        """
        self._ValidateParam(phoneme_or_hvo, "phoneme_or_hvo")

        phoneme = self.__GetPhonemeObject(phoneme_or_hvo)

        # Check feature structure for consonant features
        if not hasattr(phoneme, "FeaturesOA") or not phoneme.FeaturesOA:
            return False

        features = phoneme.FeaturesOA

        # Check for typical consonant features
        # Feature system varies by project, but common consonant features include:
        # [+consonantal], [-syllabic]
        if hasattr(features, "FeatureSpecsOC"):
            for spec in features.FeatureSpecsOC:
                if hasattr(spec, "FeatureRA") and spec.FeatureRA:
                    feature_name = ""
                    if hasattr(spec.FeatureRA, "Name"):
                        ws = self.project.project.DefaultAnalWs
                        feature_name = ITsString(spec.FeatureRA.Name.get_String(ws)).Text or ""

                    # Check for common consonant feature indicators
                    if feature_name.lower() in ["consonantal", "consonant"]:
                        # Check if feature value is positive
                        if hasattr(spec, "ValueRA") and spec.ValueRA:
                            return True

        return False

    # --- Private Helper Methods ---

    def __GetPhonemeObject(self, phoneme_or_hvo):
        """
        Resolve HVO or object to IPhPhoneme.

        Args:
            phoneme_or_hvo: Either an IPhPhoneme object or an HVO (int).

        Returns:
            IPhPhoneme: The resolved phoneme object.
        """
        if isinstance(phoneme_or_hvo, int):
            return self.project.Object(phoneme_or_hvo)
        return phoneme_or_hvo

    def __GetCodeObject(self, code_or_hvo):
        """
        Resolve HVO or object to IPhCode.

        Args:
            code_or_hvo: Either an IPhCode object or an HVO (int).

        Returns:
            IPhCode: The resolved code object.
        """
        if isinstance(code_or_hvo, int):
            return self.project.Object(code_or_hvo)
        return code_or_hvo

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project synchronization.

        Args:
            item: The IPhPhoneme object or HVO.

        Returns:
            dict: Dictionary mapping property names to their values. Shapes:

            - ``Name`` / ``Description`` / ``BasicIPASymbol``:
              ``{ws_id: text}`` multistring dicts (non-empty alts only).
            - ``FeaturesGuid``: ``str`` GUID of the owned IFsFeatStruc
              (retained for backward compatibility).
            - ``Features``: a list of ``{"FeatureGuid": str, "ValueGuid":
              str}`` specs — one per IFsClosedValue in the phoneme's
              ``FeaturesOA.FeatureSpecsOC`` — so a synced phoneme carries
              its phonological-feature values. The feature/value GUIDs let
              ApplySyncableProperties rewire the specs against the target
              project's (already-synced) feature system.

        Example:
            >>> phonemeOps = PhonemeOperations(project)
            >>> phoneme = list(phonemeOps.GetAll())[0]
            >>> props = phonemeOps.GetSyncableProperties(phoneme)
            >>> sorted(props.keys())
            ['BasicIPASymbol', 'Description', 'Features', 'FeaturesGuid', 'Name']

        Notes:
            - Returns all MultiString properties (all writing systems).
            - ``BasicIPASymbol``'s LCM type varies across builds (per-WS
              IMultiString in some, scalar ITsString in others); the read
              is guarded and handles both shapes, fixing the
              ``ITsString.get_String`` crash on the scalar build (issue
              #222).
            - Does not include CodesOS (owned allophonic codes).
            - Does not include the phoneme's own GUID or HVO.
        """
        phoneme = self.__GetPhonemeObject(item)

        # Enumerate writing systems via WritingSystemOperations.GetAll()
        # (ILgWritingSystemFactory has no .WritingSystems property).
        all_ws = {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()}

        props = {}

        # MultiString properties (Name = representation). Each read is
        # guarded so a single malformed alt or a variant BasicIPASymbol
        # shape cannot abort the whole extraction (issue #222).
        for prop_name in ("Name", "Description", "BasicIPASymbol"):
            ws_values = self.__ReadMultiString(phoneme, prop_name, all_ws)
            if ws_values:
                props[prop_name] = ws_values

        # Feature structure: retain FeaturesGuid for back-compat and surface
        # the (feature, value) specs so the phoneme carries its feature
        # values across the transfer (issue #222).
        if hasattr(phoneme, "FeaturesOA") and phoneme.FeaturesOA:
            features = phoneme.FeaturesOA
            props["FeaturesGuid"] = str(features.Guid)
            specs = []
            if hasattr(features, "FeatureSpecsOC"):
                for spec in features.FeatureSpecsOC:
                    try:
                        cv = IFsClosedValue(spec)
                        feat_ra = cv.FeatureRA
                        val_ra = cv.ValueRA
                    except Exception:
                        # Non-closed spec shape (e.g. complex value) — the
                        # phoneme feature model only uses closed values, so
                        # skip anything that isn't one.
                        continue
                    if feat_ra is None or val_ra is None:
                        continue
                    specs.append({
                        "FeatureGuid": str(feat_ra.Guid),
                        "ValueGuid": str(val_ra.Guid),
                    })
            if specs:
                props["Features"] = specs

        return props

    @OperationsMethod
    def ApplySyncableProperties(self, item, props, ws_map=None, fill_gaps=False):
        """Apply syncable properties (from GetSyncableProperties) onto a phoneme.

        Handles the multistring fields via the BaseOperations loop, applies
        ``BasicIPASymbol`` through the shape-tolerant setter, and rewires the
        ``Features`` specs against the target project's feature system by GUID
        (issue #222).

        Args:
            item: Target IPhPhoneme (already created + owned + GUID-assigned
                by the caller).
            props: dict produced by GetSyncableProperties.
            ws_map: Optional source->target writing-system Id mapping.
            fill_gaps: If True, only fill empty target alts / add missing
                feature specs; never overwrite existing target data.

        Notes:
            - ``BasicIPASymbol`` is applied via SetBasicIPASymbol so both the
              multistring and scalar LCM shapes are handled; the base loop's
              dict branch would raise on the scalar shape.
            - A feature spec is skipped when its feature or value GUID does
              not resolve in the target project (the feature system must be
              synced first). Must run inside the caller's unit of work.
        """
        if item is None:
            raise FP_ParameterError("ApplySyncableProperties: item is None")
        if not isinstance(props, dict):
            raise FP_ParameterError(
                f"ApplySyncableProperties: props must be a dict, got "
                f"{type(props).__name__}"
            )

        # Resolve once so an HVO or wrapper input is handled uniformly by the
        # base loop and the dedicated handlers below.
        phoneme = self.__GetPhonemeObject(item)

        # BasicIPASymbol and Features need dedicated handling; everything
        # else (Name, Description, and any future plain scalars) goes through
        # the base loop. FeaturesGuid is identity-only and not re-applied.
        basic_ipa = props.get("BasicIPASymbol")
        features = props.get("Features")
        base_props = {
            k: v
            for k, v in props.items()
            if k not in ("BasicIPASymbol", "Features", "FeaturesGuid")
        }
        super().ApplySyncableProperties(
            phoneme, base_props, ws_map, fill_gaps=fill_gaps
        )

        if isinstance(basic_ipa, dict) and basic_ipa:
            self.__ApplyBasicIPASymbol(phoneme, basic_ipa, ws_map, fill_gaps)

        if features:
            self.__ApplyFeatures(phoneme, features, fill_gaps)

    def __ApplyBasicIPASymbol(self, item, ws_values, ws_map, fill_gaps):
        """
        Apply a ``{ws_id: text}`` BasicIPASymbol dict via SetBasicIPASymbol,
        which tolerates both the multistring and scalar LCM shapes.
        """
        phoneme = self.__GetPhonemeObject(item)
        target_ws_by_id = {
            ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()
        }
        for src_ws_id, text in ws_values.items():
            if not text:
                continue
            tgt_ws_id = ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id
            tgt_handle = target_ws_by_id.get(tgt_ws_id)
            if tgt_handle is None:
                continue
            if fill_gaps and self.GetBasicIPASymbol(phoneme, tgt_handle).strip():
                continue
            self.SetBasicIPASymbol(phoneme, text, tgt_handle)

    def __ApplyFeatures(self, item, specs, fill_gaps):
        """
        Rewire a phoneme's FeaturesOA feature-value specs from a list of
        ``{"FeatureGuid", "ValueGuid"}`` dicts, resolving each feature/value
        against the target project by GUID.

        A missing FeaturesOA is created (ownership-first). Specs are matched
        by (FeatureGuid, ValueGuid) so re-application is idempotent; specs
        whose feature/value GUID does not resolve in the target are skipped.
        """
        phoneme = self.__GetPhonemeObject(item)

        struct = phoneme.FeaturesOA
        if struct is None:
            factory = self.project.project.ServiceLocator.GetService(
                IFsFeatStrucFactory
            )
            # Ownership-first: attach to FeaturesOA before populating specs
            # (LCM accessors NPE on free-floating IFsFeatStruc objects).
            new_struct = factory.Create()
            phoneme.FeaturesOA = new_struct
            struct = phoneme.FeaturesOA
        struct = IFsFeatStruc(struct)

        # Existing (feature, value) GUID pairs for idempotency.
        existing_pairs = set()
        for raw in struct.FeatureSpecsOC:
            try:
                cv = IFsClosedValue(raw)
                if cv.FeatureRA is not None and cv.ValueRA is not None:
                    existing_pairs.add(
                        (str(cv.FeatureRA.Guid).lower(),
                         str(cv.ValueRA.Guid).lower())
                    )
            except Exception:
                continue

        cv_factory = self.project.project.ServiceLocator.GetService(
            IFsClosedValueFactory
        )
        for spec in specs:
            if not isinstance(spec, dict):
                continue
            feat_guid = spec.get("FeatureGuid")
            val_guid = spec.get("ValueGuid")
            if not feat_guid or not val_guid:
                continue
            if (feat_guid.lower(), val_guid.lower()) in existing_pairs:
                continue  # already present (fill_gaps and normal both keep it)

            feat_obj = self.__ResolveByGuid(feat_guid)
            val_obj = self.__ResolveByGuid(val_guid)
            if feat_obj is None or val_obj is None:
                # Target feature system lacks this feature/value; skip. The
                # feature system must be synced before phonemes are rewired.
                continue

            closed_value = cv_factory.Create()
            struct.FeatureSpecsOC.Add(closed_value)
            cv = IFsClosedValue(closed_value)
            cv.FeatureRA = feat_obj
            cv.ValueRA = val_obj
            existing_pairs.add((feat_guid.lower(), val_guid.lower()))

    def __ResolveByGuid(self, guid_str):
        """
        Resolve a GUID string to an LCM object in this (target) project,
        returning None if it does not exist rather than raising.
        """
        try:
            return self.project.Object(guid_str)
        except Exception:
            return None

    def __ReadMultiString(self, obj, prop_name, all_ws):
        """
        Read a multistring property into a ``{ws_id: text}`` dict, guarding
        each per-WS read. Handles both the IMultiString (per-WS) and scalar
        ITsString shapes; the scalar value is keyed under the default
        vernacular writing system so ApplySyncableProperties can re-place it.

        Returns None when the property is absent or has no non-empty text.
        This guarding fixes the ``ITsString.get_String`` crash the previous
        implementation hit on BasicIPASymbol's scalar shape (issue #222).
        """
        if not hasattr(obj, prop_name):
            return None
        prop_obj = getattr(obj, prop_name)
        if prop_obj is None:
            return None

        ws_values = {}
        if hasattr(prop_obj, "get_String"):
            # IMultiUnicode / IMultiString: per-WS read.
            for ws_id, ws_handle in all_ws.items():
                try:
                    text = ITsString(prop_obj.get_String(ws_handle)).Text
                except Exception:
                    continue
                if text:
                    ws_values[ws_id] = text
        else:
            # Scalar ITsString shape: read once, key under default vern WS.
            try:
                text = ITsString(prop_obj).Text
            except Exception:
                text = None
            if text:
                default_vern = self.project.project.DefaultVernWs
                for ws_id, ws_handle in all_ws.items():
                    if ws_handle == default_vern:
                        ws_values[ws_id] = text
                        break
        return ws_values or None

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two phonemes and return detailed differences.

        Args:
            item1: First phoneme to compare (from source project).
            item2: Second phoneme to compare (from target project).
            ops1: Optional PhonemeOperations instance for item1's project.
                 Defaults to self.
            ops2: Optional PhonemeOperations instance for item2's project.
                 Defaults to self.

        Returns:
            tuple: (is_different, differences) where:
                - is_different (bool): True if items differ
                - differences (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> phoneme1 = project1_phonemeOps.Find("/p/")
            >>> phoneme2 = project2_phonemeOps.Find("/p/")
            >>> is_diff, diffs = project1_phonemeOps.CompareTo(
            ...     phoneme1, phoneme2,
            ...     ops1=project1_phonemeOps,
            ...     ops2=project2_phonemeOps
            ... )
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} -> {val2}")

        Notes:
            - Compares all MultiString properties across all writing systems
            - Compares feature structure reference by GUID
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

            if val1 != val2:
                is_different = True
                differences[key] = (val1, val2)

        return (is_different, differences)

    # --- Private Helper Methods ---

    def __is_placeholder_code(self, code):
        """
        True iff `code` is the factory-autocreated placeholder IPhCode --
        i.e. its Representation is empty (or the FLEX '***' null marker)
        across EVERY populated writing system. (issue #112)

        The naive "empty in this one WS" check would falsely classify a
        real UI-created code as a placeholder whenever the caller's
        target WS happened to be unpopulated -- and AddCode would then
        silently overwrite real vernacular data.
        """
        for ws_id in code.Representation.AvailableWritingSystemIds:
            text = ITsString(code.Representation.get_String(ws_id)).Text
            if normalize_text(text):
                return False
        return True

    def __WSHandle(self, wsHandle):
        """
        Get writing system handle, defaulting to vernacular WS for phoneme representations.

        Args:
            wsHandle: Optional writing system handle.

        Returns:
            int: The writing system handle.
        """
        if wsHandle is None:
            return self.project.project.DefaultVernWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultVernWs)

    # ========== CATALOG IMPORT METHODS ==========
    #
    # BasicIPAInfo.xml ships ~245 IPA segments with Name, BasicIPASymbol,
    # English description, and a feature-value bundle keyed against
    # PhonFeatsEticGlossList.xml. Unlike GOLDEtic / eticGlossList catalogs,
    # segments have NO per-entry GUIDs and IPhPhoneme has no
    # CatalogSourceId field -- so CatalogBackedMixin's GUID-based
    # idempotency strategy doesn't fit. We use the Phase 6b/6c
    # refuse-on-non-empty pattern instead.

    @OperationsMethod
    def ImportCatalog(self, progress=None, force=False):
        """
        Import the BasicIPAInfo segment catalog into this project's
        phoneme set.

        Populates ~245 IPhPhonemes with representation (Name +
        BasicIPASymbol), description, and a FeaturesOA feature structure
        composed of (IFsClosedFeature, IFsSymFeatVal) pairs resolved
        against PhFeatureSystemOA via the PhonFeats catalog.

        Args:
            progress: Optional callable accepting ``(count, total, name)``
                for progress reporting. May be None.
            force (bool): If True, skip the non-empty-phoneme-set guard.
                BasicIPAInfo has no per-segment GUIDs and IPhPhoneme has
                no CatalogSourceId, so re-importing would duplicate
                existing phonemes; the default (force=False) refuses to
                run on a non-empty set. Pass True to layer additional
                segments onto an existing inventory.

        Returns:
            CatalogImportResult: Created/skipped counts and any warnings.
            ``created_guids`` contains synthetic ``"BasicIPA:{code_point_id}"``
            tags (one per created phoneme) -- BasicIPAInfo has no real
            GUIDs, so the field is repurposed for verification only.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_ParameterError: If the project has no PhonologicalDataOA,
                no phoneme set, the phoneme set is non-empty and force is
                False, or PhFeatureSystemOA has not been populated yet
                (the BasicIPA catalog cross-references PhonFeats feature
                ids and cannot be resolved against an empty feature
                system).
            FileNotFoundError: If BasicIPAInfo.xml or
                PhonFeatsEticGlossList.xml is not found under FWCodeDir.

        Notes:
            - Refuse-on-non-empty idempotency (SemDom / Anthropology
              pattern). If the phoneme set already contains phonemes and
              ``force=False``, raises FP_ParameterError.
            - Refuse-with-remediation on missing PhonFeats. If the
              project's PhFeatureSystemOA is empty, ImportCatalog refuses
              and tells the caller to run
              ``project.PhonFeatures.ImportCatalog()`` first. We do NOT
              auto-import: a silent dependency import would surprise the
              caller and mask real configuration issues.
            - Representation goes into both ``IPhPhoneme.Name`` (vernacular
              WS, defaulting to en-fonipa when the project has it, else
              the default vernacular WS) and ``BasicIPASymbol`` (same WS,
              dual-shape MultiString/ITsString aware via SetBasicIPASymbol).
              Description goes into the default analysis WS.
            - PhonFeats value resolution is best-effort: missing feature
              or value ids are recorded as warnings and the offending
              FeatureValuePair is skipped. The phoneme is still created
              with whatever pairs DID resolve.
            - Segments with empty ``<Features/>`` (the seven tone entries
              at the head of BasicIPAInfo.xml) are created without a
              FeaturesOA struct -- MakeFeatStruc is only invoked when
              there is at least one resolved spec.

        Example:
            >>> project.PhonFeatures.ImportCatalog()    # prerequisite
            >>> result = project.Phonemes.ImportCatalog()
            >>> print(f"Created {result.created_count} phonemes; "
            ...       f"{len(result.warnings)} warnings")
        """
        self._EnsureWriteEnabled()

        # --- Resolve phoneme set + non-empty guard --------------------
        phon_data = self.project.lp.PhonologicalDataOA
        if not phon_data:
            raise FP_ParameterError(
                "Project has no PhonologicalDataOA; cannot import phonemes."
            )
        if phon_data.PhonemeSetsOS.Count == 0:
            raise FP_ParameterError(
                "Project has no phoneme set; cannot import phonemes."
            )
        phoneme_set = phon_data.PhonemeSetsOS[0]

        existing_count = phoneme_set.PhonemesOC.Count
        if existing_count > 0 and not force:
            raise FP_ParameterError(
                f"PhonemeSet already has {existing_count} phoneme(s). "
                f"BasicIPAInfo.xml has no per-segment GUIDs, so re-importing "
                f"would duplicate. Pass force=True to layer additional segments."
            )

        # --- PhonFeats dependency check (refuse-with-remediation) -----
        feature_system = self.project.lp.PhFeatureSystemOA
        if feature_system is None or feature_system.FeaturesOC.Count == 0:
            raise FP_ParameterError(
                "BasicIPAInfo references PhonFeats features by id (e.g. "
                "'fPAConsonantal'). Import PhonFeats first: "
                "project.PhonFeatures.ImportCatalog()"
            )

        # --- Locate + parse both catalogs ------------------------------
        basic_path = find_catalog_file(
            BASIC_IPA_CATALOG_FILENAME, subdir=BASIC_IPA_CATALOG_SUBDIR
        )
        segments = parse_basic_ipa_info(basic_path)

        phonfeats_path = find_catalog_file(
            PHON_FEATS_CATALOG_FILENAME, subdir=PHON_FEATS_CATALOG_SUBDIR
        )
        phonfeats_entries = parse_etic_gloss_list(phonfeats_path)

        # --- Build PhonFeats lookups (catalog side + project side) -----
        # value_id -> (feature_id, value_term_en) from the catalog XML.
        # Used to map a BasicIPAInfo value id ("vPAConsonantalNegative")
        # to its parent feature id ("fPAConsonantal") and its analysis-WS
        # term ("negative"), which is what we have to match against in
        # the project's IFsClosedFeature.ValuesOC (we can't match by id
        # because IFsSymFeatVal has no CatalogSourceId field).
        value_id_to_info = {}
        for feat_entry in phonfeats_entries:
            for val_entry in feat_entry.children:
                term_en = val_entry.term.get("en", "")
                value_id_to_info[val_entry.id] = (feat_entry.id, term_en)

        # feature_source_id -> IFsClosedFeature already in the project.
        # PhonFeats writes BARE ids to CatalogSourceId (no "PHON:" prefix).
        features_by_source_id = {}
        for raw_feat in feature_system.FeaturesOC:
            try:
                cf = IFsClosedFeature(raw_feat)
            except Exception:
                continue
            src_id = cf.CatalogSourceId or ""
            if src_id:
                features_by_source_id[src_id] = cf

        # --- Writing systems -------------------------------------------
        # Name + BasicIPASymbol use a vernacular WS; prefer en-fonipa
        # when the project has it (matches FW convention for IPA), fall
        # back to the default vernacular WS otherwise. Description uses
        # the default analysis WS.
        fonipa_handle = self.project.WSHandle("en-fonipa")
        if fonipa_handle is None:
            vern_ws = self.project.GetDefaultVernacularWSHandle()
        else:
            vern_ws = fonipa_handle
        analysis_ws = self.project.GetDefaultAnalysisWSHandle()

        # Precompute (feature_source_id, NFD-normalized term) -> IFsSymFeatVal.
        # Walking feature_obj.ValuesOC inside the per-segment loop is O(values
        # × pairs × segments) and does one LCM string fetch per visit; doing
        # it here is O(total values) once. The NFD normalize via
        # normalize_match_key makes the lookup safe against any future
        # catalog change to a non-ASCII term ("négatif" etc.) — Python source
        # is NFC, LCM stores NFD.
        values_by_feat_and_term = {}
        for src_id, cf in features_by_source_id.items():
            for v in cf.ValuesOC:
                v_name = ITsString(v.Name.get_String(analysis_ws)).Text or ""
                key = (src_id, normalize_match_key(v_name, casefold=False))
                values_by_feat_and_term[key] = v

        # --- Import loop -----------------------------------------------
        with self._TransactionCM("Import phoneme catalog"):
            result = CatalogImportResult()
            seen_code_points = set()  # in-pass dedup against malformed catalogs

            total = len(segments)

            for idx, seg in enumerate(segments, start=1):
                if not seg.representation:
                    result.warnings.append(
                        f"Segment '{seg.code_point_id}' has empty representation; skipping."
                    )
                    continue

                # In-pass dedup: same unicodeCodePoints appearing twice in
                # the catalog (shouldn't happen but defensive).
                if seg.code_point_id and seg.code_point_id in seen_code_points:
                    result.skipped_count += 1
                    continue
                seen_code_points.add(seg.code_point_id)

                # Resolve (feature, value) specs against the project's
                # PhFeatureSystemOA. Missing references are warned and
                # skipped; the phoneme is still created.
                specs = []
                for feat_id, val_id in seg.feature_pairs:
                    cat_feat_id, val_term = value_id_to_info.get(val_id, (None, None))
                    if cat_feat_id is None:
                        result.warnings.append(
                            f"Segment '{seg.representation}': PhonFeats value "
                            f"'{val_id}' not found in catalog; skipping pair."
                        )
                        continue
                    # The pair's feature attribute and the value's catalog
                    # parent should agree; honour whichever is non-empty.
                    lookup_feat_id = feat_id or cat_feat_id
                    feature_obj = features_by_source_id.get(lookup_feat_id)
                    if feature_obj is None:
                        result.warnings.append(
                            f"Segment '{seg.representation}': PhonFeats feature "
                            f"'{lookup_feat_id}' not imported into project; "
                            f"skipping value '{val_id}'."
                        )
                        continue
                    # Match value by NFD-normalized analysis-WS Name. Lookup
                    # is O(1) per pair via the precomputed map; bare equality
                    # is unsafe across NFC/NFD encodings.
                    value_obj = values_by_feat_and_term.get(
                        (lookup_feat_id, normalize_match_key(val_term, casefold=False))
                    )
                    if value_obj is None:
                        result.warnings.append(
                            f"Segment '{seg.representation}': value '{val_term}' "
                            f"not found on feature '{lookup_feat_id}'.ValuesOC; "
                            f"skipping pair."
                        )
                        continue
                    specs.append((feature_obj, value_obj))

                # Create the phoneme. Create() handles ownership-ordering
                # (Phase 2): attach to PhonemesOC, then set Name.
                try:
                    phoneme = self.Create(seg.representation, wsHandle=vern_ws)
                except FP_ParameterError as e:
                    # Duplicate representation (only possible under force=True
                    # with an overlapping pre-existing inventory) -- skip and
                    # warn.
                    result.warnings.append(
                        f"Segment '{seg.representation}': {e}; skipping."
                    )
                    continue

                # BasicIPASymbol (dual-shape MultiString/ITsString aware).
                self.SetBasicIPASymbol(phoneme, seg.representation, wsHandle=vern_ws)

                # Description (English; other langs in the catalog may be sparse).
                desc_en = seg.descriptions.get("en", "")
                if desc_en:
                    self.SetDescription(phoneme, desc_en, wsHandle=analysis_ws)

                # FeaturesOA atomic-owning attach. MakeFeatStruc attaches FIRST
                # (Phase 2) then populates FeatureSpecsOC -- pass owner=phoneme.
                if specs:
                    try:
                        self.project.PhonFeatures.MakeFeatStruc(specs, owner=phoneme)
                    except Exception as e:
                        result.warnings.append(
                            f"Segment '{seg.representation}': failed to build "
                            f"FeaturesOA ({e}); phoneme created without features."
                        )

                # Synthetic catalog tag (BasicIPAInfo has no real GUIDs).
                synthetic_tag = (
                    f"BasicIPA:{seg.code_point_id}" if seg.code_point_id else
                    f"BasicIPA:{seg.representation}"
                )
                result.created_count += 1
                result.created_guids.append(synthetic_tag)

                if progress:
                    try:
                        progress(idx, total, seg.representation)
                    except Exception:
                        # Progress callbacks must never break the import.
                        pass

            return result
