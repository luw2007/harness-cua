"""Tests for cua_harness P0 changes."""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest


def test_client_call_raises_runtime_error_on_failure():
    from cua_harness.client import CuaClient

    client = CuaClient("/tmp/nonexistent.sock")
    fake_resp = {"ok": False, "error": "invalid JSON from tool"}

    with patch.object(client, "_send", return_value=fake_resp):
        with pytest.raises(RuntimeError, match="invalid JSON from tool"):
            client.call("some_tool")


def test_client_call_returns_result_on_success():
    from cua_harness.client import CuaClient

    client = CuaClient("/tmp/nonexistent.sock")
    fake_resp = {"ok": True, "result": {"success": True, "data": 42}}

    with patch.object(client, "_send", return_value=fake_resp):
        result = client.call("some_tool")
        assert result == {"success": True, "data": 42}


def test_tmp_png_tracked_for_cleanup():
    from cua_harness.helpers import _tmp_png, _tmp_files

    before = len(_tmp_files)
    path = _tmp_png()
    assert path.endswith(".png")
    assert len(_tmp_files) == before + 1
    assert _tmp_files[-1] == path
    assert os.path.exists(path)
    os.unlink(path)


def test_cleanup_tmp_files_removes_files():
    from cua_harness.helpers import _cleanup_tmp_files, _tmp_files

    f = tempfile.NamedTemporaryFile(suffix=".png", prefix="cua_test_", delete=False)
    f.close()
    _tmp_files.append(f.name)

    assert os.path.exists(f.name)
    _cleanup_tmp_files()
    assert not os.path.exists(f.name)


def test_ensure_daemon_surfaces_stderr_on_timeout():
    from cua_harness.client import ensure_daemon

    with patch("cua_harness.client.daemon_alive", return_value=False):
        fake_proc = MagicMock()
        fake_proc.communicate.return_value = (None, "bind: address already in use")

        with patch("cua_harness.client.subprocess.Popen", return_value=fake_proc):
            with patch("cua_harness.client.time.sleep"):
                with pytest.raises(RuntimeError, match="address already in use"):
                    ensure_daemon()


def test_ensure_daemon_skips_when_alive():
    from cua_harness.client import ensure_daemon

    with patch("cua_harness.client.daemon_alive", return_value=True):
        ensure_daemon()
