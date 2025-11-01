#!/usr/bin/env python3
"""
Local Data Analysis - Analyze captured trading data directly from SQLite
No OpenMemory needed - works with local database
"""
import sqlite3
import sys
from pathlib import Path
from datetime import datetime
from collections import Counter, defaultdict
import re

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Prompt, Confirm
except ImportError:
    print("Error: 'rich' not installed. Run: uv add rich")
    sys.exit(1)

console = Console()
DB_PATH = Path(__file__).parent.parent / "collector" / "nof1_data.db"


class LocalDataAnalyzer:
    """Analyze trading data directly from local SQLite database"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

    def get_overview(self):
        """Get overview statistics"""
        conn = sqlite3.connect(self.db_path)
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
        by_model = cursor.fetchall()

        # Date range
        cursor.execute("""
            SELECT MIN(timestamp), MAX(timestamp)
            FROM model_chat
        """)
        date_range = cursor.fetchone()

        conn.close()

        return {
            "total": total,
            "by_model": by_model,
            "date_range": date_range
        }

    def search_reasoning(self, keyword: str, model_name: str = None, limit: int = 10):
        """Search chain of thought for keyword"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if model_name:
            query = """
                SELECT id, model_name, timestamp,
                       SUBSTR(reasoning, 1, 300) as preview
                FROM model_chat
                WHERE model_name = ? AND
                      (reasoning LIKE ? OR raw_content LIKE ?)
                ORDER BY timestamp DESC
                LIMIT ?
            """
            cursor.execute(query, (model_name, f"%{keyword}%", f"%{keyword}%", limit))
        else:
            query = """
                SELECT id, model_name, timestamp,
                       SUBSTR(reasoning, 1, 300) as preview
                FROM model_chat
                WHERE reasoning LIKE ? OR raw_content LIKE ?
                ORDER BY timestamp DESC
                LIMIT ?
            """
            cursor.execute(query, (f"%{keyword}%", f"%{keyword}%", limit))

        results = cursor.fetchall()
        conn.close()
        return results

    def get_trading_decisions_stats(self):
        """Analyze trading decisions across all messages"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        cursor.execute("""
            SELECT model_name, action, COUNT(*) as count
            FROM model_chat
            WHERE action IS NOT NULL AND action != ''
            GROUP BY model_name, action
            ORDER BY model_name, count DESC
        """)

        results = cursor.fetchall()
        conn.close()

        # Organize by model
        by_model = defaultdict(dict)
        for model, action, count in results:
            by_model[model][action] = count

        return by_model

    def analyze_keywords(self, keywords: list):
        """Count occurrences of keywords in reasoning"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        results = {}
        for keyword in keywords:
            cursor.execute("""
                SELECT COUNT(*)
                FROM model_chat
                WHERE reasoning LIKE ? OR raw_content LIKE ?
            """, (f"%{keyword}%", f"%{keyword}%"))
            count = cursor.fetchone()[0]
            results[keyword] = count

        conn.close()
        return results

    def compare_models(self, keywords: list):
        """Compare how often different models use certain concepts"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Get all models
        cursor.execute("SELECT DISTINCT model_name FROM model_chat")
        models = [row[0] for row in cursor.fetchall()]

        results = {}
        for model in models:
            results[model] = {}
            for keyword in keywords:
                cursor.execute("""
                    SELECT COUNT(*)
                    FROM model_chat
                    WHERE model_name = ? AND
                          (reasoning LIKE ? OR raw_content LIKE ?)
                """, (model, f"%{keyword}%", f"%{keyword}%"))
                count = cursor.fetchone()[0]
                results[model][keyword] = count

        conn.close()
        return results

    def export_model_reasoning(self, model_name: str, output_file: Path, limit: int = None):
        """Export all reasoning from a specific model"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        if limit:
            cursor.execute("""
                SELECT id, model_name, timestamp, reasoning, raw_content
                FROM model_chat
                WHERE model_name = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (model_name, limit))
        else:
            cursor.execute("""
                SELECT id, model_name, timestamp, reasoning, raw_content
                FROM model_chat
                WHERE model_name = ?
                ORDER BY timestamp DESC
            """, (model_name,))

        messages = cursor.fetchall()
        conn.close()

        # Write to file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(f"# {model_name} - Trading Reasoning Export\n")
            f.write(f"# Total messages: {len(messages)}\n")
            f.write(f"# Exported: {datetime.now().isoformat()}\n\n")
            f.write("=" * 80 + "\n\n")

            for msg in messages:
                f.write(f"Message ID: {msg['id']}\n")
                f.write(f"Timestamp: {msg['timestamp']}\n")
                f.write(f"Model: {msg['model_name']}\n\n")
                f.write("REASONING:\n")
                f.write("-" * 80 + "\n")
                f.write(msg['reasoning'] or "(empty)")
                f.write("\n" + "=" * 80 + "\n\n")

        return len(messages)


def interactive_menu():
    """Interactive analysis menu"""
    analyzer = LocalDataAnalyzer(DB_PATH)

    while True:
        console.clear()
        console.print("[bold cyan]Local Data Analysis Menu[/bold cyan]\n")

        # Show overview
        stats = analyzer.get_overview()
        console.print(f"Database: {DB_PATH.name}")
        console.print(f"Total messages: [green]{stats['total']}[/green]")
        console.print(f"Date range: {stats['date_range'][0]} to {stats['date_range'][1]}\n")

        console.print("[bold]Options:[/bold]")
        console.print("  [cyan]1[/cyan] - Search for keyword in reasoning")
        console.print("  [cyan]2[/cyan] - Show trading decision statistics")
        console.print("  [cyan]3[/cyan] - Analyze keyword frequency")
        console.print("  [cyan]4[/cyan] - Compare models by keywords")
        console.print("  [cyan]5[/cyan] - Export model reasoning to file")
        console.print("  [cyan]6[/cyan] - Show overview by model")
        console.print("  [cyan]q[/cyan] - Quit\n")

        choice = Prompt.ask("Select option", default="q")

        if choice == "q":
            break
        elif choice == "1":
            search_keyword(analyzer)
        elif choice == "2":
            show_decision_stats(analyzer)
        elif choice == "3":
            analyze_keyword_frequency(analyzer)
        elif choice == "4":
            compare_models_by_keywords(analyzer)
        elif choice == "5":
            export_model_data(analyzer)
        elif choice == "6":
            show_model_overview(analyzer)

        if choice != "q":
            Prompt.ask("\nPress Enter to continue")


def search_keyword(analyzer):
    """Search for keyword"""
    console.print("\n[bold]Search Reasoning[/bold]\n")
    keyword = Prompt.ask("Enter keyword")
    model = Prompt.ask("Filter by model (leave empty for all)", default="")

    model = model if model else None
    results = analyzer.search_reasoning(keyword, model, limit=10)

    if not results:
        console.print(f"[yellow]No results found for '{keyword}'[/yellow]")
        return

    console.print(f"\n[green]Found {len(results)} results:[/green]\n")

    table = Table()
    table.add_column("ID", style="cyan")
    table.add_column("Model", style="green")
    table.add_column("Timestamp", style="dim")
    table.add_column("Preview", style="white")

    for row in results:
        table.add_row(
            str(row['id']),
            row['model_name'],
            row['timestamp'][:19],
            row['preview'][:100] + "..."
        )

    console.print(table)


def show_decision_stats(analyzer):
    """Show trading decision statistics"""
    console.print("\n[bold]Trading Decision Statistics[/bold]\n")

    stats = analyzer.get_trading_decisions_stats()

    for model, actions in stats.items():
        console.print(f"\n[cyan]{model}:[/cyan]")
        table = Table(show_header=True)
        table.add_column("Action", style="yellow")
        table.add_column("Count", justify="right", style="green")

        for action, count in sorted(actions.items(), key=lambda x: x[1], reverse=True):
            table.add_row(action, str(count))

        console.print(table)


def analyze_keyword_frequency(analyzer):
    """Analyze keyword frequency"""
    console.print("\n[bold]Keyword Frequency Analysis[/bold]\n")

    # Common trading concepts
    keywords = [
        "risk", "stop loss", "take profit", "MACD", "RSI",
        "trend", "momentum", "breakout", "support", "resistance",
        "leverage", "position size", "volatility"
    ]

    console.print("Analyzing common trading keywords...\n")
    results = analyzer.analyze_keywords(keywords)

    table = Table()
    table.add_column("Keyword", style="cyan")
    table.add_column("Occurrences", justify="right", style="green")

    for keyword, count in sorted(results.items(), key=lambda x: x[1], reverse=True):
        table.add_row(keyword, str(count))

    console.print(table)


def compare_models_by_keywords(analyzer):
    """Compare models"""
    console.print("\n[bold]Model Comparison[/bold]\n")

    keywords = ["risk", "MACD", "RSI", "breakout", "stop loss"]
    console.print(f"Comparing models by keywords: {', '.join(keywords)}\n")

    results = analyzer.compare_models(keywords)

    table = Table()
    table.add_column("Model", style="cyan")
    for keyword in keywords:
        table.add_column(keyword, justify="right")

    for model, counts in results.items():
        row = [model] + [str(counts.get(kw, 0)) for kw in keywords]
        table.add_row(*row)

    console.print(table)


def export_model_data(analyzer):
    """Export model data"""
    console.print("\n[bold]Export Model Data[/bold]\n")

    model = Prompt.ask("Enter model name")
    limit = Prompt.ask("Limit (leave empty for all)", default="")
    limit = int(limit) if limit else None

    output_file = Path(f"data/analysis/{model.replace(' ', '_')}_reasoning.txt")
    output_file.parent.mkdir(parents=True, exist_ok=True)

    console.print(f"\nExporting to {output_file}...")
    count = analyzer.export_model_reasoning(model, output_file, limit)

    console.print(f"[green]Exported {count} messages to {output_file}[/green]")


def show_model_overview(analyzer):
    """Show overview by model"""
    console.print("\n[bold]Model Overview[/bold]\n")

    stats = analyzer.get_overview()

    table = Table()
    table.add_column("Model", style="cyan")
    table.add_column("Messages", justify="right", style="green")
    table.add_column("Percentage", justify="right", style="yellow")

    total = stats['total']
    for model, count in stats['by_model']:
        pct = (count / total * 100) if total > 0 else 0
        table.add_row(model, str(count), f"{pct:.1f}%")

    console.print(table)


def main():
    """Main entry point"""
    if not DB_PATH.exists():
        console.print(f"[red]Error: Database not found at {DB_PATH}[/red]")
        console.print("\nStart the collector first:")
        console.print("[cyan]cd collector[/cyan]")
        console.print("[cyan]node server.js[/cyan]")
        sys.exit(1)

    try:
        interactive_menu()
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()
