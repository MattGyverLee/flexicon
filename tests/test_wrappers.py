#
# test_wrappers.py
#
# Unit tests for LCMObjectWrapper class
#
# Tests the wrapper functionality for transparently accessing both base
# and concrete interface properties without manual casting.
#
# Platform: Python.NET
#           FieldWorks Version 9+
#
# Copyright 2025
#

"""
Unit tests for LCMObjectWrapper class.

This test suite validates that the LCMObjectWrapper class correctly:
- Stores both base and concrete interfaces
- Routes property access intelligently (concrete first, then base)
- Provides the class_type property
- Implements get_property() with defaults
- Handles both properties and methods
- Works with various mock LCM object types
- Properly handles missing properties
- String representations work correctly
"""

import pytest
from unittest.mock import Mock, MagicMock, PropertyMock
import sys
import os

# Add project root to path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_test_dir)
sys.path.insert(0, _project_root)

from flexlibs2.code.Shared.wrapper_base import LCMObjectWrapper


# =============================================================================
# FIXTURES FOR MOCK LCM OBJECTS
# =============================================================================


@pytest.fixture
def mock_base_interface():
    """
    Fixture: Mock base interface object (e.g., IPhSegmentRule).

    Simulates a basic LCM interface with:
    - ClassName attribute identifying the concrete type
    - Common properties available on all types
    - Methods that can be called
    """
    obj = Mock()
    obj.ClassName = "PhRegularRule"
    obj.Id = "guid-rule-001"
    obj.Hvo = 5001
    obj.Name = "voicing_rule"
    obj.Direction = "LTR"
    obj.SomeMethod = Mock(return_value="method_result")
    return obj


@pytest.fixture
def mock_concrete_interface():
    """
    Fixture: Mock concrete interface object (e.g., IPhRegularRule).

    Simulates a concrete type with:
    - All properties from base interface
    - Type-specific properties (e.g., RightHandSidesOS)
    - Methods from derived type
    """
    obj = Mock()
    obj.ClassName = "PhRegularRule"
    obj.Id = "guid-rule-001"
    obj.Hvo = 5001
    obj.Name = "voicing_rule"
    obj.Direction = "LTR"
    obj.RightHandSidesOS = Mock()
    obj.RightHandSidesOS.Count = 3
    obj.SomeMethod = Mock(return_value="method_result")
    obj.ConcreteOnlyMethod = Mock(return_value="concrete_result")
    return obj


@pytest.fixture
def mock_cast_to_concrete(mock_base_interface, mock_concrete_interface, monkeypatch):
    """
    Fixture: Mock the cast_to_concrete function.

    Returns the concrete interface when cast_to_concrete is called,
    allowing tests to isolate wrapper behavior from actual casting logic.
    """

    def _cast(obj):
        """Mock cast function that returns concrete when called."""
        if obj == mock_base_interface:
            return mock_concrete_interface
        return obj

    monkeypatch.setattr("flexlibs2.code.Shared.wrapper_base.cast_to_concrete", _cast)
    return _cast


@pytest.fixture
def wrapped_object(mock_base_interface, mock_cast_to_concrete):
    """
    Fixture: LCMObjectWrapper wrapping a mock base interface.

    Creates a wrapper with both base and concrete interfaces mocked,
    ready for testing property access patterns.
    """
    return LCMObjectWrapper(mock_base_interface)


# =============================================================================
# TESTS FOR INITIALIZATION
# =============================================================================


class TestLCMObjectWrapperInit:
    """Test __init__() method stores both base and concrete interfaces."""

    def test_init_stores_base_interface(self, mock_base_interface, mock_cast_to_concrete):
        """Test that __init__() stores the base interface."""
        wrapper = LCMObjectWrapper(mock_base_interface)
        assert wrapper._obj == mock_base_interface

    def test_init_stores_concrete_interface(self, mock_base_interface, mock_concrete_interface, mock_cast_to_concrete):
        """Test that __init__() stores the concrete interface via cast_to_concrete()."""
        wrapper = LCMObjectWrapper(mock_base_interface)
        assert wrapper._concrete == mock_concrete_interface

    def test_init_calls_cast_to_concrete(self, mock_base_interface, mock_cast_to_concrete):
        """Test that __init__() calls cast_to_concrete() on the object."""
        mock_base_interface.ClassName = "TestType"
        wrapper = LCMObjectWrapper(mock_base_interface)
        # Verify cast_to_concrete was called by checking concrete was set
        assert hasattr(wrapper, "_concrete")


# =============================================================================
# TESTS FOR PROPERTY ROUTING (__getattr__)
# =============================================================================


class TestLCMObjectWrapperGetAttr:
    """Test __getattr__() property routing across base and concrete types."""

    def test_getattr_accesses_concrete_property(self, wrapped_object, mock_concrete_interface):
        """Test that __getattr__() returns properties from concrete type."""
        # RightHandSidesOS is only on concrete type
        result = wrapped_object.RightHandSidesOS
        assert result == mock_concrete_interface.RightHandSidesOS

    def test_getattr_prefers_concrete_over_base(self, wrapped_object, mock_concrete_interface, mock_base_interface):
        """Test that concrete properties are preferred over base interface."""
        # Both have 'Name', but concrete should be tried first
        result = wrapped_object.Name
        # Should get from concrete (which is mocked)
        assert result == mock_concrete_interface.Name

    def test_getattr_falls_back_to_base(self, wrapped_object, mock_base_interface):
        """Test that __getattr__() falls back to base interface if concrete doesn't have property."""
        # SomeMethod exists on base interface
        wrapped_object._concrete = Mock(spec=[])  # Concrete with no attributes
        result = wrapped_object.SomeMethod
        assert result == mock_base_interface.SomeMethod

    def test_getattr_raises_attribute_error_when_missing(
        self, mock_base_interface, mock_concrete_interface, mock_cast_to_concrete
    ):
        """Test that __getattr__() raises AttributeError for missing properties."""
        # Configure mocks to raise AttributeError for unknown properties
        mock_base_interface_limited = Mock(spec=["ClassName", "Name"])
        mock_base_interface_limited.ClassName = "TestType"
        mock_base_interface_limited.Name = "test"

        # Set up cast to return concrete with limited spec
        mock_concrete_limited = Mock(spec=["ClassName", "Name"])
        mock_concrete_limited.ClassName = "TestType"

        def _cast_limited(obj):
            return mock_concrete_limited

        import flexlibs2.code.Shared.wrapper_base as wrapper_module

        original_cast = wrapper_module.cast_to_concrete
        wrapper_module.cast_to_concrete = _cast_limited

        try:
            wrapper = LCMObjectWrapper(mock_base_interface_limited)
            with pytest.raises(AttributeError) as exc_info:
                _ = wrapper.NonExistentProperty
            assert "NonExistentProperty" in str(exc_info.value)
        finally:
            wrapper_module.cast_to_concrete = original_cast

    def test_getattr_prevents_infinite_recursion(
        self, mock_base_interface, mock_concrete_interface, mock_cast_to_concrete
    ):
        """Test that __getattr__() prevents infinite recursion for _obj and _concrete."""
        wrapper = LCMObjectWrapper(mock_base_interface)
        # These should be accessible as object attributes, not through __getattr__
        # So they should not raise AttributeError - they should work normally
        assert wrapper._obj is not None
        assert wrapper._concrete is not None

    def test_getattr_accesses_methods_on_concrete(self, wrapped_object, mock_concrete_interface):
        """Test that __getattr__() can access methods from concrete type."""
        method = wrapped_object.ConcreteOnlyMethod
        assert method == mock_concrete_interface.ConcreteOnlyMethod

    def test_getattr_calls_method_successfully(self, wrapped_object):
        """Test that methods accessed through wrapper can be called."""
        # SomeMethod is available on both base and concrete
        result = wrapped_object.SomeMethod()
        assert result == "method_result"

    def test_getattr_handles_attribute_on_both_types(
        self, mock_base_interface, mock_concrete_interface, mock_cast_to_concrete
    ):
        """Test __getattr__() when attribute exists on both types."""
        # Direction exists on both - concrete should be tried first
        wrapper = LCMObjectWrapper(mock_base_interface)
        result = wrapper.Direction
        assert result == "LTR"


# =============================================================================
# TESTS FOR CLASS_TYPE PROPERTY
# =============================================================================


class TestLCMObjectWrapperClassType:
    """Test class_type property returns ClassName."""

    def test_class_type_returns_classname(self, wrapped_object):
        """Test that class_type property returns the ClassName attribute."""
        assert wrapped_object.class_type == "PhRegularRule"

    def test_class_type_with_different_types(self, mock_cast_to_concrete):
        """Test class_type with different concrete types."""
        # Test with MetathesisRule
        obj = Mock()
        obj.ClassName = "PhMetathesisRule"
        mock_cast_to_concrete(obj)
        wrapper = LCMObjectWrapper(obj)
        assert wrapper.class_type == "PhMetathesisRule"

        # Test with ReduplicationRule
        obj2 = Mock()
        obj2.ClassName = "PhReduplicationRule"
        mock_cast_to_concrete(obj2)
        wrapper2 = LCMObjectWrapper(obj2)
        assert wrapper2.class_type == "PhReduplicationRule"

    def test_class_type_is_read_only(self, wrapped_object):
        """Test that class_type property is read-only."""
        with pytest.raises(AttributeError):
            wrapped_object.class_type = "SomeOtherType"


# =============================================================================
# TESTS FOR GET_PROPERTY METHOD
# =============================================================================


class TestLCMObjectWrapperGetProperty:
    """Test get_property() method with valid and invalid properties."""

    def test_get_property_returns_existing_property(self, wrapped_object):
        """Test get_property() returns the property value when it exists."""
        result = wrapped_object.get_property("Name")
        assert result == "voicing_rule"

    def test_get_property_returns_concrete_property(self, wrapped_object, mock_concrete_interface):
        """Test get_property() can access concrete-only properties."""
        result = wrapped_object.get_property("RightHandSidesOS")
        assert result == mock_concrete_interface.RightHandSidesOS

    def test_get_property_returns_default_for_missing(self, mock_cast_to_concrete):
        """Test get_property() returns default when property doesn't exist."""
        # Use spec to prevent Mock from creating attributes automatically
        obj = Mock(spec=["ClassName", "Name"])
        obj.ClassName = "TestType"
        obj.Name = "test"
        mock_cast_to_concrete(obj)
        wrapper = LCMObjectWrapper(obj)

        result = wrapper.get_property("NonExistent")
        assert result is None

    def test_get_property_returns_custom_default(self, mock_cast_to_concrete):
        """Test get_property() returns custom default value."""
        obj = Mock(spec=["ClassName", "Name"])
        obj.ClassName = "TestType"
        obj.Name = "test"
        mock_cast_to_concrete(obj)
        wrapper = LCMObjectWrapper(obj)

        result = wrapper.get_property("NonExistent", "custom_default")
        assert result == "custom_default"

    def test_get_property_with_list_default(self, mock_cast_to_concrete):
        """Test get_property() with list as default."""
        obj = Mock(spec=["ClassName"])
        obj.ClassName = "TestType"
        mock_cast_to_concrete(obj)
        wrapper = LCMObjectWrapper(obj)

        result = wrapper.get_property("NonExistent", [])
        assert result == []

    def test_get_property_with_zero_default(self, mock_cast_to_concrete):
        """Test get_property() with numeric default (0)."""
        obj = Mock(spec=["ClassName"])
        obj.ClassName = "TestType"
        mock_cast_to_concrete(obj)
        wrapper = LCMObjectWrapper(obj)

        result = wrapper.get_property("NonExistent", 0)
        assert result == 0

    def test_get_property_with_false_default(self, mock_cast_to_concrete):
        """Test get_property() with False as default (falsy value)."""
        obj = Mock(spec=["ClassName"])
        obj.ClassName = "TestType"
        mock_cast_to_concrete(obj)
        wrapper = LCMObjectWrapper(obj)

        result = wrapper.get_property("NonExistent", False)
        assert result is False

    def test_get_property_none_is_valid_value(self, mock_base_interface, mock_cast_to_concrete):
        """Test get_property() distinguishes None as actual value vs default."""
        # If a property actually has None value, should return None (not default)
        obj = Mock()
        obj.ClassName = "TestType"
        obj.NullProperty = None
        mock_cast_to_concrete(obj)
        wrapper = LCMObjectWrapper(obj)
        # This is tricky - we need to test that accessing None property works
        result = wrapper.get_property("NullProperty", "default")
        # Should return None because property exists (even though value is None)
        # However, get_property catches AttributeError, so if property exists, we get it
        assert result is None


# =============================================================================
# TESTS FOR ACCESSING CONCRETE-SPECIFIC PROPERTIES
# =============================================================================


class TestLCMObjectWrapperConcreteProperties:
    """Test accessing concrete type-specific properties through wrapper."""

    def test_access_phonological_rule_specific_properties(self, wrapped_object):
        """Test accessing PhRegularRule-specific properties."""
        # RightHandSidesOS is specific to PhRegularRule
        rhs = wrapped_object.RightHandSidesOS
        assert rhs is not None
        assert rhs.Count == 3

    def test_access_nested_properties(self, wrapped_object):
        """Test accessing nested properties through wrapper."""
        # Access a property and then access its attributes
        rhs = wrapped_object.RightHandSidesOS
        count = rhs.Count
        assert count == 3

    def test_access_multiple_concrete_properties(
        self, mock_base_interface, mock_concrete_interface, mock_cast_to_concrete
    ):
        """Test accessing multiple concrete-specific properties."""
        # Set up concrete with multiple properties
        mock_concrete_interface.LeftContextOS = Mock(Count=2)
        mock_concrete_interface.RightContextOS = Mock(Count=1)

        wrapper = LCMObjectWrapper(mock_base_interface)

        assert wrapper.LeftContextOS.Count == 2
        assert wrapper.RightContextOS.Count == 1


# =============================================================================
# TESTS FOR __repr__ AND __str__
# =============================================================================


class TestLCMObjectWrapperStringRepresentations:
    """Test string representations of wrapper objects."""

    def test_repr_shows_class_type(self, wrapped_object):
        """Test __repr__() shows wrapper class and LCM class type."""
        repr_str = repr(wrapped_object)
        assert "LCMObjectWrapper" in repr_str
        assert "PhRegularRule" in repr_str

    def test_repr_format(self, wrapped_object):
        """Test __repr__() format matches expected pattern."""
        repr_str = repr(wrapped_object)
        assert repr_str == "LCMObjectWrapper(PhRegularRule)"

    def test_str_is_human_readable(self, wrapped_object):
        """Test __str__() returns human-readable description."""
        str_repr = str(wrapped_object)
        assert "Wrapped" in str_repr
        assert "PhRegularRule" in str_repr

    def test_str_format(self, wrapped_object):
        """Test __str__() format."""
        str_repr = str(wrapped_object)
        assert str_repr == "Wrapped LCM object of type PhRegularRule"

    def test_repr_with_different_types(self, mock_cast_to_concrete):
        """Test __repr__() with different concrete types."""
        obj = Mock()
        obj.ClassName = "MoStemMsa"
        mock_cast_to_concrete(obj)
        wrapper = LCMObjectWrapper(obj)

        assert "MoStemMsa" in repr(wrapper)


# =============================================================================
# TESTS FOR EDGE CASES AND ERROR CONDITIONS
# =============================================================================


class TestLCMObjectWrapperEdgeCases:
    """Test edge cases and error conditions."""

    def test_wrapper_with_minimal_mock(self, mock_cast_to_concrete):
        """Test wrapper with minimal mock object (only ClassName)."""
        obj = Mock()
        obj.ClassName = "MinimalType"
        mock_cast_to_concrete(obj)

        wrapper = LCMObjectWrapper(obj)
        assert wrapper.class_type == "MinimalType"

    def test_property_with_special_characters(
        self, mock_base_interface, mock_concrete_interface, mock_cast_to_concrete
    ):
        """Test accessing properties with special naming conventions."""
        mock_concrete_interface.PropertyWithOS = Mock()
        mock_base_interface.PropertyWithOS = None

        wrapper = LCMObjectWrapper(mock_base_interface)
        result = wrapper.PropertyWithOS
        assert result is not None

    def test_accessing_collection_properties(self, mock_base_interface, mock_concrete_interface, mock_cast_to_concrete):
        """Test accessing collection-type properties (e.g., SomethingOS)."""
        mock_concrete_interface.AllomorphsOS = Mock()
        mock_concrete_interface.AllomorphsOS.Count = 5

        wrapper = LCMObjectWrapper(mock_base_interface)
        allomorphs = wrapper.AllomorphsOS
        assert allomorphs.Count == 5

    def test_wrapper_preserves_mock_behavior(self, mock_base_interface, mock_concrete_interface, mock_cast_to_concrete):
        """Test that wrapper preserves behavior of mocked methods."""
        mock_concrete_interface.CallableMethod = Mock(return_value=42)

        wrapper = LCMObjectWrapper(mock_base_interface)
        result = wrapper.CallableMethod()
        assert result == 42

    def test_wrapper_with_property_that_raises_exception(
        self, mock_base_interface, mock_concrete_interface, mock_cast_to_concrete
    ):
        """Test wrapper behavior when property access raises an exception."""
        # Set concrete to raise when accessing this property
        type(mock_concrete_interface).BadProperty = PropertyMock(side_effect=RuntimeError("Property access failed"))

        wrapper = LCMObjectWrapper(mock_base_interface)
        with pytest.raises(RuntimeError):
            _ = wrapper.BadProperty

    def test_get_property_handles_exceptions_gracefully(self, mock_cast_to_concrete):
        """Test that get_property() returns default if property raises exception."""
        # Create mocks with limited spec so they raise AttributeError for unknown properties
        obj = Mock(spec=["ClassName", "ExistingProp"])
        obj.ClassName = "TestType"
        obj.ExistingProp = "value"

        concrete = Mock(spec=["ClassName", "ExistingProp"])
        concrete.ClassName = "TestType"

        def _cast(o):
            return concrete

        import flexlibs2.code.Shared.wrapper_base as wrapper_module

        original_cast = wrapper_module.cast_to_concrete
        wrapper_module.cast_to_concrete = _cast

        try:
            wrapper = LCMObjectWrapper(obj)
            # get_property should return default when property doesn't exist
            result = wrapper.get_property("NonExistent", "fallback")
            assert result == "fallback"
        finally:
            wrapper_module.cast_to_concrete = original_cast


# =============================================================================
# TESTS FOR INTEGRATION WITH MOCK OBJECTS
# =============================================================================


class TestLCMObjectWrapperWithMockTypes:
    """Test wrapper with various mock object configurations."""

    def test_wrapper_with_dict_like_mock(self, mock_cast_to_concrete):
        """Test wrapper with mock configured like a dictionary."""
        obj = Mock()
        obj.ClassName = "DictLikeMock"
        obj.attribute = "value"
        mock_cast_to_concrete(obj)

        wrapper = LCMObjectWrapper(obj)
        assert wrapper.attribute == "value"

    def test_wrapper_with_spec_mock(self, mock_cast_to_concrete):
        """Test wrapper with mock configured with spec."""

        class TestInterface:
            ClassName = "SpecMock"
            Name = "test"

            def method(self):
                pass

        obj = Mock(spec=TestInterface)
        obj.ClassName = "SpecMock"
        obj.Name = "test"
        mock_cast_to_concrete(obj)

        wrapper = LCMObjectWrapper(obj)
        assert wrapper.class_type == "SpecMock"
        assert wrapper.Name == "test"

    def test_wrapper_with_multiple_property_accesses(self, wrapped_object):
        """Test wrapper with repeated property accesses."""
        # Access same property multiple times
        result1 = wrapped_object.Name
        result2 = wrapped_object.Name
        result3 = wrapped_object.Name

        assert result1 == result2 == result3 == "voicing_rule"

    def test_wrapper_with_method_chain(self, mock_base_interface, mock_concrete_interface, mock_cast_to_concrete):
        """Test wrapper supporting method chaining if methods return something."""
        mock_concrete_interface.GetSomething = Mock(return_value=mock_concrete_interface)

        wrapper = LCMObjectWrapper(mock_base_interface)
        result = wrapper.GetSomething()
        # Result should be the mock_concrete_interface (which also wraps same type)
        assert result == mock_concrete_interface


# =============================================================================
# TESTS FOR lcm_object / AsICmObject (issue #199)
# =============================================================================


class TestLCMObjectWrapperLcmObject:
    """Test the public `lcm_object` accessor for external casting."""

    def test_lcm_object_returns_exact_stored_object(self, mock_base_interface, mock_cast_to_concrete):
        """lcm_object must return the exact object passed to __init__ (the raw _obj)."""
        wrapper = LCMObjectWrapper(mock_base_interface)
        assert wrapper.lcm_object is mock_base_interface

    def test_lcm_object_is_not_the_concrete_cast(self, mock_base_interface, mock_concrete_interface, mock_cast_to_concrete):
        """lcm_object should return the base object, not the concrete cast."""
        wrapper = LCMObjectWrapper(mock_base_interface)
        assert wrapper.lcm_object is not mock_concrete_interface

    def test_lcm_object_is_read_only(self, wrapped_object):
        """lcm_object should be a read-only property."""
        with pytest.raises(AttributeError):
            wrapped_object.lcm_object = "something else"

    def test_lcm_object_none_when_obj_is_none(self, monkeypatch):
        """If the wrapper was constructed with None, lcm_object reflects that."""
        monkeypatch.setattr("flexlibs2.code.Shared.wrapper_base.cast_to_concrete", lambda obj: obj)
        wrapper = LCMObjectWrapper(None)
        assert wrapper.lcm_object is None


class TestLCMObjectWrapperAsICmObject:
    """Test the AsICmObject() convenience cast method."""

    def test_as_icmobject_calls_icmobject_cast(self, mock_base_interface, mock_cast_to_concrete, monkeypatch):
        """AsICmObject() should cast lcm_object via ICmObject and return the result."""
        sentinel = Mock(name="ICmObject-cast-result")
        fake_icmobject_ctor = Mock(return_value=sentinel)

        # SIL.LCModel may not be importable in this environment; provide a fake module.
        fake_module = MagicMock()
        fake_module.ICmObject = fake_icmobject_ctor
        monkeypatch.setitem(sys.modules, "SIL.LCModel", fake_module)

        wrapper = LCMObjectWrapper(mock_base_interface)
        result = wrapper.AsICmObject()

        fake_icmobject_ctor.assert_called_once_with(mock_base_interface)
        assert result is sentinel

    def test_as_icmobject_raises_fp_null_parameter_error_when_obj_is_none(self, monkeypatch):
        """AsICmObject() must raise FP_NullParameterError (not a raw TypeError) when there is
        no underlying LCM object to cast."""
        monkeypatch.setattr("flexlibs2.code.Shared.wrapper_base.cast_to_concrete", lambda obj: obj)

        from flexlibs2.code.FLExProject import FP_NullParameterError

        wrapper = LCMObjectWrapper(None)

        with pytest.raises(FP_NullParameterError):
            wrapper.AsICmObject()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
