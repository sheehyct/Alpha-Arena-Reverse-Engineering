#!/usr/bin/env python3
"""
Verification Script - Check if full message content is being captured

Checks:
1. Extension database has messages
2. raw_content field contains full data
3. USER_PROMPT section present
4. CHAIN_OF_THOUGHT section present
5. TRADING_DECISIONS section present
"""

import sqlite3
import sys
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
except ImportError:
    print("Error: 'rich' not installed. Run: uv add rich")
    sys.exit(1)

console = Console()

DB_PATH = Path("GPT_Implementation_Proposal/collector/nof1_data.db")


def verify_database():
    """Verify database exists and has data"""
    if not DB_PATH.exists():
        console.print("[red]Database not found[/red]")
        console.print(f"\nExpected location: {DB_PATH}")
        console.print("\nStart the collector first:")
        console.print("[cyan]cd GPT_Implementation_Proposal/collector[/cyan]")
        console.print("[cyan]node server.js[/cyan]")
        return False

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM model_chat")
    count = cursor.fetchone()[0]

    if count == 0:
        console.print("[yellow]Database found but empty[/yellow]")
        console.print("\nWaiting for messages to be captured...")
        console.print("1. Make sure collector is running (node server.js)")
        console.print("2. Open Chrome and navigate to https://nof1.ai/")
        console.print("3. Wait 2-3 minutes for messages to appear")
        conn.close()
        return False

    console.print(f"[green]Database found with {count} messages[/green]\n")
    conn.close()
    return True


def analyze_content_completeness():
    """Analyze if messages contain complete content"""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id, model_name, timestamp,
            LENGTH(raw_content) as content_length,
            raw_content
        FROM model_chat
        ORDER BY scraped_at DESC
        LIMIT 5
    """)

    messages = cursor.fetchall()
    conn.close()

    if not messages:
        console.print("[yellow]No messages found[/yellow]")
        return

    console.print("[bold cyan]Content Completeness Analysis[/bold cyan]\n")

    for msg in messages:
        content = msg['raw_content'] or ""

        # Check for key sections
        has_user_prompt = "USER_PROMPT" in content or "user_prompt" in content.lower()
        has_chain = "CHAIN_OF_THOUGHT" in content or "chain_of_thought" in content.lower()
        has_decisions = "TRADING_DECISIONS" in content or "trading_decisions" in content.lower()

        # Check content richness
        has_market_data = any(coin in content.upper() for coin in ["BTC", "ETH", "SOL"])
        has_indicators = any(ind in content.upper() for ind in ["MACD", "RSI", "EMA"])
        has_positions = "position" in content.lower() or "leverage" in content.lower()

        # Display analysis
        console.print(f"[bold]Message ID {msg['id']}:[/bold] {msg['model_name']}")
        console.print(f"Timestamp: {msg['timestamp']}")
        console.print(f"Content Length: {msg['content_length']:,} characters")

        # Section check
        table = Table(title="Content Sections", show_header=True)
        table.add_column("Section", style="cyan")
        table.add_column("Present", style="green")

        table.add_row(
            "USER_PROMPT",
            "[green]YES[/green]" if has_user_prompt else "[red]NO[/red]"
        )
        table.add_row(
            "CHAIN_OF_THOUGHT",
            "[green]YES[/green]" if has_chain else "[red]NO[/red]"
        )
        table.add_row(
            "TRADING_DECISIONS",
            "[green]YES[/green]" if has_decisions else "[red]NO[/red]"
        )
        table.add_row(
            "Market Data (BTC/ETH/SOL)",
            "[green]YES[/green]" if has_market_data else "[red]NO[/red]"
        )
        table.add_row(
            "Indicators (MACD/RSI/EMA)",
            "[green]YES[/green]" if has_indicators else "[red]NO[/red]"
        )
        table.add_row(
            "Position Details",
            "[green]YES[/green]" if has_positions else "[red]NO[/red]"
        )

        console.print(table)

        # Completeness assessment
        all_sections = all([has_user_prompt, has_chain, has_decisions])
        rich_content = all([has_market_data, has_indicators, has_positions])

        if all_sections and rich_content:
            console.print("[bold green]Status: COMPLETE CAPTURE[/bold green]")
        elif all_sections:
            console.print("[bold yellow]Status: Basic sections present, but content may be truncated[/bold yellow]")
        else:
            console.print("[bold red]Status: INCOMPLETE - Missing key sections[/bold red]")

        # Show preview
        console.print("\n[dim]Content preview (first 500 chars):[/dim]")
        console.print(Panel(content[:500], border_style="dim"))

        console.print("\n" + "=" * 70 + "\n")


def show_recommendations():
    """Show recommendations based on analysis"""
    console.print("\n[bold cyan]Recommendations:[/bold cyan]\n")

    console.print("[bold]If content is complete:[/bold]")
    console.print("  - Collector is working correctly")
    console.print("  - Continue capturing data")
    console.print("  - Use sync workflow to export\n")

    console.print("[bold]If content is incomplete:[/bold]")
    console.print("  1. Check Chrome extension is properly installed")
    console.print("  2. Verify extension is active on nof1.ai page")
    console.print("  3. Check Chrome DevTools console for errors")
    console.print("  4. Try reloading the nof1.ai page\n")

    console.print("[bold]Expected content length:[/bold]")
    console.print("  - USER_PROMPT: ~5,000-15,000 characters")
    console.print("  - CHAIN_OF_THOUGHT: ~1,000-5,000 characters")
    console.print("  - TRADING_DECISIONS: ~500-2,000 characters")
    console.print("  - Total: ~10,000-25,000 characters per message\n")


def main():
    """Main entry point"""
    console.print("\n[bold cyan]Content Capture Verification[/bold cyan]\n")

    if not verify_database():
        sys.exit(1)

    analyze_content_completeness()
    show_recommendations()


if __name__ == "__main__":
    main()
