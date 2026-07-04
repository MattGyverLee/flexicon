#
#   phonological_context.py
#
#   Class: PhonologicalContext
#          Wrapper for phonological context objects providing unified interface
#          access across multiple concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Wrapper class for phonological context objects with unified interface.

This module provides PhonologicalContext, a wrapper class that transparently
handles the multiple concrete types of phonological contexts:
- PhSimpleContextSeg: Simple context with single segment
- PhSimpleContextNC: Simple context with natural class
- PhComplexContextSeg: Complex context with segments
- PhComplexContextNC: Complex context with natural class
- PhBoundaryContext: Boundary context

All share a base interface IPhPhonContext or similar.

Problem:
    Phonological contexts have different properties depending on their concrete type:
    - PhSimpleContextSeg: Represents a single segment
    - PhSimpleContextNC: Represents a natural class
    - PhComplexContextSeg: Complex segment specifications
    - PhComplexContextNC: Complex natural class specifications
    - PhBoundaryContext: Word/morpheme boundaries

    All have Name, Description, and other common properties.

    Users working with mixed collections need to check ClassName and cast to
    access type-specific properties, which is error-prone and verbose.

Solution:
    PhonologicalContext wrapper provides:
    - Simple properties for common features (context_name, description)
    - Capability check properties (is_simple_context_seg, is_boundary, etc.)
    - Property access that works across all types
    - Optional: Methods for advanced users who know C# types

Example::

    from flexlibs2.code.System.phonological_context import PhonologicalContext

    # Wrap a context from a rule's input contexts
    context = rule.input_contexts[0]  # Typed as IPhPhonContext
    wrapped = PhonologicalContext(context)

    # Access common properties
    print(wrapped.context_name)  # Works for all context types

    # Check capabilities
    if wrapped.is_simple_context_seg:
        print("This is a simple segment context")

    if wrapped.is_boundary_context:
        print("This is a boundary context")

    # Optional: Advanced users can access concrete types
    if wrapped.as_simple_context_seg():
        concrete = wrapped.as_simple_context_seg()
        # Use concrete interface for advanced operations
"""

from ..Shared.wrapper_base import LCMObjectWrapper
from ..lcm_casting import cast_to_concrete


class PhonologicalContext(LCMObjectWrapper):
    """
    Wrapper for phonological context objects providing unified interface access.

    Handles the multiple concrete types of phonological contexts transparently,
    providing common properties and capability checks without exposing ClassName
    or casting.

    Attributes:
        _obj: The base interface object (IPhPhonContext)
        _concrete: The concrete type object (IPhSimpleContextSeg, IPhSimpleContextNC,
                  IPhComplexContextSeg, IPhComplexContextNC, IPhBoundaryContext, etc.)

    Example::

        context = rule.input_contexts[0]
        wrapped = PhonologicalContext(context)
        print(wrapped.context_name)
        if wrapped.is_simple_context_seg:
            print("Simple segment context")
    """

    def __init__(self, lcm_context):
        """
        Initialize PhonologicalContext wrapper with a context object.

        Args:
            lcm_context: An IPhPhonContext object (or derived type).
                        Typically from a phonological rule's input_contexts.

        Example::

            context = rule.input_contexts[0]
            wrapped = PhonologicalContext(context)
        """
        super().__init__(lcm_context)

    # ========== Common Properties (work across all context types) ==========

    @property
    def context_name(self) -> str:
        """
        Get the context's name or identifier.

        Returns:
            str: The context name/identifier, or empty string if not set.

        Example::

            print(f"Context: {wrapped.context_name}")

        Notes:
            - For simple contexts, this may be the segment or natural class name
            - For boundary contexts, this identifies the boundary type
        """
        try:
            # Many contexts have a Name property
            if hasattr(self._concrete, "Name"):
                return str(self._concrete.Name) if self._concrete.Name else ""
            return ""
        except Exception:
            return ""

    @property
    def description(self) -> str:
        """
        Get the context's description if available.

        Returns:
            str: The description, or empty string if not set.

        Example::

            print(f"Context: {wrapped.description}")
        """
        try:
            if hasattr(self._concrete, "Description"):
                return str(self._concrete.Description) if self._concrete.Description else ""
            return ""
        except Exception:
            return ""

    # ========== Capability Checks (for type-specific properties) ==========

    @property
    def is_simple_context_seg(self):
        """
        Check if this is a simple segment context.

        Returns:
            bool: True if this is a PhSimpleContextSeg.

        Example::

            if wrapped.is_simple_context_seg:
                print("Simple segment context")

        Notes:
            - Simple segment contexts represent a single segment
            - Use segment property to access the actual segment
        """
        try:
            return self.class_type == "PhSimpleContextSeg"
        except Exception:
            return False

    @property
    def is_simple_context_nc(self):
        """
        Check if this is a simple natural class context.

        Returns:
            bool: True if this is a PhSimpleContextNC.

        Example::

            if wrapped.is_simple_context_nc:
                print("Simple natural class context")

        Notes:
            - Simple natural class contexts represent a natural class
            - Use natural_class property to access the actual natural class
        """
        try:
            return self.class_type == "PhSimpleContextNC"
        except Exception:
            return False

    @property
    def is_simple_context(self):
        """
        Check if this is any simple context (segment or natural class).

        Returns:
            bool: True if this is either PhSimpleContextSeg or PhSimpleContextNC.

        Example::

            if wrapped.is_simple_context:
                print("This is a simple context")

        Notes:
            - Convenience property for checking if context is "simple"
            - Use is_simple_context_seg or is_simple_context_nc for type specificity
        """
        return self.is_simple_context_seg or self.is_simple_context_nc

    @property
    def is_complex_context_seg(self):
        """
        Check if this is a complex segment context.

        Returns:
            bool: True if this is a PhComplexContextSeg.

        Example::

            if wrapped.is_complex_context_seg:
                print("Complex segment context")

        Notes:
            - Complex segment contexts have multiple segment specifications
        """
        try:
            return self.class_type == "PhComplexContextSeg"
        except Exception:
            return False

    @property
    def is_complex_context_nc(self):
        """
        Check if this is a complex natural class context.

        Returns:
            bool: True if this is a PhComplexContextNC.

        Example::

            if wrapped.is_complex_context_nc:
                print("Complex natural class context")

        Notes:
            - Complex natural class contexts have multiple natural class specifications
        """
        try:
            return self.class_type == "PhComplexContextNC"
        except Exception:
            return False

    @property
    def is_complex_context(self):
        """
        Check if this is any complex context (segment or natural class).

        Returns:
            bool: True if this is either PhComplexContextSeg or PhComplexContextNC.

        Example::

            if wrapped.is_complex_context:
                print("This is a complex context")

        Notes:
            - Convenience property for checking if context is "complex"
            - Use is_complex_context_seg or is_complex_context_nc for type specificity
        """
        return self.is_complex_context_seg or self.is_complex_context_nc

    @property
    def is_boundary_context(self):
        """
        Check if this is a boundary context.

        Returns:
            bool: True if this is a PhBoundaryContext.

        Example::

            if wrapped.is_boundary_context:
                print("Word/morpheme boundary context")

        Notes:
            - Boundary contexts represent word or morpheme boundaries
            - Different from other context types in purpose and properties
        """
        try:
            return self.class_type == "PhBoundaryContext"
        except Exception:
            return False

    # ========== Type-Specific Property Access (via capability checks) ==========

    @property
    def segment(self) -> "Optional[object]":
        """
        Get the segment from a simple segment context.

        Returns:
            The segment object if this is a PhSimpleContextSeg, None otherwise.

        Example::

            if wrapped.is_simple_context_seg:
                seg = wrapped.segment
                if seg:
                    print(f"Segment: {seg.Name}")

        Notes:
            - Only meaningful for PhSimpleContextSeg
            - Returns None for other context types
        """
        if not self.is_simple_context_seg:
            return None

        try:
            if hasattr(self._concrete, "SegmentRA"):
                return self._concrete.SegmentRA
            return None
        except Exception:
            return None

    @property
    def natural_class(self) -> "Optional[object]":
        """
        Get the natural class from a simple natural class context.

        Returns:
            The natural class object if this is a PhSimpleContextNC, None otherwise.

        Example::

            if wrapped.is_simple_context_nc:
                nc = wrapped.natural_class
                if nc:
                    print(f"Natural Class: {nc.Name}")

        Notes:
            - Only meaningful for PhSimpleContextNC
            - Returns None for other context types
        """
        if not self.is_simple_context_nc:
            return None

        try:
            if hasattr(self._concrete, "NaturalClassRA"):
                return self._concrete.NaturalClassRA
            return None
        except Exception:
            return None

    @property
    def boundary_type(self):
        """
        Get the boundary type from a boundary context.

        Returns:
            int: The boundary type (0=word, 1=morpheme, etc.), or -1 if not applicable.

        Example::

            if wrapped.is_boundary_context:
                btype = wrapped.boundary_type
                print(f"Boundary type: {btype}")

        Notes:
            - Only meaningful for PhBoundaryContext
            - Different boundary types have different values
        """
        if not self.is_boundary_context:
            return -1

        try:
            if hasattr(self._concrete, "Type"):
                return self._concrete.Type
            return -1
        except Exception:
            return -1

    # ========== Advanced: Direct C# class access (optional for power users) ==========

    def as_simple_context_seg(self):
        """
        Cast to IPhSimpleContextSeg if this is a simple segment context.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a PhSimpleContextSeg.

        Returns:
            IPhSimpleContextSeg or None: The concrete interface if this is a
                PhSimpleContextSeg, None otherwise.

        Example::

            if context_obj.as_simple_context_seg():
                concrete = context_obj.as_simple_context_seg()
                # Can now access IPhSimpleContextSeg-specific methods/properties
                segment = concrete.SegmentRA
                # Advanced operations...

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like is_simple_context_seg and
              segment instead
        """
        if self.class_type == "PhSimpleContextSeg":
            return self._concrete
        return None

    def as_simple_context_nc(self):
        """
        Cast to IPhSimpleContextNC if this is a simple natural class context.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a PhSimpleContextNC.

        Returns:
            IPhSimpleContextNC or None: The concrete interface if this is a
                PhSimpleContextNC, None otherwise.

        Example::

            if context_obj.as_simple_context_nc():
                concrete = context_obj.as_simple_context_nc()
                # Can now access IPhSimpleContextNC-specific methods/properties

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like is_simple_context_nc and
              natural_class instead
        """
        if self.class_type == "PhSimpleContextNC":
            return self._concrete
        return None

    def as_complex_context_seg(self):
        """
        Cast to IPhComplexContextSeg if this is a complex segment context.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a PhComplexContextSeg.

        Returns:
            IPhComplexContextSeg or None: The concrete interface if applicable.

        Example::

            if context_obj.as_complex_context_seg():
                concrete = context_obj.as_complex_context_seg()
                # Advanced operations...

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like is_complex_context_seg instead
        """
        if self.class_type == "PhComplexContextSeg":
            return self._concrete
        return None

    def as_complex_context_nc(self):
        """
        Cast to IPhComplexContextNC if this is a complex natural class context.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a PhComplexContextNC.

        Returns:
            IPhComplexContextNC or None: The concrete interface if applicable.

        Example::

            if context_obj.as_complex_context_nc():
                concrete = context_obj.as_complex_context_nc()
                # Advanced operations...

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like is_complex_context_nc instead
        """
        if self.class_type == "PhComplexContextNC":
            return self._concrete
        return None

    def as_boundary_context(self):
        """
        Cast to IPhBoundaryContext if this is a boundary context.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a PhBoundaryContext.

        Returns:
            IPhBoundaryContext or None: The concrete interface if this is a
                PhBoundaryContext, None otherwise.

        Example::

            if context_obj.as_boundary_context():
                concrete = context_obj.as_boundary_context()
                # Can now access IPhBoundaryContext-specific methods/properties

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like is_boundary_context and
              boundary_type instead
        """
        if self.class_type == "PhBoundaryContext":
            return self._concrete
        return None

    @property
    def concrete(self):
        """
        Get the raw concrete interface object.

        For advanced users who need to access the underlying C# interface
        directly without going through wrapper properties.

        Returns:
            The concrete interface object (IPhSimpleContextSeg, IPhSimpleContextNC,
            IPhComplexContextSeg, IPhComplexContextNC, IPhBoundaryContext, etc.,
            depending on the context's actual type).

        Example::

            # Direct access to concrete interface
            concrete = context_obj.concrete
            segment = concrete.SegmentRA  # PhSimpleContextSeg property

        Notes:
            - For power users only
            - Bypasses the wrapper's abstraction
            - Normal users should prefer wrapper properties like
              is_simple_context_seg, segment, etc.
        """
        return self._concrete

    def __repr__(self):
        """String representation showing context type."""
        return f"PhonologicalContext({self.class_type})"

    def __str__(self):
        """Human-readable description."""
        name = self.context_name or "Unnamed"
        return f"Context '{name}' ({self.class_type})"
