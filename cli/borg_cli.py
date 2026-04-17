"""Borg CLI — thin client for initializing and managing Borg memory."""

from __future__ import annotations

from pathlib import Path

import click
import httpx
from jinja2 import Environment, FileSystemLoader

TEMPLATES_DIR = Path(__file__).parent / "templates"

# Mapping of detected tool -> (template file, output path relative to project dir)
TOOL_CONFIG = {
    "claude": ("CLAUDE.md.j2", "CLAUDE.md"),
    "copilot": ("copilot-instructions.md.j2", ".github/copilot-instructions.md"),
    "codex": ("AGENTS.md.j2", "AGENTS.md"),
    "kiro": ("kiro.md.j2", "kiro.md"),
}


def _detect_tools(project_dir: Path) -> list[str]:
    """Detect which AI coding tools are configured in the project directory."""
    tools: list[str] = []
    if (project_dir / ".claude").is_dir():
        tools.append("claude")
    if (project_dir / ".github").is_dir():
        tools.append("copilot")
    if (project_dir / "AGENTS.md").is_file():
        tools.append("codex")
    if (project_dir / "kiro.md").is_file():
        tools.append("kiro")
    return tools


def _render_template(template_name: str, **kwargs: str) -> str:
    """Render a Jinja2 template from the templates directory."""
    env = Environment(
        loader=FileSystemLoader(str(TEMPLATES_DIR)),
        keep_trailing_newline=True,
    )
    template = env.get_template(template_name)
    return template.render(**kwargs)


@click.group()
def cli() -> None:
    """Borg — persistent memory for AI coding agents."""


@cli.command()
@click.option(
    "--namespace",
    required=True,
    help="Borg namespace for this project.",
)
@click.option(
    "--dir",
    "project_dir",
    default=".",
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help="Project directory to initialize (default: current directory).",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Overwrite existing files.",
)
@click.option(
    "--borg-url",
    default="http://localhost:8080",
    help="Borg engine URL.",
)
def init(namespace: str, project_dir: str, force: bool, borg_url: str) -> None:
    """Initialize Borg memory hooks for a project directory."""
    proj = Path(project_dir)
    tools = _detect_tools(proj)

    if not tools:
        click.echo("No AI tool directories detected. Generating CLAUDE.md as default.")
        tools = ["claude"]
    else:
        click.echo(f"Detected tools: {', '.join(tools)}")

    for tool in tools:
        template_name, rel_output = TOOL_CONFIG[tool]
        output_path = proj / rel_output

        if output_path.exists() and not force:
            click.echo(f"  Skipping {rel_output} (already exists, use --force to overwrite)")
            continue

        # Ensure parent directory exists (e.g., .github/)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        content = _render_template(template_name, namespace=namespace, borg_url=borg_url)
        output_path.write_text(content)
        click.echo(f"  Created {rel_output}")

    click.echo("Done.")


@cli.command()
@click.option(
    "--dir",
    "docs_dir",
    required=True,
    type=click.Path(exists=True, file_okay=False, resolve_path=True),
    help="Directory containing markdown files to ingest.",
)
@click.option(
    "--namespace",
    required=True,
    help="Borg namespace for ingested content.",
)
@click.option(
    "--borg-url",
    default="http://localhost:8080",
    help="Borg engine URL.",
)
@click.option(
    "--source",
    default="bootstrap",
    help="Source label for ingested memories.",
)
@click.option(
    "--dry-run",
    is_flag=True,
    default=False,
    help="List files without ingesting.",
)
def bootstrap(
    docs_dir: str,
    namespace: str,
    borg_url: str,
    source: str,
    dry_run: bool,
) -> None:
    """Bulk-ingest markdown files into Borg memory."""
    docs_path = Path(docs_dir)
    md_files = sorted(docs_path.rglob("*.md"))

    if not md_files:
        click.echo("No .md files found.")
        return

    if dry_run:
        click.echo(f"Found {len(md_files)} markdown file(s):")
        for f in md_files:
            size = f.stat().st_size
            rel = f.relative_to(docs_path)
            skip = " (skip: too short)" if len(f.read_text(encoding="utf-8")) < 20 else ""
            click.echo(f"  {rel} ({size} bytes){skip}")
        return

    headers: dict[str, str] = {"Content-Type": "application/json"}

    ingested = 0
    skipped = 0
    errors = 0

    with httpx.Client(timeout=30.0) as client:
        for f in md_files:
            content = f.read_text(encoding="utf-8")
            rel = f.relative_to(docs_path)

            if len(content) < 20:
                click.echo(f"  Skipped {rel} (too short)")
                skipped += 1
                continue

            payload = {
                "content": content,
                "source": source,
                "namespace": namespace,
                "metadata": {"filename": str(rel)},
            }

            try:
                resp = client.post(f"{borg_url}/api/learn", json=payload, headers=headers)
                resp.raise_for_status()
                click.echo(f"  Ingested {rel}")
                ingested += 1
            except httpx.HTTPError as exc:
                click.echo(f"  Error ingesting {rel}: {exc}")
                errors += 1

    click.echo(f"\nDone: {ingested} ingested, {skipped} skipped, {errors} errors.")


@cli.command()
@click.option(
    "--borg-url",
    default="http://localhost:8080",
    help="Borg engine URL.",
)
def status(borg_url: str) -> None:
    """Check Borg engine health status."""
    try:
        with httpx.Client(timeout=10.0) as client:
            resp = client.get(f"{borg_url}/health")
            resp.raise_for_status()
            data = resp.json()

            click.echo(f"Status:  {data.get('status', 'unknown')}")

            if "profile" in data:
                click.echo(f"Profile: {data['profile']}")

            if "worker" in data:
                worker = data["worker"]
                if isinstance(worker, dict):
                    for key, val in worker.items():
                        click.echo(f"Worker {key}: {val}")
                else:
                    click.echo(f"Worker:  {worker}")

    except httpx.ConnectError:
        click.echo("Borg is not running.")
        click.echo(f"Could not connect to {borg_url}")
        click.echo("Hint: start Borg with `docker compose up -d`")
    except httpx.HTTPError as exc:
        click.echo(f"Error checking Borg status: {exc}")


if __name__ == "__main__":
    cli()
