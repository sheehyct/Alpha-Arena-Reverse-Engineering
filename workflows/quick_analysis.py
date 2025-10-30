#!/usr/bin/env python3
"""Quick analysis commands for local data"""
import sqlite3
import sys
from pathlib import Path

# Get project root and construct path to database
PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "collector" / "nof1_data.db"


def quick_stats():
    """Show quick statistics"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    print("\n=== Quick Statistics ===\n")

    # Total
    cursor.execute("SELECT COUNT(*) FROM model_chat")
    print(f"Total messages: {cursor.fetchone()[0]}")

    # By model
    cursor.execute("""
        SELECT model_name, COUNT(*) as count
        FROM model_chat
        GROUP BY model_name
        ORDER BY count DESC
    """)
    print("\nBy model:")
    for model, count in cursor.fetchall():
        print(f"  {model}: {count}")

    # Date range
    cursor.execute("SELECT MIN(timestamp), MAX(timestamp) FROM model_chat")
    first, last = cursor.fetchone()
    print(f"\nDate range:")
    print(f"  First: {first}")
    print(f"  Last: {last}")

    conn.close()


def search(keyword, limit=10):
    """Search for keyword"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, model_name, timestamp,
               SUBSTR(reasoning, 1, 200) as preview
        FROM model_chat
        WHERE reasoning LIKE ? OR raw_content LIKE ?
        ORDER BY timestamp DESC
        LIMIT ?
    """, (f"%{keyword}%", f"%{keyword}%", limit))

    results = cursor.fetchall()
    conn.close()

    print(f"\n=== Search Results for '{keyword}' ===\n")
    if not results:
        print("No results found")
        return

    for row in results:
        msg_id, model, timestamp, preview = row
        print(f"[{msg_id}] {model} - {timestamp}")
        print(f"  {preview}...")
        print()


def main():
    """Main entry point"""
    if not DB_PATH.exists():
        print(f"Error: Database not found at {DB_PATH}")
        return

    import argparse
    parser = argparse.ArgumentParser(description="Quick analysis of local data")
    parser.add_argument("--search", "-s", help="Search for keyword")
    parser.add_argument("--limit", "-l", type=int, default=10, help="Limit results")

    args = parser.parse_args()

    if args.search:
        search(args.search, args.limit)
    else:
        quick_stats()


if __name__ == "__main__":
    main()
