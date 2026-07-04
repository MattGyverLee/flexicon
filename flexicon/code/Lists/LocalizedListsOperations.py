#
#   LocalizedListsOperations.py
#
#   Class: LocalizedListsOperations
#          Localized possibility-list translation-pack import for
#          FieldWorks Language Explorer projects via SIL Language and
#          Culture Model (LCM) API.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import logging
import os
import warnings
from collections import namedtuple

from SIL.LCModel.Application.ApplicationServices import XmlTranslatedLists

from .. import FLExGlobals
from ..BaseOperations import BaseOperations
from ..FLExProject import (
    FP_FileNotFoundError,
    FP_NullParameterError,
    FP_ParameterError,
    FP_ReadOnlyError,
)

logger = logging.getLogger(__name__)


# Reason constants for SkippedWS.reason -- stable surface for callers
# that want to branch on skip cause without string matching.
SKIP_NO_TRANSLATION_PACK = "no shipping translation pack"
SKIP_EMPTY_ICU_LOCALE = "writing system has empty IcuLocale"
SKIP_FILE_NOT_FOUND = "file not found"


SkippedWS = namedtuple("SkippedWS", ("code", "reason"))
SkippedWS.__doc__ = """
One entry in ``ImportLocalizedListsResult.skipped``.

Fields:
    code (str): IcuLocale of the writing system that was skipped, or
        ``"<empty>"`` if the WS had no IcuLocale set.
    reason (str): Short diagnostic explaining why the pack was not
        applied. One of the ``SKIP_*`` module constants, or a more
        specific message for the file-not-found path.
"""


ImportLocalizedListsResult = namedtuple(
    "ImportLocalizedListsResult",
    ("imported", "skipped"),
)
ImportLocalizedListsResult.__doc__ = """
Structured result for ``ImportForAllAnalysisWritingSystems``.

Fields:
    imported (list[str]): IcuLocale codes whose translation pack was
        successfully merged into the project's possibility lists.
    skipped (list[SkippedWS]): One ``SkippedWS(code, reason)`` entry
        per writing system whose pack was not applied. ``code`` is the
        IcuLocale (or ``"<empty>"`` if the WS had no IcuLocale set);
        ``reason`` is a short human-readable diagnostic, generally one
        of the ``SKIP_*`` module constants.
"""


class LocalizedListsOperations(BaseOperations):
    """
    Localized possibility-list translation-pack imports.

    Translation packs ship at
    ``<FWCodeDir>/Templates/LocalizedLists-<lang>.zip`` and carry Name
    and Abbreviation alternatives for the canonical possibility lists
    shared across LangProject and LexDb (SemanticDomains, AnthroList,
    DomainTypes, UsageTypes, RestrictionsList, ...). Items are matched
    by canonical GUID, so the corresponding ``ImportCatalog`` call
    must have already seeded those items in English before
    translations can land.

    Access via ``FLExProject.LocalizedLists`` -- a lazy property.

    Usage::

        from flexlibs2 import FLExProject

        project = FLExProject()
        project.OpenProject("MyProject", writeEnabled=True)

        # Seed canonical SemDom items in English first.
        project.SemanticDomains.ImportCatalog()

        # Layer translations for one specific WS.
        project.LocalizedLists.Import("fr")

        # Or fan out across every enabled analysis WS that has a
        # shipping pack:
        result = project.LocalizedLists.ImportForAllAnalysisWritingSystems()
        print(result.imported)  # e.g. ["en", "fr"]
        for code, reason in result.skipped:
            print(f"  skipped {code}: {reason}")
    """

    def Import(self, language_code, progress=None):
        """
        Import the localized-lists ZIP for a target writing system.

        Wraps ``XmlTranslatedLists.ImportTranslatedListsForWs`` --
        LCM's purpose-built importer for translated lists. Unlike
        ``XmlList.ImportList`` (which appends new items), this method
        merges Name / Abbreviation alternatives onto existing items
        by canonical GUID; no duplicates are created.

        Order matters: call after ``*Operations.ImportCatalog`` has
        seeded canonical items, never before. Translation packs match
        by canonical GUID and silently ignore GUIDs they don't carry,
        so calling Import before the catalog leaves nothing to merge
        onto.

        Args:
            language_code (str): ISO writing-system code identifying
                which LocalizedLists-XX.zip to import. Examples:
                ``"fr"``, ``"es"``, ``"ar"``, ``"zh-CN"``.
            progress: Optional ``SIL.LCModel.Utils.IProgress`` instance
                for progress reporting. ``None`` (default) skips
                reporting.

        Raises:
            FP_ReadOnlyError: If the project is not opened with
                writeEnabled=True.
            FP_NullParameterError: If ``language_code`` is None.
            FP_ParameterError: If ``language_code`` is empty.
            FP_FileNotFoundError: If the corresponding ZIP is not
                found in the FieldWorks Templates directory.

        Example:
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> project.SemanticDomains.ImportCatalog()
            >>> project.LocalizedLists.Import("fr")
            >>> project.LocalizedLists.Import("es")

        Notes:
            Translation packs match by canonical GUID and silently
            ignore GUIDs they don't recognise (and silently leave
            GUIDs they don't carry untranslated). Catalog skew is
            therefore invisible at the call site. The biggest known
            case: ``OCM-Frame.xml`` (loaded via
            ``AnthropologyOperations.ImportFrameCatalog``) carries
            116 GUIDs that ``OCM.xml`` does not. Pairing the wrong
            catalog with the wrong pack leaves part of AnthroListOA
            untranslated without any warning. (issue #82)
        """
        if language_code is None:
            raise FP_NullParameterError()
        if not isinstance(language_code, str) or not language_code.strip():
            raise FP_ParameterError(
                f"language_code must be a non-empty string, got {language_code!r}"
            )
        if not self.project.writeEnabled:
            raise FP_ReadOnlyError()

        templates_dir = self._templates_dir()
        if templates_dir is None:
            raise FP_FileNotFoundError(
                f"LocalizedLists-{language_code}.zip",
                RuntimeError(
                    "FLExGlobals.FWCodeDir is not set; ensure FLEx "
                    "initialisation has run."
                ),
            )
        expected_zip = os.path.join(
            templates_dir, f"LocalizedLists-{language_code}.zip"
        )
        if not os.path.isfile(expected_zip):
            raise FP_FileNotFoundError(
                expected_zip,
                FileNotFoundError(
                    f"LocalizedLists-{language_code}.zip not found in "
                    f"{templates_dir}. Check the language code is a "
                    f"valid ISO writing-system identifier shipped with "
                    f"FieldWorks."
                ),
            )

        with self._TransactionCM(
            f"LocalizedLists.Import({language_code!r})"
        ):
            XmlTranslatedLists.ImportTranslatedListsForWs(
                language_code,
                self.project.project,
                templates_dir,
                progress,
            )

    def ImportForAllAnalysisWritingSystems(self, progress=None):
        """
        Import LocalizedLists translation packs for every enabled
        analysis writing system whose ``IcuLocale`` matches a shipping
        ``LocalizedLists-<IcuLocale>.zip``.

        Iterates ``project.ServiceLocator.WritingSystems
        .CurrentAnalysisWritingSystems`` and dispatches
        ``Import(ws.IcuLocale)`` for each entry. WSes whose
        ``IcuLocale`` does not map to a shipping ZIP are reported in
        the ``skipped`` field of the returned result rather than
        silently ignored.

        Convenience wrapper over ``Import`` that closes the typical
        post-ImportCatalog gap: a user enables an analysis WS
        (Portuguese, French, ...), runs ``SemanticDomains
        .ImportCatalog`` and then expects the catalog items to carry
        translations for every WS they've enabled.

        Important: this does NOT back-fill translations for analysis
        WSes that get enabled AFTER catalog content is added. Re-run
        this method (or call ``Import(code)`` directly) after enabling
        additional analysis WSes.

        Precondition: at least one ``ImportCatalog`` call should have
        run first -- the merger has nothing to land on otherwise. A
        ``logger.warning`` is emitted if ``SemanticDomainsOA`` is
        empty when this method is invoked.

        Args:
            progress: Optional ``SIL.LCModel.Utils.IProgress`` instance
                passed through to each ``Import`` call.

        Returns:
            ImportLocalizedListsResult: Named tuple with
            ``imported`` (list[str] of IcuLocale codes that merged
            successfully) and ``skipped`` (list[SkippedWS] of
            ``SkippedWS(code, reason)`` entries for WSes that did not
            apply).

        Raises:
            FP_ReadOnlyError: If the project is not write-enabled.

        Warns:
            UserWarning: If the SemanticDomains list is empty when this
                method is invoked -- translation packs will silently
                no-op because there are no canonical items to merge
                onto. Raised via ``warnings.warn`` so it surfaces in
                interactive REPL use.

        Example:
            >>> project.OpenProject("MyProject", writeEnabled=True)
            >>> project.SemanticDomains.ImportCatalog()
            >>> result = project.LocalizedLists.ImportForAllAnalysisWritingSystems()
            >>> # result.imported == ["en", "fr"] if those packs ship
            >>> # result.skipped == [SkippedWS("pt", "no shipping translation pack")]
        """
        if not self.project.writeEnabled:
            raise FP_ReadOnlyError()

        # Empty-catalog precondition probe: with nothing to merge
        # onto, every translation pack silently no-ops, which is a
        # usability trap. warnings.warn so the signal surfaces in
        # interactive use, not just in log files.
        try:
            semdom_list = (
                self.project.project.LangProject.SemanticDomainListOA
            )
            if semdom_list is None or semdom_list.PossibilitiesOS.Count == 0:
                warnings.warn(
                    "ImportForAllAnalysisWritingSystems: SemanticDomains "
                    "list is empty; translation packs will have nothing "
                    "to merge onto. Run *Operations.ImportCatalog (e.g. "
                    "project.SemanticDomains.ImportCatalog) first.",
                    UserWarning,
                    stacklevel=2,
                )
        except Exception as exc:
            # Best-effort probe only; don't fail the import on a
            # precondition check, but log so probe regressions are
            # visible at debug level.
            logger.debug(
                "Precondition probe failed: %s", exc, exc_info=True
            )

        imported = []
        skipped = []
        analysis_ws_list = (
            self.project.project.ServiceLocator.WritingSystems
            .CurrentAnalysisWritingSystems
        )
        templates_dir = self._templates_dir()
        for ws in analysis_ws_list:
            code = ws.IcuLocale
            if not code:
                logger.warning(
                    "ImportForAllAnalysisWritingSystems: skipping WS with "
                    "empty IcuLocale (hvo=%s)", getattr(ws, "Hvo", "?")
                )
                skipped.append(SkippedWS("<empty>", SKIP_EMPTY_ICU_LOCALE))
                continue
            # Validate that a matching ZIP exists before attempting the
            # import. LocalizedLists-<IcuLocale>.zip must exist in the
            # Templates directory; if not, record and skip.
            #
            # Note: variant locales (e.g. ``pt-BR`` when only ``pt``
            # ships) are categorised as SKIP_NO_TRANSLATION_PACK -- the
            # filename match is exact, so a variant mismatch and a
            # truly absent language are indistinguishable here.
            if templates_dir is not None:
                expected_zip = os.path.join(
                    templates_dir, f"LocalizedLists-{code}.zip"
                )
                if not os.path.isfile(expected_zip):
                    logger.warning(
                        "ImportForAllAnalysisWritingSystems: no translation "
                        "pack for %r (expected %s); skipping",
                        code, expected_zip,
                    )
                    skipped.append(SkippedWS(code, SKIP_NO_TRANSLATION_PACK))
                    continue
            try:
                self.Import(code, progress=progress)
            except FP_FileNotFoundError as exc:
                skipped.append(
                    SkippedWS(code, f"{SKIP_FILE_NOT_FOUND}: {exc}")
                )
                continue
            imported.append(code)
        return ImportLocalizedListsResult(imported=imported, skipped=skipped)

    def _templates_dir(self):
        """Return the FieldWorks Templates directory or None if unset."""
        if FLExGlobals.FWCodeDir is None:
            return None
        return os.path.join(FLExGlobals.FWCodeDir, "Templates")
