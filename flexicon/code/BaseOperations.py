#
#   BaseOperations.py
#
#   Class: BaseOperations
#          Base class for all FLEx operation classes.
#          Provides reordering functionality for owning sequences.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

# --- Imports ------------------------------------------------------------------

from typing import Any

from .exceptions import (
    FP_ReadOnlyError,
    FP_NullParameterError,
    FP_ParameterError,
)
from .Shared.lcm_constants import OWNING_SEQUENCE_SUFFIX, FEATURE_STRUC_OWNER_TABLE

# --- Constants ---------------------------------------------------------------


class EnumerableWrapper:
    """
    Wraps C# IEnumerable to provide Pythonic interface.

    C# IEnumerable collections don't support indexing or .Count in Python.
    This wrapper makes them behave like Python sequences while maintaining
    lazy evaluation when possible.

    Provides:
      - .Count property (returns count of items)
      - Indexing support ([0], [1:3], etc.)
      - Iteration support (for item in collection)
      - Contains support (x in collection)

    Usage::

        items = GetWordforms()  # Returns IEnumerable
        count = items.Count      # ✅ Works (Pythonic!)
        first = items[0]         # ✅ Works (indexing)
        if "word" in items:      # ✅ Works (contains)
            ...
    """

    def __init__(self, enumerable):
        """Wrap an IEnumerable collection.

        Args:
            enumerable: A C# IEnumerable object from LibLCM
        """
        self._enumerable = enumerable
        self._cached_list = None

    def _ensure_list(self):
        """Convert to list on first access (lazy evaluation)."""
        if self._cached_list is None:
            self._cached_list = list(self._enumerable)
        return self._cached_list

    @property
    def Count(self):
        """Get count of items in the collection (Pythonic for C# .Count).

        Returns:
            int: Number of items in the enumerable.

        Example::

            items = project.GetWordforms()
            count = items.Count  # Returns number of wordforms
        """
        return len(self._ensure_list())

    def __len__(self):
        """Support len() function."""
        return self.Count

    def __getitem__(self, index):
        """Support indexing and slicing.

        Args:
            index: Integer index or slice object

        Returns:
            Item at index or slice of items

        Example::

            items = project.GetWordforms()
            first = items[0]      # First item
            last = items[-1]      # Last item
            some = items[1:5]     # Slice
        """
        return self._ensure_list()[index]

    def __iter__(self):
        """Support iteration (for item in collection)."""
        return iter(self._ensure_list())

    def __contains__(self, item):
        """Support 'in' operator.

        Example::

            items = project.GetWordforms()
            if my_word in items:
                ...
        """
        return item in self._ensure_list()

    def __repr__(self):
        """String representation."""
        return f"EnumerableWrapper({self._enumerable})"


def _needs_enumerable_wrap(result):
    """
    Decide whether `result` needs to be wrapped in EnumerableWrapper.

    Historically this only checked for raw C# IEnumerable objects (those
    exposing `GetEnumerator`). That missed two common return shapes used
    throughout the Operations classes:

    - `self.project.ObjectsIn(...)`, which already calls Python's
      built-in `iter()` on the underlying C# enumerable before returning
      it. The resulting object exposes `__next__`/`__iter__` but *not*
      `GetEnumerator`, so it slipped past the old check untouched.
    - Generator-function GetAll()/GetAnalyses() implementations (using
      `yield`), which return a plain Python generator object -- also has
      `__next__` but no `GetEnumerator`, and is not subscriptable and
      has no `len()`.

    Both shapes produced the exact bug in issue #201: callers got back a
    bare iterator/generator that looked list-like but raised
    `TypeError` on `entries[0]` or `len(entries)`.

    Anything that already supports both indexing and `len()` (plain
    lists, tuples, existing EnumerableWrapper/SmartCollection instances,
    etc.) is left alone -- there's nothing to fix and no need to
    re-wrap it.

    Args:
        result: The raw value returned by the wrapped method.

    Returns:
        bool: True if `result` should be wrapped in EnumerableWrapper.
    """
    if result is None:
        return False
    if isinstance(result, EnumerableWrapper):
        return False
    # Raw C# IEnumerable (pythonnet objects exposing GetEnumerator).
    if hasattr(result, "GetEnumerator"):
        return True
    # Plain Python iterator/generator (has __next__) that does not
    # already behave like a sequence (no __len__ + __getitem__ pair).
    # This covers both `iter(repo.AllInstances())` (from ObjectsIn())
    # and generator-function bodies using `yield`.
    if hasattr(result, "__next__"):
        already_sequence = hasattr(result, "__len__") and hasattr(result, "__getitem__")
        if not already_sequence:
            return True
    return False


class wrap_enumerable:
    """
    Descriptor to automatically wrap IEnumerable/iterator return values.

    Wraps methods that return C# IEnumerable collections -- or plain
    Python iterators/generators built on top of them (e.g. via
    `self.project.ObjectsIn(...)` or a `yield`-based method body) -- to
    make them Pythonic with `.Count`, `len()`, and indexing support.

    Must be a descriptor to properly delegate to OperationsMethod's __get__,
    ensuring the descriptor protocol works correctly when stacked decorators
    are used.

    Usage::

        class MyOperations(BaseOperations):
            @wrap_enumerable
            @OperationsMethod
            def GetAll(self):
                return self.project.GetAllItems()

            # Now users can do:
            items = GetAll(project)
            count = items.Count      # Works!
            first = items[0]         # Works!
            length = len(items)      # Works!

    Behavioral collection contract:
        Every ``GetAll`` in flexicon returns a **behavioral collection**: you
        can always loop it, ``len()`` it, index into it, and re-iterate it.
        The concrete return type -- ``EnumerableWrapper`` (this decorator, for
        large/lazily-materialized results), a plain ``list`` (already a
        sequence, so wrapping is a no-op), or a ``SmartCollection`` subtype
        (adds ``.filter()``/type-breakdown display on top of the same
        sequence guarantees) -- is an implementation detail callers never
        have to branch on. See ``docs/getall-contract.md`` for the full
        guarantee and rationale.
    """

    def __init__(self, func):
        """Store the inner function/method."""
        self.func = func
        self.__doc__ = getattr(func, '__doc__', '')
        self.__name__ = getattr(func, '__name__', 'wrapped')

    def __get__(self, obj, objtype=None):
        """
        Descriptor protocol: delegate to inner descriptor if present.

        If the wrapped function is a descriptor (like OperationsMethod),
        call its __get__ to get the proper bound method, then wrap the
        result to handle IEnumerable returns.
        """
        # If the inner function is a descriptor, get its bound method
        if hasattr(self.func, '__get__'):
            inner_method = self.func.__get__(obj, objtype)
        else:
            # Not a descriptor, just bind normally
            if obj is None:
                inner_method = self.func
            else:
                inner_method = self.func.__get__(obj, objtype)

        # Return a wrapper that will wrap the result
        def wrapped_method(*args, **kwargs):
            result = inner_method(*args, **kwargs)
            if _needs_enumerable_wrap(result):
                return EnumerableWrapper(result)
            return result

        return wrapped_method

    def __call__(self, *args, **kwargs):
        """
        Direct call support (when decorator is applied to a function, not a method).

        This is called when the wrapped method is invoked without going through
        the descriptor protocol (rare, but needed for some edge cases).
        """
        result = self.func(*args, **kwargs)
        if _needs_enumerable_wrap(result):
            return EnumerableWrapper(result)
        return result

class OperationsMethod:
    """
    Descriptor enabling methods to work as both class and instance methods.

    Allows calling operation methods in two ways:
      - Class level (no instantiation): POSOperations.GetAll(project)
      - Instance level (traditional): POSOperations(project).GetAll()

    Both patterns work identically and are equally valid. The descriptor
    automatically handles instantiation when called at class level.

    Usage::

        class POSOperations(BaseOperations):
            @wrap_enumerable
            @OperationsMethod
            def GetAll(self):
                # Implementation
                return self.project.GetAllPOS()

        # Both work:
        pos_list = POSOperations.GetAll(project)  # Class-level
        pos_list = POSOperations(project).GetAll()  # Instance-level
    """

    def __init__(self, func):
        """Store the method being decorated."""
        self.func = func
        self.__doc__ = func.__doc__
        self.__name__ = func.__name__

    def __get__(self, obj, objtype=None):
        """
        Descriptor protocol: handle both class and instance access.

        When called on the class (POSOperations.GetAll(project)):
            - Returns a function that takes project as first argument
            - Automatically instantiates the class and calls the method

        When called on an instance (POSOperations(project).GetAll()):
            - Returns a bound method as normal

        Defensive casting: Unwraps nested OperationsMethod objects to prevent
        'OperationsMethod' object is not callable errors from bad decorator order.
        """
        # Defensive casting: unwrap if self.func is a nested OperationsMethod
        func = self.func
        while isinstance(func, OperationsMethod):
            func = func.func

        if obj is None:
            # Called on class: POSOperations.GetAll(project)
            def class_method(project, *args, **kwargs):
                """Automatically instantiate and call the method."""
                instance = objtype(project)
                return func(instance, *args, **kwargs)

            return class_method
        else:
            # Called on instance: POSOperations(project).GetAll()
            return func.__get__(obj, objtype)


def _apply_props_loop(item, props, target_ws_by_id, fill_gaps=False,
                      ws_map=None, _default_ws_getter=None, _ts_string_utils=None):
    """Pure loop body of ApplySyncableProperties. No project handle required.

    Extracted so that unit tests (T-S3a) can call this directly with fabricated
    dicts and fake item objects, without needing a live self.project.

    Args:
        item: LCM object to update.
        props: dict of {prop_name: value} from GetSyncableProperties.
        target_ws_by_id: dict of {ws_id: handle} for multistring WS resolution.
            Must already be built from self.project.WritingSystems.GetAll() by
            the caller (ApplySyncableProperties); this helper makes no runtime
            lookups itself.
        fill_gaps: if True, skip non-empty target values (fill-gaps / merge mode).
            For multistring: a WS alt is skipped when existing.RunCount > 0
            (RunCount directly reflects text-run presence; equivalent but weaker
            alternative: (existing.Text or "").strip()).
            For plain str: skipped when getattr(item, prop_name) is non-empty.
            For bool/int: ALWAYS skipped when fill_gaps=True — stored False/0 is
            a real choice, never overwrite.
        ws_map: Optional source->target WS Id mapping dict.
        _default_ws_getter: Callable returning the default analysis WS handle,
            used only for ITsString fallback on plain str properties.
        _ts_string_utils: The imported TsStringUtils class, passed in to avoid
            a re-import inside the pure helper.
    """
    for prop_name, value in props.items():
        if value is None:
            continue
        if isinstance(value, dict):
            # Multi-WS multistring property.
            prop_obj = getattr(item, prop_name, None)
            if prop_obj is None:
                continue
            for src_ws_id, text in value.items():
                if not text:
                    continue
                tgt_ws_id = (
                    ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id
                )
                tgt_handle = target_ws_by_id.get(tgt_ws_id)
                if tgt_handle is None:
                    # Target lacks this WS; skip silently. Callers wanting
                    # strict mapping should pre-validate ws_map.
                    continue
                if fill_gaps:
                    existing = prop_obj.get_String(tgt_handle)
                    # Guard: treat whitespace-only alts as empty so a valid source
                    # fill is not blocked by a phantom-whitespace alt (RunCount>0
                    # but no real text). Mirrors the plain-str branch below.
                    if (existing.Text or "").strip():
                        continue  # target alt non-empty: target wins
                if _ts_string_utils is not None:
                    prop_obj.set_String(
                        tgt_handle, _ts_string_utils.MakeString(text, tgt_handle)
                    )
        elif isinstance(value, str):
            # Plain string attribute. LCM properties come in three
            # shapes from the perspective of "assign a Python str":
            # (1) plain string properties (works directly with setattr);
            # (2) ITsString properties (need TsStringUtils wrapping);
            # (3) object-reference properties typed as some LCM
            #     interface (e.g. IMoMorphSynAnalysis) — these can't
            #     be assigned a string at all; they need a cross-project
            #     object lookup which lives outside this dict-driven
            #     sync path.
            # We handle (1) via the bare setattr, (2) via the ITsString
            # fallback, and (3) by skipping silently — the caller is
            # responsible for object-reference wiring.
            if not hasattr(item, prop_name):
                continue
            if fill_gaps:
                current = getattr(item, prop_name, None)
                if current is not None and str(current).strip():
                    continue  # target str non-empty: target wins
            try:
                setattr(item, prop_name, value)
            except TypeError as exc:
                msg = str(exc)
                if "ITsString" in msg:
                    try:
                        default_ws = _default_ws_getter() if _default_ws_getter else None
                        if default_ws is not None and _ts_string_utils is not None:
                            setattr(
                                item,
                                prop_name,
                                _ts_string_utils.MakeString(value, default_ws),
                            )
                    except Exception:
                        # If wrapping also fails, skip the property
                        # silently — the sync framework treats this as
                        # a soft incompatibility rather than a hard error.
                        continue
                elif "cannot be converted to SIL.LCModel." in msg:
                    # Object-reference property — case (3). Skip; the
                    # caller wires cross-project references explicitly
                    # via GUID lookup (e.g. target.MSA.CreateInflAff).
                    continue
                else:
                    raise
        elif isinstance(value, bool):
            # Bool flag (e.g. Disabled, Final). stored False is a deliberate
            # choice; always skip in fill-gaps mode.
            if fill_gaps:
                continue
            if hasattr(item, prop_name):
                try:
                    setattr(item, prop_name, value)
                except (TypeError, AttributeError):
                    continue
        elif isinstance(value, int):
            # Pure int attribute (e.g. HomographNumber). Apply the same
            # non-empty-current guard as the plain-str branch: in fill-gaps
            # mode only skip when the target already has a non-zero/non-None
            # value. bool is checked first so True/False never reaches here.
            if fill_gaps:
                current = getattr(item, prop_name, None)
                if current is not None and current != 0:
                    continue
            if hasattr(item, prop_name):
                try:
                    setattr(item, prop_name, value)
                except (TypeError, AttributeError):
                    continue
        else:
            # Unknown shape; subclasses override to handle.
            continue


class BaseOperations:
    """
    Base class for all FLEx operation classes.

    Provides common reordering functionality that works with any FLEx
    Owning Sequence (OS) collection. Subclasses must override _GetSequence()
    to specify which OS property to reorder.

    All 43 operation classes inherit from this base class, gaining access
    to 7 reordering methods without code duplication.

    Reordering Safety:
        - Reordering is SAFE - preserves all data connections
        - GUIDs, references, properties, and children remain intact
        - Only changes the sequence position (index)
        - Uses safe Clear/Add pattern for all operations

    Linguistic Significance:
        - Reordering changes linguistic meaning and behavior
        - Senses: First sense is primary
        - Allomorphs: First matching allomorph selected by parser
        - Examples: Order may reflect preference or pedagogy
        - Reorder only when linguistically justified

    Usage::

        from flexicon import FLExProject

        project = FLExProject()
        project.OpenProject("MyProject", writeEnabled=True)

        entry = list(project.LexiconAllEntries())[0]

        # All operation classes have these methods:

        # Sort senses alphabetically
        project.Senses.Sort(entry,
                           key_func=lambda s: project.Senses.GetGloss(s))

        # Move sense up one position
        sense = entry.SensesOS[2]
        project.Senses.MoveUp(entry, sense)

        # Move allomorph to specific index
        allo = entry.AlternateFormsOS[3]
        project.Allomorphs.MoveToIndex(entry, allo, 0)

        # Swap two examples
        ex1 = sense.ExamplesOS[0]
        ex2 = sense.ExamplesOS[1]
        project.Examples.Swap(ex1, ex2)

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize BaseOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        self.project = project

    # ========== REORDERING METHODS ==========

    @OperationsMethod
    def Sort(self, parent_or_hvo, key_func=None, reverse=False):
        """
        Sort items in an owning sequence using a custom key function.

        This method reorders all items in the sequence according to a
        sorting criterion. The sort is stable and uses Python's built-in
        sort algorithm.

        Args:
            parent_or_hvo: The parent object or HVO containing the sequence.
            key_func: Optional function(item) -> comparable_value.
                     If None, uses natural ordering (may fail if items
                     don't support comparison).
            reverse: If True, sort in descending order. Default False.

        Returns:
            int: Number of items sorted (length of sequence).

        Raises:
            TypeError: If key_func is None and items don't support comparison.
            Exception: If any error occurs during sorting.

        Example:
            >>> # Sort allomorphs by form length
            >>> project.Allomorphs.Sort(entry,
            ...     key_func=lambda a: len(project.Allomorphs.GetForm(a)))
            3

            >>> # Sort senses alphabetically by gloss
            >>> project.Senses.Sort(entry,
            ...     key_func=lambda s: project.Senses.GetGloss(s))
            5

            >>> # Sort in reverse order (most complex first)
            >>> def complexity(allo):
            ...     env = project.Allomorphs.GetEnvironment(allo)
            ...     return len(str(env)) if env else 0
            >>> project.Allomorphs.Sort(entry,
            ...     key_func=complexity,
            ...     reverse=True)
            3

            >>> # Sort examples by length (shortest first)
            >>> project.Examples.Sort(sense,
            ...     key_func=lambda ex: len(project.Examples.GetText(ex)))
            4

        Notes:
            - Returns count even if order unchanged
            - Empty sequence returns 0
            - Uses safe Clear/Add pattern - preserves all data
            - Sort is stable (equal elements maintain relative order)
            - If key_func raises exception, sort fails

        Linguistic Warning:
            Reordering changes linguistic behavior:
            - Senses: Primary sense is first
            - Allomorphs: Parser tries in sequence order
            - Examples: Order may be pedagogically significant

        See Also:
            MoveToIndex, MoveUp, MoveDown
        """
        parent = self._GetObject(parent_or_hvo)
        sequence = self._GetSequence(parent)

        # Get all items with their indices
        count = sequence.Count
        if count <= 1:
            return count  # Nothing to sort

        items_with_indices = [(i, sequence[i]) for i in range(count)]

        # Sort based on key function or natural order
        if key_func:
            items_with_indices.sort(key=lambda x: key_func(x[1]), reverse=reverse)
        else:
            items_with_indices.sort(key=lambda x: x[1], reverse=reverse)

        # Apply new order using MoveTo. Bracketed as ONE transaction: a sort
        # issues up to `count` MoveTo calls, and a failure partway through
        # leaves the sequence in a half-sorted order that is neither the old
        # nor the new one. This is exactly the multi-mutation case
        # _TransactionCM exists for.
        with self._TransactionCM("Sort sequence"):
            # We need to move items from their current position to their target position
            # Process from end to beginning to avoid index shifting issues
            for target_index in range(count):
                # Find where the item that should be at target_index currently is
                current_index = target_index
                for j in range(target_index, count):
                    if sequence[j] == items_with_indices[target_index][1]:
                        current_index = j
                        break

                # Move it to the target position if not already there
                if current_index != target_index:
                    sequence.MoveTo(current_index, current_index, sequence, target_index)

            return count

    @OperationsMethod
    def MoveUp(self, parent_or_hvo, item, positions=1):
        """
        Move an item up (toward index 0) by specified number of positions.

        Moves an item toward the beginning of the sequence. If the requested
        number of positions would move past index 0, the item is clamped at
        index 0 (no error raised).

        Args:
            parent_or_hvo: The parent object or HVO containing the sequence.
            item: The item to move (object, not HVO).
            positions: Number of positions to move up. Must be positive.
                      Default is 1.

        Returns:
            int: Actual number of positions moved. May be less than requested
                 if item reaches index 0. Returns 0 if already at index 0.

        Raises:
            ValueError: If item not found in sequence.
            ValueError: If positions is negative or zero.

        Example:
            >>> # Move sense up one position (e.g., from index 3 to 2)
            >>> sense = entry.SensesOS[3]
            >>> moved = project.Senses.MoveUp(entry, sense)
            >>> print(f"Moved {moved} positions")
            Moved 1 positions

            >>> # Move allomorph to top (up 5 positions)
            >>> allo = entry.AlternateFormsOS[5]
            >>> moved = project.Allomorphs.MoveUp(entry, allo, positions=5)
            >>> print(f"Now at index {list(entry.AlternateFormsOS).index(allo)}")
            Now at index 0

            >>> # Try to move past start (clamped at 0)
            >>> example = sense.ExamplesOS[1]
            >>> moved = project.Examples.MoveUp(sense, example, positions=10)
            >>> print(f"Actually moved {moved} positions")
            Actually moved 1 positions

            >>> # Already at start - no movement
            >>> first = entry.SensesOS[0]
            >>> moved = project.Senses.MoveUp(entry, first)
            >>> print(f"Moved {moved} positions")
            Moved 0 positions

        Notes:
            - Auto-clamps at boundary (no IndexError)
            - Returns actual movement for UI feedback
            - Item stays at current position if already at top
            - Uses safe Clear/Add pattern
            - Perfect for "Move Up" buttons in UI

        Linguistic Warning:
            Moving items up increases their priority:
            - Senses: Moving to index 0 makes it primary
            - Allomorphs: Moving up means parser tries earlier

        See Also:
            MoveDown, MoveToIndex, MoveBefore
        """
        self._EnsureWriteEnabled()

        if positions <= 0:
            raise ValueError("positions must be positive integer")

        parent = self._GetObject(parent_or_hvo)
        sequence = self._GetSequence(parent)

        # Find current index
        current_index = -1
        for i in range(sequence.Count):
            if sequence[i] == item:
                current_index = i
                break

        if current_index == -1:
            raise ValueError("Item not found in sequence")

        # Already at top - no movement
        if current_index == 0:
            return 0

        # Calculate new index (clamped to 0)
        new_index = max(0, current_index - positions)
        actual_moved = current_index - new_index

        # Move using FLEx's MoveTo method
        # When moving backward (up), use target index directly
        if actual_moved > 0:
            with self._TransactionCM(f"Move item up {actual_moved} position(s)"):
                sequence.MoveTo(current_index, current_index, sequence, new_index)

        return actual_moved

    @OperationsMethod
    def MoveDown(self, parent_or_hvo, item, positions=1):
        """
        Move an item down (toward end) by specified number of positions.

        Moves an item toward the end of the sequence. If the requested
        number of positions would move past the end, the item is clamped
        at the last index (no error raised).

        Args:
            parent_or_hvo: The parent object or HVO containing the sequence.
            item: The item to move (object, not HVO).
            positions: Number of positions to move down. Must be positive.
                      Default is 1.

        Returns:
            int: Actual number of positions moved. May be less than requested
                 if item reaches last index. Returns 0 if already at end.

        Raises:
            ValueError: If item not found in sequence.
            ValueError: If positions is negative or zero.

        Example:
            >>> # Move sense down one position (e.g., from index 1 to 2)
            >>> sense = entry.SensesOS[1]
            >>> moved = project.Senses.MoveDown(entry, sense)
            >>> print(f"Moved {moved} positions")
            Moved 1 positions

            >>> # Demote primary sense significantly
            >>> primary = entry.SensesOS[0]
            >>> moved = project.Senses.MoveDown(entry, primary, positions=3)
            >>> print(f"Now at index {list(entry.SensesOS).index(primary)}")
            Now at index 3

            >>> # Try to move past end (clamped)
            >>> allo = entry.AlternateFormsOS[8]  # Count = 10
            >>> moved = project.Allomorphs.MoveDown(entry, allo, positions=5)
            >>> print(f"Actually moved {moved} positions")
            Actually moved 1 positions

            >>> # Already at end - no movement
            >>> last = entry.SensesOS[entry.SensesOS.Count - 1]
            >>> moved = project.Senses.MoveDown(entry, last)
            >>> print(f"Moved {moved} positions")
            Moved 0 positions

        Notes:
            - Auto-clamps at boundary (no IndexError)
            - Returns actual movement for UI feedback
            - Item stays at current position if already at end
            - Uses safe Clear/Add pattern
            - Perfect for "Move Down" buttons in UI

        Linguistic Warning:
            Moving items down decreases their priority:
            - Senses: Moving from index 0 demotes primary sense
            - Allomorphs: Moving down means parser tries later

        See Also:
            MoveUp, MoveToIndex, MoveAfter
        """
        self._EnsureWriteEnabled()

        if positions <= 0:
            raise ValueError("positions must be positive integer")

        parent = self._GetObject(parent_or_hvo)
        sequence = self._GetSequence(parent)

        # Find current index
        current_index = -1
        for i in range(sequence.Count):
            if sequence[i] == item:
                current_index = i
                break

        if current_index == -1:
            raise ValueError("Item not found in sequence")

        # Already at end - no movement
        max_index = sequence.Count - 1
        if current_index == max_index:
            return 0

        # Calculate new index (clamped to max)
        new_index = min(max_index, current_index + positions)
        actual_moved = new_index - current_index

        # Move using FLEx's MoveTo method
        # When moving forward (down), need to use new_index + 1 due to FLEx behavior
        if actual_moved > 0:
            with self._TransactionCM(f"Move item down {actual_moved} position(s)"):
                sequence.MoveTo(current_index, current_index, sequence, new_index + 1)

        return actual_moved

    @OperationsMethod
    def MoveToIndex(self, parent_or_hvo, item, new_index):
        """
        Move an item to a specific index position.

        Directly moves an item to the specified index. Other items are
        shifted accordingly. This is useful for absolute positioning.

        Args:
            parent_or_hvo: The parent object or HVO containing the sequence.
            item: The item to move (object, not HVO).
            new_index: Target index (0-based). Must be valid index for
                      current sequence length.

        Returns:
            bool: True if successful.

        Raises:
            ValueError: If item not found in sequence.
            IndexError: If new_index is out of range [0, count-1].

        Example:
            >>> # Make third sense the primary sense
            >>> third_sense = entry.SensesOS[2]
            >>> project.Senses.MoveToIndex(entry, third_sense, 0)
            True

            >>> # Move allomorph to end
            >>> allo = entry.AlternateFormsOS[1]
            >>> last_index = entry.AlternateFormsOS.Count - 1
            >>> project.Allomorphs.MoveToIndex(entry, allo, last_index)
            True

            >>> # Move example to middle position
            >>> ex = sense.ExamplesOS[0]
            >>> project.Examples.MoveToIndex(sense, ex, 2)
            True

        Notes:
            - Validates index before moving
            - Raises IndexError for out-of-range index
            - Moving to current index is allowed (no-op)
            - Uses safe Clear/Add pattern
            - Good for drag-and-drop UI implementation

        Linguistic Warning:
            Index 0 has special significance:
            - Senses: Index 0 is the primary sense
            - Allomorphs: Index 0 is the default form
            - Moving to index 0 changes linguistic priority

        See Also:
            MoveUp, MoveDown, MoveBefore, MoveAfter
        """
        self._EnsureWriteEnabled()

        parent = self._GetObject(parent_or_hvo)
        sequence = self._GetSequence(parent)

        # Find current index
        current_index = -1
        for i in range(sequence.Count):
            if sequence[i] == item:
                current_index = i
                break

        if current_index == -1:
            raise ValueError("Item not found in sequence")

        # Validate new index
        if new_index < 0 or new_index >= sequence.Count:
            raise IndexError(f"Index {new_index} out of range [0, {sequence.Count-1}]")

        # Move using FLEx's MoveTo method
        # Adjust destination index based on direction
        if current_index != new_index:
            with self._TransactionCM(f"Move item to index {new_index}"):
                if current_index < new_index:
                    # Moving forward - use new_index + 1
                    sequence.MoveTo(current_index, current_index, sequence, new_index + 1)
                else:
                    # Moving backward - use new_index directly
                    sequence.MoveTo(current_index, current_index, sequence, new_index)

        return True

    @OperationsMethod
    def MoveBefore(self, item_to_move, target_item):
        """
        Move an item to position immediately before another item.

        Positions item_to_move directly before target_item in the sequence.
        Both items must be in the same sequence (same parent). The parent
        is automatically determined by examining the items' Owner property.

        Args:
            item_to_move: The item to reposition (object, not HVO).
            target_item: The item before which to insert (object, not HVO).

        Returns:
            bool: True if successful.

        Raises:
            ValueError: If items not in same sequence or not found.

        Example:
            >>> # Move secondary sense to become primary
            >>> primary = entry.SensesOS[0]
            >>> secondary = entry.SensesOS[2]
            >>> project.Senses.MoveBefore(secondary, primary)
            True

            >>> # Move variant allomorph before default
            >>> default = entry.AlternateFormsOS[0]
            >>> variant = entry.AlternateFormsOS[3]
            >>> project.Allomorphs.MoveBefore(variant, default)
            True

        Notes:
            - Automatically finds common parent sequence
            - Both items must be in same owning sequence
            - Uses safe Clear/Add pattern
            - Perfect for drag-and-drop "insert before" operations
            - No parent_or_hvo parameter needed

        Linguistic Warning:
            Relative positioning changes processing order:
            - Allomorphs: Earlier forms tried first by parser
            - Senses: Earlier senses are more prominent

        See Also:
            MoveAfter, MoveToIndex, Swap
        """
        self._EnsureWriteEnabled()

        # Find which sequence contains both items
        sequence = self._FindCommonSequence(item_to_move, target_item)

        # Find indices of both items
        # Note: sequence from reflection may not support indexing, use enumeration
        move_index = -1
        target_index = -1
        index = 0
        for item in sequence:
            if item == item_to_move:
                move_index = index
            if item == target_item:
                target_index = index
            index += 1

        # Move using FLEx's MoveTo method
        if move_index != -1 and target_index != -1 and move_index != target_index:
            with self._TransactionCM("Move item before target"):
                if move_index < target_index:
                    # Moving forward - use target_index (will end up before target)
                    sequence.MoveTo(move_index, move_index, sequence, target_index)
                else:
                    # Moving backward - use target_index directly
                    sequence.MoveTo(move_index, move_index, sequence, target_index)

        return True

    @OperationsMethod
    def MoveAfter(self, item_to_move, target_item):
        """
        Move an item to position immediately after another item.

        Positions item_to_move directly after target_item in the sequence.
        Both items must be in the same sequence (same parent). The parent
        is automatically determined by examining the items' Owner property.

        Args:
            item_to_move: The item to reposition (object, not HVO).
            target_item: The item after which to insert (object, not HVO).

        Returns:
            bool: True if successful.

        Raises:
            ValueError: If items not in same sequence or not found.

        Example:
            >>> # Move primary sense to second position
            >>> primary = entry.SensesOS[0]
            >>> secondary = entry.SensesOS[1]
            >>> project.Senses.MoveAfter(primary, secondary)
            True

            >>> # Move variant allomorph after default
            >>> default = entry.AlternateFormsOS[0]
            >>> variant = entry.AlternateFormsOS[3]
            >>> project.Allomorphs.MoveAfter(variant, default)
            True

        Notes:
            - Automatically finds common parent sequence
            - Both items must be in same owning sequence
            - Uses safe Clear/Add pattern
            - Perfect for drag-and-drop "insert after" operations
            - No parent_or_hvo parameter needed

        Linguistic Warning:
            Relative positioning changes processing order:
            - Allomorphs: Later forms tried after earlier ones
            - Senses: Later senses are less prominent

        See Also:
            MoveBefore, MoveToIndex, Swap
        """
        self._EnsureWriteEnabled()

        # Find which sequence contains both items
        sequence = self._FindCommonSequence(item_to_move, target_item)

        # Find indices of both items
        # Note: sequence from reflection may not support indexing, use enumeration
        move_index = -1
        target_index = -1
        index = 0
        for item in sequence:
            if item == item_to_move:
                move_index = index
            if item == target_item:
                target_index = index
            index += 1

        # Move to position after target
        if move_index != -1 and target_index != -1 and move_index != target_index:
            with self._TransactionCM("Move item after target"):
                # When moving after, we want to end up at target_index + 1
                # If moving forward: use target_index + 1 (will insert after due to removal)
                # If moving backward: use target_index + 1 directly
                if move_index < target_index:
                    sequence.MoveTo(move_index, move_index, sequence, target_index + 1)
                else:
                    sequence.MoveTo(move_index, move_index, sequence, target_index + 1)

        return True

    @OperationsMethod
    def Swap(self, item1, item2):
        """
        Swap the positions of two items in a sequence.

        Exchanges the positions of two items. Both items must be in the
        same sequence (same parent). The parent is automatically determined
        by examining the items' Owner property.

        Args:
            item1: First item to swap (object, not HVO).
            item2: Second item to swap (object, not HVO).

        Returns:
            bool: True if successful.

        Raises:
            ValueError: If items not in same sequence or not found.

        Example:
            >>> # Swap first and second senses
            >>> sense1 = entry.SensesOS[0]
            >>> sense2 = entry.SensesOS[1]
            >>> project.Senses.Swap(sense1, sense2)
            True

            >>> # Swap allomorphs
            >>> allo1 = entry.AlternateFormsOS[0]
            >>> allo2 = entry.AlternateFormsOS[3]
            >>> project.Allomorphs.Swap(allo1, allo2)
            True

        Notes:
            - Automatically finds common parent sequence
            - Both items must be in same owning sequence
            - Swapping item with itself is allowed (no-op)
            - Uses safe Clear/Add pattern
            - Works for adjacent or non-adjacent items
            - No parent_or_hvo parameter needed

        Linguistic Warning:
            Swapping changes relative priority:
            - Swapping primary sense changes which is primary
            - Swapping allomorphs changes parser order

        See Also:
            MoveBefore, MoveAfter, MoveToIndex
        """
        # Find which sequence contains both items
        sequence = self._FindCommonSequence(item1, item2)

        # Find indices
        # Note: sequence from reflection may not support indexing, use enumeration
        idx1 = -1
        idx2 = -1
        index = 0
        for item in sequence:
            if item == item1:
                idx1 = index
            if item == item2:
                idx2 = index
            index += 1

        # Swap using MoveTo operations. Bracketed as ONE transaction: the swap
        # is a deliberate two-step MoveTo dance, and failing between the steps
        # leaves the sequence in an order that is neither the original nor the
        # swapped one.
        # Strategy: Move lower-index item after higher-index item, then move higher item to original position
        if idx1 != -1 and idx2 != -1 and idx1 != idx2:
            with self._TransactionCM("Swap items"):
                if idx1 < idx2:
                    # item1 is before item2
                    # Step 1: Move item1 to after item2 (this pushes item2 earlier)
                    # After this: [..., item2 at idx1, ..., item1 at idx2, ...]
                    sequence.MoveTo(idx1, idx1, sequence, idx2 + 1)
                    # Step 2: Now item2 is at idx1, move it to idx2
                    # But idx2 is now idx2-1 because we removed item1
                    sequence.MoveTo(idx1, idx1, sequence, idx2)
                else:
                    # item2 is before item1
                    # Step 1: Move item2 to after item1
                    sequence.MoveTo(idx2, idx2, sequence, idx1 + 1)
                    # Step 2: Now item1 is at idx2, move it to idx1
                    sequence.MoveTo(idx2, idx2, sequence, idx1)

        return True

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get dictionary of syncable properties for cross-project synchronization.

        This method is OPTIONAL for sync framework integration. Subclasses that
        want to support the sync framework (flexicon.sync) should implement this
        method to specify which properties can be safely synchronized between
        projects.

        The sync framework uses this method to:
        - Extract property values for comparison (DiffEngine)
        - Build property-level diffs showing what changed
        - Enable selective merging of individual properties (MergeOperations)
        - Support conflict resolution in multi-way syncs

        Args:
            item: The FLEx object to extract properties from.

        Returns:
            dict: Property names mapped to their values. Keys should be property
                  names (strings), values should be JSON-serializable when possible.
                  For complex FLEx objects (MultiString, etc.), return appropriate
                  representations.

        Raises:
            NotImplementedError: If subclass doesn't implement sync support.

        Example Implementation (in LexSenseOperations):
            >>> def GetSyncableProperties(self, sense):
            ...     '''Get syncable properties from a sense.'''
            ...     return {
            ...         'Gloss': self.GetGloss(sense),
            ...         'Definition': self.GetDefinition(sense),
            ...         'PartOfSpeech': self.GetPartOfSpeech(sense),
            ...         'SemanticDomains': self.GetSemanticDomains(sense),
            ...         'ExampleCount': sense.ExamplesOS.Count,
            ...         # Note: Don't include order-dependent items in properties
            ...         # The sync framework handles OS sequences separately
            ...     }

        Example Usage (by sync framework):
            >>> from flexicon.sync import DiffEngine
            >>>
            >>> # Compare senses between two projects
            >>> props1 = project1.Senses.GetSyncableProperties(sense1)
            >>> props2 = project2.Senses.GetSyncableProperties(sense2)
            >>>
            >>> diff_engine = DiffEngine()
            >>> is_different, differences = diff_engine.CompareProperties(
            ...     props1, props2
            ... )
            >>>
            >>> if is_different:
            ...     print(f"Properties changed: {list(differences.keys())}")
            ...     for prop, (old_val, new_val) in differences.items():
            ...         print(f"  {prop}: {old_val} -> {new_val}")

        Notes:
            - Return only properties that make sense to sync (not GUIDs, HVOs)
            - Don't include computed properties that depend on context
            - Don't include owning sequences (OS) - sync framework handles those
            - Return None or empty string for missing/empty properties
            - Complex objects: return string representations or dicts
            - This method is optional - subclasses that don't implement it
              simply won't support property-level sync

        What to Include:
            - Text fields (gloss, definition, notes)
            - References (part of speech, semantic domains)
            - Simple flags/enums (morpheme type, status)
            - Counts (for validation)

        What to Exclude:
            - GUIDs (sync framework uses these for matching)
            - HVOs (project-specific IDs)
            - Owner references (implicit in structure)
            - Owning sequences (handled separately by sync framework)
            - DateCreated/DateModified (use merge strategy instead)

        Sync Framework Integration:
            Used by: flexicon.sync.DiffEngine.CompareItems()
            Used by: flexicon.sync.MergeOperations.MergeProperties()
            See also: CompareTo() for full item comparison

        See Also:
            CompareTo, flexicon.sync.DiffEngine, flexicon.sync.MergeOperations
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement GetSyncableProperties(). "
            "This method is OPTIONAL for sync framework integration. "
            "Implement it if you want to enable property-level synchronization "
            "for this item type. See flexicon.sync documentation for details."
        )

    @OperationsMethod
    def ApplySyncableProperties(self, item, props, ws_map=None, fill_gaps=False):
        """
        Apply a syncable-properties dict (from GetSyncableProperties) onto an
        item. Inverse of GetSyncableProperties.

        Used by cross-project transfer workflows (e.g. GramTrans Phase 0):
        extract syncable props from a source item, create a target item via
        the appropriate factory + add to owner + assign Guid, then call
        ApplySyncableProperties to copy the syncable fields. Caller handles
        creation and identity; this method only sets values.

        The default implementation handles two value shapes returned by
        canonical GetSyncableProperties implementations:

        - **dict[str, str]** — a multilingual string field, keyed by source
          writing-system Id. Each value is applied to the target object's
          matching multistring field via set_String(), with writing-system
          handles resolved on the target side. If ws_map is provided, source
          Id is translated via that mapping; otherwise identity match by Id.
        - **str** — a plain string attribute. Set directly via setattr.

        Subclasses MAY override to handle category-specific shapes
        (object references that need cross-project resolution, owning
        collections, etc.). Subclass overrides typically delegate to
        super().ApplySyncableProperties for the multistring/string case and
        then add their own per-field logic.

        Args:
            item: Target LCM object. MUST already exist and be owned in the
                target project (callers create + add to owner + assign Guid
                before calling).
            props: dict produced by GetSyncableProperties on a source item.
            ws_map: Optional dict mapping source-project writing-system Id
                strings to target-project writing-system Id strings. Default
                is identity (a source 'en' value is applied to target's 'en'
                writing system if it exists). Source values whose mapped
                target WS Id does not exist in the target are silently
                skipped — callers wishing strict matching should validate
                ws_map against the target's WS inventory before calling.

        Returns:
            None.

        Raises:
            FP_NullParameterError: If item is None.
            FP_ParameterError: If props is not a dict.

        Example (cross-project POS copy):
            >>> src_pos = source.POS.Find("Verb")
            >>> props = source.POS.GetSyncableProperties(src_pos)
            >>> # Create target POS via raw factory pattern.
            >>> factory = target.GetService(IPartOfSpeechFactory)
            >>> new_pos = factory.Create()
            >>> target.Cache.LangProject.PartsOfSpeechOA.PossibilitiesOS.Add(new_pos)
            >>> new_pos.Guid = source_guid  # GUID preservation
            >>> target.POS.ApplySyncableProperties(new_pos, props)
        """
        self._EnsureWriteEnabled()

        if item is None:
            raise FP_NullParameterError()
        if not isinstance(props, dict):
            raise FP_ParameterError(
                f"ApplySyncableProperties: props must be a dict, got "
                f"{type(props).__name__}"
            )

        # Lazy import — avoids burdening module load for users who don't sync.
        from SIL.LCModel.Core.Text import TsStringUtils

        target_ws_by_id = {
            ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()
        }

        # B2/D5 bracket. This one was missed by the original 295-site sweep
        # because the sweep enumerated Operations *methods* and the writes
        # actually live in `_apply_props_loop`, a module-level helper -- so no
        # per-method scheme reached them. It was latent under `undoable=False`
        # (the session envelope covered every write) and became a hard failure
        # the moment DEF made `undoable=True` the default: with no envelope
        # open, `MultiUnicodeAccessor.set_String` raises
        # `InvalidOperationException: Not in the right state to register a
        # change.` One bracket for the whole loop, not per property: a partial
        # sync that failed halfway would otherwise leave the target item with
        # some fields updated and some stale, which is precisely the
        # half-applied state this method's callers cannot detect.
        with self._TransactionCM("Apply syncable properties"):
            _apply_props_loop(item, props, target_ws_by_id, fill_gaps,
                              ws_map=ws_map,
                              _default_ws_getter=self.project.GetDefaultAnalysisWSHandle,
                              _ts_string_utils=TsStringUtils)

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two items and return detailed differences.

        This method is OPTIONAL for sync framework integration. Subclasses that
        want to support the sync framework (flexicon.sync) should implement this
        method to enable intelligent comparison and merging between projects.

        The sync framework uses this method to:
        - Detect if two items (matched by GUID) have diverged
        - Generate detailed diff reports showing what changed
        - Support conflict detection in multi-way merges
        - Enable selective merge operations

        Args:
            item1: First item to compare (from source project).
            item2: Second item to compare (from target project).
            ops1: Optional. Operations instance for item1's project.
                  If None, uses self (assumes items from same project).
            ops2: Optional. Operations instance for item2's project.
                  If None, uses self (assumes items from same project).

        Returns:
            tuple: (is_different, differences) where:
                - is_different (bool): True if items differ in any way
                - differences (dict): Detailed differences with structure:
                    {
                        'properties': {
                            'PropertyName': {
                                'source': value_in_item1,
                                'target': value_in_item2,
                                'type': 'modified'|'added'|'removed'
                            },
                            ...
                        },
                        'children': {
                            'ChildSequenceName': {
                                'added': [guid1, guid2, ...],
                                'removed': [guid3, guid4, ...],
                                'modified': [guid5, guid6, ...]
                            },
                            ...
                        }
                    }

        Raises:
            NotImplementedError: If subclass doesn't implement sync support.

        Example Implementation (in LexSenseOperations):
            >>> def CompareTo(self, sense1, sense2, ops1=None, ops2=None):
            ...     '''Compare two senses for differences.'''
            ...     if ops1 is None:
            ...         ops1 = self
            ...     if ops2 is None:
            ...         ops2 = self
            ...
            ...     is_different = False
            ...     differences = {'properties': {}, 'children': {}}
            ...
            ...     # Compare properties
            ...     props1 = ops1.GetSyncableProperties(sense1)
            ...     props2 = ops2.GetSyncableProperties(sense2)
            ...
            ...     for key in set(props1.keys()) | set(props2.keys()):
            ...         val1 = props1.get(key)
            ...         val2 = props2.get(key)
            ...         if val1 != val2:
            ...             is_different = True
            ...             differences['properties'][key] = {
            ...                 'source': val1,
            ...                 'target': val2,
            ...                 'type': 'modified'
            ...             }
            ...
            ...     # Compare child sequences (examples)
            ...     guids1 = {ex.Guid for ex in sense1.ExamplesOS}
            ...     guids2 = {ex.Guid for ex in sense2.ExamplesOS}
            ...
            ...     added = guids2 - guids1
            ...     removed = guids1 - guids2
            ...
            ...     if added or removed:
            ...         is_different = True
            ...         differences['children']['Examples'] = {
            ...             'added': list(added),
            ...             'removed': list(removed),
            ...             'modified': []
            ...         }
            ...
            ...     return is_different, differences

        Example Usage (by sync framework):
            >>> from flexicon.sync import DiffEngine
            >>>
            >>> # Find matching senses by GUID in two projects
            >>> sense1 = project1.Senses.FindByGuid(guid)
            >>> sense2 = project2.Senses.FindByGuid(guid)
            >>>
            >>> # Compare them
            >>> is_diff, diffs = project1.Senses.CompareTo(
            ...     sense1, sense2,
            ...     ops1=project1.Senses,
            ...     ops2=project2.Senses
            ... )
            >>>
            >>> if is_diff:
            ...     print("Sense has diverged between projects:")
            ...     for prop, details in diffs['properties'].items():
            ...         print(f"  {prop}: {details['source']} -> {details['target']}")
            ...
            ...     for child_name, child_diffs in diffs['children'].items():
            ...         if child_diffs['added']:
            ...             print(f"  {child_name} added: {len(child_diffs['added'])}")
            ...         if child_diffs['removed']:
            ...             print(f"  {child_name} removed: {len(child_diffs['removed'])}")

        Notes:
            - Compare items by content, not identity (different objects, same data)
            - Use GetSyncableProperties() for property comparison
            - Compare child sequences by GUID (not position or count alone)
            - Return empty differences dict if items are identical
            - This method is optional - subclasses that don't implement it
              simply won't support detailed diff/merge operations

        Comparison Strategy:
            1. Extract properties using GetSyncableProperties()
            2. Compare property values (use appropriate equality for types)
            3. Compare child sequences by GUID membership
            4. Optionally recurse to compare child content (use ops1/ops2)
            5. Build structured differences dict

        Cross-Project Comparison:
            - ops1/ops2 allow comparing items from different projects
            - Each ops instance knows how to extract properties from its project
            - Handles differences in project structure gracefully
            - Use GUID for matching children across projects

        Sync Framework Integration:
            Used by: flexicon.sync.DiffEngine.GenerateDiff()
            Used by: flexicon.sync.MergeOperations.DetectConflicts()
            See also: GetSyncableProperties() for property extraction

        See Also:
            GetSyncableProperties, flexicon.sync.DiffEngine,
            flexicon.sync.MergeOperations
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement CompareTo(). "
            "This method is OPTIONAL for sync framework integration. "
            "Implement it if you want to enable detailed comparison and "
            "conflict detection for this item type. See flexicon.sync "
            "documentation for details."
        )

    # ========== HELPER METHODS ==========

    def _GetSequence(self, parent):
        """
        Get the owning sequence from parent object.

        This method MUST be overridden in subclasses to specify which
        owning sequence (OS) property to reorder.

        Args:
            parent: The parent object containing the sequence.

        Returns:
            ILcmOwningSequence: The sequence to reorder.

        Raises:
            NotImplementedError: If subclass doesn't override this method.

        Example (in subclass):
            >>> # In LexSenseOperations
            >>> def _GetSequence(self, parent):
            ...     return parent.SensesOS

            >>> # In AllomorphOperations
            >>> def _GetSequence(self, parent):
            ...     return parent.AlternateFormsOS

            >>> # In ExampleOperations
            >>> def _GetSequence(self, parent):
            ...     return parent.ExamplesOS

        Notes:
            - Each subclass specifies its own OS property
            - Called internally by all reordering methods
            - Provides type safety and correct sequence access

        See Also:
            All reordering methods use this internally.
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} must implement _GetSequence() "
            "to specify which owning sequence to reorder. "
            "Example: return parent.SensesOS"
        )

    def _GetObject(self, obj_or_hvo):
        """
        Get object from HVO or return object directly.

        Handles the common pattern where methods accept either an object
        or its HVO (Handle Value Object = integer ID).

        Args:
            obj_or_hvo: Either an object or an HVO (int).

        Returns:
            object: The resolved object.

        Example:
            >>> # Using object directly
            >>> sense = entry.SensesOS[0]
            >>> resolved = self._GetObject(sense)
            >>> assert resolved is sense

            >>> # Using HVO
            >>> hvo = sense.Hvo
            >>> resolved = self._GetObject(hvo)
            >>> assert resolved.Hvo == hvo

        Notes:
            - If obj_or_hvo is int, retrieves object by HVO
            - If obj_or_hvo is object, returns it unchanged
            - Uses FLExProject.Object() for HVO resolution

        See Also:
            All methods that accept parent_or_hvo use this.
        """
        if isinstance(obj_or_hvo, int):
            return self.project.Object(obj_or_hvo)
        return obj_or_hvo

    def _GetTypedOwner(self, obj):
        """
        Return obj.Owner cast to its concrete LCM interface.

        Owned LCM objects expose `.Owner` as the base ICmObject interface,
        which does NOT surface typed collection properties (SensesOS,
        AlternateFormsOS, EtymologyOS, AnnotationsOC, EntryRefsOS,
        SubPossibilitiesOS, RowsOS, etc.). Operations that need to add to
        or remove from one of those collections must therefore route the
        owner through `cast_to_concrete()` first; raw `obj.Owner.XxxOS` raises
        AttributeError, and `hasattr(obj.Owner, "XxxOS")` returns False even
        when the concrete owner does expose the collection -- which silently
        no-ops Delete and orphans Duplicate output.

        This helper centralises that cast so individual operations classes
        do not each have to import lcm_casting.

        Args:
            obj: An owned LCM object (must have an .Owner property).

        Returns:
            The owner cast to its concrete interface (e.g. ILexEntry,
            ICmAnthroItem, IDsConstChart, IRnGenericRec). Returns the raw
            owner unchanged if cast_to_concrete() does not recognise its
            ClassName, or None if obj has no .Owner.

        Notes:
            - Use the return value to access typed properties like
              SensesOS, AlternateFormsOS, AnnotationsOC.
            - Caller still owns existence checks (e.g. whether the owner
              actually has the expected collection for that path).
        """
        if obj is None or not hasattr(obj, "Owner"):
            return None
        owner = obj.Owner
        if owner is None:
            return None
        from .lcm_casting import cast_to_concrete
        return cast_to_concrete(owner)

    def _ResolveFeatureStrucOwner(self, owner, slot=None):
        """
        Resolve which atomic-owning ('OA') property on ``owner`` holds an
        ``IFsFeatStruc``, and return ``owner`` cast to the CONCRETE LCM
        interface that declares it.

        Single, ``ClassName``-driven source of truth for the "which
        differently-named property owns the feature structure on this
        object" question (spec ``feature-structure-sync-gap``, contract
        C1/C5). Backed by ``FEATURE_STRUC_OWNER_TABLE``
        (``Shared/lcm_constants.py``) -- the one and only copy of the
        frozen C1 table.

        Args:
            owner: An LCM object (or an ``LCMObjectWrapper``-style wrapper
                exposing ``._obj``) whose ``ClassName`` is looked up in
                ``FEATURE_STRUC_OWNER_TABLE``. Callers reaching ``owner``
                via an HVO or GUID must resolve/cast it to a real LCM
                object THEMSELVES first (contract C2) -- this method does
                not accept an ``int``/HVO.
            slot: Required ONLY when ``owner``'s ``ClassName`` has more
                than one row in the table (``MoDerivAffMsa``: ``"From"``/
                ``"To"``; ``PartOfSpeech``: ``"Default"``/
                ``"InherFeatVal"``). Ignored -- not an error -- for a
                ClassName with exactly one row, even if the caller passes
                one anyway (documented behaviour, not a defect).

        Returns:
            tuple: ``(concrete_owner, prop_name)`` where ``concrete_owner``
            is ``owner`` cast to its concrete LCM interface (e.g.
            ``IMoStemMsa(owner)``) and ``prop_name`` is the LCM
            atomic-owning property name on that interface (e.g.
            ``"MsFeaturesOA"``) -- read/write it directly:
            ``getattr(concrete_owner, prop_name)`` /
            ``setattr(concrete_owner, prop_name, new_struct)``.

        Raises:
            FP_ParameterError: If ``owner`` is ``None``; if ``owner`` has
                no ``ClassName`` (not an LCM object); if ``owner``'s
                ``ClassName`` is not a row in
                ``FEATURE_STRUC_OWNER_TABLE`` (message names the
                ClassName AND lists every supported ClassName -- this
                covers the table's deliberately-excluded ``ClassName``s,
                ``MoDerivStepMsa``, ``LexEntryInflType``, ``MoStemName``,
                ``MoUnclassifiedAffixMsa``, which raise here rather than
                being guessed at); if ``owner``'s ClassName has more than
                one row and ``slot`` is ``None`` or does not match any
                row's slot (message names the valid slot values -- NEVER
                guessed); or if no ``I<ClassName>`` interface exists in
                ``SIL.LCModel`` for a ClassName that IS in the table
                (an environment/LCM-version mismatch, not a caller error).
            TypeError: If the concrete cast itself fails (pythonnet
                rejects casting ``owner`` to its own ClassName's
                interface -- should not happen in normal operation since
                the interface is chosen FROM ``owner.ClassName`` itself,
                but this is intentionally NOT caught: a cast failure here
                indicates something is genuinely wrong with ``owner`` and
                must surface loudly, not be silently swallowed (probe
                item 2; contract C1 step 5).

        Notes:
            - Never gates on ``hasattr`` for a subtype-declared member --
              discriminates on ``.ClassName`` (always visible on the base
              interface under pythonnet) and then casts explicitly. This
              is the frozen rule the whole ``feature-structure-sync-gap``
              family exists to enforce (spec D5).
            - This method resolves OWNERSHIP only. It does not read or
              create the ``IFsFeatStruc`` itself -- see
              ``_GetFeatureStruc`` (serialize) and the future
              ``_ApplyFeatureStruc`` (T4) for that, and remember the
              ownership-first invariant: attach the struct to the owning
              property BEFORE populating or even reading its
              ``FeatureSpecsOC`` (a free-floating ``IFsFeatStruc``'s own
              getter raises ``NullReferenceException``).

        Example::

            >>> concrete, prop_name = self._ResolveFeatureStrucOwner(
            ...     msa, slot=None
            ... )
            >>> concrete.ClassName
            'MoStemMsa'
            >>> prop_name
            'MsFeaturesOA'
            >>> struct = getattr(concrete, prop_name)  # IFsFeatStruc | None

            >>> # Ambiguous owner -- slot required
            >>> concrete, prop_name = self._ResolveFeatureStrucOwner(
            ...     deriv_msa, slot="From"
            ... )
            >>> prop_name
            'FromMsFeaturesOA'
        """
        if owner is None:
            raise FP_ParameterError(
                "_ResolveFeatureStrucOwner: owner is None."
            )

        # Unwrap LCMObjectWrapper-style wrappers before reading ClassName.
        # Mirrors InflectionFeatureOperations.__Unwrap / PhonFeatureOperations
        # .__Unwrap -- a plain LCM object passes through unchanged.
        unwrapped = owner
        if hasattr(unwrapped, "_obj") and not hasattr(unwrapped, "Hvo"):
            unwrapped = unwrapped._obj
        elif hasattr(unwrapped, "_obj") and hasattr(unwrapped._obj, "Hvo"):
            unwrapped = unwrapped._obj

        if not hasattr(unwrapped, "ClassName"):
            raise FP_ParameterError(
                f"_ResolveFeatureStrucOwner: owner {unwrapped!r} has no "
                f"ClassName; expected an LCM object (or a wrapper "
                f"exposing one via ._obj)."
            )
        class_name = unwrapped.ClassName

        rows = FEATURE_STRUC_OWNER_TABLE.get(class_name)
        if not rows:
            supported = ", ".join(sorted(FEATURE_STRUC_OWNER_TABLE))
            raise FP_ParameterError(
                f"_ResolveFeatureStrucOwner: ClassName {class_name!r} is "
                f"not a recognized feature-structure owner. Supported "
                f"ClassNames: {supported}."
            )

        if len(rows) > 1:
            valid_slots = ", ".join(repr(row[0]) for row in rows)
            if slot is None:
                raise FP_ParameterError(
                    f"_ResolveFeatureStrucOwner: ClassName {class_name!r} "
                    f"has {len(rows)} feature-structure owning properties "
                    f"and requires an explicit slot=. Valid slot values: "
                    f"{valid_slots}. Never guessed."
                )
            for row_slot, prop_name, _props_key in rows:
                if row_slot == slot:
                    break
            else:
                raise FP_ParameterError(
                    f"_ResolveFeatureStrucOwner: ClassName {class_name!r} "
                    f"has no slot {slot!r}. Valid slot values: "
                    f"{valid_slots}."
                )
        else:
            # Single row: slot is IGNORED (documented behaviour, not an
            # error), even if the caller supplied one.
            _row_slot, prop_name, _props_key = rows[0]

        import SIL.LCModel as _lcm_module

        iface_name = "I" + class_name
        interface_type = getattr(_lcm_module, iface_name, None)
        if interface_type is None:
            raise FP_ParameterError(
                f"_ResolveFeatureStrucOwner: no {iface_name} interface "
                f"found in SIL.LCModel for ClassName {class_name!r}, even "
                f"though it is a row in FEATURE_STRUC_OWNER_TABLE. This "
                f"indicates an LCM-version mismatch, not a caller error."
            )

        # The cast itself is NOT wrapped in try/except -- a failure here
        # must raise TypeError loudly (contract C1 step 5); silently
        # falling back to the unchanged base object would defeat the
        # entire point of resolving a CONCRETE owner.
        concrete_owner = interface_type(unwrapped)

        return concrete_owner, prop_name

    def _GetFeatureStruc(self, struct, _top_level=True):
        """
        Serialize an ``IFsFeatStruc`` into the frozen C4 sync wire-format
        dict, RECURSIVELY -- an ``IFsComplexValue`` spec's ``ValueOA``
        becomes a nested dict of the same shape.

        Spec ``feature-structure-sync-gap``, contract C4/C5.

        Args:
            struct: An ``IFsFeatStruc`` (or an object castable to one --
                e.g. the base-typed value read back from a nested
                ``IFsComplexValue.ValueOA``, which pythonnet returns
                statically typed as the base ``IFsAbstractStructure``).
                May be ``None``.
            _top_level: Internal recursion flag. Always leave at the
                default (``True``) when calling this method directly --
                recursive calls into a nested ``ValueOA`` pass
                ``_top_level=False`` themselves. Controls only whether the
                returned dict carries a ``"Guid"`` key (see Returns).

        Returns:
            dict | None: ``None`` if ``struct`` is ``None`` (a genuinely
            absent/null feature structure -- the ONLY case that returns
            ``None``). Otherwise a dict shaped::

                {
                    "TypeGuid": "<guid>" | None,   # struct.TypeRA, THIS level
                    "Guid": "<guid>",              # NESTED levels only --
                                                    # omitted at top level
                    "specs": {
                        "<featDefnGuid>": "<valueGuid>",      # IFsClosedValue
                        "<complexFeatGuid>": {...recursive...} # IFsComplexValue
                                                                # .ValueOA
                    },
                }

            An empty-but-present structure (a real, attached
            ``IFsFeatStruc`` whose ``FeatureSpecsOC`` has zero entries)
            serializes as ``{"TypeGuid": ..., "specs": {}}`` -- NEVER
            ``None``. Only a struct that IS ``None`` returns ``None``.

        Notes:
            - Walks ``FeatureSpecsOC`` only. ``FeatureDisjunctionsOC`` is
              deliberately NOT traversed (out of scope for this feature;
              disjunctive feature structures are a new capability, filed
              separately per spec D2).
            - Discriminates each spec by ``.ClassName`` (``FsClosedValue``
              vs ``FsComplexValue``), then casts explicitly -- never
              ``hasattr``-probes a subtype member.
            - ``TypeGuid`` is copied PER LEVEL, independently. Live data
              has a NULL outer ``TypeRA`` and a NON-NULL inner one on a
              nested struct -- ``TypeRA`` is never a whole-struct
              property.
            - A spec whose ``FeatureRA``/``ValueRA`` (closed) or
              ``FeatureRA``/``ValueOA`` (complex) is ``None`` is skipped,
              matching the existing NC/Phoneme capture behaviour for a
              malformed/partial spec.
            - This is a pure READ/serialize helper -- it never creates or
              attaches anything, so the ownership-first invariant does not
              apply to it directly. It DOES rely on the caller having
              already attached ``struct`` to its owner: a free-floating
              (unattached) ``IFsFeatStruc``'s own ``FeatureSpecsOC``
              getter raises ``NullReferenceException`` in LCM.
            - C4a (Lead ruling, binding on future work): the CURRENTLY
              SHIPPED wire format for ``NaturalClassOperations`` /
              ``PhonemeOperations``'s ``props["Features"]`` is a FLAT LIST
              of ``{"FeatureGuid", "ValueGuid"}`` dicts
              (``NaturalClassOperations.py:1162``,
              ``PhonemeOperations.py:1373``), NOT this C4 dict shape. This
              method ALWAYS emits the C4 dict -- it does not, and must
              not, special-case its output to match the legacy list shape.
              The legacy flat list REMAINS a supported INPUT shape for the
              future ``_ApplyFeatureStruc``/generalized ``MakeFeatStruc``
              (T4/T5) to accept, alongside the new recursive C4 dict and
              recursive-dict specs surface (C3). Capture in
              ``NaturalClassOperations``/``PhonemeOperations`` is NOT
              migrated to C4 by this method's addition -- those two
              classes' ``GetSyncableProperties`` are untouched here and
              keep emitting the flat list until T4/T10 re-point them.

        Example::

            >>> concrete, prop_name = self._ResolveFeatureStrucOwner(msa)
            >>> struct = getattr(concrete, prop_name)
            >>> self._GetFeatureStruc(struct)
            {'TypeGuid': None, 'specs': {
                '11111111-...': '22222222-...',
                '33333333-...': {'TypeGuid': '44444444-...',
                                  'Guid': '55555555-...',
                                  'specs': {'66666666-...': '77777777-...'}},
            }}
        """
        if struct is None:
            return None

        from SIL.LCModel import IFsFeatStruc, IFsComplexValue, IFsClosedValue

        fs = IFsFeatStruc(struct)

        type_ra = fs.TypeRA
        result = {
            "TypeGuid": str(type_ra.Guid) if type_ra is not None else None,
            "specs": {},
        }
        if not _top_level:
            result["Guid"] = str(fs.Guid)

        for spec in fs.FeatureSpecsOC:
            # Discriminate on ClassName (always visible on the base
            # interface under pythonnet), then cast explicitly -- never
            # hasattr-probe a subtype-declared member.
            spec_class_name = spec.ClassName
            if spec_class_name == "FsClosedValue":
                closed_value = IFsClosedValue(spec)
                feat_ra = closed_value.FeatureRA
                val_ra = closed_value.ValueRA
                if feat_ra is None or val_ra is None:
                    continue
                result["specs"][str(feat_ra.Guid)] = str(val_ra.Guid)
            elif spec_class_name == "FsComplexValue":
                complex_value = IFsComplexValue(spec)
                feat_ra = complex_value.FeatureRA
                if feat_ra is None:
                    continue
                nested_value_oa = complex_value.ValueOA
                if nested_value_oa is None:
                    continue
                # Every read-back of a nested ValueOA needs its OWN
                # explicit IFsFeatStruc(...) cast -- it comes back typed
                # as the base IFsAbstractStructure (probe item 5).
                # _GetFeatureStruc performs that cast at the top of its
                # own recursive call, so we hand the raw ValueOA through.
                result["specs"][str(feat_ra.Guid)] = self._GetFeatureStruc(
                    nested_value_oa, _top_level=False
                )
            # else: an unrecognized spec ClassName -- out of scope
            # (FeatureDisjunctionsOC members live on a different
            # property entirely and are never reached via this loop
            # anyway). Silently skipped, matching NC/Phoneme's existing
            # "continue on unrecognized spec shape" behaviour.

        return result

    def _ResolveFsByGuid(self, guid, kind=None):
        """
        Resolve a GUID string to an LCM object in THIS project, returning
        ``None`` on failure rather than raising.

        De-duplicates the byte-for-byte identical
        ``NaturalClassOperations.__ResolveByGuid``
        (``NaturalClassOperations.py:1403``) and
        ``PhonemeOperations.__ResolveByGuid``
        (``PhonemeOperations.py:1525``) private methods into one shared
        helper (spec ``feature-structure-sync-gap``, contract C5). Those
        two private methods are left untouched here -- re-pointing them at
        this helper is T4's job, not this task's; this addition is purely
        additive and changes no existing caller's behaviour.

        Args:
            guid: GUID string to resolve (braced or unbraced -- whatever
                ``FLExProject.Object()`` itself accepts).
            kind (str, optional): Descriptive label for what is being
                resolved (e.g. ``"feature"``, ``"value"``), used only for
                a debug-level log line on failure. Purely diagnostic --
                does not affect this method's return value or behaviour.

        Returns:
            The resolved LCM object, or ``None`` if ``guid`` does not
            resolve to an object in this project (unknown/foreign GUID,
            or a malformed GUID string).

        Notes:
            - This method NEVER raises on a resolution failure -- per
              contract C7, an unresolved GUID must become a loud
              ``FP_ParameterError`` naming the GUID, but that raise is the
              CALLER's responsibility (mirroring the existing NC/Phoneme
              methods' division of labour: NC's caller raises, Phoneme's
              historically did not -- see spec D1/T9 for the ``skip``
              default's own upcoming policy flip, which is unrelated to
              this method's own contract).
        """
        import logging

        try:
            return self.project.Object(guid)
        except Exception as exc:
            logging.getLogger("flexicon").debug(
                "_ResolveFsByGuid: could not resolve %s GUID %r: %s: %s",
                kind or "object", guid, type(exc).__name__, exc,
            )
            return None

    def _CastFsFeatStruc(self, obj):
        """
        Cast ``obj`` to the concrete ``IFsFeatStruc`` LCM interface.

        Isolated into its own one-line method -- rather than an inline
        ``IFsFeatStruc(obj)`` -- purely as a TEST SEAM. ``SIL.LCModel`` is
        a pythonnet CLR namespace, not a regular Python module, and
        rejects ``setattr`` outright (``AttributeError: type does not
        support setting attributes``), so a fake-object unit test cannot
        monkeypatch ``SIL.LCModel.IFsFeatStruc`` the way
        ``NaturalClassOperations``'s own MODULE-LEVEL import of the same
        name CAN be monkeypatched (a plain Python module's ``__dict__``
        *does* support ``setattr``). Routing the cast through a
        ``BaseOperations`` method gives fake-object tests the same seam
        already used for ``_TransactionCM``/``_CreateWithGuid``
        (``monkeypatch.setattr(BaseOperations, "_CastFsFeatStruc", ...)``).
        Production callers are unaffected -- this performs exactly the
        cast the inline call used to.
        """
        from SIL.LCModel import IFsFeatStruc
        return IFsFeatStruc(obj)

    def _CastFsClosedValue(self, obj):
        """Cast ``obj`` to the concrete ``IFsClosedValue`` LCM interface.
        See ``_CastFsFeatStruc`` for why this one-line cast is its own
        method (test-seam, since ``SIL.LCModel`` rejects ``setattr``)."""
        from SIL.LCModel import IFsClosedValue
        return IFsClosedValue(obj)

    def _CastFsComplexValue(self, obj):
        """Cast ``obj`` to the concrete ``IFsComplexValue`` LCM interface.
        See ``_CastFsFeatStruc`` for why this one-line cast is its own
        method (test-seam, since ``SIL.LCModel`` rejects ``setattr``)."""
        from SIL.LCModel import IFsComplexValue
        return IFsComplexValue(obj)

    def _ApplyFeatureStruc(self, owner, prop_name, spec_dict, struct_guid=None,
                            on_unresolved="raise", label=None):
        """
        Rewrite ``owner``'s ``prop_name``-owned ``IFsFeatStruc`` from a
        wire-format spec, resolving every feature/value/type GUID against
        THIS (target) project's feature system, RECURSIVELY.

        Spec ``feature-structure-sync-gap``, contract C5/C6/C7 (+ C4a).
        Single generalized implementation of the algorithm that used to
        be duplicated verbatim as
        ``NaturalClassOperations.__ApplyFeatures`` and
        ``PhonemeOperations.__ApplyFeatures`` -- both are now thin
        call-throughs to this method (T4). It also de-duplicates the two
        private ``__ResolveByGuid`` twins into ``_ResolveFsByGuid`` (T3).

        Args:
            owner: The target object ALREADY CAST to the concrete LCM
                interface that declares ``prop_name`` (e.g. an
                ``IPhNCFeatures``, an ``IPhPhoneme``) -- callers resolve
                this themselves via ``_ResolveFeatureStrucOwner`` (C1) or,
                for NC/Phoneme's own dispatch, their existing
                ``ClassName``-driven cast. This method does not re-derive
                ``prop_name`` from ``owner`` -- see ``prop_name``.
            prop_name: The LCM atomic-owning ('OA') property name on
                ``owner`` that holds the ``IFsFeatStruc`` (e.g.
                ``"FeaturesOA"``, ``"MsFeaturesOA"``). Read via
                ``getattr(owner, prop_name)``, written via
                ``setattr(owner, prop_name, new_struct)``.
            spec_dict: The feature-value specs to apply. C4a (FROZEN):
                accepts BOTH wire shapes --
                (a) the C4 RECURSIVE DICT emitted by ``_GetFeatureStruc``:
                    ``{"TypeGuid": ..., "specs": {featGuid: valGuid |
                    {...nested C4 dict...}}}``; and
                (b) the LEGACY FLAT LIST shipped by
                    ``NaturalClassOperations``/``PhonemeOperations``:
                    ``[{"FeatureGuid": ..., "ValueGuid": ...}, ...]``.
                The shape is detected by ``isinstance(spec_dict, dict)``
                -- a list (or ``None``, treated as ``[]``) is handled as
                legacy; a dict is handled as C4. Legacy is NOT rewritten
                into a C4 dict as a preprocessing pass -- it is applied by
                an equivalent single-level algorithm so that per-item
                malformed/unresolved handling stays IDENTICAL to the
                original NC/Phoneme code (including partial application
                before a mid-list raise -- see Notes).
            struct_guid: Optional ``str`` GUID of the source
                ``IFsFeatStruc``, used to preserve identity when a new
                struct must be created on ``owner``. ``None`` reproduces
                the historical Phoneme behaviour (bare ``factory.Create()``,
                no GUID preserved) via ``_CreateWithGuid(..., guid=None)``,
                which is defined to be exactly the old no-arg
                ``Create()``.
            on_unresolved: ``"raise"`` (default) or ``"skip"``.
                ``"raise"``: an unresolved feature/value/type GUID, or a
                malformed legacy list entry, raises ``FP_ParameterError``
                naming the offending GUID/entry and ``label`` (contract
                C7 -- the NaturalClassOperations policy). ``"skip"``: the
                same conditions are silently skipped (the historical
                PhonemeOperations policy, D1). ``"skip"`` remains a fully
                supported, explicit opt-in -- it is just no caller's
                default after T9's flip.
            label: Human-readable description of ``owner`` used ONLY in
                raised error messages (e.g. ``"natural class 'Nasals'"``).
                Defaults to ``owner.ClassName`` when omitted.

        Returns:
            IFsFeatStruc: ``owner``'s (possibly newly-created)
            ``prop_name``-owned feature structure, cast to the concrete
            ``IFsFeatStruc`` interface.

        Raises:
            FP_ParameterError: If ``on_unresolved == "raise"`` and a
                feature, value, or (C4 only) feature-structure-type GUID
                does not resolve in the target project, or (legacy shape
                only) a list entry is malformed (not a dict, or missing
                ``FeatureGuid``/``ValueGuid``). If ``on_unresolved ==
                "skip"``, all of the above are silently skipped instead.

        Notes:
            - Ownership-first (C5 invariant, at EVERY nesting level): a
              missing ``prop_name`` is created and attached to ``owner``
              BEFORE its ``FeatureSpecsOC`` is populated or even read --
              a free-floating ``IFsFeatStruc``'s own ``FeatureSpecsOC``
              getter raises ``NullReferenceException`` (probe evidence).
            - Idempotency: existing ``(feature_guid, value_guid)`` pairs
              (legacy shape) / existing feature GUIDs (C4 shape, per
              level) are read ONCE before the loop and updated as each
              new spec is added, so re-applying the same
              ``ApplySyncableProperties`` call twice is a no-op the
              second time. This also fixes NC's original in-call
              duplicate-spec double-insert (the pre-T4 code re-scanned
              ``FeatureSpecsOC`` fresh each iteration; this method
              maintains one ``existing_*`` set/dict across the whole
              loop).
            - All guards (malformed entry, unresolved GUID) are evaluated
              OUTSIDE any ``_TransactionCM`` block, so a spec that fails
              to resolve never opens an empty named undo entry -- only
              the actual mutation (struct creation, spec insertion) is
              wrapped.
            - For the LEGACY list shape, items are applied ONE AT A TIME,
              in order, exactly like the original NC/Phoneme loops: a
              ``"raise"``-mode failure partway through the list leaves
              every ALREADY-PROCESSED prior item's mutation committed --
              this method does not validate the whole list up front. This
              is a deliberate byte-for-byte behavioural match, not an
              oversight.
            - For the C4 dict shape, every read-back of a nested
              ``IFsComplexValue.ValueOA`` gets its own explicit
              ``IFsFeatStruc(...)`` cast (mirrors ``_GetFeatureStruc``);
              nested application is delegated to
              ``_ApplyFeatureStrucSpecMap`` (a private recursion helper,
              not part of the C5 frozen surface).
            - Transaction labels used by this method ("Create feature
              structure" / "Add feature value") are intentionally
              OWNER-AGNOSTIC -- the pre-T4 NC/Phoneme code used
              owner-specific undo-stack text ("Create natural class
              feature structure" / "Create phoneme feature structure").
              No test locks that exact wording (only the RAISED
              ``FP_ParameterError`` messages are ever asserted on, and
              those still carry ``label``), so this is a cosmetic-only
              change to the FLEx Ctrl+Z menu entry text, not a functional
              behaviour change.
            - C4a's dual-shape support is exercised end-to-end for the
              legacy shape by the existing NC/Phoneme live tests (T4);
              the C4 dict shape (needed by future T6-T8 callers) has its
              own dedicated tests but is not yet driven by any NC/Phoneme
              call site -- ``_GetFeatureStruc`` always emits C4, but
              NC/Phoneme capture stays on the legacy list until T9b (C4b).
        """
        if on_unresolved not in ("raise", "skip"):
            raise FP_ParameterError(
                f"_ApplyFeatureStruc: on_unresolved must be 'raise' or "
                f"'skip', got {on_unresolved!r}."
            )
        if label is None:
            label = getattr(owner, "ClassName", None) or "object"

        from SIL.LCModel import (
            IFsFeatStrucFactory,
            IFsClosedValueFactory,
        )

        struct = getattr(owner, prop_name)
        if struct is None:
            factory = self.project.project.ServiceLocator.GetService(
                IFsFeatStrucFactory
            )
            # Ownership-first: attach to prop_name before populating specs
            # (LCM accessors NPE on free-floating IFsFeatStruc objects).
            with self._TransactionCM("Create feature structure"):
                new_struct = self._CreateWithGuid(
                    factory, guid=struct_guid, kind="feature structure",
                )
                setattr(owner, prop_name, new_struct)
            struct = getattr(owner, prop_name)
        struct = self._CastFsFeatStruc(struct)

        if isinstance(spec_dict, dict):
            cv_factory = self.project.project.ServiceLocator.GetService(
                IFsClosedValueFactory
            )
            self._ApplyFeatureStrucSpecMap(
                struct, spec_dict, on_unresolved, label, cv_factory,
            )
            return struct

        # --- Legacy flat list of {"FeatureGuid", "ValueGuid"} dicts (C4a) ---
        specs = spec_dict or []

        # Existing (feature, value) GUID pairs for idempotency.
        existing_pairs = set()
        for raw in struct.FeatureSpecsOC:
            try:
                cv = self._CastFsClosedValue(raw)
                if cv.FeatureRA is not None and cv.ValueRA is not None:
                    existing_pairs.add(
                        (str(cv.FeatureRA.Guid).lower(),
                         str(cv.ValueRA.Guid).lower())
                    )
            except Exception:
                continue

        cv_factory = self.project.project.ServiceLocator.GetService(
            IFsClosedValueFactory
        )
        for spec in specs:
            if not isinstance(spec, dict):
                if on_unresolved == "raise":
                    raise FP_ParameterError(
                        f"ApplySyncableProperties: {label} Features entry "
                        f"is not a dict: {spec!r}"
                    )
                continue
            feat_guid = spec.get("FeatureGuid")
            val_guid = spec.get("ValueGuid")
            if not feat_guid or not val_guid:
                if on_unresolved == "raise":
                    raise FP_ParameterError(
                        f"ApplySyncableProperties: {label} has a Features "
                        f"spec missing FeatureGuid/ValueGuid: {spec!r}"
                    )
                continue
            if (feat_guid.lower(), val_guid.lower()) in existing_pairs:
                continue  # already present (fill_gaps and normal both keep it)

            if on_unresolved == "raise":
                feat_obj = self._ResolveFsByGuid(feat_guid, kind="feature")
                if feat_obj is None:
                    raise FP_ParameterError(
                        f"ApplySyncableProperties: {label} references "
                        f"feature GUID {feat_guid} which does not exist "
                        f"in the target project. The feature system must "
                        f"be synced before this item is rewired; "
                        f"silently dropping this spec would leave the "
                        f"target's feature structure incomplete with no "
                        f"visible error."
                    )
                val_obj = self._ResolveFsByGuid(val_guid, kind="value")
                if val_obj is None:
                    raise FP_ParameterError(
                        f"ApplySyncableProperties: {label} references "
                        f"value GUID {val_guid} (feature {feat_guid}) "
                        f"which does not exist in the target project. "
                        f"The feature system must be synced before this "
                        f"item is rewired; silently dropping this spec "
                        f"would leave the target's feature structure "
                        f"incomplete with no visible error."
                    )
            else:
                feat_obj = self._ResolveFsByGuid(feat_guid, kind="feature")
                val_obj = self._ResolveFsByGuid(val_guid, kind="value")
                if feat_obj is None or val_obj is None:
                    # Target feature system lacks this feature/value; skip.
                    continue

            # Every guard above stays outside the transaction: a spec that
            # fails to resolve raises/continues before any transaction
            # opens, so no empty named undo entry is ever created.
            with self._TransactionCM("Add feature value"):
                closed_value = cv_factory.Create()
                struct.FeatureSpecsOC.Add(closed_value)
                cv = self._CastFsClosedValue(closed_value)
                cv.FeatureRA = feat_obj
                cv.ValueRA = val_obj

            existing_pairs.add((feat_guid.lower(), val_guid.lower()))

        return struct

    def _ApplyFeatureStrucSpecMap(self, struct, spec, on_unresolved, label,
                                   cv_factory):
        """
        Apply a single C4-dict LEVEL onto an already-attached
        ``IFsFeatStruc`` ``struct``, recursing into any nested
        ``IFsComplexValue.ValueOA`` level.

        Private recursion helper for ``_ApplyFeatureStruc``'s C4 dict-shape
        branch (C4a) -- not part of the C5 frozen surface. Mirrors
        ``_GetFeatureStruc``'s traversal in reverse: a scalar ``specs``
        value becomes an ``IFsClosedValue``; a nested-dict value becomes an
        ``IFsComplexValue`` whose ``ValueOA`` is populated by recursing.

        Args:
            struct: The ``IFsFeatStruc`` at THIS level (already attached to
                its owner -- ownership-first, per C5).
            spec: A C4-shaped dict for THIS level: ``{"TypeGuid": ...,
                "specs": {featGuid: valGuid | {...nested...}}}``.
            on_unresolved: ``"raise"`` | ``"skip"`` -- see
                ``_ApplyFeatureStruc``.
            label: Human-readable description used in raised messages.
            cv_factory: An ``IFsClosedValueFactory`` service instance,
                threaded through from the top-level call so every
                recursion level shares one factory lookup.

        Raises:
            FP_ParameterError: Mirrors ``_ApplyFeatureStruc``'s Raises
                section, for an unresolved feature/value/type GUID when
                ``on_unresolved == "raise"``.
        """
        from SIL.LCModel import (
            IFsComplexValueFactory,
            IFsFeatStrucFactory,
        )

        type_guid = spec.get("TypeGuid")
        if type_guid:
            type_obj = self._ResolveFsByGuid(
                type_guid, kind="feature structure type"
            )
            if type_obj is None:
                if on_unresolved == "raise":
                    raise FP_ParameterError(
                        f"ApplySyncableProperties: {label} references "
                        f"feature structure type GUID {type_guid} which "
                        f"does not exist in the target project."
                    )
            else:
                with self._TransactionCM("Set feature structure type"):
                    struct.TypeRA = type_obj

        # Existing closed-value (feature -> IFsClosedValue) and complex-value
        # (feature -> IFsComplexValue) entries, keyed by lower-cased feature
        # GUID, for idempotency -- read ONCE before the loop (mirrors the
        # legacy-shape existing_pairs set in _ApplyFeatureStruc).
        existing_closed = {}
        existing_complex = {}
        for raw in struct.FeatureSpecsOC:
            spec_class_name = raw.ClassName
            if spec_class_name == "FsClosedValue":
                cv = self._CastFsClosedValue(raw)
                if cv.FeatureRA is not None and cv.ValueRA is not None:
                    existing_closed[str(cv.FeatureRA.Guid).lower()] = cv
            elif spec_class_name == "FsComplexValue":
                cx = self._CastFsComplexValue(raw)
                if cx.FeatureRA is not None:
                    existing_complex[str(cx.FeatureRA.Guid).lower()] = cx

        for feat_guid, value in (spec.get("specs") or {}).items():
            feat_obj = self._ResolveFsByGuid(feat_guid, kind="feature")
            if feat_obj is None:
                if on_unresolved == "raise":
                    raise FP_ParameterError(
                        f"ApplySyncableProperties: {label} references "
                        f"feature GUID {feat_guid} which does not exist "
                        f"in the target project. The feature system must "
                        f"be synced before this item is rewired; "
                        f"silently dropping this spec would leave the "
                        f"target's feature structure incomplete with no "
                        f"visible error."
                    )
                continue

            if isinstance(value, dict):
                # Complex (nested) feature spec -> IFsComplexValue.ValueOA.
                existing_cx = existing_complex.get(feat_guid.lower())
                if existing_cx is not None:
                    nested_struct = self._CastFsFeatStruc(existing_cx.ValueOA)
                else:
                    cx_factory = self.project.project.ServiceLocator.GetService(
                        IFsComplexValueFactory
                    )
                    fs_factory = self.project.project.ServiceLocator.GetService(
                        IFsFeatStrucFactory
                    )
                    nested_guid = value.get("Guid")
                    with self._TransactionCM("Add feature value"):
                        complex_value = cx_factory.Create()
                        struct.FeatureSpecsOC.Add(complex_value)
                        cx = self._CastFsComplexValue(complex_value)
                        cx.FeatureRA = feat_obj
                        nested = self._CreateWithGuid(
                            fs_factory, guid=nested_guid,
                            kind="feature structure",
                        )
                        cx.ValueOA = nested
                    existing_complex[feat_guid.lower()] = cx
                    nested_struct = self._CastFsFeatStruc(cx.ValueOA)

                self._ApplyFeatureStrucSpecMap(
                    nested_struct, value, on_unresolved, label, cv_factory,
                )
                continue

            # Scalar (closed) feature spec.
            val_guid = value
            if feat_guid.lower() in existing_closed:
                continue  # already present
            val_obj = self._ResolveFsByGuid(val_guid, kind="value")
            if val_obj is None:
                if on_unresolved == "raise":
                    raise FP_ParameterError(
                        f"ApplySyncableProperties: {label} references "
                        f"value GUID {val_guid} (feature {feat_guid}) "
                        f"which does not exist in the target project. "
                        f"The feature system must be synced before this "
                        f"item is rewired; silently dropping this spec "
                        f"would leave the target's feature structure "
                        f"incomplete with no visible error."
                    )
                continue

            with self._TransactionCM("Add feature value"):
                closed_value = cv_factory.Create()
                struct.FeatureSpecsOC.Add(closed_value)
                cv = self._CastFsClosedValue(closed_value)
                cv.FeatureRA = feat_obj
                cv.ValueRA = val_obj
            existing_closed[feat_guid.lower()] = cv

    def _MakeFeatStruc(self, specs, owner=None, slot=None):
        """
        Build (and attach) an ``IFsFeatStruc`` from user-facing specs.

        Spec ``feature-structure-sync-gap``, contract C3 (FROZEN).
        Single generalized implementation of what used to be two
        byte-identical-except-for-the-owner-check bodies --
        ``InflectionFeatureOperations.MakeFeatStruc`` (``:970``) and
        ``PhonFeatureOperations.MakeFeatStruc`` (``:553``) are now thin
        call-throughs to this method (T5). Closes issue **#256**.

        **#256 was NOT a casting bug.** Both pre-T5 bodies gated with
        ``if not hasattr(owner_unwrapped, "FeaturesOA"): raise`` --
        which is coincidentally correct ONLY for ``IPhNCFeatures``/
        ``IPhPhoneme`` (the two owners that happen to be named
        ``FeaturesOA``) and unconditionally wrong -- 100% dead-code-as-a-
        fix -- for every other owner (MSA x4, POS x2, Allomorph), which
        own their struct through a DIFFERENTLY NAMED property
        (``MsFeaturesOA``, ``InflFeatsOA``, ``FromMsFeaturesOA``, ...).
        This method replaces that ``hasattr`` gate with T2's
        ``ClassName``-driven ``_ResolveFeatureStrucOwner``
        (``Shared/lcm_constants.py::FEATURE_STRUC_OWNER_TABLE``, C1) --
        never guessing, never gating on ``hasattr`` for a subtype-
        declared member (spec D5).

        Args:
            specs: EITHER of two accepted shapes (both resolved via the
                SAME per-operand resolution the two pre-T5 bodies used --
                an HVO ``int``, an already-resolved LCM object/wrapper,
                or (new, additive) a GUID ``str``; see Notes):

                (a) RECURSIVE DICT (canonical, C3)::

                        {"noun agreement": {"class": "1", "number": "sg"},
                         "polarity": "positive"}

                    A dict VALUE -> ``IFsComplexValue`` whose ``ValueOA``
                    is a nested ``IFsFeatStruc`` built by recursing. A
                    SCALAR value -> ``IFsClosedValue``. No depth limit.

                (b) FLAT LIST OF ``(feature, value)`` TUPLES (legacy,
                    SUPPORTED INDEFINITELY -- 5 internal call sites +
                    4 shipped test files pass this shape; see spec.md
                    C3/C4a). Exactly equivalent to a one-level dict. The
                    REJECTED ``("feat", [(f, v), ...])`` tuple-nesting
                    overload (a silent ``isinstance`` branch capped at
                    one extra level) is deliberately NOT special-cased
                    here -- a list-shaped tuple VALUE falls through to
                    the scalar branch and fails loudly at the LCM
                    property-set call, which is the correct outcome for
                    an overload this contract explicitly rejects.

            owner: LCM object (or wrapper) that owns the struct.
                **Required -- ``owner=None`` always raises** (issue #28
                ruling, unchanged by T5): LCM property accessors NPE on
                free-floating ``IFsFeatStruc`` objects, so an unowned-
                empty mode would return an unusable struct.
            slot: Disambiguates owners with more than one feature-
                structure-owning property (``MoDerivAffMsa``:
                ``"From"``/``"To"``; ``PartOfSpeech``: ``"Default"``/
                ``"InherFeatVal"``). Ignored -- not an error -- for a
                single-property owner, even if supplied. See C1 /
                ``_ResolveFeatureStrucOwner``.

        Returns:
            IFsFeatStruc: The populated feature structure, attached to
            ``owner``'s C1-resolved owning property.

        Raises:
            FP_ParameterError: If ``owner`` is ``None``; if a spec entry
                is malformed (legacy shape: not a 2-tuple); if ``owner``'s
                ``ClassName`` is not a recognized feature-structure owner,
                or is ambiguous and ``slot`` is missing/invalid (see
                ``_ResolveFeatureStrucOwner``); or if a GUID-string
                operand is malformed.

        Notes:
            - Per-operand resolution mirrors the two pre-T5 bodies
              EXACTLY for ``int`` (HVO) and already-resolved LCM
              object/wrapper inputs -- zero behaviour change for any
              input that worked before. GUID ``str`` support is
              ADDITIVE: neither pre-T5 body special-cased a string, so
              one used to fall through unresolved and fail at the LCM
              property-set call; routing it through ``project.Object()``
              is a strict improvement with no back-compat risk. Plain
              NAME-string resolution (e.g. passing ``"back"`` instead of
              the feature object returned by ``Find("back")``) is
              deliberately NOT added -- neither pre-T5 body supported it,
              no shipped test exercises it, and guessing which of
              several ``Find``-style lookups applies to an arbitrary
              string would be exactly the kind of silent guess C1's
              resolver exists to forbid.
            - Ownership-first (C5 invariant) at EVERY nesting level: the
              struct/``ValueOA`` is attached to its owner BEFORE its
              ``FeatureSpecsOC`` is populated or even read -- a free-
              floating ``IFsFeatStruc``'s own getter raises
              ``NullReferenceException`` (probe evidence).
            - Every spec is normalized (resolved, malformed-shape
              checked) BEFORE the owner is resolved or any transaction is
              opened -- mirrors both pre-T5 bodies' up-front validation,
              so a malformed spec never leaves a partially-attached
              struct behind.
            - This is the C3 user-facing COMPOSE surface, resolving
              named/object/HVO/GUID operands directly against LCM --
              a DIFFERENT recursion from the C4/C5 sync APPLY surface
              (``_ApplyFeatureStruc``/``_ApplyFeatureStrucSpecMap``,
              T3/T4), which resolves GUID-only wire-format specs against
              a target project's feature system. The two are not merged:
              they solve different problems (compose-from-friendly-
              specs vs. apply-a-serialized-wire-spec) and merging them
              would mean round-tripping every already-resolved object
              through a GUID for no reason.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(specs, "specs")

        if owner is None:
            raise FP_ParameterError(
                "MakeFeatStruc requires an owner. LCM property "
                "accessors NPE on free-floating IFsFeatStruc objects, "
                "so the previous unowned-empty mode produced an "
                "unusable struct (issue #28). Pass owner=phoneme / "
                "owner=natural_class / owner=msa / owner=pos / "
                "owner=allomorph / owner=context, plus slot= when the "
                "owner has more than one feature-structure-owning "
                "property (MoDerivAffMsa: 'From'/'To'; PartOfSpeech: "
                "'Default'/'InherFeatVal') -- see "
                "_ResolveFeatureStrucOwner."
            )

        # Normalize (resolve + validate shape) ALL specs, recursively,
        # BEFORE touching owner or opening a transaction -- mirrors both
        # pre-T5 bodies' up-front normalization pass.
        normalized = self.__NormalizeFeatStrucLevel(specs)

        # THE #256 FIX: resolve owner via the C1 table instead of the
        # `hasattr(owner, "FeaturesOA")` gate. Raises FP_ParameterError
        # for an unrecognized/ambiguous-without-slot ClassName; raises
        # TypeError (uncaught, by design -- C1 step 5) if the concrete
        # cast itself fails.
        concrete_owner, prop_name = self._ResolveFeatureStrucOwner(
            owner, slot=slot
        )

        from SIL.LCModel import IFsFeatStrucFactory

        factory = self.project.project.ServiceLocator.GetService(
            IFsFeatStrucFactory
        )

        with self._TransactionCM("Make feature structure"):
            struct = factory.Create()
            setattr(concrete_owner, prop_name, struct)
            # Re-fetch via the owning property to hold the LCM view of
            # the now-owned struct (ownership-first, C5).
            struct = self._CastFsFeatStruc(
                getattr(concrete_owner, prop_name)
            )
            self.__PopulateFeatStrucLevel(struct, normalized)

            return struct

    def __NormalizeFeatStrucLevel(self, level_specs):
        """
        Recursively resolve ONE level of ``_MakeFeatStruc`` specs (either
        shape from C3) into a list of ``(resolved_feat, resolved_val)``
        pairs, where ``resolved_val`` is itself such a list for a nested
        (dict) value, or a resolved scalar LCM object/operand otherwise.

        Pure resolution -- ``project.Object()`` lookups only, no factory
        calls, no LCM mutation -- so it is safe to run to completion,
        and raise on a malformed shape, before any transaction opens.
        """
        if isinstance(level_specs, dict):
            raw_pairs = list(level_specs.items())
        else:
            raw_pairs = []
            for i, pair in enumerate(level_specs):
                if not isinstance(pair, (list, tuple)) or len(pair) != 2:
                    raise FP_ParameterError(
                        f"specs[{i}] must be a (feature, value) tuple"
                    )
                raw_pairs.append(tuple(pair))

        normalized = []
        for feat_raw, val_raw in raw_pairs:
            feat = self.__ResolveFeatStrucOperand(feat_raw)
            if isinstance(val_raw, dict):
                nested = self.__NormalizeFeatStrucLevel(val_raw)
                normalized.append((feat, nested))
            else:
                val = self.__ResolveFeatStrucOperand(val_raw)
                normalized.append((feat, val))
        return normalized

    def __PopulateFeatStrucLevel(self, struct, normalized_pairs,
                                  _factories=None):
        """
        Populate an ALREADY-ATTACHED ``IFsFeatStruc`` ``struct`` from a
        level of ``(resolved_feat, resolved_val)`` pairs produced by
        ``__NormalizeFeatStrucLevel``, recursing into nested-list values
        (a nested value is always a ``list`` -- ``__NormalizeFeatStrucLevel``
        only ever produces a ``list`` for a dict-shaped spec value; any
        other value, including a malformed raw ``list``, is treated as a
        scalar operand and left to fail naturally at the LCM property-set
        call). Ownership-first (C5) at every level: the nested struct is
        attached to its owning ``IFsComplexValue.ValueOA`` BEFORE this
        method recurses into it.
        """
        if _factories is None:
            from SIL.LCModel import (
                IFsClosedValueFactory,
                IFsComplexValueFactory,
                IFsFeatStrucFactory,
            )
            _factories = (
                self.project.project.ServiceLocator.GetService(
                    IFsClosedValueFactory
                ),
                self.project.project.ServiceLocator.GetService(
                    IFsComplexValueFactory
                ),
                self.project.project.ServiceLocator.GetService(
                    IFsFeatStrucFactory
                ),
            )
        cv_factory, cx_factory, fs_factory = _factories

        for feat, val in normalized_pairs:
            if isinstance(val, list):
                # Nested (complex) feature spec -> IFsComplexValue.ValueOA.
                # Own transaction per mutation (matches
                # _ApplyFeatureStrucSpecMap's "Add feature value" label for
                # the identical complex-value-creation shape, and satisfies
                # the B2g unbracketed-mutation ratchet, which scans each
                # method's OWN body for a lexically-enclosing
                # `with self._TransactionCM(...)` -- an outer caller's
                # transaction does not count).
                with self._TransactionCM("Add feature value"):
                    complex_value = cx_factory.Create()
                    struct.FeatureSpecsOC.Add(complex_value)
                    cx = self._CastFsComplexValue(complex_value)
                    cx.FeatureRA = feat
                    nested_raw = fs_factory.Create()
                    cx.ValueOA = nested_raw
                nested = self._CastFsFeatStruc(cx.ValueOA)
                self.__PopulateFeatStrucLevel(nested, val, _factories)
            else:
                with self._TransactionCM("Add feature value"):
                    closed_value = cv_factory.Create()
                    struct.FeatureSpecsOC.Add(closed_value)
                    cv = self._CastFsClosedValue(closed_value)
                    cv.FeatureRA = feat
                    cv.ValueRA = val

    def __ResolveFeatStrucOperand(self, raw):
        """
        Resolve one ``_MakeFeatStruc`` feature/value operand: an HVO
        (``int``), a GUID (``str``), or an already-resolved LCM
        object/wrapper. See ``_MakeFeatStruc``'s Notes for why GUID
        strings are additive-only and plain name strings are
        deliberately unsupported.
        """
        if isinstance(raw, int) and not isinstance(raw, bool):
            return self.project.Object(raw)
        if isinstance(raw, str):
            return self.project.Object(raw)
        # Peel off LCMObjectWrapper-style wrappers -- mirrors
        # InflectionFeatureOperations.__Unwrap / PhonFeatureOperations
        # .__Unwrap.
        if hasattr(raw, "_obj") and not hasattr(raw, "Hvo"):
            return raw._obj
        if hasattr(raw, "_obj") and hasattr(raw._obj, "Hvo"):
            return raw._obj
        return raw

    def _RejectLegacyKwargs(self, kwargs, legacy_to_new):
        """
        Trap unexpected legacy keyword arguments with a clear,
        actionable TypeError pointing at the rename + migration guide.

        Used by methods that renamed parameters in d423e83 (v2.4 -> v2.5
        breaking change: ``flat=`` -> ``recursive=``,
        ``include_subcategories=`` -> ``recursive=``). Per CLAUDE.md, the
        repo does not ship compat shims, so the rename remains a hard
        break -- but a bare ``TypeError: unexpected keyword 'flat'``
        offers no breadcrumb to the new name. This helper raises a
        TypeError that names the new parameter and points at the
        migration guide. (issue #104)

        Args:
            kwargs: The caller's ``**kwargs`` dict (after the named
                parameters have been bound).
            legacy_to_new: Mapping of legacy kwarg name to a
                ``(new_kwarg_name, semantics_note)`` tuple, e.g.
                ``{"flat": ("recursive", "semantics inverted: "
                "flat=True is now recursive=False")}``. The semantics
                note is appended to the error message to flag any
                non-name-only changes.

        Raises:
            TypeError: When ``kwargs`` contains a legacy name OR any
                other unrecognized kwarg (so typos in the new name
                surface as errors too).

        Example:
            >>> def GetAll(self, recursive=True, **kwargs):
            ...     self._RejectLegacyKwargs(kwargs, {
            ...         "flat": ("recursive",
            ...                  "semantics inverted: flat=True -> "
            ...                  "recursive=False"),
            ...     })
            ...     ...
        """
        for legacy_name, (new_name, semantics_note) in legacy_to_new.items():
            if legacy_name in kwargs:
                raise TypeError(
                    f"{legacy_name!r} was renamed to {new_name!r} in v2.5 "
                    f"({semantics_note}). See docs/MIGRATION_GUIDE.md."
                )
        if kwargs:
            unknown = sorted(kwargs)
            raise TypeError(
                f"unexpected keyword argument(s) {unknown!r}"
            )

    def _FindCommonSequence(self, item1, item2):
        """
        Find the sequence that contains both items.

        Used by MoveBefore, MoveAfter, and Swap to automatically determine
        which sequence contains both items. Examines the Owner property
        and searches for OS properties containing both items.

        Args:
            item1: First item (object, not HVO).
            item2: Second item (object, not HVO).

        Returns:
            ILcmOwningSequence: The sequence containing both items.

        Raises:
            ValueError: If items don't have same owner.
            ValueError: If items not found in same sequence.
            ValueError: If no OS property contains both items.

        Example:
            >>> # Both senses from same entry
            >>> sense1 = entry.SensesOS[0]
            >>> sense2 = entry.SensesOS[2]
            >>> sequence = self._FindCommonSequence(sense1, sense2)
            >>> assert sequence is entry.SensesOS

            >>> # Both examples from same sense
            >>> ex1 = sense.ExamplesOS[0]
            >>> ex2 = sense.ExamplesOS[1]
            >>> sequence = self._FindCommonSequence(ex1, ex2)
            >>> assert sequence is sense.ExamplesOS

        Notes:
            - Checks Owner property first (most efficient)
            - Scans all properties ending in 'OS' (owning sequences)
            - Returns first sequence containing both items
            - Used internally by MoveBefore, MoveAfter, Swap

        Algorithm:
            1. Check if items have same Owner
            2. Search owner's properties for name ending in 'OS'
            3. Check if both items present in sequence
            4. Return first matching sequence

        See Also:
            MoveBefore, MoveAfter, Swap
        """
        # Verify items have Owner property
        if not hasattr(item1, "Owner") or not hasattr(item2, "Owner"):
            raise ValueError("Items must have Owner property to find common sequence")

        # Check if items have same owner
        if item1.Owner != item2.Owner:
            raise ValueError(
                "Items not in same sequence (different owners). "
                "MoveBefore/MoveAfter/Swap require items in same sequence."
            )

        # Items must also have the same OwningFlid (field ID) to be in same sequence
        if item1.OwningFlid != item2.OwningFlid:
            raise ValueError(
                "Items not in same sequence (different OwningFlid). "
                "MoveBefore/MoveAfter/Swap require items in same sequence."
            )

        # Get the parent object
        # Note: item1.Owner returns ICmObject, which doesn't expose properties like SensesOS
        # We need to use reflection to access properties
        parent = self._GetObject(item1.Owner.Hvo)

        # Use reflection to find the sequence property that contains both items
        # Iterate through all properties ending in 'OS' (Owning Sequence)
        parent_type = parent.GetType()
        for prop_info in parent_type.GetProperties():
            if prop_info.Name.endswith(OWNING_SEQUENCE_SUFFIX):
                try:
                    sequence = prop_info.GetValue(parent, None)
                    if sequence is None or not hasattr(sequence, "Count"):
                        continue

                    # Check if both items are in this sequence
                    # Note: sequence from reflection may not support indexing, use iteration
                    found1 = False
                    found2 = False
                    for item in sequence:
                        if item == item1:
                            found1 = True
                        if item == item2:
                            found2 = True
                        if found1 and found2:
                            return sequence
                except Exception:
                    # Property might not be accessible or not a sequence
                    continue

        # Items have same owner but not found in any OS property
        raise ValueError(
            "Items not in same sequence or sequence not found. " "Both items must be in the same owning sequence (OS)."
        )

    # ========== VALIDATION METHODS ==========

    def _EnsureWriteEnabled(self) -> None:
        """
        Verify that the project is open in write mode.

        This method checks that the FLExProject is properly opened with write
        capabilities. All modification operations should call this method before
        making any changes.

        Args:
            None

        Returns:
            None

        Raises:
            FP_ReadOnlyError: If project is not writable (opened read-only or closed).

        Example:
            >>> def CreateNewSense(self, entry):
            ...     self._EnsureWriteEnabled()  # Check before modification
            ...     sense = entry.SensesOS.Create()
            ...     return sense

        Notes:
            - Should be called at the start of any modification method
            - Provides early failure with clear error message
            - Prevents partial modifications on closed/read-only projects
            - Lightweight check (just checks project.writeEnabled property)

        Implementation Notes:
            - Checks project.writeEnabled property
            - Raises FP_ReadOnlyError with descriptive message
            - No side effects
        """
        if not self.project.writeEnabled:
            raise FP_ReadOnlyError()

    def _TransactionCM(self, label):
        """
        Return a transaction context manager appropriate to the project mode.

        Intended for methods that perform **two or more distinct LCM mutations**
        (e.g. ``factory.Create()``, ``OS.Add()``, and one or more property
        writes).  Single-mutation methods (one ``OS.Add`` or one property set)
        do not need this wrapper -- the LCM write is already atomic.

        Auto-selects Phase 2 (``UndoableOperation``, visible in the FLEx
        Ctrl+Z menu) when the project was opened with ``undoable=True``,
        otherwise Phase 1 (``Transaction``). Use this to wrap the body of
        any write method that performs two or more LCM mutations, so a
        failure partway through is at least labelled and grouped -- see the
        Notes below for what this wrapper does and does NOT protect against
        in each mode; today, neither mode auto-rolls-back a partial write.

        Wrap only the mutation portion of a method: call validation helpers
        (``_EnsureWriteEnabled``, ``_Validate*``) and any lookups that may
        raise BEFORE entering this context, so input errors never mark the
        undo stack. Keep the method's ``return`` inside the ``with`` block.

        Args:
            label (str): Human-readable description used for logging and, in
                Phase 2, the FLEx undo menu (e.g. "Create entry 'famba'").

        Returns:
            A ``_NestingAwareTransaction`` context manager that delegates to
            ``_FLExTransaction`` (Phase 1) or ``_FLExUndoableOperation``
            (Phase 2), or becomes a no-op when nested inside another
            ``_TransactionCM`` block in Phase 2 (see Notes).

        Example::

            def Create(self, form, ws=None):
                self._EnsureWriteEnabled()
                self._ValidateStringNotEmpty(form, "form")
                with self._TransactionCM(f"Create entry '{form}'"):
                    entry = entry_factory.Create()
                    entry.LexemeFormOA = allomorph_factory.Create()
                    entry.LexemeFormOA.Form.set_String(ws_handle, tss)
                    return entry

        Notes:
            - Phase 1 (``Transaction``) does NOT roll back on exception in the
              current build. liblcm exposes no reachable rollback-to-mark API
              in this mode (issue #236; see
              ``specs/write-path-transactions/spec.md`` D1 and
              ``FLExProject.Transaction()``'s docstring for the specific API
              name checked). ``_TransactionCM`` in Phase 1 is a labelling and
              nesting construct only; the atomicity unit is the whole
              session, not this block. See ``docs/EXCEPTION_HANDLING.md``.
            - Phase 2 (``UndoableOperation``) IS rollback-capable (see B1,
              `specs/write-path-transactions/spec.md`): ``_TransactionCM``
              constructs liblcm's own ``UndoableUnitOfWorkHelper`` directly
              for the outermost block. An exception raised inside the block
              rolls back every mutation that block made, in addition to the
              partial work remaining undoable by the FLEx user via Ctrl+Z up
              until the point of rollback.
            - ``_undoable`` is only ever True when the project is also
              write-enabled, so Phase 2 selection cannot collide with the
              read-only guard already enforced by ``_EnsureWriteEnabled``.
            - Nesting differs by phase:

              * Phase 1 (``Transaction``) nests without error. Each ``with``
                block enters and exits cleanly, but since neither the inner
                nor the outer block can roll back, "nesting" here means only
                that labels compose -- there is no independent rollback point
                to speak of at any depth.
              * Phase 2 (``UndoableOperation``) does NOT nest at the LCM level:
                ``BeginUndoTask``/``EndUndoTask`` cannot be nested without
                corrupting the undo stack. ``_TransactionCM`` guards against
                this automatically by asking LCM's own
                ``cache.ActionHandlerAccessor.CurrentDepth`` at every
                ``__enter__`` -- never by tracking depth itself in Python
                (that hand-rolled counter was issue #234, and is gone). Only
                the OUTERMOST block (``CurrentDepth == 0``) opens a new
                ``UndoableUnitOfWorkHelper``; any ``_TransactionCM`` entered
                while one is already active (``CurrentDepth > 0``) becomes a
                no-op and lets the outer task group all of its mutations into
                the single named undo entry (the desired Phase 2 behavior).
                This means an inner method's mutations are not separately
                undoable (or separately rolled back) in Phase 2 -- they are
                absorbed into the enclosing operation's undo task, and its
                rollback decision covers them too.
        """
        from .transaction import _NestingAwareTransaction

        return _NestingAwareTransaction(self.project, label)

    def _CreateWithGuid(self, factory, guid=None, kind=None):
        """
        Create an object through an LCM factory, preserving a caller-supplied GUID.

        Nearly every LibLCM factory exposes a ``Create(Guid)`` overload alongside
        the no-arg ``Create()``. Callers that are REPRODUCING an object from
        another project (a transfer, a merge, a round-trip) must be able to keep
        the original identity: a target object carrying the source GUID is
        recognisably the same object on a later run, which is what makes
        deduplication and re-linking possible at all. Without it, downstream
        tools are forced to invent structural fingerprints to recover identity
        that was needlessly discarded.

        When ``guid`` is None this is exactly the old no-arg ``Create()``, so
        existing callers are unaffected.

        Args:
            factory: An LCM factory instance exposing ``Create()`` and,
                optionally, ``Create(Guid)``.
            guid: Optional. The GUID to assign, as a ``System.Guid`` or a string
                (braced or unbraced). None (the default) mints a fresh GUID.
            kind (str, optional): Descriptive name used in the warning logged
                when a requested GUID could not be honoured.

        Returns:
            The newly created object.

        Raises:
            FP_ParameterError: If ``guid`` was supplied but is not a valid GUID.

        Note:
            If the GUID is already present in the project, LCM raises and this
            falls back to a fresh identity, logging a warning that names the
            GUID. Callers that must not silently lose identity should check for
            an existing object first (see the ``Find``/``Get*`` helpers).

        Example:
            >>> # Reproduce a paragraph from another project under its own GUID
            >>> para = project.Paragraphs.Create(text, "In the beginning...",
            ...                                  guid=src_para.Guid)
            >>> str(para.Guid) == str(src_para.Guid)
            True

        See Also:
            _ValidateParam
        """
        import logging

        label = f"Create {kind}" if kind else "Create object"

        if guid is None:
            with self._TransactionCM(label):
                return factory.Create()

        # GUID parsing happens BEFORE the transaction: a malformed GUID is a
        # caller error and must raise without opening an undo task (decision
        # D5's validate-then-mutate discipline).
        guid_arg = guid
        if isinstance(guid, str):
            from System import Guid as _DotNetGuid
            try:
                guid_arg = _DotNetGuid.Parse(guid)
            except Exception as exc:
                raise FP_ParameterError(
                    "guid %r is not a valid GUID" % (guid,)) from exc

        # The attempt-then-fallback pair is ONE transaction. The failed
        # Create(Guid) is caught here rather than escaping, so the block still
        # exits cleanly and commits the fallback object -- the identity-loss
        # warning, not a rollback, is the documented outcome.
        with self._TransactionCM(label):
            try:
                return factory.Create(guid_arg)
            except Exception as exc:
                logging.getLogger("flexicon").warning(
                    "%s: Create(Guid=%s) failed (%s: %s); falling back to a new "
                    "identity. The requested GUID was NOT preserved.",
                    kind or type(factory).__name__, guid, type(exc).__name__, exc)
                return factory.Create()

    def _ValidateParam(self, param: Any, param_name: str = "parameter") -> None:
        """
        Validate that a parameter is not None and not a stale LCM object.

        This method performs a null check on a required parameter. Use this for
        any parameter that must be provided and non-None. When the parameter is
        a live LCM object reference, it is additionally rejected if it refers to
        a deleted/invalid object (``IsValidObject`` is False).

        Args:
            param: The parameter value to validate (any type).
            param_name: Optional. Descriptive name for error messages.
                       Default: "parameter".

        Returns:
            None

        Raises:
            FP_NullParameterError: If param is None.
            FP_ParameterError: If param is an LCM object that has been deleted
                or otherwise invalidated (``IsValidObject`` is False).

        Example:
            >>> def SetGloss(self, sense, gloss):
            ...     self._ValidateParam(sense, "sense")
            ...     self._ValidateParam(gloss, "gloss")
            ...     sense.Gloss.BestAnalysisAlternative.Text = gloss

            >>> def MoveItem(self, parent, item):
            ...     self._ValidateParam(parent, "parent")
            ...     self._ValidateParam(item, "item")
            ...     # Perform move operation

        Notes:
            - Lightweight null check
            - Works with any type (objects, primitives, etc.)
            - Provides helpful error message with parameter name
            - Use _ValidateInstanceOf for type checking
            - Use _ValidateParamNotEmpty for string empty checks

        Implementation Notes:
            - Simple if param is None check
            - Stale-reference guard: a cascade-deleted LCM object keeps a live
              .NET reference but its Cache/Services pointers are torn down, so
              touching any property raises a NullReferenceException from deep
              inside LCM. ICmObject exposes IsValidObject (False once deleted);
              mirrors LCM's own guard pattern (OverridesLing_Lex.cs:1500).
            - getattr(..., None) means non-LCM params (str/int/dict/etc.) have
              no IsValidObject attribute -> None -> skipped. Only an explicit
              False triggers the error, so a True value is never mistaken.
            - No side effects
            - Exception message includes parameter name
        """
        if param is None:
            raise FP_NullParameterError()
        # Reject stale LCM object references (cascade-deleted / invalidated).
        # Non-LCM params return None here and are left untouched.
        if getattr(param, "IsValidObject", None) is False:
            raise FP_ParameterError(
                f"{param_name} refers to a deleted or invalid LCM object"
            )

    def _ValidateParamNotEmpty(self, param: Any, param_name: str = "parameter") -> None:
        """
        Validate that a parameter is not None and not empty.

        This method performs both a null check and an emptiness check. Use this
        for parameters like lists, strings, or collections that must have content.

        Args:
            param: The parameter to validate (list, string, dict, or object
                   with __len__ method).
            param_name: Optional. Descriptive name for error messages.
                       Default: "parameter".

        Returns:
            None

        Raises:
            Exception: If param is None.
            Exception: If param is empty (len() == 0).

        Example:
            >>> def CreateEntries(self, entry_list):
            ...     self._ValidateParamNotEmpty(entry_list, "entry_list")
            ...     for entry in entry_list:
            ...         # Process each entry

            >>> def SortItems(self, items):
            ...     self._ValidateParamNotEmpty(items, "items")
            ...     return self.Sort(parent, key_func=lambda i: str(i))

            >>> def SetGloss(self, gloss):
            ...     self._ValidateParamNotEmpty(gloss, "gloss text")
            ...     sense.Gloss.BestAnalysisAlternative.Text = gloss

        Notes:
            - Checks for both None and empty conditions
            - Works with any object supporting len()
            - Provides helpful error messages
            - Use _ValidateParam for None-only checks
            - Use _ValidateStringNotEmpty for string-specific validation

        Implementation Notes:
            - First checks if param is None
            - Then checks if len(param) == 0
            - No side effects
        """
        if param is None:
            raise FP_NullParameterError()
        if len(param) == 0:
            raise FP_ParameterError(f"{param_name} cannot be empty")

    def _ValidateInstanceOf(self, obj: Any, expected_type: type, param_name: str = "object") -> None:
        """
        Validate that an object is an instance of expected type.

        This method performs strict type checking. Use this to ensure parameters
        are the correct type before attempting operations that depend on specific
        properties or methods.

        Args:
            obj: The object to validate.
            expected_type: The expected type or tuple of types.
                          Examples: str, int, ILexEntry, (str, int)
            param_name: Optional. Descriptive name for error messages.
                       Default: "object".

        Returns:
            None

        Raises:
            TypeError: If obj is not instance of expected_type.

        Example:
            >>> def UpdateSense(self, sense):
            ...     self._ValidateInstanceOf(sense, ILexSense, "sense")
            ...     sense.Gloss.BestAnalysisAlternative.Text = "new gloss"

            >>> def ProcessEntries(self, entries):
            ...     self._ValidateInstanceOf(entries, list, "entries")
            ...     for entry in entries:
            ...         self._ValidateInstanceOf(entry, ILexEntry, "entry")

            >>> def FindSenseByGloss(self, entry, gloss):
            ...     self._ValidateInstanceOf(entry, ILexEntry, "entry")
            ...     self._ValidateInstanceOf(gloss, (str, type(None)), "gloss")

        Notes:
            - Performs isinstance() check
            - Supports single type or tuple of types
            - Helpful error message with actual and expected types
            - Use _ValidateParam for None checks
            - Use _ValidateStringNotEmpty for string-specific validation

        Implementation Notes:
            - Uses isinstance() internally
            - Raises TypeError (not generic Exception)
            - Gets type names for helpful error messages
            - No side effects
        """
        if not isinstance(obj, expected_type):
            if isinstance(expected_type, tuple):
                type_names = " or ".join(t.__name__ for t in expected_type)
            else:
                type_names = expected_type.__name__
            raise TypeError(f"{param_name} must be {type_names}, " f"got {type(obj).__name__}")

    def _ValidateStringNotEmpty(self, text: str, param_name: str = "text") -> None:
        """
        Validate that a string is not None and not empty.

        This method performs validation specific to string parameters. Use this
        for text fields that require non-empty content.

        Args:
            text: The string to validate.
            param_name: Optional. Descriptive name for error messages.
                       Default: "text".

        Returns:
            None

        Raises:
            TypeError: If text is not a string.
            Exception: If text is None.
            Exception: If text is empty string or contains only whitespace.

        Example:
            >>> def SetGloss(self, sense, gloss_text):
            ...     self._ValidateStringNotEmpty(gloss_text, "gloss")
            ...     sense.Gloss.BestAnalysisAlternative.Text = gloss_text

            >>> def UpdateDefinition(self, sense, definition):
            ...     self._ValidateStringNotEmpty(definition, "definition")
            ...     sense.Definition.BestAnalysisAlternative.Text = definition

            >>> def CreateNote(self, note_text):
            ...     self._ValidateStringNotEmpty(note_text, "note")
            ...     # Create note with validated text

        Notes:
            - Checks for None, empty string, and whitespace-only
            - Validates type is string
            - Useful for text fields that must have content
            - Use _ValidateParam for general None checks
            - Use _ValidateParamNotEmpty for collections

        Implementation Notes:
            - First validates type is string
            - Then checks if None
            - Then checks if stripped length is 0
            - No side effects
        """
        if not isinstance(text, str):
            raise TypeError(f"{param_name} must be a string, got {type(text).__name__}")
        if text is None:
            raise FP_NullParameterError()
        if len(text.strip()) == 0:
            raise FP_ParameterError(f"{param_name} cannot be empty or contain only whitespace")

    def _ValidateIndexBounds(self, index: int, max_count: int, param_name: str = "index") -> None:
        """
        Validate that an index is within bounds [0, max_count-1].

        This method performs bounds checking for array/collection indices.
        Use this to ensure index parameters are valid before accessing sequences.

        Args:
            index: The index to validate (must be int).
            max_count: The maximum count (length) of the collection.
                      Must be positive int.
            param_name: Optional. Descriptive name for error messages.
                       Default: "index".

        Returns:
            None

        Raises:
            TypeError: If index is not an integer.
            ValueError: If index is negative.
            IndexError: If index >= max_count.

        Example:
            >>> def GetSenseAt(self, entry, index):
            ...     self._ValidateIndexBounds(index, entry.SensesOS.Count, "sense_index")
            ...     return entry.SensesOS[index]

            >>> def MoveToIndex(self, parent, item, index):
            ...     self._ValidateIndexBounds(index, len(self._GetSequence(parent)), "target_index")
            ...     # Perform move operation

            >>> def InsertAtPosition(self, collection, index, item):
            ...     self._ValidateIndexBounds(index, len(collection) + 1, "insertion_index")
            ...     collection.Insert(index, item)

        Notes:
            - Validates both lower bound (>= 0) and upper bound (< max_count)
            - Requires integer index
            - max_count must be positive
            - Provides helpful error with valid range
            - Use for array/sequence/collection access
            - Use _ValidateParam for other integer validation

        Implementation Notes:
            - Checks isinstance(index, int)
            - Checks index >= 0
            - Checks index < max_count
            - Raises appropriate exception types
            - No side effects
        """
        if not isinstance(index, int):
            raise TypeError(f"{param_name} must be an integer, got {type(index).__name__}")
        if index < 0:
            raise ValueError(f"{param_name} cannot be negative, got {index}")
        if index >= max_count:
            raise IndexError(f"{param_name} out of bounds: {index} >= {max_count} " f"(valid range: 0-{max_count - 1})")

    def _ValidateOwner(self, obj: Any, expected_owner: Any, param_name: str = "object") -> None:
        """
        Validate that an object has expected owner.

        This method performs owner validation. Use this to ensure an object
        belongs to the correct parent before performing ownership-dependent
        operations.

        Args:
            obj: The object to validate (must have Owner property).
            expected_owner: The expected owner object.
            param_name: Optional. Descriptive name for error messages.
                       Default: "object".

        Returns:
            None

        Raises:
            AttributeError: If obj doesn't have Owner property.
            ValueError: If obj.Owner does not match expected_owner.

        Example:
            >>> def AddExampleToSense(self, sense, example):
            ...     self._ValidateOwner(example, sense, "example")
            ...     # Example must belong to this sense

            >>> def MoveToParent(self, item, new_parent):
            ...     if hasattr(item, 'Owner'):
            ...         old_owner = item.Owner
            ...         self._ValidateOwner(item, old_owner, "item")

            >>> def VerifySenseInEntry(self, sense, entry):
            ...     self._ValidateOwner(sense, entry, "sense")
            ...     # Now we know sense.Owner == entry

        Notes:
            - Checks that object has Owner property
            - Validates Owner matches expected_owner
            - Works with any object with Owner property
            - Provides helpful error message
            - Useful for ensuring object hierarchy correctness

        Implementation Notes:
            - Checks if obj has Owner attribute
            - Compares obj.Owner with expected_owner
            - Uses equality check (==), not identity (is)
            - No side effects
        """
        if not hasattr(obj, "Owner"):
            raise AttributeError(f"{param_name} does not have Owner property")
        if obj.Owner != expected_owner:
            raise ValueError(
                f"{param_name} owner does not match expected owner. "
                f"Object owner: {obj.Owner}, Expected: {expected_owner}"
            )

    # ========== DATA TRANSFORMATION HELPERS ==========

    def _NormalizeMultiString(self, value: str) -> str:
        """
        Convert FLEx empty placeholder to Python empty string.

        LibLCM (the underlying C# library) represents empty multistring fields
        with the placeholder "***". This helper converts it to Python's standard
        empty string ("") for a more Pythonic API.

        Args:
            value: The string value from a LibLCM multistring field.
                  May be "***", "", None, or actual text.

        Returns:
            str: The value converted to "" if it was "***", otherwise unchanged.
                - "***" → ""
                - "" → ""
                - "word" → "word"
                - None → None (unchanged)

        Example:
            >>> sense_gloss = sense.Gloss.BestAnalysisAlternative.Text  # Returns "***"
            >>> normalized = self._NormalizeMultiString(sense_gloss)  # Returns ""
            >>> if normalized:  # Python-standard empty check works
            ...     print(f"Gloss: {normalized}")

        Notes:
            - This is called automatically by all public methods that return
              multistring field values, so users don't need to call it directly
            - See MIGRATION_GUIDE.md for breaking change details
            - FLEx/LCM Convention: "***" is used to represent empty multistring
              fields rather than None or empty string (for internal consistency)

        Implementation Notes:
            - Simple string comparison and replacement
            - No side effects
            - Preserves None (useful for optional fields)
        """
        if value == "***":
            return ""
        return value

    # ========== ITsString (SINGLE-STRING) HELPERS ==========
    #
    # FLEx multilingual fields come in two LCM flavors that look similar at
    # the API surface but behave very differently. Confusing them is the
    # recurring source of the "single-string field" bug class:
    #
    #   ITsString
    #       One localised string with an embedded writing-system handle.
    #       Read via .Text directly. Build via TsStringUtils.MakeString.
    #       Examples (NON-exhaustive):
    #         - ILexSense.Source
    #         - ILexSense.ScientificName
    #         - ILexSense.ImportResidue
    #         - ILexEntry.ImportResidue
    #
    #   IMultiString / IMultiUnicode
    #       Collection of localised strings indexed by ws handle. Read via
    #       .get_String(ws); write via .set_String(ws, ts_string).
    #       Examples (NON-exhaustive):
    #         - ILexEtymology.Source           (same name as above, DIFFERENT type)
    #         - IStText.Source                 (same name as above, DIFFERENT type)
    #         - ILexSense.Definition
    #         - ILexSense.Gloss
    #
    # The two helpers below are the canonical adapters for ITsString fields.
    # Use them instead of assigning a Python str directly to an ITsString
    # attribute (raises TypeError at the pythonnet boundary) or passing a
    # raw ITsString through a Python-string normaliser (returns garbage).

    def _MakeTsString(self, text, wsHandle=None):
        """
        Build an ITsString for assignment to a single-string ITsString field.

        Args:
            text (str): The Python string to wrap.
            wsHandle: Optional writing system handle (int) or language tag
                (str). Defaults to the project's analysis WS when None.

        Returns:
            ITsString: The wrapped string ready to assign to an
            ITsString-typed LCM property.

        Notes:
            - This is the correct path for writes to ILexSense.Source,
              ILexSense.ScientificName, ILexSense.ImportResidue,
              ILexEntry.ImportResidue, and other single-string fields.
            - For IMultiString fields use ``field.set_String(ws, ts)``
              directly with a TsStringUtils.MakeString result; do NOT
              assign through this helper.
        """
        from SIL.LCModel.Core.Text import TsStringUtils

        if wsHandle is None:
            ws = self.project.project.DefaultAnalWs
        else:
            ws = self.project._FLExProject__WSHandle(
                wsHandle, self.project.project.DefaultAnalWs
            )
        return TsStringUtils.MakeString(text, ws)

    def _ReadTsString(self, tss):
        """
        Read an ITsString field as a Python str.

        Collapses unset / None / the FLEx null-marker ('***') to "".
        Single-string fields have no per-WS dimension where None vs ""
        would be meaningful, so the multistring family's None-passthrough
        is not appropriate here.

        Args:
            tss: An ITsString-typed LCM value (or None).

        Returns:
            str: The string content. Always a Python str -- never None,
            never a raw ITsString object.

        Notes:
            - This is the correct path for reads from ILexSense.Source,
              ILexSense.ScientificName, ILexSense.ImportResidue,
              ILexEntry.ImportResidue, and other single-string fields.
            - For IMultiString fields read via ``field.get_String(ws)``
              and call ``ITsString(...).Text`` yourself; do NOT route a
              per-WS read through this helper.
        """
        from SIL.LCModel.Core.KernelInterfaces import ITsString

        if tss is None:
            return ""
        text = ITsString(tss).Text
        if text is None:
            return ""
        return self._NormalizeMultiString(text)
