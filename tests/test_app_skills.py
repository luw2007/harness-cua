"""Tests for app-skills surfacing, persistence, versioning and loading."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest


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


SAMPLE_CODE = """\
from cua_harness import get_window_state, click

def open_messages(pid):
    state = get_window_state(pid, query="消息")
    click(pid, element_index=0)
"""


class TestSurfaceAppSkills:
    def test_surfaces_helpers_py_when_enabled(self, _patch_workspace):
        ws = _patch_workspace
        bundle = "com.googlecode.iterm2"
        skill_dir = ws / "app-skills" / bundle
        skill_dir.mkdir(parents=True)
        (skill_dir / "helpers.py").write_text("def hello(): pass")

        from cua_harness.helpers import _surface_app_skills

        result = {
            "payload": {"structuredContent": {"bundle_id": bundle, "tree_markdown": "..."}}
        }
        with patch.dict(os.environ, {"CUA_APP_SKILLS": "1"}):
            out = _surface_app_skills(result)

        assert out["app_skills"] == str(skill_dir / "helpers.py")

    def test_no_surfacing_when_disabled(self, _patch_workspace):
        ws = _patch_workspace
        bundle = "com.googlecode.iterm2"
        skill_dir = ws / "app-skills" / bundle
        skill_dir.mkdir(parents=True)
        (skill_dir / "helpers.py").write_text("def hello(): pass")

        from cua_harness.helpers import _surface_app_skills

        result = {"payload": {"structuredContent": {"bundle_id": bundle}}}
        with patch.dict(os.environ, {}, clear=False):
            os.environ.pop("CUA_APP_SKILLS", None)
            out = _surface_app_skills(result)

        assert "app_skills" not in out

    def test_no_surfacing_when_no_dir(self, _patch_workspace):
        from cua_harness.helpers import _surface_app_skills

        result = {"payload": {"structuredContent": {"bundle_id": "com.nonexistent.app"}}}
        with patch.dict(os.environ, {"CUA_APP_SKILLS": "1"}):
            out = _surface_app_skills(result)

        assert "app_skills" not in out

    def test_no_surfacing_without_bundle_id(self, _patch_workspace):
        from cua_harness.helpers import _surface_app_skills

        result = {"payload": {"content": [{"text": "hello"}]}}
        with patch.dict(os.environ, {"CUA_APP_SKILLS": "1"}):
            out = _surface_app_skills(result)

        assert "app_skills" not in out

    def test_no_surfacing_without_helpers_py(self, _patch_workspace):
        ws = _patch_workspace
        bundle = "com.test.app"
        skill_dir = ws / "app-skills" / bundle
        skill_dir.mkdir(parents=True)
        (skill_dir / "notes.txt").write_text("not a helpers.py")

        from cua_harness.helpers import _surface_app_skills

        result = {"payload": {"structuredContent": {"bundle_id": bundle}}}
        with patch.dict(os.environ, {"CUA_APP_SKILLS": "1"}):
            out = _surface_app_skills(result)

        assert "app_skills" not in out


class TestSaveAppSkill:
    def test_creates_helpers_py(self, _patch_workspace):
        ws = _patch_workspace
        from cua_harness.helpers import save_app_skill

        path = save_app_skill("com.test.app", SAMPLE_CODE, reason="initial")
        p = Path(path)
        assert p.exists()
        assert p.name == "helpers.py"
        assert "open_messages" in p.read_text()

    def test_backup_on_update(self, _patch_workspace):
        ws = _patch_workspace
        from cua_harness.helpers import save_app_skill

        save_app_skill("com.test.app", "# v1\ndef v1(): pass")
        save_app_skill("com.test.app", "# v2\ndef v2(): pass", reason="added v2")

        skill_dir = ws / "app-skills" / "com.test.app"
        baks = list(skill_dir.glob("helpers.*.bak.py"))
        assert len(baks) == 1
        assert "v1" in baks[0].read_text()
        assert "v2" in (skill_dir / "helpers.py").read_text()

    def test_changelog_written(self, _patch_workspace):
        ws = _patch_workspace
        from cua_harness.helpers import save_app_skill

        save_app_skill("com.test.app", SAMPLE_CODE, reason="learned message path")
        changelog = ws / "app-skills" / "com.test.app" / "CHANGELOG.md"
        assert changelog.exists()
        assert "learned message path" in changelog.read_text()

    def test_max_5_backups(self, _patch_workspace):
        ws = _patch_workspace
        from cua_harness.helpers import save_app_skill

        for i in range(7):
            save_app_skill("com.test.app", f"# v{i}\ndef v{i}(): pass")

        skill_dir = ws / "app-skills" / "com.test.app"
        baks = list(skill_dir.glob("helpers.*.bak.py"))
        assert len(baks) == 5

    def test_same_day_multiple_backups(self, _patch_workspace):
        from cua_harness.helpers import save_app_skill

        save_app_skill("com.test.app", "# v1")
        save_app_skill("com.test.app", "# v2")
        save_app_skill("com.test.app", "# v3")

        ws = _patch_workspace
        skill_dir = ws / "app-skills" / "com.test.app"
        baks = sorted(skill_dir.glob("helpers.*.bak.py"))
        assert len(baks) == 2
        assert "v1" in baks[0].read_text()
        assert "v2" in baks[1].read_text()


class TestLoadAppSkills:
    def test_loads_into_namespace(self, _patch_workspace):
        ws = _patch_workspace
        bundle = "com.test.app"
        skill_dir = ws / "app-skills" / bundle
        skill_dir.mkdir(parents=True)
        (skill_dir / "helpers.py").write_text("def greet():\n    return 'hello'\n")

        from cua_harness.helpers import load_app_skills

        ns = {}
        loaded = load_app_skills(bundle, ns)
        assert loaded is True
        assert "greet" in ns
        assert ns["greet"]() == "hello"

    def test_returns_false_when_no_file(self, _patch_workspace):
        from cua_harness.helpers import load_app_skills

        ns = {}
        loaded = load_app_skills("com.nonexistent", ns)
        assert loaded is False
        assert ns == {}
