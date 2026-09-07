#
#   test_guid_create_agent_reversals_live.py
#
#   Live write-path verification for feature #236: guid-preserving
#   Create() added to AgentOperations, ReversalIndexOperations, and
#   ReversalIndexEntryOperations, consistent with the existing
#   BaseOperations._CreateWithGuid() callers (WordformOperations,
#   TextOperations, ParagraphOperations, WfiGlossOperations, etc.).
#
#   Copied structure from test_target_live_smoke.py. Uses target_sandbox
#   (tempdir copy of the Target .fwbackup) exclusively -- nothing here
#   can leak into a real project.
#
#   Platform: Python.NET
#             FieldWorks Version 9+
#
#   Copyright 2026
#

import pytest

# Import flexicon.code.FLExProject FIRST: it does `import clr`, which
# installs pythonnet's import hook for CLR namespaces. Only after that
# hook is installed does a bare `from System import Guid` succeed --
# reversing this order raises ModuleNotFoundError: No module named
# 'System' when this file happens to be the first one pytest collects.
from flexicon.code.FLExProject import FP_ParameterError
from System import Guid as DotNetGuid

pytestmark = pytest.mark.requires_live_project

TEST_PREFIX = "TEST_"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _reread_by_guid(project, guid_str):
    """
    Re-query an object from its repository by GUID, rather than trusting
    the object handle Create() itself returned. This is the point of the
    test: prove the GUID was actually persisted into the LCM, not just
    echoed back on the Python wrapper.
    """
    return project.Object(guid_str)


def _find_free_analysis_ws_handles(project, count=1):
    """
    Return up to `count` analysis writing-system handles that currently
    have NO reversal index in this project. Returns fewer than `count`
    (possibly zero) if not enough are free -- callers must check the
    length and skip/report explicitly rather than deleting an existing
    index to make room.
    """
    rev_ops = project.ReversalIndexes
    free = []
    for ws in project.lp.CurrentAnalysisWritingSystems:
        handle = project.WSHandle(ws.Id)
        if handle is None:
            continue
        if rev_ops.FindByWritingSystem(handle) is None:
            free.append(handle)
        if len(free) >= count:
            break
    return free


# ---------------------------------------------------------------------------
# AgentOperations.Create(guid=...)
# ---------------------------------------------------------------------------


class TestGuidCreateAgent:

    @pytest.mark.live_phase("AgentOperations", "add")
    def test_create_with_explicit_guid_is_persisted(self, target_sandbox):
        """Create(guid=X) persists X; re-querying the LCM by GUID confirms it."""
        agents = target_sandbox.Agents
        requested = str(DotNetGuid.NewGuid())

        agent = agents.Create(f"{TEST_PREFIX}agent_explicit_guid", guid=requested)
        assert agent is not None

        reread = _reread_by_guid(target_sandbox, requested)
        assert reread is not None, "GUID was not found in the LCM after Create()"
        assert str(reread.Guid).lower() == requested.lower()

    @pytest.mark.live_phase("AgentOperations", "add")
    def test_create_with_guid_none_mints_fresh_guid(self, target_sandbox):
        """Create(guid=None) -- the default -- still mints a valid, non-null GUID."""
        agents = target_sandbox.Agents

        agent = agents.Create(f"{TEST_PREFIX}agent_default_guid")
        assert agent is not None

        guid_str = str(agent.Guid)
        assert guid_str and guid_str != str(DotNetGuid.Empty)

        reread = _reread_by_guid(target_sandbox, guid_str)
        assert reread is not None
        assert str(reread.Guid).lower() == guid_str.lower()

    @pytest.mark.live_phase("AgentOperations", "add")
    def test_create_duplicate_guid_falls_back_without_raising(self, target_sandbox):
        """
        Requesting a GUID already present in the project (the 3 bootstrap
        agents, or one we just created) must NOT raise -- it falls back
        to a fresh identity with a logged warning.
        """
        agents = target_sandbox.Agents
        requested = str(DotNetGuid.NewGuid())

        first = agents.Create(f"{TEST_PREFIX}agent_dup_first", guid=requested)
        assert str(first.Guid).lower() == requested.lower()

        second = agents.Create(f"{TEST_PREFIX}agent_dup_second", guid=requested)
        assert second is not None, "Create() raised instead of falling back"
        assert str(second.Guid).lower() != requested.lower(), (
            "Second Create() with a duplicate GUID kept the requested GUID "
            "instead of falling back to a fresh identity"
        )

    @pytest.mark.live_phase("AgentOperations", "add")
    def test_create_with_malformed_guid_raises_parameter_error(self, target_sandbox):
        """A malformed guid string is a caller error -- FP_ParameterError, not a crash."""
        agents = target_sandbox.Agents

        with pytest.raises(FP_ParameterError):
            agents.Create(f"{TEST_PREFIX}agent_bad_guid", guid="not-a-guid")

    @pytest.mark.live_phase("AgentOperations", "add")
    def test_created_agent_present_in_analyzing_agents_oc(self, target_sandbox):
        """The new agent is really in LangProject.AnalyzingAgentsOC, not just returned."""
        agents = target_sandbox.Agents
        requested = str(DotNetGuid.NewGuid())

        agent = agents.Create(f"{TEST_PREFIX}agent_in_oc", guid=requested)

        oc_guids = [str(a.Guid).lower() for a in target_sandbox.lp.AnalyzingAgentsOC]
        assert requested.lower() in oc_guids


# ---------------------------------------------------------------------------
# ReversalIndexOperations.Create(guid=...)
# ---------------------------------------------------------------------------


class TestGuidCreateReversalIndex:

    @pytest.mark.live_phase("ReversalIndexOperations", "add")
    def test_create_with_explicit_guid_is_persisted(self, target_sandbox):
        """Create(guid=X) persists X; re-querying the LCM by GUID confirms it."""
        free = _find_free_analysis_ws_handles(target_sandbox, count=1)
        if not free:
            pytest.skip(
                "Every analysis writing system in the Target project already "
                "has a reversal index -- no free WS available for this test. "
                "Not deleting an existing index to make room."
            )
        ws_handle = free[0]

        rev_ops = target_sandbox.ReversalIndexes
        requested = str(DotNetGuid.NewGuid())

        index = rev_ops.Create(f"{TEST_PREFIX}index_explicit_guid", ws_handle, guid=requested)
        assert index is not None

        reread = _reread_by_guid(target_sandbox, requested)
        assert reread is not None
        assert str(reread.Guid).lower() == requested.lower()

    @pytest.mark.live_phase("ReversalIndexOperations", "add")
    def test_create_with_guid_none_mints_fresh_guid(self, target_sandbox):
        """Create(guid=None) -- the default -- still mints a valid, non-null GUID."""
        free = _find_free_analysis_ws_handles(target_sandbox, count=1)
        if not free:
            pytest.skip(
                "Every analysis writing system in the Target project already "
                "has a reversal index -- no free WS available for this test."
            )
        ws_handle = free[0]

        rev_ops = target_sandbox.ReversalIndexes
        index = rev_ops.Create(f"{TEST_PREFIX}index_default_guid", ws_handle)
        assert index is not None

        guid_str = str(index.Guid)
        assert guid_str and guid_str != str(DotNetGuid.Empty)

        reread = _reread_by_guid(target_sandbox, guid_str)
        assert reread is not None
        assert str(reread.Guid).lower() == guid_str.lower()

    @pytest.mark.live_phase("ReversalIndexOperations", "add")
    def test_create_duplicate_guid_falls_back_without_raising(self, target_sandbox):
        """
        Requesting a GUID already present in the project must NOT raise --
        it falls back to a fresh identity. Needs TWO free writing systems
        since each index requires its own WS.
        """
        free = _find_free_analysis_ws_handles(target_sandbox, count=2)
        if len(free) < 2:
            pytest.skip(
                "Fewer than 2 analysis writing systems without an existing "
                "reversal index are available in the Target project -- "
                "cannot exercise the duplicate-GUID-across-two-indexes case "
                "without deleting an existing index."
            )
        ws_handle_a, ws_handle_b = free

        rev_ops = target_sandbox.ReversalIndexes
        requested = str(DotNetGuid.NewGuid())

        first = rev_ops.Create(f"{TEST_PREFIX}index_dup_first", ws_handle_a, guid=requested)
        assert str(first.Guid).lower() == requested.lower()

        second = rev_ops.Create(f"{TEST_PREFIX}index_dup_second", ws_handle_b, guid=requested)
        assert second is not None, "Create() raised instead of falling back"
        assert str(second.Guid).lower() != requested.lower()

    @pytest.mark.live_phase("ReversalIndexOperations", "add")
    def test_create_with_malformed_guid_raises_parameter_error(self, target_sandbox):
        """A malformed guid string is a caller error -- FP_ParameterError, not a crash."""
        free = _find_free_analysis_ws_handles(target_sandbox, count=1)
        if not free:
            pytest.skip(
                "Every analysis writing system in the Target project already "
                "has a reversal index -- no free WS available for this test."
            )
        ws_handle = free[0]

        rev_ops = target_sandbox.ReversalIndexes
        with pytest.raises(FP_ParameterError):
            rev_ops.Create(f"{TEST_PREFIX}index_bad_guid", ws_handle, guid="not-a-guid")

    @pytest.mark.live_phase("ReversalIndexOperations", "add")
    def test_create_duplicate_writing_system_still_raises_with_guid(self, target_sandbox):
        """
        Contract test: guid= does NOT bypass the one-index-per-writing-
        system rule. A duplicate WS still raises FP_ParameterError even
        when a guid is supplied.
        """
        free = _find_free_analysis_ws_handles(target_sandbox, count=1)
        if not free:
            pytest.skip(
                "Every analysis writing system in the Target project already "
                "has a reversal index -- no free WS available for this test."
            )
        ws_handle = free[0]

        rev_ops = target_sandbox.ReversalIndexes
        rev_ops.Create(f"{TEST_PREFIX}index_ws_first", ws_handle)

        with pytest.raises(FP_ParameterError):
            rev_ops.Create(
                f"{TEST_PREFIX}index_ws_second",
                ws_handle,
                guid=str(DotNetGuid.NewGuid()),
            )


# ---------------------------------------------------------------------------
# ReversalIndexEntryOperations.Create(guid=...)
# ---------------------------------------------------------------------------


class TestGuidCreateReversalIndexEntry:

    def _make_index(self, project):
        """
        Create a scratch reversal index on a free analysis WS, or skip.
        Returns (index, ws_handle).

        Note: ReversalIndexOperations.Create() stores
        ``str(writing_system)`` verbatim into ``IReversalIndex
        .WritingSystem`` -- when the caller passes an int handle (the
        pattern shown in that method's own docstring), this stores the
        stringified INT, not an ICU locale tag. That is a pre-existing
        bug independent of #236 (unrelated to the guid= addition; not
        touched here per this task's scope), but it means
        ReversalIndexEntryOperations.Create()'s own
        ``wsHandle = self.project.WSHandle(index.WritingSystem)``
        fallback fails to resolve a handle and raises
        ArgumentNullException deep in TsStringUtils.MakeString. Every
        entry-creation call below sidesteps it by passing ``wsHandle=``
        explicitly (a legitimate, already-supported parameter), rather
        than relying on the index to resolve its own WS.
        """
        free = _find_free_analysis_ws_handles(project, count=1)
        if not free:
            pytest.skip(
                "Every analysis writing system in the Target project already "
                "has a reversal index -- no free WS available to create a "
                "scratch index for entry tests."
            )
        ws_handle = free[0]
        index = project.ReversalIndexes.Create(f"{TEST_PREFIX}index_for_entries", ws_handle)
        return index, ws_handle

    @pytest.mark.live_phase("ReversalIndexEntryOperations", "add")
    def test_create_with_explicit_guid_is_persisted(self, target_sandbox):
        """Create(guid=X) persists X; re-querying the LCM by GUID confirms it."""
        index, ws_handle = self._make_index(target_sandbox)
        entries = target_sandbox.ReversalEntries
        requested = str(DotNetGuid.NewGuid())

        entry = entries.Create(index, "run", wsHandle=ws_handle, guid=requested)
        assert entry is not None

        reread = _reread_by_guid(target_sandbox, requested)
        assert reread is not None
        assert str(reread.Guid).lower() == requested.lower()

    @pytest.mark.live_phase("ReversalIndexEntryOperations", "add")
    def test_create_with_guid_none_mints_fresh_guid(self, target_sandbox):
        """Create(guid=None) -- the default -- still mints a valid, non-null GUID."""
        index, ws_handle = self._make_index(target_sandbox)
        entries = target_sandbox.ReversalEntries

        entry = entries.Create(index, "walk", wsHandle=ws_handle)
        assert entry is not None

        guid_str = str(entry.Guid)
        assert guid_str and guid_str != str(DotNetGuid.Empty)

        reread = _reread_by_guid(target_sandbox, guid_str)
        assert reread is not None
        assert str(reread.Guid).lower() == guid_str.lower()

    @pytest.mark.live_phase("ReversalIndexEntryOperations", "add")
    def test_create_duplicate_guid_falls_back_without_raising(self, target_sandbox):
        """Requesting a GUID already present in the project falls back, no raise."""
        index, ws_handle = self._make_index(target_sandbox)
        entries = target_sandbox.ReversalEntries
        requested = str(DotNetGuid.NewGuid())

        first = entries.Create(index, "jump", wsHandle=ws_handle, guid=requested)
        assert str(first.Guid).lower() == requested.lower()

        second = entries.Create(index, "leap", wsHandle=ws_handle, guid=requested)
        assert second is not None, "Create() raised instead of falling back"
        assert str(second.Guid).lower() != requested.lower()

    @pytest.mark.live_phase("ReversalIndexEntryOperations", "add")
    def test_create_with_malformed_guid_raises_parameter_error(self, target_sandbox):
        """A malformed guid string is a caller error -- FP_ParameterError, not a crash."""
        index, ws_handle = self._make_index(target_sandbox)
        entries = target_sandbox.ReversalEntries

        with pytest.raises(FP_ParameterError):
            entries.Create(index, "skip", wsHandle=ws_handle, guid="not-a-guid")

    @pytest.mark.live_phase("ReversalIndexEntryOperations", "add")
    def test_created_entry_present_in_index_entries_oc(self, target_sandbox):
        """The new entry is really in index.EntriesOC, not just returned."""
        index, ws_handle = self._make_index(target_sandbox)
        entries = target_sandbox.ReversalEntries
        requested = str(DotNetGuid.NewGuid())

        entries.Create(index, "climb", wsHandle=ws_handle, guid=requested)

        oc_guids = [str(e.Guid).lower() for e in index.EntriesOC]
        assert requested.lower() in oc_guids
