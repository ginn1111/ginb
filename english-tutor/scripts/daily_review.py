#!/usr/bin/env python3
"""
Daily English tutor review at 18:00 (+07).
Reads today's prompts, generates feedback, delivers via telegram.
Then archives and clears today's file.
"""
import json
import os
import sys
import subprocess
from datetime import datetime, timezone, timedelta
from pathlib import Path

PROFILE_DIR = Path(__file__).parent.parent.parent
DAILY_DIR = PROFILE_DIR / "english-tutor" / "daily_prompts"
ARCHIVE_DIR = PROFILE_DIR / "english-tutor" / "archive"
ARCHIVE_DIR.mkdir(parents=True, exist_ok=True)

TZ = timezone(timedelta(hours=7))
TODAY = datetime.now(TZ).strftime('%Y-%m-%d')
DAILY_FILE = DAILY_DIR / f"prompts_{TODAY}.jsonl"
ARCHIVE_FILE = ARCHIVE_DIR / f"prompts_{TODAY}.jsonl"
FEEDBACK_FILE = ARCHIVE_DIR / f"feedback_{TODAY}.md"

TELEGRAM_BOT_TOKEN = os.environ.get('TELEGRAM_BOT_TOKEN')
TELEGRAM_CHAT_ID = os.environ.get('TELEGRAM_CHAT_ID')

PROMPT = """You are an English tutor for a Vietnamese speaker who wants concise, direct feedback.
User speaks Vietnamese, replies in Vietnamese. Technical terms (API, API, HTTP, DB, CI/CD, etc.) stay in English.

Review today's prompts. Give concise Vietnamese feedback:
1. **Tổng quan**: 1-2 câu tóm tắt thói quen hôm nay (ngắn gọn, trực tiếp)
2. **Lỗi thường gặp**: 2-3 lỗi hay gặp (ngữ pháp, từ vựng, cấu trúc câu) - kèm ví dụ từ prompt hôm nay
3. **Cải thiện**: 2-3 gợi ý cụ thể, có thể áp dụng ngay
4. **Từ vựng/pattern hay**: 2-3 cụm từ/cấu trúc hay dùng hôm nay

Ngắn gọn, không chào hỏi, không giải thích thừa. Tiếng Việt tự nhiên, thuật ngữ tech giữ nguyên tiếng Anh."""

def load_prompts():
    if not DAILY_FILE.exists():
        return []
    prompts = []
    with open(DAILY_FILE) as f:
        for line in f:
            line = line.strip()
            if line:
                try:
                    prompts.append(json.loads(line))
                except json.JSONDecodeError:
                    pass
    return prompts

def generate_feedback(prompts):
    if not prompts:
        return "Hôm nay không có prompt nào được ghi nhận."
    
    prompt_texts = [p['prompt'] for p in prompts]
    combined = "\n---\n".join(prompt_texts)
    
    # Use hermes to generate feedback
    prompt = f"{PROMPT}\n\n--- PROMPTS HÔM NAY ({len(prompts)} câu) ---\n{combined}\n\n--- PHẢN HỒI ---"
    
    try:
        result = subprocess.run(
            ['hermes', 'chat', '-q', prompt, '-Q', '-m', 'aux'],
            capture_output=True, text=True, timeout=120, cwd=str(PROFILE_DIR)
        )
        if result.returncode == 0:
            return result.stdout.strip()
        else:
            return f"Lỗi tạo phản hồi: {result.stderr}"
    except subprocess.TimeoutExpired:
        return "Timeout khi tạo phản hồi."
    except Exception as e:
        return f"Lỗi: {e}"

def send_telegram(message):
    if not TELEGRAM_BOT_TOKEN or not TELEGRAM_CHAT_ID:
        print("Telegram not configured", file=sys.stderr)
        return False
    try:
        import requests
        url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
        data = {'chat_id': TELEGRAM_CHAT_ID, 'text': message, 'parse_mode': 'Markdown'}
        resp = requests.post(url, json=data, timeout=10)
        return resp.status_code == 200
    except Exception as e:
        print(f"Telegram error: {e}", file=sys.stderr)
        return False

def archive_and_cleanup():
    if DAILY_FILE.exists():
        DAILY_FILE.rename(ARCHIVE_FILE)
    # Clean up daily file if archive failed
    if DAILY_FILE.exists():
        DAILY_FILE.unlink()

def main():
    prompts = load_prompts()
    feedback = generate_feedback(prompts)
    
    # Save feedback for reference
    with open(FEEDBACK_FILE, 'w') as f:
        f.write(f"# English Tutor Feedback - {TODAY}\n\n")
        f.write(f"Số prompt: {len(prompts)}\n\n")
        f.write(feedback)
    
    # Send via telegram
    header = f"📚 *English Tutor - {TODAY}* ({len(prompts)} prompts)\n\n"
    message = header + feedback
    if len(message) > 4000:
        message = message[:3997] + "..."
    send_telegram(message)
    
    # Archive and cleanup
    archive_and_cleanup()
    return 0

if __name__ == '__main__':
    sys.exit(main())