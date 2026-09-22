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
handles the concrete types of phonological rules that exist in this LCM:
- PhRegularRule: Standard rules with output specifications
- PhMetathesisRule: Metathesis rules with swapped segments

The wrapper exposes a unified interface for accessing common properties
and provides convenience methods for checking type-specific capabilities
without exposing the underlying ClassName or casting complexity.

Problem:
    Phonological rules have different properties depending on their concrete type:
    - PhRegularRule has RightHandSidesOS (output specs)
    - PhMetathesisRule has StrucDescOS plus switch-index fields
      (LeftSwitchIndex, LeftSwitchLimit, RightSwitchIndex, RightSwitchLimit)

    All have StrucDescOS (input contexts), Name, Direction, etc.

    Users working with mixed collections need to check ClassName and cast to
    access type-specific properties, which is error-prone and verbose.

Solution:
    PhonologicalRule wrapper provides:
    - Simple properties for common features (name, input_contexts)
    - Capability check properties (has_output_specs, has_metathesis_parts)
    - Property access that works across all types
    - Optional: Methods for advanced users who know C# types

Example::

    from flexicon.code.Grammar.phonological_rule import PhonologicalRule

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
        left, right = wrapped.metathesis_parts
        print(f"Swap: {left} <-> {right}")

    # Optional: Advanced users can access concrete types
    if wrapped.as_regular_rule():
        concrete = wrapped.as_regular_rule()
        # Use concrete interface for advanced operations
"""

import logging
import warnings

from ..Shared.wrapper_base import LCMObjectWrapper
from ..System.phonological_context import PhonologicalContext
from ..System.context_collection import ContextCollection

logger = logging.getLogger(__name__)


# Common deprecation message for the PhReduplicationRule public surface that
# T4 (lex-author) ruled to deprecate-then-remove at flexicon v5.0.0.
_REDUP_DEPRECATION_MSG = (
    "{name} is deprecated; PhReduplicationRule is not supported by this LCM "
    "and will be removed in flexicon v5.0.0."
)


class PhonologicalRule(LCMObjectWrapper):
    """
    Wrapper for phonological rule objects providing unified interface access.

    Handles the concrete types of phonological rules that exist in this LCM
    (PhRegularRule, PhMetathesisRule) transparently, providing common
    properties and capability checks without exposing ClassName or casting.

    Attributes:
        _obj: The base interface object (IPhSegmentRule)
        _concrete: The concrete type object (IPhRegularRule or IPhMetathesisRule)

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
            - Works on all rule types (regular, metathesis)
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
            - PhMetathesisRule uses StrucDescOS plus switch indices
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
            return list(self._concrete.RightHandSidesOS)
        except Exception:
            return []

    def _is_valid_index_range(self, start, end, count):
        """Return True when 0 <= start < end <= count and both are set."""
        try:
            if start is None or end is None:
                return False
            start = int(start)
            end = int(end)
            if start < 0 or end < 0:
                return False
            return 0 <= start < end <= count
        except Exception:
            return False

    def _get_int_field(self, obj, name, default=-1):
        """Safely read an integer field from an LCM object."""
        try:
            val = getattr(obj, name, default)
            if val is None:
                return default
            return int(val)
        except Exception:
            return default

    def _metathesis_ranges(self):
        """
        Return validated (left_start, left_end, right_start, right_end) slices
        for a PhMetathesisRule, or None when the rule is not a metathesis rule
        or the switch ranges are unset/invalid.
        """
        try:
            if self.class_type != "PhMetathesisRule":
                return None

            sd = self._concrete.StrucDescOS
            count = getattr(sd, "Count", None)
            if count is None:
                count = len(list(sd))
            if count == 0:
                return None

            left_start = self._get_int_field(self._concrete, "LeftSwitchIndex")
            left_end = self._get_int_field(self._concrete, "LeftSwitchLimit")
            right_start = self._get_int_field(self._concrete, "RightSwitchIndex")
            right_end = self._get_int_field(self._concrete, "RightSwitchLimit")

            if not self._is_valid_index_range(left_start, left_end, count):
                return None
            if not self._is_valid_index_range(right_start, right_end, count):
                return None

            return left_start, left_end, right_start, right_end
        except Exception:
            logger.debug("_metathesis_ranges: failed to read switch indices", exc_info=True)
            return None

    @property
    def has_metathesis_parts(self):
        """
        Check if this rule has non-empty metathesis parts.

        Returns:
            bool: True if this is a PhMetathesisRule whose StrucDescOS can be
                sliced into left and right switch ranges.

        Example::

            if wrapped.has_metathesis_parts:
                left, right = wrapped.metathesis_parts
                print(f"Swap: {left} <-> {right}")

        Notes:
            - Only PhMetathesisRule objects have this capability
            - Empty or index-unset rules report False gracefully
            - Use metathesis_parts to get the actual parts
        """
        return self._metathesis_ranges() is not None

    @property
    def metathesis_parts(self):
        """
        Get the metathesis parts (left and right swapped segments).

        Returns:
            tuple: (left_collection, right_collection) where each is a
                ContextCollection of PhonologicalContext wrappers, or two empty
                collections if this is not a metathesis rule with valid ranges.

        Example::

            if wrapped.has_metathesis_parts:
                left, right = wrapped.metathesis_parts
                for part in left:
                    print(f"Left swapped part: {part.context_name}")

        Notes:
            - Only PhMetathesisRule has these parts
            - Parts are derived from StrucDescOS using the switch-index fields
              LeftSwitchIndex/LeftSwitchLimit and RightSwitchIndex/RightSwitchLimit
            - Use has_metathesis_parts to check before accessing
        """
        ranges = self._metathesis_ranges()
        if ranges is None:
            return ContextCollection(), ContextCollection()

        left_start, left_end, right_start, right_end = ranges
        try:
            contexts = list(self._concrete.StrucDescOS)
            left = [PhonologicalContext(ctx) for ctx in contexts[left_start:left_end]]
            right = [PhonologicalContext(ctx) for ctx in contexts[right_start:right_end]]
            return ContextCollection(left), ContextCollection(right)
        except Exception:
            logger.debug("metathesis_parts: failed to slice StrucDescOS", exc_info=True)
            return ContextCollection(), ContextCollection()

    @property
    def has_redup_parts(self):
        """
        Deprecated. Always returns False.

        PhReduplicationRule is not supported by this LCM and this property will
        be removed in flexicon v5.0.0.

        Returns:
            bool: False
        """
        warnings.warn(
            _REDUP_DEPRECATION_MSG.format(name="PhonologicalRule.has_redup_parts"),
            DeprecationWarning,
            stacklevel=2,
        )
        return False

    @property
    def redup_parts(self):
        """
        Deprecated. Always returns two empty collections.

        PhReduplicationRule is not supported by this LCM and this property will
        be removed in flexicon v5.0.0.

        Returns:
            tuple: (ContextCollection(), ContextCollection())
        """
        warnings.warn(
            _REDUP_DEPRECATION_MSG.format(name="PhonologicalRule.redup_parts"),
            DeprecationWarning,
            stacklevel=2,
        )
        return ContextCollection(), ContextCollection()

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
        Deprecated. Always returns None.

        PhReduplicationRule is not supported by this LCM and this method will
        be removed in flexicon v5.0.0.

        Returns:
            None
        """
        warnings.warn(
            _REDUP_DEPRECATION_MSG.format(name="PhonologicalRule.as_reduplication_rule()"),
            DeprecationWarning,
            stacklevel=2,
        )
        return None

    @property
    def concrete(self):
        """
        Get the raw concrete interface object.

        For advanced users who need to access the underlying C# interface
        directly without going through wrapper properties.

        Returns:
            The concrete interface object (IPhRegularRule or IPhMetathesisRule
            depending on the rule's actual type).

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
