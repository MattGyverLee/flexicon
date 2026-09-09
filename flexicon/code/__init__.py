# Flexicon Code Module
#
# Exports the PythonicWrapper for suffix-free property access, and
# `cast_to_concrete` -- the public escape hatch for polymorphic LCM
# collections and direct-LCM work (see #271). The canonical import path is
# `from flexicon import cast_to_concrete`; this re-export keeps
# `flexicon.code.cast_to_concrete` working alongside the long-standing
# `flexicon.code.lcm_casting.cast_to_concrete`.

from .PythonicWrapper import wrap, unwrap, p, PythonicWrapper
from .lcm_casting import cast_to_concrete

__all__ = ["wrap", "unwrap", "p", "PythonicWrapper", "cast_to_concrete"]
