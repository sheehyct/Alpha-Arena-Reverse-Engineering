#!/usr/bin/env python3
"""Verify that extraction logic is working correctly"""

import sqlite3
import sys
from pathlib import Path

def verify_extraction():
    db_path = Path("GPT_Implementation_Proposal/collector/nof1_data.db")

    if not db_path.exists():
        print(f"Database not found: {db_path}")
        return

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Get the 3 most recent messages
    cursor.execute("""
        SELECT id, model_name, timestamp,
               LENGTH(raw_content) as raw_len,
               LENGTH(reasoning) as reasoning_len,
               reasoning
        FROM model_chat
        ORDER BY id DESC
        LIMIT 3
    """)

    rows = cursor.fetchall()

    if not rows:
        print("No messages found in database")
        return

    print("="*80)
    print("EXTRACTION VERIFICATION - Latest 3 Messages")
    print("="*80)

    for row in rows:
        msg_id, model_name, timestamp, raw_len, reasoning_len, reasoning = row

        print(f"\nMessage ID {msg_id}:")
        print(f"  Model: {model_name}")
        print(f"  Timestamp: {timestamp}")
        print(f"  Raw content length: {raw_len:,} chars")
        print(f"  Extracted reasoning length: {reasoning_len:,} chars")
        print()

        # Check for sections
        has_user_prompt = "USER_PROMPT:" in reasoning if reasoning else False
        has_cot = "CHAIN_OF_THOUGHT:" in reasoning if reasoning else False
        has_decisions = "TRADING_DECISIONS:" in reasoning if reasoning else False

        print(f"  Extracted sections:")
        print(f"    USER_PROMPT: {'YES' if has_user_prompt else 'NO'}")
        print(f"    CHAIN_OF_THOUGHT: {'YES' if has_cot else 'NO'}")
        print(f"    TRADING_DECISIONS: {'YES' if has_decisions else 'NO'}")

        if reasoning and reasoning_len > 100:
            print(f"\n  First 800 chars of extracted reasoning:")
            print(f"  {'-'*76}")
            print(f"  {reasoning[:800]}")
            print(f"  {'-'*76}")
        else:
            print(f"\n  WARNING: Reasoning field is empty or too short!")

        print("\n" + "="*80)

    conn.close()

if __name__ == "__main__":
    verify_extraction()
