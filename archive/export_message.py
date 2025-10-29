#!/usr/bin/env python3
"""Export a specific message's extracted content to a file"""

import sqlite3
import sys

def export_message(msg_id):
    conn = sqlite3.connect('GPT_Implementation_Proposal/collector/nof1_data.db')
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, model_name, timestamp, reasoning
        FROM model_chat
        WHERE id = ?
    """, (msg_id,))

    row = cursor.fetchone()

    if not row:
        print(f"Message ID {msg_id} not found")
        return

    msg_id, model_name, timestamp, reasoning = row

    output_file = f"extracted_message_{msg_id}.txt"

    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(f"Message ID: {msg_id}\n")
        f.write(f"Model: {model_name}\n")
        f.write(f"Timestamp: {timestamp}\n")
        f.write(f"Extracted Reasoning Length: {len(reasoning):,} chars\n")
        f.write("="*80 + "\n\n")
        f.write(reasoning)

    print(f"Extracted content saved to: {output_file}")
    print(f"Length: {len(reasoning):,} characters")

    conn.close()

if __name__ == "__main__":
    msg_id = int(sys.argv[1]) if len(sys.argv) > 1 else 174
    export_message(msg_id)
