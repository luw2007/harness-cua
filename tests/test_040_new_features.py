"""Tests for new features: structuredContent unwrap, auto window selection, app_skills surfacing, macros."""

import json
from pathlib import Path
from unittest.mock import call, patch

import pytest

from cua_harness.session import Session, set_default_session


@pytest.fixture
def mock_session():
    with patch("cua_harness.session.CuaClient") as MockClient:
        MockClient.return_value.call.return_value = {"success": True}
        s = Session(socket_path="/tmp/fake.sock", dry_run=False)
    yield s
    set_default_session(None)


@pytest.fixture
def tmp_workspace(tmp_path):
    workspace = tmp_path / "agent-workspace"
    workspace.mkdir()
    (workspace / "app-skills").mkdir()
    return workspace


@pytest.fixture
def _patch_workspace(tmp_workspace):
    with patch("cua_harness.helpers.AGENT_WORKSPACE", tmp_workspace):
        yield tmp_workspace


# --- 1. _cua() structuredContent envelope unwrap ---

class TestCuaEnvelopeUnwrap:
    def test_unwraps_structured_content(self, mock_session):
        mock_session.client.call.return_value = {
            "kind": "structuredContent",
            "payload": {
                "structuredContent": {"pid": 123, "windows": [{"window_id": 1}]}
            },
        }
        set_default_session(mock_session)
        from cua_harness.helpers import _cua

        result = _cua("launch_app", bundle_id="com.apple.finder")
        assert result == {"pid": 123, "windows": [{"window_id": 1}]}

    def test_passthrough_without_envelope(self, mock_session):
        mock_session.client.call.return_value = {"width": 1920, "height": 1080}
        set_default_session(mock_session)
        from cua_harness.helpers import _cua

        result = _cua("get_screen_size")
        assert result == {"width": 1920, "height": 1080}

    def test_passthrough_when_payload_not_dict(self, mock_session):
        mock_session.client.call.return_value = {"payload": "string_value"}
        set_default_session(mock_session)
        from cua_harness.helpers import _cua

        result = _cua("some_tool")
        assert result == {"payload": "string_value"}

    def test_passthrough_when_structured_content_not_dict(self, mock_session):
        mock_session.client.call.return_value = {
            "payload": {"structuredContent": "not_a_dict"}
        }
        set_default_session(mock_session)
        from cua_harness.helpers import _cua

        result = _cua("some_tool")
        assert result == {"payload": {"structuredContent": "not_a_dict"}}


# --- 2. _pick_window_id() auto window selection ---

class TestPickWindowId:
    def test_selects_visible_on_current_space(self, mock_session):
        mock_session.client.call.return_value = {
            "windows": [
                {"window_id": 10, "is_on_screen": False, "on_current_space": True},
                {"window_id": 20, "is_on_screen": True, "on_current_space": True},
                {"window_id": 30, "is_on_screen": True, "on_current_space": False},
            ]
        }
        set_default_session(mock_session)
        from cua_harness.helpers import _pick_window_id

        assert _pick_window_id(pid=999) == 20

    def test_falls_back_to_on_current_space(self, mock_session):
        mock_session.client.call.return_value = {
            "windows": [
                {"window_id": 10, "is_on_screen": False, "on_current_space": True},
                {"window_id": 20, "is_on_screen": False, "on_current_space": False},
            ]
        }
        set_default_session(mock_session)
        from cua_harness.helpers import _pick_window_id

        assert _pick_window_id(pid=999) == 10

    def test_falls_back_to_any_window(self, mock_session):
        mock_session.client.call.return_value = {
            "windows": [
                {"window_id": 5, "is_on_screen": False, "on_current_space": False},
            ]
        }
        set_default_session(mock_session)
        from cua_harness.helpers import _pick_window_id

        assert _pick_window_id(pid=999) == 5

    def test_returns_none_when_no_windows(self, mock_session):
        mock_session.client.call.return_value = {"windows": []}
        set_default_session(mock_session)
        from cua_harness.helpers import _pick_window_id

        assert _pick_window_id(pid=999) is None

    def test_returns_none_when_windows_key_missing(self, mock_session):
        mock_session.client.call.return_value = {}
        set_default_session(mock_session)
        from cua_harness.helpers import _pick_window_id

        assert _pick_window_id(pid=999) is None


# --- 3. get_window_state without window_id ---

class TestGetWindowStateAutoSelect:
    def test_calls_pick_window_id_when_none(self, mock_session):
        call_count = {"n": 0}

        def fake_call(tool, args=None):
            call_count["n"] += 1
            if tool == "list_windows":
                return {
                    "windows": [
                        {"window_id": 42, "is_on_screen": True, "on_current_space": True}
                    ]
                }
            return {"bundle_id": "com.apple.finder", "element_count": 10}

        mock_session.client.call.side_effect = fake_call
        set_default_session(mock_session)
        from cua_harness.helpers import get_window_state

        get_window_state(pid=100)
        assert call_count["n"] == 2
        # Verify the second call (get_window_state) received window_id=42
        second_call_args = mock_session.client.call.call_args_list[1]
        tool_name = second_call_args[0][0]
        kwargs_passed = second_call_args[0][1] if len(second_call_args[0]) > 1 else {}
        assert tool_name == "get_window_state"
        assert kwargs_passed.get("window_id") == 42

    def test_skips_pick_when_window_id_provided(self, mock_session):
        mock_session.client.call.return_value = {
            "bundle_id": "com.apple.finder",
            "element_count": 5,
        }
        set_default_session(mock_session)
        from cua_harness.helpers import get_window_state

        get_window_state(pid=100, window_id=77)
        # Only one call (no list_windows needed)
        assert mock_session.client.call.call_count == 1
        call_args = mock_session.client.call.call_args[0]
        assert call_args[0] == "get_window_state"
        assert call_args[1]["window_id"] == 77


# --- 4. _surface_app_skills() path injection ---

class TestSurfaceAppSkillsIntegration:
    def test_injects_path_when_helpers_exists(self, _patch_workspace, mock_session):
        ws = _patch_workspace
        bundle = "com.apple.finder"
        skill_dir = ws / "app-skills" / bundle
        skill_dir.mkdir(parents=True)
        (skill_dir / "helpers.py").write_text("def go(): pass")

        mock_session.client.call.return_value = {
            "payload": {
                "structuredContent": {
                    "bundle_id": bundle,
                    "element_count": 3,
                }
            }
        }
        set_default_session(mock_session)
        from cua_harness.helpers import get_window_state

        result = get_window_state(pid=100, window_id=1)
        assert result["app_skills"] == str(skill_dir / "helpers.py")

    def test_no_injection_without_helpers(self, _patch_workspace, mock_session):
        ws = _patch_workspace
        bundle = "com.test.nohelpers"
        skill_dir = ws / "app-skills" / bundle
        skill_dir.mkdir(parents=True)
        (skill_dir / "notes.txt").write_text("not helpers")

        mock_session.client.call.return_value = {
            "bundle_id": bundle,
            "element_count": 1,
        }
        set_default_session(mock_session)
        from cua_harness.helpers import get_window_state

        result = get_window_state(pid=100, window_id=1)
        assert "app_skills" not in result


# --- 5. launch_app returns top-level dict ---

class TestLaunchAppTopLevel:
    def test_returns_unwrapped_dict(self, mock_session):
        mock_session.client.call.return_value = {
            "kind": "structuredContent",
            "payload": {
                "structuredContent": {
                    "bundle_id": "com.apple.Notes",
                    "pid": 5678,
                    "windows": [{"window_id": 1, "title": "Notes"}],
                }
            },
        }
        set_default_session(mock_session)
        from cua_harness.helpers import launch_app

        result = launch_app(bundle_id="com.apple.Notes")
        assert result["pid"] == 5678
        assert result["bundle_id"] == "com.apple.Notes"
        assert len(result["windows"]) == 1

    def test_raises_without_bundle_or_name(self):
        from cua_harness.helpers import launch_app

        with pytest.raises(ValueError, match="requires bundle_id or name"):
            launch_app()


# --- 6. start_macro / stop_macro / replay_macro ---

class TestMacroHelpers:
    def test_start_macro_begins_recording(self, mock_session):
        set_default_session(mock_session)
        from cua_harness.helpers import start_macro

        start_macro()
        assert mock_session.is_recording is True

    def test_stop_macro_returns_trajectory(self, mock_session):
        set_default_session(mock_session)
        from cua_harness.helpers import start_macro, stop_macro

        start_macro()
        # Simulate a call that gets recorded
        mock_session.client.call.return_value = {"success": True}
        mock_session.call("click", pid=1, x=10, y=20)

        trajectory = stop_macro()
        assert isinstance(trajectory, list)
        assert len(trajectory) == 1
        assert trajectory[0]["tool"] == "click"
        assert mock_session.is_recording is False

    def test_stop_macro_writes_to_file(self, mock_session, tmp_path):
        set_default_session(mock_session)
        from cua_harness.helpers import start_macro, stop_macro

        start_macro()
        mock_session.client.call.return_value = {"success": True}
        mock_session.call("type_text", pid=1, text="hello")

        out = str(tmp_path / "macro.json")
        stop_macro(output_path=out)
        data = json.loads(Path(out).read_text())
        assert len(data) == 1
        assert data[0]["tool"] == "type_text"

    def test_replay_macro_delegates_to_session(self, mock_session, tmp_path):
        trajectory = [
            {"tool": "click", "args": {"pid": 1, "x": 5, "y": 5}, "t": 0.0},
            {"tool": "click", "args": {"pid": 1, "x": 10, "y": 10}, "t": 1.0},
        ]
        macro_file = tmp_path / "test.json"
        macro_file.write_text(json.dumps(trajectory))

        set_default_session(mock_session)
        mock_session.client.call.return_value = {"success": True}
        from cua_harness.helpers import replay_macro

        with patch("cua_harness.session.time.sleep") as mock_sleep:
            results = replay_macro(str(macro_file), speed=2.0)

        assert len(results) == 2
        # First step: delay = (0.0 - 0.0) / 2.0 = 0.0, no sleep
        # Second step: delay = (1.0 - 0.0) / 2.0 = 0.5
        mock_sleep.assert_called_once_with(0.5)


# --- 7. Session.replay speed parameter ---

class TestSessionReplay:
    def test_replay_respects_speed(self, tmp_path):
        trajectory = [
            {"tool": "scroll", "args": {"pid": 1, "direction": "down"}, "t": 0.0},
            {"tool": "scroll", "args": {"pid": 1, "direction": "down"}, "t": 2.0},
            {"tool": "scroll", "args": {"pid": 1, "direction": "down"}, "t": 5.0},
        ]
        macro_file = tmp_path / "replay.json"
        macro_file.write_text(json.dumps(trajectory))

        with patch("cua_harness.session.CuaClient") as MockClient:
            MockClient.return_value.call.return_value = {"success": True}
            s = Session(socket_path="/tmp/fake.sock", dry_run=False)

        with patch("cua_harness.session.time.sleep") as mock_sleep:
            results = s.replay(str(macro_file), speed=4.0)

        assert len(results) == 3
        # step 0: delay = 0/4 = 0 → no sleep
        # step 1: delay = 2.0/4 = 0.5
        # step 2: delay = 3.0/4 = 0.75
        assert mock_sleep.call_args_list == [call(0.5), call(0.75)]

    def test_replay_at_default_speed(self, tmp_path):
        trajectory = [
            {"tool": "click", "args": {"pid": 1, "x": 0, "y": 0}, "t": 0.0},
            {"tool": "click", "args": {"pid": 1, "x": 1, "y": 1}, "t": 1.5},
        ]
        macro_file = tmp_path / "replay2.json"
        macro_file.write_text(json.dumps(trajectory))

        with patch("cua_harness.session.CuaClient") as MockClient:
            MockClient.return_value.call.return_value = {"success": True}
            s = Session(socket_path="/tmp/fake.sock", dry_run=False)

        with patch("cua_harness.session.time.sleep") as mock_sleep:
            s.replay(str(macro_file), speed=1.0)

        mock_sleep.assert_called_once_with(1.5)

    def test_replay_calls_correct_tools(self, tmp_path):
        trajectory = [
            {"tool": "click", "args": {"pid": 2, "x": 10, "y": 20}, "t": 0.0},
            {"tool": "type_text", "args": {"pid": 2, "text": "hi"}, "t": 0.1},
        ]
        macro_file = tmp_path / "replay3.json"
        macro_file.write_text(json.dumps(trajectory))

        with patch("cua_harness.session.CuaClient") as MockClient:
            MockClient.return_value.call.return_value = {"ok": True}
            s = Session(socket_path="/tmp/fake.sock", dry_run=False)

        with patch("cua_harness.session.time.sleep"):
            s.replay(str(macro_file), speed=10.0)

        calls = MockClient.return_value.call.call_args_list
        assert calls[0][0] == ("click", {"pid": 2, "x": 10, "y": 20})
        assert calls[1][0] == ("type_text", {"pid": 2, "text": "hi"})
