#!/usr/bin/env python3
"""
Workflow 2: Sync Data to OpenMemory

Responsibilities:
- Merge Chrome Extension + Playwright data
- Prepare data for OpenMemory format
- Generate batch export file
- Provide instructions for Claude Code to import

Professional Principles:
- Idempotent (safe to run multiple times)
- Progress tracking
- Error handling with graceful degradation
- Clear output for next steps

Note: This script PREPARES data for OpenMemory.
Claude Code must call the actual MCP tools to store it.
"""

import sys
import json
from pathlib import Path
from typing import Optional, List, Dict
from datetime import datetime

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Confirm
except ImportError:
    print("Error: 'rich' not installed. Run: uv add rich")
    sys.exit(1)

from src.merger import DataMerger
from src.openmemory_exporter import OpenMemoryExporter

console = Console()

# Configuration
EXTENSION_DB = Path("GPT_Implementation_Proposal/collector/nof1_data.db")
PLAYWRIGHT_DIR = Path("data")
OUTPUT_DIR = Path("data/openmemory_export")


class OpenMemorySyncer:
    """Handles syncing data to OpenMemory"""

    def __init__(
        self,
        extension_db: Path,
        playwright_dir: Path,
        output_dir: Path
    ):
        self.extension_db = extension_db
        self.playwright_dir = playwright_dir
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)

    def check_prerequisites(self) -> bool:
        """Check if required components are available"""
        checks = []

        # Check extension database
        if self.extension_db.exists():
            checks.append(("Extension Database", True, str(self.extension_db)))
        else:
            checks.append(("Extension Database", False, "Not found"))

        # Check playwright data
        playwright_exists = self.playwright_dir.exists()
        checks.append(("Playwright Data Dir", playwright_exists, str(self.playwright_dir)))

        # Display results
        table = Table(title="Prerequisites Check")
        table.add_column("Component", style="cyan")
        table.add_column("Status", style="green")
        table.add_column("Location", style="dim")

        all_ok = True
        for component, status, location in checks:
            status_str = "[green]OK[/green]" if status else "[red]MISSING[/red]"
            table.add_row(component, status_str, location)
            if not status and component == "Extension Database":
                all_ok = False

        console.print(table)
        console.print()

        return all_ok

    def get_data_summary(self, merger: DataMerger) -> Dict:
        """Get summary of available data"""
        with console.status("[cyan]Analyzing data sources..."):
            stats = merger.get_merge_statistics()
        return stats

    def display_summary(self, stats: Dict):
        """Display data summary"""
        console.print("[bold]Data Summary:[/bold]\n")

        # Source counts
        ext_count = stats["extension"]["total_messages"]
        pw_count = stats["playwright"]["total_messages"]
        merged_count = stats["merged"]["total_unique_messages"]
        dupes = stats["merged"]["duplicates_removed"]

        summary_table = Table(show_header=False)
        summary_table.add_column("Source", style="cyan")
        summary_table.add_column("Count", style="green", justify="right")

        summary_table.add_row("Chrome Extension", str(ext_count))
        summary_table.add_row("Playwright Scraper", str(pw_count))
        summary_table.add_row("", "")
        summary_table.add_row("Total Unique", str(merged_count))
        summary_table.add_row("Duplicates Removed", str(dupes))

        console.print(summary_table)
        console.print()

        # Model breakdown
        if stats["merged"]["by_model"]:
            console.print("[bold]By Model:[/bold]\n")

            model_table = Table()
            model_table.add_column("Model", style="cyan")
            model_table.add_column("Messages", style="green", justify="right")
            model_table.add_column("Priority", style="magenta")

            priority_map = {
                "deepseek-v3.1": "[1] Highest P/L",
                "qwen3-max": "[2] Second P/L",
                "claude-sonnet-4.5": "[3] Negative P/L"
            }

            for model, count in stats["merged"]["by_model"].items():
                priority = priority_map.get(model, "")
                model_table.add_row(model, str(count), priority)

            console.print(model_table)
            console.print()

    def export_batch_file(
        self,
        exporter: OpenMemoryExporter,
        model_filter: Optional[str] = None
    ) -> Path:
        """Export batch file for OpenMemory import"""

        # Determine filename
        if model_filter:
            filename = f"openmemory_batch_{model_filter}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        else:
            filename = f"openmemory_batch_all_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"

        output_path = self.output_dir / filename

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            console=console
        ) as progress:

            task = progress.add_task(
                f"[cyan]Preparing data...",
                total=None
            )

            # Prepare all messages
            prepared = exporter.prepare_all_for_export(model_filter=model_filter)

            progress.update(task, completed=True)

            # Save to file
            task2 = progress.add_task(
                f"[cyan]Writing to {filename}...",
                total=None
            )

            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(prepared, f, indent=2, ensure_ascii=False)

            progress.update(task2, completed=True)

        return output_path

    def display_next_steps(self, batch_file: Path, message_count: int):
        """Display instructions for next steps"""
        console.print("\n[bold green]Export Complete![/bold green]\n")

        console.print(f"Batch file created: [cyan]{batch_file}[/cyan]")
        console.print(f"Total messages: [green]{message_count}[/green]\n")

        # Next steps panel
        next_steps = """
[bold]Next Steps:[/bold]

1. Make sure OpenMemory MCP is running:
   [cyan]cd C:\\Dev\\openmemory\\backend[/cyan]
   [cyan]npm run mcp[/cyan]

2. Ask Claude Code to import the batch file:
   [cyan]"Read the file {batch_file} and import all messages to OpenMemory
   using mcp__openmemory__openmemory_store for each item"[/cyan]

3. After import, you can query with semantic search:
   [cyan]mcp__openmemory__openmemory_query(
       query="DeepSeek risk management strategies",
       k=10
   )[/cyan]
""".format(batch_file=batch_file.name)

        console.print(Panel(next_steps, title="Next Steps", border_style="cyan"))

    def run(self, model_filter: Optional[str] = None, auto_yes: bool = False):
        """Main sync workflow"""
        console.print("\n[bold cyan]Sync Data to OpenMemory[/bold cyan]\n")

        # Check prerequisites
        if not self.check_prerequisites():
            console.print("[bold red]Error:[/bold red] Extension database not found")
            console.print("\nStart the collector first:")
            console.print("[cyan]uv run python workflows/start_capture.py[/cyan]")
            return False

        # Create merger
        try:
            merger = DataMerger(self.extension_db, self.playwright_dir)
            exporter = OpenMemoryExporter(merger)
        except Exception as e:
            console.print(f"[bold red]Error:[/bold red] Failed to initialize: {e}")
            return False

        # Get and display summary
        stats = self.get_data_summary(merger)
        self.display_summary(stats)

        # Check if any data available
        if stats["merged"]["total_unique_messages"] == 0:
            console.print("[yellow]No messages available to export[/yellow]")
            console.print("\nWait for data to be captured, then try again")
            return False

        # Confirm export
        if not auto_yes:
            if model_filter:
                prompt = f"Export {model_filter} data to OpenMemory batch file?"
            else:
                prompt = "Export ALL models to OpenMemory batch file?"

            if not Confirm.ask(prompt, default=True):
                console.print("[yellow]Export cancelled[/yellow]")
                return False

        # Export batch file
        console.print()
        batch_file = self.export_batch_file(exporter, model_filter)

        # Count messages in batch file
        with open(batch_file) as f:
            batch_data = json.load(f)
            message_count = len(batch_data)

        # Display next steps
        self.display_next_steps(batch_file, message_count)

        return True


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Sync captured data to OpenMemory"
    )
    parser.add_argument(
        "--model",
        "-m",
        help="Export only this model (e.g., 'deepseek-v3.1')"
    )
    parser.add_argument(
        "--yes",
        "-y",
        action="store_true",
        help="Skip confirmation prompts"
    )

    args = parser.parse_args()

    syncer = OpenMemorySyncer(
        extension_db=EXTENSION_DB,
        playwright_dir=PLAYWRIGHT_DIR,
        output_dir=OUTPUT_DIR
    )

    success = syncer.run(model_filter=args.model, auto_yes=args.yes)

    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
