#
#   StratumOperations.py
#
#   Class: StratumOperations
#          Stratum operations for FieldWorks Language Explorer projects
#          via SIL Language and Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

# Import BaseOperations parent class
from ..BaseOperations import BaseOperations, OperationsMethod, wrap_enumerable

# Import FLEx LCM types
from SIL.LCModel import (
    IMoStratum,
    IMoStratumFactory,
)
from SIL.LCModel.Core.KernelInterfaces import ITsString
from SIL.LCModel.Core.Text import TsStringUtils

# Import flexlibs exceptions
from ..FLExProject import (
    FP_ParameterError,
)

# Import string utilities
from ..Shared.string_utils import normalize_match_key, normalize_text

import logging
logger = logging.getLogger(__name__)


class StratumOperations(BaseOperations):
    """
    This class provides operations for managing morphological strata in a
    FieldWorks project.

    Strata are ordered layers in the morphology/phonology that organise
    affix templates, MSAs, compound rules, and phonological rules. They
    live on ``LangProject.MorphologicalDataOA.StrataOS`` and are referenced
    via ``StratumRA`` from ``IMoInflAffixTemplate``, ``IMoDerivAffMsa``,
    ``IMoStemMsa``, ``IMoCompoundRule`` and ``IPhPhonologicalRule``.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("my project", writeEnabled=True)

        # Enumerate strata
        for stratum in project.Strata.GetAll():
            name = project.Strata.GetName(stratum)
            print(name)

        # Create a new stratum
        new_stratum = project.Strata.Create("Stem", abbreviation="stem")

        project.CloseProject()
    """

    def __init__(self, project):
        super().__init__(project)

    def _GetSequence(self, parent):
        """Reordering sequence target for strata.

        Args:
            parent (IMoMorphologicalData): The morphological data object that
                owns ``StrataOS``.

        Returns:
            ILcmOwningSequence: The ``StrataOS`` sequence on *parent*.
        """
        return parent.StrataOS

    # ----- helpers -----

    def __Container(self):
        morph_data = self.project.lp.MorphologicalDataOA
        if morph_data is None:
            raise FP_ParameterError(
                "No MorphologicalDataOA on the language project"
            )
        return morph_data.StrataOS

    def __ResolveObject(self, stratum_or_hvo):
        if isinstance(stratum_or_hvo, int):
            return self.project.Object(stratum_or_hvo)
        return stratum_or_hvo

    def __WSHandle(self, wsHandle):
        if wsHandle is None:
            return self.project.project.DefaultAnalWs
        return self.project._FLExProject__WSHandle(
            wsHandle, self.project.project.DefaultAnalWs
        )

    # ----- CRUD -----

    @wrap_enumerable
    @OperationsMethod
    def GetAll(self):
        """
        Yield every stratum in ``MorphologicalDataOA.StrataOS``.

        Returns:
            EnumerableWrapper[IMoStratum]: Each stratum in declaration order.
        """
        morph_data = self.project.lp.MorphologicalDataOA
        if morph_data is None:
            return
        for stratum in list(morph_data.StrataOS):
            yield stratum

    @OperationsMethod
    def Find(self, name, wsHandle=None):
        """
        Find a stratum by name (NFD-normalised casefold match).

        Args:
            name (str): Name to search for.
            wsHandle: Optional WS handle; defaults to analysis WS.

        Returns:
            IMoStratum or None.
        """
        self._ValidateParam(name, "name")

        ws = self.__WSHandle(wsHandle)
        target = normalize_match_key(name)

        morph_data = self.project.lp.MorphologicalDataOA
        if morph_data is None:
            return None

        for stratum in morph_data.StrataOS:
            current = ITsString(stratum.Name.get_String(ws)).Text
            if current and normalize_match_key(current) == target:
                return stratum
        return None

    @OperationsMethod
    def Exists(self, name, wsHandle=None):
        """
        Return True if a stratum with the given name exists.

        Args:
            name (str): Name to search for (NFD-normalised casefold match).
            wsHandle: Optional WS handle; defaults to analysis WS.

        Returns:
            bool: True if a matching stratum is found, False otherwise.
        """
        return self.Find(name, wsHandle) is not None

    @OperationsMethod
    def Create(self, name, abbreviation="", wsHandle=None):
        """
        Create a new stratum and add it to ``StrataOS``.

        Args:
            name (str): Stratum name. Required and non-empty.
            abbreviation (str): Optional abbreviation.
            wsHandle: Optional WS handle; defaults to analysis WS.

        Returns:
            IMoStratum: The newly created stratum.

        Raises:
            FP_ReadOnlyError: If the project is not writable.
            FP_NullParameterError: If ``name`` is None.
            FP_ParameterError: If ``name`` is empty or already used, or if
                ``MorphologicalDataOA`` is missing.

        Note:
            The duplicate-name guard is WS-scoped: two strata whose Name text
            is identical but stored in *different* writing systems will not
            collide and both will be created successfully.
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(name, "name")

        if not name or not name.strip():
            raise FP_ParameterError("Name cannot be empty")

        if self.Exists(name, wsHandle):
            raise FP_ParameterError(f"Stratum '{name}' already exists")

        container = self.__Container()
        ws = self.__WSHandle(wsHandle)

        factory = self.project.project.ServiceLocator.GetService(IMoStratumFactory)

        with self._TransactionCM(f"Create stratum '{name}'"):
            new_stratum = factory.Create()

            # Owner first, then set MultiString properties (LCM MultiString
            # setters can NPE on free-floating objects).
            container.Add(new_stratum)

            new_stratum.Name.set_String(ws, TsStringUtils.MakeString(name, ws))
            if abbreviation:
                new_stratum.Abbreviation.set_String(
                    ws, TsStringUtils.MakeString(abbreviation, ws)
                )

            return new_stratum

    @OperationsMethod
    def Delete(self, stratum_or_hvo):
        """
        Remove a stratum from ``StrataOS``.

        Args:
            stratum_or_hvo: IMoStratum object or HVO integer.

        Warning:
            LCM does not enforce referential integrity when removing a Stratum
            from StrataOS. Inbound StratumRA references on affixes, MSAs,
            compound rules, and phonological rules will become dangling and
            surface later as silent HermitCrab parser failures. The caller is
            responsible for clearing or reassigning all inbound references
            before calling Delete().

        Note:
            Delete silently succeeds if the stratum is not present in the
            container (parity with sibling-class behaviour).
        """
        self._EnsureWriteEnabled()
        self._ValidateParam(stratum_or_hvo, "stratum_or_hvo")

        stratum = self.__ResolveObject(stratum_or_hvo)
        self.__Container().Remove(stratum)

    # ----- accessors -----

    @OperationsMethod
    def GetName(self, stratum_or_hvo, wsHandle=None):
        """Return the stratum's Name in the given WS, or "" if unset."""
        self._ValidateParam(stratum_or_hvo, "stratum_or_hvo")
        stratum = self.__ResolveObject(stratum_or_hvo)
        ws = self.__WSHandle(wsHandle)
        return normalize_text(ITsString(stratum.Name.get_String(ws)).Text) or ""

    @OperationsMethod
    def GetAbbreviation(self, stratum_or_hvo, wsHandle=None):
        """Return the stratum's Abbreviation in the given WS, or ""."""
        self._ValidateParam(stratum_or_hvo, "stratum_or_hvo")
        stratum = self.__ResolveObject(stratum_or_hvo)
        ws = self.__WSHandle(wsHandle)
        return (
            normalize_text(ITsString(stratum.Abbreviation.get_String(ws)).Text) or ""
        )

    @OperationsMethod
    def GetDescription(self, stratum_or_hvo, wsHandle=None):
        """Return the stratum's Description in the given WS, or ""."""
        self._ValidateParam(stratum_or_hvo, "stratum_or_hvo")
        stratum = self.__ResolveObject(stratum_or_hvo)
        ws = self.__WSHandle(wsHandle)
        return (
            normalize_text(ITsString(stratum.Description.get_String(ws)).Text) or ""
        )

    # ----- sync integration -----

    @OperationsMethod
    def GetSyncableProperties(self, item):
        """
        Return a dict of syncable properties for cross-project transfer.

        The default shape covers MultiString fields (Name, Abbreviation,
        Description) keyed by WS Id. Reference collections (PhonemesRS,
        MorphTypesRC) are intentionally omitted: they require
        cross-project object resolution that the dict-driven sync path
        in ``BaseOperations.ApplySyncableProperties`` cannot perform.
        """
        stratum = self.__ResolveObject(item)

        all_ws = {ws.Id: ws.Handle for ws in self.project.WritingSystems.GetAll()}

        props = {}
        for prop_name in ["Name", "Abbreviation", "Description"]:
            prop_obj = getattr(stratum, prop_name, None)
            if prop_obj is None:
                continue
            ws_values = {}
            for ws_id, ws_handle in all_ws.items():
                raw = ITsString(prop_obj.get_String(ws_handle)).Text
                text = normalize_text(raw)
                if text:
                    ws_values[ws_id] = text
            if ws_values:
                props[prop_name] = ws_values

        return props

    @OperationsMethod
    def ApplySyncableProperties(self, item, props, ws_map=None, fill_gaps=False):
        """
        Apply syncable properties produced by GetSyncableProperties.

        Args:
            item: Target IMoStratum object or HVO.
            props (dict): Property dict as returned by GetSyncableProperties.
            ws_map (dict or None): Optional mapping of source WS IDs to target
                WS IDs; passed through to BaseOperations implementation.
            fill_gaps (bool): When True, only write fields whose current target
                value is empty/absent; passed through to BaseOperations.

        Returns:
            None
        """
        return super().ApplySyncableProperties(item, props, ws_map=ws_map, fill_gaps=fill_gaps)

    @OperationsMethod
    def CompareTo(self, item1, item2, ops1=None, ops2=None):
        """
        Compare two strata and return ``(is_different, differences)``.

        Args:
            item1: First IMoStratum object or HVO.
            item2: Second IMoStratum object or HVO.
            ops1 (StratumOperations or None): Operations instance used to read
                *item1*; defaults to ``self``.
            ops2 (StratumOperations or None): Operations instance used to read
                *item2*; defaults to ``self``.

        Returns:
            tuple: ``(is_different, differences)`` where *is_different* is a
            bool and *differences* maps property name to
            ``(value_in_item1, value_in_item2)``.

        Example::

            changed, diffs = project.Strata.CompareTo(stratum_a, stratum_b)
            if changed:
                for prop, (v1, v2) in diffs.items():
                    print(f"{prop}: {v1!r} -> {v2!r}")
        """
        if ops1 is None:
            ops1 = self
        if ops2 is None:
            ops2 = self

        props1 = ops1.GetSyncableProperties(item1)
        props2 = ops2.GetSyncableProperties(item2)

        is_different = False
        differences = {}
        for key in set(props1.keys()) | set(props2.keys()):
            v1 = props1.get(key)
            v2 = props2.get(key)
            if v1 != v2:
                is_different = True
                differences[key] = (v1, v2)
        return (is_different, differences)
