"""Tests for external agent framework integration examples."""

import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cua_harness.session import Session

sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))


def _mock_session(dry_run: bool = False) -> Session:
    with patch("cua_harness.session.CuaClient") as MockClient:
        MockClient.return_value.call.return_value = {"success": True}
        s = Session(socket_path="/tmp/fake.sock", dry_run=dry_run)
    return s


class TestLangChainToolsAdapter:
    def test_builds_tools(self):
        from langchain_tools import build_cua_tools, Tool
        tools = build_cua_tools()
        assert len(tools) == 11
        for t in tools:
            assert isinstance(t, Tool)
            assert t.name
            assert t.description

    def test_tool_invoke_dry_run(self):
        from langchain_tools import build_cua_tools

        s = _mock_session(dry_run=True)
        with patch("cua_harness.helpers.get_session", return_value=s):
            tools = {t.name: t for t in build_cua_tools()}
            result = tools["click"](pid=1, element_index=3)
            assert result["dry_run"] is True
            assert result["tool"] == "click"

    def test_read_only_tool_passthrough(self):
        from langchain_tools import build_cua_tools

        s = _mock_session(dry_run=True)
        s.client.call = MagicMock(return_value={"width": 1920, "height": 1080})

        with patch("cua_harness.helpers.get_session", return_value=s):
            tools = {t.name: t for t in build_cua_tools()}
            result = tools["get_screen_size"]()
            assert result == {"width": 1920, "height": 1080}


class TestClaudeCodeAgent:
    def test_imports_and_callable(self):
        from claude_code_agent import run_agent
        assert callable(run_agent)
