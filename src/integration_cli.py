"""
Integration CLI - Command-line interface for data integration operations
Combines Chrome Extension + Playwright data and prepares for OpenMemory
"""

import typer
from pathlib import Path
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.progress import Progress
import json
from typing import Optional

from .merger import DataMerger
from .openmemory_exporter import OpenMemoryExporter

app = typer.Typer(help="NOF1.AI Data Integration CLI")
console = Console()


# Default paths
DEFAULT_EXTENSION_DB = Path("GPT_Implementation_Proposal/collector/nof1_data.db")
DEFAULT_PLAYWRIGHT_DIR = Path("data")
DEFAULT_OUTPUT_DIR = Path("data/integrated")


@app.command()
def stats(
    extension_db: Path = typer.Option(
        DEFAULT_EXTENSION_DB,
        "--extension-db",
        "-e",
        help="Path to Chrome extension SQLite database"
    ),
    playwright_dir: Path = typer.Option(
        DEFAULT_PLAYWRIGHT_DIR,
        "--playwright-dir",
        "-p",
        help="Path to Playwright data directory"
    )
):
    """
    Show statistics about available data from all sources
    """
    console.print("\n[bold cyan]Data Integration Statistics[/bold cyan]\n")

    try:
        merger = DataMerger(extension_db, playwright_dir)
        stats = merger.get_merge_statistics()

        # Extension stats
        console.print("[bold]Chrome Extension Data:[/bold]")
        ext_table = Table(show_header=False)
        ext_table.add_column("Metric", style="cyan")
        ext_table.add_column("Value", style="green")
        ext_table.add_row("Total Messages", str(stats["extension"]["total_messages"]))
        ext_table.add_row("Database", str(stats["extension"]["database_path"]))
        ext_table.add_row("First Message", stats["extension"]["first_message"] or "N/A")
        ext_table.add_row("Last Message", stats["extension"]["last_message"] or "N/A")
        console.print(ext_table)
        console.print()

        # By model (extension)
        console.print("[bold]Extension Messages by Model:[/bold]")
        model_table = Table()
        model_table.add_column("Model", style="cyan")
        model_table.add_column("Count", style="green", justify="right")
        for model, count in stats["extension"]["by_model"].items():
            model_table.add_row(model, str(count))
        console.print(model_table)
        console.print()

        # Playwright stats
        console.print("[bold]Playwright Scraped Data:[/bold]")
        pw_table = Table(show_header=False)
        pw_table.add_column("Metric", style="cyan")
        pw_table.add_column("Value", style="green")
        pw_table.add_row("Total Messages", str(stats["playwright"]["total_messages"]))
        console.print(pw_table)
        console.print()

        # Merged stats
        console.print("[bold]Merged (Deduplicated) Data:[/bold]")
        merged_table = Table(show_header=False)
        merged_table.add_column("Metric", style="cyan")
        merged_table.add_column("Value", style="green")
        merged_table.add_row("Total Unique Messages", str(stats["merged"]["total_unique_messages"]))
        merged_table.add_row("Duplicates Removed", str(stats["merged"]["duplicates_removed"]))
        console.print(merged_table)
        console.print()

        # Priority models
        console.print("[bold]Priority Models (by P/L):[/bold]")
        priority_table = Table()
        priority_table.add_column("Priority", style="yellow")
        priority_table.add_column("Model", style="cyan")
        priority_table.add_column("Messages", style="green", justify="right")
        priority_table.add_column("Performance", style="magenta")

        priority_models = [
            ("[1]", "deepseek-v3.1", "Highest P/L"),
            ("[2]", "qwen3-max", "Second P/L"),
            ("[3]", "claude-sonnet-4.5", "Negative P/L")
        ]

        for priority, model_name, perf in priority_models:
            count = stats["merged"]["by_model"].get(model_name, 0)
            priority_table.add_row(priority, model_name, str(count), perf)

        console.print(priority_table)

    except FileNotFoundError as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        console.print("\n[yellow]Make sure the Chrome extension collector is running and has created the database.[/yellow]")
        raise typer.Exit(1)
    except Exception as e:
        console.print(f"[bold red]Unexpected error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def export_json(
    output: Path = typer.Argument(
        ...,
        help="Output JSON file path"
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Export only this model (e.g., 'deepseek-v3.1')"
    ),
    extension_db: Path = typer.Option(
        DEFAULT_EXTENSION_DB,
        "--extension-db",
        "-e",
        help="Path to Chrome extension SQLite database"
    ),
    playwright_dir: Path = typer.Option(
        DEFAULT_PLAYWRIGHT_DIR,
        "--playwright-dir",
        "-p",
        help="Path to Playwright data directory"
    )
):
    """
    Export merged data to JSON file
    """
    console.print(f"\n[bold cyan]Exporting merged data to {output}[/bold cyan]\n")

    try:
        merger = DataMerger(extension_db, playwright_dir)
        merger.export_merged_to_json(output, model_name=model)
        console.print(f"\n[bold green]Export complete![/bold green]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def prepare_openmemory(
    output: Optional[Path] = typer.Option(
        None,
        "--output",
        "-o",
        help="Save prepared data to JSON file (for inspection)"
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Prepare only this model (e.g., 'deepseek-v3.1')"
    ),
    limit: int = typer.Option(
        5,
        "--limit",
        "-l",
        help="Number of samples to show/save"
    ),
    extension_db: Path = typer.Option(
        DEFAULT_EXTENSION_DB,
        "--extension-db",
        "-e",
        help="Path to Chrome extension SQLite database"
    ),
    playwright_dir: Path = typer.Option(
        DEFAULT_PLAYWRIGHT_DIR,
        "--playwright-dir",
        "-p",
        help="Path to Playwright data directory"
    )
):
    """
    Prepare data for OpenMemory export (Claude Code will do the actual MCP calls)

    This command shows you what will be exported and optionally saves samples to a file.
    You (Claude Code) will then use mcp__openmemory__openmemory_store to actually send it.
    """
    console.print("\n[bold cyan]Preparing data for OpenMemory[/bold cyan]\n")

    try:
        merger = DataMerger(extension_db, playwright_dir)
        exporter = OpenMemoryExporter(merger)

        # Get statistics
        stats = exporter.get_export_statistics()

        console.print("[bold]Export Statistics:[/bold]")
        stats_table = Table(show_header=False)
        stats_table.add_column("Metric", style="cyan")
        stats_table.add_column("Value", style="green")
        stats_table.add_row("Total Messages", str(stats["total_messages"]))
        stats_table.add_row("Unique Tags", str(stats["unique_tags"]))
        console.print(stats_table)
        console.print()

        console.print("[bold]Messages by Model:[/bold]")
        model_table = Table()
        model_table.add_column("Model", style="cyan")
        model_table.add_column("Count", style="green", justify="right")
        for model_name, count in stats["by_model"].items():
            model_table.add_row(model_name, str(count))
        console.print(model_table)
        console.print()

        console.print("[bold]Top Tags:[/bold]")
        tag_table = Table()
        tag_table.add_column("Tag", style="cyan")
        tag_table.add_column("Count", style="green", justify="right")
        for tag, count in list(stats["top_tags"].items())[:15]:
            tag_table.add_row(tag, str(count))
        console.print(tag_table)
        console.print()

        # Save sample if requested
        if output:
            exporter.export_sample_to_file(output, limit=limit)
            console.print(f"\n[bold green]Saved {limit} samples to {output}[/bold green]")
            console.print("\n[yellow]Review the samples, then use Claude Code to call:[/yellow]")
            console.print("[yellow]  mcp__openmemory__openmemory_store[/yellow]")
        else:
            console.print("[bold]Sample prepared data:[/bold]")
            prepared = exporter.prepare_all_for_export(model_filter=model)[:limit]
            for i, item in enumerate(prepared, 1):
                console.print(f"\n[bold cyan]Sample {i}:[/bold cyan]")
                console.print(Panel(
                    item["content"][:300] + "...",
                    title=f"Tags: {', '.join(item['tags'][:5])}..."
                ))

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


@app.command()
def export_openmemory_batch(
    output: Path = typer.Argument(
        ...,
        help="Output JSON file with batch data for OpenMemory"
    ),
    model: Optional[str] = typer.Option(
        None,
        "--model",
        "-m",
        help="Export only this model"
    ),
    extension_db: Path = typer.Option(
        DEFAULT_EXTENSION_DB,
        "--extension-db",
        "-e",
        help="Path to Chrome extension SQLite database"
    ),
    playwright_dir: Path = typer.Option(
        DEFAULT_PLAYWRIGHT_DIR,
        "--playwright-dir",
        "-p",
        help="Path to Playwright data directory"
    )
):
    """
    Export ALL prepared data to JSON for batch OpenMemory import

    Claude Code can then read this file and loop through calling
    mcp__openmemory__openmemory_store for each item.
    """
    console.print("\n[bold cyan]Exporting batch data for OpenMemory[/bold cyan]\n")

    try:
        merger = DataMerger(extension_db, playwright_dir)
        exporter = OpenMemoryExporter(merger)

        prepared = exporter.prepare_all_for_export(model_filter=model)

        output.parent.mkdir(parents=True, exist_ok=True)
        with open(output, 'w', encoding='utf-8') as f:
            json.dump(prepared, f, indent=2, ensure_ascii=False)

        console.print(f"[bold green]Exported {len(prepared)} messages to {output}[/bold green]")
        console.print("\n[yellow]Claude Code: Read this file and call mcp__openmemory__openmemory_store for each item[/yellow]")

    except Exception as e:
        console.print(f"[bold red]Error:[/bold red] {e}")
        raise typer.Exit(1)


if __name__ == "__main__":
    app()
