#!/usr/bin/env python3
"""
Extract portfolio values and position information from captured data

Examines the database to identify:
- Portfolio values over time per model
- Position changes (entries/exits)
- Account performance metrics
- Position details (size, entry price, PnL)
"""

import sqlite3
import json
import re
from pathlib import Path
from collections import defaultdict
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
except ImportError:
    print("Error: rich not installed. Run: uv add rich")
    exit(1)

console = Console()
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "collector" / "nof1_data.db"


def extract_portfolio_value(text):
    """Extract portfolio/account value from text"""
    if not text:
        return None

    # Patterns for account value
    patterns = [
        r'account value[:\s]+\$?([0-9,]+\.?[0-9]*)',
        r'total value[:\s]+\$?([0-9,]+\.?[0-9]*)',
        r'portfolio value[:\s]+\$?([0-9,]+\.?[0-9]*)',
        r'current account value[:\s]+\$?([0-9,]+\.?[0-9]*)',
    ]

    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            value_str = match.group(1).replace(',', '')
            try:
                return float(value_str)
            except:
                pass

    return None


def extract_return_percentage(text):
    """Extract return percentage from text"""
    if not text:
        return None

    patterns = [
        r'total return[:\s]+([0-9.]+)%',
        r'return[:\s]+([0-9.]+)%',
        r'gain[:\s]+([0-9.]+)%',
    ]

    text_lower = text.lower()
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            try:
                return float(match.group(1))
            except:
                pass

    return None


def analyze_portfolio_data():
    """Analyze portfolio values and positions from database"""
    console.print("\n[bold cyan]Portfolio & Position Data Analysis[/bold cyan]\n")

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Get all records with reasoning (which contains portfolio info)
    cursor.execute("""
        SELECT
            model_name,
            timestamp,
            reasoning,
            positions,
            raw_content
        FROM model_chat
        ORDER BY model_name, timestamp
    """)

    records = cursor.fetchall()
    conn.close()

    console.print(f"[dim]Analyzing {len(records)} total records[/dim]\n")

    # Track portfolio values by model over time
    portfolio_values = defaultdict(list)
    position_counts = defaultdict(int)
    models_with_data = set()

    for record in records:
        model = record['model_name']
        timestamp = record['timestamp']
        reasoning = record['reasoning'] or ''
        raw_content = record['raw_content'] or ''
        positions = record['positions'] or '[]'

        # Try to extract portfolio value
        portfolio_value = extract_portfolio_value(reasoning)
        if not portfolio_value:
            portfolio_value = extract_portfolio_value(raw_content)

        if portfolio_value:
            portfolio_values[model].append({
                'timestamp': timestamp,
                'value': portfolio_value
            })
            models_with_data.add(model)

        # Count position records
        try:
            pos_list = json.loads(positions)
            if pos_list and len(pos_list) > 0:
                position_counts[model] += 1
        except:
            pass

    # Display results
    console.print("[bold]Portfolio Value Data Availability[/bold]\n")

    table = Table()
    table.add_column("Model", style="cyan")
    table.add_column("Records with Portfolio Value", justify="right", style="green")
    table.add_column("Records with Position Data", justify="right", style="yellow")
    table.add_column("Date Range", style="dim")

    for model in sorted(set(list(portfolio_values.keys()) + list(position_counts.keys()))):
        pv_count = len(portfolio_values.get(model, []))
        pos_count = position_counts.get(model, 0)

        if portfolio_values.get(model):
            timestamps = [pv['timestamp'] for pv in portfolio_values[model]]
            date_range = f"{timestamps[0][:10]} to {timestamps[-1][:10]}"
        else:
            date_range = "N/A"

        table.add_row(
            model,
            str(pv_count) if pv_count > 0 else "-",
            str(pos_count) if pos_count > 0 else "-",
            date_range
        )

    console.print(table)

    # Show sample portfolio values for models with data
    if models_with_data:
        console.print("\n[bold]Sample Portfolio Values[/bold]\n")

        for model in sorted(models_with_data):
            values = portfolio_values[model]
            if len(values) >= 3:
                console.print(f"[cyan]{model}:[/cyan]")
                console.print(f"  First: ${values[0]['value']:,.2f} ({values[0]['timestamp'][:19]})")
                console.print(f"  Mid:   ${values[len(values)//2]['value']:,.2f} ({values[len(values)//2]['timestamp'][:19]})")
                console.print(f"  Last:  ${values[-1]['value']:,.2f} ({values[-1]['timestamp'][:19]})")

                # Calculate return if we have first and last
                first_val = values[0]['value']
                last_val = values[-1]['value']
                total_return = ((last_val - first_val) / first_val) * 100
                console.print(f"  Return: {total_return:+.2f}%\n")

    # Summary
    console.print("\n[bold yellow]Summary:[/bold yellow]")
    console.print(f"  Models with portfolio value data: {len(models_with_data)}")
    console.print(f"  Models with position data: {len([m for m in position_counts if position_counts[m] > 0])}")

    total_portfolio_records = sum(len(v) for v in portfolio_values.values())
    total_position_records = sum(position_counts.values())

    console.print(f"  Total portfolio value records: {total_portfolio_records}")
    console.print(f"  Total position records: {total_position_records}")

    if total_portfolio_records == 0:
        console.print("\n[yellow]Note: No portfolio values found in reasoning or raw_content fields.[/yellow]")
        console.print("[dim]This data may be in a different format or not captured during scraping.[/dim]")

    return portfolio_values, position_counts


def check_regime_timestamps():
    """Check if we have data covering the regime periods"""
    console.print("\n[bold cyan]Regime Period Coverage[/bold cyan]\n")

    regime_dates = {
        'Bull Phase Start': '2025-10-17',
        'Bull Phase Peak': '2025-10-27',
        'Correction Bottom': '2025-10-30',
        'Current Date': '2025-11-01'
    }

    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    table = Table()
    table.add_column("Regime Date", style="cyan")
    table.add_column("Date", style="yellow")
    table.add_column("Records Available", justify="right", style="green")

    for label, date in regime_dates.items():
        cursor.execute("""
            SELECT COUNT(*)
            FROM model_chat
            WHERE timestamp LIKE ?
        """, (f"{date}%",))

        count = cursor.fetchone()[0]
        table.add_row(label, date, str(count))

    console.print(table)
    conn.close()

    console.print("\n[dim]Note: Final competition results available November 3rd[/dim]")


if __name__ == "__main__":
    if not DB_PATH.exists():
        console.print(f"[red]Error: Database not found at {DB_PATH}[/red]")
        exit(1)

    try:
        portfolio_values, position_counts = analyze_portfolio_data()
        check_regime_timestamps()

        console.print("\n[bold green]Analysis Complete[/bold green]\n")

    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
