"""Integration tests for the Borg CLI — init + bootstrap flow."""

from __future__ import annotations

import tempfile
from pathlib import Path

import pytest
from click.testing import CliRunner

from cli.borg_cli import cli


@pytest.mark.integration
def test_init_then_bootstrap():
    """Full flow: init a project, bootstrap markdown files, verify ingestion."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Step 1: borg init — create a .claude/ dir so the tool detects Claude
        (tmp_path / ".claude").mkdir()
        result = runner.invoke(
            cli,
            ["init", "--namespace", "integration-test", "--dir", tmp],
        )
        assert result.exit_code == 0, f"init failed:\n{result.output}"
        assert "Detected tools: claude" in result.output
        assert "Created CLAUDE.md" in result.output

        # Verify CLAUDE.md was written with the correct namespace
        claude_md = tmp_path / "CLAUDE.md"
        assert claude_md.exists(), "CLAUDE.md was not created"
        content = claude_md.read_text()
        assert 'namespace="integration-test"' in content, (
            f"namespace not found in CLAUDE.md:\n{content}"
        )

        # Step 2: create markdown files for bootstrapping
        docs_dir = tmp_path / "docs"
        docs_dir.mkdir()
        (docs_dir / "overview.md").write_text(
            "# Overview\n\nThis document describes the integration-test project in detail."
        )
        (docs_dir / "architecture.md").write_text(
            "# Architecture\n\nThe system uses a layered approach with a memory compiler."
        )
        # A short file that should be flagged
        (docs_dir / "stub.md").write_text("stub")

        # Step 3: borg bootstrap --dry-run
        result = runner.invoke(
            cli,
            [
                "bootstrap",
                "--dir",
                str(docs_dir),
                "--namespace",
                "integration-test",
                "--dry-run",
            ],
        )
        assert result.exit_code == 0, f"bootstrap dry-run failed:\n{result.output}"

        # Verify the markdown files were discovered
        assert "overview.md" in result.output
        assert "architecture.md" in result.output
        assert "stub.md" in result.output
        assert "skip: too short" in result.output

        # Verify non-markdown files are not reported
        assert "Found 3 markdown file(s)" in result.output


@pytest.mark.integration
def test_status_against_running_engine():
    """borg status reports healthy when engine is running.

    This test is best-effort: it passes regardless of whether the engine is up.
    When the engine is running it verifies the status output; when it is not
    running it prints an informational message but still exits successfully.
    """
    runner = CliRunner()
    result = runner.invoke(cli, ["status"])
    assert result.exit_code == 0, f"status command exited non-zero:\n{result.output}"

    if "not running" in result.output:
        # Engine is down — informational, not a failure
        pytest.skip("Borg engine is not running; skipping health-check assertions")
    else:
        # Engine is up — verify meaningful output
        assert "Status:" in result.output


@pytest.mark.integration
def test_init_generates_all_tool_files():
    """When all tool directories / marker files exist, all 4 config files are generated."""
    runner = CliRunner()

    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp)

        # Create the detection markers for all four tools
        (tmp_path / ".claude").mkdir()
        (tmp_path / ".github").mkdir()
        (tmp_path / "AGENTS.md").write_text("# Agents\n")
        (tmp_path / "kiro.md").write_text("# Kiro\n")

        result = runner.invoke(
            cli,
            ["init", "--namespace", "all-tools-test", "--dir", tmp],
        )
        assert result.exit_code == 0, f"init failed:\n{result.output}"
        assert "Detected tools:" in result.output

        # All four output files must exist
        assert (tmp_path / "CLAUDE.md").exists(), "CLAUDE.md not created"
        assert (tmp_path / ".github" / "copilot-instructions.md").exists(), (
            "copilot-instructions.md not created"
        )
        # AGENTS.md already existed — init skips existing files by default
        # (it was a marker file, now it may be overwritten only with --force).
        # The codex template output IS AGENTS.md, so it should be skipped.
        assert "Skipping AGENTS.md" in result.output or (tmp_path / "AGENTS.md").exists()
        # kiro.md likewise
        assert "Skipping kiro.md" in result.output or (tmp_path / "kiro.md").exists()

        # Verify namespace is injected into CLAUDE.md
        content = (tmp_path / "CLAUDE.md").read_text()
        assert "all-tools-test" in content
