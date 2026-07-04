#
#   ExampleOperations.py
#
#   Class: ExampleOperations
#          Example sentence operations for FieldWorks Language Explorer
#          projects via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2025
#

import logging

logger = logging.getLogger(__name__)

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# Import FLEx LCM types
from SIL.LCModel import (
    ILexExampleSentence,
    ILexExampleSentenceFactory,
    ILexSense,
    ICmTranslation,
    ICmTranslationFactory,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# Import string utilities
from ..Shared.string_utils import normalize_text


class ExampleOperations(BaseOperations):
    """
    This class provides operations for managing example sentences in a FieldWorks project.

    Example sentences illustrate the usage of lexical senses in context. Each example
    can have vernacular text, translations in multiple analysis languages, references
    to source texts, and associated media files.

    Usage::

        from flexlibs2 import FLExProject, ExampleOperations

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        exampleOps = ExampleOperations(project)

        # Get first entry and sense
        entry = project.LexiconAllEntries().__next__()
        sense = entry.SensesOS[0] if entry.SensesOS.Count > 0 else None

        # Get all examples for a sense
        for example in exampleOps.GetAll(sense):
            text = exampleOps.GetExample(example)
            trans = exampleOps.GetTranslation(example)
            print(f"Example: {text}")
            print(f"Translation: {trans}")

        # Create a new example
        example = exampleOps.Create(sense, "The cat sat on the mat.")
        exampleOps.SetTranslation(example, "Le chat s'est assis sur le tapis.")
        exampleOps.SetReference(example, "Example Corpus 1.23")

        project.CloseProject()
    """

    def __init__(self, project):
        """
        Initialize ExampleOperations with a FLExProject instance.

        Args:
            project: The FLExProject instance to operate on.
        """
        super().__init__(project)

    def _GetSequence(self, parent):
        """
        Specify which sequence to reorder for examples.
        For Example, we reorder sense.ExamplesOS
        """
        return parent.ExamplesOS

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self, sense_or_hvo=None):
        """
        Get example sentences for a sense or all examples in the project.

        Args:
            sense_or_hvo: Optional ILexSense object or HVO.
                         If provided, returns examples for that sense only.
                         If None, returns ALL examples in the entire project.

        Yields:
            ILexExampleSentence: Each example sentence.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>>
            >>> # Get examples for a specific sense
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> for example in exampleOps.GetAll(sense):
            ...     text = exampleOps.GetExample(example)
            ...     print(f"Example: {text}")
            Example: The dog ran quickly.
            Example: Dogs run faster than cats.
            >>>
            >>> # Get ALL examples in entire project
            >>> for example in exampleOps.GetAll():
            ...     text = exampleOps.GetExample(example)
            ...     print(f"Example: {text}")

        Notes:
            - When called with no argument, iterates all examples in project
            - When called with sense, returns only that sense's examples
            - Returns examples in the order they appear in FLEx
            - Returns empty generator if no examples exist
            - Examples are ordered collections (can be reordered)

        See Also:
            Create, Delete, Reorder
        """
        if sense_or_hvo is None:
            # Iterate ALL examples in entire project
            for entry in self.project.lexDB.Entries:
                for sense in entry.AllSenses:  # Includes subsenses
                    for example in sense.ExamplesOS:
                        yield example
        else:
            # Iterate examples for specific sense
            sense = self.__GetSenseObject(sense_or_hvo)
            for example in sense.ExamplesOS:
                yield example

    @OperationsMethod
    def Create(self, sense_or_hvo, example_text, wsHandle=None):
        """
        Create a new example sentence for a lexical sense.

        Args:
            sense_or_hvo: The ILexSense object or HVO.
            example_text (str): The example sentence text.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            ILexExampleSentence: The newly created example object.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If sense_or_hvo or example_text is None.
            FP_ParameterError: If example_text is empty.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> example = exampleOps.Create(sense, "The cat slept.")
            >>> print(exampleOps.GetExample(example))
            The cat slept.

            >>> # Create with specific writing system
            >>> example = exampleOps.Create(sense, "Le chat dort.",
            ...                              project.WSHandle('fr'))

        Notes:
            - The example is added to the end of the sense's examples list
            - You can add translations after creation using SetTranslation()
            - References and media can also be added separately
            - Use vernacular writing system for the example text

        See Also:
            Delete, SetExample, SetTranslation
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(sense_or_hvo, "sense_or_hvo")
        self._ValidateParam(example_text, "example_text")

        self._ValidateStringNotEmpty(example_text, "example_text")

        sense = self.__GetSenseObject(sense_or_hvo)
        wsHandle = self.__WSHandleVern(wsHandle)

        # Create the new example using the factory
        factory = self.project.project.ServiceLocator.GetService(ILexExampleSentenceFactory)

        with self._TransactionCM("Create example"):
            # factory.Create() is the first mutation; kept inside the transaction
            # so the object is owned atomically with its Add() and property writes.
            example = factory.Create()

            # Add to sense's examples collection (must be done before setting properties)
            sense.ExamplesOS.Add(example)

            # Set example text
            mkstr = TsStringUtils.MakeString(example_text, wsHandle)
            example.Example.set_String(wsHandle, mkstr)

            return example

    @OperationsMethod
    def Delete(self, example_or_hvo):
        """
        Delete an example sentence.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO to delete.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If example_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if len(examples) > 0:
            ...     exampleOps.Delete(examples[-1])

        Warning:
            - Deletion is permanent and cannot be undone
            - All translations and associated data are also deleted
            - Media file links are removed (but files themselves remain)

        Notes:
            - Removes the example from the owning sense's collection
            - Automatically removes all translations

        See Also:
            Create, GetAll
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)

        # ExamplesOS lives on ILexSense (the concrete owner), not on the
        # base ICmObject that pythonnet returns from .Owner. The prior
        # hasattr(owner, "ExamplesOS") was always False on the base type
        # and Delete silently no-op'd. Route through _GetTypedOwner to
        # recover the concrete ILexSense first. Same shape as #160 / #98.
        # (issue #162)
        sense = self._GetTypedOwner(example)
        if sense is not None and hasattr(sense, "ExamplesOS"):
            sense.ExamplesOS.Remove(example)

    @OperationsMethod
    def Duplicate(self, item_or_hvo, insert_after=True, deep=False):
        """
        Duplicate an example sentence, creating a new copy with a new GUID.

        Args:
            item_or_hvo: The ILexExampleSentence object or HVO to duplicate.
            insert_after (bool): If True (default), insert after the source example.
                                If False, insert at end of parent's examples list.
            deep (bool): If True, also duplicate owned objects (translations).
                        If False (default), only copy simple properties.

        Returns:
            ILexExampleSentence: The newly created duplicate example with a new GUID.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If item_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     # Shallow duplicate (no translations)
            ...     dup = exampleOps.Duplicate(examples[0])
            ...     print(f"Original: {exampleOps.GetGuid(examples[0])}")
            ...     print(f"Duplicate: {exampleOps.GetGuid(dup)}")
            Original: 12345678-1234-1234-1234-123456789abc
            Duplicate: 87654321-4321-4321-4321-cba987654321
            ...
            ...     # Deep duplicate (includes translations)
            ...     deep_dup = exampleOps.Duplicate(examples[0], deep=True)
            ...     trans = exampleOps.GetTranslation(deep_dup)
            ...     print(f"Translation: {trans}")

        Notes:
            - Factory.Create() automatically generates a new GUID
            - insert_after=True preserves the original example's position/priority
            - Simple properties copied: Example (MultiString), Reference
            - Owned objects (deep=True): TranslationsOC
            - LiftResidue is not copied (import-specific data)
            - MediaFilesOS are not copied (would require file handling)

        See Also:
            Create, Delete, GetGuid
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(item_or_hvo, "item_or_hvo")

        # Get source example and parent.  Cast owner to its concrete
        # ILexSense (the only LCM owner of ILexExample) so ExamplesOS is
        # reachable. Raw source.Owner is typed ICmObject; hasattr(...,
        # "ExamplesOS") returns False there, silently no-opping Duplicate.
        source = self.__GetExampleObject(item_or_hvo)
        parent = self._GetTypedOwner(source)
        if parent is None:
            raise FP_ParameterError("Example has no owning sense")

        # Create new example using factory (auto-generates new GUID)
        factory = self.project.project.ServiceLocator.GetService(ILexExampleSentenceFactory)

        with self._TransactionCM("Duplicate example"):
            duplicate = factory.Create()

            # Determine insertion position
            if insert_after:
                # Insert after source example
                source_index = parent.ExamplesOS.IndexOf(source)
                parent.ExamplesOS.Insert(source_index + 1, duplicate)
            else:
                # Insert at end
                parent.ExamplesOS.Add(duplicate)

            # Copy simple MultiString properties (AFTER adding to parent)
            duplicate.Example.CopyAlternatives(source.Example)

            # Skip copying Reference - it's complex and often empty
            # Reference is an ITsString pointing to the source text location
            # For duplicates, this reference doesn't make sense to copy

            # Handle owned objects if deep=True
            if deep:
                # Duplicate translations
                for translation in source.TranslationsOC:
                    if translation.TypeRA is None:
                        logger.warning(
                            "Duplicate: skipping translation copy -- source TypeRA is null"
                        )
                        continue
                    trans_factory = self.project.project.ServiceLocator.GetService(ICmTranslationFactory)
                    new_trans = trans_factory.Create(duplicate, translation.TypeRA)
                    duplicate.TranslationsOC.Add(new_trans)

                    # Copy translation properties
                    new_trans.Translation.CopyAlternatives(translation.Translation)

            return duplicate

    # ========== SYNC INTEGRATION METHODS ==========

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Get all syncable properties of an example sentence for comparison.

        Args:
            item: The ILexExampleSentence object.

        Returns:
            dict: Dictionary mapping property names to their values:
                - MultiString properties as dicts {ws: text}
                - Atomic properties as simple values
                - Does NOT include Owning Sequence (OS) properties (translations)
        """
        props = {}

        # MultiString properties
        # Example - the example sentence in various writing systems
        example_dict = {}
        if hasattr(item, "Example"):
            for ws_def in self.project.WritingSystems.GetAll():
                text = normalize_text(
                    ITsString(item.Example.get_String(ws_def.Handle)).Text
                )
                if text:
                    example_dict[ws_def.Id] = text
        props["Example"] = example_dict

        # Reference - ILexExampleSentence.Reference is ITsString (single-string),
        # NOT IMultiString. Treating it as IMultiString with a WS-handle loop would
        # raise AttributeError at runtime because ITsString has no get_String(handle)
        # method. Use _ReadTsString instead. (P0 bug fix -- Category 8 same-name
        # field: ILexEtymology.Reference is IMultiString, ILexExampleSentence.Reference
        # is ITsString.)
        if hasattr(item, "Reference"):
            props["Reference"] = self._ReadTsString(item.Reference)
        else:
            props["Reference"] = ""

        # TranslationsOC - owned collection of ICmTranslation objects.
        # Each ICmTranslation has:
        #   Translation: IMultiString (text per writing system)
        #   TypeRA: ICmPossibility (e.g. "Free translation") -- serialized as GUID string
        # Serialize as a list of dicts (order-preserving, matching TranslationsOC order).
        translations_list = []
        if hasattr(item, "TranslationsOC"):
            for trans in item.TranslationsOC:
                trans_text_dict = {}
                if hasattr(trans, "Translation"):
                    for ws_def in self.project.WritingSystems.GetAll():
                        text = normalize_text(
                            ITsString(trans.Translation.get_String(ws_def.Handle)).Text
                        )
                        if text:
                            trans_text_dict[ws_def.Id] = text
                type_guid = None
                if hasattr(trans, "TypeRA") and trans.TypeRA is not None:
                    type_guid = str(trans.TypeRA.Guid)
                translations_list.append({
                    "Translation": trans_text_dict,
                    "TypeRA": type_guid,
                })
        props["TranslationsOC"] = translations_list

        return props

    @OperationsMethod
    def ApplySyncableProperties(self, item, props, ws_map=None, fill_gaps=False):
        """
        Apply a syncable-properties dict onto an ILexExampleSentence item.

        Extends the base implementation to handle:
        - Reference: ITsString (not IMultiString) -- set via default analysis WS.
        - TranslationsOC: owned collection of ICmTranslation objects. Strategy is
          clear-and-rebuild (v1 choice: simpler than index-based reconciliation;
          acceptable because the diff layer identifies examples by GUID and replaces
          them as a unit). A comment marks where v2 could do smarter merging.

        Args:
            item: Target ILexExampleSentence (must already exist in target project).
            props: dict produced by GetSyncableProperties on a source example.
            ws_map: Optional source->target writing-system Id mapping.
            fill_gaps (bool): When True, only write fields whose current target
                value is empty/absent; passed through to BaseOperations.
                Reference/TranslationsOC are always applied regardless (domain
                has not ruled on them).
        """
        import logging as _logging
        _log = _logging.getLogger(__name__)

        self._EnsureWriteEnabled()

        _special_fields = ("Reference", "TranslationsOC")
        remaining_props = {}
        special_props = {}
        for k, v in props.items():
            if k in _special_fields:
                special_props[k] = v
            else:
                remaining_props[k] = v

        with self._TransactionCM("Apply example sync properties"):
            # Apply plain / multistring fields via base class.
            super().ApplySyncableProperties(item, remaining_props, ws_map=ws_map, fill_gaps=fill_gaps)

            # --- Reference (ITsString, single-string) ---
            if "Reference" in special_props:
                ref_text = special_props["Reference"] or ""
                if ref_text:
                    ws_handle = self.project.project.DefaultAnalWs
                    item.Reference = TsStringUtils.MakeString(ref_text, ws_handle)

            # --- TranslationsOC (owned collection -- clear-and-rebuild) ---
            # V1 choice: clear all existing ICmTranslation objects and recreate from
            # the serialized list. This is safe for cross-project sync where the target
            # example was just created. A future v2 could reconcile by TypeRA GUID to
            # preserve locally-authored translations not present in the source.
            if "TranslationsOC" in special_props:
                translations_data = special_props["TranslationsOC"]
                if not isinstance(translations_data, list):
                    _log.warning(
                        "[WARN] ApplySyncableProperties: TranslationsOC expected list, "
                        "got %s -- skipping", type(translations_data).__name__
                    )
                else:
                    # Resolve target writing systems once.
                    target_ws_by_id = {
                        ws.Id: ws.Handle
                        for ws in self.project.WritingSystems.GetAll()
                    }

                    # Build a GUID->object map for the translation type possibility list.
                    # Translation types live in LangProject.TranslationTagsOA.
                    type_guid_map = {}
                    try:
                        for tt in self.project.lp.TranslationTagsOA.PossibilitiesOS:
                            type_guid_map[str(tt.Guid)] = tt
                    except Exception as exc:
                        _log.warning(
                            "[WARN] ApplySyncableProperties: could not enumerate "
                            "TranslationTagsOA: %s", exc
                        )

                    # Clear existing translations on the target example.
                    item.TranslationsOC.Clear()

                    for trans_dict in translations_data:
                        if not isinstance(trans_dict, dict):
                            _log.warning(
                                "[WARN] ApplySyncableProperties: TranslationsOC entry "
                                "is not a dict -- skipped"
                            )
                            continue

                        # Resolve TypeRA by GUID before Create() -- factory requires a non-null possibility.
                        type_guid_str = trans_dict.get("TypeRA")
                        type_obj = None
                        if type_guid_str:
                            type_obj = type_guid_map.get(type_guid_str)
                            if type_obj is None:
                                _log.warning(
                                    "[WARN] ApplySyncableProperties: TranslationsOC "
                                    "TypeRA GUID %s not found in target project's "
                                    "TranslationTagsOA -- translation skipped",
                                    type_guid_str
                                )
                        if type_obj is None:
                            _log.warning(
                                "[WARN] ApplySyncableProperties: TranslationsOC entry "
                                "has no resolvable TypeRA -- translation skipped"
                            )
                            continue

                        # Create a new ICmTranslation owned by this example.
                        new_trans = self.project.project.ServiceLocator.GetService(
                            ICmTranslationFactory
                        ).Create(item, type_obj)
                        item.TranslationsOC.Add(new_trans)

                        # Set Translation IMultiString per writing system.
                        trans_text_dict = trans_dict.get("Translation", {})
                        for src_ws_id, text in trans_text_dict.items():
                            if not text:
                                continue
                            tgt_ws_id = (
                                ws_map.get(src_ws_id, src_ws_id) if ws_map else src_ws_id
                            )
                            tgt_handle = target_ws_by_id.get(tgt_ws_id)
                            if tgt_handle is None:
                                continue
                            new_trans.Translation.set_String(
                                tgt_handle,
                                TsStringUtils.MakeString(text, tgt_handle)
                            )

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two example sentences and return their differences.

        Args:
            item1: The first ILexExampleSentence object.
            item2: The second ILexExampleSentence object.
            ops1: Optional ExampleOperations instance for item1.
            ops2: Optional ExampleOperations instance for item2.

        Returns:
            tuple: (is_different, differences_dict)
        """
        ops1 = ops1 or self
        ops2 = ops2 or self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        differences = {}
        all_keys = set(props1.keys()) | set(props2.keys())
        for key in all_keys:
            val1 = props1.get(key)
            val2 = props2.get(key)
            if val1 != val2:
                differences[key] = (val1, val2)

        is_different = len(differences) > 0
        return is_different, differences

    @OperationsMethod
    def Reorder(self, sense_or_hvo, example_list):
        """
        Reorder the examples for a sense.

        Args:
            sense_or_hvo: The ILexSense object or HVO.
            example_list: List of ILexExampleSentence objects or HVOs in desired order.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If sense_or_hvo or example_list is None.
            FP_ParameterError: If example_list doesn't contain all examples or
                contains examples not belonging to this sense.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> # Reverse the order
            >>> exampleOps.Reorder(sense, reversed(examples))

        Notes:
            - All examples must be provided in the new order
            - Examples not in the list will be removed
            - All examples must belong to the specified sense
            - This is useful for organizing examples by frequency or importance

        See Also:
            GetAll, Create
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(sense_or_hvo, "sense_or_hvo")
        self._ValidateParam(example_list, "example_list")

        sense = self.__GetSenseObject(sense_or_hvo)

        # Convert to list if it's an iterator
        example_list = list(example_list)

        # Resolve all to objects
        examples = [self.__GetExampleObject(ex) for ex in example_list]

        # Verify all examples belong to this sense
        current_examples = set(sense.ExamplesOS)
        new_examples = set(examples)

        if current_examples != new_examples:
            raise FP_ParameterError("Example list must contain exactly the same examples as the sense")

        with self._TransactionCM("Reorder examples"):
            # Clear and re-add in new order
            sense.ExamplesOS.Clear()
            for example in examples:
                sense.ExamplesOS.Add(example)

    @OperationsMethod
    def GetExample(self, example_or_hvo, wsHandle=None):
        """
        Get the example text of an example sentence.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Returns:
            str: The example text, or empty string if not set.

        Raises:
            FP_NullParameterError: If example_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     text = exampleOps.GetExample(examples[0])
            ...     print(text)
            The dog ran quickly.

            >>> # Get in specific writing system
            >>> text_fr = exampleOps.GetExample(examples[0],
            ...                                   project.WSHandle('fr'))

        Notes:
            - Returns empty string if text not set in specified writing system
            - Use vernacular writing system for example sentences
            - Different writing systems can contain different text

        See Also:
            SetExample, Create
        """
        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)
        wsHandle = self.__WSHandleVern(wsHandle)

        text = ITsString(example.Example.get_String(wsHandle)).Text
        # _NormalizeMultiString turns "***" into "" but leaves None alone.
        # GetExample's docstring promises a str (empty when unset), so coerce
        # the None-on-unset case to "" as well -- callers do not expect to
        # have to .startswith()-guard the return value.
        return self._NormalizeMultiString(text) or ""

    @OperationsMethod
    def SetExample(self, example_or_hvo, text, wsHandle=None):
        """
        Set the example text of an example sentence.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.
            text (str): The new example text.
            wsHandle: Optional writing system handle. Defaults to vernacular WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If example_or_hvo or text is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     exampleOps.SetExample(examples[0], "The cat ran quickly.")
            ...     print(exampleOps.GetExample(examples[0]))
            The cat ran quickly.

        Notes:
            - Empty string is allowed (clears the text)
            - Use different writing systems for different representations
            - Does not affect translations (update those separately)

        See Also:
            GetExample, Create, SetTranslation
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(example_or_hvo, "example_or_hvo")
        self._ValidateParam(text, "text")

        example = self.__GetExampleObject(example_or_hvo)
        wsHandle = self.__WSHandleVern(wsHandle)

        mkstr = TsStringUtils.MakeString(text, wsHandle)
        example.Example.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetTranslations(self, example_or_hvo):
        """
        Get all translation objects for an example sentence.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.

        Returns:
            list: List of ICmTranslation objects (empty list if none).

        Raises:
            FP_NullParameterError: If example_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     translations = exampleOps.GetTranslations(examples[0])
            ...     for trans in translations:
            ...         wsHandle = project.project.DefaultAnalWs
            ...         text = ITsString(trans.Translation.get_String(wsHandle)).Text
            ...         print(f"Translation: {text}")
            Translation: The dog ran quickly.
            Translation: El perro corrió rápidamente.

        Notes:
            - Returns ICmTranslation objects, not strings
            - To get text, use GetTranslation() for a specific WS
            - Translations are in analysis writing systems
            - Multiple translations can exist for different languages

        See Also:
            GetTranslation, SetTranslation, AddTranslation
        """
        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)
        return list(example.TranslationsOC)

    @OperationsMethod
    def GetTranslation(self, example_or_hvo, wsHandle=None):
        """
        Get the translation text for a specific writing system.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The translation text, or empty string if not set.

        Raises:
            FP_NullParameterError: If example_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     trans = exampleOps.GetTranslation(examples[0])
            ...     print(trans)
            The dog ran quickly.

            >>> # Get Spanish translation
            >>> trans_es = exampleOps.GetTranslation(examples[0],
            ...                                       project.WSHandle('es'))
            >>> print(trans_es)
            El perro corrió rápidamente.

        Notes:
            - Returns empty string if no translation in specified WS
            - Use analysis writing system for translations
            - Searches through all translation objects for matching WS
            - Returns the first match found

        See Also:
            SetTranslation, GetTranslations, GetExample
        """
        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Search through translations for this writing system
        for translation in example.TranslationsOC:
            text = ITsString(translation.Translation.get_String(wsHandle)).Text
            if text:
                return text

        return ""

    @OperationsMethod
    def SetTranslation(self, example_or_hvo, text, wsHandle=None):
        """
        Set the translation text for a specific writing system.

        Creates a translation object if one doesn't exist for the writing system.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.
            text (str): The translation text.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If example_or_hvo or text is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> example = exampleOps.Create(sense, "El gato durmió.")
            >>> exampleOps.SetTranslation(example, "The cat slept.")
            >>> print(exampleOps.GetTranslation(example))
            The cat slept.

            >>> # Set French translation
            >>> exampleOps.SetTranslation(example, "Le chat a dormi.",
            ...                            project.WSHandle('fr'))

        Notes:
            - Creates new translation object if needed
            - Updates existing translation if already present
            - Use analysis writing system for translations
            - Empty string is allowed (clears the translation)

        See Also:
            GetTranslation, AddTranslation, RemoveTranslation
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(example_or_hvo, "example_or_hvo")
        self._ValidateParam(text, "text")

        example = self.__GetExampleObject(example_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Find existing translation for this WS or create new one
        translation = None
        for trans in example.TranslationsOC:
            existing_text = ITsString(trans.Translation.get_String(wsHandle)).Text
            if existing_text:  # This translation has content in our WS
                translation = trans
                break

        with self._TransactionCM("Set translation"):
            if translation is None:
                # Create new translation
                factory = self.project.project.ServiceLocator.GetService(ICmTranslationFactory)
                translation = factory.Create()
                example.TranslationsOC.Add(translation)

            # Set the translation text
            mkstr = TsStringUtils.MakeString(text, wsHandle)
            translation.Translation.set_String(wsHandle, mkstr)

    @OperationsMethod
    def AddTranslation(self, example_or_hvo, text, wsHandle=None):
        """
        Add a new translation to an example sentence.

        This is an alias for SetTranslation() - both create or update translations.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.
            text (str): The translation text.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If example_or_hvo or text is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> example = exampleOps.Create(sense, "Le chien a couru.")
            >>> exampleOps.AddTranslation(example, "The dog ran.")
            >>> exampleOps.AddTranslation(example, "El perro corrió.",
            ...                            project.WSHandle('es'))

        Notes:
            - Identical to SetTranslation() in functionality
            - Creates new translation if needed, updates if exists
            - Use for semantic clarity when adding first translation

        See Also:
            SetTranslation, GetTranslation, RemoveTranslation
        """
        self._EnsureWriteEnabled()

        self.SetTranslation(example_or_hvo, text, wsHandle)

    @OperationsMethod
    def RemoveTranslation(self, example_or_hvo, wsHandle=None):
        """
        Remove the translation for a specific writing system.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If example_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     # Remove English translation
            ...     exampleOps.RemoveTranslation(examples[0])
            ...     # Remove Spanish translation
            ...     exampleOps.RemoveTranslation(examples[0],
            ...                                   project.WSHandle('es'))

        Notes:
            - Sets translation text to empty string for the WS
            - Does not remove the translation object itself
            - If translation has content in other WSs, those are preserved
            - No error if translation doesn't exist

        See Also:
            SetTranslation, AddTranslation, GetTranslation
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)
        wsHandle = self.__WSHandle(wsHandle)

        # Find and clear translation for this WS
        for translation in example.TranslationsOC:
            text = ITsString(translation.Translation.get_String(wsHandle)).Text
            if text:
                translation.Translation.set_String(wsHandle, None)
                break

    @OperationsMethod
    def GetReference(self, example_or_hvo):
        """
        Get the reference (source citation) for an example sentence.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.

        Returns:
            str: The reference text, or empty string if not set.

        Raises:
            FP_NullParameterError: If example_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     ref = exampleOps.GetReference(examples[0])
            ...     print(f"Reference: {ref}")
            Reference: Genesis 1:1

        Notes:
            - Reference can be a corpus citation, biblical reference, etc.
            - Format is free-form text
            - Commonly used formats: "Book Chapter:Verse", "Corpus ID"
            - Returns empty string if no reference set

        See Also:
            SetReference
        """
        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)

        if hasattr(example, "Reference") and example.Reference:
            ref = ITsString(example.Reference).Text
            return self._NormalizeMultiString(ref)
        return ""

    @OperationsMethod
    def SetReference(self, example_or_hvo, reference_text):
        """
        Set the reference (source citation) for an example sentence.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.
            reference_text (str): The reference text (e.g., "Genesis 1:1").

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If example_or_hvo or reference_text is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> example = exampleOps.Create(sense, "In the beginning...")
            >>> exampleOps.SetReference(example, "Genesis 1:1")
            >>> print(exampleOps.GetReference(example))
            Genesis 1:1

            >>> # Corpus reference
            >>> exampleOps.SetReference(example, "Corpus A, Text 3, Line 12")

        Notes:
            - Reference format is free-form
            - Common formats: biblical citations, corpus IDs, page numbers
            - Empty string is allowed (clears the reference)
            - Use consistent format within a project

        See Also:
            GetReference
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(example_or_hvo, "example_or_hvo")
        self._ValidateParam(reference_text, "reference_text")

        example = self.__GetExampleObject(example_or_hvo)
        wsHandle = self.project.project.DefaultAnalWs

        mkstr = TsStringUtils.MakeString(reference_text, wsHandle)
        example.Reference = mkstr

    @OperationsMethod
    def GetMediaFiles(self, example_or_hvo):
        """
        Get all media files associated with an example sentence.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.

        Returns:
            list: List of media file objects (empty list if none).

        Raises:
            FP_NullParameterError: If example_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     media = exampleOps.GetMediaFiles(examples[0])
            ...     print(f"Media count: {len(media)}")
            Media count: 2

        Notes:
            - Returns media file objects from MediaFilesOS collection
            - Media files can be audio, video, or image files
            - File objects contain path and metadata information
            - Empty list if no media files attached

        See Also:
            GetMediaCount
        """
        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)

        if hasattr(example, "MediaFilesOS"):
            return list(example.MediaFilesOS)
        return []

    @OperationsMethod
    def GetMediaCount(self, example_or_hvo):
        """
        Get the count of media files associated with an example sentence.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.

        Returns:
            int: The number of media files.

        Raises:
            FP_NullParameterError: If example_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     count = exampleOps.GetMediaCount(examples[0])
            ...     print(f"This example has {count} media files")
            This example has 2 media files

        Notes:
            - More efficient than len(GetMediaFiles()) for just counting
            - Returns 0 if no media files attached
            - Includes all media types (audio, video, images)

        See Also:
            GetMediaFiles
        """
        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)

        if hasattr(example, "MediaFilesOS"):
            return example.MediaFilesOS.Count
        return 0

    @OperationsMethod
    def AddMediaFile(self, example_or_hvo, file_path, label=None):
        """
        Add a media file (typically audio) to an example sentence.

        Copies the file to the project's LinkedFiles directory and creates
        a media reference linked to the example.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.
            file_path (str): Path to the external media file to import.
            label (str, optional): Descriptive label for the media file.

        Returns:
            ICmFile: The created media file object with proper path.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If example_or_hvo or file_path is None.
            FP_ParameterError: If file_path is empty or file doesn't exist.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> example = exampleOps.Create(sense, "The dog barked loudly.")
            >>> # Add audio recording
            >>> media = exampleOps.AddMediaFile(
            ...     example,
            ...     "/path/to/audio.wav",
            ...     label="Native speaker pronunciation"
            ... )
            >>> print(f"Added media file")
            Added media file

            >>> # Verify the media was added
            >>> count = exampleOps.GetMediaCount(example)
            >>> print(f"Example now has {count} media file(s)")
            Example now has 1 media file(s)

        Notes:
            - File is copied to LinkedFiles/AudioVisual directory
            - Unique filename generated if collision occurs (audio_1.wav, etc.)
            - Creates ICmFile object with proper LinkedFiles path
            - Supported formats: WAV, MP3, OGG, WMA (audio), MP4, AVI (video)
            - Multiple media files can be added to one example
            - Label is stored in the default analysis writing system

        See Also:
            RemoveMediaFile, MoveMediaFile, GetMediaFiles, GetMediaCount
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(example_or_hvo, "example_or_hvo")
        self._ValidateParam(file_path, "file_path")

        self._ValidateStringNotEmpty(file_path, "file_path")

        example = self.__GetExampleObject(example_or_hvo)

        with self._TransactionCM("Add media file"):
            # Use MediaOperations to properly copy file and create ICmFile
            # Copy file to project and get ICmFile reference
            media_file = self.project.Media.CopyToProject(file_path, internal_subdir="AudioVisual", label=label)

            # Add to example's media collection
            if hasattr(example, "MediaFilesOS"):
                example.MediaFilesOS.Add(media_file)
            else:
                raise FP_ParameterError("Example does not support media files")

            return media_file

    @OperationsMethod
    def RemoveMediaFile(self, example_or_hvo, media_or_hvo):
        """
        Remove a media file from an example sentence.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.
            media_or_hvo: The ICmFile object or HVO to remove.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If example_or_hvo or media_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     media_files = exampleOps.GetMediaFiles(examples[0])
            ...     if media_files:
            ...         exampleOps.RemoveMediaFile(examples[0], media_files[0])
            ...         print("Media file removed")
            Media file removed

        Notes:
            - Removes the media file reference from the example
            - Does NOT delete the actual file from disk
            - The media file object is deleted from the database
            - Cannot be undone
            - If you need to delete the physical file, use project.Media methods

        Warning:
            - This operation cannot be undone
            - The media file reference is permanently removed
            - Other examples may still reference the same physical file

        See Also:
            AddMediaFile, MoveMediaFile, GetMediaFiles
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(example_or_hvo, "example_or_hvo")
        self._ValidateParam(media_or_hvo, "media_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)

        # Resolve media object
        if isinstance(media_or_hvo, int):
            media = self.project.Object(media_or_hvo)
        else:
            media = media_or_hvo

        # Remove from collection
        if hasattr(example, "MediaFilesOS"):
            example.MediaFilesOS.Remove(media)

    @OperationsMethod
    def MoveMediaFile(self, media, from_example_or_hvo, to_example_or_hvo):
        """
        Move a media file from one example sentence to another example sentence.

        This is useful when reorganizing examples or moving audio recordings to the
        correct example sentence.

        Args:
            media: ICmFile object to move.
            from_example_or_hvo: Source ILexExampleSentence object or HVO.
            to_example_or_hvo: Destination ILexExampleSentence object or HVO.

        Returns:
            bool: True if media was moved, False if source and destination are same.

        Raises:
            FP_ReadOnlyError: If the project is not opened with write enabled.
            FP_NullParameterError: If any parameter is None.
            FP_ParameterError: If media not in source example's collection.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> # Get two examples from the sense
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if len(examples) >= 2:
            ...     example1 = examples[0]
            ...     example2 = examples[1]
            ...
            ...     # Get media from first example
            ...     media_files = exampleOps.GetMediaFiles(example1)
            ...     if media_files:
            ...         # Move the first audio file
            ...         moved = exampleOps.MoveMediaFile(media_files[0], example1, example2)
            ...         if moved:
            ...             print("Media file moved successfully")
            ...
            ...         # Verify the move
            ...         count1 = exampleOps.GetMediaCount(example1)
            ...         count2 = exampleOps.GetMediaCount(example2)
            ...         print(f"Example 1 media: {count1}")
            ...         print(f"Example 2 media: {count2}")
            Media file moved successfully
            Example 1 media: 0
            Example 2 media: 1

            >>> # Can also move between different senses
            >>> other_sense = entry.SensesOS[1] if entry.SensesOS.Count > 1 else None
            >>> if other_sense:
            ...     other_examples = list(exampleOps.GetAll(other_sense))
            ...     if other_examples:
            ...         other_example = other_examples[0]
            ...         media_files = exampleOps.GetMediaFiles(example2)
            ...         if media_files:
            ...             exampleOps.MoveMediaFile(media_files[0], example2, other_example)

        Notes:
            - Media is removed from source MediaFilesOS and added to destination
            - File reference and description are preserved
            - The physical media file is NOT moved/copied
            - Cannot move to the same example (returns False)
            - Media object's GUID remains the same
            - No changes are made to the physical file location

        Warning:
            - Moving media between different sense's examples is allowed
            - Ensure the media is semantically appropriate for the target example
            - The media will be associated with the new example
            - Consider adding/updating labels to clarify context after moving

        See Also:
            AddMediaFile, RemoveMediaFile, GetMediaFiles, GetMediaCount
        """
        self._EnsureWriteEnabled()

        self._ValidateParam(media, "media")
        self._ValidateParam(from_example_or_hvo, "from_example_or_hvo")
        self._ValidateParam(to_example_or_hvo, "to_example_or_hvo")

        from_example = self.__GetExampleObject(from_example_or_hvo)
        to_example = self.__GetExampleObject(to_example_or_hvo)

        # Can't move to same example
        if from_example == to_example:
            logger.warning("Source and destination are the same example")
            return False

        # Verify media is in source collection
        if not hasattr(from_example, "MediaFilesOS"):
            raise FP_ParameterError("Source example does not support media files")

        if media not in from_example.MediaFilesOS:
            raise FP_ParameterError("Media file not found in source example's media collection")

        # Verify destination supports media
        if not hasattr(to_example, "MediaFilesOS"):
            raise FP_ParameterError("Destination example does not support media files")

        with self._TransactionCM("Move media file"):
            # Move the media (remove from source, add to destination)
            from_example.MediaFilesOS.Remove(media)
            to_example.MediaFilesOS.Add(media)

            logger.info(f"Moved media from example {from_example.Guid} to example {to_example.Guid}")

            return True

    @OperationsMethod
    def GetOwningSense(self, example_or_hvo):
        """
        Get the lexical sense that owns this example sentence.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.

        Returns:
            ILexSense: The owning sense object.

        Raises:
            FP_NullParameterError: If example_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     owner = exampleOps.GetOwningSense(examples[0])
            ...     gloss = project.LexiconGetSenseGloss(owner)
            ...     print(f"Example belongs to sense: {gloss}")
            Example belongs to sense: run (verb)

        Notes:
            - Returns the ILexSense that contains this example
            - Useful for navigation and context
            - Examples always have exactly one owning sense

        See Also:
            GetAll, Create
        """
        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)
        return ILexSense(example.Owner)

    @OperationsMethod
    def GetGuid(self, example_or_hvo):
        """
        Get the GUID of an example sentence.

        Args:
            example_or_hvo: The ILexExampleSentence object or HVO.

        Returns:
            System.Guid: The GUID of the example.

        Raises:
            FP_NullParameterError: If example_or_hvo is None.

        Example:
            >>> exampleOps = ExampleOperations(project)
            >>> entry = project.LexiconAllEntries().__next__()
            >>> sense = entry.SensesOS[0]
            >>> examples = list(exampleOps.GetAll(sense))
            >>> if examples:
            ...     guid = exampleOps.GetGuid(examples[0])
            ...     print(f"Example GUID: {guid}")
            Example GUID: 12345678-1234-1234-1234-123456789abc

        Notes:
            - GUIDs are globally unique identifiers
            - Persistent across project versions
            - Use for external references and tracking
            - Same GUID across different copies of the project

        See Also:
            GetOwningSense
        """
        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)
        return example.Guid

    # --- Additional Properties ---

    @OperationsMethod
    def GetLiteralTranslation(self, example_or_hvo, wsHandle=None):
        """
        Get the literal translation of an example sentence.

        Args:
            example_or_hvo: Either an ILexExampleSentence object or its HVO
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Returns:
            str: The literal translation text

        Example:
            >>> sense = list(project.Senses.GetAll())[0]
            >>> examples = project.Examples.GetAll(sense)
            >>> if examples:
            ...     lit_trans = project.Examples.GetLiteralTranslation(examples[0])
            ...     print(lit_trans)
        """
        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        return self._NormalizeMultiString(ITsString(example.LiteralTranslation.get_String(wsHandle)).Text)

    @OperationsMethod
    def SetLiteralTranslation(self, example_or_hvo, text, wsHandle=None):
        """
        Set the literal translation of an example sentence.

        Args:
            example_or_hvo: Either an ILexExampleSentence object or its HVO
            text (str): The literal translation text
            wsHandle: Optional writing system handle. Defaults to analysis WS.

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If example_or_hvo or text is None

        Example:
            >>> sense = list(project.Senses.GetAll())[0]
            >>> examples = project.Examples.GetAll(sense)
            >>> if examples:
            ...     project.Examples.SetLiteralTranslation(examples[0], "word-for-word translation")
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(example_or_hvo, "example_or_hvo")
        self._ValidateParam(text, "text")

        example = self.__GetExampleObject(example_or_hvo)
        wsHandle = self.__WSHandleAnalysis(wsHandle)

        mkstr = TsStringUtils.MakeString(text, wsHandle)
        example.LiteralTranslation.set_String(wsHandle, mkstr)

    @OperationsMethod
    def GetDoNotPublishIn(self, example_or_hvo):
        """
        Get the publications this example should not be published in.

        Args:
            example_or_hvo: Either an ILexExampleSentence object or its HVO

        Returns:
            list: List of publication names

        Example:
            >>> sense = list(project.Senses.GetAll())[0]
            >>> examples = project.Examples.GetAll(sense)
            >>> if examples:
            ...     pubs = project.Examples.GetDoNotPublishIn(examples[0])
            ...     print(pubs)
        """
        self._ValidateParam(example_or_hvo, "example_or_hvo")

        example = self.__GetExampleObject(example_or_hvo)

        result = []
        for pub in example.DoNotPublishInRC:
            name = normalize_text(pub.Name.BestAnalysisAlternative.Text) if pub.Name else str(pub.Guid)
            result.append(name)
        return result

    @OperationsMethod
    def AddDoNotPublishIn(self, example_or_hvo, publication):
        """
        Add a publication to exclude this example from.

        Args:
            example_or_hvo: Either an ILexExampleSentence object or its HVO
            publication: Publication name (str) or ICmPossibility object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If example_or_hvo or publication is None
            FP_ParameterError: If publication name not found
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(example_or_hvo, "example_or_hvo")
        self._ValidateParam(publication, "publication")

        example = self.__GetExampleObject(example_or_hvo)

        # Find publication object if string provided
        if isinstance(publication, str):
            pub_obj = self.project.Publications.Find(publication)
            if not pub_obj:
                raise FP_ParameterError(f"Publication '{publication}' not found")
            publication = pub_obj

        if publication not in example.DoNotPublishInRC:
            example.DoNotPublishInRC.Add(publication)

    @OperationsMethod
    def RemoveDoNotPublishIn(self, example_or_hvo, publication):
        """
        Remove a publication from the exclude list for this example.

        Args:
            example_or_hvo: Either an ILexExampleSentence object or its HVO
            publication: Publication name (str) or ICmPossibility object

        Raises:
            FP_ReadOnlyError: If project is not opened with write enabled
            FP_NullParameterError: If example_or_hvo or publication is None
            FP_ParameterError: If publication name not found
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(example_or_hvo, "example_or_hvo")
        self._ValidateParam(publication, "publication")

        example = self.__GetExampleObject(example_or_hvo)

        # Find publication object if string provided
        if isinstance(publication, str):
            pub_obj = self.project.Publications.Find(publication)
            if not pub_obj:
                raise FP_ParameterError(f"Publication '{publication}' not found")
            publication = pub_obj

        if publication in example.DoNotPublishInRC:
            example.DoNotPublishInRC.Remove(publication)

    # --- Private Helper Methods ---

    def __GetSenseObject(self, sense_or_hvo):
        """
        Resolve HVO or object to ILexSense.

        Args:
            sense_or_hvo: Either an ILexSense object or an HVO (int).

        Returns:
            ILexSense: The resolved sense object.
        """
        if isinstance(sense_or_hvo, int):
            return self.project.Object(sense_or_hvo)
        return sense_or_hvo

    def __GetExampleObject(self, example_or_hvo):
        """
        Resolve HVO or object to ILexExampleSentence.

        Args:
            example_or_hvo: Either an ILexExampleSentence object or an HVO (int).

        Returns:
            ILexExampleSentence: The resolved example object.
        """
        if isinstance(example_or_hvo, int):
            return self.project.Object(example_or_hvo)
        return example_or_hvo

    def __WSHandle(self, wsHandle):
        """
        Get writing system handle, defaulting to analysis WS for translations.

        Args:
            wsHandle: Optional writing system handle.

        Returns:
            int: The writing system handle.
        """
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultAnalWs)

    def __WSHandleVern(self, wsHandle):
        """
        Get writing system handle, defaulting to vernacular WS for example text.

        Args:
            wsHandle: Optional writing system handle.

        Returns:
            int: The writing system handle.
        """
        if wsHandle is None:
            return self.project.project.DefaultVernWs
        return self.project._FLExProject__WSHandle(wsHandle, self.project.project.DefaultVernWs)
