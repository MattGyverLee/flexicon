#
#   __init__.py
#
#   Grammar module exports
#
#   Copyright 2025
#

from .affix_template import AffixTemplate
from .affix_template_collection import AffixTemplateCollection
from .compound_rule import CompoundRule
from .compound_rule_collection import CompoundRuleCollection

# Don't import MorphRuleOperations here - it requires FLExProject which has
# heavy dependencies. Users should import it directly when needed.
# from .MorphRuleOperations import MorphRuleOperations

__all__ = [
    "AffixTemplate",
    "AffixTemplateCollection",
    "CompoundRule",
    "CompoundRuleCollection",
    # 'MorphRuleOperations',  # Import directly when needed
]
