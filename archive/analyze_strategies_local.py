#!/usr/bin/env python3
"""
Local Strategy Analysis - Analyze trading strategies from local SQLite database

This is the LOCAL version that queries SQLite directly.
For OpenMemory semantic search, use analyze_strategies.py instead.

Key Differences:
- Works with local database (no MCP/OpenMemory needed)
- Keyword-based search (not semantic)
- Instant results (no API calls)
- Expanded keyword lists for better coverage
"""

import sys
import sqlite3
from pathlib import Path
from typing import List, Dict, Tuple
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.prompt import Prompt, Confirm
    from rich.markdown import Markdown
except ImportError:
    print("Error: 'rich' not installed. Run: uv add rich")
    sys.exit(1)

console = Console()
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "collector" / "nof1_data.db"


class LocalStrategyAnalyzer:
    """Analyze trading strategies from local SQLite database"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")
        self.query_library = self._build_query_library()

    def _build_query_library(self) -> Dict[str, Dict]:
        """Build library of pre-defined queries with keyword expansions"""
        return {
            "1": {
                "name": "Risk Management Strategies",
                "category": "Risk",
                "keywords": ["risk", "position siz", "stop loss", "drawdown", "capital", "exposure", "leverage"],
                "model_filter": None,
                "limit": 15,
                "description": "Find how models manage risk in volatile conditions"
            },
            "2": {
                "name": "Entry Signals - Trending Markets",
                "category": "Entry",
                "keywords": ["entry", "buy", "long", "breakout", "trend", "momentum", "signal"],
                "model_filter": None,
                "limit": 15,
                "description": "Identify entry patterns in trending conditions"
            },
            "3": {
                "name": "Exit Strategies - Profit Taking",
                "category": "Exit",
                "keywords": ["exit", "sell", "take profit", "profit target", "close position", "lock in"],
                "model_filter": None,
                "limit": 15,
                "description": "How models lock in profits"
            },
            "4": {
                "name": "Stop Loss Placement",
                "category": "Risk",
                "keywords": ["stop loss", "stop-loss", "invalidation", "cut loss", "exit", "protective stop"],
                "model_filter": None,
                "limit": 15,
                "description": "Stop loss strategies and when to exit losers"
            },
            "5": {
                "name": "DeepSeek Winning Patterns",
                "category": "Model-Specific",
                "keywords": ["confidence", "high confidence", "strong signal", "profitable", "winner"],
                "model_filter": "deepseek-chat-v3.1",
                "limit": 20,
                "description": "Best trades from DeepSeek V3.1 (priority model #1)"
            },
            "6": {
                "name": "QWEN3 Strategies",
                "category": "Model-Specific",
                "keywords": ["confidence", "high confidence", "strong", "strategy", "decision"],
                "model_filter": "qwen3-max",
                "limit": 20,
                "description": "Strategies from QWEN3 MAX (priority model #2)"
            },
            "7": {
                "name": "Claude Analysis Patterns",
                "category": "Model-Specific",
                "keywords": ["analysis", "reasoning", "decision", "trade", "strategy"],
                "model_filter": "claude-sonnet-4-5",
                "limit": 15,
                "description": "Claude Sonnet 4.5 trading approaches (priority model #3)"
            },
            "8": {
                "name": "Technical Indicators",
                "category": "Technical",
                "keywords": ["MACD", "RSI", "moving average", "MA", "indicator", "oscillator", "volume"],
                "model_filter": None,
                "limit": 15,
                "description": "How models use technical indicators"
            },
            "9": {
                "name": "Market Conditions",
                "category": "Market",
                "keywords": ["volatile", "volatility", "trending", "sideways", "ranging", "market condition"],
                "model_filter": None,
                "limit": 15,
                "description": "How models adapt to different market conditions"
            },
            "10": {
                "name": "All Priority Models Comparison",
                "category": "Comparison",
                "keywords": ["confidence", "decision", "trade"],
                "model_filter": ["deepseek-chat-v3.1", "qwen3-max", "claude-sonnet-4-5"],
                "limit": 30,
                "description": "Compare all three priority models"
            }
        }

    def execute_query(self, query_data: Dict) -> List[sqlite3.Row]:
        """Execute query against local database"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Build WHERE clause from keywords
        keyword_conditions = []
        params = []

        for keyword in query_data["keywords"]:
            keyword_conditions.append("(reasoning LIKE ? OR raw_content LIKE ?)")
            params.extend([f"%{keyword}%", f"%{keyword}%"])

        where_clause = " OR ".join(keyword_conditions)

        # Add model filter if specified
        if query_data["model_filter"]:
            if isinstance(query_data["model_filter"], list):
                # Multiple models
                model_placeholders = ",".join(["?" for _ in query_data["model_filter"]])
                model_clause = f"model_name IN ({model_placeholders})"
                params.extend(query_data["model_filter"])
            else:
                # Single model
                model_clause = "model_name = ?"
                params.append(query_data["model_filter"])

            where_clause = f"({where_clause}) AND {model_clause}"

        # Execute query
        sql = f"""
            SELECT id, model_name, timestamp,
                   SUBSTR(reasoning, 1, 500) as preview,
                   LENGTH(reasoning) as reasoning_length
            FROM model_chat
            WHERE {where_clause}
            ORDER BY timestamp DESC
            LIMIT ?
        """
        params.append(query_data["limit"])

        cursor.execute(sql, params)
        results = cursor.fetchall()
        conn.close()

        return results

    def get_full_message(self, message_id: int) -> sqlite3.Row:
        """Get full message content by ID"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT id, model_name, timestamp, reasoning, raw_content, action
            FROM model_chat
            WHERE id = ?
        """, (message_id,))

        result = cursor.fetchone()
        conn.close()
        return result

    def display_query_library(self):
        """Display available query templates"""
        console.print("\n[bold cyan]Local Strategy Analysis - Query Library[/bold cyan]\n")

        # Group by category
        by_category = {}
        for query_id, query_data in self.query_library.items():
            category = query_data["category"]
            if category not in by_category:
                by_category[category] = []
            by_category[category].append((query_id, query_data))

        # Display each category
        for category in sorted(by_category.keys()):
            console.print(f"[bold]{category}:[/bold]")

            table = Table(show_header=False, box=None)
            table.add_column("ID", style="cyan", width=4)
            table.add_column("Name", style="green")
            table.add_column("Description", style="dim")

            for query_id, query_data in sorted(by_category[category]):
                table.add_row(
                    query_id,
                    query_data["name"],
                    query_data["description"]
                )

            console.print(table)
            console.print()

    def display_results(self, query_data: Dict, results: List[sqlite3.Row]):
        """Display query results"""
        console.print(f"\n[bold cyan]Results for: {query_data['name']}[/bold cyan]\n")

        if not results:
            console.print("[yellow]No results found[/yellow]")
            return

        console.print(f"[green]Found {len(results)} messages:[/green]\n")

        table = Table()
        table.add_column("ID", style="cyan", width=8)
        table.add_column("Model", style="green", width=20)
        table.add_column("Timestamp", style="dim", width=20)
        table.add_column("Length", style="yellow", width=10)
        table.add_column("Preview", style="white")

        for row in results:
            table.add_row(
                str(row['id']),
                row['model_name'],
                row['timestamp'][:19],
                f"{row['reasoning_length']:,}",
                row['preview'][:80] + "..." if len(row['preview']) > 80 else row['preview']
            )

        console.print(table)

        # Show keywords used
        console.print(f"\n[dim]Keywords used: {', '.join(query_data['keywords'])}[/dim]")
        if query_data['model_filter']:
            if isinstance(query_data['model_filter'], list):
                console.print(f"[dim]Models: {', '.join(query_data['model_filter'])}[/dim]")
            else:
                console.print(f"[dim]Model: {query_data['model_filter']}[/dim]")

    def view_full_message(self, message_id: int):
        """Display full message content"""
        message = self.get_full_message(message_id)

        if not message:
            console.print(f"[red]Message {message_id} not found[/red]")
            return

        console.clear()

        # Header
        header = f"""
[bold cyan]Message ID: {message['id']}[/bold cyan]
[dim]Model:[/dim] {message['model_name']}
[dim]Timestamp:[/dim] {message['timestamp']}
[dim]Action:[/dim] {message['action'] or 'N/A'}
"""
        console.print(Panel(header, border_style="cyan"))

        # Reasoning content
        console.print("\n[bold]REASONING:[/bold]")
        console.print("-" * 80)
        console.print(message['reasoning'] or "(empty)")
        console.print("-" * 80)

    def custom_query_builder(self):
        """Interactive custom query builder"""
        console.print("\n[bold cyan]Custom Query Builder[/bold cyan]\n")

        # Get keywords
        keywords_input = Prompt.ask("Enter keywords (comma-separated)")
        keywords = [k.strip() for k in keywords_input.split(",")]

        # Get model filter
        model = Prompt.ask("Filter by model (leave empty for all)", default="")
        model_filter = model if model else None

        # Get limit
        limit = int(Prompt.ask("Number of results to return", default="15"))

        # Build query data
        query_data = {
            "name": "Custom Query",
            "category": "Custom",
            "keywords": keywords,
            "model_filter": model_filter,
            "limit": limit,
            "description": "Custom user query"
        }

        # Execute and display
        results = self.execute_query(query_data)
        self.display_results(query_data, results)

    def interactive_mode(self):
        """Run interactive query selection"""
        while True:
            console.clear()
            self.display_query_library()

            console.print("[bold]Options:[/bold]")
            console.print("  [cyan]1-10[/cyan]  - Run pre-defined query")
            console.print("  [cyan]c[/cyan]     - Custom query")
            console.print("  [cyan]v[/cyan]     - View full message by ID")
            console.print("  [cyan]help[/cyan]  - Show help")
            console.print("  [cyan]q[/cyan]     - Quit")

            choice = Prompt.ask("\nSelect option", default="q")

            if choice.lower() == "q":
                break

            elif choice.lower() == "c":
                self.custom_query_builder()
                Prompt.ask("\nPress Enter to continue")

            elif choice.lower() == "v":
                message_id = Prompt.ask("Enter message ID")
                try:
                    self.view_full_message(int(message_id))
                    Prompt.ask("\nPress Enter to continue")
                except ValueError:
                    console.print("[red]Invalid message ID[/red]")
                    Prompt.ask("Press Enter to continue")

            elif choice.lower() == "help":
                self.show_help()
                Prompt.ask("\nPress Enter to continue")

            elif choice in self.query_library:
                query_data = self.query_library[choice]
                results = self.execute_query(query_data)
                self.display_results(query_data, results)

                # Offer to view full message
                console.print("\n[dim]Enter message ID to view full content, or press Enter to continue[/dim]")
                view_choice = Prompt.ask("Message ID", default="")
                if view_choice:
                    try:
                        self.view_full_message(int(view_choice))
                        Prompt.ask("\nPress Enter to continue")
                    except ValueError:
                        pass

            else:
                console.print(f"[red]Invalid option: {choice}[/red]")
                Prompt.ask("Press Enter to continue")

    def show_help(self):
        """Show help information"""
        help_text = """
# Local Strategy Analysis Help

## How This Works

This tool searches your LOCAL SQLite database using keyword matching.
No OpenMemory or API calls required - instant results.

## How to Use

1. **Select a pre-defined query** (options 1-10)
   - Each query uses expanded keyword lists for better coverage
   - Model-specific queries focus on priority models

2. **Build a custom query** (option 'c')
   - Enter comma-separated keywords
   - Optionally filter by model
   - Set result limit

3. **View full messages** (option 'v')
   - Enter any message ID to see complete reasoning
   - Useful after reviewing query results

## Query Tips

- Keywords are case-insensitive
- Partial matches work: "stop" finds "stop loss", "stopped out"
- Multiple keywords use OR logic (finds any match)
- Model filters narrow results to specific models

## Priority Models

Focus on these three models:
1. **deepseek-chat-v3.1** - Use query #5
2. **qwen3-max** - Use query #6
3. **claude-sonnet-4-5** - Use query #7

Query #10 compares all three priority models.

## Example Workflow

1. Run query #5 (DeepSeek Winning Patterns)
2. Review results, note interesting message IDs
3. Use option 'v' to view full reasoning for those IDs
4. Extract specific rules or patterns
5. Run query #6 (QWEN3) to compare approaches

## Difference from OpenMemory Version

- **Local**: Keyword matching, instant, offline
- **OpenMemory**: Semantic search, finds related concepts
- Use local for speed, OpenMemory for discovery

## Export Results

To export a specific message:
```
uv run python archive/export_message.py <message_id>
```
"""
        console.print(Markdown(help_text))


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze trading strategies from local SQLite database"
    )
    parser.add_argument(
        "--query",
        "-q",
        help="Run specific query by ID (1-10)"
    )
    parser.add_argument(
        "--list",
        "-l",
        action="store_true",
        help="List all available queries and exit"
    )
    parser.add_argument(
        "--view",
        "-v",
        type=int,
        help="View full message by ID"
    )

    args = parser.parse_args()

    if not DB_PATH.exists():
        console.print(f"[red]Error: Database not found at {DB_PATH}[/red]")
        console.print("\nStart the collector first:")
        console.print("[cyan]cd collector[/cyan]")
        console.print("[cyan]node server.js[/cyan]")
        sys.exit(1)

    analyzer = LocalStrategyAnalyzer(DB_PATH)

    if args.list:
        analyzer.display_query_library()
        sys.exit(0)

    if args.view:
        analyzer.view_full_message(args.view)
        sys.exit(0)

    if args.query:
        query_data = analyzer.query_library.get(args.query)
        if query_data:
            results = analyzer.execute_query(query_data)
            analyzer.display_results(query_data, results)
        else:
            console.print(f"[red]Invalid query ID: {args.query}[/red]")
            sys.exit(1)
    else:
        # Interactive mode
        try:
            analyzer.interactive_mode()
        except KeyboardInterrupt:
            console.print("\n[yellow]Interrupted[/yellow]")


if __name__ == "__main__":
    main()
