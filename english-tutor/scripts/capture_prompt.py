#!/usr/bin/env python3
"""
Capture user prompt from the most recent session message.
Runs via post_user_message hook.
"""
import json
import sys
import os
from datetime import datetime
from pathlib import Path

PROFILE_DIR = Path(__file__).parent.parent.parent
DAILY_DIR = PROFILE_DIR / "english-tutor" / "daily_prompts"
DAILY_DIR.mkdir(parents=True, exist_ok=True)

SESSION_DB = PROFILE_DIR / "state.db"
DAILY_FILE = DAILY_DIR / f"prompts_{datetime.now().strftime('%Y-%m-%d')}.jsonl"

def get_latest_user_message():
    """Get the most recent user message from the session DB."""
    import sqlite3
    try:
        conn = sqlite3.connect(SESSION_DB)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("""
            SELECT content, timestamp FROM messages
            WHERE role = 'user'
            ORDER BY id DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        conn.close()
        if row:
            return row['content'], row['timestamp']
    except Exception as e:
        print(f"DB error: {e}", file=sys.stderr)
    return None, None

def main():
    content, timestamp = get_latest_user_message()
    if not content or not content.strip():
        return 0
    
    # Skip very short messages, commands, or system messages
    content = content.strip()
    if len(content) < 5:
        return 0
    if content.startswith(('/', '!', '@', '#')):
        return 0
    
    record = {
        "timestamp": timestamp or datetime.now().isoformat(),
        "prompt": content,
        "length": len(content)
    }
    
    try:
        with open(DAILY_FILE, 'a') as f:
            f.write(json.dumps(record, ensure_ascii=False) + '\n')
    except Exception as e:
        print(f"Write error: {e}", file=sys.stderr)
        return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())