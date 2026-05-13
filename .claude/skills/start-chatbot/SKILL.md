---
name: start-chatbot
description: Start the WF Intelligence Chatbot backend and begin monitoring for incoming questions
disable-model-invocation: true
user-invocable: true
allowed-tools: Bash(python wf_chatbot_ws.py) Bash(python -c *) Read Write
argument-hint:
---

## WF Intelligence Chatbot — Startup & Monitor

You are the answering brain behind the WF chatbot. The chatbot backend (`wf_chatbot_ws.py`) listens on Pusher for questions and writes them to `analysis/_pending_question.json`. **YOUR job is to read those questions, generate answers, and write them to `analysis/_pending_answer.json`.**

### Step 1: Refresh expired cache entries

The cache (`analysis/response_cache.json`) has a 2-hour TTL. On startup, refresh all timestamps so cached answers work immediately:

```python
python -c "
import json
from datetime import datetime
c = json.load(open('analysis/response_cache.json','r',encoding='utf-8'))
for v in c.values():
    v['cached_at'] = datetime.now().isoformat(timespec='seconds')
json.dump(c, open('analysis/response_cache.json','w',encoding='utf-8'), indent=2, ensure_ascii=False)
print(f'Refreshed {len(c)} cache entries')
"
```

### Step 2: Start the chatbot backend

Run `python wf_chatbot_ws.py` **in the background**. Verify it connects to Pusher by checking for "Subscribed to wf-queries channel" in the output.

### Step 3: Monitor for pending questions

After the server is running, **poll `analysis/_pending_question.json` every 10 seconds**. When a question appears:

1. Read `analysis/_pending_question.json` to get the question, session_id, and mode
2. Look up the answer:
   - **First**: Check `analysis/kpi_metrics.json` and `analysis/insights_narrative.md`
   - **Then**: Query `data/wf_intelligence.db` with SQL if needed (see CLAUDE.md for schema)
   - **Use**: `analysis/precomputed_data.json` for pre-computed datasets
3. Format the answer as **inline HTML** (styled `<div>`, `<table>`, `<p>` — no markdown)
4. Write the answer to `analysis/_pending_answer.json`:

```json
{
  "response_html": "<div class=\"analysis-response\">...</div>",
  "chart_url": null,
  "tools_used": ["claude_session"]
}
```

### HTML formatting rules

- Wrap in `<div class="analysis-response">`
- Use inline styles (the frontend has no stylesheet for your content)
- Header color: `#1a1a2e`, accent: `#1e8449` for good metrics, `#c0392b` for bad
- Indian currency: ₹ with Cr (crore = 10M) and L (lakh = 100K)
- Tables: `border-collapse:collapse`, alternating rows, right-align numbers
- Keep responses concise — 500-2000 chars typical

### Monitoring loop pattern

```bash
while true; do
  if [ -f analysis/_pending_question.json ]; then
    # read and process
  fi
  sleep 10
done
```

Or use Python with `time.sleep(10)` and `Path.exists()`.

**IMPORTANT**: Do NOT wait for the user to tell you a question came in. Proactively monitor and answer. That is the entire point of this skill.
