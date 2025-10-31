#!/usr/bin/env python3
"""Analyze extraction cost for different strategies"""
import sqlite3
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent
DB_PATH = PROJECT_ROOT / "collector" / "nof1_data.db"

conn = sqlite3.connect(DB_PATH)

print('=== EXTRACTION STRATEGY ANALYSIS ===\n')

# Strategy 1: Skip empty
cursor = conn.execute('''
    SELECT COUNT(*), SUM(LENGTH(reasoning))
    FROM model_chat
    WHERE LENGTH(reasoning) > 0
''')
non_empty = cursor.fetchone()
print(f'Strategy 1: Skip Empty Messages')
print(f'  Messages: {non_empty[0]:,} (from 4,425)')
print(f'  Est Cost: ${non_empty[0] * 0.018:.2f}\n')

# Strategy 2: Skip empty + tiny (<500)
cursor = conn.execute('''
    SELECT COUNT(*), SUM(LENGTH(reasoning))
    FROM model_chat
    WHERE LENGTH(reasoning) >= 500
''')
substantive = cursor.fetchone()
print(f'Strategy 2: Skip Empty + Tiny (<500 chars)')
print(f'  Messages: {substantive[0]:,} (from 4,425)')
print(f'  Est Cost: ${substantive[0] * 0.018:.2f}\n')

# Strategy 3: Priority models only
cursor = conn.execute('''
    SELECT COUNT(*), SUM(LENGTH(reasoning))
    FROM model_chat
    WHERE model_name IN ('deepseek-chat-v3.1', 'qwen3-max', 'claude-sonnet-4-5')
    AND LENGTH(reasoning) >= 500
''')
priority = cursor.fetchone()
print(f'Strategy 3: Priority Models Only (DeepSeek, QWEN3, Claude) + substantive')
print(f'  Messages: {priority[0]:,} (from 4,425)')
print(f'  Est Cost: ${priority[0] * 0.018:.2f}\n')

# Strategy 4: All models + substantive unknown-model
cursor = conn.execute('''
    SELECT COUNT(*), SUM(LENGTH(reasoning))
    FROM model_chat
    WHERE (
        model_name != 'unknown-model'
        OR (model_name = 'unknown-model' AND LENGTH(reasoning) >= 500)
    )
''')
smart_all = cursor.fetchone()
print(f'Strategy 4: All Named Models + Substantive unknown-model')
print(f'  Messages: {smart_all[0]:,} (from 4,425)')
print(f'  Est Cost: ${smart_all[0] * 0.018:.2f}\n')

# Strategy 5: All named models, skip all unknown-model
cursor = conn.execute('''
    SELECT COUNT(*), SUM(LENGTH(reasoning))
    FROM model_chat
    WHERE model_name != 'unknown-model'
''')
no_unknown = cursor.fetchone()
print(f'Strategy 5: All Named Models, Skip ALL unknown-model')
print(f'  Messages: {no_unknown[0]:,} (from 4,425)')
print(f'  Est Cost: ${no_unknown[0] * 0.018:.2f}\n')

print('=== RECOMMENDATION ===')
print('Budget: $50.00')
print('\nBest Strategy: #4 - All Named Models + Substantive unknown-model')
print('  - Processes all valuable content')
print('  - Filters only empty/tiny messages')
print('  - Within budget')
print('  - Captures unknown-model reasoning (likely misidentified models)')

conn.close()
