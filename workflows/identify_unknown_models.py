#!/usr/bin/env python3
"""
Identify Unknown Models Using Reasoning Pattern Matching

After extraction, analyzes unknown-model messages and attempts to identify
which actual model they came from based on reasoning patterns, style, and
extracted structured data.

Matching Techniques:
1. Reasoning length fingerprints
2. Indicator usage patterns
3. Confidence expression styles
4. Stop loss placement approaches
5. Risk management language
6. Sentence structure and vocabulary

Usage:
  python identify_unknown_models.py
  python identify_unknown_models.py --confidence-threshold 0.7
"""

import sqlite3
import json
from pathlib import Path
from collections import Counter
from typing import Dict, List, Tuple
import sys

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
except ImportError:
    print("Error: 'rich' not installed. Run: uv add rich")
    sys.exit(1)

console = Console()
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "collector" / "nof1_data.db"


class ModelIdentifier:
    """Identify unknown models using reasoning patterns"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        # Build fingerprints from known models
        self.model_fingerprints = self._build_fingerprints()

    def _build_fingerprints(self) -> Dict:
        """Build fingerprints from known model data"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get structured reasoning for known models
        cursor.execute("""
            SELECT
                sr.model_name,
                sr.entry_indicators,
                sr.exit_type,
                sr.confidence_level,
                sr.risk_management,
                sr.decision_summary,
                mc.reasoning
            FROM structured_reasoning sr
            JOIN model_chat mc ON sr.message_id = mc.id
            WHERE sr.model_name != 'unknown-model'
        """)

        fingerprints = {}
        for row in cursor.fetchall():
            model = row['model_name']
            if model not in fingerprints:
                fingerprints[model] = {
                    'reasoning_lengths': [],
                    'entry_indicators': Counter(),
                    'exit_types': Counter(),
                    'confidence_levels': Counter(),
                    'risk_keywords': Counter(),
                    'total_messages': 0
                }

            fp = fingerprints[model]
            fp['total_messages'] += 1
            fp['reasoning_lengths'].append(len(row['reasoning'] or ''))

            # Entry indicators
            if row['entry_indicators']:
                try:
                    indicators = json.loads(row['entry_indicators'])
                    for ind in indicators:
                        fp['entry_indicators'][ind] += 1
                except:
                    pass

            # Exit types
            if row['exit_type']:
                fp['exit_types'][row['exit_type']] += 1

            # Confidence
            if row['confidence_level']:
                fp['confidence_levels'][row['confidence_level']] += 1

            # Risk management keywords
            if row['risk_management']:
                risk_text = row['risk_management'].lower()
                for keyword in ['stop loss', 'position size', 'risk', 'drawdown', 'hedge']:
                    if keyword in risk_text:
                        fp['risk_keywords'][keyword] += 1

        conn.close()

        # Calculate averages
        for model, fp in fingerprints.items():
            if fp['reasoning_lengths']:
                fp['avg_length'] = sum(fp['reasoning_lengths']) / len(fp['reasoning_lengths'])
                fp['length_std'] = (sum((x - fp['avg_length'])**2 for x in fp['reasoning_lengths']) / len(fp['reasoning_lengths'])) ** 0.5

        return fingerprints

    def match_unknown_message(self, unknown_data: Dict) -> Tuple[str, float]:
        """Match an unknown message to a known model

        Returns:
            (model_name, confidence_score) where confidence is 0.0 to 1.0
        """
        scores = {}

        for model, fp in self.model_fingerprints.items():
            score = 0.0
            weights_sum = 0.0

            # 1. Reasoning length similarity (weight: 0.3)
            if fp.get('avg_length'):
                unknown_length = len(unknown_data.get('reasoning', ''))
                length_diff = abs(unknown_length - fp['avg_length'])
                length_similarity = max(0, 1 - (length_diff / fp['avg_length']))
                score += length_similarity * 0.3
                weights_sum += 0.3

            # 2. Entry indicator overlap (weight: 0.25)
            if unknown_data.get('entry_indicators'):
                try:
                    unknown_inds = json.loads(unknown_data['entry_indicators'])
                    indicator_matches = sum(1 for ind in unknown_inds if ind in fp['entry_indicators'])
                    if unknown_inds:
                        indicator_score = indicator_matches / len(unknown_inds)
                        score += indicator_score * 0.25
                        weights_sum += 0.25
                except:
                    pass

            # 3. Exit type match (weight: 0.15)
            if unknown_data.get('exit_type') and fp['exit_types']:
                if unknown_data['exit_type'] in fp['exit_types']:
                    exit_score = fp['exit_types'][unknown_data['exit_type']] / fp['total_messages']
                    score += exit_score * 0.15
                    weights_sum += 0.15

            # 4. Confidence level match (weight: 0.15)
            if unknown_data.get('confidence_level') and fp['confidence_levels']:
                if unknown_data['confidence_level'] in fp['confidence_levels']:
                    conf_score = fp['confidence_levels'][unknown_data['confidence_level']] / fp['total_messages']
                    score += conf_score * 0.15
                    weights_sum += 0.15

            # 5. Risk management keyword overlap (weight: 0.15)
            if unknown_data.get('risk_management') and fp['risk_keywords']:
                risk_text = unknown_data['risk_management'].lower()
                keyword_matches = sum(1 for kw in ['stop loss', 'position size', 'risk', 'drawdown', 'hedge'] if kw in risk_text and kw in fp['risk_keywords'])
                if keyword_matches:
                    risk_score = keyword_matches / len(fp['risk_keywords'])
                    score += risk_score * 0.15
                    weights_sum += 0.15

            # Normalize score
            if weights_sum > 0:
                scores[model] = score / weights_sum
            else:
                scores[model] = 0.0

        # Return best match
        if scores:
            best_model = max(scores.items(), key=lambda x: x[1])
            return best_model
        else:
            return ("unknown", 0.0)

    def identify_all_unknown(self, confidence_threshold: float = 0.5) -> Dict:
        """Identify all unknown-model messages"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        # Get all unknown-model structured data
        cursor.execute("""
            SELECT
                sr.message_id,
                sr.model_name,
                sr.entry_indicators,
                sr.exit_type,
                sr.confidence_level,
                sr.risk_management,
                mc.reasoning
            FROM structured_reasoning sr
            JOIN model_chat mc ON sr.message_id = mc.id
            WHERE sr.model_name = 'unknown-model'
        """)

        results = {
            'total_unknown': 0,
            'identified': 0,
            'unidentified': 0,
            'by_identified_model': Counter(),
            'identifications': []
        }

        for row in cursor.fetchall():
            results['total_unknown'] += 1

            unknown_data = dict(row)
            identified_model, confidence = self.match_unknown_message(unknown_data)

            if confidence >= confidence_threshold:
                results['identified'] += 1
                results['by_identified_model'][identified_model] += 1
                results['identifications'].append({
                    'message_id': row['message_id'],
                    'identified_as': identified_model,
                    'confidence': confidence
                })
            else:
                results['unidentified'] += 1

        conn.close()
        return results

    def update_database(self, identifications: List[Dict], dry_run: bool = True):
        """Update database with identified models"""
        if dry_run:
            console.print("[yellow]Dry run - no changes made[/yellow]")
            return

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        for ident in identifications:
            cursor.execute("""
                UPDATE structured_reasoning
                SET
                    model_name = ?,
                    full_json = json_set(full_json, '$.original_model', 'unknown-model'),
                    full_json = json_set(full_json, '$.identification_confidence', ?)
                WHERE message_id = ?
            """, (ident['identified_as'], ident['confidence'], ident['message_id']))

        conn.commit()
        conn.close()

        console.print(f"[green]Updated {len(identifications)} messages[/green]")

    def display_results(self, results: Dict):
        """Display identification results"""
        console.print("\n[bold cyan]Unknown Model Identification Results[/bold cyan]\n")

        # Summary
        summary_table = Table()
        summary_table.add_column("Metric", style="cyan")
        summary_table.add_column("Count", justify="right", style="green")

        summary_table.add_row("Total unknown-model messages", str(results['total_unknown']))
        summary_table.add_row("Successfully identified", str(results['identified']))
        summary_table.add_row("Could not identify", str(results['unidentified']))

        console.print(summary_table)

        # By identified model
        if results['by_identified_model']:
            console.print("\n[bold cyan]Identified As:[/bold cyan]\n")

            model_table = Table()
            model_table.add_column("Model", style="cyan")
            model_table.add_column("Count", justify="right", style="green")
            model_table.add_column("Percentage", justify="right", style="yellow")

            for model, count in results['by_identified_model'].most_common():
                pct = (count / results['identified']) * 100
                model_table.add_row(model, str(count), f"{pct:.1f}%")

            console.print(model_table)


def main():
    """Main entry point"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Identify unknown models using reasoning patterns"
    )
    parser.add_argument(
        "--confidence-threshold",
        "-c",
        type=float,
        default=0.5,
        help="Minimum confidence score to identify (0.0-1.0, default: 0.5)"
    )
    parser.add_argument(
        "--update-database",
        "-u",
        action="store_true",
        help="Update database with identifications (not dry run)"
    )

    args = parser.parse_args()

    if not DB_PATH.exists():
        console.print(f"[red]Error: Database not found at {DB_PATH}[/red]")
        sys.exit(1)

    # Check if structured_reasoning table exists
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='structured_reasoning'")
    if not cursor.fetchone():
        console.print("[red]Error: structured_reasoning table not found[/red]")
        console.print("\nRun extraction first:")
        console.print("[cyan]uv run python workflows/extract_structured_reasoning.py[/cyan]")
        conn.close()
        sys.exit(1)
    conn.close()

    console.print("\n[bold cyan]Building model fingerprints...[/bold cyan]")
    identifier = ModelIdentifier(DB_PATH)

    console.print("[dim]Fingerprints built from known models[/dim]")
    console.print(f"[dim]Models: {', '.join(identifier.model_fingerprints.keys())}[/dim]")

    console.print("\n[bold cyan]Identifying unknown-model messages...[/bold cyan]")
    results = identifier.identify_all_unknown(confidence_threshold=args.confidence_threshold)

    identifier.display_results(results)

    # Update database if requested
    if results['identifications']:
        console.print(f"\n[dim]Confidence threshold: {args.confidence_threshold}[/dim]")

        if args.update_database:
            identifier.update_database(results['identifications'], dry_run=False)
        else:
            console.print("\n[yellow]To update database, run with --update-database flag[/yellow]")


if __name__ == "__main__":
    main()
