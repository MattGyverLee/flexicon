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
from ..System.rule_feature import RuleFeature, RuleFeatureCollection

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

    # ========== Environment, rule-feature, POS and disabled readers (C1-C6, C8) ==========

    def _rhs_at(self, rhs_index):
        """
        Return the RHS owning sequence element at rhs_index.

        Returns None when the rule has no environments (a metathesis rule,
        or a regular rule with no RHS). Raises IndexError for an
        out-of-range index on a rule that has RHSs, so "no environment
        here" (None) is never conflated with "bad index".

        Args:
            rhs_index: Zero-based index into RightHandSidesOS.

        Returns:
            The IPhSegRuleRHS at rhs_index, or None.

        Raises:
            IndexError: If the rule has RHSs and rhs_index is out of range.
        """
        if not self.has_environments:
            return None
        try:
            rhs_list = list(self._concrete.RightHandSidesOS)
        except Exception:
            return None
        if rhs_index < 0 or rhs_index >= len(rhs_list):
            raise IndexError(
                f"rhs_index {rhs_index!r} out of range: "
                f"rule has {len(rhs_list)} right-hand side(s)"
            )
        return rhs_list[rhs_index]

    @property
    def has_environments(self) -> bool:
        """
        Check if this rule carries per-RHS environments.

        Returns:
            bool: True only for a concrete IPhRegularRule with at least
                one RHS. A metathesis rule has no RightHandSidesOS and
                therefore no environment at all.

        Example::

            if wrapped.has_environments:
                print(wrapped.left_context(0).context_name)

        Notes:
            - The capability check replaces a ClassName test (API design
              rule 4); callers ask this before asking for a context.
            - Every read goes through self._concrete (C10): a raw
              PhonRulesOS element reads RightHandSidesOS as absent until
              cast, while the wrapper reports it.
        """
        try:
            if self.class_type != "PhRegularRule":
                return False
            rhs = getattr(self._concrete, "RightHandSidesOS", None)
            if rhs is None:
                return False
            return rhs.Count > 0
        except Exception:
            return False

    def left_context(self, rhs_index=0):
        """
        Get the left environment of one right-hand side.

        Args:
            rhs_index: Zero-based index into RightHandSidesOS. Defaults
                to 0 because WireRule only ever writes index 0 and a
                single-RHS rule is the overwhelming norm.

        Returns:
            Optional[PhonologicalContext]: The LeftContextOA wrapped, or
                None when the slot is unset or the rule is a metathesis
                rule (which has no environment; see has_environments).

        Raises:
            IndexError: If rhs_index is out of range on a rule that has
                RHSs.

        Example::

            ctx = wrapped.left_context()
            if ctx is not None:
                print(ctx.context_name)

        Notes:
            - A metathesis rule yields None silently: no warnings.warn is
              emitted, since a caller iterating GetAll() would get one
              per metathesis rule per call (C2, Q2 ruling).
            - Returns a wrapper, not a raw IPhPhonContext: the raw
              interface declares no content members, so handing one out
              would defeat the wrapper (C1).
        """
        rhs = self._rhs_at(rhs_index)
        if rhs is None:
            return None
        try:
            ctx = getattr(rhs, "LeftContextOA", None)
        except Exception:
            return None
        if ctx is None:
            return None
        return PhonologicalContext(ctx)

    def right_context(self, rhs_index=0):
        """
        Get the right environment of one right-hand side.

        Args:
            rhs_index: Zero-based index into RightHandSidesOS. Defaults
                to 0 because WireRule only ever writes index 0 and a
                single-RHS rule is the overwhelming norm.

        Returns:
            Optional[PhonologicalContext]: The RightContextOA wrapped, or
                None when the slot is unset or the rule is a metathesis
                rule (which has no environment; see has_environments).

        Raises:
            IndexError: If rhs_index is out of range on a rule that has
                RHSs.

        Example::

            ctx = wrapped.right_context()
            if ctx is not None:
                print(ctx.context_name)

        Notes:
            - A metathesis rule yields None silently: no warnings.warn is
              emitted, since a caller iterating GetAll() would get one
              per metathesis rule per call (C2, Q2 ruling).
            - Returns a wrapper, not a raw IPhPhonContext: the raw
              interface declares no content members, so handing one out
              would defeat the wrapper (C1).
        """
        rhs = self._rhs_at(rhs_index)
        if rhs is None:
            return None
        try:
            ctx = getattr(rhs, "RightContextOA", None)
        except Exception:
            return None
        if ctx is None:
            return None
        return PhonologicalContext(ctx)

    def input_poses(self, rhs_index=0):
        """
        Get the parts of speech one right-hand side is limited to.

        Args:
            rhs_index: Zero-based index into RightHandSidesOS. Defaults
                to 0.

        Returns:
            list: The IPartOfSpeech objects from InputPOSesRC, uncast
                (the LCM collection is already typed, so a cast would
                only cost the caller the object). Empty when unset or
                when the rule has no environments.

        Raises:
            IndexError: If rhs_index is out of range on a rule that has
                RHSs.

        Example::

            for pos in wrapped.input_poses():
                print(best_analysis_text(pos.Name))
        """
        rhs = self._rhs_at(rhs_index)
        if rhs is None:
            return []
        try:
            poses = getattr(rhs, "InputPOSesRC", None)
            if poses is None:
                return []
            return list(poses)
        except Exception:
            logger.debug("input_poses: failed to read InputPOSesRC", exc_info=True)
            return []

    def required_rule_features(self, rhs_index=0):
        """
        Get the rule features one right-hand side requires.

        Args:
            rhs_index: Zero-based index into RightHandSidesOS. Defaults
                to 0.

        Returns:
            RuleFeatureCollection: The ReqRuleFeatsRC features wrapped.
                Always a collection, empty never None, because "the rule
                requires nothing" and "unreadable" are different and only
                the first is true.

        Raises:
            IndexError: If rhs_index is out of range on a rule that has
                RHSs.

        Example::

            print(wrapped.required_rule_features().names)
        """
        rhs = self._rhs_at(rhs_index)
        if rhs is None:
            return RuleFeatureCollection()
        try:
            feats = getattr(rhs, "ReqRuleFeatsRC", None)
            if feats is None:
                return RuleFeatureCollection()
            return RuleFeatureCollection([RuleFeature(f) for f in feats])
        except Exception:
            logger.debug("required_rule_features: failed to read ReqRuleFeatsRC", exc_info=True)
            return RuleFeatureCollection()

    def excluded_rule_features(self, rhs_index=0):
        """
        Get the rule features one right-hand side excludes.

        Args:
            rhs_index: Zero-based index into RightHandSidesOS. Defaults
                to 0.

        Returns:
            RuleFeatureCollection: The ExclRuleFeatsRC features wrapped.
                Always a collection, empty never None.

        Raises:
            IndexError: If rhs_index is out of range on a rule that has
                RHSs.

        Example::

            print(wrapped.excluded_rule_features().names)
        """
        rhs = self._rhs_at(rhs_index)
        if rhs is None:
            return RuleFeatureCollection()
        try:
            feats = getattr(rhs, "ExclRuleFeatsRC", None)
            if feats is None:
                return RuleFeatureCollection()
            return RuleFeatureCollection([RuleFeature(f) for f in feats])
        except Exception:
            logger.debug("excluded_rule_features: failed to read ExclRuleFeatsRC", exc_info=True)
            return RuleFeatureCollection()

    @property
    def is_disabled(self) -> bool:
        """
        Check if this rule is disabled.

        Returns:
            bool: The Disabled flag. Declared on the base IPhSegmentRule,
                so every rule this wrapper handles has it and no guard is
                needed (R-8).

        Example::

            state = "disabled" if wrapped.is_disabled else "active"
        """
        return bool(self._concrete.Disabled)

    def set_disabled(self, disabled) -> None:
        """
        Set the disabled state of this rule.

        This is the primitive: it performs the assignment itself, with no
        project write check and no transaction. Callers going through
        PhonologicalRuleOperations.SetDisabled get both (the check first,
        inside the class's transaction bracket).

        Args:
            disabled: True to disable the rule, False to enable it.

        Raises:
            FP_NullParameterError: If disabled is None.

        Example::

            wrapped.set_disabled(True)
        """
        from ..FLExProject import FP_NullParameterError

        if disabled is None:
            raise FP_NullParameterError()
        self._concrete.Disabled = bool(disabled)

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
