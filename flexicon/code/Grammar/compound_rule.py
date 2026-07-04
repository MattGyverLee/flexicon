#
#   compound_rule.py
#
#   Class: CompoundRule
#          Wrapper for compound rule objects providing unified interface
#          access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Wrapper class for compound rule objects with unified interface.

This module provides CompoundRule, a wrapper class that transparently
handles the two concrete types of compound rules:
- MoEndoCompound: Head is internal to the compound
- MoExoCompound: Head is external to the compound

The wrapper exposes a unified interface for accessing common properties
and provides convenience methods for checking type-specific capabilities
without exposing the underlying ClassName or casting complexity.

Problem:
    Compound rules have different properties depending on their concrete type:
    - MoEndoCompound and MoExoCompound both have LeftHeadDep, RightHeadDep,
      LeftContextOA, RightContextOA

    Users working with mixed collections need to check ClassName and cast to
    access type-specific properties, which is error-prone and verbose.

Solution:
    CompoundRule wrapper provides:
    - Simple properties for common features (name, head_dependency, contexts)
    - Capability check properties (is_endo_compound, is_exo_compound)
    - Property access that works across all types
    - Optional: Methods for advanced users who know C# types

Example::

    from flexlibs2.code.Grammar.compound_rule import CompoundRule

    # Wrap a rule from GetAll()
    rule = morphRuleOps.GetAll()[0]  # Typed as IMoCompoundRule
    wrapped = CompoundRule(rule)

    # Access common properties
    print(wrapped.name)  # Works for all rule types
    if wrapped.left_head_dep:
        print(f"Left head dependency: {wrapped.left_head_dep}")

    # Check type
    if wrapped.is_endo_compound:
        print("Head is internal to the compound")

    # Optional: Advanced users can access concrete types
    if wrapped.as_endo_compound():
        concrete = wrapped.as_endo_compound()
        # Use concrete interface for advanced operations
"""

from ..Shared.wrapper_base import LCMObjectWrapper
from ..lcm_casting import cast_to_concrete


class CompoundRule(LCMObjectWrapper):
    """
    Wrapper for compound rule objects providing unified interface access.

    Handles the two concrete types of compound rules (MoEndoCompound,
    MoExoCompound) transparently, providing common properties and
    capability checks without exposing ClassName or casting.

    Attributes:
        _obj: The base interface object (IMoCompoundRule)
        _concrete: The concrete type object (IMoEndoCompound or IMoExoCompound)

    Example::

        rule = morphRuleOps.GetAll()[0]
        wrapped = CompoundRule(rule)
        print(wrapped.name)
        print(wrapped.is_endo_compound)
        if wrapped.left_head_dep:
            print(wrapped.left_head_dep)
    """

    def __init__(self, lcm_rule):
        """
        Initialize CompoundRule wrapper with a rule object.

        Args:
            lcm_rule: An IMoCompoundRule object (or derived type).
                     Typically from MorphRuleOperations.GetAll().

        Example::

            rule = morphRuleOps.GetAll()[0]
            wrapped = CompoundRule(rule)
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
    def left_head_dep(self):
        """
        Get the left head dependency.

        Returns:
            int or None: The left head dependency value, or None if not set.

        Example::

            if wrapped.left_head_dep:
                print(f"Left head dep: {wrapped.left_head_dep}")

        Notes:
            - Available on both MoEndoCompound and MoExoCompound
            - Use head_dependency for generic access
        """
        try:
            if hasattr(self._concrete, "LeftHeadDep"):
                return self._concrete.LeftHeadDep
            return None
        except Exception:
            return None

    @property
    def right_head_dep(self):
        """
        Get the right head dependency.

        Returns:
            int or None: The right head dependency value, or None if not set.

        Example::

            if wrapped.right_head_dep:
                print(f"Right head dep: {wrapped.right_head_dep}")

        Notes:
            - Available on both MoEndoCompound and MoExoCompound
            - Use head_dependency for generic access
        """
        try:
            if hasattr(self._concrete, "RightHeadDep"):
                return self._concrete.RightHeadDep
            return None
        except Exception:
            return None

    @property
    def head_dependency(self):
        """
        Get the primary head dependency (convenience property).

        Returns the first non-None head dependency (left takes precedence).

        Returns:
            int or None: The head dependency value, or None if neither set.

        Example::

            if wrapped.head_dependency:
                print(f"Head dependency: {wrapped.head_dependency}")

        Notes:
            - Tries left_head_dep first, then right_head_dep
            - Use left_head_dep or right_head_dep for specific access
        """
        left = self.left_head_dep
        if left is not None:
            return left
        return self.right_head_dep

    @property
    def left_context(self):
        """
        Get the left context.

        Returns:
            IMoPhonContext or None: The left context object, or None if not set.

        Example::

            if wrapped.left_context:
                print(f"Left context: {wrapped.left_context}")

        Notes:
            - Available on both MoEndoCompound and MoExoCompound
            - Use contexts property for generic access
        """
        try:
            if hasattr(self._concrete, "LeftContextOA"):
                return self._concrete.LeftContextOA
            return None
        except Exception:
            return None

    @property
    def right_context(self):
        """
        Get the right context.

        Returns:
            IMoPhonContext or None: The right context object, or None if not set.

        Example::

            if wrapped.right_context:
                print(f"Right context: {wrapped.right_context}")

        Notes:
            - Available on both MoEndoCompound and MoExoCompound
            - Use contexts property for generic access
        """
        try:
            if hasattr(self._concrete, "RightContextOA"):
                return self._concrete.RightContextOA
            return None
        except Exception:
            return None

    @property
    def contexts(self):
        """
        Get both left and right contexts as a tuple.

        Returns:
            tuple: (left_context, right_context) where each can be None.

        Example::

            left_ctx, right_ctx = wrapped.contexts
            if left_ctx:
                print(f"Left: {left_ctx}")
            if right_ctx:
                print(f"Right: {right_ctx}")

        Notes:
            - Convenience property for accessing both contexts
            - Use left_context or right_context for individual access
        """
        return (self.left_context, self.right_context)

    # ========== Capability Checks (for type-specific properties) ==========

    @property
    def is_endo_compound(self):
        """
        Check if this is an endocentric compound rule.

        Returns:
            bool: True if this is MoEndoCompound (head is internal).

        Example::

            if wrapped.is_endo_compound:
                print("Head is internal to the compound")

        Notes:
            - MoEndoCompound has the head inside the compound structure
            - Mutually exclusive with is_exo_compound
        """
        try:
            return self.class_type == "MoEndoCompound"
        except Exception:
            return False

    @property
    def is_exo_compound(self):
        """
        Check if this is an exocentric compound rule.

        Returns:
            bool: True if this is MoExoCompound (head is external).

        Example::

            if wrapped.is_exo_compound:
                print("Head is external to the compound")

        Notes:
            - MoExoCompound has the head outside the compound structure
            - Mutually exclusive with is_endo_compound
        """
        try:
            return self.class_type == "MoExoCompound"
        except Exception:
            return False

    # ========== Advanced: Direct C# class access (optional for power users) ==========

    def as_endo_compound(self):
        """
        Cast to IMoEndoCompound if this is an endo compound rule.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not an MoEndoCompound.

        Returns:
            IMoEndoCompound or None: The concrete interface if this is an
                MoEndoCompound, None otherwise.

        Example::

            if rule_obj.as_endo_compound():
                concrete = rule_obj.as_endo_compound()
                # Can now access IMoEndoCompound-specific methods/properties
                # Advanced operations...

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like is_endo_compound instead
            - Only useful if you need to call methods or access properties
              that aren't exposed through the wrapper
        """
        if self.class_type == "MoEndoCompound":
            return self._concrete
        return None

    def as_exo_compound(self):
        """
        Cast to IMoExoCompound if this is an exo compound rule.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not an MoExoCompound.

        Returns:
            IMoExoCompound or None: The concrete interface if this is an
                MoExoCompound, None otherwise.

        Example::

            if rule_obj.as_exo_compound():
                concrete = rule_obj.as_exo_compound()
                # Can now access IMoExoCompound-specific methods/properties

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like is_exo_compound instead
        """
        if self.class_type == "MoExoCompound":
            return self._concrete
        return None

    @property
    def concrete(self):
        """
        Get the raw concrete interface object.

        For advanced users who need to access the underlying C# interface
        directly without going through wrapper properties.

        Returns:
            The concrete interface object (IMoEndoCompound or IMoExoCompound
            depending on the rule's actual type).

        Example::

            # Direct access to concrete interface
            concrete = rule_obj.concrete
            left_dep = concrete.LeftHeadDep

        Notes:
            - For power users only
            - Bypasses the wrapper's abstraction
            - Normal users should prefer wrapper properties like
              is_endo_compound, left_head_dep, etc.
        """
        return self._concrete

    def __repr__(self):
        """String representation showing rule name and type."""
        return f"CompoundRule({self.name or 'Unnamed'}, {self.class_type})"

    def __str__(self):
        """Human-readable description."""
        if self.name:
            return f"Rule '{self.name}' ({self.class_type})"
        return f"Unnamed {self.class_type}"
