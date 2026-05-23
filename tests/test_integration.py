"""Tests for external agent framework integration examples."""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest

sys.path.insert(0, str(Path(__file__).parent.parent / "examples"))


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
        from cua_harness import set_dry_run
        from langchain_tools import build_cua_tools

        set_dry_run(True)
        tools = {t.name: t for t in build_cua_tools()}
        result = tools["click"](pid=1, element_index=3)
        assert result["dry_run"] is True
        assert result["tool"] == "click"
        set_dry_run(False)

    def test_read_only_tool_passthrough(self):
        from langchain_tools import build_cua_tools
        from cua_harness import set_dry_run

        set_dry_run(True)
        tools = {t.name: t for t in build_cua_tools()}

        with patch("cua_harness.helpers.get_client") as mock_client:
            mock_client.return_value.call.return_value = {"width": 1920, "height": 1080}
            result = tools["get_screen_size"]()
            assert result == {"width": 1920, "height": 1080}

        set_dry_run(False)


class TestClaudeCodeAgent:
    def test_imports_and_callable(self):
        from claude_code_agent import run_agent
        assert callable(run_agent)
