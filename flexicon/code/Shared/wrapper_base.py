#
#   wrapper_base.py
#
#   Class: LCMObjectWrapper
#          Base class for wrapping LCM objects with unified interface access.
#          Transparently handles casting from base interfaces to concrete types.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Base wrapper class for LCM objects with intelligent property routing.

This module provides LCMObjectWrapper, a base class for creating wrapper objects
that transparently handle the two-layer LCM type system:

- Base Interface: Generic interface typed by pythonnet (e.g., IPhSegmentRule)
- Concrete Type: Actual runtime type identified by ClassName attribute
- Concrete Interface: Type-specific interface with additional properties

The Problem:
    In pythonnet, when you access objects from a collection, they're typed as
    the base interface. Accessing concrete type-specific properties requires
    explicit casting based on the ClassName attribute.

The Solution:
    LCMObjectWrapper stores both the base interface and concrete type, then
    uses __getattr__() to route property access intelligently:
    - Try concrete type first (more specific properties)
    - Fall back to base interface if property doesn't exist
    - Return None for missing properties instead of raising AttributeError

Example::

    from flexlibs2.code.Shared.wrapper_base import LCMObjectWrapper
    from flexlibs2.code.lcm_casting import cast_to_concrete

    # Wrap an LCM object
    rule = phonRuleOps.GetAll()[0]  # Typed as IPhSegmentRule
    wrapped = LCMObjectWrapper(rule)

    # Access type-specific properties transparently
    if wrapped.ClassName == 'PhRegularRule':
        rhs_count = wrapped.RightHandSidesOS.Count  # Works without casting!

    # Check what properties are available
    common_props = wrapped.get_property('StrucDescOS')
    if common_props:
        print(f"Rule has {len(common_props)} input contexts")

Usage Notes:
    - Wrapper classes inherit from LCMObjectWrapper
    - Never access _obj or _concrete directly in subclasses
    - Use get_property() for safe access with defaults
    - Use class_type property to check the concrete type
"""

from ..lcm_casting import cast_to_concrete


class LCMObjectWrapper:
    """
    Base wrapper for LCM objects providing unified interface access.

    Stores both the base interface and concrete type, routing property access
    intelligently to support the two-layer LCM type system transparently.

    Attributes:
        _obj: The base interface object (e.g., IPhSegmentRule)
        _concrete: The concrete type object (e.g., IPhRegularRule)
    """

    def __init__(self, lcm_obj):
        """
        Initialize wrapper with an LCM object.

        Automatically casts the object to its concrete type using the
        lcm_casting module. Both base and concrete are stored for
        flexible property access.

        Args:
            lcm_obj: An LCM object with a ClassName attribute.
                    Typically a base interface type (e.g., IPhSegmentRule,
                    IMoMorphSynAnalysis, IMoForm).

        Example::

            rule = phonRuleOps.GetAll()[0]
            wrapped = LCMObjectWrapper(rule)
            print(wrapped.class_type)  # "PhRegularRule" or similar
        """
        self._obj = lcm_obj
        self._concrete = cast_to_concrete(lcm_obj)

    def __getattr__(self, name):
        """
        Route property access intelligently across base and concrete types.

        When a property is accessed on the wrapper, this method:
        1. First tries the concrete type (more specific)
        2. Falls back to the base interface if property not found
        3. Raises AttributeError only if property doesn't exist on either

        This allows seamless access to both common properties (on base interface)
        and type-specific properties (on concrete interface) without manual casting.

        Args:
            name: Property or method name being accessed.

        Returns:
            The property value or method from whichever type has it.

        Raises:
            AttributeError: If the property doesn't exist on either type.

        Example::

            # Access common property on base interface
            name = wrapped.Name

            # Access type-specific property on concrete interface
            if wrapped.ClassName == 'PhRegularRule':
                rhs = wrapped.RightHandSidesOS  # Concrete type only

            # Calling methods works transparently
            wrapped.SomeMethod()
        """
        # Prevent infinite recursion when accessing _obj or _concrete
        if name in ("_obj", "_concrete"):
            raise AttributeError(f"'{type(self).__name__}' object has no attribute '{name}'")

        # Try concrete type first (more specific)
        try:
            return getattr(self._concrete, name)
        except AttributeError:
            pass

        # Fall back to base interface
        try:
            return getattr(self._obj, name)
        except AttributeError:
            pass

        # Property not found on either type
        raise AttributeError(f"'{type(self).__name__}' object and its wrapped LCM object have no attribute '{name}'")

    @property
    def class_type(self):
        """
        Get the concrete class type as a string.

        Returns the ClassName attribute, which uniquely identifies the concrete
        type of the wrapped object. This is the primary way to check which
        concrete interface the object implements.

        Returns:
            str: The ClassName (e.g., "PhRegularRule", "PhMetathesisRule",
                "MoStemMsa", "MoInflAffMsa", etc.)

        Example::

            wrapped = LCMObjectWrapper(rule)
            if wrapped.class_type == 'PhRegularRule':
                # Object is a regular phonological rule
                pass
            elif wrapped.class_type == 'PhMetathesisRule':
                # Object is a metathesis rule
                pass
        """
        return self._obj.ClassName

    def get_property(self, prop_name, default=None):
        """
        Safely get a property value with a fallback default.

        Attempts to access a property on the wrapped object, returning
        a default value if the property doesn't exist. This is safer than
        direct property access when you're unsure whether a property exists
        on the wrapped object's type.

        Args:
            prop_name: Name of the property to access.
            default: Value to return if property doesn't exist. Default: None.

        Returns:
            The property value if it exists, otherwise the default value.

        Example::

            # Safe access to type-specific properties
            rhs = wrapped.get_property('RightHandSidesOS')
            if rhs:
                print(f"Rule has {rhs.Count} RHS")

            # Check for optional properties
            frequency = wrapped.get_property('Frequency', 0)
            print(f"Rule frequency: {frequency}")

            # Provide meaningful defaults
            context_count = wrapped.get_property('StrucDescOS', [])
            print(f"Input contexts: {len(context_count)}")
        """
        try:
            return getattr(self, prop_name)
        except AttributeError:
            return default

    def __repr__(self):
        """
        String representation showing the wrapped object's class type.

        Returns:
            str: Representation like "LCMObjectWrapper(PhRegularRule)"
        """
        return f"{type(self).__name__}({self.class_type})"

    def __str__(self):
        """
        Human-readable string representation.

        Returns:
            str: Description like "Wrapped LCM object of type PhRegularRule"
        """
        return f"Wrapped LCM object of type {self.class_type}"
