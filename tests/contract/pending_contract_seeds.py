#
#   pending_contract_seeds.py
#
#   Anticipatory LCM dependency seeds for the contract extractor.
#
#   Not part of flexicon/code -- never imported at runtime. Purely a
#   parseable-by-AST source file so extract_lcm_contract.py's existing
#   AST walk can pick up type/member dependencies that flexicon/code does
#   not use *yet*, but is specified to use imminently (spec.md
#   write-path-transactions, tasks.md item B1).
#
#   Why this exists: tasks.md item CB ("Contract-baseline extension ...
#   Must land before B1") requires liblcm_baseline.json to cover
#   UndoableUnitOfWorkHelper / NonUndoableUnitOfWorkHelper / IActionHandler
#   *before* transaction.py is rewritten to use them. Until B1 lands, no
#   file in flexicon/code imports these types, so the AST extractor has
#   nothing organic to find. Hand-editing snapshots/expected_contract.json
#   directly would silently diverge from what extract_lcm_contract.py
#   produces on the next run (the exact kind of drift this suite exists to
#   catch). This file keeps the seed inside the same AST-based mechanism
#   instead of a parallel one: extract_contract() scans it in addition to
#   flexicon/code (see PENDING_SEEDS_PATH in extract_lcm_contract.py).
#
#   Delete this file's IActionHandler/UndoableUnitOfWorkHelper/
#   NonUndoableUnitOfWorkHelper section once transaction.py (B1) imports
#   and uses them for real -- at that point the dependency becomes organic
#   and this file would only be recording a duplicate.
#
#   Platform: Python 3.8+
#   Copyright 2025
#

#
#   NOTE ON STYLE: extract_lcm_contract.py's AST visitor only tracks
#   attribute/call access of the literal form ``TypeName.member`` where
#   ``TypeName`` is itself the imported LCM name (see LCMContractVisitor.
#   visit_Attribute/visit_Call -- it checks ``node.value.id in
#   self.lcm_names``, not usage through an intermediate local variable).
#   That is the same convention every other flexicon/code file relies on
#   for static-style entries (e.g. ``TsStringUtils.MakeString``), so this
#   seed file follows it even though ``IActionHandler.BeginUndoTask(...)``
#   is not literally how instance calls read in real code. The point here
#   is purely to register the member name with the extractor, not to be
#   executable.
#

from SIL.LCModel.Infrastructure import UndoableUnitOfWorkHelper, NonUndoableUnitOfWorkHelper
from SIL.LCModel.Core.KernelInterfaces import IActionHandler

# Mirrors the liblcm nesting idiom tasks.md B1 specifies verbatim:
# ``if actionHandler.CurrentDepth > 0: task() else: Do(...)``, plus the
# undo/redo/mark surface B3 and A3 build on.
IActionHandler.CurrentDepth
IActionHandler.BeginUndoTask("undo text", "redo text")
IActionHandler.EndUndoTask()
IActionHandler.CanUndo()
IActionHandler.CanRedo()
IActionHandler.Undo()
IActionHandler.Redo()
IActionHandler.Rollback(0)
IActionHandler.Mark()
IActionHandler.DiscardToMark(0)
IActionHandler.CollapseToMark(0, "undo text", "redo text")

# UndoableUnitOfWorkHelper: Dispose (IDisposable). RollBack is deliberately
# NOT seeded here -- it is a write-only property ({private get; set;}, see
# tasks.md O1) that the plain dir()-based member-name check in
# generate_lcm_snapshot.py cannot see under its bare name (only as
# ``set_RollBack``). Seeding it here would produce a permanent false-positive
# "missing property" in the generic member_checks/compare_contracts path.
# It is verified instead, deep-reflection style, by
# TestTransactionLayerContract.test_undoable_unit_of_work_helper_shape via
# ``reflected_properties`` -- see generate_lcm_snapshot._introspect_signatures.
UndoableUnitOfWorkHelper.Dispose()

# NonUndoableUnitOfWorkHelper: same RollBack/Dispose disposal contract.
NonUndoableUnitOfWorkHelper.Dispose()
