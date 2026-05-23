"""Tests for 0.2.0 features: wait_for, get_screen_size(display_id), ax_diff."""

import time
from unittest.mock import patch, MagicMock

import pytest

from cua_harness.wait import wait_for
from cua_harness.diff import ax_diff, StateCapture


class TestWaitFor:
    def test_returns_immediately_on_truthy(self):
        result = wait_for(lambda: {"ready": True}, timeout=1)
        assert result == {"ready": True}

    def test_raises_timeout_error(self):
        with pytest.raises(TimeoutError, match="timed out after 0.2s"):
            wait_for(lambda: None, timeout=0.2, poll_interval=0.05)

    def test_waits_until_truthy(self):
        calls = {"n": 0}

        def pred():
            calls["n"] += 1
            return calls["n"] >= 3

        result = wait_for(pred, timeout=2, poll_interval=0.01)
        assert result is True
        assert calls["n"] == 3

    def test_custom_message(self):
        with pytest.raises(TimeoutError, match="button not found"):
            wait_for(lambda: False, timeout=0.1, poll_interval=0.05, message="button not found")

    def test_respects_poll_interval(self):
        t0 = time.monotonic()
        calls = {"n": 0}

        def pred():
            calls["n"] += 1
            if calls["n"] >= 3:
                return True
            return False

        wait_for(pred, timeout=2, poll_interval=0.05)
        elapsed = time.monotonic() - t0
        assert elapsed >= 0.09  # at least 2 intervals


class TestAxDiff:
    def test_detects_added_elements(self):
        before = {"elements": [
            {"index": 0, "role": "button", "title": "OK", "value": ""},
        ]}
        after = {"elements": [
            {"index": 0, "role": "button", "title": "OK", "value": ""},
            {"index": 1, "role": "button", "title": "Cancel", "value": ""},
        ]}
        d = ax_diff(before, after)
        assert len(d["added"]) == 1
        assert d["added"][0]["title"] == "Cancel"
        assert len(d["removed"]) == 0

    def test_detects_removed_elements(self):
        before = {"elements": [
            {"index": 0, "role": "button", "title": "OK", "value": ""},
            {"index": 1, "role": "button", "title": "Cancel", "value": ""},
        ]}
        after = {"elements": [
            {"index": 0, "role": "button", "title": "OK", "value": ""},
        ]}
        d = ax_diff(before, after)
        assert len(d["removed"]) == 1
        assert d["removed"][0]["title"] == "Cancel"

    def test_detects_changed_elements(self):
        before = {"elements": [
            {"index": 0, "role": "textField", "title": "Name", "value": ""},
        ]}
        after = {"elements": [
            {"index": 0, "role": "textField", "title": "Name", "value": "Alice"},
        ]}
        d = ax_diff(before, after)
        assert len(d["changed"]) == 1
        assert d["changed"][0]["changes"]["value"] == {"before": "", "after": "Alice"}

    def test_empty_diff(self):
        state = {"elements": [{"index": 0, "role": "button", "title": "OK", "value": ""}]}
        d = ax_diff(state, state)
        assert d["added"] == []
        assert d["removed"] == []
        assert d["changed"] == []
        assert d["summary"] == "+0 -0 ~0"

    def test_summary_format(self):
        before = {"elements": []}
        after = {"elements": [
            {"index": 0, "role": "button", "title": "A", "value": ""},
            {"index": 1, "role": "button", "title": "B", "value": ""},
        ]}
        d = ax_diff(before, after)
        assert d["summary"] == "+2 -0 ~0"


class TestGetScreenSizeMultiDisplay:
    def test_no_display_id(self):
        from cua_harness.helpers import get_screen_size
        with patch("cua_harness.helpers.get_client") as mock_client:
            mock_client.return_value.call.return_value = {"width": 1920, "height": 1080}
            result = get_screen_size()
            mock_client.return_value.call.assert_called_once_with("get_screen_size", None)
            assert result == {"width": 1920, "height": 1080}

    def test_with_display_id(self):
        from cua_harness.helpers import get_screen_size
        with patch("cua_harness.helpers.get_client") as mock_client:
            mock_client.return_value.call.return_value = {"width": 2560, "height": 1440}
            result = get_screen_size(display_id=2)
            mock_client.return_value.call.assert_called_once_with("get_screen_size", {"display_id": 2})
            assert result == {"width": 2560, "height": 1440}
