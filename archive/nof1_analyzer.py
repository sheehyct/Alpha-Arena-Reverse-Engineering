#!/usr/bin/env python3
"""
NOF1.AI Data Analyzer - Extract Trading Insights from ModelChat
Analyzes DeepSeek's reasoning patterns to identify systematic strategies
"""

import sqlite3
import json
import re
from datetime import datetime
from typing import Dict, List, Tuple
from collections import Counter, defaultdict


class NOF1Analyzer:
    """Analyze scraped ModelChat data to extract trading patterns"""
    
    def __init__(self, db_path: str = "nof1_data.db"):
        self.db_path = db_path
    
    def get_messages(self, model_name: str = None, limit: int = None) -> List[Dict]:
        """Retrieve messages from database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        if model_name:
            query = 'SELECT * FROM model_chat WHERE model_name = ? ORDER BY scraped_at DESC'
            params = (model_name,)
        else:
            query = 'SELECT * FROM model_chat ORDER BY scraped_at DESC'
            params = ()
        
        if limit:
            query += f' LIMIT {limit}'
        
        cursor.execute(query, params)
        
        columns = [desc[0] for desc in cursor.description]
        messages = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return messages
    
    def extract_key_phrases(self, messages: List[Dict]) -> Counter:
        """Extract and count key trading phrases"""
        phrases = []
        
        # Key pattern indicators
        patterns = [
            r'stop[- ]loss',
            r'take[- ]profit',
            r'invalidation',
            r'confidence',
            r'breakout',
            r'momentum',
            r'trend',
            r'support',
            r'resistance',
            r'volume',
            r'\d+x leverage',
            r'long position',
            r'short position',
            r'entry',
            r'exit',
            r'risk[- ]reward'
        ]
        
        for msg in messages:
            text = msg.get('reasoning') or msg.get('raw_content', '')
            text = text.lower()
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                phrases.extend(matches)
        
        return Counter(phrases)
    
    def analyze_deepseek_strategy(self) -> Dict:
        """Analyze DeepSeek's trading strategy patterns"""
        messages = self.get_messages(model_name='deepseek-v3.1')
        
        if not messages:
            return {"error": "No DeepSeek messages found"}
        
        analysis = {
            'total_messages': len(messages),
            'date_range': (messages[-1]['scraped_at'], messages[0]['scraped_at']),
            'key_phrases': {},
            'position_patterns': {},
            'confidence_patterns': {},
            'sample_reasoning': []
        }
        
        # Extract key phrases
        phrases = self.extract_key_phrases(messages)
        analysis['key_phrases'] = dict(phrases.most_common(20))
        
        # Sample reasoning chains
        for msg in messages[:5]:
            analysis['sample_reasoning'].append({
                'timestamp': msg['scraped_at'],
                'content': msg.get('reasoning') or msg.get('raw_content', '')[:500]
            })
        
        return analysis
    
    def compare_models(self) -> Dict:
        """Compare strategy differences between models"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Get message counts per model
        cursor.execute('SELECT model_name, COUNT(*) FROM model_chat GROUP BY model_name')
        message_counts = dict(cursor.fetchall())
        
        # Get average confidence by model (if available)
        cursor.execute('''
            SELECT model_name, AVG(confidence), MIN(confidence), MAX(confidence)
            FROM model_chat 
            WHERE confidence IS NOT NULL
            GROUP BY model_name
        ''')
        confidence_stats = {}
        for row in cursor.fetchall():
            confidence_stats[row[0]] = {
                'avg': row[1],
                'min': row[2],
                'max': row[3]
            }
        
        conn.close()
        
        return {
            'message_counts': message_counts,
            'confidence_stats': confidence_stats
        }
    
    def find_entry_signals(self, model_name: str = 'deepseek-v3.1') -> List[Dict]:
        """Extract entry signal patterns from messages"""
        messages = self.get_messages(model_name=model_name)
        
        entry_signals = []
        
        # Entry signal keywords
        entry_keywords = [
            'opening', 'entering', 'taking position', 'buying', 'going long', 
            'going short', 'initiating', 'entry'
        ]
        
        for msg in messages:
            text = (msg.get('reasoning') or msg.get('raw_content', '')).lower()
            
            # Check if this is an entry signal
            if any(keyword in text for keyword in entry_keywords):
                # Try to extract position details
                position_info = {
                    'timestamp': msg['scraped_at'],
                    'confidence': msg.get('confidence'),
                    'reasoning_snippet': text[:300],
                    'detected_patterns': []
                }
                
                # Extract leverage
                leverage_match = re.search(r'(\d+)x\s*leverage', text)
                if leverage_match:
                    position_info['leverage'] = leverage_match.group(1)
                
                # Extract stop loss mention
                if 'stop' in text or 'sl' in text:
                    position_info['detected_patterns'].append('stop_loss_defined')
                
                # Extract invalidation
                if 'invalidation' in text or 'invalid' in text:
                    position_info['detected_patterns'].append('invalidation_condition')
                
                # Extract momentum
                if 'momentum' in text or 'accelerat' in text:
                    position_info['detected_patterns'].append('momentum_signal')
                
                entry_signals.append(position_info)
        
        return entry_signals
    
    def find_exit_patterns(self, model_name: str = 'deepseek-v3.1') -> Dict:
        """Analyze exit decision patterns"""
        messages = self.get_messages(model_name=model_name)
        
        exit_patterns = {
            'invalidation_exits': [],
            'profit_target_exits': [],
            'stop_loss_exits': [],
            'discretionary_exits': []
        }
        
        exit_keywords = ['closing', 'exiting', 'exit', 'sold', 'closed position']
        
        for msg in messages:
            text = (msg.get('reasoning') or msg.get('raw_content', '')).lower()
            
            if any(keyword in text for keyword in exit_keywords):
                exit_info = {
                    'timestamp': msg['scraped_at'],
                    'reasoning': text[:200]
                }
                
                # Categorize exit type
                if 'invalidat' in text:
                    exit_patterns['invalidation_exits'].append(exit_info)
                elif 'target' in text or 'profit' in text:
                    exit_patterns['profit_target_exits'].append(exit_info)
                elif 'stop' in text or 'loss' in text:
                    exit_patterns['stop_loss_exits'].append(exit_info)
                else:
                    exit_patterns['discretionary_exits'].append(exit_info)
        
        # Add counts
        for key in exit_patterns:
            exit_patterns[f'{key}_count'] = len(exit_patterns[key])
        
        return exit_patterns
    
    def extract_timeframe_mentions(self, model_name: str = 'deepseek-v3.1') -> Counter:
        """Extract mentioned timeframes"""
        messages = self.get_messages(model_name=model_name)
        
        timeframes = []
        patterns = [
            r'(\d+)[-\s]?(min|minute)',
            r'(\d+)[-\s]?(hour|hr)',
            r'(\d+)[-\s]?(day)',
            r'(daily|hourly|weekly)',
            r'(short[- ]term|medium[- ]term|long[- ]term)'
        ]
        
        for msg in messages:
            text = (msg.get('reasoning') or msg.get('raw_content', '')).lower()
            for pattern in patterns:
                matches = re.findall(pattern, text)
                timeframes.extend([' '.join(m) if isinstance(m, tuple) else m for m in matches])
        
        return Counter(timeframes)
    
    def generate_summary_report(self, output_file: str = "deepseek_analysis.txt"):
        """Generate comprehensive analysis report"""
        
        print("🔍 Analyzing DeepSeek Trading Strategy...\n")
        
        report = []
        report.append("=" * 70)
        report.append("DEEPSEEK V3.1 TRADING STRATEGY ANALYSIS")
        report.append("=" * 70)
        report.append("")
        
        # Basic stats
        strategy = self.analyze_deepseek_strategy()
        report.append(f"Total Messages Analyzed: {strategy.get('total_messages', 0)}")
        report.append(f"Date Range: {strategy.get('date_range', ('N/A', 'N/A'))}")
        report.append("")
        
        # Key phrases
        report.append("📊 Most Common Trading Phrases:")
        report.append("-" * 70)
        for phrase, count in list(strategy.get('key_phrases', {}).items())[:15]:
            report.append(f"  {phrase:30s} {count:>5d} occurrences")
        report.append("")
        
        # Entry signals
        entry_signals = self.find_entry_signals()
        report.append(f"🎯 Entry Signals Detected: {len(entry_signals)}")
        report.append("-" * 70)
        if entry_signals:
            for i, signal in enumerate(entry_signals[:5], 1):
                report.append(f"\nSignal #{i}:")
                report.append(f"  Timestamp: {signal['timestamp']}")
                report.append(f"  Confidence: {signal.get('confidence', 'N/A')}")
                report.append(f"  Patterns: {', '.join(signal['detected_patterns']) or 'None detected'}")
                report.append(f"  Snippet: {signal['reasoning_snippet'][:150]}...")
        report.append("")
        
        # Exit patterns
        exit_patterns = self.find_exit_patterns()
        report.append("🚪 Exit Pattern Analysis:")
        report.append("-" * 70)
        report.append(f"  Invalidation Exits: {exit_patterns.get('invalidation_exits_count', 0)}")
        report.append(f"  Profit Target Exits: {exit_patterns.get('profit_target_exits_count', 0)}")
        report.append(f"  Stop Loss Exits: {exit_patterns.get('stop_loss_exits_count', 0)}")
        report.append(f"  Discretionary Exits: {exit_patterns.get('discretionary_exits_count', 0)}")
        report.append("")
        
        # Timeframes
        timeframes = self.extract_timeframe_mentions()
        if timeframes:
            report.append("⏰ Timeframe Mentions:")
            report.append("-" * 70)
            for tf, count in timeframes.most_common(10):
                report.append(f"  {tf:20s} {count:>3d} mentions")
        report.append("")
        
        # Sample reasoning
        report.append("💭 Sample Reasoning Chains:")
        report.append("-" * 70)
        for i, sample in enumerate(strategy.get('sample_reasoning', [])[:3], 1):
            report.append(f"\n[{sample['timestamp']}]")
            report.append(sample['content'][:400])
            report.append("...")
        
        report.append("")
        report.append("=" * 70)
        
        # Write to file
        report_text = '\n'.join(report)
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report_text)
        
        print(report_text)
        print(f"\n✓ Full report saved to: {output_file}")
        
        return report_text


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Analyze NOF1.AI scraped data')
    parser.add_argument('--db', default='nof1_data.db', help='Database file path')
    parser.add_argument('--model', default='deepseek-v3.1', help='Model to analyze')
    parser.add_argument('--report', action='store_true', help='Generate full report')
    parser.add_argument('--entries', action='store_true', help='Show entry signals')
    parser.add_argument('--exits', action='store_true', help='Show exit patterns')
    parser.add_argument('--compare', action='store_true', help='Compare all models')
    
    args = parser.parse_args()
    
    analyzer = NOF1Analyzer(db_path=args.db)
    
    if args.report:
        analyzer.generate_summary_report()
    elif args.entries:
        signals = analyzer.find_entry_signals(args.model)
        print(f"\n🎯 Found {len(signals)} entry signals for {args.model}\n")
        for i, signal in enumerate(signals[:10], 1):
            print(f"Signal #{i}:")
            print(f"  Time: {signal['timestamp']}")
            print(f"  Patterns: {signal['detected_patterns']}")
            print(f"  Reasoning: {signal['reasoning_snippet'][:200]}...")
            print()
    elif args.exits:
        patterns = analyzer.find_exit_patterns(args.model)
        print(f"\n🚪 Exit Analysis for {args.model}\n")
        for key, value in patterns.items():
            if key.endswith('_count'):
                print(f"{key.replace('_', ' ').title()}: {value}")
    elif args.compare:
        comparison = analyzer.compare_models()
        print("\n📊 Model Comparison\n")
        print("Message Counts:")
        for model, count in comparison['message_counts'].items():
            print(f"  {model:25s} {count:>5d} messages")
    else:
        # Default: show basic stats
        strategy = analyzer.analyze_deepseek_strategy()
        print(f"\n📈 DeepSeek Strategy Summary")
        print(f"Messages: {strategy.get('total_messages', 0)}")
        print(f"Top phrases: {list(strategy.get('key_phrases', {}).keys())[:5]}")
        print("\nUse --report for full analysis")


if __name__ == '__main__':
    main()
