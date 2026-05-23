"""Unix socket client for cua-driver daemon. Line-delimited JSON protocol."""

import json
import socket
import subprocess
import shutil
import sys
import time
from pathlib import Path

SOCKET_PATH = Path.home() / "Library" / "Caches" / "cua-driver" / "cua-driver.sock"
CALL_TIMEOUT = 30
STATUS_TIMEOUT = 5


class CuaClient:
    def __init__(self, socket_path: Path | str = SOCKET_PATH):
        self._socket_path = Path(socket_path)
        self._sock: socket.socket | None = None

    def _connect(self) -> socket.socket:
        if self._sock is not None:
            return self._sock
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        sock.settimeout(CALL_TIMEOUT)
        sock.connect(str(self._socket_path))
        self._sock = sock
        return sock

    def _disconnect(self) -> None:
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
            self._sock = None

    def _send(self, request: dict, timeout: float = CALL_TIMEOUT) -> dict:
        sock = self._connect()
        sock.settimeout(timeout)
        line = json.dumps(request, separators=(",", ":")) + "\n"
        try:
            sock.sendall(line.encode())
            return self._read_response(sock)
        except (OSError, ConnectionError):
            self._disconnect()
            raise

    def _read_response(self, sock: socket.socket) -> dict:
        buf = b""
        while True:
            chunk = sock.recv(65536)
            if not chunk:
                self._disconnect()
                raise ConnectionError("daemon closed connection")
            buf += chunk
            if b"\n" in buf:
                line, _ = buf.split(b"\n", 1)
                return json.loads(line)

    def call(self, tool: str, args: dict | None = None) -> dict:
        request: dict = {"method": "call", "name": tool}
        if args:
            request["args"] = args
        resp = self._send(request)
        if not resp.get("ok"):
            raise RuntimeError(resp.get("error", f"tool {tool} failed"))
        return resp.get("result", {})

    def alive(self) -> bool:
        if not self._socket_path.exists():
            return False
        try:
            resp = self._send({"method": "list"}, timeout=STATUS_TIMEOUT)
            return resp.get("ok", False)
        except (OSError, ConnectionError, TimeoutError):
            self._disconnect()
            return False

    def close(self) -> None:
        self._disconnect()


_default_client: CuaClient | None = None


def get_client() -> CuaClient:
    global _default_client
    if _default_client is None:
        _default_client = CuaClient()
    return _default_client


def daemon_alive() -> bool:
    if not shutil.which("cua-driver"):
        return False
    return get_client().alive()


def ensure_daemon() -> dict:
    if daemon_alive():
        return {"success": True}
    proc = subprocess.Popen(
        ["cua-driver", "serve"],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.PIPE,
        text=True,
    )
    for _ in range(20):
        time.sleep(0.25)
        if daemon_alive():
            return
    stderr = ""
    try:
        _, err = proc.communicate(timeout=1)
        if err:
            stderr = err.strip()
    except Exception:
        pass
    msg = "Failed to start cua-driver daemon within 5s"
    if stderr:
        msg += f"\nstderr: {stderr}"
    print(msg, file=sys.stderr)
    raise RuntimeError(msg)


def kill_daemon() -> None:
    subprocess.run(["cua-driver", "kill"], capture_output=True, timeout=5)
    global _default_client
    if _default_client:
        _default_client.close()
        _default_client = None
