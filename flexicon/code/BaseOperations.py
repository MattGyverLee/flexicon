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
from .Shared.lcm_constants import OWNING_SEQUENCE_SUFFIX

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

        from flexlibs2 import FLExProject

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

        # Apply new order using MoveTo
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

        # Swap using MoveTo operations
        # Strategy: Move lower-index item after higher-index item, then move higher item to original position
        if idx1 != -1 and idx2 != -1 and idx1 != idx2:
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
        want to support the sync framework (flexlibs2.sync) should implement this
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
            >>> from flexlibs2.sync import DiffEngine
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
            Used by: flexlibs2.sync.DiffEngine.CompareItems()
            Used by: flexlibs2.sync.MergeOperations.MergeProperties()
            See also: CompareTo() for full item comparison

        See Also:
            CompareTo, flexlibs2.sync.DiffEngine, flexlibs2.sync.MergeOperations
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement GetSyncableProperties(). "
            "This method is OPTIONAL for sync framework integration. "
            "Implement it if you want to enable property-level synchronization "
            "for this item type. See flexlibs2.sync documentation for details."
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

        _apply_props_loop(item, props, target_ws_by_id, fill_gaps,
                          ws_map=ws_map,
                          _default_ws_getter=self.project.GetDefaultAnalysisWSHandle,
                          _ts_string_utils=TsStringUtils)

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two items and return detailed differences.

        This method is OPTIONAL for sync framework integration. Subclasses that
        want to support the sync framework (flexlibs2.sync) should implement this
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
            >>> from flexlibs2.sync import DiffEngine
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
            Used by: flexlibs2.sync.DiffEngine.GenerateDiff()
            Used by: flexlibs2.sync.MergeOperations.DetectConflicts()
            See also: GetSyncableProperties() for property extraction

        See Also:
            GetSyncableProperties, flexlibs2.sync.DiffEngine,
            flexlibs2.sync.MergeOperations
        """
        raise NotImplementedError(
            f"{self.__class__.__name__} does not implement CompareTo(). "
            "This method is OPTIONAL for sync framework integration. "
            "Implement it if you want to enable detailed comparison and "
            "conflict detection for this item type. See flexlibs2.sync "
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
        otherwise Phase 1 (``Transaction``, programmatic rollback-only). Use
        this to wrap the body of any write method that performs two or more
        LCM mutations, so a failure partway through does not leave a
        partially-constructed object persisted in the cache with no rollback.

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
            - Phase 1 (``Transaction``) rolls back to a mark on exception.
            - Phase 2 (``UndoableOperation``) wraps the changes in a single
              named undo task; it does NOT auto-rollback on exception, but
              the partial work is undoable by the FLEx user via Ctrl+Z.
            - ``_undoable`` is only ever True when the project is also
              write-enabled, so Phase 2 selection cannot collide with the
              read-only guard already enforced by ``_EnsureWriteEnabled``.
            - Nesting differs by phase:

              * Phase 1 (``Transaction``) nests safely. Each ``with`` block
                marks an independent rollback point; an inner rollback rolls
                back to the inner mark, an outer rollback rolls back
                everything. A caller-supplied outer
                ``with project.Transaction("batch"):`` therefore captures
                every write made by the inner ``_TransactionCM`` blocks.
              * Phase 2 (``UndoableOperation``) does NOT nest at the LCM level:
                ``BeginUndoTask``/``EndUndoTask`` cannot be nested without
                corrupting the undo stack. ``_TransactionCM`` guards against
                this automatically using ``project._transaction_depth``: only
                the OUTERMOST block opens an undo task; any ``_TransactionCM``
                entered while one is already active becomes a no-op and lets
                the outer task group all of its mutations into the single
                named undo entry (the desired Phase 2 behavior). This means an
                inner method's mutations are not separately undoable in Phase 2
                - they are absorbed into the enclosing operation's undo task.
        """
        from .transaction import _NestingAwareTransaction

        return _NestingAwareTransaction(self.project, label)

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
