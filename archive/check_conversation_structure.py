import sqlite3
import json

conn = sqlite3.connect('GPT_Implementation_Proposal/collector/nof1_data.db')
cursor = conn.cursor()

# Get message 62 (claude-sonnet-4-5)
cursor.execute('SELECT raw_content FROM model_chat WHERE id = 62')
row = cursor.fetchone()

if row:
    content = row[0]
    try:
        data = json.loads(content)
        if 'conversations' in data and len(data['conversations']) > 0:
            conv = data['conversations'][0]
            print("Conversation structure for claude-sonnet-4-5:")
            print(f"All keys: {list(conv.keys())}")
            print()

            for key in conv.keys():
                value = conv[key]
                if isinstance(value, str):
                    print(f"{key}: string, length={len(value)}")
                elif isinstance(value, (list, dict)):
                    print(f"{key}: {type(value).__name__}, content={str(value)[:100]}")
                else:
                    print(f"{key}: {type(value).__name__} = {value}")
        else:
            print("No conversations found")
    except json.JSONDecodeError as e:
        print(f"JSON parse error: {e}")
        print(f"Content length: {len(content)}")
else:
    print("Message 62 not found")

conn.close()
