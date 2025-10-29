"""
Show recent messages captured in the database.

Usage:
    uv run python workflows/show_recent_messages.py [--limit N]

Options:
    --limit N    Number of messages to show (default: 10)
"""

import sqlite3
import sys
from pathlib import Path

def show_recent_messages(limit=10):
    """Display the most recent messages with ID, model name, and timestamp."""

    # Get project root directory
    project_root = Path(__file__).parent.parent
    db_path = project_root / "collector" / "nof1_data.db"

    if not db_path.exists():
        print(f"Error: Database not found at {db_path}")
        print("Make sure the collector has been run at least once.")
        return

    # Connect to database
    conn = sqlite3.connect(str(db_path))
    cursor = conn.cursor()

    # Get recent messages
    cursor.execute('''
        SELECT id, model_name, timestamp
        FROM model_chat
        ORDER BY id DESC
        LIMIT ?
    ''', (limit,))

    rows = cursor.fetchall()
    conn.close()

    if not rows:
        print("No messages found in database.")
        return

    # Display results
    print(f"\nLatest {len(rows)} Messages:")
    print("-" * 70)

    for row in rows:
        message_id = row[0]
        model_name = row[1]
        timestamp = row[2]
        print(f"  ID {message_id}: {model_name} ({timestamp})")

    print("-" * 70)
    print(f"\nTotal messages shown: {len(rows)}")
    print(f"\nTo export a specific message:")
    print(f"  uv run python archive/export_message.py <message_id>")

if __name__ == "__main__":
    # Parse command line arguments
    limit = 10

    if len(sys.argv) > 1:
        if sys.argv[1] in ["-h", "--help"]:
            print(__doc__)
            sys.exit(0)

        if sys.argv[1] == "--limit" and len(sys.argv) > 2:
            try:
                limit = int(sys.argv[2])
            except ValueError:
                print("Error: --limit must be followed by a number")
                sys.exit(1)

    show_recent_messages(limit)
