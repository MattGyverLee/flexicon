#
#   PythonicWrapper.py
#
#   Class: PythonicWrapper
#          Wraps LibLCM objects to provide suffix-free property access.
#          Translates pythonic names like 'Senses' to LibLCM names like 'SensesOS'.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

"""
Pythonic Wrapper for LibLCM Objects

LibLCM uses 2-character suffixes to indicate relationship types:
  - OA: Owning Atomic (single owned child)
  - OS: Owning Sequence (ordered collection of owned children)
  - OC: Owning Collection (unordered collection of owned children)
  - RA: Reference Atomic (single reference)
  - RS: Reference Sequence (ordered collection of references)
  - RC: Reference Collection (unordered collection of references)

This wrapper allows Python code to use suffix-free names:
  - entry.Senses instead of entry.SensesOS
  - entry.LexemeForm instead of entry.LexemeFormOA
  - sense.SemanticDomains instead of sense.SemanticDomainsRC

Usage::

    from flexlibs2.code.PythonicWrapper import wrap, unwrap

    # Wrap an LCM object
    entry = wrap(raw_entry)

    # Now use pythonic names
    for sense in entry.Senses:      # Resolves to SensesOS
        print(sense.Gloss)          # Resolves to Gloss (no suffix needed)

    # Unwrap to get original object
    raw = unwrap(entry)

    # Or use the p() shorthand
    from flexlibs2.code.PythonicWrapper import p
    for sense in p(entry).Senses:
        print(p(sense).Gloss)
"""

from .Shared.lcm_constants import SUFFIXES


class PythonicWrapper:
    """
    Wrapper that provides suffix-free property access to LibLCM objects.

    Uses __getattr__ to intercept attribute access and try suffixed variants
    when the base name isn't found.

    Example::

        wrapped = PythonicWrapper(entry)
        for sense in wrapped.Senses:  # Tries SensesOS, SensesOC, etc.
            text = wrapped.Gloss      # Returns Gloss directly if it exists
    """

    __slots__ = ("_obj", "_cache")

    def __init__(self, obj):
        """
        Initialize wrapper with an LCM object.

        Args:
            obj: The LibLCM object to wrap (ILexEntry, ILexSense, etc.)
        """
        object.__setattr__(self, "_obj", obj)
        object.__setattr__(self, "_cache", {})

    def __getattr__(self, name):
        """
        Get attribute, trying suffixed variants if base name not found.

        Resolution order:
        1. Check cache for previously resolved name
        2. Try the exact name on the wrapped object
        3. Try each suffix variant (OS, OC, OA, RS, RC, RA)
        4. Raise AttributeError if nothing found
        """
        # Check cache first
        cache = object.__getattribute__(self, "_cache")
        if name in cache:
            return getattr(object.__getattribute__(self, "_obj"), cache[name])

        obj = object.__getattribute__(self, "_obj")

        # Try exact name first
        if hasattr(obj, name):
            cache[name] = name
            return getattr(obj, name)

        # Try each suffix
        for suffix in SUFFIXES:
            suffixed_name = name + suffix
            if hasattr(obj, suffixed_name):
                cache[name] = suffixed_name
                return getattr(obj, suffixed_name)

        # Not found
        raise AttributeError(
            f"'{type(obj).__name__}' object has no attribute '{name}' "
            f"(also tried: {', '.join(name + s for s in SUFFIXES)})"
        )

    def __setattr__(self, name, value):
        """
        Set attribute, trying suffixed variants if base name not found.
        """
        if name in ("_obj", "_cache"):
            object.__setattr__(self, name, value)
            return

        obj = object.__getattribute__(self, "_obj")
        cache = object.__getattribute__(self, "_cache")

        # Check cache first
        if name in cache:
            setattr(obj, cache[name], value)
            return

        # Try exact name first
        if hasattr(obj, name):
            cache[name] = name
            setattr(obj, name, value)
            return

        # Try each suffix
        for suffix in SUFFIXES:
            suffixed_name = name + suffix
            if hasattr(obj, suffixed_name):
                cache[name] = suffixed_name
                setattr(obj, suffixed_name, value)
                return

        # Not found - try setting anyway (might be a new attribute)
        setattr(obj, name, value)

    def __repr__(self):
        obj = object.__getattribute__(self, "_obj")
        return f"PythonicWrapper({type(obj).__name__})"

    def __str__(self):
        obj = object.__getattribute__(self, "_obj")
        return str(obj)

    def __eq__(self, other):
        obj = object.__getattribute__(self, "_obj")
        if isinstance(other, PythonicWrapper):
            return obj == object.__getattribute__(other, "_obj")
        return obj == other

    def __hash__(self):
        obj = object.__getattribute__(self, "_obj")
        return hash(obj)

    def __iter__(self):
        """Allow iteration if wrapped object is iterable."""
        obj = object.__getattribute__(self, "_obj")
        return iter(obj)

    def __len__(self):
        """Return length if wrapped object has Count or __len__."""
        obj = object.__getattribute__(self, "_obj")
        if hasattr(obj, "Count"):
            return obj.Count
        return len(obj)

    def __getitem__(self, key):
        """Allow indexing if wrapped object supports it."""
        obj = object.__getattribute__(self, "_obj")
        return obj[key]

    def __contains__(self, item):
        """Support 'in' operator."""
        obj = object.__getattribute__(self, "_obj")
        if isinstance(item, PythonicWrapper):
            item = object.__getattribute__(item, "_obj")
        if hasattr(obj, "Contains"):
            return obj.Contains(item)
        return item in obj

    @property
    def _unwrap(self):
        """Get the underlying LCM object."""
        return object.__getattribute__(self, "_obj")


def wrap(obj):
    """
    Wrap an LCM object for pythonic property access.

    Args:
        obj: LibLCM object (ILexEntry, ILexSense, etc.)

    Returns:
        PythonicWrapper: Wrapped object with suffix-free property access

    Example::

        entry = wrap(raw_entry)
        for sense in entry.Senses:  # Uses SensesOS internally
            print(sense)
    """
    if obj is None:
        return None
    if isinstance(obj, PythonicWrapper):
        return obj  # Already wrapped
    return PythonicWrapper(obj)


def unwrap(obj):
    """
    Get the underlying LCM object from a wrapper.

    Args:
        obj: PythonicWrapper or raw LCM object

    Returns:
        The underlying LCM object

    Example::

        raw = unwrap(wrapped_entry)
    """
    if isinstance(obj, PythonicWrapper):
        return object.__getattribute__(obj, "_obj")
    return obj


# Shorthand alias
p = wrap
