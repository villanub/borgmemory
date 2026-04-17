"""Tests for the Borg CLI."""

from __future__ import annotations

import tempfile
from pathlib import Path

from click.testing import CliRunner

from cli.borg_cli import cli


def test_init_detects_claude_directory():
    """.claude/ dir -> generates CLAUDE.md."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".claude").mkdir()
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--namespace", "test-ns", "--dir", tmp])
        assert result.exit_code == 0
        assert "Detected tools: claude" in result.output
        claude_md = Path(tmp) / "CLAUDE.md"
        assert claude_md.exists()
        content = claude_md.read_text()
        assert 'namespace="test-ns"' in content


def test_init_detects_github_copilot():
    """.github/ dir -> generates .github/copilot-instructions.md."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / ".github").mkdir()
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--namespace", "copilot-ns", "--dir", tmp])
        assert result.exit_code == 0
        assert "copilot" in result.output
        copilot_md = Path(tmp) / ".github" / "copilot-instructions.md"
        assert copilot_md.exists()
        content = copilot_md.read_text()
        assert "copilot-ns" in content


def test_init_creates_claude_md_by_default():
    """No tool dirs -> still generates CLAUDE.md."""
    with tempfile.TemporaryDirectory() as tmp:
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--namespace", "fallback-ns", "--dir", tmp])
        assert result.exit_code == 0
        assert "No AI tool directories detected" in result.output
        assert (Path(tmp) / "CLAUDE.md").exists()


def test_init_does_not_overwrite_existing():
    """Existing CLAUDE.md -> skips, doesn't clobber."""
    with tempfile.TemporaryDirectory() as tmp:
        claude_md = Path(tmp) / "CLAUDE.md"
        claude_md.write_text("original content")
        (Path(tmp) / ".claude").mkdir()
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--namespace", "test-ns", "--dir", tmp])
        assert result.exit_code == 0
        assert "Skipping" in result.output
        assert claude_md.read_text() == "original content"


def test_init_force_overwrites_existing():
    """--force flag overwrites existing files."""
    with tempfile.TemporaryDirectory() as tmp:
        claude_md = Path(tmp) / "CLAUDE.md"
        claude_md.write_text("original content")
        (Path(tmp) / ".claude").mkdir()
        runner = CliRunner()
        result = runner.invoke(cli, ["init", "--namespace", "test-ns", "--dir", tmp, "--force"])
        assert result.exit_code == 0
        assert "Created CLAUDE.md" in result.output
        assert claude_md.read_text() != "original content"


def test_bootstrap_finds_markdown_files():
    """Dry-run finds .md files, ignores .txt, flags short files."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "readme.md").write_text("This is a readme with enough content to pass.")
        (Path(tmp) / "short.md").write_text("tiny")
        (Path(tmp) / "notes.txt").write_text("This is a text file, not markdown.")
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["bootstrap", "--dir", tmp, "--namespace", "test-ns", "--dry-run"],
        )
        assert result.exit_code == 0
        assert "readme.md" in result.output
        assert "short.md" in result.output
        assert "skip: too short" in result.output
        assert "notes.txt" not in result.output


def test_bootstrap_skips_short_files():
    """Normal mode skips files shorter than 20 chars."""
    with tempfile.TemporaryDirectory() as tmp:
        (Path(tmp) / "tiny.md").write_text("hi")
        runner = CliRunner()
        result = runner.invoke(
            cli,
            ["bootstrap", "--dir", tmp, "--namespace", "test-ns"],
        )
        assert result.exit_code == 0
        assert "Skipped tiny.md" in result.output
        assert "0 ingested" in result.output
        assert "1 skipped" in result.output


def test_status_reports_unreachable():
    """Bad URL -> 'not running' message."""
    runner = CliRunner()
    result = runner.invoke(cli, ["status", "--borg-url", "http://localhost:19999"])
    assert result.exit_code == 0
    assert "not running" in result.output
    assert "docker compose" in result.output
