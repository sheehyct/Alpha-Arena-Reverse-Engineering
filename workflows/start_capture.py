#!/usr/bin/env python3
"""
Workflow 1: Start and Monitor Data Capture

Responsibilities:
- Check if Node.js collector is running
- Start collector if needed (or provide instructions)
- Monitor database for new messages
- Display live statistics
- Handle graceful shutdown

Professional Principles:
- Single responsibility (capture only)
- Fail-fast with clear error messages
- Observable (real-time stats)
- Graceful degradation
"""

import subprocess
import time
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from typing import Optional, Dict
import signal

# Rich for terminal UI
try:
    from rich.console import Console
    from rich.live import Live
    from rich.table import Table
    from rich.panel import Panel
    from rich.layout import Layout
except ImportError:
    print("Error: 'rich' not installed. Run: uv add rich")
    sys.exit(1)

console = Console()

# Configuration
PROJECT_ROOT = Path(__file__).parent.parent
COLLECTOR_DIR = PROJECT_ROOT / "collector"
SERVER_SCRIPT = COLLECTOR_DIR / "server.js"
DATABASE_PATH = COLLECTOR_DIR / "nof1_data.db"
CHECK_INTERVAL = 5  # seconds


class CaptureMonitor:
    """Monitors the data capture process"""

    def __init__(self):
        self.running = True
        self.collector_process: Optional[subprocess.Popen] = None
        self.start_time = datetime.now()
        self.last_count = 0

        # Setup signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)

    def signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        self.running = False

    def check_collector_running(self) -> bool:
        """Check if Node.js collector is already running"""
        try:
            # Try to read from database (if collector running, it should exist)
            if not DATABASE_PATH.exists():
                return False

            # On Windows, check if node process is running on port 8787
            if sys.platform == "win32":
                result = subprocess.run(
                    ["netstat", "-ano"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return ":8787" in result.stdout
            else:
                # Unix-like systems
                result = subprocess.run(
                    ["lsof", "-i", ":8787"],
                    capture_output=True,
                    text=True,
                    timeout=5
                )
                return result.returncode == 0

        except Exception:
            return False

    def get_database_stats(self) -> Dict:
        """Get current statistics from database"""
        if not DATABASE_PATH.exists():
            return {
                "total": 0,
                "by_model": {},
                "last_message": None
            }

        try:
            conn = sqlite3.connect(DATABASE_PATH)
            cursor = conn.cursor()

            # Total messages
            cursor.execute("SELECT COUNT(*) FROM model_chat")
            total = cursor.fetchone()[0]

            # By model
            cursor.execute("""
                SELECT model_name, COUNT(*) as count
                FROM model_chat
                GROUP BY model_name
                ORDER BY count DESC
            """)
            by_model = {row[0]: row[1] for row in cursor.fetchall()}

            # Last message timestamp
            cursor.execute("SELECT MAX(scraped_at) FROM model_chat")
            last_message = cursor.fetchone()[0]

            conn.close()

            return {
                "total": total,
                "by_model": by_model,
                "last_message": last_message
            }

        except Exception as e:
            return {
                "total": 0,
                "by_model": {},
                "last_message": None,
                "error": str(e)
            }

    def generate_status_table(self, stats: Dict) -> Table:
        """Generate live status table"""
        table = Table(title="Capture Status", show_header=True)
        table.add_column("Metric", style="cyan")
        table.add_column("Value", style="green")

        # Uptime
        uptime = datetime.now() - self.start_time
        uptime_str = str(uptime).split('.')[0]  # Remove microseconds
        table.add_row("Uptime", uptime_str)

        # Total messages
        total = stats.get("total", 0)
        new_messages = total - self.last_count
        if new_messages > 0:
            table.add_row("Total Messages", f"{total} (+{new_messages} new)")
        else:
            table.add_row("Total Messages", str(total))

        # Last message
        last_msg = stats.get("last_message")
        if last_msg:
            table.add_row("Last Message", last_msg)
        else:
            table.add_row("Last Message", "None yet")

        # Messages per minute
        minutes = max(1, uptime.total_seconds() / 60)
        rate = total / minutes
        table.add_row("Messages/min", f"{rate:.2f}")

        return table

    def generate_model_table(self, stats: Dict) -> Table:
        """Generate model breakdown table"""
        table = Table(title="By Model", show_header=True)
        table.add_column("Model", style="cyan")
        table.add_column("Count", style="green", justify="right")
        table.add_column("Priority", style="magenta")

        by_model = stats.get("by_model", {})

        # Priority models
        priority_map = {
            "deepseek-chat-v3.1": "[1] Highest P/L",
            "qwen3-max": "[2] Second P/L",
            "claude-sonnet-4-5": "[3] Negative P/L"
        }

        # Add priority models first
        for model_name, priority in priority_map.items():
            count = by_model.get(model_name, 0)
            table.add_row(model_name, str(count), priority)

        # Add other models
        for model_name, count in by_model.items():
            if model_name not in priority_map:
                table.add_row(model_name, str(count), "")

        return table

    def start_collector_instructions(self):
        """Show instructions for starting collector"""
        console.print("\n[bold yellow]Collector Not Running[/bold yellow]\n")
        console.print("To start the collector, open a new terminal and run:\n")

        if sys.platform == "win32":
            console.print("[cyan]cd collector[/cyan]")
        else:
            console.print("[cyan]cd collector[/cyan]")

        console.print("[cyan]node server.js[/cyan]")

        console.print("\n[yellow]Then:[/yellow]")
        console.print("1. Open Chrome browser")
        console.print("2. Navigate to https://nof1.ai/")
        console.print("3. Extension will automatically capture messages")

        console.print("\n[dim]This monitor will detect when collector starts...[/dim]")

    def run(self):
        """Main monitoring loop"""
        console.print("\n[bold cyan]Data Capture Monitor[/bold cyan]\n")

        # Check if collector is running
        if not self.check_collector_running():
            self.start_collector_instructions()
            console.print("\n[yellow]Waiting for collector to start...[/yellow]")

            # Wait for collector to start
            while self.running and not self.check_collector_running():
                time.sleep(2)

            if not self.running:
                return

            console.print("[green]Collector detected![/green]\n")

        else:
            console.print("[green]Collector is running[/green]\n")

        # Main monitoring loop
        console.print("[dim]Press Ctrl+C to stop monitoring[/dim]\n")

        with Live(console=console, refresh_per_second=0.5) as live:
            while self.running:
                # Get current stats
                stats = self.get_database_stats()

                # Create layout
                layout = Layout()
                layout.split_column(
                    Layout(self.generate_status_table(stats), name="status"),
                    Layout(self.generate_model_table(stats), name="models")
                )

                live.update(layout)

                # Update last count for delta calculation
                self.last_count = stats.get("total", 0)

                # Sleep
                time.sleep(CHECK_INTERVAL)

        console.print("\n[green]Monitor stopped[/green]")

        # Show final stats
        final_stats = self.get_database_stats()
        console.print(f"\nFinal Count: {final_stats['total']} messages captured")


def main():
    """Main entry point"""
    # Verify paths exist
    if not COLLECTOR_DIR.exists():
        console.print(f"[bold red]Error:[/bold red] Collector directory not found: {COLLECTOR_DIR}")
        console.print("Make sure you're running from the project root directory")
        sys.exit(1)

    if not SERVER_SCRIPT.exists():
        console.print(f"[bold red]Error:[/bold red] Server script not found: {SERVER_SCRIPT}")
        sys.exit(1)

    # Start monitor
    monitor = CaptureMonitor()

    try:
        monitor.run()
    except Exception as e:
        console.print(f"\n[bold red]Error:[/bold red] {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
