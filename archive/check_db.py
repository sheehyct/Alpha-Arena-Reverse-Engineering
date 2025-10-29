import sqlite3

conn = sqlite3.connect('GPT_Implementation_Proposal/collector/nof1_data.db')
cursor = conn.cursor()

# Check all messages for 'conversations' keyword
cursor.execute('SELECT id, LENGTH(raw_content), raw_content FROM model_chat')
rows = cursor.fetchall()

for msg_id, length, content in rows:
    has_conversations = 'conversations' in content
    has_user_prompt = 'user_prompt' in content
    has_chain_of_thought = 'chain_of_thought' in content

    print(f"\nMessage ID {msg_id} (length={length}):")
    print(f"  - Has 'conversations': {has_conversations}")
    print(f"  - Has 'user_prompt': {has_user_prompt}")
    print(f"  - Has 'chain_of_thought': {has_chain_of_thought}")

    if has_conversations:
        idx = content.find('"conversations"')
        print(f"\n  Sample around 'conversations':")
        print(f"  {content[max(0, idx-50):idx+800]}")
        break  # Stop after first match
    elif has_user_prompt:
        idx = content.find('"user_prompt"')
        print(f"\n  Sample around 'user_prompt':")
        print(f"  {content[max(0, idx-50):idx+500]}")

conn.close()
