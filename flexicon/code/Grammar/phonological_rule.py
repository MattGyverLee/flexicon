#
#   phonological_rule.py
#
#   Class: PhonologicalRule
#          Wrapper for phonological rule objects providing unified interface
#          access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Wrapper class for phonological rule objects with unified interface.

This module provides PhonologicalRule, a wrapper class that transparently
handles the three concrete types of phonological rules:
- PhRegularRule: Standard rules with output specifications
- PhMetathesisRule: Metathesis rules with swapped segments
- PhReduplicationRule: Reduplication rules with repeated segments

The wrapper exposes a unified interface for accessing common properties
and provides convenience methods for checking type-specific capabilities
without exposing the underlying ClassName or casting complexity.

Problem:
    Phonological rules have different properties depending on their concrete type:
    - PhRegularRule has RightHandSidesOS (output specs)
    - PhMetathesisRule has LeftPartOfMetathesisOS, RightPartOfMetathesisOS
    - PhReduplicationRule has LeftPartOfReduplicationOS, RightPartOfReduplicationOS

    All have StrucDescOS (input contexts), Name, Direction, etc.

    Users working with mixed collections need to check ClassName and cast to
    access type-specific properties, which is error-prone and verbose.

Solution:
    PhonologicalRule wrapper provides:
    - Simple properties for common features (name, input_contexts)
    - Capability check properties (has_output_specs, has_metathesis_parts, etc.)
    - Property access that works across all types
    - Optional: Methods for advanced users who know C# types

Example::

    from flexlibs2.code.Grammar.phonological_rule import PhonologicalRule

    # Wrap a rule from GetAll()
    rule = phonRuleOps.GetAll()[0]  # Typed as IPhSegmentRule
    wrapped = PhonologicalRule(rule)

    # Access common properties
    print(wrapped.name)  # Works for all rule types
    for context in wrapped.input_contexts:
        print(context)

    # Check capabilities
    if wrapped.has_output_specs:
        for spec in wrapped.output_specs:
            print(f"Output: {spec}")

    if wrapped.has_metathesis_parts:
        print("This is a metathesis rule")

    # Optional: Advanced users can access concrete types
    if wrapped.as_regular_rule():
        concrete = wrapped.as_regular_rule()
        # Use concrete interface for advanced operations
"""

from ..Shared.wrapper_base import LCMObjectWrapper
from ..lcm_casting import cast_to_concrete
from ..System.phonological_context import PhonologicalContext
from ..System.context_collection import ContextCollection


class PhonologicalRule(LCMObjectWrapper):
    """
    Wrapper for phonological rule objects providing unified interface access.

    Handles the three concrete types of phonological rules (PhRegularRule,
    PhMetathesisRule, PhReduplicationRule) transparently, providing common
    properties and capability checks without exposing ClassName or casting.

    Attributes:
        _obj: The base interface object (IPhSegmentRule)
        _concrete: The concrete type object (IPhRegularRule, IPhMetathesisRule,
                  or IPhReduplicationRule)

    Example::

        rule = phonRuleOps.GetAll()[0]
        wrapped = PhonologicalRule(rule)
        print(wrapped.name)
        print(wrapped.input_contexts)
        if wrapped.has_output_specs:
            print(wrapped.output_specs)
    """

    def __init__(self, lcm_rule):
        """
        Initialize PhonologicalRule wrapper with a rule object.

        Args:
            lcm_rule: An IPhSegmentRule object (or derived type).
                     Typically from PhonologicalRuleOperations.GetAll().

        Example::

            rule = phonRuleOps.GetAll()[0]
            wrapped = PhonologicalRule(rule)
        """
        super().__init__(lcm_rule)

    # ========== Common Properties (work across all rule types) ==========

    @property
    def name(self) -> str:
        """
        Get the rule's name.

        Returns:
            str: The rule name, or empty string if not set.

        Example::

            print(f"Rule: {wrapped.name}")
        """
        from SIL.LCModel.Core.KernelInterfaces import ITsString

        name_multistring = self._obj.Name
        if not name_multistring:
            return ""
        default_ws = self._obj.Cache.DefaultAnalWs
        name_text = ITsString(name_multistring.get_String(default_ws)).Text
        return name_text or ""

    @property
    def direction(self) -> int:
        """
        Get the direction of rule application.

        Returns:
            int: Direction value (0=left-to-right, 1=right-to-left,
                2=simultaneous).

        Example::

            if wrapped.direction == 0:
                print("Left-to-right application")
        """
        try:
            if hasattr(self._concrete, "Direction"):
                return self._concrete.Direction
            return 0  # Default: left-to-right
        except Exception:
            return 0

    @property
    def stratum(self) -> "Optional[object]":
        """
        Get the stratum this rule applies in.

        Returns:
            IMoStratum or None: The stratum object if set, None otherwise.

        Example::

            if wrapped.stratum:
                print(f"Stratum: {wrapped.stratum.Name.BestAnalysisAlternative.Text}")
        """
        try:
            if hasattr(self._concrete, "StratumRA"):
                return self._concrete.StratumRA
            return None
        except Exception:
            return None

    @property
    def input_contexts(self) -> "ContextCollection":
        """
        Get the input contexts (structural description) for this rule.

        Returns:
            ContextCollection: Smart collection of PhonologicalContext wrapper objects
                representing the structural description (input) of this rule.
                Returns empty collection if none.

        Example::

            for context in wrapped.input_contexts:
                print(f"Input context: {context.context_name}")
                if context.is_simple_context_seg:
                    segment = context.segment
                    print(f"Segment: {segment}")

            # Filter contexts
            simple_contexts = wrapped.input_contexts.simple_contexts()
            boundaries = wrapped.input_contexts.boundary_contexts()

        Notes:
            - StrucDescOS contains the input specifications
            - Works on all rule types (regular, metathesis, reduplication)
            - Returns ContextCollection for convenient filtering and type checking
            - Contexts are wrapped in PhonologicalContext for unified interface
        """
        try:
            if hasattr(self._concrete, "StrucDescOS"):
                contexts = list(self._concrete.StrucDescOS)
                # Wrap each context in PhonologicalContext
                wrapped_contexts = [PhonologicalContext(ctx) for ctx in contexts]
                return ContextCollection(wrapped_contexts)
            return ContextCollection()
        except Exception:
            return ContextCollection()

    # ========== Capability Checks (for type-specific properties) ==========

    @property
    def has_output_specs(self):
        """
        Check if this rule has output specifications.

        Returns:
            bool: True if this is a PhRegularRule with RightHandSidesOS.

        Example::

            if wrapped.has_output_specs:
                for spec in wrapped.output_specs:
                    print(f"Output: {spec}")

        Notes:
            - Only PhRegularRule has output specifications
            - PhMetathesisRule and PhReduplicationRule have their own
              output representations
        """
        try:
            return self.class_type == "PhRegularRule" and hasattr(self._concrete, "RightHandSidesOS")
        except Exception:
            return False

    @property
    def output_specs(self):
        """
        Get the output specifications for this rule.

        Only available on PhRegularRule. Returns empty list for other types.

        Returns:
            list: List of IPhSegRuleRHS objects, or empty list if not available.

        Example::

            if wrapped.has_output_specs:
                for rhs in wrapped.output_specs:
                    print(f"Output spec: {rhs}")

        Notes:
            - Only PhRegularRule has RightHandSidesOS
            - Use has_output_specs to check before accessing
        """
        if not self.has_output_specs:
            return []

        try:
            if hasattr(self._concrete, "RightHandSidesOS"):
                return list(self._concrete.RightHandSidesOS)
            return []
        except Exception:
            return []

    @property
    def has_metathesis_parts(self):
        """
        Check if this rule is a metathesis rule.

        Returns:
            bool: True if this is a PhMetathesisRule with metathesis parts.

        Example::

            if wrapped.has_metathesis_parts:
                left, right = wrapped.metathesis_parts
                print(f"Swap: {left} <-> {right}")

        Notes:
            - Only PhMetathesisRule objects have this capability
            - Use metathesis_parts to get the actual parts
        """
        try:
            return (
                self.class_type == "PhMetathesisRule"
                and hasattr(self._concrete, "LeftPartOfMetathesisOS")
                and hasattr(self._concrete, "RightPartOfMetathesisOS")
            )
        except Exception:
            return False

    @property
    def metathesis_parts(self):
        """
        Get the metathesis parts (left and right swapped segments).

        Returns:
            tuple: (left_parts, right_parts) where each is a list of contexts,
                   or ([], []) if not a metathesis rule.

        Example::

            if wrapped.has_metathesis_parts:
                left, right = wrapped.metathesis_parts
                for part in left:
                    print(f"Left swapped part: {part}")

        Notes:
            - Only PhMetathesisRule has these parts
            - Use has_metathesis_parts to check before accessing
        """
        if not self.has_metathesis_parts:
            return [], []

        try:
            left = (
                list(self._concrete.LeftPartOfMetathesisOS) if hasattr(self._concrete, "LeftPartOfMetathesisOS") else []
            )
            right = (
                list(self._concrete.RightPartOfMetathesisOS)
                if hasattr(self._concrete, "RightPartOfMetathesisOS")
                else []
            )
            return left, right
        except Exception:
            return [], []

    @property
    def has_redup_parts(self):
        """
        Check if this rule is a reduplication rule.

        Returns:
            bool: True if this is a PhReduplicationRule with reduplication parts.

        Example::

            if wrapped.has_redup_parts:
                left, right = wrapped.redup_parts
                print(f"Reduplication: {left} <-> {right}")

        Notes:
            - Only PhReduplicationRule objects have this capability
            - Use redup_parts to get the actual parts
        """
        try:
            return (
                self.class_type == "PhReduplicationRule"
                and hasattr(self._concrete, "LeftPartOfReduplicationOS")
                and hasattr(self._concrete, "RightPartOfReduplicationOS")
            )
        except Exception:
            return False

    @property
    def redup_parts(self):
        """
        Get the reduplication parts (left and right repeated segments).

        Returns:
            tuple: (left_parts, right_parts) where each is a list of contexts,
                   or ([], []) if not a reduplication rule.

        Example::

            if wrapped.has_redup_parts:
                left, right = wrapped.redup_parts
                for part in left:
                    print(f"Left reduplicated part: {part}")

        Notes:
            - Only PhReduplicationRule has these parts
            - Use has_redup_parts to check before accessing
        """
        if not self.has_redup_parts:
            return [], []

        try:
            left = (
                list(self._concrete.LeftPartOfReduplicationOS)
                if hasattr(self._concrete, "LeftPartOfReduplicationOS")
                else []
            )
            right = (
                list(self._concrete.RightPartOfReduplicationOS)
                if hasattr(self._concrete, "RightPartOfReduplicationOS")
                else []
            )
            return left, right
        except Exception:
            return [], []

    # ========== Advanced: Direct C# class access (optional for power users) ==========

    def as_regular_rule(self):
        """
        Cast to IPhRegularRule if this is a regular rule.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a PhRegularRule.

        Returns:
            IPhRegularRule or None: The concrete interface if this is a
                PhRegularRule, None otherwise.

        Example::

            if rule_obj.as_regular_rule():
                concrete = rule_obj.as_regular_rule()
                # Can now access IPhRegularRule-specific methods/properties
                rhs = concrete.RightHandSidesOS
                # Advanced operations...

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like has_output_specs and
              output_specs instead
            - Only useful if you need to call methods or access properties
              that aren't exposed through the wrapper
        """
        if self.class_type == "PhRegularRule":
            return self._concrete
        return None

    def as_metathesis_rule(self):
        """
        Cast to IPhMetathesisRule if this is a metathesis rule.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a PhMetathesisRule.

        Returns:
            IPhMetathesisRule or None: The concrete interface if this is a
                PhMetathesisRule, None otherwise.

        Example::

            if rule_obj.as_metathesis_rule():
                concrete = rule_obj.as_metathesis_rule()
                # Can now access IPhMetathesisRule-specific methods/properties

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like has_metathesis_parts and
              metathesis_parts instead
        """
        if self.class_type == "PhMetathesisRule":
            return self._concrete
        return None

    def as_reduplication_rule(self):
        """
        Cast to IPhReduplicationRule if this is a reduplication rule.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a PhReduplicationRule.

        Returns:
            IPhReduplicationRule or None: The concrete interface if this is a
                PhReduplicationRule, None otherwise.

        Example::

            if rule_obj.as_reduplication_rule():
                concrete = rule_obj.as_reduplication_rule()
                # Can now access IPhReduplicationRule-specific methods/properties

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like has_redup_parts and
              redup_parts instead
        """
        if self.class_type == "PhReduplicationRule":
            return self._concrete
        return None

    @property
    def concrete(self):
        """
        Get the raw concrete interface object.

        For advanced users who need to access the underlying C# interface
        directly without going through wrapper properties.

        Returns:
            The concrete interface object (IPhRegularRule, IPhMetathesisRule,
            or IPhReduplicationRule depending on the rule's actual type).

        Example::

            # Direct access to concrete interface
            concrete = rule_obj.concrete
            rhs = concrete.RightHandSidesOS  # PhRegularRule property

        Notes:
            - For power users only
            - Bypasses the wrapper's abstraction
            - Normal users should prefer wrapper properties like
              has_output_specs, output_specs, etc.
        """
        return self._concrete

    def __repr__(self):
        """String representation showing rule name and type."""
        return f"PhonologicalRule({self.name or 'Unnamed'}, {self.class_type})"

    def __str__(self):
        """Human-readable description."""
        if self.name:
            return f"Rule '{self.name}' ({self.class_type})"
        return f"Unnamed {self.class_type}"
