"""
Tasknova — Chatbot File Watcher
================================
Polls chatbot_query.txt. When a question arrives, prints it and exits.
Designed to be re-launched by the Claude Code session after each answer.

Run: python _wf_chatbot_watcher.py
"""

import time
from pathlib import Path

QUERY_FILE = Path(__file__).parent / 'chatbot_query.txt'
POLL_INTERVAL = 2

while True:
    if QUERY_FILE.exists():
        question = QUERY_FILE.read_text(encoding='utf-8').strip()
        if question:
            QUERY_FILE.unlink()
            print(question)
            break
    time.sleep(POLL_INTERVAL)
