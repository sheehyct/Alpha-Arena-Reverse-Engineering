#!/usr/bin/env python3
"""
Workflow 3: Analyze Trading Strategies

Responsibilities:
- Provide query templates for OpenMemory
- Generate analysis commands
- Display common query patterns
- Export analysis results

Professional Principles:
- Clear interface for common operations
- Composable queries
- Documentation of available patterns
- Export results for further analysis

Note: This script GENERATES commands for Claude Code to execute.
It cannot directly call MCP tools (only Claude Code can).
"""

import sys
from pathlib import Path
from typing import List, Dict
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


class StrategyAnalyzer:
    """Provides analysis queries and patterns"""

    def __init__(self):
        self.query_library = self._build_query_library()

    def _build_query_library(self) -> Dict[str, Dict]:
        """Build library of pre-defined queries"""
        return {
            "1": {
                "name": "Risk Management Strategies",
                "category": "Risk",
                "query": "risk management and position sizing strategies for volatile markets",
                "k": 15,
                "description": "Find how models manage risk in volatile conditions"
            },
            "2": {
                "name": "Entry Signals - Trending Markets",
                "category": "Entry",
                "query": "aggressive entry signals and timing for strong trending markets",
                "k": 15,
                "description": "Identify entry patterns in trending conditions"
            },
            "3": {
                "name": "Exit Strategies - Profit Taking",
                "category": "Exit",
                "query": "profit taking strategies and exit timing for winning trades",
                "k": 15,
                "description": "How models lock in profits"
            },
            "4": {
                "name": "Stop Loss Placement",
                "category": "Risk",
                "query": "stop loss placement and invalidation conditions",
                "k": 15,
                "description": "Stop loss strategies and when to exit losers"
            },
            "5": {
                "name": "DeepSeek Winning Patterns",
                "category": "Model-Specific",
                "query": "model_deepseek_chat_v3_1 high_confidence profitable trades",
                "k": 20,
                "description": "Best trades from highest P/L model"
            },
            "6": {
                "name": "QWEN3 Strategies",
                "category": "Model-Specific",
                "query": "model_qwen3_max high_confidence trading decisions",
                "k": 20,
                "description": "Strategies from second-best model"
            },
            "7": {
                "name": "Claude Negative Patterns",
                "category": "Model-Specific",
                "query": "model_claude_sonnet_4_5 unprofitable trades",
                "k": 15,
                "description": "What NOT to do (negative P/L model)"
            },
            "8": {
                "name": "Bitcoin Strategies",
                "category": "Asset-Specific",
                "query": "symbol_btc trading strategies and market analysis",
                "k": 15,
                "description": "BTC-specific trading approaches"
            },
            "9": {
                "name": "Portfolio Diversification",
                "category": "Portfolio",
                "query": "portfolio diversification and multi-asset strategies",
                "k": 15,
                "description": "How models manage multiple positions"
            },
            "10": {
                "name": "Market Regime Adaptation",
                "category": "Advanced",
                "query": "market regime detection and strategy adaptation",
                "k": 15,
                "description": "How models adapt to changing market conditions"
            }
        }

    def display_query_library(self):
        """Display available query templates"""
        console.print("\n[bold cyan]Query Library[/bold cyan]\n")

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

    def get_query(self, query_id: str) -> Dict:
        """Get query by ID"""
        return self.query_library.get(query_id)

    def generate_mcp_command(self, query_data: Dict) -> str:
        """Generate MCP command string"""
        return f"""mcp__openmemory__openmemory_query(
    query="{query_data['query']}",
    k={query_data['k']}
)"""

    def display_query_details(self, query_data: Dict):
        """Display detailed query information"""
        details = f"""
[bold]{query_data['name']}[/bold]

[dim]Category:[/dim] {query_data['category']}
[dim]Description:[/dim] {query_data['description']}

[bold cyan]Query String:[/bold cyan]
{query_data['query']}

[bold cyan]Results to Return:[/bold cyan]
{query_data['k']} matches

[bold cyan]MCP Command:[/bold cyan]
```python
{self.generate_mcp_command(query_data)}
```
"""
        console.print(Panel(details, border_style="cyan"))

    def generate_comparison_commands(self, models: List[str]) -> List[str]:
        """Generate commands to compare multiple models"""
        commands = []
        for model in models:
            model_tag = model.lower().replace(" ", "_").replace(".", "_")
            query = f"model_{model_tag} high_confidence"
            cmd = f"""mcp__openmemory__openmemory_query(
    query="{query}",
    k=10
)"""
            commands.append(cmd)
        return commands

    def custom_query_builder(self):
        """Interactive custom query builder"""
        console.print("\n[bold cyan]Custom Query Builder[/bold cyan]\n")

        # Get query text
        query_text = Prompt.ask("Enter your search query")

        # Get number of results
        k = Prompt.ask("Number of results to return", default="10")

        # Generate command
        cmd = f"""mcp__openmemory__openmemory_query(
    query="{query_text}",
    k={k}
)"""

        console.print("\n[bold cyan]Generated Command:[/bold cyan]\n")
        console.print(Panel(cmd, border_style="cyan"))

        console.print("\n[yellow]Copy this command and tell Claude Code to execute it[/yellow]")

    def interactive_mode(self):
        """Run interactive query selection"""
        while True:
            console.clear()
            self.display_query_library()

            console.print("[bold]Options:[/bold]")
            console.print("  [cyan]1-10[/cyan]  - Select a pre-defined query")
            console.print("  [cyan]c[/cyan]     - Custom query")
            console.print("  [cyan]comp[/cyan]  - Compare models")
            console.print("  [cyan]help[/cyan]  - Show help")
            console.print("  [cyan]q[/cyan]     - Quit")

            choice = Prompt.ask("\nSelect option", default="q")

            if choice.lower() == "q":
                break

            elif choice.lower() == "c":
                self.custom_query_builder()
                Prompt.ask("\nPress Enter to continue")

            elif choice.lower() == "comp":
                self.model_comparison_mode()
                Prompt.ask("\nPress Enter to continue")

            elif choice.lower() == "help":
                self.show_help()
                Prompt.ask("\nPress Enter to continue")

            elif choice in self.query_library:
                query_data = self.query_library[choice]
                console.print()
                self.display_query_details(query_data)
                console.print("\n[yellow]Copy the MCP command above and tell Claude Code to execute it[/yellow]")
                Prompt.ask("\nPress Enter to continue")

            else:
                console.print(f"[red]Invalid option: {choice}[/red]")
                Prompt.ask("Press Enter to continue")

    def model_comparison_mode(self):
        """Compare strategies across models"""
        console.print("\n[bold cyan]Model Comparison[/bold cyan]\n")

        models = [
            "deepseek-chat-v3.1",
            "qwen3-max",
            "claude-sonnet-4-5"
        ]

        console.print("[bold]Available Models:[/bold]")
        for i, model in enumerate(models, 1):
            console.print(f"  {i}. {model}")

        console.print("\n[bold cyan]Generated Commands:[/bold cyan]\n")

        commands = self.generate_comparison_commands(models)
        for i, (model, cmd) in enumerate(zip(models, commands), 1):
            console.print(f"[bold]{i}. {model}:[/bold]")
            console.print(Panel(cmd, border_style="cyan"))
            console.print()

        console.print("[yellow]Tell Claude Code to execute these commands in sequence[/yellow]")

    def show_help(self):
        """Show help information"""
        help_text = """
# Strategy Analysis Help

## How to Use This Tool

1. **Select a pre-defined query** (options 1-10)
   - Each query targets a specific trading pattern
   - Optimized for finding actionable insights

2. **Build a custom query** (option 'c')
   - Enter natural language query
   - Semantic search finds similar concepts

3. **Compare models** (option 'comp')
   - Generate queries for all models
   - Compare strategies side-by-side

## Query Tips

- Use natural language: "risk management in volatile markets"
- Tag-based queries: "model_deepseek_v3.1 high_confidence"
- Combine concepts: "entry signals and momentum indicators"

## After Getting Results

1. Review the chain-of-thought reasoning
2. Identify common patterns across results
3. Extract specific rules or conditions
4. Compare with lower-performing models
5. Backtest discovered patterns

## Priority Focus

Focus on DeepSeek Chat V3.1 (highest P/L):
- Query: model_deepseek_chat_v3_1 high_confidence
- Look for: Entry timing, risk management, exit conditions

## Need Help?

Read: INTEGRATION_GUIDE.md for full documentation
"""
        console.print(Markdown(help_text))


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze trading strategies from captured data"
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

    args = parser.parse_args()

    analyzer = StrategyAnalyzer()

    if args.list:
        analyzer.display_query_library()
        sys.exit(0)

    if args.query:
        query_data = analyzer.get_query(args.query)
        if query_data:
            analyzer.display_query_details(query_data)
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
