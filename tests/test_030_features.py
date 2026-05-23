"""Tests for 0.3.0 features: macro record/replay, profiler, dry-run."""

import json
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from cua_harness.macro import start_recording, stop_recording, is_recording, record_call
from cua_harness.profiler import Profiler, get_profiler, profile
from cua_harness.dryrun import set_dry_run, is_dry_run, should_skip, log_skipped


class TestMacroRecording:
    def setup_method(self):
        import cua_harness.macro as m
        m._recording = False
        m._trajectory = []

    def test_start_stop_recording(self):
        assert not is_recording()
        start_recording()
        assert is_recording()
        traj = stop_recording()
        assert not is_recording()
        assert traj == []

    def test_records_calls(self):
        start_recording()
        record_call("click", {"pid": 123, "x": 10}, {"success": True})
        record_call("type_text", {"pid": 123, "text": "hi"}, {"success": True})
        traj = stop_recording()
        assert len(traj) == 2
        assert traj[0]["tool"] == "click"
        assert traj[1]["tool"] == "type_text"
        assert traj[0]["t"] >= 0
        assert traj[1]["t"] >= traj[0]["t"]

    def test_does_not_record_when_inactive(self):
        record_call("click", {"pid": 1}, {"success": True})
        start_recording()
        traj = stop_recording()
        assert traj == []

    def test_save_to_file(self):
        start_recording()
        record_call("click", {"pid": 1, "x": 5}, {"success": True})
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        stop_recording(output_path=path)
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

        with patch("cua_harness.helpers.get_client") as mock_client:
            mock_client.return_value.call.return_value = {"success": True}
            from cua_harness.macro import replay
            results = replay(path, speed=100.0)
            assert len(results) == 2
            assert mock_client.return_value.call.call_count == 2

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
        with patch("cua_harness.profiler._global_profiler", Profiler()):
            with patch("builtins.print"):
                with profile() as p:
                    p.record("click", 3.0)
            assert p.report()["total_calls"] == 1

    def test_global_profiler(self):
        p = get_profiler()
        assert isinstance(p, Profiler)


class TestDryRun:
    def setup_method(self):
        set_dry_run(False)

    def test_toggle(self):
        assert not is_dry_run()
        set_dry_run(True)
        assert is_dry_run()
        set_dry_run(False)
        assert not is_dry_run()

    def test_should_skip_mutations(self):
        set_dry_run(True)
        assert should_skip("click")
        assert should_skip("type_text")
        assert should_skip("press_key")
        assert should_skip("drag")
        assert not should_skip("get_window_state")
        assert not should_skip("screenshot")
        assert not should_skip("list_apps")

    def test_should_not_skip_when_disabled(self):
        set_dry_run(False)
        assert not should_skip("click")

    def test_log_skipped(self, capsys):
        result = log_skipped("click", {"pid": 1, "x": 10})
        assert result["dry_run"] is True
        assert result["tool"] == "click"
        captured = capsys.readouterr()
        assert "[dry-run] SKIP click" in captured.err

    def test_integration_with_cua(self):
        set_dry_run(True)
        from cua_harness.helpers import _cua
        result = _cua("click", pid=1, x=10)
        assert result["dry_run"] is True
        set_dry_run(False)
