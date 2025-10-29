#!/usr/bin/env python3
"""
NOF1.AI Real-Time Monitor - Live dashboard for scraping activity
Shows latest messages and statistics as they're scraped
"""

import sqlite3
import time
import os
from datetime import datetime, timedelta
from typing import Dict, List


class NOF1Monitor:
    """Real-time monitoring dashboard for scraper"""
    
    def __init__(self, db_path: str = "nof1_data.db", refresh_interval: int = 10):
        self.db_path = db_path
        self.refresh_interval = refresh_interval
        
    def clear_screen(self):
        """Clear terminal screen"""
        os.system('cls' if os.name == 'nt' else 'clear')
    
    def get_recent_activity(self, minutes: int = 30) -> List[Dict]:
        """Get messages from last N minutes"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cutoff = (datetime.now() - timedelta(minutes=minutes)).isoformat()
        
        cursor.execute('''
            SELECT model_name, timestamp, scraped_at, 
                   SUBSTR(raw_content, 1, 150) as snippet
            FROM model_chat 
            WHERE scraped_at > ?
            ORDER BY scraped_at DESC
            LIMIT 20
        ''', (cutoff,))
        
        columns = ['model_name', 'timestamp', 'scraped_at', 'snippet']
        messages = [dict(zip(columns, row)) for row in cursor.fetchall()]
        
        conn.close()
        return messages
    
    def get_stats_summary(self) -> Dict:
        """Get overall statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Total messages
        cursor.execute('SELECT COUNT(*) FROM model_chat')
        total = cursor.fetchone()[0]
        
        # By model
        cursor.execute('''
            SELECT model_name, COUNT(*) 
            FROM model_chat 
            GROUP BY model_name 
            ORDER BY COUNT(*) DESC
        ''')
        by_model = dict(cursor.fetchall())
        
        # Recent activity (last hour)
        one_hour_ago = (datetime.now() - timedelta(hours=1)).isoformat()
        cursor.execute('''
            SELECT COUNT(*) FROM model_chat WHERE scraped_at > ?
        ''', (one_hour_ago,))
        recent_count = cursor.fetchone()[0]
        
        # Last scraper run
        cursor.execute('''
            SELECT run_timestamp, new_messages 
            FROM scraper_runs 
            ORDER BY id DESC 
            LIMIT 1
        ''')
        last_run = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_messages': total,
            'by_model': by_model,
            'recent_hour': recent_count,
            'last_run': last_run
        }
    
    def format_time_ago(self, timestamp: str) -> str:
        """Format timestamp as 'X minutes ago'"""
        try:
            dt = datetime.fromisoformat(timestamp)
            delta = datetime.now() - dt
            
            if delta.total_seconds() < 60:
                return f"{int(delta.total_seconds())}s ago"
            elif delta.total_seconds() < 3600:
                return f"{int(delta.total_seconds() / 60)}m ago"
            elif delta.total_seconds() < 86400:
                return f"{int(delta.total_seconds() / 3600)}h ago"
            else:
                return f"{int(delta.total_seconds() / 86400)}d ago"
        except:
            return timestamp
    
    def display_dashboard(self):
        """Display the monitoring dashboard"""
        self.clear_screen()
        
        print("┏" + "━" * 78 + "┓")
        print("┃" + " " * 20 + "NOF1.AI SCRAPER - LIVE MONITOR" + " " * 27 + "┃")
        print("┗" + "━" * 78 + "┛")
        print()
        
        # Get data
        stats = self.get_stats_summary()
        recent = self.get_recent_activity(minutes=30)
        
        # Display stats
        print("📊 OVERALL STATISTICS")
        print("─" * 80)
        print(f"  Total Messages:     {stats['total_messages']:,}")
        print(f"  Last Hour:          {stats['recent_hour']} new messages")
        
        if stats['last_run']:
            run_time, new_msgs = stats['last_run']
            print(f"  Last Scrape:        {self.format_time_ago(run_time)} ({new_msgs} new)")
        
        print()
        print("  Messages by Model:")
        for model, count in stats['by_model'].items():
            bar_length = int((count / stats['total_messages']) * 30)
            bar = "█" * bar_length + "░" * (30 - bar_length)
            print(f"    {model:20s} {bar} {count:>4d}")
        
        print()
        print("🔴 RECENT ACTIVITY (Last 30 minutes)")
        print("─" * 80)
        
        if recent:
            for msg in recent[:10]:
                time_ago = self.format_time_ago(msg['scraped_at'])
                model = msg['model_name'][:15].ljust(15)
                snippet = msg['snippet'].replace('\n', ' ')[:45]
                
                print(f"  [{time_ago:>8s}] {model} │ {snippet}...")
        else:
            print("  No recent activity")
        
        print()
        print("─" * 80)
        print(f"  Refreshing every {self.refresh_interval}s | Press Ctrl+C to exit")
        print(f"  Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    def run(self):
        """Run continuous monitoring"""
        print("🚀 Starting NOF1.AI Monitor...")
        print(f"   Database: {self.db_path}")
        print(f"   Refresh: {self.refresh_interval}s")
        print()
        print("   Press Ctrl+C to exit")
        time.sleep(2)
        
        try:
            while True:
                self.display_dashboard()
                time.sleep(self.refresh_interval)
        except KeyboardInterrupt:
            print("\n\n⏹️  Monitor stopped")
    
    def tail_messages(self, count: int = 20):
        """Show last N messages (like tail -f)"""
        print(f"📜 Last {count} messages:\n")
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT model_name, scraped_at, raw_content
            FROM model_chat 
            ORDER BY scraped_at DESC 
            LIMIT ?
        ''', (count,))
        
        for row in cursor.fetchall():
            model, timestamp, content = row
            print(f"┌─ {model} @ {self.format_time_ago(timestamp)}")
            print(f"│  {content[:200].replace(chr(10), ' ')}...")
            print(f"└─")
            print()
        
        conn.close()


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NOF1.AI Real-Time Monitor')
    parser.add_argument('--db', default='nof1_data.db', help='Database file path')
    parser.add_argument('--refresh', type=int, default=10, 
                       help='Refresh interval in seconds (default: 10)')
    parser.add_argument('--tail', type=int, 
                       help='Show last N messages and exit')
    
    args = parser.parse_args()
    
    monitor = NOF1Monitor(db_path=args.db, refresh_interval=args.refresh)
    
    if args.tail:
        monitor.tail_messages(count=args.tail)
    else:
        monitor.run()


if __name__ == '__main__':
    main()
