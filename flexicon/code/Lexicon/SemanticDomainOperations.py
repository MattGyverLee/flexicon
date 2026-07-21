#
#   SemanticDomainOperations.py
#
#   Class: SemanticDomainOperations
#          Semantic domain operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key, best_analysis_text
from ..Shared.catalog_backed import _LCMNativeCatalogImportMixin

# Import FLEx LCM types
from SIL.LCModel import (
    ICmSemanticDomain,
    ICmSemanticDomainFactory,
    ILexSenseRepository,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class SemanticDomainOperations(BaseOperations, _LCMNativeCatalogImportMixin):
    """
    This class provides operations for managing semantic domains in a
    FieldWorks project.

    Semantic domains are hierarchical categorizations of word meanings used
    to organize the lexicon semantically. Most projects use predefined domain
    lists (e.g., from SIL), but custom domains can also be created.

    This class should be accessed via FLExProject.SemanticDomains property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Get all semantic domains (flat list)
        for domain in project.SemanticDomains.GetAll():
            number = project.SemanticDomains.GetNumber(domain)
            name = project.SemanticDomains.GetName(domain)
            print(f"{number} - {name}")

        # Find a specific domain by number
        domain = project.SemanticDomains.Find("7.2.1")
        if domain:
            name = project.SemanticDomains.GetName(domain)
            desc = project.SemanticDomains.GetDescription(domain)
            print(f"{name}: {desc}")

        # Get all senses in a domain
        senses = project.SemanticDomains.GetSensesInDomain(domain)
        print(f"Found {len(senses)} senses in this domain")

        project.CloseProject()
    """

    # ---- _LCMNativeCatalogImportMixin configuration -------------------
    # SemDom ships as LCM-native XML in <FWCodeDir>/Templates/SemDom.xml;
    # ImportCatalog delegates to XmlList.ImportList via the mixin's
    # _import_lcm_native_catalog helper. See catalog_backed.py.
    CATALOG_FILE = "SemDom.xml"
    CATALOG_SUBDIR = "Templates"
    LCM_FIELD_NAME = "SemanticDomainList"
    LANG_PROJECT_LIST_ATTR = "SemanticDomainListOA"
    DOMAIN_ITEM_LABEL_SINGULAR = "domain"
    DOMAIN_ITEM_LABEL_PLURAL = "domains"

    def __init__(self, project):
        """
        Initialize SemanticDomainOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    # --- Core Read Operations ---

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, recursive=True, **kwargs):
        """
        Get all semantic domains in the project.

        Args:
            recursive (bool): If True (default), returns every domain in the
                hierarchy (depth-first, parents before children). If False,
                returns only top-level domains and the caller must descend
                via GetSubdomains.

        Returns:
            list[ICmSemanticDomain]: All semantic domains.

        Example:
            >>> for domain in project.SemanticDomains.GetAll():
            ...     print(project.SemanticDomains.GetNumber(domain),
            ...           project.SemanticDomains.GetName(domain))
            1 - Universe, creation
            1.1 - Sky
            1.1.1 - Sun
            ...

            >>> # Top-level only
            >>> for domain in project.SemanticDomains.GetAll(recursive=False):
            ...     print(project.SemanticDomains.GetName(domain))

        See Also:
            Find, FindByName, GetSubdomains
        """
        self._RejectLegacyKwargs(kwargs, {
            "flat": ("recursive", "semantics inverted: flat=True is now recursive=True"),
        })
        domain_list = self.project.lp.SemanticDomainListOA
        if not domain_list:
            return []

        return list(self.project.UnpackNestedPossibilityList(
            domain_list.PossibilitiesOS, ICmSemanticDomain, recursive))

    @OperationsMethod
    def Find(self, number):
        """
        Find a semantic domain by its number.

        Args:
            number (str): The domain number to search for (e.g., "3.5.1.1").

        Returns:
            ICmSemanticDomain or None: The domain object if found, None otherwise.

        Raises:
            Exception: If number is None.

        Example:
            >>> # Find a specific domain
            >>> domain = project.SemanticDomains.Find("7.2.1")
            >>> if domain:
            ...     name = project.SemanticDomains.GetName(domain)
            ...     print(f"Found: {name}")
            Found: Walk

            >>> # Try to find non-existent domain
            >>> missing = project.SemanticDomains.Find("999.999")
            >>> print(missing)
            None

        Notes:
            - Number format is hierarchical (e.g., "1.2.3.4")
            - Search is exact match on the abbreviation field
            - Returns first match only (should be unique)
            - Returns None if not found (doesn't raise exception)
            - Number comparison is string-based, not numeric

        See Also:
            FindByName, Exists, GetNumber
        """
        self._ValidateParam(number, "number")

        if not number or not number.strip():
            return None

        number = number.strip()
        wsHandle = self.project.project.DefaultAnalWs

        # Search through all domains (flat)
        for domain in self.GetAll():
            domain_num = self.GetNumber(domain)
            if domain_num == number:
                return domain

        return None

    @OperationsMethod
    def FindByName(self, name):
        """
        Find a semantic domain by its name.

        Args:
            name (str): The domain name to search for (case-insensitive).

        Returns:
            ICmSemanticDomain or None: The domain object if found, None otherwise.

        Raises:
            Exception: If name is None.

        Example:
            >>> # Find by English name
            >>> domain = project.SemanticDomains.FindByName("Walk")
            >>> if domain:
            ...     number = project.SemanticDomains.GetNumber(domain)
            ...     print(f"Domain number: {number}")
            Domain number: 7.2.1

            >>> # Case-insensitive search
            >>> domain = project.SemanticDomains.FindByName("walk")
            >>> print(domain is not None)
            True

        Notes:
            - Search is case-insensitive
            - Searches in default analysis writing system
            - Returns first match only
            - Returns None if not found (doesn't raise exception)
            - For multilingual searches, iterate GetAll() manually

        See Also:
            Find, Exists, GetName
        """
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            return None

        target = normalize_match_key(name.strip(), casefold=True)
        wsHandle = self.project.project.DefaultAnalWs

        # Search through all domains
        for domain in self.GetAll():
            domain_name = ITsString(domain.Name.get_String(wsHandle)).Text
            if normalize_match_key(domain_name, casefold=True) == target:
                return domain

        return None

    @OperationsMethod
    def Exists(self, number):
        """
        Check if a semantic domain with the given number exists.

        Args:
            number (str): The domain number to check (e.g., "3.5.1.1").

        Returns:
            bool: True if domain exists, False otherwise.

        Raises:
            Exception: If number is None.

        Example:
            >>> if project.SemanticDomains.Exists("7.2.1"):
            ...     print("Walk domain exists")
            Walk domain exists

            >>> if not project.SemanticDomains.Exists("999.999"):
            ...     print("Custom domain 999.999 does not exist")
            Custom domain 999.999 does not exist

        Notes:
            - Returns False for empty or whitespace-only numbers
            - More efficient than Find() when you only need existence check
            - Use Find() if you need the actual domain object

        See Also:
            Find, FindByName
        """
        self._ValidateParam(number, "number")

        return self.Find(number) is not None

    # --- Domain Properties ---

    @OperationsMethod
    def GetName(self, domain_or_hvo, wsHandle=None):
        """
        Get the name of a semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The domain name, or empty string if not set.

        Raises:
            Exception: If domain_or_hvo is None.

        Example:
            >>> domain = project.SemanticDomains.Find("7.2.1")
            >>> name = project.SemanticDomains.GetName(domain)
            >>> print(name)
            Walk

            >>> # Get name in a specific writing system
            >>> name_fr = project.SemanticDomains.GetName(domain,
            ...                                            project.WSHandle('fr'))
            >>> print(name_fr)
            Marcher

        Notes:
            - Returns empty string if name not set in specified writing system
            - Names are typically set in multiple writing systems
            - Default writing system is the default analysis WS

        See Also:
            SetName, GetDescription, GetAbbreviation
        """
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name = ITsString(domain.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetName(self, domain_or_hvo, name, wsHandle=None):
        """
        Set the name of a semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If domain_or_hvo or name is None.

        Example:
            >>> domain = project.SemanticDomains.Find("900.1")  # custom domain
            >>> project.SemanticDomains.SetName(domain, "Custom Category")
            >>> print(project.SemanticDomains.GetName(domain))
            Custom Category

        Warning:
            - Modifying standard semantic domains (e.g., SIL domains) may
              cause compatibility issues with other projects
            - Consider creating custom domains instead of modifying standard ones

        See Also:
            GetName, Create
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")
        self._ValidateParam(name, "name")

        domain = self.__ResolveObject(domain_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        domain.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetDescription(self, domain_or_hvo, wsHandle=None):
        """
        Get the description of a semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The domain description, or empty string if not set.

        Raises:
            FP_NullParameterError: If domain_or_hvo is None.

        Example:
            >>> domain = project.SemanticDomains.Find("7.2.1")
            >>> desc = project.SemanticDomains.GetDescription(domain)
            >>> print(desc)
            Use this domain for words related to walking.

        Notes:
            - Description provides guidance on domain usage
            - Often includes examples of words that belong in the domain
            - Returns empty string if not set in specified writing system
            - Descriptions can be quite lengthy

        See Also:
            SetDescription, GetName, GetQuestions
        """
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Description is a MultiString
        desc = ITsString(domain.Description.get_String(wsHandle)).Text
        return desc or ""

    @OperationsMethod
    def SetDescription(self, domain_or_hvo, description, wsHandle=None):
        """
        Set the description of a semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.
            description (str): The new description text.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If domain_or_hvo or description is None.

        Example:
            >>> domain = project.SemanticDomains.Find("900.1")  # custom domain
            >>> project.SemanticDomains.SetDescription(domain,
            ...     "Use this domain for words related to modern technology.")

        See Also:
            GetDescription, SetName
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")
        self._ValidateParam(description, "description")

        domain = self.__ResolveObject(domain_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Description is a MultiString
        domain.Description.set_String(wsHandle, description)

    @OperationsMethod
    def GetAbbreviation(self, domain_or_hvo, wsHandle=None):
        """
        Get the abbreviation of a semantic domain.

        The abbreviation typically contains the domain number.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The domain abbreviation, or empty string if not set.

        Raises:
            FP_NullParameterError: If domain_or_hvo is None.

        Example:
            >>> domain = project.SemanticDomains.Find("7.2.1")
            >>> abbr = project.SemanticDomains.GetAbbreviation(domain)
            >>> print(abbr)
            7.2.1

        Notes:
            - Abbreviation usually equals the domain number
            - Returns empty string if not set in specified writing system
            - For domain number specifically, use GetNumber()

        See Also:
            GetNumber, GetName
        """
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        abbr = ITsString(domain.Abbreviation.get_String(wsHandle)).Text
        return abbr or ""

    @OperationsMethod
    def GetNumber(self, domain_or_hvo):
        """
        Get the domain number of a semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.

        Returns:
            str: The domain number (e.g., "7.2.1"), or empty string if not set.

        Raises:
            FP_NullParameterError: If domain_or_hvo is None.

        Example:
            >>> domain = project.SemanticDomains.FindByName("Walk")
            >>> number = project.SemanticDomains.GetNumber(domain)
            >>> print(number)
            7.2.1

            >>> # Use number to navigate hierarchy
            >>> parent_num = ".".join(number.split(".")[:-1])
            >>> parent = project.SemanticDomains.Find(parent_num)
            >>> print(project.SemanticDomains.GetName(parent))
            Move

        Notes:
            - Domain number is stored in the abbreviation field
            - Numbers are hierarchical (e.g., 1.2.3.4)
            - Resolves via BestAnalysisAlternative so canonical-catalog
              numbers (only populated in English by SemDom.xml) are
              still found when the project's default analysis WS is a
              language without translated abbreviations.
            - Returns empty string if domain has no number

        See Also:
            GetAbbreviation, Find, GetDepth
        """
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)

        # Domain number is stored in the abbreviation. SemDom.xml only
        # populates the English alternative, so BestAnalysisAlternative
        # is required for projects whose default analysis WS is not
        # English (e.g., Sena 3, where DefaultAnalWs is Portuguese).
        number = best_analysis_text(domain.Abbreviation)
        return number or ""

    @OperationsMethod
    def GetQuestions(self, domain_or_hvo, wsHandle=None):
        """
        Get elicitation questions for a semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The elicitation questions, or empty string if not set.

        Raises:
            FP_NullParameterError: If domain_or_hvo is None.

        Example:
            >>> domain = project.SemanticDomains.Find("7.2.1")
            >>> questions = project.SemanticDomains.GetQuestions(domain)
            >>> print(questions)
            (1) What words refer to walking?
            (2) What words refer to the way a person walks?
            (3) What words refer to walking a long distance?
            ...

        Notes:
            - Questions are used for elicitation during fieldwork
            - Questions help speakers think of words in the domain
            - Returns empty string if no questions are defined
            - Questions may be numbered or bulleted
            - Standard SIL domains include comprehensive question sets

        See Also:
            GetDescription, GetName
        """
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Questions is an owning sequence of CmDomainQ objects (QuestionsOS)
        # Each CmDomainQ has a Question property (MultiUnicode)
        questions_list = []
        if hasattr(domain, "QuestionsOS"):
            for domain_q in domain.QuestionsOS:
                if hasattr(domain_q, "Question"):
                    q_text = ITsString(domain_q.Question.get_String(wsHandle)).Text
                    if q_text:
                        questions_list.append(q_text)
        return "\n".join(questions_list)

    @OperationsMethod
    def GetOcmCodes(self, domain_or_hvo):
        """
        Get OCM (Outline of Cultural Materials) codes for a semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.

        Returns:
            str: The OCM codes, or empty string if not set.

        Raises:
            FP_NullParameterError: If domain_or_hvo is None.

        Example:
            >>> domain = project.SemanticDomains.Find("7.2.1")
            >>> ocm = project.SemanticDomains.GetOcmCodes(domain)
            >>> print(ocm)
            484

        Notes:
            - OCM codes link to the Outline of Cultural Materials
            - OCM is a standard anthropological classification system
            - Returns empty string if no OCM codes are assigned
            - Multiple codes may be separated by spaces or commas
            - Uses default analysis writing system

        See Also:
            GetNumber, GetDescription
        """
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)
        wsHandle = self.project.project.DefaultAnalWs

        # OcmCodes is a MultiUnicode
        ocm = ITsString(domain.OcmCodes.get_String(wsHandle)).Text
        return ocm or ""

    # --- Hierarchy Operations ---

    @OperationsMethod
    def GetSubdomains(self, domain_or_hvo, recursive=True, **kwargs):
        """
        Get the subdomains of a semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.
            recursive (bool): If True (default), returns every descendant
                domain (depth-first, parents before children). If False,
                returns only direct children.

        Returns:
            list: List of ICmSemanticDomain objects (empty list if none).

        Raises:
            FP_NullParameterError: If domain_or_hvo is None.

        Example:
            >>> top = project.SemanticDomains.Find("1")
            >>> for sub in project.SemanticDomains.GetSubdomains(top):
            ...     print(project.SemanticDomains.GetNumber(sub))   # All descendants

            >>> # Direct children only
            >>> for sub in project.SemanticDomains.GetSubdomains(top, recursive=False):
            ...     print(project.SemanticDomains.GetNumber(sub))

        See Also:
            GetParent, GetAll, GetDepth
        """
        self._RejectLegacyKwargs(kwargs, {
            "flat": ("recursive", "semantics inverted: flat=True is now recursive=True"),
        })
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)

        if not recursive:
            return [ICmSemanticDomain(child) for child in domain.SubPossibilitiesOS]

        result = []
        def walk(collection):
            for raw in collection:
                child = ICmSemanticDomain(raw)
                result.append(child)
                if child.SubPossibilitiesOS.Count > 0:
                    walk(child.SubPossibilitiesOS)
        walk(domain.SubPossibilitiesOS)
        return result

    @OperationsMethod
    def GetParent(self, domain_or_hvo):
        """
        Get the parent domain of a semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.

        Returns:
            ICmSemanticDomain or None: The parent domain, or None if top-level.

        Raises:
            FP_NullParameterError: If domain_or_hvo is None.

        Example:
            >>> # Get parent of "Walk" (7.2.1)
            >>> walk = project.SemanticDomains.Find("7.2.1")
            >>> parent = project.SemanticDomains.GetParent(walk)
            >>> if parent:
            ...     number = project.SemanticDomains.GetNumber(parent)
            ...     name = project.SemanticDomains.GetName(parent)
            ...     print(f"Parent: {number} - {name}")
            Parent: 7.2 - Move

            >>> # Top-level domains have no parent
            >>> top = project.SemanticDomains.Find("1")
            >>> parent = project.SemanticDomains.GetParent(top)
            >>> print(parent)
            None

        Notes:
            - Returns None for top-level domains
            - Parent is determined by ownership hierarchy
            - Use GetNumber() and string parsing for alternative navigation
            - Parent-child relationships form a tree structure

        See Also:
            GetSubdomains, GetDepth, GetNumber
        """
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)
        owner = domain.Owner

        # Check if owner is a semantic domain (subdomain) or the list (top-level)
        if owner and hasattr(owner, "ClassName"):
            if owner.ClassName == "CmSemanticDomain":
                # Cast to typed interface; raw owner is ICmObject in LCM.
                return ICmSemanticDomain(owner)

        return None

    @OperationsMethod
    def GetDepth(self, domain_or_hvo):
        """
        Get the depth of a semantic domain in the hierarchy.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.

        Returns:
            int: The depth (0 for top-level, 1 for first level subdomains, etc.).

        Raises:
            FP_NullParameterError: If domain_or_hvo is None.

        Example:
            >>> # Top-level domain
            >>> universe = project.SemanticDomains.Find("1")
            >>> depth = project.SemanticDomains.GetDepth(universe)
            >>> print(depth)
            0

            >>> # Third-level domain
            >>> walk = project.SemanticDomains.Find("7.2.1")
            >>> depth = project.SemanticDomains.GetDepth(walk)
            >>> print(depth)
            2

        Notes:
            - Depth is 0-based (top-level = 0)
            - Depth equals the number of dots in domain number
            - Calculated by traversing parent chain
            - Useful for indentation in tree displays

        See Also:
            GetParent, GetNumber, GetSubdomains
        """
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)

        # Count parents by traversing ownership chain
        depth = 0
        current = domain
        while True:
            parent = self.GetParent(current)
            if parent is None:
                break
            depth += 1
            current = parent

        return depth

    # --- Usage Operations ---

    @OperationsMethod
    def GetSensesInDomain(self, domain_or_hvo):
        """
        Get all lexical senses that belong to this semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.

        Returns:
            list: List of ILexSense objects that reference this domain.

        Raises:
            FP_NullParameterError: If domain_or_hvo is None.

        Example:
            >>> domain = project.SemanticDomains.Find("7.2.1")
            >>> senses = project.SemanticDomains.GetSensesInDomain(domain)
            >>> for sense in senses:
            ...     entry = sense.Entry
            ...     headword = project.LexiconGetHeadword(entry)
            ...     gloss = project.LexiconGetSenseGloss(sense)
            ...     print(f"{headword}: {gloss}")
            walk: to move on foot
            stroll: to walk leisurely
            march: to walk in formation
            ...

        Notes:
            - Searches all senses in the lexicon
            - Returns empty list if no senses use this domain
            - May be slow for large lexicons
            - Senses can belong to multiple domains
            - Use GetSenseCount() for just the count

        See Also:
            GetSenseCount, GetSubdomains
        """
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)
        domain_hvo = domain.Hvo

        # Search all senses for this domain
        senses = []
        sense_repo = self.project.project.ServiceLocator.GetService(ILexSenseRepository)

        for sense in sense_repo.AllInstances():
            # Check if this sense has this domain in its SemanticDomainsRC
            if domain in sense.SemanticDomainsRC:
                senses.append(sense)

        return senses

    @OperationsMethod
    def GetSenseCount(self, domain_or_hvo, recursive=False):
        """
        Get the count of lexical senses that belong to this semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO.
            recursive (bool): If False (default), counts only senses
                tagged with this domain exactly -- matches what FLEx's UI
                shows in the Semantic Domain browse view (every count
                column in FLEx is direct-only, same convention as
                POSOperations.GetEntryCount). If True, rolls up senses
                tagged with this domain OR any descendant domain
                (e.g. counting "1" rolls up everything under
                "1.1", "1.1.1", ...).

        Returns:
            int: The count of senses using this domain (direct-only by
            default; including descendants when ``recursive=True``).

        Raises:
            FP_NullParameterError: If domain_or_hvo is None.

        Example:
            >>> domain = project.SemanticDomains.Find("7.2.1")
            >>> count = project.SemanticDomains.GetSenseCount(domain)
            >>> print(f"Domain 7.2.1 (Walk) has {count} senses (direct)")
            Domain 7.2.1 (Walk) has 15 senses (direct)

            >>> # Roll up: include 7.2.1.x sub-domains
            >>> rollup = project.SemanticDomains.GetSenseCount(domain, recursive=True)

            >>> # Find empty domains
            >>> for domain in project.SemanticDomains.GetAll():
            ...     count = project.SemanticDomains.GetSenseCount(domain)
            ...     if count == 0:
            ...         number = project.SemanticDomains.GetNumber(domain)
            ...         name = project.SemanticDomains.GetName(domain)
            ...         print(f"Empty: {number} - {name}")

        Notes:
            - More efficient than len(GetSensesInDomain())
            - May still be slow for large lexicons
            - Returns 0 for domains with no senses
            - Useful for coverage analysis
            - Counting queries default to ``recursive=False`` (FLEx UI
              parity), matching POSOperations.GetEntryCount. Collection
              queries (GetAll, GetSubdomains) default to True; the
              asymmetry is intentional. (issue #106 part 1)

        See Also:
            GetSensesInDomain, GetSubdomains
        """
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)

        # Build the set of domain HVOs to match. With recursive=True
        # this expands to include every descendant domain so callers
        # don't miss senses tagged with a sub-domain of the requested
        # one. (issue #106 part 1)
        match_hvos = {domain.Hvo}
        if recursive:
            match_hvos.update(
                d.Hvo for d in self.GetSubdomains(domain, recursive=True)
            )

        count = 0
        sense_repo = self.project.project.ServiceLocator.GetService(ILexSenseRepository)

        for sense in sense_repo.AllInstances():
            for sense_domain in sense.SemanticDomainsRC:
                if sense_domain.Hvo in match_hvos:
                    count += 1
                    break  # Count each sense only once

        return count

    # --- Custom Domain Management ---

    @OperationsMethod
    def Create(self, name, number, parent=None, wsHandle=None):
        """
        Create a new custom semantic domain.

        Args:
            name (str): The name of the new domain.
            number (str): The domain number (e.g., "900.1").
            parent: Optional parent ICmSemanticDomain object or HVO. If None,
                creates a top-level domain.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            ICmSemanticDomain: The newly created domain object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name or number is None.
            FP_ParameterError: If name or number is empty, or domain number
                already exists.

        Example:
            >>> # Create a top-level custom domain
            >>> custom = project.SemanticDomains.Create("Technology", "900")
            >>> print(project.SemanticDomains.GetName(custom))
            Technology

            >>> # Create a subdomain
            >>> computers = project.SemanticDomains.Create(
            ...     "Computers", "900.1", parent=custom)
            >>> print(project.SemanticDomains.GetNumber(computers))
            900.1

        Warning:
            - Custom domain numbers should not conflict with standard domains
            - Standard SIL domains use numbers 1-9
            - Consider using 900+ for custom domains
            - Creating many custom domains may impact performance

        Notes:
            - Domain is added to parent's subdomains or to top level
            - Number must be unique across all domains
            - Name is set in specified writing system
            - Use SetDescription() and GetQuestions() to add more details

        See Also:
            Delete, SetName, SetDescription, GetSubdomains
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(name, "name")
        self._ValidateParam(number, "number")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")
        if not number or not number.strip():
            raise FP_ParameterError("Number cannot be empty")

        # Check if domain number already exists
        if self.Exists(number):
            raise FP_ParameterError(f"Semantic domain '{number}' already exists")

        wsHandle = self.__WSHandle(wsHandle)

        with self._TransactionCM(f"Create semantic domain {number}"):
            # Create the new domain using the factory
            factory = self.project.project.ServiceLocator.GetService(ICmSemanticDomainFactory)
            new_domain = factory.Create()

            # Add to parent or top-level list (must be done before setting properties)
            if parent:
                parent_obj = self.__ResolveObject(parent)
                parent_obj.SubPossibilitiesOS.Add(new_domain)
            else:
                domain_list = self.project.lp.SemanticDomainListOA
                domain_list.PossibilitiesOS.Add(new_domain)

            # Set name
            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_domain.Name.set_String(wsHandle, mkstr_name)

            # Set abbreviation (domain number)
            mkstr_num = TsStringUtils.MakeString(number, wsHandle)
            new_domain.Abbreviation.set_String(wsHandle, mkstr_num)

            return new_domain

    @OperationsMethod
    def Delete(self, domain_or_hvo):
        """
        Delete a semantic domain.

        Args:
            domain_or_hvo: The ICmSemanticDomain object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If domain_or_hvo is None.

        Example:
            >>> # Delete a custom domain
            >>> custom = project.SemanticDomains.Find("900.1")
            >>> if custom:
            ...     project.SemanticDomains.Delete(custom)

        Warning:
            - DO NOT delete standard semantic domains (1-9)
            - Deletion is permanent and cannot be undone
            - Deletes all subdomains recursively
            - Senses using this domain will lose the domain reference
            - Consider removing from senses first

        Notes:
            - Best practice: only delete custom domains (900+)
            - Deletion cascades to all subdomains
            - Domain references in senses are automatically cleaned up
            - Use with caution on shared projects

        See Also:
            Create, GetSensesInDomain
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(domain_or_hvo, "domain_or_hvo")

        domain = self.__ResolveObject(domain_or_hvo)

        # Get the parent or top-level list
        parent = self.GetParent(domain)

        if parent:
            # Remove from parent's subdomains
            parent.SubPossibilitiesOS.Remove(domain)
        else:
            # Remove from top-level list
            domain_list = self.project.lp.SemanticDomainListOA
            domain_list.PossibilitiesOS.Remove(domain)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True, deep=True):
        """
        Duplicate a semantic domain, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The ICmSemanticDomain object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source domain.
                                If False, insert at end of parent's subdomain list.
            deep (bool): If True (default), also duplicate owned objects (subdomains, examples).
                        If False, only copy simple properties.

        Returns:
            ICmSemanticDomain: The newly created duplicate domain with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> # Deep duplicate (default: includes all subdomains)
            >>> domain = project.SemanticDomains.Find("900.1")
            >>> if domain:
            ...     dup = project.SemanticDomains.Duplicate(domain)  # deep=True by default
            ...     print(f"Original: {project.SemanticDomains.GetNumber(domain)}")
            ...     print(f"Duplicate: {project.SemanticDomains.GetNumber(dup)}")
            ...     subdomains = project.SemanticDomains.GetSubdomains(dup)
            ...     print(f"Subdomains: {len(subdomains)}")
            ...     # Note: Duplicate number - must be set manually
            ...
            ...     # Shallow duplicate (no subdomains)
            ...     shallow_dup = project.SemanticDomains.Duplicate(domain, deep=False)

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original domain's position
            - Simple properties copied: Name, Description, Abbreviation, Questions, OcmCodes
            - Owned objects (deep=True): SubPossibilitiesOS (subdomains), OccurrencesRS
            - Abbreviation (domain number) is copied but should typically be changed
            - ReferringObjects (senses) are not copied (back-references)

        Warning:
            - After duplication, update the Abbreviation (domain number) to be unique
            - Domain numbers must be unique across the project
            - Deep duplication of standard domains (1-9) is not recommended

        See Also:
            Create, Delete, GetNumber
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source domain and parent
        source = self.__ResolveObject(item_or_hvo)
        parent = self.GetParent(source)

        with self._TransactionCM("Duplicate semantic domain"):
            # Create new domain using factory (auto-generates new GUID)
            factory = self.project.project.ServiceLocator.GetService(ICmSemanticDomainFactory)
            duplicate = factory.Create()

            # Determine insertion position - ADD TO PARENT FIRST
            if parent:
                # Has a parent - add to parent's subdomains
                if insert_after:
                    source_index = parent.SubPossibilitiesOS.IndexOf(source)
                    parent.SubPossibilitiesOS.Insert(source_index + 1, duplicate)
                else:
                    parent.SubPossibilitiesOS.Add(duplicate)
            else:
                # Top-level domain - add to main list
                domain_list = self.project.lp.SemanticDomainListOA
                if insert_after:
                    source_index = domain_list.PossibilitiesOS.IndexOf(source)
                    domain_list.PossibilitiesOS.Insert(source_index + 1, duplicate)
                else:
                    domain_list.PossibilitiesOS.Add(duplicate)

            # Copy simple MultiString properties (AFTER adding to parent)
            duplicate.Name.CopyAlternatives(source.Name)
            duplicate.Description.CopyAlternatives(source.Description)
            duplicate.Abbreviation.CopyAlternatives(source.Abbreviation)
            duplicate.Questions.CopyAlternatives(source.Questions)
            duplicate.OcmCodes.CopyAlternatives(source.OcmCodes)

            # Handle owned objects if deep=True
            if deep:
                # Duplicate subdomains recursively
                for subdomain in source.SubPossibilitiesOS:
                    self.Duplicate(subdomain, insert_after=False, deep=True)

                # Copy OccurrencesRS (references to examples in the semantic domain)
                for occurrence in source.OccurrencesRS:
                    duplicate.OccurrencesRS.Add(occurrence)

            return duplicate

    # ========== CATALOG IMPORT METHODS ==========
    #
    # Unlike POS / PhonFeatures / InflectionFeatures (which use the etic
    # CatalogEntry parser via CatalogBackedMixin), the semantic-domain
    # catalog ships as LCM-native XML at:
    #
    #     <FWCodeDir>/Templates/SemDom.xml
    #
    # i.e. <LangProject><SemanticDomainList><CmPossibilityList>... with
    # <CmSemanticDomain guid="..."> items. That shape is what
    # SIL.LCModel.Application.ApplicationServices.XmlList.ImportList
    # consumes natively, so we delegate to it directly rather than
    # reimplementing the parser. Items whose canonical GUIDs already
    # exist in the project are reused; new ones are created; localized
    # Name/Abbreviation/Description, OcmCodes, LouwNidaCodes, Questions,
    # and nested SubPossibilities all come from the catalog.

    @OperationsMethod
    def ImportCatalog(self, progress=None, force=False):
        """
        Import the full SemDom semantic-domain catalog into this project.

        Loads SIL's standard semantic-domain hierarchy (~1700 domains)
        from ``<FWCodeDir>/Templates/SemDom.xml`` via LCM's native
        ``XmlList.ImportList``. The catalog supplies localized Name /
        Abbreviation / Description, OcmCodes, LouwNidaCodes, Questions
        and the full nested SubPossibilities hierarchy.

        **Idempotency guard**: LCM's underlying ``XmlList.ImportList``
        APPENDS items into ``SemanticDomainListOA.PossibilitiesOS``
        without checking for canonical-GUID duplicates -- each call
        adds another full set of top-level domains. To prevent
        accidental duplication, this method refuses by default when
        the list is already non-empty. Pass ``force=True`` to import
        anyway (e.g. to layer a second-language localization on top of
        an existing import). The caller then takes responsibility for
        any resulting duplicates.

        **Recovery from past duplication**: If a project already has
        duplicate top-level domains from prior unguarded imports, this
        method does NOT clean them up automatically -- that would be
        destructive. Recovery requires either manual cleanup via the
        FieldWorks GUI, or deliberate ``bulk_delete``-style code the
        caller writes to remove duplicate GUID groups.

        Note: single-domain import via ``CreateFromCatalog(source_id)``
        is not yet supported for this catalog. The SemDom catalog is
        hierarchical and large (~2.7 MB); the typical workflow is a
        full import, after which existing operations (``Find``,
        ``FindByName``, ``GetAll``) work normally. File a request if
        you need single-item import.

        Args:
            progress: Optional ``SIL.LCModel.Utils.IProgress`` instance
                      to report import progress. Pass ``None`` (the
                      default) for silent import.
            force: If True, skip the non-empty list check and import
                   anyway. Default False (refuse if list is non-empty).

        Returns:
            int: Number of top-level domains in
                 ``LangProject.SemanticDomainListOA.PossibilitiesOS``
                 after import. Useful as a sanity check for callers.

        Raises:
            FP_ReadOnlyError: If the project is not write-enabled.
            FP_FileNotFoundError: If SemDom.xml cannot be located under
                                  the FieldWorks install.
            FP_ParameterError: If ``SemanticDomainListOA`` already has
                               domains and ``force`` is False.
        """
        # Body extracted to _LCMNativeCatalogImportMixin in Phase Q-3a;
        # this thin wrapper preserves the @OperationsMethod descriptor
        # on the class itself (tests introspect via __dict__).
        return self._import_lcm_native_catalog(progress=progress, force=force)

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of a semantic domain for comparison.

        Args:
            item: The ICmSemanticDomain object.

        Returns:
            dict: Dictionary mapping property names to their values.
        """
        props = {}

        # MultiString properties
        # Name - domain name
        name_dict = {}
        if hasattr(item, "Name"):
            for ws_def in self.project.WritingSystems.GetAll():
                text = ITsString(item.Name.get_String(ws_def.Handle)).Text
                if text:
                    name_dict[ws_def.Id] = text
        props["Name"] = name_dict

        # Description - domain description
        description_dict = {}
        if hasattr(item, "Description"):
            for ws_def in self.project.WritingSystems.GetAll():
                text = ITsString(item.Description.get_String(ws_def.Handle)).Text
                if text:
                    description_dict[ws_def.Id] = text
        props["Description"] = description_dict

        # Abbreviation - domain number
        abbreviation_dict = {}
        if hasattr(item, "Abbreviation"):
            for ws_def in self.project.WritingSystems.GetAll():
                text = ITsString(item.Abbreviation.get_String(ws_def.Handle)).Text
                if text:
                    abbreviation_dict[ws_def.Id] = text
        props["Abbreviation"] = abbreviation_dict

        # Questions - elicitation questions
        questions_dict = {}
        if hasattr(item, "Questions"):
            for ws_def in self.project.WritingSystems.GetAll():
                text = ITsString(item.Questions.get_String(ws_def.Handle)).Text
                if text:
                    questions_dict[ws_def.Id] = text
        props["Questions"] = questions_dict

        # OcmCodes - OCM codes
        ocm_dict = {}
        if hasattr(item, "OcmCodes"):
            for ws_def in self.project.WritingSystems.GetAll():
                text = ITsString(item.OcmCodes.get_String(ws_def.Handle)).Text
                if text:
                    ocm_dict[ws_def.Id] = text
        props["OcmCodes"] = ocm_dict

        # Note: SubPossibilitiesOS is an Owning Sequence (OS) - not included
        # Note: OccurrencesRS is a Reference Sequence (complex) - not included

        return props

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two semantic domains and return their differences.

        Args:
            item1: The first ICmSemanticDomain object.
            item2: The second ICmSemanticDomain object.
            ops1: Optional SemanticDomainOperations instance for item1.
            ops2: Optional SemanticDomainOperations instance for item2.

        Returns:
            tuple: (is_different, differences_dict)
        """
        ops1 = ops1 or self
        ops2 = ops2 or self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        differences = {}
        all_keys = set(props1.keys()) | set(props2.keys())
        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)
            if val1 != val2:
                differences[key] = (val1, val2)

        is_different = len(differences) > 0
        return is_different, differences

    # --- Private Helper Methods ---

    def __ResolveObject(self, domain_or_hvo):
        """
        Resolve HVO or object to ICmSemanticDomain.

        Args:
            domain_or_hvo: Either an ICmSemanticDomain object or an HVO (int).

        Returns:
            ICmSemanticDomain: The resolved domain object.

        Raises:
            FP_ParameterError: If HVO doesn't refer to a semantic domain.
        """
        if isinstance(domain_or_hvo, int):
            obj = self.project.Object(domain_or_hvo)
            if not isinstance(obj, ICmSemanticDomain):
                raise FP_ParameterError("HVO does not refer to a semantic domain")
            return obj
        return domain_or_hvo

    def __WSHandle(self, wsHandle):
        """
        Get writing system handle, defaulting to analysis WS.

        Args:
            wsHandle: Optional writing system handle.

        Returns:
            int: The writing system handle.
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)
