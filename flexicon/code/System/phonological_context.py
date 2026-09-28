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
- PhSimpleContextBdry: Boundary context
- PhIterationContext: Iteration (repetition) context
- PhSequenceContext: Sequence of member contexts

All share a base interface IPhPhonContext.

Problem:
    Phonological contexts have different properties depending on their concrete type:
    - PhSimpleContextSeg: Represents a single segment
    - PhSimpleContextNC: Represents a natural class
    - PhComplexContextSeg: Complex segment specifications
    - PhComplexContextNC: Complex natural class specifications
    - PhSimpleContextBdry: Word/morpheme boundaries
    - PhIterationContext: A member context with repetition bounds
    - PhSequenceContext: An ordered sequence of member contexts

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

    from flexicon.code.System.phonological_context import PhonologicalContext

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

import logging

from ..Shared.string_utils import best_analysis_text, normalize_text
from ..Shared.wrapper_base import LCMObjectWrapper

logger = logging.getLogger(__name__)


class PhonologicalContext(LCMObjectWrapper):
    """
    Wrapper for phonological context objects providing unified interface access.

    Handles the multiple concrete types of phonological contexts transparently,
    providing common properties and capability checks without exposing ClassName
    or casting.

    Attributes:
        _obj: The base interface object (IPhPhonContext)
        _concrete: The concrete type object (IPhSimpleContextSeg, IPhSimpleContextNC,
                   IPhComplexContextSeg, IPhComplexContextNC, IPhSimpleContextBdry,
                   IPhIterationContext, IPhSequenceContext, etc.)

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
            - Read through best_analysis_text, never str(): Name is an
              IMultiString and str() returns a .NET type name.
        """
        try:
            return best_analysis_text(
                getattr(self._concrete, "Name", None)
            )
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

        Notes:
            - DescriptionOA is an owning atomic context whose own Name
              carries the text; an IStText paragraph fallback covers
              projects that store it as running text instead.
        """
        try:
            desc_oa = getattr(self._concrete, "DescriptionOA", None)
        except Exception:
            return ""
        if desc_oa is None:
            return ""
        try:
            name = getattr(desc_oa, "Name", None)
            if name is not None:
                text = best_analysis_text(name)
                if text:
                    return text
        except Exception:
            pass
        try:
            paragraphs = getattr(desc_oa, "ParagraphsOS", None)
            if paragraphs is not None:
                texts = []
                for para in paragraphs:
                    try:
                        contents = para.Contents
                        para_text = (
                            contents.Text if contents is not None else ""
                        )
                        if para_text:
                            texts.append(para_text)
                    except Exception:
                        continue
                return normalize_text("\n".join(texts))
        except Exception:
            pass
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
            bool: True if this is a PhSimpleContextBdry.

        Example::

            if wrapped.is_boundary_context:
                print("Word/morpheme boundary context")

        Notes:
            - Boundary contexts represent word or morpheme boundaries
            - Different from other context types in purpose and properties
            - The LCM class is PhSimpleContextBdry; identity is the IPhBdryMarker
              behind FeatureStructureRA, exposed as boundary_marker/boundary_name.
        """
        try:
            return self.class_type == "PhSimpleContextBdry"
        except Exception:
            return False

    @property
    def boundary_marker(self):
        """
        Get the boundary marker for a boundary context.

        Returns:
            IPhBdryMarker or None: The marker behind FeatureStructureRA,
                or None when this is not a boundary context or no marker
                is set.

        Example::

            if wrapped.is_boundary_context:
                marker = wrapped.boundary_marker
                print(f"Marker: {wrapped.boundary_name}")

        Notes:
            - Only meaningful for PhSimpleContextBdry
            - Returns None for other context types
        """
        if not self.is_boundary_context:
            return None

        try:
            fsra = getattr(self._concrete, "FeatureStructureRA", None)
            if fsra is None:
                return None
            from SIL.LCModel import IPhBdryMarker

            return IPhBdryMarker(fsra)
        except Exception:
            logger.debug(
                "boundary_marker: failed to cast FeatureStructureRA "
                "to IPhBdryMarker",
                exc_info=True,
            )
            return None

    @property
    def boundary_name(self) -> str:
        """
        Get the boundary marker's name text.

        Returns:
            str: The marker name, or empty string when unset or when this
                is not a boundary context.

        Example::

            if wrapped.is_boundary_context:
                print(f"Boundary: {wrapped.boundary_name}")
        """
        try:
            marker = self.boundary_marker
            if marker is None:
                return ""
            return best_analysis_text(getattr(marker, "Name", None))
        except Exception:
            return ""

    # ========== Iteration and sequence contexts (C5, C6) ==========

    @property
    def is_iteration_context(self) -> bool:
        """
        Check if this is an iteration (repetition) context.

        Returns:
            bool: True if this is a PhIterationContext.

        Example::

            if wrapped.is_iteration_context:
                print(f"Repeats {wrapped.min_count}..{wrapped.max_count}")
        """
        try:
            return self.class_type == "PhIterationContext"
        except Exception:
            return False

    @property
    def min_count(self) -> int:
        """
        Get the minimum repetition count of an iteration context.

        Returns:
            int: Minimum, or -1 when this is not an iteration context.

        Example::

            if wrapped.is_iteration_context:
                print(f"At least {wrapped.min_count} repetitions")
        """
        if not self.is_iteration_context:
            return -1
        try:
            return int(self._concrete.Minimum)
        except Exception:
            return -1

    @property
    def max_count(self):
        """
        Get the maximum repetition count of an iteration context.

        Returns:
            Optional[int]: Maximum, or None when unbounded (the LCM stores
                -1 for unbounded; FieldWorks renders it as infinity at
                Src/LexText/Morphology/RuleFormulaVcBase.cs:554, so the raw
                -1 is not exposed). None for a non-iteration context.

        Example::

            if wrapped.is_iteration_context:
                maximum = wrapped.max_count
                print("unbounded" if maximum is None else f"At most {maximum}")
        """
        if not self.is_iteration_context:
            return None
        try:
            maximum = int(self._concrete.Maximum)
        except Exception:
            return None
        if maximum == -1:
            return None
        return maximum

    @property
    def member(self):
        """
        Get the repeated member context of an iteration context.

        Returns:
            Optional[PhonologicalContext]: The MemberRA context wrapped,
                or None when this is not an iteration context or no member
                is set.

        Example::

            if wrapped.is_iteration_context:
                print(f"Repeats: {wrapped.member.context_name}")
        """
        if not self.is_iteration_context:
            return None
        try:
            member = getattr(self._concrete, "MemberRA", None)
            if member is None:
                return None
            return PhonologicalContext(member)
        except Exception:
            logger.debug(
                "member: failed to wrap MemberRA", exc_info=True
            )
            return None

    @property
    def is_sequence_context(self) -> bool:
        """
        Check if this is a sequence context.

        Returns:
            bool: True if this is a PhSequenceContext.

        Example::

            if wrapped.is_sequence_context:
                for element in wrapped.members:
                    print(element.context_name)
        """
        try:
            return self.class_type == "PhSequenceContext"
        except Exception:
            return False

    @property
    def members(self):
        """
        Get the member contexts of a sequence context.

        Returns:
            ContextCollection: The wrapped MembersRS references. Empty for
                a non-sequence context.

        Notes:
            - The members are references into PhonologicalDataOA.ContextsOS
              (the project-wide owner pool), not owned children of the
              sequence. Removing the sequence slot without removing its
              members from the pool leaks them.

        Example::

            if wrapped.is_sequence_context:
                for element in wrapped.members:
                    print(element.context_name)
        """
        from .context_collection import ContextCollection

        if not self.is_sequence_context:
            return ContextCollection([])
        try:
            refs = getattr(self._concrete, "MembersRS", None)
            if refs is None:
                return ContextCollection([])
            return ContextCollection([PhonologicalContext(m) for m in refs])
        except Exception:
            logger.debug(
                "members: failed to wrap MembersRS", exc_info=True
            )
            return ContextCollection([])

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
                    from flexicon.code.Shared.string_utils import (
                        best_analysis_text,
                    )

                    print(f"Segment: {best_analysis_text(seg.Name)}")

        Notes:
            - Only meaningful for PhSimpleContextSeg
            - Returns None for other context types
        """
        if not self.is_simple_context_seg:
            return None

        try:
            fsra = getattr(self._concrete, "FeatureStructureRA", None)
            if fsra is None:
                return None
            # Live LCM uses FeatureStructureRA as the link to the phoneme
            # (despite the name; SegmentRA does not exist).
            from SIL.LCModel import IPhPhoneme

            return IPhPhoneme(fsra)
        except Exception:
            logger.debug("segment: failed to cast FeatureStructureRA to IPhPhoneme", exc_info=True)
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
                    from flexicon.code.Shared.string_utils import (
                        best_analysis_text,
                    )

                    print(f"Natural Class: {best_analysis_text(nc.Name)}")

        Notes:
            - Only meaningful for PhSimpleContextNC
            - Returns None for other context types
        """
        if not self.is_simple_context_nc:
            return None

        try:
            fsra = getattr(self._concrete, "FeatureStructureRA", None)
            if fsra is None:
                return None
            # Live LCM uses FeatureStructureRA as the link to the natural
            # class (despite the name; NaturalClassRA does not exist).
            from SIL.LCModel import IPhNaturalClass

            return IPhNaturalClass(fsra)
        except Exception:
            logger.debug("natural_class: failed to cast FeatureStructureRA to IPhNaturalClass", exc_info=True)
            return None

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
                # Can now access IPhSimpleContextSeg-specific methods/properties.
                # The phoneme link lives on FeatureStructureRA, not SegmentRA.
                from SIL.LCModel import IPhPhoneme

                segment = IPhPhoneme(concrete.FeatureStructureRA)
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
        Cast to IPhSimpleContextBdry if this is a boundary context.

        For advanced users who need direct access to the C# concrete interface.
        Returns None if this is not a PhSimpleContextBdry.

        Returns:
            IPhSimpleContextBdry or None: The concrete interface if this is a
                PhSimpleContextBdry, None otherwise.

        Example::

            if context_obj.as_boundary_context():
                concrete = context_obj.as_boundary_context()
                # Can now access IPhSimpleContextBdry-specific methods/properties

        Notes:
            - For users who know C# interfaces and want advanced control
            - Most users should use properties like is_boundary_context and
              boundary_name instead
        """
        if self.is_boundary_context:
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
            IPhComplexContextSeg, IPhComplexContextNC, IPhSimpleContextBdry,
            IPhIterationContext, IPhSequenceContext, etc.,
            depending on the context's actual type).

        Example::

            # Direct access to concrete interface
            concrete = context_obj.concrete
            # PhSimpleContextSeg links to its phoneme via FeatureStructureRA,
            # not SegmentRA (SegmentRA does not exist in this LCM).
            from SIL.LCModel import IPhPhoneme

            segment = IPhPhoneme(concrete.FeatureStructureRA)

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
