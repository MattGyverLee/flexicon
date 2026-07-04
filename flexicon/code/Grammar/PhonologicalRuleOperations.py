#
#   PhonologicalRuleOperations.py
#
#   Class: PhonologicalRuleOperations
#          Phonological rule operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable
from ..Shared.string_utils import normalize_match_key

# Import FLEx LCM types
from SIL.LCModel import (
    IPhRegularRuleFactory,  # Fixed: was IPhPhonRuleFactory
    IPhSegRuleRHSFactory,
    IPhSegmentRuleFactory,
    IPhSimpleContextNC,
    IPhSimpleContextNCFactory,
    IPhSimpleContextSegFactory,
    IPhSimpleContextBdryFactory,
    IPhSequenceContext,
    IPhSequenceContextFactory,
    IPhFeatureConstraintFactory,
    IPhFeatureConstraint,
    IPhIterationContextFactory,
    ICmObjectRepository,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import pattern-element dataclasses for the WireRule composer
from ..Shared.rule_patterns import Seg, NC, Boundary

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)


class PhonologicalRuleOperations(BaseOperations):
    """
    This class provides operations for managing phonological rules in a
    FieldWorks project.

    Phonological rules define systematic sound changes that apply in specific
    phonological environments. They consist of input specifications, output
    specifications, and contextual conditions.

    Usage::

        from flexlibs2 import FLExProject, PhonologicalRuleOperations

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        phonRuleOps = PhonologicalRuleOperations(project)

        # Get all phonological rules
        for rule in phonRuleOps.GetAll():
            name = phonRuleOps.GetName(rule)
            desc = phonRuleOps.GetDescription(rule)
            print(f"{name}: {desc}")

        # Create a new phonological rule
        rule = phonRuleOps.Create("Voicing Assimilation")
        phonRuleOps.SetDescription(rule, "Obstruents become voiced before vowels")

        # Wire the rule via WireRule (the supported composer).
        # SetLeftContext / SetRightContext are refused with
        # NotImplementedError (they wrote to the wrong owner -- see #142).
        from flexlibs2 import Seg, NC
        phonRuleOps.WireRule(rule,
            input_pattern=[Seg(phoneme_t)],
            output_change=[Seg(phoneme_d)],
            right_context=[NC(vowel_class)],
        )

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize PhonologicalRuleOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for phonological rules.
        For PhonologicalRule, we reorder parent.PhonRulesOS
        """
        return parent.PhonRulesOS

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Get all phonological rules in the project.

        Returns:
            RuleCollection: Smart collection of PhonologicalRule wrapped objects.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> rules = phonRuleOps.GetAll()
            >>> print(rules)  # Shows type breakdown
            RuleCollection (12 total)
              PhRegularRule: 7 (58%)
              PhMetathesisRule: 3 (25%)
              PhReduplicationRule: 2 (17%)

            >>> # Access individual rules
            >>> for rule in rules:
            ...     print(rule.name)

            >>> # Filter to specific type
            >>> regular_only = rules.regular_rules()

            >>> # Filter by name
            >>> voicing_rules = rules.filter(name_contains='voicing')

        Notes:
            - Returns RuleCollection (smart collection) instead of generator
            - Wrapped rules hide ClassName/casting complexity
            - Use rule.name instead of GetName(rule)
            - Use rule.input_contexts instead of accessing StrucDescOS
            - Returns empty collection if no phonological data defined
            - Type breakdown is visible when printed

        See Also:
            Create, Find, RuleCollection, PhonologicalRule
        """
        from .phonological_rule import PhonologicalRule
        from .rule_collection import RuleCollection

        phon_data = self.project.lp.PhonologicalDataOA
        if not phon_data:
            return RuleCollection()

        rules = []
        if hasattr(phon_data, "PhonRulesOS"):
            for rule in phon_data.PhonRulesOS:
                wrapped = PhonologicalRule(rule)
                rules.append(wrapped)

        return RuleCollection(rules)

    @OperationsMethod
    def Create(self, name, description=None):
        """
        Create a new phonological rule.

        Args:
            name (str): The name of the rule (e.g., "Voicing Assimilation").
            description (str, optional): Optional description of the rule.
                Defaults to None.

        Returns:
            IPhPhonRule: The newly created phonological rule object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> rule = phonRuleOps.Create("Voicing Assimilation",
            ...     "Voiceless stops become voiced between vowels")
            >>> print(phonRuleOps.GetName(rule))
            Voicing Assimilation

            >>> # Create and configure
            >>> rule = phonRuleOps.Create("Final Devoicing")
            >>> phonRuleOps.SetDescription(rule, "Obstruents devoice word-finally")

        Notes:
            - Name should describe the phonological process
            - Description is optional but recommended
            - Rule is created in the default analysis writing system
            - New rules start as inactive by default
            - Must add input/output specifications separately

        See Also:
            Delete, SetDescription, WireRule
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        # Get the writing system handle
        wsHandle = self.project.project.DefaultAnalWs

        # Create the new phonological rule using the factory
        factory = self.project.project.ServiceLocator.GetService(IPhRegularRuleFactory)

        # Pre-flight: ensure the phonological data container exists before creating any object.
        phon_data = self.project.lp.PhonologicalDataOA
        if not phon_data:
            raise FP_ParameterError("Project has no phonological data defined")

        with self._TransactionCM(f"Create phonological rule {name!r}"):
            new_rule = factory.Create()

            # Add to the phonological rules collection (must be done before setting properties)
            phon_data.PhonRulesOS.Add(new_rule)

            # Set name
            mkstr_name = TsStringUtils.MakeString(name, wsHandle)
            new_rule.Name.set_String(wsHandle, mkstr_name)

            # Set description if provided
            if description:
                mkstr_desc = TsStringUtils.MakeString(description, wsHandle)
                new_rule.Description.set_String(wsHandle, mkstr_desc)

            return new_rule

    @OperationsMethod
    def Delete(self, rule_or_hvo):
        """
        Delete a phonological rule.

        Args:
            rule_or_hvo: The IPhPhonRule object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> obsolete = phonRuleOps.Create("Obsolete Rule")
            >>> # ... realize it's not needed
            >>> phonRuleOps.Delete(obsolete)

        Warning:
            - Deletion is permanent and cannot be undone
            - Any references to this rule will be broken
            - Consider deactivating instead of deleting

        See Also:
            Create, GetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(rule_or_hvo, "rule_or_hvo")

        # Resolve to rule object
        rule = self.__ResolveObject(rule_or_hvo)

        # Remove from phonological rules collection
        phon_data = self.project.lp.PhonologicalDataOA
        if phon_data and hasattr(phon_data, "PhonRulesOS"):
            if rule in phon_data.PhonRulesOS:
                phon_data.PhonRulesOS.Remove(rule)

    @OperationsMethod
    def Exists(self, name):
        """
        Check if a phonological rule with the given name exists.

        Args:
            name (str): The name to search for.

        Returns:
            bool: True if a rule with this name exists, False otherwise.

        Raises:
            FP_NullParameterError: If name is None.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> if phonRuleOps.Exists("Voicing Assimilation"):
            ...     print("Rule already exists")
            >>> else:
            ...     rule = phonRuleOps.Create("Voicing Assimilation")

        See Also:
            Find, GetAll, Create
        """
        self._ValidateParam(name, "name")

        return self.Find(name) is not None

    @OperationsMethod
    def Find(self, name):
        """
        Find a phonological rule by name.

        Args:
            name (str): The name to search for (case-insensitive).

        Returns:
            PhonologicalRule or None: The wrapped rule object if found, None otherwise.

        Raises:
            FP_NullParameterError: If name is None.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> rule = phonRuleOps.Find("Voicing Assimilation")
            >>> if rule:
            ...     print(f"Found: {rule.name}")
            ...     print(f"Direction: {rule.direction}")

            >>> # Case-insensitive search
            >>> rule = phonRuleOps.Find("voicing assimilation")

        Notes:
            - Search is case-insensitive
            - Returns first matching rule if multiple exist
            - Searches in default analysis writing system
            - Returns wrapped PhonologicalRule, not raw LCM object

        See Also:
            Exists, GetAll, PhonologicalRule
        """
        self._ValidateParam(name, "name")

        target = normalize_match_key(name, casefold=True)
        for wrapped_rule in self.GetAll():
            if normalize_match_key(wrapped_rule.name, casefold=True) == target:
                return wrapped_rule

        return None

    @OperationsMethod
    def GetName(self, rule_or_hvo, wsHandle=None):
        """
        Get the name of a phonological rule.

        Args:
            rule_or_hvo: The IPhPhonRule object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The rule name, or empty string if not set.

        Raises:
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> for rule in phonRuleOps.GetAll():
            ...     name = phonRuleOps.GetName(rule)
            ...     print(name)
            Voicing Assimilation
            Final Devoicing

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
        Set the name of a phonological rule.

        Args:
            rule_or_hvo: The IPhPhonRule object or HVO.
            name (str): The new name.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If rule_or_hvo or name is None.
            FP_ParameterError: If name is empty.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> rule = list(phonRuleOps.GetAll())[0]
            >>> phonRuleOps.SetName(rule, "Intervocalic Voicing")

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
        Get the description of a phonological rule.

        Args:
            rule_or_hvo: The IPhPhonRule object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The rule description, or empty string if not set.

        Raises:
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> for rule in phonRuleOps.GetAll():
            ...     name = phonRuleOps.GetName(rule)
            ...     desc = phonRuleOps.GetDescription(rule)
            ...     print(f"{name}: {desc}")

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
        Set the description of a phonological rule.

        Args:
            rule_or_hvo: The IPhPhonRule object or HVO.
            description (str): The new description.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If rule_or_hvo or description is None.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> rule = list(phonRuleOps.GetAll())[0]
            >>> phonRuleOps.SetDescription(rule,
            ...     "Voiceless stops become voiced between vowels")

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
        Get the stratum of a phonological rule.

        Args:
            rule_or_hvo: The IPhPhonRule object or HVO.

        Returns:
            IMoStratum or None: The stratum object if set, None otherwise.

        Raises:
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> rule = list(phonRuleOps.GetAll())[0]
            >>> stratum = phonRuleOps.GetStratum(rule)
            >>> if stratum:
            ...     print(f"Rule applies in stratum: {stratum.Name.BestAnalysisAlternative.Text}")

        Notes:
            - Strata define ordering levels for phonological rules
            - Rules in lower strata apply before rules in higher strata
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
        Set the stratum of a phonological rule.

        Args:
            rule_or_hvo: The IPhPhonRule object or HVO.
            stratum: The IMoStratum object, HVO, or None to clear.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> rule = list(phonRuleOps.GetAll())[0]
            >>> # Get first stratum
            >>> morph_data = project.lp.MorphologicalDataOA
            >>> if morph_data and morph_data.StrataOS.Count > 0:
            ...     stratum = morph_data.StrataOS[0]
            ...     phonRuleOps.SetStratum(rule, stratum)

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
    def GetDirection(self, rule_or_hvo):
        """
        Get the direction of rule application.

        Args:
            rule_or_hvo: The IPhPhonRule object or HVO.

        Returns:
            int: The direction value (0=left-to-right, 1=right-to-left,
                2=simultaneous).

        Raises:
            FP_NullParameterError: If rule_or_hvo is None.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> rule = list(phonRuleOps.GetAll())[0]
            >>> direction = phonRuleOps.GetDirection(rule)
            >>> if direction == 0:
            ...     print("Left-to-right application")

        See Also:
            SetDirection
        """
        self._ValidateParam(rule_or_hvo, "rule_or_hvo")

        rule = self.__ResolveObject(rule_or_hvo)

        if hasattr(rule, "Direction"):
            return rule.Direction

        return 0  # Default: left-to-right

    @OperationsMethod
    def SetDirection(self, rule_or_hvo, direction):
        """
        Set the direction of rule application.

        Args:
            rule_or_hvo: The IPhPhonRule object or HVO.
            direction (int): 0=left-to-right, 1=right-to-left, 2=simultaneous.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If rule_or_hvo is None.
            FP_ParameterError: If direction is not 0, 1, or 2.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> rule = list(phonRuleOps.GetAll())[0]
            >>> # Set to right-to-left
            >>> phonRuleOps.SetDirection(rule, 1)

        See Also:
            GetDirection
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(rule_or_hvo, "rule_or_hvo")

        if direction not in [0, 1, 2]:
            raise FP_ParameterError("Direction must be 0 (L-R), 1 (R-L), or 2 (simultaneous)")

        rule = self.__ResolveObject(rule_or_hvo)

        if hasattr(rule, "Direction"):
            rule.Direction = direction

    @OperationsMethod
    def SetLeftContext(self, rule_or_hvo, context_item):
        """
        Refuses with NotImplementedError.

        This method's previous implementation wrote to
        ``StrucDescOS[0].LeftContextOA``, but ``LeftContextOA`` /
        ``RightContextOA`` actually live on ``IPhSegRuleRHS`` (the
        structural-change/environment owner), not on
        ``IPhSimpleContext``. The method therefore never produced
        runnable rules -- the call appeared to succeed but the rule
        could not be applied. Refusing loudly is strictly better than
        silently emitting a non-runnable rule. (issue #142)

        Use :meth:`WireRule` instead, which writes to the correct
        ownership path (``rhs.LeftContextOA``) and supports
        Seg/NC/Boundary elements::

            project.PhonRules.WireRule(rule, left_context=[Seg('a')])

        Raises:
            NotImplementedError: Always.

        See Also:
            WireRule, SetRightContext
        """
        raise NotImplementedError(
            "SetLeftContext never produced runnable rules (it wrote to "
            "LeftContextOA on a simple context, but that property lives "
            "on IPhSegRuleRHS). Use WireRule(rule, left_context=...) "
            "instead. (issue #142)"
        )

    @OperationsMethod
    def SetRightContext(self, rule_or_hvo, context_item):
        """
        Refuses with NotImplementedError.

        This method's previous implementation wrote to
        ``StrucDescOS[0].RightContextOA``, but ``RightContextOA`` /
        ``LeftContextOA`` actually live on ``IPhSegRuleRHS``, not on
        ``IPhSimpleContext``. The method therefore never produced
        runnable rules. Refusing loudly is strictly better than
        silently emitting a non-runnable rule. (issue #142)

        Use :meth:`WireRule` instead, which writes to the correct
        ownership path (``rhs.RightContextOA``) and supports
        Seg/NC/Boundary elements::

            project.PhonRules.WireRule(rule, right_context=[NC(vowels)])

        Raises:
            NotImplementedError: Always.

        See Also:
            WireRule, SetLeftContext
        """
        raise NotImplementedError(
            "SetRightContext never produced runnable rules (it wrote to "
            "RightContextOA on a simple context, but that property lives "
            "on IPhSegRuleRHS). Use WireRule(rule, right_context=...) "
            "instead. (issue #142)"
        )

    # ========================================================================
    # ALPHA-FEATURE CONSTRAINTS (Greek-variable agreement)
    # ========================================================================

    @OperationsMethod
    def MakeConstraint(self, feature_or_hvo):
        """
        Create an alpha-feature constraint variable bound to a feature.

        Args:
            feature_or_hvo: An IFsFeatDefn object, HVO (int), or wrapper.

        Returns:
            IPhFeatureConstraint: The newly created feature constraint.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If feature_or_hvo is None.

        Example:
            >>> # Turkish vowel harmony: same backness as preceding vowel
            >>> feat_back = project.PhonFeatures.Find("back")
            >>> alpha_back = project.PhonRules.MakeConstraint(feat_back)
            >>> # Re-use alpha_back across positions for alpha-variable
            >>> # identity (the SAME object means the SAME alpha value)

        Notes:
            - Identity matters: pass the SAME returned object to multiple
              NC positions to express alpha-sharing (e.g. [aBack]...[aBack]).
            - Constraints are owned by
              ``project.lp.PhonologicalDataOA.FeatConstraintsOS``.
            - The Phase 2 ownership rule is applied: the constraint is
              attached to its owner BEFORE ``FeatureRA`` is set.

        See Also:
            DeleteConstraint, GetConstraints, WireRule
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(feature_or_hvo, "feature_or_hvo")

        feature = self.__ResolveFeature(feature_or_hvo)

        # Hardened path: raise on factory failure, no silent fallback.
        factory = self.project.project.ServiceLocator.GetService(
            IPhFeatureConstraintFactory
        )
        if factory is None:
            raise FP_ParameterError(
                "IPhFeatureConstraintFactory service is unavailable; "
                "cannot create feature constraint."
            )

        phon_data = self.project.lp.PhonologicalDataOA
        if not phon_data:
            raise FP_ParameterError("Project has no phonological data defined")

        with self._TransactionCM("Make feature constraint"):
            constraint = factory.Create()
            # Phase 2 ownership rule: attach BEFORE setting FeatureRA so the
            # LCM property setter doesn't NPE on an unowned constraint.
            phon_data.FeatConstraintsOS.Add(constraint)
            constraint.FeatureRA = feature

            return constraint

    @OperationsMethod
    def DeleteConstraint(self, constraint_or_hvo):
        """
        Delete a feature constraint from the project.

        Args:
            constraint_or_hvo: An IPhFeatureConstraint object or HVO.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If constraint_or_hvo is None.
            FP_ParameterError: If the constraint is not present in
                ``PhonologicalDataOA.FeatConstraintsOS``.

        Example:
            >>> alpha = project.PhonRules.MakeConstraint(feat_back)
            >>> # ... later ...
            >>> project.PhonRules.DeleteConstraint(alpha)

        Warning:
            Deletion is permanent. Any positions referencing this
            constraint (via ``PlusConstrRS`` / ``MinusConstrRS``) will
            lose the alpha-binding.

        See Also:
            MakeConstraint, GetConstraints
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(constraint_or_hvo, "constraint_or_hvo")

        constraint = self.__ResolveObject(constraint_or_hvo)

        phon_data = self.project.lp.PhonologicalDataOA
        if (
            not phon_data
            or not hasattr(phon_data, "FeatConstraintsOS")
            or constraint not in phon_data.FeatConstraintsOS
        ):
            raise FP_ParameterError(
                "constraint is not present in "
                "PhonologicalDataOA.FeatConstraintsOS"
            )
        phon_data.FeatConstraintsOS.Remove(constraint)

    @OperationsMethod
    def GetConstraints(self):
        """
        Get all feature constraints in the project.

        Returns:
            list[IPhFeatureConstraint]: All constraints in
            ``PhonologicalDataOA.FeatConstraintsOS``. Returns an empty
            list if no phonological data is defined.

        Example:
            >>> for c in project.PhonRules.GetConstraints():
            ...     feat = c.FeatureRA
            ...     print(feat.Name.BestAnalysisAlternative.Text)

        See Also:
            MakeConstraint, DeleteConstraint
        """
        phon_data = self.project.lp.PhonologicalDataOA
        if not phon_data or not hasattr(phon_data, "FeatConstraintsOS"):
            return []
        return list(phon_data.FeatConstraintsOS)

    # ========================================================================
    # HIGH-LEVEL RULE COMPOSER (WireRule)
    # ========================================================================

    @OperationsMethod
    def WireRule(self, rule_or_hvo, input_pattern=None, output_change=None,
                 left_context=None, right_context=None, mode="replace"):
        """
        High-level composer for phonological rules using SPE notation.

        Args:
            rule_or_hvo: The IPhSegmentRule (or HVO) to wire.
            input_pattern: List of one or more pattern elements (Seg/NC/Boundary)
                representing the rule's structural description (LHS).
            output_change: List of pattern elements (Seg/NC/Boundary) representing
                the structural change (RHS).
            left_context: List of pattern elements for the left-side context
                (right-justified to the focus position).
            right_context: List of pattern elements for the right-side context.
            mode: ``"replace"`` (default) clears existing slots before wiring;
                ``"append"`` adds to existing.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If rule_or_hvo is None.
            FP_ParameterError: If a pattern element is malformed (e.g. a
                Seg with alpha-feature constraints, or a Boundary appearing
                in the structural change).

        Notes:
            The composer translates pattern elements into LCM simple-context
            objects and attaches feature constraints to NC positions. The
            same IPhFeatureConstraint object can appear in multiple
            positions to express Greek-variable agreement (alpha-back,
            beta-round, etc.).

            **Ownership-ordering (Phase 2):** every context object is
            attached to its parent BEFORE its
            ``FeatureStructureRA`` / ``PlusConstrRS`` / ``MinusConstrRS``
            properties are populated.

            **LCM property locations:**
              - ``rule.StrucDescOS``: input pattern (structural description, LHS).
              - ``rhs.StrucChangeOS``: output change (RHS).
              - ``rhs.LeftContextOA``: left environment (NOT
                ``ctx.LeftContextOA`` -- the deprecated SetLeftContext
                method writes to the wrong owner).
              - ``rhs.RightContextOA``: right environment.

            **Multi-element contexts:**
              Left/right contexts of arbitrary length are supported. When
              ``len(left_context) > 1`` or ``len(right_context) > 1``, the
              wrapper creates each member as an IPhSimpleContext* attached
              to ``PhonologicalDataOA.ContextsOS`` (the project-level owner
              pool), then assembles an IPhSequenceContext whose MembersRS
              references them. This supports rules like Bantu glide
              formation ``i -> y / _ + V`` and place-assimilation
              ``N -> [alpha_place] / _ + C[alpha_place]``.

              **mode='replace' cleanup:** when an existing multi-element
              context is replaced, the previous members are removed from
              ``PhonologicalDataOA.ContextsOS`` first -- otherwise repeated
              re-wires (typical in MCP / batch rule-tuning workflows) leak
              N members per call into the project-wide pool. (issue #134)

            **Boundary markers:**
              Word/morpheme boundaries (Boundary('#'), Boundary('+'),
              Boundary('.')) are looked up from
              ``PhonemeSetsOS[0].BoundaryMarkersOC``; new markers are NOT
              created.

        Example:
            >>> # Turkish vowel harmony fragment: I -> [+back] / V[+back] _
            >>> from flexlibs2 import Seg, NC, Boundary
            >>> feat_back = project.PhonFeatures.Find("back")
            >>> alpha_back = project.PhonRules.MakeConstraint(feat_back)
            >>> rule = project.PhonRules.Create("Back harmony")
            >>> project.PhonRules.WireRule(rule,
            ...     input_pattern=[NC(archi_I)],
            ...     output_change=[NC(archi_I, plus=[alpha_back])],
            ...     left_context=[NC(vowels, plus=[alpha_back])],
            ...     right_context=None,
            ... )

        See Also:
            MakeConstraint, Create, Seg, NC, Boundary
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(rule_or_hvo, "rule_or_hvo")

        if mode not in ("replace", "append"):
            raise FP_ParameterError(
                f"mode must be 'replace' or 'append', got {mode!r}"
            )

        rule = self.__ResolveObject(rule_or_hvo)

        # Ensure the rule has an RHS to write into.
        if not hasattr(rule, "RightHandSidesOS"):
            raise FP_ParameterError(
                "Rule has no RightHandSidesOS; not a structural rule type."
            )
        # Pre-flight: if the rule has no RHS yet, verify the factory is available
        # before opening the transaction (avoids an orphaned mid-clear state on
        # mode="replace" when the factory is missing).
        if rule.RightHandSidesOS.Count == 0:
            rhs_factory = self.project.project.ServiceLocator.GetService(
                IPhSegRuleRHSFactory
            )
            if rhs_factory is None:
                raise FP_ParameterError(
                    "IPhSegRuleRHSFactory service is unavailable; "
                    "cannot create RHS for rule."
                )
        else:
            rhs_factory = None  # existing RHS will be reused; factory not needed

        with self._TransactionCM("Wire phonological rule"):
            if rule.RightHandSidesOS.Count == 0:
                rhs = rhs_factory.Create()
                # Attach BEFORE further property writes (Phase 2 ownership rule).
                rule.RightHandSidesOS.Add(rhs)
            rhs = rule.RightHandSidesOS[0]

            # --- Clear existing slots if mode == 'replace' ---
            if mode == "replace":
                self.__ClearSequence(rule.StrucDescOS)
                self.__ClearSequence(rhs.StrucChangeOS)
                # For multi-element contexts the members live in
                # PhPhonData.ContextsOS (the project-wide owner pool) and
                # are merely *referenced* by the sequence's MembersRS.
                # Nulling rhs.LeftContextOA / rhs.RightContextOA detaches
                # only the sequence container; the members would otherwise
                # leak into ContextsOS, accumulating across every re-wire
                # of the same rule. Clean those up first. (issue #134)
                self.__CleanupSequenceContextMembers(rhs.LeftContextOA)
                self.__CleanupSequenceContextMembers(rhs.RightContextOA)
                if rhs.LeftContextOA is not None:
                    rhs.LeftContextOA = None
                if rhs.RightContextOA is not None:
                    rhs.RightContextOA = None

            # --- Wire input pattern -> rule.StrucDescOS ---
            if input_pattern:
                for elem in input_pattern:
                    ctx = self.__BuildSimpleContext(elem, slot_name="input_pattern")
                    rule.StrucDescOS.Add(ctx)
                    self.__PopulateSimpleContext(ctx, elem)

            # --- Wire output change -> rhs.StrucChangeOS ---
            if output_change:
                for elem in output_change:
                    if isinstance(elem, Boundary):
                        raise FP_ParameterError(
                            "Boundary elements cannot appear in the structural "
                            "change -- only in left/right contexts."
                        )
                    ctx = self.__BuildSimpleContext(elem, slot_name="output_change")
                    rhs.StrucChangeOS.Add(ctx)
                    self.__PopulateSimpleContext(ctx, elem)

            # --- Wire left context -> rhs.LeftContextOA ---
            if left_context:
                ctx, deferred_elem = self.__WireContext(
                    left_context, slot_name="left_context"
                )
                # OwningAtomic: assignment IS the attach. Do NOT re-fetch via
                # rhs.LeftContextOA -- pythonnet narrows the proxy to the
                # IPhPhonContext base interface, losing access to concrete-type
                # properties like PlusConstrRS / MinusConstrRS. The local `ctx`
                # already points at the same LCM object with the concrete type.
                rhs.LeftContextOA = ctx
                if deferred_elem is not None:
                    # Single-element path: ctx is now owned by rhs; populate
                    # FeatureStructureRA / alpha constraints after the attach
                    # so LCM's validity check via Owner passes.
                    self.__PopulateSimpleContext(ctx, deferred_elem)

            # --- Wire right context -> rhs.RightContextOA ---
            if right_context:
                ctx, deferred_elem = self.__WireContext(
                    right_context, slot_name="right_context"
                )
                # See note on LeftContextOA above -- skip the defensive re-fetch.
                rhs.RightContextOA = ctx
                if deferred_elem is not None:
                    self.__PopulateSimpleContext(ctx, deferred_elem)

    # ------------------------------------------------------------------
    # WireRule internals
    # ------------------------------------------------------------------

    def __ClearSequence(self, seq):
        """Remove all elements from an owning sequence."""
        # Walk by index from the end to avoid index drift during removal.
        while seq.Count > 0:
            seq.RemoveAt(seq.Count - 1)

    def __CleanupSequenceContextMembers(self, ctx):
        """
        If ``ctx`` is an IPhSequenceContext, remove its MembersRS items
        from PhPhonData.ContextsOS. No-op for None or for single-context
        cases (where ``ctx`` is an IPhSimpleContext* owned directly by
        the rhs.LeftContextOA / RightContextOA OwningAtomic, so nulling
        the slot already detaches it). (issue #134)

        Multi-element contexts park their members in the project-wide
        ContextsOS owner pool while the sequence container references
        them via MembersRS. Setting rhs.LeftContextOA = None detaches
        only the sequence; the members would otherwise leak.
        """
        if ctx is None:
            return
        # ClassName check: IPhSequenceContext sequences vs IPhSimpleContext*
        # simple contexts. The simple-context concrete classes
        # (PhSimpleContextNC / PhSimpleContextSeg / PhSimpleContextBdry)
        # have no MembersRS and own their own state via rhs's
        # OwningAtomic slot, so they don't need this cleanup.
        if ctx.ClassName != "PhSequenceContext":
            return
        phon_data = self.project.lp.PhonologicalDataOA
        if phon_data is None:
            return
        seq_typed = IPhSequenceContext(ctx)
        # Snapshot the members because RemoveAt would shift indices,
        # and MembersRS may stop being readable once the sequence is
        # detached. Copy refs out, then remove from ContextsOS.
        members_to_remove = list(seq_typed.MembersRS)
        contexts_pool = phon_data.ContextsOS
        for member in members_to_remove:
            if member is not None:
                contexts_pool.Remove(member)

    def __WireContext(self, elements, slot_name):
        """
        Build the appropriate context object for a left/right context list.

        Returns ``(ctx, deferred_elem)``:

        * Single-element fast path: ``ctx`` is an unattached
          IPhSimpleContext*; ``deferred_elem`` is the source pattern
          element. The caller MUST assign ``ctx`` to
          rhs.LeftContextOA / RightContextOA first (the attach), then call
          ``__PopulateSimpleContext(ctx, deferred_elem)`` to set
          FeatureStructureRA + alpha constraints. Populating before the
          attach raises System.NullReferenceException from LCM's setter
          because the context's Owner is unset.

        * Multi-element path: each member is attached to
          PhonologicalDataOA.ContextsOS (the project-level owner pool)
          and fully populated inline, then an IPhSequenceContext is
          created and the members are added via MembersRS (reference-
          only list). ``ctx`` is the sequence (still unowned -- caller
          assigns to rhs.LeftContextOA / RightContextOA); ``deferred_elem``
          is None because no further population is required.

        Ownership-ordering trap (single AND multi paths): each
        IPhSimpleContext* must be owned BEFORE its FeatureStructureRA /
        constraint properties are populated. LCM's validity check runs
        through the context's Owner. See the diagnosis in issue #23.
        """
        if not elements:
            return None, None

        if len(elements) == 1:
            elem = elements[0]
            ctx = self.__BuildSimpleContext(elem, slot_name=slot_name)
            # Defer population until the caller's OwningAtomic assignment
            # has happened (ownership-ordering trap).
            return ctx, elem

        # Multi-element path. Members live in PhPhonData.ContextsOS; the
        # sequence references them via MembersRS (reference-only).
        phon_data = self.project.lp.PhonologicalDataOA
        if phon_data is None:
            raise FP_ParameterError(
                f"{slot_name}: project has no PhonologicalDataOA; cannot "
                f"create a multi-element context."
            )
        contexts_pool = phon_data.ContextsOS

        # Build and own each member context first.
        members = []
        for i, elem in enumerate(elements):
            member_slot = f"{slot_name}[{i}]"
            member = self.__BuildSimpleContext(elem, slot_name=member_slot)
            # Phase 2 ownership-ordering: Add to the owner pool BEFORE
            # populating so the validity-check via Owner passes.
            contexts_pool.Add(member)
            self.__PopulateSimpleContext(member, elem)
            members.append(member)

        # Create the sequence container. The sequence itself is unowned
        # until the caller assigns it to rhs.LeftContextOA / RightContextOA;
        # MembersRS is a reference list, so no ownership concerns for the
        # member references.
        seq_factory = self.project.project.ServiceLocator.GetService(
            IPhSequenceContextFactory
        )
        if seq_factory is None:
            raise FP_ParameterError(
                "IPhSequenceContextFactory service is unavailable."
            )
        seq = seq_factory.Create()
        seq_typed = IPhSequenceContext(seq)
        for member in members:
            seq_typed.MembersRS.Add(member)

        return seq, None

    def __BuildSimpleContext(self, elem, slot_name):
        """Create the appropriate IPhSimpleContext* for a pattern element.

        Returns an unattached context; caller is responsible for attaching
        it to a parent BEFORE further property writes.
        """
        if isinstance(elem, Seg):
            if isinstance(elem.phoneme, (list, tuple)):
                raise FP_ParameterError(
                    f"{slot_name}: Seg.phoneme must be a single phoneme."
                )
            factory = self.project.project.ServiceLocator.GetService(
                IPhSimpleContextSegFactory
            )
            if factory is None:
                raise FP_ParameterError(
                    "IPhSimpleContextSegFactory service is unavailable."
                )
            return factory.Create()

        if isinstance(elem, NC):
            factory = self.project.project.ServiceLocator.GetService(
                IPhSimpleContextNCFactory
            )
            if factory is None:
                raise FP_ParameterError(
                    "IPhSimpleContextNCFactory service is unavailable."
                )
            return factory.Create()

        if isinstance(elem, Boundary):
            factory = self.project.project.ServiceLocator.GetService(
                IPhSimpleContextBdryFactory
            )
            if factory is None:
                raise FP_ParameterError(
                    "IPhSimpleContextBdryFactory service is unavailable."
                )
            return factory.Create()

        raise FP_ParameterError(
            f"{slot_name}: pattern element must be Seg, NC, or Boundary, "
            f"got {type(elem).__name__}"
        )

    def __PopulateSimpleContext(self, ctx, elem):
        """Populate FeatureStructureRA + alpha constraints (Phase 2 order)."""
        if isinstance(elem, Seg):
            # Seg has no plus/minus fields by construction (TypeError at
            # call site if a caller tries to pass them). Alpha-feature
            # constraints on a single phoneme require a singleton NC --
            # see Seg's docstring.
            phoneme = self.__ResolveLcmObject(elem.phoneme)
            ctx.FeatureStructureRA = phoneme
            return

        if isinstance(elem, NC):
            nc = self.__ResolveLcmObject(elem.natural_class)
            ctx.FeatureStructureRA = nc
            # Attach alpha-variable constraints (identity = sharing).
            for c in elem.plus:
                resolved = self.__ResolveLcmObject(c)
                ctx.PlusConstrRS.Add(resolved)
            for c in elem.minus:
                resolved = self.__ResolveLcmObject(c)
                ctx.MinusConstrRS.Add(resolved)
            return

        if isinstance(elem, Boundary):
            marker = self.__ResolveBoundary(elem.marker)
            ctx.FeatureStructureRA = marker
            return

        raise FP_ParameterError(
            f"Cannot populate context from element of type {type(elem).__name__}"
        )

    def __ResolveBoundary(self, marker_name):
        """Look up an IPhBdryMarker by name from PhonemeSetsOS[0]."""
        phon_data = self.project.lp.PhonologicalDataOA
        if not phon_data:
            raise FP_ParameterError(
                "Project has no phonological data; can't resolve boundary markers"
            )
        if phon_data.PhonemeSetsOS.Count == 0:
            raise FP_ParameterError(
                "Project has no phoneme sets; can't resolve boundary markers"
            )
        bdry_markers = phon_data.PhonemeSetsOS[0].BoundaryMarkersOC
        for bm in bdry_markers:
            if (ITsString(bm.Name.BestAnalysisAlternative).Text or "") == marker_name:
                return bm
        available = [
            ITsString(bm.Name.BestAnalysisAlternative).Text or ""
            for bm in bdry_markers
        ]
        raise FP_ParameterError(
            f"Boundary marker {marker_name!r} not found in "
            f"PhonemeSetsOS[0].BoundaryMarkersOC. Available: {available}"
        )

    def __ResolveFeature(self, feature_or_hvo):
        """Resolve a feature argument (object/HVO/wrapper) to its LCM object."""
        if isinstance(feature_or_hvo, int):
            return self.project.Object(feature_or_hvo)
        if hasattr(feature_or_hvo, "_obj") and hasattr(feature_or_hvo, "_concrete"):
            return feature_or_hvo._obj
        if hasattr(feature_or_hvo, "_obj") and not hasattr(feature_or_hvo, "Hvo"):
            return feature_or_hvo._obj
        return feature_or_hvo

    def __ResolveLcmObject(self, obj_or_hvo):
        """Resolve an HVO or wrapper to its underlying LCM object.

        Identity-preserving for plain LCM objects (important for
        IPhFeatureConstraint sharing: the same constraint object must
        round-trip unchanged so alpha-variable identity holds).
        """
        if isinstance(obj_or_hvo, int):
            return self.project.Object(obj_or_hvo)
        if hasattr(obj_or_hvo, "_obj") and hasattr(obj_or_hvo, "_concrete"):
            return obj_or_hvo._obj
        if hasattr(obj_or_hvo, "_obj") and not hasattr(obj_or_hvo, "Hvo"):
            return obj_or_hvo._obj
        return obj_or_hvo

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True, deep=True):
        """
        Duplicate a phonological rule, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The IPhPhonRule object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source rule.
                                If False, insert at end of rules list.
            deep (bool): If True (default), deep copy owned objects (StrucDescOS, RightHandSidesOS).
                        If False, owned objects are not copied.

        Returns:
            IPhPhonRule: The newly created duplicate rule with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> voicing = phonRuleOps.Create("Voicing Assimilation")
            >>> # Deep copy (default - includes StrucDescOS and RightHandSidesOS)
            >>> copy = phonRuleOps.Duplicate(voicing)
            >>> print(phonRuleOps.GetName(copy))
            Voicing Assimilation

            >>> # Shallow copy (no owned objects)
            >>> rule = phonRuleOps.Create("Complex Rule")
            >>> copy = phonRuleOps.Duplicate(rule, deep=False)

        Notes:
            - Preserves the source's concrete subtype: a PhMetathesisRule
              source produces a PhMetathesisRule duplicate, etc. Dispatches
              on source.ClassName to pick the matching factory. (issue #126)
            - insert_after=True preserves the original rule's position
            - Copies all simple properties: Name, Description, Direction, StratumRA
            - Copies all owned objects when deep=True:
              - StrucDescOS (structural description / input)
              - RightHandSidesOS (output specifications)
            - Emulates FieldWorks' "Duplicate selected Phonological Rule" pattern

        See Also:
            Create, Delete, SetDirection
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source rule
        source = self.__ResolveObject(item_or_hvo)

        phon_data = self.project.lp.PhonologicalDataOA

        # Dispatch on the source's concrete subtype so a metathesis or
        # reduplication rule duplicate doesn't silently become a regular
        # rule. PhonRulesOS is polymorphic (PhRegularRule, PhMetathesisRule,
        # PhReduplicationRule); CreateAndAppendElement and the previous
        # IPhRegularRuleFactory-only fallback both produced PhRegularRule
        # regardless of source. Same fix shape as 76204e0 (#27) for
        # NaturalClassOperations.Duplicate. (issue #126)
        #
        # Resolve the factory through lcm_casting's _get_factory_for_class
        # rather than importing IPh{Metathesis,Reduplication}RuleFactory at
        # module load. Some pythonnet/LCM builds don't expose all three
        # factory interfaces at import time; lcm_casting wraps the lookup
        # in a try/except and returns None if the factory isn't bindable
        # on the current build. That lets PhonologicalRuleOperations
        # itself remain importable everywhere, and surfaces a clear
        # FP_ParameterError only when a caller actually asks to duplicate
        # a rule of an unsupported concrete type.
        from ..lcm_casting import _get_factory_for_class

        source_class = source.ClassName
        factory = _get_factory_for_class(source_class, self.project.project)
        if factory is None:
            raise FP_ParameterError(
                f"Cannot duplicate rule of class {source_class!r}: no "
                f"factory available on this LCM build. Known concrete "
                f"phonological rule types are PhRegularRule, "
                f"PhMetathesisRule, PhReduplicationRule."
            )
        with self._TransactionCM("Duplicate phonological rule"):
            duplicate = factory.Create()
            if insert_after:
                source_index = phon_data.PhonRulesOS.IndexOf(source)
                phon_data.PhonRulesOS.Insert(source_index + 1, duplicate)
            else:
                phon_data.PhonRulesOS.Add(duplicate)

            # Clone all properties (simple, reference, and owned objects)
            if deep:
                # Deep clone using the LCM cloning utilities
                from ..lcm_casting import clone_properties

                clone_properties(source, duplicate, self.project)
            else:
                # Shallow copy - only simple properties
                duplicate.Name.CopyAlternatives(source.Name)
                duplicate.Description.CopyAlternatives(source.Description)

                # Copy Reference Atomic (RA) properties
                if hasattr(source, "StratumRA") and source.StratumRA:
                    duplicate.StratumRA = source.StratumRA

                # Copy integer properties
                if hasattr(source, "Direction"):
                    duplicate.Direction = source.Direction

            return duplicate

    def __ResolveObject(self, rule_or_hvo):
        """
        Resolve HVO or object to IPhPhonRule.

        Args:
            rule_or_hvo: Either an IPhPhonRule object, a PhonologicalRule
                         wrapper, or an HVO (int).

        Returns:
            IPhPhonRule: The resolved rule object.
        """
        if isinstance(rule_or_hvo, int):
            return self.project.Object(rule_or_hvo)
        # Unwrap PhonologicalRule wrappers (from GetAll()) so collection
        # operations see the raw IPhSegmentRule. Duck-typed for any
        # LCMObjectWrapper subclass without importing the class.
        if hasattr(rule_or_hvo, "_obj") and hasattr(rule_or_hvo, "_concrete"):
            return rule_or_hvo._obj
        return rule_or_hvo

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project synchronization.

        Args:
            item: The IPhPhonRule object.

        Returns:
            dict: Dictionary mapping property names to their values.
                Keys are property names, values are the property values.

        Example:
            >>> phonRuleOps = PhonologicalRuleOperations(project)
            >>> rule = list(phonRuleOps.GetAll())[0]
            >>> props = phonRuleOps.GetSyncableProperties(rule)
            >>> print(props.keys())
            dict_keys(['Name', 'Description', 'Direction', 'StratumGuid'])

        Notes:
            - Returns all MultiString properties (all writing systems)
            - Returns Direction integer property (0=L-R, 1=R-L, 2=simultaneous)
            - Returns StratumGuid as string (GUID of referenced stratum)
            - Does not include owned objects (StrucDescOS, RightHandSidesOS)
            - Does not include GUID or HVO of the rule itself
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
                    if text:  # Only include non-empty values
                        ws_values[ws_id] = text
                if ws_values:  # Only include property if it has values
                    props[prop_name] = ws_values

        # Integer properties
        if hasattr(rule, "Direction"):
            props["Direction"] = rule.Direction

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
        Compare two phonological rules and return detailed differences.

        Args:
            item1: First rule to compare (from source project).
            item2: Second rule to compare (from target project).
            ops1: Optional PhonologicalRuleOperations instance for item1's project.
                 Defaults to self.
            ops2: Optional PhonologicalRuleOperations instance for item2's project.
                 Defaults to self.

        Returns:
            tuple: (is_different, differences) where:
                - is_different (bool): True if items differ
                - differences (dict): Maps property names to (value1, value2) tuples

        Example:
            >>> rule1 = project1_phonRuleOps.Find("Voicing Assimilation")
            >>> rule2 = project2_phonRuleOps.Find("Voicing Assimilation")
            >>> is_diff, diffs = project1_phonRuleOps.CompareTo(
            ...     rule1, rule2,
            ...     ops1=project1_phonRuleOps,
            ...     ops2=project2_phonRuleOps
            ... )
            >>> if is_diff:
            ...     for prop, (val1, val2) in diffs.items():
            ...         print(f"{prop}: {val1} -> {val2}")

        Notes:
            - Compares all MultiString properties across all writing systems
            - Compares integer and reference properties
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
