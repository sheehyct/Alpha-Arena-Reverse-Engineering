#!/usr/bin/env python3
"""
NOF1.AI Alpha Arena - Continuous ModelChat Scraper
Automatically scrapes DeepSeek and other AI model reasoning every 2-3 minutes
Stores data locally in SQLite with duplicate detection
"""

import time
import sqlite3
import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import logging

# Try importing Playwright (preferred for JS-heavy sites)
try:
    from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
    PLAYWRIGHT_AVAILABLE = True
except ImportError:
    PLAYWRIGHT_AVAILABLE = False
    print("⚠️  Playwright not installed. Install with: pip install playwright && playwright install chromium")

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s',
    handlers=[
        logging.FileHandler('nof1_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class NOF1Scraper:
    """Continuous scraper for NOF1.AI ModelChat data"""
    
    def __init__(self, db_path: str = "nof1_data.db", check_interval: int = 150):
        """
        Initialize scraper
        
        Args:
            db_path: Path to SQLite database
            check_interval: Seconds between checks (default 150 = 2.5 minutes)
        """
        self.db_path = db_path
        self.check_interval = check_interval
        self.init_database()
        
        # Model URLs to scrape
        self.models = {
            'deepseek-v3.1': 'https://nof1.ai/models/deepseek-chat-v3.1',
            'qwen3-max': 'https://nof1.ai/models/qwen3-max',
            'claude-sonnet-4.5': 'https://nof1.ai/models/claude-sonnet-4.5',
            'grok-4': 'https://nof1.ai/models/grok-4',
            'gpt-5': 'https://nof1.ai/models/gpt-5',
            'gemini-2.5-pro': 'https://nof1.ai/models/gemini-2.5-pro'
        }
        
    def init_database(self):
        """Create SQLite database schema"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Main messages table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_chat (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_name TEXT NOT NULL,
                timestamp TEXT NOT NULL,
                message_hash TEXT UNIQUE NOT NULL,
                reasoning TEXT,
                action TEXT,
                confidence REAL,
                positions TEXT,
                market_data TEXT,
                raw_content TEXT,
                scraped_at TEXT NOT NULL,
                UNIQUE(model_name, message_hash)
            )
        ''')
        
        # Scraper metadata
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS scraper_runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_timestamp TEXT NOT NULL,
                models_checked INTEGER,
                new_messages INTEGER,
                errors TEXT
            )
        ''')
        
        # Create indexes
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_model_time ON model_chat(model_name, timestamp)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_hash ON model_chat(message_hash)')
        
        conn.commit()
        conn.close()
        logger.info(f"✓ Database initialized: {self.db_path}")
    
    def hash_message(self, content: str) -> str:
        """Create hash for duplicate detection"""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def message_exists(self, message_hash: str) -> bool:
        """Check if message already scraped"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT 1 FROM model_chat WHERE message_hash = ?', (message_hash,))
        exists = cursor.fetchone() is not None
        conn.close()
        return exists
    
    def save_message(self, model_name: str, data: Dict):
        """Save message to database if new"""
        message_hash = self.hash_message(data['raw_content'])
        
        if self.message_exists(message_hash):
            return False  # Already exists
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            cursor.execute('''
                INSERT INTO model_chat 
                (model_name, timestamp, message_hash, reasoning, action, 
                 confidence, positions, market_data, raw_content, scraped_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                model_name,
                data.get('timestamp', datetime.now().isoformat()),
                message_hash,
                data.get('reasoning'),
                data.get('action'),
                data.get('confidence'),
                json.dumps(data.get('positions', [])),
                json.dumps(data.get('market_data', {})),
                data['raw_content'],
                datetime.now().isoformat()
            ))
            conn.commit()
            conn.close()
            return True  # New message saved
        except sqlite3.IntegrityError:
            conn.close()
            return False  # Duplicate
    
    def scrape_model_page(self, model_name: str, url: str, page) -> List[Dict]:
        """Scrape ModelChat from a single model page"""
        try:
            logger.info(f"  → Navigating to {model_name}...")
            page.goto(url, wait_until='networkidle', timeout=30000)
            
            # Wait for chat container to load
            page.wait_for_selector('[class*="chat"]', timeout=10000)
            
            # Extract all chat messages
            # Note: Actual selectors need to be updated based on real DOM structure
            messages = []
            
            # Try different possible selectors for chat messages
            selectors = [
                '.model-chat-message',
                '[data-testid="chat-message"]',
                '.chat-message',
                '[class*="message"]'
            ]
            
            for selector in selectors:
                try:
                    elements = page.query_selector_all(selector)
                    if elements:
                        logger.info(f"    Found {len(elements)} messages with selector: {selector}")
                        for elem in elements:
                            text = elem.inner_text()
                            if text.strip():
                                messages.append({
                                    'raw_content': text,
                                    'timestamp': datetime.now().isoformat(),
                                    'reasoning': text  # Parse this more intelligently later
                                })
                        break
                except Exception as e:
                    continue
            
            if not messages:
                # Fallback: grab all visible text in main content area
                logger.warning(f"    No messages found with standard selectors, trying fallback...")
                try:
                    main_content = page.query_selector('main') or page.query_selector('body')
                    if main_content:
                        text = main_content.inner_text()
                        # Split by common delimiters
                        chunks = [t.strip() for t in text.split('\n\n') if len(t.strip()) > 50]
                        messages = [{'raw_content': chunk, 'timestamp': datetime.now().isoformat()} 
                                   for chunk in chunks[:10]]  # Limit to recent
                except Exception as e:
                    logger.error(f"    Fallback extraction failed: {e}")
            
            return messages
            
        except PlaywrightTimeout:
            logger.error(f"  ✗ Timeout loading {model_name}")
            return []
        except Exception as e:
            logger.error(f"  ✗ Error scraping {model_name}: {e}")
            return []
    
    def run_scrape_cycle(self, playwright):
        """Run one complete scrape cycle for all models"""
        logger.info("=" * 60)
        logger.info("🔄 Starting scrape cycle...")
        
        browser = playwright.chromium.launch(headless=True)
        context = browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        )
        page = context.new_page()
        
        new_messages_total = 0
        errors = []
        
        for model_name, url in self.models.items():
            try:
                messages = self.scrape_model_page(model_name, url, page)
                new_count = 0
                
                for msg in messages:
                    if self.save_message(model_name, msg):
                        new_count += 1
                
                if new_count > 0:
                    logger.info(f"  ✓ {model_name}: {new_count} new messages")
                else:
                    logger.info(f"  ○ {model_name}: No new messages")
                
                new_messages_total += new_count
                
            except Exception as e:
                error_msg = f"{model_name}: {str(e)}"
                errors.append(error_msg)
                logger.error(f"  ✗ {error_msg}")
        
        browser.close()
        
        # Log scraper run
        self.log_scraper_run(len(self.models), new_messages_total, errors)
        
        logger.info(f"✓ Cycle complete: {new_messages_total} new messages scraped")
        return new_messages_total
    
    def log_scraper_run(self, models_checked: int, new_messages: int, errors: List[str]):
        """Log scraper run to database"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('''
            INSERT INTO scraper_runs (run_timestamp, models_checked, new_messages, errors)
            VALUES (?, ?, ?, ?)
        ''', (
            datetime.now().isoformat(),
            models_checked,
            new_messages,
            json.dumps(errors) if errors else None
        ))
        conn.commit()
        conn.close()
    
    def run_continuous(self):
        """Main loop - run scraper continuously"""
        if not PLAYWRIGHT_AVAILABLE:
            logger.error("❌ Cannot run: Playwright not installed")
            logger.error("   Install with: pip install playwright && playwright install chromium")
            return
        
        logger.info("🚀 NOF1.AI Continuous Scraper Started")
        logger.info(f"   Database: {self.db_path}")
        logger.info(f"   Check interval: {self.check_interval}s ({self.check_interval/60:.1f} min)")
        logger.info(f"   Models: {', '.join(self.models.keys())}")
        logger.info("   Press Ctrl+C to stop")
        logger.info("")
        
        cycle_count = 0
        
        with sync_playwright() as playwright:
            while True:
                try:
                    cycle_count += 1
                    logger.info(f"Cycle #{cycle_count}")
                    
                    self.run_scrape_cycle(playwright)
                    
                    logger.info(f"😴 Sleeping for {self.check_interval}s...")
                    logger.info("")
                    time.sleep(self.check_interval)
                    
                except KeyboardInterrupt:
                    logger.info("\n⏹️  Scraper stopped by user")
                    break
                except Exception as e:
                    logger.error(f"❌ Unexpected error in main loop: {e}")
                    logger.info("   Waiting 60s before retry...")
                    time.sleep(60)
    
    def export_to_csv(self, output_file: str = "nof1_data.csv"):
        """Export all scraped data to CSV"""
        import csv
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM model_chat ORDER BY scraped_at DESC')
        
        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]
        
        with open(output_file, 'w', newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(columns)
            writer.writerows(rows)
        
        conn.close()
        logger.info(f"✓ Exported {len(rows)} messages to {output_file}")
    
    def get_stats(self) -> Dict:
        """Get scraping statistics"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute('SELECT COUNT(*) FROM model_chat')
        total_messages = cursor.fetchone()[0]
        
        cursor.execute('SELECT model_name, COUNT(*) FROM model_chat GROUP BY model_name')
        by_model = dict(cursor.fetchall())
        
        cursor.execute('SELECT COUNT(*) FROM scraper_runs')
        total_runs = cursor.fetchone()[0]
        
        cursor.execute('SELECT MIN(scraped_at), MAX(scraped_at) FROM model_chat')
        date_range = cursor.fetchone()
        
        conn.close()
        
        return {
            'total_messages': total_messages,
            'by_model': by_model,
            'total_scraper_runs': total_runs,
            'first_message': date_range[0],
            'last_message': date_range[1]
        }


def main():
    """Main entry point"""
    import argparse
    
    parser = argparse.ArgumentParser(description='NOF1.AI Alpha Arena Continuous Scraper')
    parser.add_argument('--db', default='nof1_data.db', help='Database file path')
    parser.add_argument('--interval', type=int, default=150, 
                       help='Check interval in seconds (default: 150 = 2.5 min)')
    parser.add_argument('--export', action='store_true', 
                       help='Export database to CSV and exit')
    parser.add_argument('--stats', action='store_true', 
                       help='Show statistics and exit')
    
    args = parser.parse_args()
    
    scraper = NOF1Scraper(db_path=args.db, check_interval=args.interval)
    
    if args.export:
        scraper.export_to_csv()
    elif args.stats:
        stats = scraper.get_stats()
        print("\n📊 Scraper Statistics")
        print("=" * 40)
        print(f"Total messages: {stats['total_messages']}")
        print(f"Total scraper runs: {stats['total_scraper_runs']}")
        print(f"\nMessages by model:")
        for model, count in stats['by_model'].items():
            print(f"  {model}: {count}")
        print(f"\nDate range:")
        print(f"  First: {stats['first_message']}")
        print(f"  Last:  {stats['last_message']}")
    else:
        scraper.run_continuous()


if __name__ == '__main__':
    main()
