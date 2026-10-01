#
#   rule_feature.py
#
#   Class: RuleFeature
#          Wrapper for phonological rule-feature objects providing unified
#          interface access to the possibility name and its ItemRA target.
#          Class: RuleFeatureCollection
#          Smart collection for rule features with name/item access.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

"""
Wrapper classes for phonological rule features.

This module provides RuleFeature, a wrapper class that transparently handles
the single concrete type behind phonological rule features:

- IPhPhonRuleFeat: Implements ICmPossibility and declares exactly one
  property, ItemRA (an ICmObject that is an IMoInflClass or another
  ICmPossibility). There is no FeatureStructureRA on this interface.

Problem:
    ReqRuleFeatsRC / ExclRuleFeatsRC on IPhSegRuleRHS are typed reference
    collections of IPhPhonRuleFeat. A caller asking "what blocks this rule"
    gets objects whose name is their own possibility name, while the thing
    each feature constrains hides behind the polymorphic ItemRA link.

Solution:
    RuleFeature wrapper provides:
    - Simple properties for the feature name and its ItemRA target
    - item_name for the target's name without assuming the target's type
    - RuleFeatureCollection with names/items for one-call access to strings

Example::

    from flexicon import FLExProject

    project = FLExProject()
    project.OpenProject("morphboundary", writeEnabled=False)
    try:
        for rule in project.PhonRules.GetAll():
            for feat in rule.required_rule_features:
                print(f"{feat.name} constrains {feat.item_name}")
    finally:
        project.CloseProject()
"""

import logging

from ..Shared.smart_collection import SmartCollection
from ..Shared.string_utils import best_analysis_text
from ..Shared.wrapper_base import LCMObjectWrapper
from ..lcm_casting import cast_to_concrete

logger = logging.getLogger(__name__)


class RuleFeature(LCMObjectWrapper):
    """
    Wrapper for phonological rule-feature objects.

    Wraps one IPhPhonRuleFeat, which implements ICmPossibility and declares
    exactly one property, ItemRA. The feature's name is its own possibility
    name; ItemRA is the thing it constrains and is polymorphic (IMoInflClass
    or another ICmPossibility), so item is returned uncast and item_name
    reads the target's Name without assuming its type.

    Attributes:
        _obj: The base interface object (IPhPhonRuleFeat).
        _concrete: The concrete type object (IPhPhonRuleFeat).

    Example::

        for feat in rule.required_rule_features:
            print(feat.name)
            print(feat.item_name)

    Notes:
        - IPhPhonRuleFeat has no FeatureStructureRA; nothing here references
          it.
        - Every read goes through self._concrete (C10).
    """

    def __init__(self, lcm_feature):
        """
        Initialize RuleFeature wrapper with a rule-feature object.

        Args:
            lcm_feature: An IPhPhonRuleFeat object, typically from a rule's
                ReqRuleFeatsRC / ExclRuleFeatsRC.

        Example::

            feat = RuleFeature(raw_feat)
        """
        super().__init__(lcm_feature)

    @property
    def name(self) -> str:
        """
        Get the rule feature's own possibility name.

        Returns:
            str: The name text, or empty string if not set.

        Example::

            print(f"Feature: {feat.name}")

        Notes:
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
    def item(self):
        """
        Get the object this rule feature constrains.

        Returns:
            The ItemRA target uncast (an IMoInflClass or another
            ICmPossibility), or None when unset.

        Example::

            target = feat.item

        Notes:
            - Returned uncast on purpose: the LCM collection is already
              typed and casting would only cost the caller the object.
        """
        try:
            return getattr(self._concrete, "ItemRA", None)
        except Exception:
            logger.debug("item: failed to read ItemRA", exc_info=True)
            return None

    @property
    def item_name(self) -> str:
        """
        Get the name of the object this rule feature constrains.

        Returns:
            str: The target's name text, or empty string when there is no
                target or it has no name.

        Example::

            print(f"Constrains: {feat.item_name}")

        Notes:
            - Makes no assumption about the target's type: it reads Name
              through best_analysis_text on whatever ItemRA turns out to
              be (IMoInflClass or ICmPossibility).
            - ItemRA is typed ICmObject, so the narrowed proxy exposes no
              Name until it is cast: this read goes through
              cast_to_concrete first (C10). The item property itself stays
              uncast; only the name lookup casts.
        """
        try:
            target = self.item
            if target is None:
                return ""
            concrete = cast_to_concrete(target)
            return best_analysis_text(getattr(concrete, "Name", None))
        except Exception:
            return ""


class RuleFeatureCollection(SmartCollection):
    """
    Smart collection for phonological rule features.

    Manages collections of RuleFeature wrapper objects with type-aware
    display and filtering capabilities.

    Attributes:
        _items: List of RuleFeature wrapper objects

    Example::

        feats = rule.required_rule_features
        print(feats.names)
    """

    def __init__(self, items=None):
        """
        Initialize a RuleFeatureCollection.

        Args:
            items: Iterable of RuleFeature objects, or None for empty.

        Example::

            collection = RuleFeatureCollection()
            collection = RuleFeatureCollection([feat1, feat2])
        """
        super().__init__(items)

    @property
    def names(self) -> list:
        """
        Get the name of every rule feature in the collection.

        Returns:
            list[str]: One name per feature, in collection order.

        Example::

            print(feats.names)
        """
        return [feat.name for feat in self._items]

    @property
    def items(self) -> list:
        """
        Get the ItemRA target of every rule feature in the collection.

        Returns:
            list: The uncast ItemRA targets, in collection order. Entries
                may be None where a feature has no target set.

        Example::

            for target in feats.items:
                print(target)
        """
        return [feat.item for feat in self._items]

    def filter(self, name_contains=None, where=None):
        """
        Filter the collection by feature name.

        Args:
            name_contains (str, optional): Filter to features whose name
                contains this string (case-sensitive).
            where (callable, optional): Custom predicate function. If
                provided, other criteria are ignored.

        Returns:
            RuleFeatureCollection: New collection with filtered items.

        Example::

            req = feats.filter(name_contains='voice')

        Notes:
            - Returns new collection (doesn't modify original)
            - Use where() for complex custom filtering
        """
        if where is not None:
            filtered = [item for item in self._items if where(item)]
            return RuleFeatureCollection(filtered)

        filtered = self._items

        if name_contains is not None:
            filtered = [feat for feat in filtered if name_contains in (feat.name or "")]

        return RuleFeatureCollection(filtered)

    def where(self, predicate):
        """
        Filter using a custom predicate function.

        Args:
            predicate (callable): Function that takes a RuleFeature and
                returns True to include it in the result.

        Returns:
            RuleFeatureCollection: New collection with items matching the
                predicate.

        Example::

            infl = feats.where(lambda f: f.item is not None)
        """
        filtered = [feat for feat in self._items if predicate(feat)]
        return RuleFeatureCollection(filtered)
