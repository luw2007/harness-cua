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


def test_ensure_daemon_retries_on_address_in_use():
    from cua_harness.client import ensure_daemon
    from pathlib import Path

    call_count = {"popen": 0}

    def daemon_alive_side_effect():
        return call_count["popen"] >= 2

    fake_proc = MagicMock()
    fake_proc.communicate.return_value = (None, "bind: address already in use")

    def popen_side_effect(*args, **kwargs):
        call_count["popen"] += 1
        return fake_proc

    with patch("cua_harness.client.daemon_alive", side_effect=daemon_alive_side_effect):
        with patch("cua_harness.client.subprocess.Popen", side_effect=popen_side_effect):
            with patch("cua_harness.client.time.sleep"):
                with patch.object(Path, "unlink") as mock_unlink:
                    ensure_daemon()

    assert call_count["popen"] == 2
    mock_unlink.assert_called_once()


def test_ensure_daemon_skips_when_alive():
    from cua_harness.client import ensure_daemon

    with patch("cua_harness.client.daemon_alive", return_value=True):
        ensure_daemon()


def test_kill_daemon_removes_stale_socket():
    from cua_harness.client import kill_daemon, SOCKET_PATH

    tmp = tempfile.NamedTemporaryFile(delete=False, suffix=".sock")
    tmp.close()
    fake_socket = tmp.name

    with patch("cua_harness.client.SOCKET_PATH", new=type(SOCKET_PATH)(fake_socket)):
        with patch("cua_harness.client.subprocess.run"):
            with patch("cua_harness.client._default_client", None):
                kill_daemon()

    assert not os.path.exists(fake_socket)


def test_send_reconnects_on_stale_connection():
    from cua_harness.client import CuaClient

    client = CuaClient("/tmp/fake.sock")

    stale_sock = MagicMock()
    stale_sock.sendall.side_effect = BrokenPipeError("stale")

    fresh_sock = MagicMock()

    call_count = {"n": 0}

    def fake_connect():
        call_count["n"] += 1
        if call_count["n"] == 1:
            client._sock = stale_sock
            return stale_sock
        client._sock = fresh_sock
        return fresh_sock

    with patch.object(client, "_connect", side_effect=fake_connect):
        with patch.object(client, "_read_response", return_value={"ok": True, "result": {}}):
            result = client._send({"method": "list"})

    assert result == {"ok": True, "result": {}}
    assert call_count["n"] == 2
    stale_sock.sendall.assert_called_once()
    fresh_sock.sendall.assert_called_once()
