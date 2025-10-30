#!/usr/bin/env python3
"""
Phase 1: Pattern-Based Reasoning Analysis

Extracts trading patterns using regex and keyword analysis.
Fast, free, immediate insights without API calls.

Analyzes:
- Indicator combinations (MACD + RSI, etc.)
- Causal reasoning patterns ("because X", "due to Y")
- Entry/Exit triggers
- Stop loss placement rationale
- Risk management approaches
- Confidence levels by model

Works by:
1. Regex pattern matching for indicators and values
2. Context detection (entry/exit/stop loss sections)
3. Co-occurrence analysis (what appears together)
4. Frequency tables by model
"""

import sqlite3
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple
import sys

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
except ImportError:
    print("Error: 'rich' not installed. Run: uv add rich")
    sys.exit(1)

console = Console()
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "collector" / "nof1_data.db"


class ReasoningPatternAnalyzer:
    """Extract and analyze reasoning patterns from trading messages"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        # Define patterns
        self.indicator_patterns = {
            "MACD": r'\bMACD\b',
            "RSI": r'\bRSI\b',
            "Moving Average": r'\b(?:MA|moving average|SMA|EMA)\b',
            "Volume": r'\bvolume\b',
            "Bollinger Bands": r'\bBollinger\s+Bands?\b',
            "Stochastic": r'\bstochastic\b',
            "ATR": r'\bATR\b',
            "Support": r'\bsupport\b',
            "Resistance": r'\bresistance\b',
            "Trend": r'\btrend(?:ing|s)?\b',
            "Breakout": r'\bbreakout\b',
            "Momentum": r'\bmomentum\b'
        }

        self.causal_patterns = {
            "because": r'\bbecause\b',
            "due to": r'\bdue\s+to\b',
            "since": r'\bsince\b',
            "as": r'\bas\b',
            "given": r'\bgiven\b',
            "invalidated": r'\binvalidat(?:ed|ion)\b',
            "confirmed": r'\bconfirm(?:ed|ation)\b',
            "triggered": r'\btrigger(?:ed)?\b'
        }

        self.confidence_patterns = {
            "High Confidence": r'\b(?:high|strong|very)\s+(?:confidence|conviction|certainty)\b',
            "Medium Confidence": r'\b(?:medium|moderate|reasonable)\s+(?:confidence|conviction)\b',
            "Low Confidence": r'\b(?:low|weak|limited)\s+(?:confidence|conviction)\b',
            "Uncertain": r'\b(?:uncertain|unsure|unclear|ambiguous)\b'
        }

        self.action_patterns = {
            "Enter Long": r'\b(?:enter|buy|long|open long)\b',
            "Enter Short": r'\b(?:short|sell short|open short)\b',
            "Exit": r'\b(?:exit|close|sell|take profit)\b',
            "Hold": r'\b(?:hold|maintain|keep)\s+(?:position|exposure)\b',
            "Stop Loss": r'\b(?:stop loss|stop-loss|SL|protective stop)\b',
            "Scale In": r'\b(?:scale in|add to|increase)\s+(?:position|exposure)\b',
            "Scale Out": r'\b(?:scale out|reduce|partial)\s+(?:position|exit)\b'
        }

    def get_all_messages(self, model_filter: str = None) -> List[Tuple]:
        """Get all messages from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        if model_filter:
            cursor.execute("""
                SELECT id, model_name, reasoning, raw_content
                FROM model_chat
                WHERE model_name = ?
                ORDER BY timestamp DESC
            """, (model_filter,))
        else:
            cursor.execute("""
                SELECT id, model_name, reasoning, raw_content
                FROM model_chat
                ORDER BY timestamp DESC
            """)

        results = cursor.fetchall()
        conn.close()
        return results

    def extract_indicators(self, text: str) -> List[str]:
        """Extract technical indicators mentioned"""
        if not text:
            return []

        text = text.lower()
        found = []
        for name, pattern in self.indicator_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.append(name)
        return found

    def extract_causal_reasoning(self, text: str) -> List[str]:
        """Extract causal reasoning patterns"""
        if not text:
            return []

        text = text.lower()
        found = []
        for name, pattern in self.causal_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.append(name)
        return found

    def extract_confidence(self, text: str) -> str:
        """Extract confidence level"""
        if not text:
            return "Unknown"

        text = text.lower()
        for name, pattern in self.confidence_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                return name
        return "Unknown"

    def extract_actions(self, text: str) -> List[str]:
        """Extract trading actions mentioned"""
        if not text:
            return []

        text = text.lower()
        found = []
        for name, pattern in self.action_patterns.items():
            if re.search(pattern, text, re.IGNORECASE):
                found.append(name)
        return found

    def detect_context(self, text: str) -> Dict[str, str]:
        """Detect if text is discussing entry, exit, or stop loss"""
        if not text:
            return {}

        text = text.lower()
        contexts = {}

        # Entry context
        entry_section = re.search(r'(entry|signal|setup|trigger).*?(?=exit|stop|$)', text, re.DOTALL | re.IGNORECASE)
        if entry_section:
            contexts['entry'] = entry_section.group(0)[:500]

        # Exit context
        exit_section = re.search(r'(exit|take profit|close|target).*?(?=stop|entry|$)', text, re.DOTALL | re.IGNORECASE)
        if exit_section:
            contexts['exit'] = exit_section.group(0)[:500]

        # Stop loss context
        stop_section = re.search(r'(stop loss|stop-loss|invalidation).*?(?=entry|exit|$)', text, re.DOTALL | re.IGNORECASE)
        if stop_section:
            contexts['stop'] = stop_section.group(0)[:500]

        return contexts

    def analyze_indicator_cooccurrence(self, messages: List[Tuple]) -> Dict:
        """Analyze which indicators appear together"""
        cooccurrence = defaultdict(Counter)

        for msg_id, model, reasoning, raw in messages:
            text = f"{reasoning or ''} {raw or ''}"
            indicators = self.extract_indicators(text)

            # Count pairs
            for i, ind1 in enumerate(indicators):
                for ind2 in indicators[i+1:]:
                    pair = tuple(sorted([ind1, ind2]))
                    cooccurrence[model][pair] += 1

        return dict(cooccurrence)

    def analyze_by_model(self, messages: List[Tuple]) -> Dict:
        """Analyze patterns grouped by model"""
        by_model = defaultdict(lambda: {
            'total': 0,
            'indicators': Counter(),
            'causal_patterns': Counter(),
            'confidence': Counter(),
            'actions': Counter(),
            'indicator_pairs': Counter()
        })

        for msg_id, model, reasoning, raw in messages:
            text = f"{reasoning or ''} {raw or ''}"

            by_model[model]['total'] += 1

            # Indicators
            indicators = self.extract_indicators(text)
            by_model[model]['indicators'].update(indicators)

            # Indicator pairs
            for i, ind1 in enumerate(indicators):
                for ind2 in indicators[i+1:]:
                    pair = f"{ind1} + {ind2}"
                    by_model[model]['indicator_pairs'][pair] += 1

            # Causal reasoning
            causal = self.extract_causal_reasoning(text)
            by_model[model]['causal_patterns'].update(causal)

            # Confidence
            confidence = self.extract_confidence(text)
            by_model[model]['confidence'][confidence] += 1

            # Actions
            actions = self.extract_actions(text)
            by_model[model]['actions'].update(actions)

        return dict(by_model)

    def display_indicator_analysis(self, by_model: Dict):
        """Display indicator usage analysis"""
        console.print("\n[bold cyan]Technical Indicator Usage[/bold cyan]\n")

        for model, data in sorted(by_model.items()):
            if data['total'] == 0:
                continue

            table = Table(title=f"{model} ({data['total']} messages)")
            table.add_column("Indicator", style="cyan")
            table.add_column("Count", justify="right", style="green")
            table.add_column("Frequency", justify="right", style="yellow")

            for indicator, count in data['indicators'].most_common(10):
                freq = (count / data['total']) * 100
                table.add_row(indicator, str(count), f"{freq:.1f}%")

            console.print(table)
            console.print()

    def display_indicator_pairs(self, by_model: Dict):
        """Display common indicator combinations"""
        console.print("\n[bold cyan]Indicator Combinations[/bold cyan]\n")

        for model, data in sorted(by_model.items()):
            if data['total'] == 0:
                continue

            if not data['indicator_pairs']:
                continue

            table = Table(title=f"{model} - Top Combinations")
            table.add_column("Combination", style="cyan")
            table.add_column("Count", justify="right", style="green")

            for pair, count in data['indicator_pairs'].most_common(10):
                table.add_row(pair, str(count))

            console.print(table)
            console.print()

    def display_confidence_analysis(self, by_model: Dict):
        """Display confidence level distribution"""
        console.print("\n[bold cyan]Confidence Levels[/bold cyan]\n")

        table = Table()
        table.add_column("Model", style="cyan")
        table.add_column("High", justify="right", style="green")
        table.add_column("Medium", justify="right", style="yellow")
        table.add_column("Low", justify="right", style="red")
        table.add_column("Unknown", justify="right", style="dim")

        for model, data in sorted(by_model.items()):
            if data['total'] == 0:
                continue

            high = data['confidence']['High Confidence']
            medium = data['confidence']['Medium Confidence']
            low = data['confidence']['Low Confidence']
            unknown = data['confidence']['Unknown']

            table.add_row(
                model,
                f"{high} ({high/data['total']*100:.0f}%)" if high else "0",
                f"{medium} ({medium/data['total']*100:.0f}%)" if medium else "0",
                f"{low} ({low/data['total']*100:.0f}%)" if low else "0",
                f"{unknown} ({unknown/data['total']*100:.0f}%)" if unknown else "0"
            )

        console.print(table)

    def display_action_analysis(self, by_model: Dict):
        """Display trading action distribution"""
        console.print("\n[bold cyan]Trading Actions[/bold cyan]\n")

        for model, data in sorted(by_model.items()):
            if data['total'] == 0:
                continue

            table = Table(title=f"{model}")
            table.add_column("Action", style="cyan")
            table.add_column("Count", justify="right", style="green")
            table.add_column("Frequency", justify="right", style="yellow")

            for action, count in data['actions'].most_common():
                freq = (count / data['total']) * 100
                table.add_row(action, str(count), f"{freq:.1f}%")

            console.print(table)
            console.print()

    def run_analysis(self, model_filter: str = None):
        """Run complete pattern analysis"""
        console.print("\n[bold cyan]Reasoning Pattern Analysis[/bold cyan]\n")

        # Get messages
        messages = self.get_all_messages(model_filter)
        console.print(f"Analyzing {len(messages)} messages...")

        if not messages:
            console.print("[yellow]No messages found[/yellow]")
            return

        # Analyze
        by_model = self.analyze_by_model(messages)

        # Display results
        self.display_indicator_analysis(by_model)
        self.display_indicator_pairs(by_model)
        self.display_confidence_analysis(by_model)
        self.display_action_analysis(by_model)

        console.print("\n[dim]Note: This is pattern-based analysis (keyword matching).[/dim]")
        console.print("[dim]For deeper insights, use Phase 2 (LLM structured extraction).[/dim]")


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Analyze reasoning patterns from trading messages"
    )
    parser.add_argument(
        "--model",
        "-m",
        help="Filter by specific model"
    )

    args = parser.parse_args()

    if not DB_PATH.exists():
        console.print(f"[red]Error: Database not found at {DB_PATH}[/red]")
        console.print("\nStart the collector first:")
        console.print("[cyan]cd collector[/cyan]")
        console.print("[cyan]node server.js[/cyan]")
        sys.exit(1)

    analyzer = ReasoningPatternAnalyzer(DB_PATH)

    try:
        analyzer.run_analysis(model_filter=args.model)
    except KeyboardInterrupt:
        console.print("\n[yellow]Interrupted[/yellow]")
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
