import sqlite3
import json

conn = sqlite3.connect('GPT_Implementation_Proposal/collector/nof1_data.db')
cursor = conn.cursor()

# Get message 4 which has conversations
cursor.execute('SELECT raw_content FROM model_chat WHERE id = 4')
row = cursor.fetchone()
content = row[0]

# Try to parse as JSON
try:
    data = json.loads(content)
    print("Successfully parsed as JSON")
    print(f"Top-level keys: {list(data.keys())}")

    if 'conversations' in data:
        print(f"\nNumber of conversations: {len(data['conversations'])}")
        conv = data['conversations'][0]
        print(f"\nFirst conversation keys: {list(conv.keys())}")
        print(f"Conversation ID: {conv.get('id', 'N/A')}")
        print(f"Has user_prompt: {'user_prompt' in conv}")
        print(f"Has chain_of_thought: {'chain_of_thought' in conv}")
        print(f"Has trading_decisions: {'trading_decisions' in conv}")

        if 'user_prompt' in conv:
            print(f"\nuser_prompt length: {len(conv['user_prompt'])} chars")
        if 'chain_of_thought' in conv:
            print(f"chain_of_thought length: {len(conv['chain_of_thought'])} chars")
        if 'trading_decisions' in conv:
            print(f"trading_decisions type: {type(conv['trading_decisions'])}")

except json.JSONDecodeError as e:
    print(f"Failed to parse as JSON: {e}")
    print(f"Content starts with: {content[:200]}")

conn.close()
