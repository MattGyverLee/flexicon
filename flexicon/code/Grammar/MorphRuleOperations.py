#
#   MorphRuleOperations.py
#
#   Class: MorphRuleOperations
#          Morphological rule operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#
#   Morphological rules in the LCM data model are distributed across
#   several locations:
#
#   - Compound rules (MoEndoCompound, MoExoCompound):
#     Owned by MoMorphData.CompoundRulesOS
#
#   - Inflectional affix templates (MoInflAffixTemplate):
#     Owned by PartOfSpeech.AffixTemplatesOS (per POS in hierarchy)
#
#   - Ad hoc co-prohibitions (MoAdhocProhib subclasses):
#     Owned by MoMorphData.AdhocCoProhibitionsOC
#     (Separate API — different property interface from rules/templates)
#
#   - Affix processes (MoAffixProcess):
#     Owned by LexEntry as allomorphs (LexemeFormOA/AlternateFormsOS),
#     managed through AllomorphOperations, not this class.
#

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# Import wrapper classes
from .affix_template import AffixTemplate
from .affix_template_collection import AffixTemplateCollection
from .compound_rule import CompoundRule
from .compound_rule_collection import CompoundRuleCollection

# Import FLEx LCM types
from SIL.LCModel import (
    IMoEndoCompoundFactory,
    IMoExoCompoundFactory,
    IMoInflAffixTemplateFactory,
    IPartOfSpeech,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class MorphRuleOperations(BaseOperations):
    """
    Operations for managing morphological rules in a FieldWorks project.

    Morphological rules are distributed across the LCM data model:

    - **Compound rules** (MoMorphData.CompoundRulesOS): Define compound word
      formation patterns (endocentric and exocentric).
    - **Affix templates** (PartOfSpeech.AffixTemplatesOS): Define inflectional
      affix template morphology per part of speech.
    - **Ad hoc co-prohibitions** (MoMorphData.AdhocCoProhibitionsOC): Define
      morpheme co-occurrence restrictions (separate property interface).

    Usage::

        from flexlibs2 import FLExProject, MorphRuleOperations

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        ruleOps = MorphRuleOperations(project)

        # Get all compound rules
        for rule in ruleOps.GetAllCompoundRules():
            print(ruleOps.GetName(rule), rule.ClassName)

        # Get all affix templates across all parts of speech
        for template in ruleOps.GetAllAffixTemplates():
            print(ruleOps.GetName(template))

        # Get affix templates for a specific POS
        verb = posOps.Find("Verb")
        for template in ruleOps.GetAllAffixTemplatesForPOS(verb):
            print(ruleOps.GetName(template))

        # Create a compound rule
        rule = ruleOps.CreateCompoundRule("Noun-Noun Compound")

        # Create an affix template on a POS
        template = ruleOps.CreateAffixTemplate(verb, "Verb Inflection")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize MorphRuleOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Return the appropriate rule sequence for reordering.

        Supports two parent types:
        - MoMorphData → CompoundRulesOS
        - PartOfSpeech → AffixTemplatesOS

        Ad hoc co-prohibitions are in an owning collection (OC),
        not an owning sequence (OS), so reordering does not apply.
        """
        if hasattr(parent, "CompoundRulesOS"):
            return parent.CompoundRulesOS
        elif hasattr(parent, "AffixTemplatesOS"):
            return parent.AffixTemplatesOS
        raise ValueError("Parent must be MoMorphData (for compound rules) or " "PartOfSpeech (for affix templates)")

    # ========== ENUMERATION ==========

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all compound rules and affix templates in the project.

        Yields items from CompoundRulesOS and AffixTemplatesOS. All yielded
        items support GetName, GetDescription, and GetStratum.

        Ad hoc co-prohibitions are NOT included (different property interface);
        use GetAllAdhocCoProhibitions() separately.

        Yields:
            Each compound rule or affix template object.

        Example:
            >>> ruleOps = MorphRuleOperations(project)
            >>> for rule in ruleOps.GetAll():
            ...     name = ruleOps.GetName(rule)
            ...     print(f"{name} ({rule.ClassName})")
            Noun-Noun Compound (MoEndoCompound)
            Verb Inflection (MoInflAffixTemplate)

        See Also:
            GetAllCompoundRules, GetAllAffixTemplates, GetAllAdhocCoProhibitions
        """
        yield from self.GetAllCompoundRules()
        yield from self.GetAllAffixTemplates()

    @OperationsMethod
    def GetAllCompoundRules(self):
        """
        Get all compound rules from MoMorphData.CompoundRulesOS.

        Returns:
            CompoundRuleCollection: Collection of CompoundRule wrapper objects
                (MoEndoCompound or MoExoCompound).

        Example:
            >>> rules = ruleOps.GetAllCompoundRules()
            >>> for rule in rules:
            ...     print(rule.name, rule.is_endo_compound)
            Noun-Noun True

        Notes:
            - Compound rules define patterns for compound word formation
            - MoEndoCompound: head is inside the compound
            - MoExoCompound: head is outside (e.g., exocentric compounds)
            - Returns empty collection if no morphological data defined
            - Returns CompoundRuleCollection (supports filtering and chaining)

        See Also:
            CreateCompoundRule, GetAll, CompoundRuleCollection
        """
        morph_data = self.project.lp.MorphologicalDataOA
        if morph_data is not None:
            wrapped = [CompoundRule(rule) for rule in morph_data.CompoundRulesOS]
            return CompoundRuleCollection(wrapped)
        return CompoundRuleCollection()

    @OperationsMethod
    def GetAllAffixTemplates(self):
        """
        Get all inflectional affix templates from all parts of speech.

        Walks the entire POS hierarchy and returns templates from each POS
        as a smart collection with filtering capabilities.

        Returns:
            AffixTemplateCollection: Collection of AffixTemplate wrapper objects
                from all parts of speech.

        Example:
            >>> templates = ruleOps.GetAllAffixTemplates()
            >>> verb_templates = templates.filter(name_contains='Verb')
            >>> prefix_templates = templates.with_prefix_slots()
            >>> for template in prefix_templates:
            ...     print(template.name, template.prefix_slot_count)

        Notes:
            - Affix templates are owned by PartOfSpeech, not MoMorphData
            - Each POS can have its own set of templates
            - Subcategories are included (full hierarchy walk)
            - Returns AffixTemplateCollection (supports filtering and chaining)
            - Use with_prefix_slots(), with_suffix_slots(), etc. for filtering

        See Also:
            GetAllAffixTemplatesForPOS, CreateAffixTemplate, GetAll, AffixTemplateCollection
        """
        templates = []
        pos_list = self.project.lp.PartsOfSpeechOA
        if pos_list is not None:
            for raw in pos_list.PossibilitiesOS:
                pos = IPartOfSpeech(raw)
                templates.extend(self.__WalkPOSForTemplates(pos))
        wrapped = [AffixTemplate(t) for t in templates]
        return AffixTemplateCollection(wrapped)

    @OperationsMethod
    def GetAllAffixTemplatesForPOS(self, pos_or_hvo):
        """
        Get affix templates for a specific part of speech (non-recursive).

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO.

        Returns:
            AffixTemplateCollection: Collection of AffixTemplate wrapper objects
                on the given POS.

        Raises:
            FP_NullParameterError: If pos_or_hvo is None.

        Example:
            >>> verb = posOps.Find("Verb")
            >>> templates = ruleOps.GetAllAffixTemplatesForPOS(verb)
            >>> prefix = templates.with_prefix_slots()
            >>> for template in prefix:
            ...     print(template.name)

        Notes:
            - Only returns templates directly owned by this POS
            - Does not include templates from sub-categories
            - Use GetAllAffixTemplates() to get templates from all POS
            - Returns AffixTemplateCollection (supports filtering and chaining)

        See Also:
            GetAllAffixTemplates, CreateAffixTemplate, AffixTemplateCollection
        """
        self._ValidateParam(pos_or_hvo, "pos_or_hvo")

        pos = self.__ResolveObject(pos_or_hvo)
        if hasattr(pos, "AffixTemplatesOS"):
            wrapped = [AffixTemplate(t) for t in pos.AffixTemplatesOS]
            return AffixTemplateCollection(wrapped)
        return AffixTemplateCollection()

    @OperationsMethod
    def GetAllAdhocCoProhibitions(self):
        """
        Get all ad hoc co-occurrence prohibitions from MoMorphData.

        These have a different property interface from compound rules and
        affix templates (no Name/Description). Use rule.ClassName to
        determine the subtype: MoAdhocProhibGr, MoAdhocProhibMorph,
        or MoAdhocProhibAllomorph.

        Yields:
            IMoAdhocProhib: Each co-occurrence prohibition.

        Example:
            >>> for prohib in ruleOps.GetAllAdhocCoProhibitions():
            ...     print(prohib.ClassName)

        Notes:
            - These are in an owning collection (OC), not a sequence (OS)
            - Reordering methods do not apply to co-prohibitions
            - Not included in GetAll() due to different property interface

        See Also:
            GetAll
        """
        morph_data = self.project.lp.MorphologicalDataOA
        if morph_data is not None:
            for prohib in morph_data.AdhocCoProhibitionsOC:
                yield prohib

    # ========== CREATION ==========

    @OperationsMethod
    def CreateCompoundRule(self, name, endocentric=True, description=None):
        """
        Create a new compound rule in MoMorphData.CompoundRulesOS.

        Args:
            name (str): The name of the compound rule.
            endocentric (bool): If True (default), creates MoEndoCompound.
                If False, creates MoExoCompound.
            description (str, optional): Optional description.

        Returns:
            IMoCompoundRule: The newly created compound rule.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name is None.
            FP_ParameterError: If name is empty or no morphological data.

        Example:
            >>> rule = ruleOps.CreateCompoundRule("Noun-Noun Compound")
            >>> exo = ruleOps.CreateCompoundRule("Verb-Noun", endocentric=False)

        Notes:
            - MoEndoCompound: head is inside the compound
            - MoExoCompound: head is outside the compound
            - New rules are added at the end of CompoundRulesOS

        See Also:
            CreateAffixTemplate, Delete, GetAllCompoundRules
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        morph_data = self.project.lp.MorphologicalDataOA
        if morph_data is None:
            raise FP_ParameterError("Project has no morphological data defined")

        wsHandle = self.project.project.DefaultAnalWs

        if endocentric:
            factory = self.project.project.ServiceLocator.GetService(IMoEndoCompoundFactory)
        else:
            factory = self.project.project.ServiceLocator.GetService(IMoExoCompoundFactory)

        with self._TransactionCM(f"Create compound rule '{name}'"):
            new_rule = factory.Create()
            morph_data.CompoundRulesOS.Add(new_rule)

            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_rule.Name.set_String(wsHandle, mkstr_name)

            if description:
                mkstr_desc = TsStringUtils.MakeString(description, wsHandle)
                new_rule.Description.set_String(wsHandle, mkstr_desc)

            return new_rule

    @OperationsMethod
    def CreateAffixTemplate(self, pos_or_hvo, name, description=None):
        """
        Create a new inflectional affix template on a part of speech.

        Args:
            pos_or_hvo: The IPartOfSpeech object or HVO to own the template.
            name (str): The name of the template.
            description (str, optional): Optional description.

        Returns:
            IMoInflAffixTemplate: The newly created affix template.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If pos_or_hvo or name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> verb = posOps.Find("Verb")
            >>> template = ruleOps.CreateAffixTemplate(verb, "Verb Inflection")
            >>> print(ruleOps.GetName(template))
            Verb Inflection

        Notes:
            - Templates are owned by PartOfSpeech, not MoMorphData
            - New templates are added at the end of AffixTemplatesOS
            - Slot assignments (prefix/suffix slots) must be configured separately

        See Also:
            CreateCompoundRule, Delete, GetAllAffixTemplates
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(pos_or_hvo, "pos_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        pos = self.__ResolveObject(pos_or_hvo)
        wsHandle = self.project.project.DefaultAnalWs

        factory = self.project.project.ServiceLocator.GetService(IMoInflAffixTemplateFactory)

        with self._TransactionCM(f"Create affix template '{name}'"):
            new_template = factory.Create()

            pos.AffixTemplatesOS.Add(new_template)

            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_template.Name.set_String(wsHandle, mkstr_name)

            if description:
                mkstr_desc = TsStringUtils.MakeString(description, wsHandle)
                new_template.Description.set_String(wsHandle, mkstr_desc)

            return new_template

    # ========== DELETION ==========

    @OperationsMethod
    def Delete(self, rule_or_hvo):
        """
        Delete a morphological rule.

        Automatically determines the owning collection based on ClassName
        and removes the rule from its parent.

        Args:
            rule_or_hvo: The rule object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> ruleOps.Delete(rule)

        Warning:
            - Deletion is permanent and cannot be undone
            - Deleting a rule that is referenced elsewhere may cause errors
            - Consider disabling instead of deleting (SetDisabled)

        See Also:
            CreateCompoundRule, CreateAffixTemplate, SetDisabled
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(rule_or_hvo, "rule_or_hvo")

        rule = self.__ResolveObject(rule_or_hvo)
        class_name = rule.ClassName

        morph_data = self.project.lp.MorphologicalDataOA

        if class_name in ("MoEndoCompound", "MoExoCompound"):
            if morph_data is not None:
                morph_data.CompoundRulesOS.Remove(rule)
        elif class_name == "MoInflAffixTemplate":
            # Template is owned by a PartOfSpeech
            owner = self._GetObject(rule.Owner.Hvo)
            if hasattr(owner, "AffixTemplatesOS"):
                owner.AffixTemplatesOS.Remove(rule)
        elif class_name in ("MoAdhocProhibGr", "MoAdhocProhibMorph", "MoAdhocProhibAllomorph"):
            if morph_data is not None:
                morph_data.AdhocCoProhibitionsOC.Remove(rule)

    # ========== PROPERTIES ==========

    @OperationsMethod
    def GetName(self, rule_or_hvo, wsHandle=None):
        """
        Get the name of a morphological rule or template.

        Args:
            rule_or_hvo: The rule object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The rule name, or empty string if not set.

        Raises:
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> for rule in ruleOps.GetAll():
            ...     print(ruleOps.GetName(rule))

        See Also:
            SetName, GetDescription
        """
        self._ValidateParam(rule_or_hvo, "rule_or_hvo")

        rule = self.__ResolveObject(rule_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        name = ITsString(rule.Name.get_String(wsHandle)).Text
        return name or ""

    @OperationsMethod
    def SetName(self, rule_or_hvo, name, wsHandle=None):
        """
        Set the name of a morphological rule or template.

        Args:
            rule_or_hvo: The rule object or HVO.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If rule_or_hvo or name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> ruleOps.SetName(rule, "Noun-Noun Compound")

        See Also:
            GetName, SetDescription
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(rule_or_hvo, "rule_or_hvo")
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        rule = self.__ResolveObject(rule_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(name, wsHandle)
        rule.Name.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetDescription(self, rule_or_hvo, wsHandle=None):
        """
        Get the description of a morphological rule or template.

        Args:
            rule_or_hvo: The rule object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The rule description, or empty string if not set.

        Raises:
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> for rule in ruleOps.GetAll():
            ...     print(ruleOps.GetDescription(rule))

        See Also:
            SetDescription, GetName
        """
        self._ValidateParam(rule_or_hvo, "rule_or_hvo")

        rule = self.__ResolveObject(rule_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        desc = ITsString(rule.Description.get_String(wsHandle)).Text
        return desc or ""

    @OperationsMethod
    def SetDescription(self, rule_or_hvo, description, wsHandle=None):
        """
        Set the description of a morphological rule or template.

        Args:
            rule_or_hvo: The rule object or HVO.
            description (str): The new description.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If rule_or_hvo or description is None.

        Example:
            >>> ruleOps.SetDescription(rule, "Forms compound nouns")

        See Also:
            GetDescription, SetName
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(rule_or_hvo, "rule_or_hvo")
        self._ValidateParam(description, "description")

        rule = self.__ResolveObject(rule_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        mkstr = TsStringUtils.MakeString(description, wsHandle)
        rule.Description.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetStratum(self, rule_or_hvo):
        """
        Get the stratum of a morphological rule or template.

        Args:
            rule_or_hvo: The rule object or HVO.

        Returns:
            IMoStratum or None: The stratum object if set, None otherwise.

        Raises:
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> stratum = ruleOps.GetStratum(rule)
            >>> if stratum:
            ...     print(stratum.Name.BestAnalysisAlternative.Text)

        Notes:
            - Both compound rules and affix templates can reference a stratum
            - Strata define ordering levels for rule application
            - Returns None if no stratum is assigned

        See Also:
            SetStratum
        """
        self._ValidateParam(rule_or_hvo, "rule_or_hvo")

        rule = self.__ResolveObject(rule_or_hvo)

        if hasattr(rule, "StratumRA") and rule.StratumRA:
            return rule.StratumRA

        return None

    @OperationsMethod
    def SetStratum(self, rule_or_hvo, stratum):
        """
        Set the stratum of a morphological rule or template.

        Args:
            rule_or_hvo: The rule object or HVO.
            stratum: The IMoStratum object, HVO, or None to clear.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> morph_data = project.lp.MorphologicalDataOA
            >>> if morph_data and morph_data.StrataOS.Count > 0:
            ...     ruleOps.SetStratum(rule, morph_data.StrataOS[0])

            >>> # Clear stratum assignment
            >>> ruleOps.SetStratum(rule, None)

        See Also:
            GetStratum
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(rule_or_hvo, "rule_or_hvo")

        rule = self.__ResolveObject(rule_or_hvo)

        if hasattr(rule, "StratumRA"):
            if stratum is None:
                rule.StratumRA = None
            else:
                if isinstance(stratum, int):
                    stratum = self.project.Object(stratum)
                rule.StratumRA = stratum

    @OperationsMethod
    def IsDisabled(self, rule_or_hvo):
        """
        Check if a morphological rule is disabled.

        Args:
            rule_or_hvo: The rule object or HVO.

        Returns:
            bool: True if the rule is disabled, False otherwise.

        Raises:
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> for rule in ruleOps.GetAllCompoundRules():
            ...     status = "disabled" if ruleOps.IsDisabled(rule) else "active"
            ...     print(f"{ruleOps.GetName(rule)}: {status}")

        Notes:
            - Returns False if the rule type does not have a Disabled property

        See Also:
            SetDisabled
        """
        self._ValidateParam(rule_or_hvo, "rule_or_hvo")

        rule = self.__ResolveObject(rule_or_hvo)

        if hasattr(rule, "Disabled"):
            return rule.Disabled

        return False

    @OperationsMethod
    def SetDisabled(self, rule_or_hvo, disabled):
        """
        Set the disabled state of a morphological rule.

        Args:
            rule_or_hvo: The rule object or HVO.
            disabled (bool): True to disable the rule, False to enable.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If rule_or_hvo or disabled is None.

        Example:
            >>> ruleOps.SetDisabled(rule, True)   # Disable
            >>> ruleOps.SetDisabled(rule, False)  # Enable

        Notes:
            - No-op if the rule type does not have a Disabled property

        See Also:
            IsDisabled
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(rule_or_hvo, "rule_or_hvo")
        self._ValidateParam(disabled, "disabled")

        rule = self.__ResolveObject(rule_or_hvo)

        if hasattr(rule, "Disabled"):
            rule.Disabled = bool(disabled)

    # ========== DUPLICATION ==========

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True):
        """
        Duplicate a morphological rule or template, creating a copy with a new GUID.

        Handles compound rules (MoEndoCompound, MoExoCompound) and affix
        templates (MoInflAffixTemplate). Uses the appropriate factory for
        each type and inserts into the correct owning collection.

        Args:
            item_or_hvo: The rule object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source.
                If False, insert at end of collection.
            deep (bool): If True, copy reference sequences (slot assignments
                for affix templates). If False (default), only copy simple
                properties.

        Returns:
            The newly created duplicate with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.
            FP_ParameterError: If the rule type is not supported for duplication.

        Example:
            >>> copy = ruleOps.Duplicate(compound_rule)
            >>> print(ruleOps.GetName(copy))

            >>> # Deep copy affix template (includes slot references)
            >>> copy = ruleOps.Duplicate(template, deep=True)

        Notes:
            - Factory.Create() automatically generates a new GUID
            - Simple properties copied: Name, Description (MultiString)
            - Reference property copied: StratumRA
            - Boolean properties copied: Disabled, HeadLast, Final (where applicable)
            - deep=True for affix templates copies PrefixSlotsRS, SuffixSlotsRS,
              ProcliticSlotsRS, EncliticSlotsRS (references to existing slot objects)

        See Also:
            CreateCompoundRule, CreateAffixTemplate, Delete
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        source = self.__ResolveObject(item_or_hvo)
        class_name = source.ClassName

        with self._TransactionCM(f"Duplicate {class_name}"):
            # Create duplicate and add to owning collection
            if class_name in ("MoEndoCompound", "MoExoCompound"):
                duplicate = self.__DuplicateCompoundRule(source, class_name, insert_after)
            elif class_name == "MoInflAffixTemplate":
                duplicate = self.__DuplicateAffixTemplate(source, insert_after)
            else:
                raise FP_ParameterError(f"Unsupported rule type for duplication: {class_name}")

            # Copy MultiString properties (AFTER adding to parent)
            duplicate.Name.CopyAlternatives(source.Name)
            duplicate.Description.CopyAlternatives(source.Description)

            # Copy Reference Atomic (RA) properties
            if hasattr(source, "StratumRA") and source.StratumRA:
                duplicate.StratumRA = source.StratumRA

            # Copy boolean properties (where applicable)
            if hasattr(source, "Disabled"):
                duplicate.Disabled = source.Disabled
            if hasattr(source, "HeadLast"):
                duplicate.HeadLast = source.HeadLast
            if hasattr(source, "Final"):
                duplicate.Final = source.Final

            # Deep copy: reference sequences for affix templates
            if deep and class_name == "MoInflAffixTemplate":
                for slot_prop in ("PrefixSlotsRS", "SuffixSlotsRS", "ProcliticSlotsRS", "EncliticSlotsRS"):
                    if hasattr(source, slot_prop) and hasattr(duplicate, slot_prop):
                        src_slots = getattr(source, slot_prop)
                        dst_slots = getattr(duplicate, slot_prop)
                        for slot in src_slots:
                            dst_slots.Add(slot)

            return duplicate

    def __DuplicateCompoundRule(self, source, class_name, insert_after):
        """Create and insert a duplicate compound rule."""
        if class_name == "MoEndoCompound":
            factory = self.project.project.ServiceLocator.GetService(IMoEndoCompoundFactory)
        else:
            factory = self.project.project.ServiceLocator.GetService(IMoExoCompoundFactory)

        duplicate = factory.Create()
        morph_data = self.project.lp.MorphologicalDataOA

        if insert_after:
            idx = morph_data.CompoundRulesOS.IndexOf(source)
            morph_data.CompoundRulesOS.Insert(idx + 1, duplicate)
        else:
            morph_data.CompoundRulesOS.Add(duplicate)

        return duplicate

    def __DuplicateAffixTemplate(self, source, insert_after):
        """Create and insert a duplicate affix template on the same POS."""
        factory = self.project.project.ServiceLocator.GetService(IMoInflAffixTemplateFactory)
        duplicate = factory.Create()

        owner = self._GetObject(source.Owner.Hvo)

        if insert_after:
            idx = owner.AffixTemplatesOS.IndexOf(source)
            owner.AffixTemplatesOS.Insert(idx + 1, duplicate)
        else:
            owner.AffixTemplatesOS.Add(duplicate)

        return duplicate

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project synchronization.

        Args:
            item: The rule or template object.

        Returns:
            dict: Dictionary mapping property names to their values.

        Example:
            >>> props = ruleOps.GetSyncableProperties(rule)
            >>> print(props.keys())
            dict_keys(['Name', 'Description', 'StratumGuid', 'Disabled'])

        Notes:
            - Returns all MultiString properties (all writing systems)
            - Returns boolean properties (Disabled, HeadLast, Final)
            - Returns StratumGuid as string (GUID of referenced stratum)
        """
        rule = self.__ResolveObject(item)

        # Get all writing systems for MultiString properties
        # Fix: ILgWritingSystemFactory does not expose a .WritingSystems
        # property; enumerate via the wrapper's WritingSystemOperations.GetAll(),
        # which returns CoreWritingSystemDefinition objects with .Id / .Handle.
        all_ws = {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()}

        props = {}

        # MultiString properties
        for prop_name in ["Name", "Description"]:
            if hasattr(rule, prop_name):
                prop_obj = getattr(rule, prop_name)
                ws_values = {}
                for ws_id, ws_handle in all_ws.items():
                    text = ITsString(prop_obj.get_String(ws_handle)).Text
                    if text:
                        ws_values[ws_id] = text
                if ws_values:
                    props[prop_name] = ws_values

        # Boolean properties
        for prop_name in ["Disabled", "HeadLast", "Final"]:
            if hasattr(rule, prop_name):
                props[prop_name] = getattr(rule, prop_name)

        # Reference Atomic (RA) properties - return GUID as string
        if hasattr(rule, "StratumRA") and rule.StratumRA:
            props["StratumGuid"] = str(rule.StratumRA.Guid)

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
        Compare two morphological rules and return detailed differences.

        Args:
            item1: First rule to compare (from source project).
            item2: Second rule to compare (from target project).
            ops1: Optional MorphRuleOperations instance for item1's project.
                 Defaults to self.
            ops2: Optional MorphRuleOperations instance for item2's project.
                 Defaults to self.

        Returns:
            tuple: (is_different, differences) where:
                - is_different (bool): True if items differ
                - differences (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> is_diff, diffs = ruleOps.CompareTo(rule1, rule2)
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} -> {val2}")
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        is_different = False
        differences = {}

        all_keys = set(props1.keys()) | set(props2.keys())
        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)

            if val1 != val2:
                is_different = True
                differences[key] = (val1, val2)

        return (is_different, differences)

    # ========== PRIVATE HELPERS ==========

    def __ResolveObject(self, rule_or_hvo):
        """Resolve HVO or object to LCM object."""
        if isinstance(rule_or_hvo, int):
            return self.project.Object(rule_or_hvo)
        return rule_or_hvo

    def __WSHandle(self, wsHandle):
        """Get writing system handle, defaulting to analysis WS."""
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

    def __WalkPOSForTemplates(self, pos):
        """Recursively yield affix templates from a POS and its subcategories."""
        for template in pos.AffixTemplatesOS:
            yield template
        for raw in pos.SubPossibilitiesOS:
            sub = IPartOfSpeech(raw)
            yield from self.__WalkPOSForTemplates(sub)
