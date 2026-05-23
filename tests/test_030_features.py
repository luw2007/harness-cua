"""Tests for 0.3.0 features: macro record/replay, profiler, dry-run."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cua_harness.session import Session
from cua_harness.profiler import Profiler
from cua_harness.session import get_profiler, profile


def _mock_session(dry_run: bool = False) -> Session:
    """Create a Session with a mocked client (no real socket connection)."""
    with patch("cua_harness.session.CuaClient") as MockClient:
        MockClient.return_value.call.return_value = {"success": True}
        s = Session(socket_path="/tmp/fake.sock", dry_run=dry_run)
    return s


class TestMacroRecording:
    def test_start_stop_recording(self):
        s = _mock_session()
        assert not s.is_recording
        s.start_recording()
        assert s.is_recording
        traj = s.stop_recording()
        assert not s.is_recording
        assert traj == []

    def test_records_calls(self):
        s = _mock_session()
        s.client.call = MagicMock(return_value={"success": True})
        s.start_recording()
        s.call("click", pid=123, x=10)
        s.call("type_text", pid=123, text="hi")
        traj = s.stop_recording()
        assert len(traj) == 2
        assert traj[0]["tool"] == "click"
        assert traj[1]["tool"] == "type_text"
        assert traj[0]["t"] >= 0
        assert traj[1]["t"] >= traj[0]["t"]

    def test_does_not_record_when_inactive(self):
        s = _mock_session()
        s.client.call = MagicMock(return_value={"success": True})
        s.call("click", pid=1)
        s.start_recording()
        traj = s.stop_recording()
        assert traj == []

    def test_save_to_file(self):
        s = _mock_session()
        s.client.call = MagicMock(return_value={"success": True})
        s.start_recording()
        s.call("click", pid=1, x=5)
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        s.stop_recording(output_path=path)
        data = json.loads(Path(path).read_text())
        assert len(data) == 1
        assert data[0]["tool"] == "click"
        Path(path).unlink()

    def test_replay(self):
        trajectory = [
            {"t": 0.0, "tool": "click", "args": {"pid": 1, "x": 10}},
            {"t": 0.05, "tool": "type_text", "args": {"pid": 1, "text": "a"}},
        ]
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False, mode="w") as f:
            json.dump(trajectory, f)
            path = f.name

        s = _mock_session()
        s.client.call = MagicMock(return_value={"success": True})
        results = s.replay(path, speed=100.0)
        assert len(results) == 2
        assert s.client.call.call_count == 2
        Path(path).unlink()


class TestProfiler:
    def test_basic_profiling(self):
        p = Profiler()
        p.start()
        p.record("click", 5.0)
        p.record("click", 10.0)
        p.record("screenshot", 50.0)
        p.stop()

        r = p.report()
        assert r["total_calls"] == 3
        assert r["tools"]["click"]["calls"] == 2
        assert r["tools"]["click"]["avg_ms"] == 7.5
        assert r["tools"]["screenshot"]["calls"] == 1

    def test_inactive_does_not_record(self):
        p = Profiler()
        p.record("click", 5.0)
        assert p.report()["total_calls"] == 0

    def test_context_manager(self):
        from cua_harness.session import set_default_session
        s = _mock_session()
        set_default_session(s)
        try:
            with patch("builtins.print"):
                with profile() as p:
                    p.record("click", 3.0)
            assert p.report()["total_calls"] == 1
        finally:
            set_default_session(None)

    def test_global_profiler(self):
        from cua_harness.session import set_default_session
        s = _mock_session()
        set_default_session(s)
        try:
            p = get_profiler()
            assert isinstance(p, Profiler)
        finally:
            set_default_session(None)


class TestDryRun:
    def test_toggle(self):
        s = _mock_session()
        with patch("cua_harness.session.get_session", return_value=s):
            from cua_harness.session import set_dry_run, is_dry_run
            assert not is_dry_run()
            set_dry_run(True)
            assert is_dry_run()
            set_dry_run(False)
            assert not is_dry_run()

    def test_dry_run_skips_mutations(self):
        s = _mock_session(dry_run=True)
        result = s.call("click", pid=1, x=10)
        assert result["dry_run"] is True
        assert result["tool"] == "click"

    def test_dry_run_allows_reads(self):
        s = _mock_session(dry_run=True)
        s.client.call = MagicMock(return_value={"width": 1920})
        result = s.call("get_screen_size")
        assert result == {"width": 1920}

    def test_log_skipped(self, capsys):
        s = _mock_session(dry_run=True)
        s.call("click", pid=1, x=10)
        captured = capsys.readouterr()
        assert "[dry-run] SKIP click" in captured.err

    def test_integration_with_cua(self):
        s = _mock_session(dry_run=True)
        with patch("cua_harness.helpers.get_session", return_value=s):
            from cua_harness.helpers import _cua
            result = _cua("click", pid=1, x=10)
            assert result["dry_run"] is True
