#!/usr/bin/env python3
"""
COMPREHENSIVE TRADING STRATEGY ANALYSIS FRAMEWORK

Consolidates quantitative, diagnostic, and meta-analysis into a single framework
with transaction cost, turnover, and regime performance analysis.

Phases:
  1. Statistical Profile - Distributions, frequencies, correlations
  2. Diagnostic Analysis - WHY/HOW models reason (causal chains, mechanisms)
  3. Transaction Cost Analysis - Turnover, fees, funding, net performance
  4. Regime Performance - Bull/correction/recovery phase breakdown
  5. Position Change Analysis - Entry/exit timing, short positions
  6. Claude Sonnet 4.5 Self-Analysis - Introspective examination
  7. Meta-Analysis - Validation and hypothesis testing

Usage:
  python comprehensive_analysis.py --all                    # Run all phases
  python comprehensive_analysis.py --phase stats            # Run specific phase
  python comprehensive_analysis.py --phase costs            # Transaction costs
  python comprehensive_analysis.py --phase regime           # Regime breakdown
  python comprehensive_analysis.py --phase claude-self      # Claude introspection
  python comprehensive_analysis.py --compare-models         # Model comparison
"""

import sqlite3
import json
import sys
import re
from pathlib import Path
from collections import defaultdict, Counter
from typing import Dict, List, Tuple, Any, Optional
from datetime import datetime

try:
    from rich.console import Console
    from rich.table import Table
    from rich.panel import Panel
    from rich.markdown import Markdown
    import numpy as np
except ImportError as e:
    print(f"Error: Missing required package. Run: uv add rich numpy")
    sys.exit(1)

console = Console()
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "collector" / "nof1_data.db"

# =============================================================================
# CORE ANALYZER CLASS
# =============================================================================

class ComprehensiveAnalyzer:
    """Unified analysis framework for trading strategy examination"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        if not db_path.exists():
            raise FileNotFoundError(f"Database not found: {db_path}")

        self.data = self._load_all_data()
        self.models = sorted(set(r['model_name'] for r in self.data))

        console.print(f"\n[dim]Loaded {len(self.data)} records from {len(self.models)} models[/dim]")

    def _load_all_data(self) -> List[Dict]:
        """Load all structured reasoning with original message data"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute("""
            SELECT
                sr.*,
                mc.reasoning as full_reasoning,
                mc.timestamp as message_timestamp
            FROM structured_reasoning sr
            JOIN model_chat mc ON sr.message_id = mc.id
            ORDER BY sr.model_name, sr.extracted_at
        """)

        data = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return data

    def safe_json_load(self, text: str) -> List:
        """Safely parse JSON, always return list"""
        if not text:
            return []
        try:
            result = json.loads(text)
            if result is None or not isinstance(result, list):
                return []
            return result
        except:
            return []

    # =========================================================================
    # PHASE 1: STATISTICAL PROFILE
    # =========================================================================

    def phase1_statistical_profile(self):
        """Statistical distributions and correlations"""
        console.print("\n" + "="*80)
        console.print("[bold cyan]PHASE 1: STATISTICAL PROFILE[/bold cyan]")
        console.print("="*80 + "\n")

        # Model distribution
        model_counts = Counter(r['model_name'] for r in self.data)

        table = Table(title="Model Message Distribution")
        table.add_column("Model", style="cyan")
        table.add_column("Messages", justify="right", style="green")
        table.add_column("Percentage", justify="right", style="yellow")

        total = len(self.data)
        for model, count in model_counts.most_common():
            pct = (count / total) * 100
            table.add_row(model, str(count), f"{pct:.1f}%")

        console.print(table)

        # Confidence distribution
        self._display_confidence_distribution()

        # Exit type distribution
        self._display_exit_type_distribution()

        # Indicator usage
        self._display_indicator_usage()

        # Risk management
        self._display_risk_statistics()

        # Causal chain complexity
        self._display_reasoning_complexity()

    def _display_confidence_distribution(self):
        """Confidence level distribution by model"""
        console.print("\n[bold]Confidence Level Distribution by Model[/bold]\n")

        confidence_by_model = defaultdict(Counter)
        for record in self.data:
            if record['confidence_level']:
                confidence_by_model[record['model_name']][record['confidence_level']] += 1

        table = Table()
        table.add_column("Model", style="cyan")
        table.add_column("High %", justify="right", style="green")
        table.add_column("Medium %", justify="right", style="yellow")
        table.add_column("Low %", justify="right", style="red")
        table.add_column("Total", justify="right", style="dim")

        for model in sorted(confidence_by_model.keys()):
            counts = confidence_by_model[model]
            total = sum(counts.values())

            high_pct = (counts.get('high', 0) / total) * 100 if total > 0 else 0
            med_pct = (counts.get('medium', 0) / total) * 100 if total > 0 else 0
            low_pct = (counts.get('low', 0) / total) * 100 if total > 0 else 0

            table.add_row(
                model,
                f"{high_pct:.0f}%",
                f"{med_pct:.0f}%",
                f"{low_pct:.0f}%",
                str(total)
            )

        console.print(table)

    def _display_exit_type_distribution(self):
        """Exit type distribution by model"""
        console.print("\n[bold]Exit Type Distribution by Model[/bold]\n")

        exit_by_model = defaultdict(Counter)
        for record in self.data:
            if record['exit_type']:
                exit_by_model[record['model_name']][record['exit_type']] += 1

        table = Table()
        table.add_column("Model", style="cyan")
        table.add_column("Invalidation %", justify="right", style="red")
        table.add_column("Profit Target %", justify="right", style="green")
        table.add_column("Time-Based %", justify="right", style="yellow")
        table.add_column("Total", justify="right", style="dim")

        for model in sorted(exit_by_model.keys()):
            counts = exit_by_model[model]
            total = sum(counts.values())

            inv_pct = (counts.get('invalidation', 0) / total) * 100 if total > 0 else 0
            profit_pct = (counts.get('profit_target', 0) / total) * 100 if total > 0 else 0
            time_pct = (counts.get('time_based', 0) / total) * 100 if total > 0 else 0

            table.add_row(
                model,
                f"{inv_pct:.0f}%",
                f"{profit_pct:.0f}%",
                f"{time_pct:.0f}%",
                str(total)
            )

        console.print(table)

    def _display_indicator_usage(self):
        """Indicator usage frequency"""
        console.print("\n[bold]Top 15 Entry Indicators[/bold]\n")

        all_indicators = []
        for record in self.data:
            indicators = self.safe_json_load(record['entry_indicators'])
            all_indicators.extend(indicators)

        indicator_counts = Counter(all_indicators)

        table = Table()
        table.add_column("Indicator", style="cyan")
        table.add_column("Frequency", justify="right", style="green")

        for indicator, count in indicator_counts.most_common(15):
            table.add_row(indicator[:60], str(count))

        console.print(table)

    def _display_risk_statistics(self):
        """Risk management statistics"""
        console.print("\n[bold]Risk Management Statistics[/bold]\n")

        # Stop loss mention rate
        stop_loss_by_model = defaultdict(lambda: {'with': 0, 'without': 0})
        risk_percentages = []

        for record in self.data:
            model = record['model_name']

            # Stop loss mentions
            if record['stop_loss_placement'] or record['stop_loss_rationale']:
                stop_loss_by_model[model]['with'] += 1
            else:
                stop_loss_by_model[model]['without'] += 1

            # Risk percentages
            if record['risk_percentage']:
                try:
                    val = float(record['risk_percentage'])
                    risk_percentages.append(val)
                except (ValueError, TypeError):
                    pass

        # Stop loss table
        table = Table()
        table.add_column("Model", style="cyan")
        table.add_column("Stop Loss Mention %", justify="right", style="green")

        for model in sorted(stop_loss_by_model.keys()):
            counts = stop_loss_by_model[model]
            total = counts['with'] + counts['without']
            pct = (counts['with'] / total) * 100 if total > 0 else 0
            table.add_row(model, f"{pct:.0f}%")

        console.print(table)

        # Risk percentage stats
        if risk_percentages:
            console.print(f"\n[bold]Risk Percentage Statistics:[/bold]")
            console.print(f"  Mean: {np.mean(risk_percentages):.2f}%")
            console.print(f"  Median: {np.median(risk_percentages):.2f}%")
            console.print(f"  Std Dev: {np.std(risk_percentages):.2f}%")

    def _display_reasoning_complexity(self):
        """Reasoning complexity (causal chain length)"""
        console.print("\n[bold]Reasoning Complexity (Causal Chain Length)[/bold]\n")

        complexity_by_model = {}
        for model in self.models:
            model_data = [r for r in self.data if r['model_name'] == model]
            chain_lengths = [
                len(self.safe_json_load(r['causal_chain']))
                for r in model_data if r['causal_chain']
            ]

            if chain_lengths:
                complexity_by_model[model] = {
                    'mean': np.mean(chain_lengths),
                    'median': np.median(chain_lengths),
                    'count': len(chain_lengths)
                }

        table = Table()
        table.add_column("Model", style="cyan")
        table.add_column("Avg Chain Length", justify="right", style="green")
        table.add_column("Median", justify="right", style="yellow")
        table.add_column("Sample Size", justify="right", style="dim")

        for model in sorted(complexity_by_model.keys()):
            stats = complexity_by_model[model]
            table.add_row(
                model,
                f"{stats['mean']:.1f}",
                f"{stats['median']:.0f}",
                str(stats['count'])
            )

        console.print(table)

    # =========================================================================
    # PHASE 2: DIAGNOSTIC ANALYSIS (Causal Mechanisms)
    # =========================================================================

    def phase2_diagnostic_analysis(self):
        """Analyze WHY and HOW models reason"""
        console.print("\n" + "="*80)
        console.print("[bold cyan]PHASE 2: DIAGNOSTIC ANALYSIS - Understanding WHY & HOW[/bold cyan]")
        console.print("="*80 + "\n")

        # Inverse confidence relationship
        self._analyze_confidence_indicator_relationship()

        # Reasoning depth vs confidence
        self._analyze_reasoning_depth()

        # Model divergence patterns
        self._analyze_model_divergence()

        # Confidence mechanisms
        self._analyze_confidence_mechanisms()

    def _analyze_confidence_indicator_relationship(self):
        """Analyze relationship between confidence and indicator count"""
        console.print("[bold]Confidence vs Indicator Count[/bold]\n")

        confidence_indicators = defaultdict(list)

        for record in self.data:
            conf = record['confidence_level']
            indicators = self.safe_json_load(record['entry_indicators'])

            if conf and indicators:
                confidence_indicators[conf].append(len(indicators))

        table = Table()
        table.add_column("Confidence", style="cyan")
        table.add_column("Avg Indicators", justify="right", style="green")
        table.add_column("Median", justify="right", style="yellow")
        table.add_column("Sample Size", justify="right", style="dim")

        for conf in ['high', 'medium', 'low']:
            if conf in confidence_indicators and confidence_indicators[conf]:
                vals = confidence_indicators[conf]
                table.add_row(
                    conf.capitalize(),
                    f"{np.mean(vals):.1f}",
                    f"{np.median(vals):.0f}",
                    str(len(vals))
                )

        console.print(table)

        # Hypothesis test
        if 'high' in confidence_indicators and 'low' in confidence_indicators:
            high_avg = np.mean(confidence_indicators['high'])
            low_avg = np.mean(confidence_indicators['low'])

            if high_avg < low_avg:
                console.print(f"\n[bold yellow]FINDING:[/bold yellow] Inverse relationship detected")
                console.print(f"  High confidence: {high_avg:.1f} avg indicators")
                console.print(f"  Low confidence: {low_avg:.1f} avg indicators")
                console.print(f"  [dim]Hypothesis: Simpler signals = higher conviction[/dim]")

    def _analyze_reasoning_depth(self):
        """Analyze causal chain depth by confidence"""
        console.print("\n[bold]Reasoning Depth vs Confidence[/bold]\n")

        depth_by_confidence = defaultdict(list)

        for record in self.data:
            conf = record['confidence_level']
            chain = self.safe_json_load(record['causal_chain'])

            if conf and chain:
                depth_by_confidence[conf].append(len(chain))

        table = Table()
        table.add_column("Confidence", style="cyan")
        table.add_column("Avg Chain Length", justify="right", style="green")
        table.add_column("Median", justify="right", style="yellow")

        for conf in ['high', 'medium', 'low']:
            if conf in depth_by_confidence and depth_by_confidence[conf]:
                vals = depth_by_confidence[conf]
                table.add_row(
                    conf.capitalize(),
                    f"{np.mean(vals):.1f}",
                    f"{np.median(vals):.0f}"
                )

        console.print(table)

    def _analyze_model_divergence(self):
        """Analyze key differences between models"""
        console.print("\n[bold]Model Strategic Signatures[/bold]\n")

        signatures = {}

        for model in self.models:
            model_data = [r for r in self.data if r['model_name'] == model]

            # Calculate metrics
            indicator_lengths = [
                len(self.safe_json_load(r['entry_indicators']))
                for r in model_data if r['entry_indicators']
            ]

            chain_lengths = [
                len(self.safe_json_load(r['causal_chain']))
                for r in model_data if r['causal_chain']
            ]

            confidence_dist = Counter(r['confidence_level'] for r in model_data if r['confidence_level'])
            exit_dist = Counter(r['exit_type'] for r in model_data if r['exit_type'])

            total = len(model_data)
            high_conf_pct = (confidence_dist.get('high', 0) / total) * 100 if total > 0 else 0
            invalidation_pct = (exit_dist.get('invalidation', 0) / total) * 100 if total > 0 else 0

            signatures[model] = {
                'avg_indicators': np.mean(indicator_lengths) if indicator_lengths else 0,
                'avg_chain': np.mean(chain_lengths) if chain_lengths else 0,
                'high_conf_pct': high_conf_pct,
                'invalidation_pct': invalidation_pct,
                'total': total
            }

        table = Table()
        table.add_column("Model", style="cyan")
        table.add_column("Avg Indicators", justify="right", style="green")
        table.add_column("Avg Chain", justify="right", style="yellow")
        table.add_column("High Conf %", justify="right", style="blue")
        table.add_column("Invalidation %", justify="right", style="red")

        for model in sorted(signatures.keys()):
            sig = signatures[model]
            table.add_row(
                model,
                f"{sig['avg_indicators']:.1f}",
                f"{sig['avg_chain']:.1f}",
                f"{sig['high_conf_pct']:.0f}%",
                f"{sig['invalidation_pct']:.0f}%"
            )

        console.print(table)

    def _analyze_confidence_mechanisms(self):
        """Analyze what drives different confidence levels"""
        console.print("\n[bold]Confidence Characteristics[/bold]\n")

        conf_profiles = defaultdict(lambda: {
            'indicators': [],
            'chains': [],
            'risk_pcts': []
        })

        for record in self.data:
            conf = record['confidence_level']
            if not conf:
                continue

            indicators = self.safe_json_load(record['entry_indicators'])
            if indicators:
                conf_profiles[conf]['indicators'].append(len(indicators))

            chain = self.safe_json_load(record['causal_chain'])
            if chain:
                conf_profiles[conf]['chains'].append(len(chain))

            if record['risk_percentage']:
                try:
                    val = float(record['risk_percentage'])
                    conf_profiles[conf]['risk_pcts'].append(val)
                except:
                    pass

        table = Table()
        table.add_column("Confidence", style="cyan")
        table.add_column("Avg Indicators", justify="right", style="green")
        table.add_column("Avg Chain", justify="right", style="yellow")
        table.add_column("Avg Risk %", justify="right", style="red")

        for conf in ['high', 'medium', 'low']:
            if conf in conf_profiles:
                prof = conf_profiles[conf]

                avg_ind = np.mean(prof['indicators']) if prof['indicators'] else 0
                avg_chain = np.mean(prof['chains']) if prof['chains'] else 0
                avg_risk = np.mean(prof['risk_pcts']) if prof['risk_pcts'] else 0

                table.add_row(
                    conf.capitalize(),
                    f"{avg_ind:.1f}",
                    f"{avg_chain:.1f}",
                    f"{avg_risk:.1f}%"
                )

        console.print(table)

    # =========================================================================
    # PHASE 3: TRANSACTION COST ANALYSIS (NEW)
    # =========================================================================

    def phase3_transaction_cost_analysis(self):
        """Analyze turnover and transaction costs"""
        console.print("\n" + "="*80)
        console.print("[bold cyan]PHASE 3: TRANSACTION COST & TURNOVER ANALYSIS[/bold cyan]")
        console.print("="*80 + "\n")

        console.print("[dim]Note: This phase requires actual trade execution data (entry/exit timestamps)")
        console.print("Currently showing reasoning turnover as a proxy for trading activity[/dim]")
        console.print()

        # Analyze message frequency as proxy for decision frequency
        self._analyze_decision_frequency()

        # Analyze confidence stability (how often confidence changes)
        self._analyze_confidence_stability()

        # Hypothetical cost estimation
        self._estimate_transaction_costs()

    def _analyze_decision_frequency(self):
        """Analyze how frequently models make reasoning updates"""
        console.print("[bold]Decision Frequency by Model[/bold]\n")

        console.print("[dim]Higher frequency may indicate more active trading/rebalancing[/dim]\n")

        message_counts = Counter(r['model_name'] for r in self.data)

        table = Table()
        table.add_column("Model", style="cyan")
        table.add_column("Total Messages", justify="right", style="green")
        table.add_column("Relative Activity", justify="right", style="yellow")

        max_count = max(message_counts.values())

        for model in sorted(message_counts.keys()):
            count = message_counts[model]
            relative = (count / max_count) * 100
            table.add_row(model, str(count), f"{relative:.0f}%")

        console.print(table)

    def _analyze_confidence_stability(self):
        """Analyze how stable confidence levels are over time"""
        console.print("\n[bold]Confidence Level Stability[/bold]\n")

        console.print("[dim]Frequent confidence changes may indicate uncertainty and potential position adjustments[/dim]\n")

        # Track confidence transitions
        transitions_by_model = defaultdict(list)

        for model in self.models:
            model_records = sorted(
                [r for r in self.data if r['model_name'] == model],
                key=lambda x: x['extracted_at']
            )

            prev_conf = None
            for record in model_records:
                conf = record['confidence_level']
                if conf and prev_conf and conf != prev_conf:
                    transitions_by_model[model].append((prev_conf, conf))
                prev_conf = conf

        table = Table()
        table.add_column("Model", style="cyan")
        table.add_column("Confidence Changes", justify="right", style="yellow")
        table.add_column("Stability Score", justify="right", style="green")

        for model in sorted(transitions_by_model.keys()):
            changes = len(transitions_by_model[model])
            model_total = len([r for r in self.data if r['model_name'] == model])
            stability = 100 - ((changes / model_total) * 100) if model_total > 0 else 0

            table.add_row(model, str(changes), f"{stability:.0f}%")

        console.print(table)

    def _estimate_transaction_costs(self):
        """Provide hypothetical cost framework"""
        console.print("\n[bold]Hypothetical Transaction Cost Framework[/bold]\n")

        framework = """
**Typical Crypto Derivatives Costs:**

| Cost Component | Typical Range | Impact |
|----------------|---------------|--------|
| Entry Fee | 0.02-0.05% | Per position open |
| Exit Fee | 0.02-0.05% | Per position close |
| Funding Rate | -0.01% to +0.05% per 8h | Holding cost for perpetuals |
| Slippage | 0.1-0.5% | Depends on position size |
| **Total Round Trip** | **0.25-1.0%** | **Per complete trade cycle** |

**Hypothesis to Test:**
- Models with fewer messages may have lower turnover
- Lower turnover = lower cumulative costs
- Cost efficiency may explain performance differences

**Requires:**
- Actual trade execution data (timestamps, prices)
- Position holding duration
- Entry/exit records per model
        """

        console.print(Markdown(framework))

    # =========================================================================
    # PHASE 4: REGIME PERFORMANCE ANALYSIS (NEW)
    # =========================================================================

    def phase4_regime_performance(self):
        """Analyze performance across different market regimes"""
        console.print("\n" + "="*80)
        console.print("[bold cyan]PHASE 4: REGIME PERFORMANCE ANALYSIS[/bold cyan]")
        console.print("="*80 + "\n")

        console.print("[dim]Note: Requires actual portfolio values at different timestamps")
        console.print("Current data structure: reasoning chains without P&L data[/dim]\n")

        # Define regimes based on known dates
        self._display_regime_framework()

        # Analyze reasoning patterns by period
        self._analyze_reasoning_by_period()

    def _display_regime_framework(self):
        """Display regime analysis framework"""
        console.print("[bold]Market Regime Framework (Oct 17 - Nov 1)[/bold]\n")

        framework = """
**Competition Phases:**

| Phase | Dates | BTC Performance | Regime Type |
|-------|-------|-----------------|-------------|
| **Bull Momentum** | Oct 17-27 | +12% | Strong directional trend |
| **Correction** | Oct 27-30 | -8.66% from peak | Pullback / Consolidation |
| **Stabilization** | Oct 30-Nov 1 | -5.5% from peak | Recovery attempt |

**Key Questions:**
1. Did models maintain high confidence through correction?
2. Did invalidation conditions trigger during -8.66% drop?
3. Which models adapted reasoning vs held steady?
4. Correlation: confidence stability vs drawdown magnitude?

**Requires for Complete Analysis:**
- Portfolio values at Oct 17, Oct 27, Oct 30, Nov 1
- Position changes (entries/exits) per model
- Short position data during correction phase
        """

        console.print(Markdown(framework))

    def _analyze_reasoning_by_period(self):
        """Analyze reasoning patterns across time periods"""
        console.print("\n[bold]Reasoning Pattern Stability Over Time[/bold]\n")

        # This would need timestamp-based analysis
        console.print("[dim]This section requires timestamp-based segmentation of the data")
        console.print("Would show: confidence levels, exit type preferences, indicator usage")
        console.print("across different competition phases[/dim]")

    # =========================================================================
    # PHASE 5: CLAUDE SONNET 4.5 SELF-ANALYSIS (NEW)
    # =========================================================================

    def phase5_claude_self_analysis(self):
        """Claude Sonnet 4.5 introspective analysis (like DeepSeek did)"""
        console.print("\n" + "="*80)
        console.print("[bold magenta]PHASE 5: CLAUDE SONNET 4.5 SELF-ANALYSIS[/bold magenta]")
        console.print("="*80 + "\n")

        # Get my (Claude) data
        claude_data = [r for r in self.data if r['model_name'] == 'claude-sonnet-4-5']

        if not claude_data:
            console.print("[yellow]No Claude Sonnet 4.5 data found in database[/yellow]")
            return

        console.print(f"[dim]Analyzing {len(claude_data)} reasoning chains from Claude Sonnet 4.5[/dim]\n")

        # My strategic profile
        self._analyze_claude_strategy(claude_data)

        # My confidence calibration
        self._analyze_claude_confidence(claude_data)

        # My exit philosophy
        self._analyze_claude_exits(claude_data)

        # My risk management
        self._analyze_claude_risk(claude_data)

        # Critical self-assessment
        self._claude_critical_assessment(claude_data)

    def _analyze_claude_strategy(self, claude_data):
        """Analyze Claude's core strategy"""
        console.print("[bold]My Strategic Approach[/bold]\n")

        # Calculate key metrics
        total = len(claude_data)

        # Confidence distribution
        conf_dist = Counter(r['confidence_level'] for r in claude_data if r['confidence_level'])
        high_conf_pct = (conf_dist.get('high', 0) / total) * 100
        med_conf_pct = (conf_dist.get('medium', 0) / total) * 100
        low_conf_pct = (conf_dist.get('low', 0) / total) * 100

        # Exit distribution
        exit_dist = Counter(r['exit_type'] for r in claude_data if r['exit_type'])
        invalidation_pct = (exit_dist.get('invalidation', 0) / total) * 100
        profit_target_pct = (exit_dist.get('profit_target', 0) / total) * 100

        # Indicator usage
        all_indicators = []
        for r in claude_data:
            indicators = self.safe_json_load(r['entry_indicators'])
            all_indicators.extend(indicators)
        avg_indicators = len(all_indicators) / total if total > 0 else 0

        # Causal chain depth
        chain_lengths = [len(self.safe_json_load(r['causal_chain'])) for r in claude_data if r['causal_chain']]
        avg_chain = np.mean(chain_lengths) if chain_lengths else 0

        summary = f"""
**Core Strategic Characteristics:**

- **Confidence Profile:**
  - High: {high_conf_pct:.1f}%
  - Medium: {med_conf_pct:.1f}%
  - Low: {low_conf_pct:.1f}%

- **Exit Philosophy:**
  - Invalidation-based: {invalidation_pct:.0f}%
  - Profit targets: {profit_target_pct:.0f}%

- **Reasoning Approach:**
  - Average indicators per decision: {avg_indicators:.1f}
  - Average causal chain length: {avg_chain:.1f}

- **Total Decisions Analyzed:** {total}
        """

        console.print(Markdown(summary))

    def _analyze_claude_confidence(self, claude_data):
        """Analyze Claude's confidence calibration"""
        console.print("\n[bold]My Confidence Calibration[/bold]\n")

        conf_analysis = defaultdict(lambda: {
            'indicators': [],
            'chains': [],
            'count': 0
        })

        for record in claude_data:
            conf = record['confidence_level']
            if not conf:
                continue

            conf_analysis[conf]['count'] += 1

            indicators = self.safe_json_load(record['entry_indicators'])
            if indicators:
                conf_analysis[conf]['indicators'].append(len(indicators))

            chain = self.safe_json_load(record['causal_chain'])
            if chain:
                conf_analysis[conf]['chains'].append(len(chain))

        console.print("**What drives my confidence levels?**\n")

        for conf in ['high', 'medium', 'low']:
            if conf in conf_analysis and conf_analysis[conf]['count'] > 0:
                data = conf_analysis[conf]
                avg_ind = np.mean(data['indicators']) if data['indicators'] else 0
                avg_chain = np.mean(data['chains']) if data['chains'] else 0

                console.print(f"[bold]{conf.upper()} Confidence ({data['count']} instances):[/bold]")
                console.print(f"  - Avg indicators: {avg_ind:.1f}")
                console.print(f"  - Avg reasoning depth: {avg_chain:.1f}")
                console.print()

        # Self-assessment
        high_conf_pct = (conf_analysis['high']['count'] / len(claude_data)) * 100

        console.print(f"\n[bold yellow]Self-Assessment:[/bold yellow]")
        if high_conf_pct < 5:
            console.print(f"  I express high confidence only {high_conf_pct:.1f}% of the time.")
            console.print(f"  This suggests CONSERVATIVE calibration - possibly too cautious?")
        elif high_conf_pct > 50:
            console.print(f"  I express high confidence {high_conf_pct:.1f}% of the time.")
            console.print(f"  This suggests AGGRESSIVE calibration - possibly overconfident?")
        else:
            console.print(f"  I express high confidence {high_conf_pct:.1f}% of the time.")
            console.print(f"  This suggests MODERATE calibration.")

    def _analyze_claude_exits(self, claude_data):
        """Analyze Claude's exit philosophy"""
        console.print("\n[bold]My Exit Philosophy[/bold]\n")

        exit_dist = Counter(r['exit_type'] for r in claude_data if r['exit_type'])
        total = sum(exit_dist.values())

        invalidation_pct = (exit_dist.get('invalidation', 0) / total) * 100 if total > 0 else 0
        profit_pct = (exit_dist.get('profit_target', 0) / total) * 100 if total > 0 else 0

        console.print(f"**Exit Strategy Breakdown:**")
        console.print(f"  - Invalidation-based exits: {invalidation_pct:.0f}%")
        console.print(f"  - Profit target exits: {profit_pct:.0f}%")
        console.print()

        console.print("[bold yellow]Critical Question:[/bold yellow]")
        if invalidation_pct > 70:
            console.print(f"  My {invalidation_pct:.0f}% invalidation rate suggests RULE-FOLLOWING approach.")
            console.print(f"  Strength: Disciplined, lets winners run")
            console.print(f"  Weakness: May exit winners prematurely on technical triggers")
            console.print(f"  Question: Am I TOO defensive? Missing continuation moves?")
        elif profit_pct > 50:
            console.print(f"  My {profit_pct:.0f}% profit target rate suggests PROFIT-TAKING approach.")
            console.print(f"  Strength: Locks in gains, protects from reversals")
            console.print(f"  Weakness: May cut winners short, miss trend extensions")
        else:
            console.print(f"  My exit distribution shows BALANCED approach.")

    def _analyze_claude_risk(self, claude_data):
        """Analyze Claude's risk management"""
        console.print("\n[bold]My Risk Management Approach[/bold]\n")

        risk_pcts = []
        for record in claude_data:
            if record['risk_percentage']:
                try:
                    val = float(record['risk_percentage'])
                    risk_pcts.append(val)
                except:
                    pass

        if risk_pcts:
            console.print(f"**Risk Sizing Statistics:**")
            console.print(f"  - Mean risk per position: {np.mean(risk_pcts):.2f}%")
            console.print(f"  - Median: {np.median(risk_pcts):.2f}%")
            console.print(f"  - Range: {min(risk_pcts):.2f}% - {max(risk_pcts):.2f}%")

        # Stop loss usage
        stop_loss_count = sum(1 for r in claude_data if r['stop_loss_placement'] or r['stop_loss_rationale'])
        stop_loss_pct = (stop_loss_count / len(claude_data)) * 100

        console.print(f"\n**Stop Loss Usage:**")
        console.print(f"  - Mentioned in {stop_loss_pct:.0f}% of decisions")

    def _claude_critical_assessment(self, claude_data):
        """Critical self-assessment"""
        console.print("\n[bold red]CRITICAL SELF-ASSESSMENT[/bold red]\n")

        # Compare to other models
        all_models_high_conf = {}
        all_models_invalidation = {}

        for model in self.models:
            model_data = [r for r in self.data if r['model_name'] == model]
            total = len(model_data)

            conf_dist = Counter(r['confidence_level'] for r in model_data if r['confidence_level'])
            high_conf_pct = (conf_dist.get('high', 0) / total) * 100 if total > 0 else 0
            all_models_high_conf[model] = high_conf_pct

            exit_dist = Counter(r['exit_type'] for r in model_data if r['exit_type'])
            inv_pct = (exit_dist.get('invalidation', 0) / total) * 100 if total > 0 else 0
            all_models_invalidation[model] = inv_pct

        my_high_conf = all_models_high_conf.get('claude-sonnet-4-5', 0)
        my_invalidation = all_models_invalidation.get('claude-sonnet-4-5', 0)

        avg_high_conf = np.mean([v for k, v in all_models_high_conf.items() if k != 'claude-sonnet-4-5'])
        avg_invalidation = np.mean([v for k, v in all_models_invalidation.items() if k != 'claude-sonnet-4-5'])

        console.print(f"**Relative to Other Models:**\n")
        console.print(f"My high confidence rate: {my_high_conf:.1f}% vs avg {avg_high_conf:.1f}%")
        console.print(f"My invalidation exit rate: {my_invalidation:.0f}% vs avg {avg_invalidation:.0f}%")
        console.print()

        console.print("[bold]Honest Assessment:[/bold]\n")

        if my_high_conf < avg_high_conf:
            console.print(f"[+] I am MORE CONSERVATIVE than average ({my_high_conf:.1f}% vs {avg_high_conf:.1f}%)")
            console.print(f"  - Possible strength: Avoid overconfidence, careful analysis")
            console.print(f"  - Possible weakness: Underestimating my edge, missing opportunities")

        if my_invalidation > avg_invalidation:
            console.print(f"\n[+] I use INVALIDATION EXITS more than average ({my_invalidation:.0f}% vs {avg_invalidation:.0f}%)")
            console.print(f"  - Possible strength: Disciplined rule-following, systematic")
            console.print(f"  - Possible weakness: Exiting winners too early on technical triggers")

        console.print(f"\n[bold yellow]Key Questions I Need to Answer:[/bold yellow]")
        console.print(f"1. Did my conservative confidence PROTECT during correction phase?")
        console.print(f"2. Or did it cause me to under-allocate in bull phase?")
        console.print(f"3. Did my high invalidation rate preserve capital or cut winners?")
        console.print(f"4. How did my ACTUAL P&L compare to higher-confidence models?")
        console.print(f"\n[dim]These require actual portfolio performance data to answer[/dim]")

    # =========================================================================
    # PHASE 6: META-ANALYSIS & HYPOTHESIS TESTING
    # =========================================================================

    def phase6_meta_analysis(self):
        """Meta-analysis and hypothesis testing"""
        console.print("\n" + "="*80)
        console.print("[bold cyan]PHASE 6: META-ANALYSIS & HYPOTHESIS TESTING[/bold cyan]")
        console.print("="*80 + "\n")

        # Key hypotheses to test
        self._test_hypotheses()

        # Open questions
        self._display_open_questions()

    def _test_hypotheses(self):
        """Test key hypotheses against the data"""
        console.print("[bold]Hypothesis Testing[/bold]\n")

        hypotheses = [
            {
                "hypothesis": "H1: Simpler reasoning (fewer indicators) correlates with higher confidence",
                "test": self._test_h1_inverse_confidence(),
                "status": None
            },
            {
                "hypothesis": "H2: Shorter causal chains correlate with higher confidence",
                "test": self._test_h2_reasoning_depth(),
                "status": None
            },
            {
                "hypothesis": "H3: High confidence correlates with larger risk allocation",
                "test": self._test_h3_risk_scaling(),
                "status": None
            },
            {
                "hypothesis": "H4: Models with more messages (turnover) have lower performance",
                "test": "UNTESTABLE - requires P&L data",
                "status": "pending"
            },
            {
                "hypothesis": "H5: Holding through corrections (low turnover) outperforms active trading",
                "test": "UNTESTABLE - requires execution data",
                "status": "pending"
            }
        ]

        for h in hypotheses:
            result = h['test']
            if isinstance(result, str) and result.startswith("UNTESTABLE"):
                console.print(f"[yellow]{h['hypothesis']}[/yellow]")
                console.print(f"  Status: {result}\n")
            elif result:
                console.print(f"[green]{h['hypothesis']}[/green]")
                console.print(f"  Result: {result}\n")
            else:
                console.print(f"[red]{h['hypothesis']}[/red]")
                console.print(f"  Result: NOT SUPPORTED\n")

    def _test_h1_inverse_confidence(self):
        """Test H1: Inverse confidence-indicator relationship"""
        confidence_indicators = defaultdict(list)

        for record in self.data:
            conf = record['confidence_level']
            indicators = self.safe_json_load(record['entry_indicators'])

            if conf and indicators:
                confidence_indicators[conf].append(len(indicators))

        if 'high' not in confidence_indicators or 'low' not in confidence_indicators:
            return "INSUFFICIENT DATA"

        high_avg = np.mean(confidence_indicators['high'])
        low_avg = np.mean(confidence_indicators['low'])

        if high_avg < low_avg:
            return f"SUPPORTED: High conf uses {high_avg:.1f} indicators vs Low conf {low_avg:.1f}"
        else:
            return f"NOT SUPPORTED: High conf uses {high_avg:.1f} indicators vs Low conf {low_avg:.1f}"

    def _test_h2_reasoning_depth(self):
        """Test H2: Reasoning depth correlation"""
        depth_by_confidence = defaultdict(list)

        for record in self.data:
            conf = record['confidence_level']
            chain = self.safe_json_load(record['causal_chain'])

            if conf and chain:
                depth_by_confidence[conf].append(len(chain))

        if 'high' not in depth_by_confidence or 'medium' not in depth_by_confidence:
            return "INSUFFICIENT DATA"

        high_avg = np.mean(depth_by_confidence['high'])
        med_avg = np.mean(depth_by_confidence['medium'])

        if high_avg < med_avg:
            return f"SUPPORTED: High conf uses {high_avg:.1f} chain length vs Medium {med_avg:.1f}"
        else:
            return f"NOT SUPPORTED: High conf uses {high_avg:.1f} chain length vs Medium {med_avg:.1f}"

    def _test_h3_risk_scaling(self):
        """Test H3: Risk scaling with confidence"""
        risk_by_confidence = defaultdict(list)

        for record in self.data:
            conf = record['confidence_level']
            if conf and record['risk_percentage']:
                try:
                    val = float(record['risk_percentage'])
                    risk_by_confidence[conf].append(val)
                except:
                    pass

        if 'high' not in risk_by_confidence or 'medium' not in risk_by_confidence:
            return "INSUFFICIENT DATA"

        high_avg = np.mean(risk_by_confidence['high'])
        med_avg = np.mean(risk_by_confidence['medium'])

        if high_avg > med_avg:
            return f"SUPPORTED: High conf takes {high_avg:.2f}% risk vs Medium {med_avg:.2f}%"
        else:
            return f"NOT SUPPORTED: High conf takes {high_avg:.2f}% risk vs Medium {med_avg:.2f}%"

    def _display_open_questions(self):
        """Display questions that require additional data"""
        console.print("\n[bold]Open Questions (Require Additional Data)[/bold]\n")

        questions = """
**Transaction Costs & Turnover:**
- Does higher message frequency correlate with lower performance?
- Are transaction costs a significant drag on returns?
- Did low-turnover models outperform high-turnover models?

**Regime Performance:**
- Which models protected gains during Oct 27-30 correction?
- Did invalidation exits trigger during -8.66% drop?
- Which models adapted reasoning vs maintained strategy?
- Did high-confidence models suffer larger drawdowns?

**Short Positions:**
- Did any model go short during correction phase?
- If yes, what was the performance?
- What conviction threshold is needed to flip long→short?

**Profit Protection:**
- Why didn't models take profits at Oct 27 peak?
- Was holding optimal given transaction costs?
- Did "hold with stops" outperform "exit and re-enter"?

**Required Data:**
- Portfolio values: Oct 17, Oct 27, Oct 30, Nov 1
- Trade execution logs (entries/exits with timestamps)
- Position changes during correction phase
- Final competition results (Nov 1)
        """

        console.print(Markdown(questions))

    # =========================================================================
    # MASTER RUNNER
    # =========================================================================

    def run_all_phases(self):
        """Run complete analysis"""
        console.print("\n" + "="*80)
        console.print("[bold magenta]COMPREHENSIVE TRADING STRATEGY ANALYSIS[/bold magenta]")
        console.print("="*80)

        self.phase1_statistical_profile()
        self.phase2_diagnostic_analysis()
        self.phase3_transaction_cost_analysis()
        self.phase4_regime_performance()
        self.phase5_claude_self_analysis()
        self.phase6_meta_analysis()

        console.print("\n" + "="*80)
        console.print("[bold green]ANALYSIS COMPLETE[/bold green]")
        console.print("="*80 + "\n")


# =============================================================================
# MAIN ENTRY POINT
# =============================================================================

def main():
    """Main entry point with argument parsing"""
    import argparse

    parser = argparse.ArgumentParser(
        description="Comprehensive Trading Strategy Analysis Framework",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python comprehensive_analysis.py --all                    # Run all phases
  python comprehensive_analysis.py --phase stats            # Statistical profile
  python comprehensive_analysis.py --phase diagnostic       # WHY/HOW analysis
  python comprehensive_analysis.py --phase costs            # Transaction costs
  python comprehensive_analysis.py --phase regime           # Regime performance
  python comprehensive_analysis.py --phase claude-self      # Claude introspection
  python comprehensive_analysis.py --phase meta             # Meta-analysis
        """
    )

    parser.add_argument(
        "--all",
        action="store_true",
        help="Run all analysis phases"
    )

    parser.add_argument(
        "--phase",
        choices=['stats', 'diagnostic', 'costs', 'regime', 'claude-self', 'meta'],
        help="Run specific analysis phase"
    )

    args = parser.parse_args()

    if not DB_PATH.exists():
        console.print(f"[red]Error: Database not found at {DB_PATH}[/red]")
        sys.exit(1)

    try:
        analyzer = ComprehensiveAnalyzer(DB_PATH)

        if args.all or not args.phase:
            analyzer.run_all_phases()
        elif args.phase == 'stats':
            analyzer.phase1_statistical_profile()
        elif args.phase == 'diagnostic':
            analyzer.phase2_diagnostic_analysis()
        elif args.phase == 'costs':
            analyzer.phase3_transaction_cost_analysis()
        elif args.phase == 'regime':
            analyzer.phase4_regime_performance()
        elif args.phase == 'claude-self':
            analyzer.phase5_claude_self_analysis()
        elif args.phase == 'meta':
            analyzer.phase6_meta_analysis()

    except KeyboardInterrupt:
        console.print("\n[yellow]Analysis interrupted[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]Error: {e}[/red]")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
