#!/usr/bin/env python3
"""Analyze the conversations JSON structure"""

import json
import sys

# Read the file path from command line
if len(sys.argv) < 2:
    print("Usage: python analyze_conversations.py <path_to_conversations_file>")
    sys.exit(1)

filepath = sys.argv[1]

print(f"Reading {filepath}...")

with open(filepath, 'r', encoding='utf-8') as f:
    content = f.read()

print(f"File size: {len(content):,} characters")

# Try to parse as JSON
try:
    data = json.loads(content)
    print("\n✓ Successfully parsed as JSON")
    print(f"Top-level keys: {list(data.keys())}")

    if 'conversations' in data:
        convs = data['conversations']
        print(f"\nTotal conversations: {len(convs)}")

        # Group by model
        models = {}
        for conv in convs:
            model_id = conv.get('model_id', 'unknown')
            if model_id not in models:
                models[model_id] = 0
            models[model_id] += 1

        print("\nConversations by model:")
        for model, count in sorted(models.items(), key=lambda x: -x[1]):
            print(f"  {model}: {count}")

        # Show structure of first conversation
        if len(convs) > 0:
            first = convs[0]
            print(f"\nFirst conversation structure:")
            print(f"  Keys: {list(first.keys())}")
            print(f"  ID: {first.get('id', 'N/A')}")
            print(f"  Model: {first.get('model_id', 'N/A')}")
            print(f"  Has user_prompt: {'user_prompt' in first}")
            print(f"  Has cot_trace: {'cot_trace' in first}")
            print(f"  Has llm_response: {'llm_response' in first}")

            if 'user_prompt' in first:
                print(f"  user_prompt length: {len(first['user_prompt']):,} chars")
            if 'cot_trace' in first:
                print(f"  cot_trace length: {len(first['cot_trace']):,} chars")

except json.JSONDecodeError as e:
    print(f"\n✗ JSON parse error: {e}")
    print("\nFirst 500 chars:")
    print(content[:500])
