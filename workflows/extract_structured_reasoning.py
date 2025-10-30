#!/usr/bin/env python3
"""
Phase 2: LLM-Based Structured Reasoning Extraction

Uses Claude API to extract structured data from each trading message.
One-time processing cost, creates permanent structured database.

Extracts:
- Entry indicators and conditions
- Exit triggers and reasons
- Stop loss placement and rationale
- Risk management details
- Confidence level
- Market conditions assessed
- Causal reasoning chains

Output:
- New SQLite table with structured fields
- JSON export for analysis
- Enables sophisticated queries like:
  "Show all DeepSeek trades with MACD+RSI entry, profit target exit"
  "Compare stop loss rationale across priority models"
  "What invalidation patterns correlate with losses?"

Usage:
  # Process all messages
  python extract_structured_reasoning.py

  # Process only new messages (incremental)
  python extract_structured_reasoning.py --incremental

  # Process using Batch API (50% discount, up to 24hr processing)
  python extract_structured_reasoning.py --batch

  # Dry run (show cost estimate)
  python extract_structured_reasoning.py --dry-run
"""

import sqlite3
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime
import anthropic
import os

try:
    from rich.console import Console
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.table import Table
    from rich.panel import Panel
    from rich.prompt import Confirm
except ImportError:
    print("Error: 'rich' not installed. Run: uv add rich")
    sys.exit(1)

console = Console()
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "collector" / "nof1_data.db"

# Anthropic API key
API_KEY = os.environ.get("ANTHROPIC_API_KEY")


EXTRACTION_PROMPT = """You are analyzing a trading decision message from an AI trading model. Extract structured information about the reasoning.

Message to analyze:
<message>
{message_text}
</message>

Extract the following information in JSON format:

{{
  "entry_indicators": ["list of technical indicators mentioned for entry", "e.g. MACD bullish crossover", "RSI bounced from 35"],
  "entry_conditions": "What conditions must be met for entry? (concise summary)",
  "entry_rationale": "WHY enter based on these indicators? (causal reasoning)",

  "exit_trigger": "What triggered or would trigger the exit?",
  "exit_reason": "WHY exit? (profit target, risk reduction, signal reversal, etc.)",
  "exit_type": "profit_target|stop_loss|signal_reversal|invalidation|other",

  "stop_loss_placement": "Where is stop loss placed? (price level or percentage)",
  "stop_loss_rationale": "WHY placed there? (invalidation point, risk tolerance, etc.)",

  "risk_management": "How is position sizing / risk managed?",
  "risk_percentage": "Percentage of capital risked (if mentioned, else null)",

  "market_conditions": "What market conditions are assessed? (trending, ranging, volatile, etc.)",
  "supporting_factors": ["Other factors supporting the decision", "e.g. volume confirmation", "trend alignment"],

  "confidence_level": "high|medium|low|unspecified",
  "confidence_reasoning": "WHY this confidence level?",

  "causal_chain": ["Step 1 of reasoning", "Step 2 because of step 1", "etc"],

  "decision_summary": "One sentence summary of the core decision and reasoning"
}}

Rules:
1. Extract ONLY information explicitly stated or strongly implied
2. Use null for fields not mentioned
3. Be concise but specific
4. Focus on WHY, not just WHAT
5. Capture causal reasoning ("because X", "due to Y")
6. If entry/exit not discussed, use null for those fields

Return ONLY valid JSON, no other text."""


def create_structured_table(db_path: Path):
    """Create table for structured reasoning data"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS structured_reasoning (
            id INTEGER PRIMARY KEY,
            message_id INTEGER UNIQUE NOT NULL,
            model_name TEXT NOT NULL,
            extracted_at TIMESTAMP NOT NULL,

            -- Entry analysis
            entry_indicators TEXT,  -- JSON array
            entry_conditions TEXT,
            entry_rationale TEXT,

            -- Exit analysis
            exit_trigger TEXT,
            exit_reason TEXT,
            exit_type TEXT,

            -- Stop loss
            stop_loss_placement TEXT,
            stop_loss_rationale TEXT,

            -- Risk management
            risk_management TEXT,
            risk_percentage REAL,

            -- Context
            market_conditions TEXT,
            supporting_factors TEXT,  -- JSON array

            -- Confidence
            confidence_level TEXT,
            confidence_reasoning TEXT,

            -- Reasoning
            causal_chain TEXT,  -- JSON array
            decision_summary TEXT,

            -- Full extraction
            full_json TEXT,

            FOREIGN KEY (message_id) REFERENCES model_chat(id)
        )
    """)

    # Create indexes for common queries
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sr_model ON structured_reasoning(model_name)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sr_exit_type ON structured_reasoning(exit_type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_sr_confidence ON structured_reasoning(confidence_level)")

    conn.commit()
    conn.close()


def get_messages_to_process(db_path: Path, incremental: bool = False) -> List[Dict]:
    """Get messages that need processing"""
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if incremental:
        # Only process messages not yet extracted
        cursor.execute("""
            SELECT m.id, m.model_name, m.reasoning, m.raw_content, m.timestamp
            FROM model_chat m
            LEFT JOIN structured_reasoning sr ON m.id = sr.message_id
            WHERE sr.message_id IS NULL
            ORDER BY m.timestamp DESC
        """)
    else:
        # Process all messages
        cursor.execute("""
            SELECT id, model_name, reasoning, raw_content, timestamp
            FROM model_chat
            ORDER BY timestamp DESC
        """)

    messages = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return messages


def estimate_cost(num_messages: int, avg_message_tokens: int = 4000) -> Dict:
    """Estimate API cost for processing"""
    # Claude Sonnet 3.5 pricing (as of 2024)
    INPUT_COST_PER_MTK = 3.00  # $3 per million tokens
    OUTPUT_COST_PER_MTK = 15.00  # $15 per million tokens

    # Estimates
    prompt_tokens = 500  # Extraction prompt
    message_tokens = avg_message_tokens
    output_tokens = 300  # Structured JSON output

    total_input = (prompt_tokens + message_tokens) * num_messages
    total_output = output_tokens * num_messages

    input_cost = (total_input / 1_000_000) * INPUT_COST_PER_MTK
    output_cost = (total_output / 1_000_000) * OUTPUT_COST_PER_MTK
    total_cost = input_cost + output_cost

    return {
        "num_messages": num_messages,
        "total_input_tokens": total_input,
        "total_output_tokens": total_output,
        "input_cost": input_cost,
        "output_cost": output_cost,
        "total_cost": total_cost,
        "batch_discount_cost": total_cost * 0.5  # 50% discount with Batch API
    }


def extract_reasoning(client: anthropic.Anthropic, message_text: str, model: str = "claude-3-5-sonnet-20241022") -> Dict:
    """Extract structured reasoning using Claude API"""
    try:
        response = client.messages.create(
            model=model,
            max_tokens=2000,
            temperature=0,
            messages=[{
                "role": "user",
                "content": EXTRACTION_PROMPT.format(message_text=message_text[:50000])
            }]
        )

        # Extract JSON from response
        content = response.content[0].text

        # Try to parse JSON (handle markdown code blocks)
        if "```json" in content:
            json_str = content.split("```json")[1].split("```")[0].strip()
        elif "```" in content:
            json_str = content.split("```")[1].split("```")[0].strip()
        else:
            json_str = content.strip()

        extracted = json.loads(json_str)
        return extracted

    except json.JSONDecodeError as e:
        console.print(f"[red]JSON decode error: {e}[/red]")
        console.print(f"[dim]Response: {content[:500]}[/dim]")
        return None
    except Exception as e:
        console.print(f"[red]Extraction error: {e}[/red]")
        return None


def save_structured_data(db_path: Path, message_id: int, model_name: str, extracted: Dict):
    """Save extracted data to database"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR REPLACE INTO structured_reasoning (
            message_id, model_name, extracted_at,
            entry_indicators, entry_conditions, entry_rationale,
            exit_trigger, exit_reason, exit_type,
            stop_loss_placement, stop_loss_rationale,
            risk_management, risk_percentage,
            market_conditions, supporting_factors,
            confidence_level, confidence_reasoning,
            causal_chain, decision_summary,
            full_json
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        message_id,
        model_name,
        datetime.now().isoformat(),
        json.dumps(extracted.get('entry_indicators')),
        extracted.get('entry_conditions'),
        extracted.get('entry_rationale'),
        extracted.get('exit_trigger'),
        extracted.get('exit_reason'),
        extracted.get('exit_type'),
        extracted.get('stop_loss_placement'),
        extracted.get('stop_loss_rationale'),
        extracted.get('risk_management'),
        extracted.get('risk_percentage'),
        extracted.get('market_conditions'),
        json.dumps(extracted.get('supporting_factors')),
        extracted.get('confidence_level'),
        extracted.get('confidence_reasoning'),
        json.dumps(extracted.get('causal_chain')),
        extracted.get('decision_summary'),
        json.dumps(extracted)
    ))

    conn.commit()
    conn.close()


def process_messages(messages: List[Dict], use_batch: bool = False, dry_run: bool = False):
    """Process messages and extract structured reasoning"""

    if not API_KEY:
        console.print("[red]Error: ANTHROPIC_API_KEY environment variable not set[/red]")
        console.print("\nSet it with:")
        console.print("[cyan]export ANTHROPIC_API_KEY=your-api-key[/cyan]  # Linux/Mac")
        console.print("[cyan]$env:ANTHROPIC_API_KEY='your-api-key'[/cyan]  # Windows PowerShell")
        sys.exit(1)

    # Estimate cost
    cost_est = estimate_cost(len(messages))

    console.print("\n[bold cyan]Extraction Plan[/bold cyan]\n")
    table = Table()
    table.add_column("Metric", style="cyan")
    table.add_column("Value", style="green")

    table.add_row("Messages to process", str(cost_est['num_messages']))
    table.add_row("Estimated input tokens", f"{cost_est['total_input_tokens']:,}")
    table.add_row("Estimated output tokens", f"{cost_est['total_output_tokens']:,}")
    table.add_row("Standard API cost", f"${cost_est['total_cost']:.2f}")
    if use_batch:
        table.add_row("Batch API cost (50% off)", f"${cost_est['batch_discount_cost']:.2f}")

    console.print(table)

    if dry_run:
        console.print("\n[yellow]Dry run complete. No processing performed.[/yellow]")
        return

    # Confirm
    if not Confirm.ask(f"\n[yellow]Proceed with extraction?[/yellow]"):
        console.print("[yellow]Cancelled[/yellow]")
        return

    # Initialize client
    client = anthropic.Anthropic(api_key=API_KEY)

    if use_batch:
        console.print("\n[yellow]Batch API not yet implemented - using standard API[/yellow]")
        console.print("[dim]Batch API requires setting up request files and polling[/dim]")
        use_batch = False

    # Process messages
    console.print(f"\n[bold cyan]Processing {len(messages)} messages...[/bold cyan]\n")

    success_count = 0
    error_count = 0

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        BarColumn(),
        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
        console=console
    ) as progress:

        task = progress.add_task("Extracting...", total=len(messages))

        for msg in messages:
            # Combine reasoning and raw content
            message_text = f"{msg['reasoning'] or ''}\n\n{msg['raw_content'] or ''}"

            # Extract
            extracted = extract_reasoning(client, message_text)

            if extracted:
                # Save to database
                save_structured_data(DB_PATH, msg['id'], msg['model_name'], extracted)
                success_count += 1
            else:
                error_count += 1

            progress.advance(task)

    # Summary
    console.print(f"\n[bold green]Extraction Complete![/bold green]\n")
    console.print(f"  Success: {success_count} messages")
    console.print(f"  Errors: {error_count} messages")
    console.print(f"\n[dim]Structured data saved to: {DB_PATH}[/dim]")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Extract structured reasoning using Claude API"
    )
    parser.add_argument(
        "--incremental",
        "-i",
        action="store_true",
        help="Only process new messages not yet extracted"
    )
    parser.add_argument(
        "--batch",
        "-b",
        action="store_true",
        help="Use Batch API (50%% discount, up to 24hr processing)"
    )
    parser.add_argument(
        "--dry-run",
        "-d",
        action="store_true",
        help="Show cost estimate without processing"
    )

    args = parser.parse_args()

    if not DB_PATH.exists():
        console.print(f"[red]Error: Database not found at {DB_PATH}[/red]")
        sys.exit(1)

    # Create structured table if needed
    console.print("[dim]Initializing structured reasoning table...[/dim]")
    create_structured_table(DB_PATH)

    # Get messages to process
    messages = get_messages_to_process(DB_PATH, incremental=args.incremental)

    if not messages:
        console.print("[yellow]No messages to process[/yellow]")
        return

    # Process
    try:
        process_messages(messages, use_batch=args.batch, dry_run=args.dry_run)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
