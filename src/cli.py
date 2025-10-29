"""
Command-line interface for nof1.ai scraper
"""

import json
from pathlib import Path
from typing import Optional
import typer
from rich.console import Console
from rich.panel import Panel
from rich import print as rprint

from .scraper import Nof1Scraper, ScrapeSession
from .storage import StorageManager

app = typer.Typer(
    help="nof1.ai Chain of Thought Scraper - Extract reasoning from AI trading models"
)
console = Console()


@app.command()
def guide(
    max_messages: int = typer.Option(20, help="Maximum messages to scrape"),
    filter_model: Optional[str] = typer.Option(None, help="Filter by model name"),
    data_dir: Path = typer.Option(
        Path("./data"),
        help="Directory to store scraped data"
    ),
):
    """
    Show navigation guide for scraping with Claude Code + MCP

    This displays step-by-step instructions for using MCP Playwright tools
    to scrape nof1.ai within Claude Code.
    """
    scraper = Nof1Scraper(
        data_dir=data_dir,
        max_messages=max_messages,
        filter_model=filter_model,
    )

    # Print navigation guide
    scraper.print_navigation_guide()

    # Show example MCP tool calls
    console.print("\n[bold cyan]Example MCP Tool Calls:[/bold cyan]\n")

    plan = scraper.get_scraping_plan()
    mcp_plan = plan["mcp_plan"]

    for i, step in enumerate(mcp_plan["steps"][:3], 1):
        console.print(f"[bold]Step {i}: {step['action']}[/bold]")
        console.print(f"Tool: {step['tool']}")
        console.print(f"Params: {json.dumps(step.get('params', {}), indent=2)}")
        console.print()


@app.command()
def plan(
    max_messages: int = typer.Option(20, help="Maximum messages to scrape"),
    filter_model: Optional[str] = typer.Option(None, help="Filter by model name"),
    data_dir: Path = typer.Option(
        Path("./data"),
        help="Directory to store scraped data"
    ),
    output: Optional[Path] = typer.Option(None, help="Save plan to JSON file"),
):
    """
    Generate a scraping plan (for inspection or automation)

    This generates a detailed plan that can be saved and used for
    automated scraping.
    """
    scraper = Nof1Scraper(
        data_dir=data_dir,
        max_messages=max_messages,
        filter_model=filter_model,
    )

    plan = scraper.get_scraping_plan()

    if output:
        with open(output, "w") as f:
            json.dump(plan, f, indent=2)
        console.print(f"[green]✓ Plan saved to {output}[/green]")
    else:
        rprint(plan)


@app.command()
def stats(
    data_dir: Path = typer.Option(
        Path("./data"),
        help="Directory containing scraped data"
    ),
):
    """
    Show statistics about scraped data

    Displays information about stored messages, models, and time ranges.
    """
    storage = StorageManager(data_dir)

    stats = storage.get_storage_stats()

    if stats["total_messages"] == 0:
        console.print("[yellow]No messages found in storage[/yellow]")
        return

    # Display stats in a nice panel
    stats_text = f"""
[bold]Total Messages:[/bold] {stats['total_messages']}
[bold]Total Files:[/bold] {stats['total_files']}
[bold]Unique Models:[/bold] {stats['unique_models']}

[bold]Models:[/bold]
{chr(10).join(f"  • {model}" for model in stats['models'])}

[bold]Date Range:[/bold]
  From: {stats['date_range']['earliest'].strftime('%Y-%m-%d %H:%M:%S') if stats['date_range']['earliest'] else 'N/A'}
  To:   {stats['date_range']['latest'].strftime('%Y-%m-%d %H:%M:%S') if stats['date_range']['latest'] else 'N/A'}

[bold]Storage:[/bold]
  {stats['storage_path']}
"""

    console.print(Panel(stats_text, title="Storage Statistics", border_style="cyan"))


@app.command()
def search(
    query: str = typer.Argument(..., help="Search query"),
    model: Optional[str] = typer.Option(None, help="Filter by model name"),
    data_dir: Path = typer.Option(
        Path("./data"),
        help="Directory containing scraped data"
    ),
    limit: int = typer.Option(10, help="Maximum results to show"),
):
    """
    Search scraped messages (local search)

    Performs a simple text search through locally stored messages.
    For semantic search, use OpenMemory queries.
    """
    storage = StorageManager(data_dir)

    messages = storage.load_messages(model_name=model)

    if not messages:
        console.print("[yellow]No messages found[/yellow]")
        return

    # Simple text search
    query_lower = query.lower()
    results = []

    for msg in messages:
        if query_lower in msg.chain_of_thought.lower():
            results.append(msg)

    console.print(f"\nFound {len(results)} results for '{query}'\n")

    for i, msg in enumerate(results[:limit], 1):
        console.print(f"[bold cyan]{i}. {msg.model_name}[/bold cyan] - {msg.timestamp}")
        console.print(f"Return: {msg.total_return:+.2f}% | Value: ${msg.account_value:,.2f}")

        # Show snippet
        idx = msg.chain_of_thought.lower().find(query_lower)
        start = max(0, idx - 50)
        end = min(len(msg.chain_of_thought), idx + 100)
        snippet = msg.chain_of_thought[start:end].strip()

        console.print(f"  ...{snippet}...\n")


@app.command()
def init(
    data_dir: Path = typer.Option(
        Path("./data"),
        help="Directory to initialize"
    ),
):
    """
    Initialize data directories

    Creates the necessary directory structure for the scraper.
    """
    data_dir = Path(data_dir)
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    console.print(f"[green]✓ Initialized directories:[/green]")
    console.print(f"  {raw_dir}")
    console.print(f"  {processed_dir}")


@app.command()
def interactive():
    """
    Interactive scraping assistant

    Guides you through the scraping process step by step.
    This is intended for use within Claude Code with MCP.
    """
    console.print(Panel(
        "[bold cyan]nof1.ai Interactive Scraper[/bold cyan]\n\n"
        "This tool will guide you through scraping chain of thought data.\n\n"
        "[yellow]Note:[/yellow] This requires Claude Code with MCP Playwright integration.",
        border_style="cyan"
    ))

    # Get configuration
    max_messages = typer.prompt("Maximum messages to scrape", default=20, type=int)
    filter_model = typer.prompt(
        "Filter by model (or press Enter for all)",
        default="",
        show_default=False
    )
    data_dir = Path(typer.prompt("Data directory", default="./data"))

    if not filter_model:
        filter_model = None

    # Initialize scraper
    scraper = Nof1Scraper(
        data_dir=data_dir,
        max_messages=max_messages,
        filter_model=filter_model,
    )

    # Show guide
    console.print("\n[bold]Step 1: Navigation Guide[/bold]")
    scraper.print_navigation_guide()

    console.print("\n[bold]Step 2: Ready to Start[/bold]")
    console.print(
        "\nNow, use Claude Code to execute the MCP Playwright commands "
        "shown above to navigate and scrape the data."
    )


if __name__ == "__main__":
    app()
