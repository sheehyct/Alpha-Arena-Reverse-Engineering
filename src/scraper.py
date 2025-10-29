"""
Main scraper orchestration

This module coordinates the scraping process:
1. Navigate to nof1.ai using Playwright MCP
2. Expand messages
3. Extract chain of thought data
4. Store in local files and OpenMemory
"""

from datetime import datetime
from pathlib import Path
from typing import List, Optional
from rich.console import Console
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from .models import ModelMessage, ScrapeResult
from .storage import StorageManager
from .chain_extractor import ChainExtractor
from .nof1_navigator import Nof1Navigator, NavigationConfig, MessageExpander

console = Console()


class Nof1Scraper:
    """Main scraper class for nof1.ai chain of thought data"""

    def __init__(
        self,
        data_dir: Path,
        max_messages: int = 50,
        filter_model: Optional[str] = None,
        use_openmemory: bool = True,
    ):
        """
        Initialize the scraper

        Args:
            data_dir: Directory to store scraped data
            max_messages: Maximum number of messages to scrape
            filter_model: Optional model name to filter by
            use_openmemory: Whether to store in OpenMemory
        """
        self.data_dir = Path(data_dir)
        self.max_messages = max_messages
        self.filter_model = filter_model

        # Initialize components
        self.storage = StorageManager(self.data_dir, use_openmemory=use_openmemory)
        self.extractor = ChainExtractor()
        self.navigator = Nof1Navigator(
            NavigationConfig(
                max_messages=max_messages,
                filter_model=filter_model,
            )
        )

        console.print(f"[bold green]Initialized nof1.ai scraper[/bold green]")
        console.print(f"Data directory: {self.data_dir}")
        console.print(f"Max messages: {self.max_messages}")
        if self.filter_model:
            console.print(f"Filter model: {self.filter_model}")

    def print_navigation_guide(self):
        """
        Print a guide for manual navigation when running in Claude Code

        This provides instructions for Claude Code to follow using MCP tools
        """
        console.print("\n[bold cyan]Navigation Guide for Claude Code[/bold cyan]")
        console.print("\nFollow these steps using MCP Playwright tools:\n")

        for i, step in enumerate(self.navigator.get_navigation_steps(), 1):
            console.print(f"{i}. {step}")

        console.print("\n[bold]Selectors:[/bold]")
        selectors = self.navigator.get_selector_patterns()
        for name, selector in selectors.items():
            console.print(f"  {name}: {selector}")

    def get_scraping_plan(self) -> dict:
        """
        Generate a detailed scraping plan for execution in Claude Code

        Returns:
            Dictionary with step-by-step instructions
        """
        return {
            "overview": "Scrape chain of thought data from nof1.ai",
            "steps": self.navigator.get_navigation_steps(),
            "selectors": self.navigator.get_selector_patterns(),
            "mcp_plan": self.navigator.get_mcp_navigation_plan(),
            "config": {
                "max_messages": self.max_messages,
                "filter_model": self.filter_model,
                "data_dir": str(self.data_dir),
            },
        }

    def process_snapshot(self, snapshot_data: str) -> Optional[ModelMessage]:
        """
        Process a browser snapshot to extract message data

        Args:
            snapshot_data: YAML snapshot from Playwright

        Returns:
            ModelMessage if extraction successful
        """
        try:
            # Convert snapshot string to dictionary format
            # This is simplified - actual implementation would parse YAML
            snapshot_dict = {"raw": snapshot_data}

            message = self.extractor.extract_from_snapshot(snapshot_dict)

            if message:
                console.print(
                    f"[green]OK[/green] Extracted: {message.model_name} "
                    f"at {message.timestamp.strftime('%m/%d %H:%M:%S')}"
                )
            else:
                console.print("[yellow]WARN[/yellow] Could not extract message data")

            return message

        except Exception as e:
            console.print(f"[red]✗ Error processing snapshot: {e}[/red]")
            return None

    def store_message(self, message: ModelMessage) -> bool:
        """
        Store a message to all configured backends

        Args:
            message: The message to store

        Returns:
            True if stored successfully
        """
        success = self.storage.save_message(message)

        if success:
            console.print(
                f"[green]OK[/green] Stored message from {message.model_name}"
            )
        else:
            console.print(
                f"[red]ERROR[/red] Failed to store message from {message.model_name}"
            )

        return success

    def get_openmemory_store_call(self, message: ModelMessage) -> dict:
        """
        Get the MCP tool call data for storing in OpenMemory

        This returns the exact parameters needed for:
        mcp__openmemory__openmemory_store(...)

        Args:
            message: The message to prepare for storage

        Returns:
            Dictionary with content, tags, and metadata
        """
        return self.storage.get_openmemory_store_data(message)

    def generate_summary(self, messages: List[ModelMessage]) -> None:
        """
        Generate and print a summary of scraped messages

        Args:
            messages: List of scraped messages
        """
        if not messages:
            console.print("[yellow]No messages scraped[/yellow]")
            return

        console.print("\n[bold cyan]Scrape Summary[/bold cyan]\n")

        # Create summary table
        table = Table(title="Messages by Model")
        table.add_column("Model", style="cyan")
        table.add_column("Count", justify="right", style="green")
        table.add_column("Avg Return", justify="right", style="yellow")

        # Group by model
        by_model = {}
        for msg in messages:
            if msg.model_name not in by_model:
                by_model[msg.model_name] = []
            by_model[msg.model_name].append(msg)

        for model_name in sorted(by_model.keys()):
            model_messages = by_model[model_name]
            count = len(model_messages)

            # Calculate average return
            returns = [m.total_return for m in model_messages if m.total_return]
            avg_return = sum(returns) / len(returns) if returns else 0

            table.add_row(
                model_name,
                str(count),
                f"{avg_return:+.2f}%",
            )

        console.print(table)

        # Time range
        timestamps = [m.timestamp for m in messages]
        console.print(f"\n[bold]Time Range:[/bold]")
        console.print(f"  Earliest: {min(timestamps).strftime('%Y-%m-%d %H:%M:%S')}")
        console.print(f"  Latest: {max(timestamps).strftime('%Y-%m-%d %H:%M:%S')}")

        # Storage info
        console.print(f"\n[bold]Storage:[/bold]")
        console.print(f"  Location: {self.data_dir / 'raw'}")
        console.print(f"  Files: {len(messages)} JSON files")

    def get_storage_stats(self) -> dict:
        """Get current storage statistics"""
        return self.storage.get_storage_stats()


class ScrapeSession:
    """
    Manages a scraping session with progress tracking

    This is used when running the scraper interactively
    """

    def __init__(self, scraper: Nof1Scraper):
        self.scraper = scraper
        self.start_time = datetime.now()
        self.messages_scraped: List[ModelMessage] = []
        self.errors: List[str] = []

    def add_message(self, message: ModelMessage):
        """Add a successfully scraped message"""
        self.messages_scraped.append(message)

    def add_error(self, error: str):
        """Add an error"""
        self.errors.append(error)

    def get_result(self) -> ScrapeResult:
        """Generate final scrape result"""
        return ScrapeResult(
            success=len(self.errors) == 0,
            messages_scraped=len(self.messages_scraped),
            messages_stored=len(self.messages_scraped),  # Assuming all stored
            errors=self.errors,
            start_time=self.start_time,
            end_time=datetime.now(),
        )

    def print_result(self):
        """Print the final result"""
        result = self.get_result()

        console.print("\n[bold]Scrape Complete![/bold]")
        console.print(f"Duration: {result.duration_seconds:.1f} seconds")
        console.print(f"Messages scraped: {result.messages_scraped}")
        console.print(f"Messages stored: {result.messages_stored}")

        if result.errors:
            console.print(f"\n[yellow]Errors: {len(result.errors)}[/yellow]")
            for error in result.errors[:5]:  # Show first 5
                console.print(f"  - {error}")

        self.scraper.generate_summary(self.messages_scraped)
