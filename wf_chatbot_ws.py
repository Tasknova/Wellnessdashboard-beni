"""
Tasknova — WF Intelligence Chatbot (Claude Code CLI + Pusher)
==============================================================
Listens on Pusher channel 'wf-queries' for questions, uses the
local `claude` CLI (Claude Code) for reasoning, responds on
'wf-responses-{session_id}'.

Run: python wf_chatbot_ws.py
Requires: .env with Pusher credentials. No Anthropic API key needed.
"""

import io
import json
import hashlib
import logging
import os
import queue
import sqlite3
import time
import threading
from datetime import datetime, timedelta
from pathlib import Path

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import pusher
import pysher
import requests
from dotenv import load_dotenv

# ─── Section A: Config & Data Loading ─────────────────────────────────────────

load_dotenv()

ROOT = Path(__file__).parent
DB_PATH = ROOT / 'data' / 'wf_intelligence.db'
KPI_PATH = ROOT / 'analysis' / 'kpi_metrics.json'
NARRATIVE_PATH = ROOT / 'analysis' / 'insights_narrative.md'
KB_DIR = ROOT / 'analysis'
CACHE_FILE = ROOT / 'analysis' / 'response_cache.json'
LOG_FILE = ROOT / 'analysis' / 'conversation_log.jsonl'

PUSHER_APP_ID = os.environ['PUSHER_APP_ID']
PUSHER_KEY = os.environ['PUSHER_KEY']
PUSHER_SECRET = os.environ['PUSHER_SECRET']
PUSHER_CLUSTER = os.environ.get('PUSHER_CLUSTER', 'ap2')
IMGBB_API_KEY = os.environ.get('IMGBB_API_KEY', '')

LOG_PATH = ROOT / 'analysis' / '_chatbot.log'
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%H:%M:%S',
    handlers=[
        logging.FileHandler(str(LOG_PATH), encoding='utf-8'),
        logging.StreamHandler(),
    ],
    force=True,
)
log = logging.getLogger('wf-chatbot')

# Pre-load data files
kpis = json.loads(KPI_PATH.read_text(encoding='utf-8'))
narrative = NARRATIVE_PATH.read_text(encoding='utf-8')

KB = {}
for kb_file in ['pharmacy_revenue_economics.md', 'pharmacy_supply_chain.md',
                'pharmacy_crm_customers.md', 'pharmacy_omnichannel.md',
                'pharmacy_market_landscape.md', 'pharmacy_retail_kpi_benchmarks.md']:
    path = KB_DIR / kb_file
    if path.exists():
        KB[kb_file.replace('pharmacy_', '').replace('.md', '')] = path.read_text(encoding='utf-8')
log.info(f"Loaded {len(KB)} knowledge base files, {len(kpis)} KPIs")

# ─── Section B: Utilities ─────────────────────────────────────────────────────

def query_db(sql, max_rows=50):
    """Execute a SELECT-only SQL query against wf_intelligence.db."""
    sql_stripped = sql.strip().rstrip(';')
    if not sql_stripped.upper().startswith('SELECT'):
        return {"error": "Only SELECT queries are allowed."}
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        rows = conn.execute(sql_stripped).fetchmany(max_rows)
        return [dict(r) for r in rows]
    except Exception as e:
        return {"error": str(e)}
    finally:
        conn.close()


def inr_fmt(x):
    """Format number in Indian notation (Cr/L)."""
    if abs(x) >= 1e7:
        return f'\u20b9{x/1e7:.2f} Cr'
    if abs(x) >= 1e5:
        return f'\u20b9{x/1e5:.1f} L'
    return f'\u20b9{x:,.0f}'


CACHE_TTL_HOURS = 2
SIMILARITY_THRESHOLD = 0.40  # minimum score to consider a cache hit

# Stop words excluded from similarity matching
_STOP_WORDS = frozenset(
    'what is the are of by for in on to a an and or our my me we how do does '
    'which show tell give list can could would should has have had been being '
    'this that these those it its them their there with from was were will be '
    'about all also any but each if into more most not only some than very '
    'across between where when who why please help'.split()
)

# Synonym groups — words in same group are treated as equivalent
_SYNONYM_GROUPS = [
    {'sale', 'sales', 'revenue', 'earning', 'earnings', 'income', 'turnover'},
    {'day', 'days', 'daily', 'weekday', 'weekdays', 'weekend', 'weekends'},
    {'week', 'weekly', 'month', 'monthly'},
    {'best', 'top', 'highest', 'leading', 'peak', 'maximum'},
    {'worst', 'lowest', 'bottom', 'weakest', 'minimum'},
    {'store', 'stores', 'branch', 'branches', 'outlet', 'outlets', 'location', 'locations'},
    {'product', 'products', 'sku', 'skus', 'item', 'items'},
    {'category', 'categories', 'segment', 'segments'},
    {'customer', 'customers', 'buyer', 'buyers', 'shopper', 'shoppers', 'patient', 'patients'},
    {'brand', 'brands', 'branded'},
    {'generic', 'generics'},
    {'margin', 'margins', 'profit', 'profits', 'profitability', 'profitable'},
    {'stock', 'stocks', 'inventory', 'stockout', 'stockouts', 'oos'},
    {'cancel', 'cancelled', 'cancellation', 'cancellations'},
    {'return', 'returns', 'returned'},
    {'delivery', 'deliveries', 'deliver', 'shipping', 'fulfillment', 'fulfilment'},
    {'delay', 'delays', 'delayed', 'late'},
    {'channel', 'channels', 'online', 'offline'},
    {'loyalty', 'tier', 'tiers', 'loyal'},
    {'churn', 'churned', 'attrition', 'lapsed', 'lost'},
    {'trend', 'trends', 'trending', 'pattern', 'patterns', 'performance'},
    {'demand', 'demand', 'volume', 'volumes', 'quantity'},
    {'city', 'cities', 'region', 'regions', 'area', 'areas', 'locality'},
    {'prescription', 'rx', 'medicines', 'medicine', 'drug', 'drugs', 'pharma'},
    {'wellness', 'otc', 'supplement', 'supplements'},
    {'compare', 'comparison', 'versus', 'vs'},
]

# Build lookup: word → canonical (first word in its group)
_SYNONYM_MAP = {}
for group in _SYNONYM_GROUPS:
    canonical = sorted(group)[0]  # deterministic pick
    for word in group:
        _SYNONYM_MAP[word] = canonical


def _normalize_word(w):
    """Normalize a word: apply synonym mapping and basic stemming."""
    w = _SYNONYM_MAP.get(w, w)
    # Basic suffix stripping (ing, ed, tion, ness, ly)
    if len(w) > 5:
        for suffix in ('tion', 'ness', 'ment', 'ing', 'ed', 'ly', 'er', 'est'):
            if w.endswith(suffix) and len(w) - len(suffix) >= 3:
                stem = w[:-len(suffix)]
                return _SYNONYM_MAP.get(stem, stem)
    return w


def _extract_keywords(text):
    """Extract normalized keywords from a question for similarity matching."""
    words = re.findall(r'[a-z]+', text.strip().lower())
    return set(_normalize_word(w) for w in words if w not in _STOP_WORDS and len(w) > 2)


def _similarity(kw_a, kw_b):
    """Overlap coefficient — ratio of shared keywords to the smaller set.
    Better than Jaccard for short questions where one may be more verbose."""
    if not kw_a or not kw_b:
        return 0.0
    overlap = len(kw_a & kw_b)
    return overlap / min(len(kw_a), len(kw_b))


def _cache_key(question, mode):
    return hashlib.md5(f"{mode}:{question.strip().lower()}".encode()).hexdigest()


def get_cached(question, mode):
    """Exact match only — returns cached response directly."""
    try:
        cache = json.loads(CACHE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return None

    entry = cache.get(_cache_key(question, mode))
    if entry:
        cached_at = datetime.fromisoformat(entry['cached_at'])
        if datetime.now() - cached_at <= timedelta(hours=CACHE_TTL_HOURS):
            entry['hit_count'] = entry.get('hit_count', 0) + 1
            cache[_cache_key(question, mode)] = entry
            try:
                CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding='utf-8')
            except Exception:
                pass
            log.info("Cache HIT (exact): %s", question[:60])
            return entry['response']
    return None


def find_similar_context(question, mode):
    """Find similar cached answers to use as CONTEXT (not final answer).
    Returns (prior_question, prior_answer) or (None, None)."""
    try:
        cache = json.loads(CACHE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return None, None

    q_keywords = _extract_keywords(question)
    if not q_keywords or len(q_keywords) < 2:
        return None, None

    best_score = 0.0
    best_entry = None
    best_q = None
    for key, entry in cache.items():
        if 'question' not in entry:
            continue
        cached_at = datetime.fromisoformat(entry['cached_at'])
        if datetime.now() - cached_at > timedelta(hours=CACHE_TTL_HOURS):
            continue
        cached_kw = _extract_keywords(entry['question'])
        if not cached_kw:
            continue
        score = _similarity(q_keywords, cached_kw)
        if score > best_score:
            best_score = score
            best_entry = entry
            best_q = entry['question']

    if best_score >= SIMILARITY_THRESHOLD and best_entry:
        best_entry['hit_count'] = best_entry.get('hit_count', 0) + 1
        try:
            CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding='utf-8')
        except Exception:
            pass
        log.info("Similar context found (%.0f%%): '%s' ≈ '%s'", best_score * 100, question[:40], best_q[:40])
        # Cap prior answer to avoid bloating the prompt
        prior_answer = best_entry['response'][:4000]
        return best_q, prior_answer

    return None, None


def set_cache(question, mode, response):
    try:
        cache = json.loads(CACHE_FILE.read_text(encoding='utf-8'))
    except Exception:
        cache = {}
    cache[_cache_key(question, mode)] = {
        'question': question.strip(),
        'response': response,
        'cached_at': datetime.now().isoformat(timespec='seconds'),
        'hit_count': 0,
    }
    try:
        CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass


def log_conversation(session_id, question, mode, tools_used, response_len, elapsed_ms, cached=False):
    entry = {
        'ts': datetime.now().isoformat(timespec='seconds'),
        'session_id': session_id,
        'question': question,
        'mode': mode,
        'tools_used': tools_used,
        'response_len': response_len,
        'elapsed_ms': elapsed_ms,
        'cached': cached,
    }
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass


# ─── Section C: Chart Generation ──────────────────────────────────────────────

plt.rcParams.update({
    'figure.facecolor': '#1a1a2e', 'axes.facecolor': '#16213e',
    'axes.edgecolor': '#e0e0e0', 'axes.labelcolor': '#e0e0e0',
    'text.color': '#e0e0e0', 'xtick.color': '#e0e0e0', 'ytick.color': '#e0e0e0',
    'grid.color': '#2a2a4a', 'grid.alpha': 0.3, 'font.size': 10,
})
CHART_COLORS = ['#4fc3f7', '#81c784', '#ffb74d', '#e57373', '#ba68c8',
                '#4dd0e1', '#fff176', '#a1887f', '#90a4ae', '#f48fb1']


def generate_chart(chart_type, title, labels, values, value_format='number'):
    """Render a chart and upload to imgBB. Returns {chart_url, success}."""
    try:
        fig, ax = plt.subplots(figsize=(8, 5))
        colors = CHART_COLORS[:len(labels)]

        if chart_type == 'bar':
            ax.bar(labels, values, color=colors)
            ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=9)
        elif chart_type == 'barh':
            ax.barh(labels, values, color=colors)
        elif chart_type == 'line':
            ax.plot(labels, values, color=CHART_COLORS[0], marker='o', linewidth=2)
            ax.set_xticklabels(labels, rotation=30, ha='right', fontsize=9)
        else:
            plt.close(fig)
            return {"chart_url": None, "success": False, "error": f"Unknown chart_type: {chart_type}"}

        if value_format == 'inr':
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: inr_fmt(x)))
        elif value_format == 'pct':
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(lambda x, _: f'{x:.1f}%'))

        ax.set_title(title, fontsize=13, fontweight='bold', pad=12)
        ax.grid(axis='y', alpha=0.3)
        fig.tight_layout()

        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor())
        plt.close(fig)
        buf.seek(0)

        if not IMGBB_API_KEY:
            return {"chart_url": None, "success": False, "error": "IMGBB_API_KEY not configured"}

        import base64
        b64_img = base64.b64encode(buf.getvalue()).decode()
        resp = requests.post(
            'https://api.imgbb.com/1/upload',
            data={'key': IMGBB_API_KEY, 'image': b64_img},
            timeout=15,
        )
        resp.raise_for_status()
        url = resp.json()['data']['url']
        return {"chart_url": url, "success": True}

    except Exception as e:
        plt.close('all')
        log.error(f"Chart generation failed: {e}")
        return {"chart_url": None, "success": False, "error": str(e)}


# ─── Section D: Claude CLI Integration ────────────────────────────────────────

import subprocess

# Pre-load all data from disk (generated by pre-compute step)
PRECOMPUTED_PATH = ROOT / 'analysis' / 'precomputed_data.json'
if PRECOMPUTED_PATH.exists():
    ALL_DATA = json.loads(PRECOMPUTED_PATH.read_text(encoding='utf-8'))
    log.info(f"Loaded {len(ALL_DATA)} pre-computed datasets")
else:
    ALL_DATA = {}
    log.warning("No precomputed_data.json found — will query DB on demand")


# ─── Section E: Claude CLI Question Handler ──────────────────────────────────

RELEVANCE_MAP = {
    'total_revenue': ['revenue', 'sales', 'earning', 'how much'],
    'revenue_by_category': ['category', 'revenue', 'sales'],
    'generic_vs_branded': ['generic', 'branded', 'margin'],
    'margin_by_category': ['margin', 'profit', 'category'],
    'top_brands': ['brand', 'brands'],
    'top_products': ['product', 'sku', 'seller', 'selling'],
    'stores_revenue': ['store', 'stores', 'branch', 'location', 'bleed', 'worst', 'node'],
    'stores_cancellations': ['cancel', 'bleed', 'worst', 'store'],
    'city_revenue': ['city', 'mumbai', 'pune', 'thane', 'bengaluru', 'locality'],
    'monthly_revenue': ['month', 'trend', 'growth', 'seasonal', 'monsoon'],
    'day_of_week': ['day', 'week', 'busiest', 'best day'],
    'channel_revenue': ['online', 'offline', 'channel', 'omni'],
    'payment_modes': ['payment', 'upi', 'cash', 'cod'],
    'cancel_reasons': ['cancel', 'leakage', 'return'],
    'return_reasons': ['return', 'refund', 'leakage'],
    'oos_by_store': ['stock', 'oos', 'inventory', 'stockout'],
    'delivery_stats': ['delivery', 'sla', 'delay', 'shipping'],
    'customer_stats': ['customer', 'churn', 'loyal', 'rfm'],
    'top_spenders': ['customer', 'spender', 'rfm', 'loyal'],
    'aov_by_channel': ['aov', 'basket', 'order value'],
    'inventory_health': ['inventory', 'stock', 'oos', 'overstock', 'understock', 'sku', 'assortment', 'demand'],
    'low_volume_high_margin': ['margin', 'sku', 'basket', 'strategic', 'low volume'],
    'store_category_matrix': ['store', 'category', 'node', 'fulfilment', 'assortment'],
    'oos_revenue_impact': ['stockout', 'oos', 'lost sales', 'demand'],
    'cancellation_by_category': ['cancel', 'leakage', 'category'],
    'city_category_revenue': ['city', 'locality', 'category', 'pincode'],
}

# Extra data keys to include for complex (long) questions
COMPLEX_EXTRAS = ['inventory_health', 'oos_revenue_impact', 'store_category_matrix',
                  'low_volume_high_margin', 'cancellation_by_category', 'margin_by_category',
                  'stores_revenue', 'city_category_revenue', 'generic_vs_branded',
                  'revenue_by_category', 'top_products', 'top_brands']


def _build_prompt(question, mode, prior_question=None, prior_answer=None):
    """Build the full prompt for Claude Code with DB access and optional prior context."""
    kpi_block = json.dumps(kpis, ensure_ascii=False)
    db_path = str(ROOT / 'data' / 'wf_intelligence.db').replace('\\', '/')

    # Include relevant pre-computed data as starting context
    q_lower = question.lower()
    included = set()
    data_parts = []
    for data_key, keywords in RELEVANCE_MAP.items():
        if any(kw in q_lower for kw in keywords):
            if data_key in ALL_DATA and data_key not in included:
                included.add(data_key)
                data = ALL_DATA[data_key][:10]
                data_parts.append(f"{data_key}: {json.dumps(data, ensure_ascii=False)}")
    if len(question) > 200:
        for data_key in COMPLEX_EXTRAS:
            if data_key in ALL_DATA and data_key not in included:
                included.add(data_key)
                data_parts.append(f"{data_key}: {json.dumps(ALL_DATA[data_key][:5], ensure_ascii=False)}")
    # Cap data at 6K chars
    total = 0
    capped = []
    for p in data_parts:
        if total + len(p) > 6000:
            break
        capped.append(p)
        total += len(p)
    data_block = '\n'.join(capped) if capped else 'No pre-computed data matched.'
    log.info(f"  Context: {len(included)} datasets, ~{len(data_block)} chars")

    # Prior context from similar cached answer
    prior_block = ''
    if prior_question and prior_answer:
        prior_block = f"""
PRIOR SIMILAR ANALYSIS (use as reference, adapt to the current question):
Previous question: {prior_question}
Previous answer (HTML):
{prior_answer}

Use the data and patterns from the prior analysis as a starting point. Verify key numbers by querying the database, and tailor the response to the current question.
"""
        log.info(f"  Prior context: {len(prior_answer)} chars from '{prior_question[:50]}'")

    return f"""You are Tasknova WF Intelligence Assistant for Wellness Forever (Indian pharmacy, 30 stores, 5 cities).

CRITICAL RULES:
- Your FINAL output must be ONLY raw HTML. Use <p>, <strong>, <table class="chat-table">, <ul>/<li>, <h3>. NO markdown.
- NEVER ask for permission or confirmation. Just analyze and answer directly.
- NEVER describe steps you plan to take. Just execute and present findings.
- Use ₹X.XX Cr for crores, ₹X.X L for lakhs. Include actionable insights with concrete numbers.
- You have full access to the SQLite database. Write and run Python code to query it for accurate answers.

DATABASE: {db_path}
Schema:
- stores (30 rows): store_id, store_name, city, pincode, store_type, size_sqft, online_enabled, delivery_radius_km, opened_date
- products (1K rows): product_id, product_name, brand, category, sub_type, therapeutic_area, is_generic, mrp, cost_price, margin_pct, requires_prescription, is_scheduled
- customers (5K rows): customer_id, city, pincode, gender, age, registration_date, has_rx_upload, has_subscription, preferred_store, loyalty_tier
- orders (52K rows): order_id, order_date, customer_id, store_id, channel, status, payment_mode, delivery_days, is_delayed, cancellation_reason, return_reason
- order_line_items (152K rows): line_item_id, order_id, product_id, quantity, unit_price, discount_pct, line_total, cost_amount, margin_amount
- inventory (78K rows): store_id, product_id, snapshot_date, stock_on_hand, reorder_point, is_out_of_stock, days_out_of_stock

EXAMPLE QUERIES:
SELECT SUM(li.line_total) FROM order_line_items li JOIN orders o ON li.order_id = o.order_id WHERE o.status = 'Delivered';
SELECT p.category, SUM(li.line_total) as revenue FROM order_line_items li JOIN orders o ON li.order_id = o.order_id JOIN products p ON li.product_id = p.product_id WHERE o.status = 'Delivered' GROUP BY p.category ORDER BY revenue DESC;

KPIs: {kpi_block}

PRE-COMPUTED DATA:
{data_block}
{prior_block}
---

Question: {question}
Mode: {mode}

Analyze the database by writing and executing Python code with sqlite3. Query for real numbers. Then output your final answer as ONLY raw HTML (no markdown, no ``` blocks). Use <table class="chat-table"> for all tables."""


import re

def _md_to_html(md):
    """Convert markdown to HTML for chatbot display."""
    lines = md.split('\n')
    html_parts = []
    in_table = False
    table_rows = []

    for line in lines:
        stripped = line.strip()
        if not stripped:
            if in_table and table_rows:
                html_parts.append(_build_md_table(table_rows))
                table_rows = []
                in_table = False
            continue

        # Markdown table row
        if '|' in stripped and stripped.startswith('|'):
            cells = [c.strip() for c in stripped.strip('|').split('|')]
            # Skip separator rows like |---|---|
            if all(c.replace('-', '').replace(':', '') == '' for c in cells):
                continue
            in_table = True
            table_rows.append(cells)
            continue

        if in_table and table_rows:
            html_parts.append(_build_md_table(table_rows))
            table_rows = []
            in_table = False

        # Headers
        if stripped.startswith('### '):
            html_parts.append(f'<h3>{_inline_md(stripped[4:])}</h3>')
        elif stripped.startswith('## '):
            html_parts.append(f'<h3>{_inline_md(stripped[3:])}</h3>')
        elif stripped.startswith('# '):
            html_parts.append(f'<h3>{_inline_md(stripped[2:])}</h3>')
        elif stripped.startswith('- ') or stripped.startswith('* '):
            html_parts.append(f'<li>{_inline_md(stripped[2:])}</li>')
        elif stripped.startswith('---'):
            continue  # Skip horizontal rules
        else:
            html_parts.append(f'<p>{_inline_md(stripped)}</p>')

    if in_table and table_rows:
        html_parts.append(_build_md_table(table_rows))

    return '\n'.join(html_parts)


def _inline_md(text):
    """Convert inline markdown (bold, etc.) to HTML."""
    text = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', text)
    text = re.sub(r'\*(.+?)\*', r'<em>\1</em>', text)
    text = re.sub(r'`(.+?)`', r'<code>\1</code>', text)
    return text


def _build_md_table(rows):
    """Build HTML table from parsed markdown table rows."""
    if not rows:
        return ''
    headers = rows[0]
    h = ''.join(f'<th>{_inline_md(c)}</th>' for c in headers)
    body = ''
    for row in rows[1:]:
        cells = ''.join(f'<td>{_inline_md(c)}</td>' for c in row)
        body += f'<tr>{cells}</tr>'
    return f'<table class="chat-table"><tr>{h}</tr>{body}</table>'


def run_question(session_id, question, mode='INSIGHTS'):
    """Process a question by calling Claude Code (with tool access for DB queries)."""

    # Find similar prior answer to use as context
    prior_q, prior_a = find_similar_context(question, mode)
    has_prior = prior_q is not None

    log.info(f"  Calling Claude Code (prior_context={'yes' if has_prior else 'no'})...")

    full_prompt = _build_prompt(question, mode, prior_q, prior_a)

    env = os.environ.copy()
    env.pop('CLAUDECODE', None)  # Allow nested Claude sessions
    env['PYTHONIOENCODING'] = 'utf-8'

    try:
        # Write prompt to file (avoids arg length + encoding issues on Windows)
        prompt_file = ROOT / 'analysis' / '_prompt.txt'
        prompt_file.write_text(full_prompt, encoding='utf-8')

        # Claude Code (not -p): has access to Bash, Read, Write tools for DB queries
        # --max-turns limits agentic loops, --model picks the model
        max_turns = 6 if len(question) > 100 else 3
        cmd = (f'cat analysis/_prompt.txt | claude -p '
               f'--no-session-persistence --model sonnet --max-turns {max_turns} '
               f'--allowedTools "Bash(query database:*)" "Read" "Write"')

        result = subprocess.run(
            cmd, capture_output=True, shell=True, env=env,
            timeout=240, cwd=str(ROOT),
        )
        stdout = result.stdout.decode('utf-8', errors='replace') if isinstance(result.stdout, bytes) else result.stdout
        stderr = result.stderr.decode('utf-8', errors='replace') if isinstance(result.stderr, bytes) else (result.stderr or '')

        response_html = stdout.strip()
        if not response_html:
            response_html = stderr.strip() if stderr else ''

        # Clean up markdown wrappers if Claude returns ```html blocks
        if response_html.startswith('```html'):
            response_html = response_html[7:]
        if response_html.startswith('```'):
            response_html = response_html[3:]
        if response_html.endswith('```'):
            response_html = response_html[:-3]
        response_html = response_html.strip()

        # Convert markdown to HTML if Claude returned markdown despite instructions
        if response_html and not response_html.startswith('<') and ('##' in response_html or '|' in response_html or '**' in response_html):
            response_html = _md_to_html(response_html)

        if not response_html or 'error' in response_html.lower()[:50]:
            log.warning(f"  Claude Code returned empty/error, using fallback")
            response_html = (f'<p>{narrative[:1500]}</p>'
                           f'<p><em>Try asking about: revenue, stores, products, customers, '
                           f'margins, stockouts, or delivery.</em></p>')

        tools_used = ['claude_code']
        if has_prior:
            tools_used.append('prior_context')

        return {
            'response_html': response_html,
            'chart_url': None,
            'tools_used': tools_used,
        }

    except subprocess.TimeoutExpired:
        log.error("  Claude Code timed out (240s)")
        return {
            'response_html': '<p class="chat-error">Request timed out. Please try again.</p>',
            'chart_url': None,
            'tools_used': ['timeout'],
        }
    except Exception as e:
        log.error(f"  Claude Code error: {e}")
        return {
            'response_html': f'<p class="chat-error">Error: {str(e)[:200]}</p>',
            'chart_url': None,
            'tools_used': ['error'],
        }


# ─── Section G: Pusher Connection & Message Handler ───────────────────────────

pusher_server = pusher.Pusher(
    app_id=PUSHER_APP_ID,
    key=PUSHER_KEY,
    secret=PUSHER_SECRET,
    cluster=PUSHER_CLUSTER,
    ssl=True,
)


PENDING_Q_FILE = ROOT / 'analysis' / '_pending_question.json'
PENDING_A_FILE = ROOT / 'analysis' / '_pending_answer.json'
ANSWER_TIMEOUT = 300  # seconds to wait for Claude Code to answer

# Per-session conversation history: {session_id: [{"q": ..., "a": ...}, ...]}
SESSION_HISTORY = {}
SESSION_HISTORY_MAX = 6  # keep last 6 Q&A turns per session
SESSION_HISTORY_ANSWER_CAP = 1500  # cap each prior answer to 1500 chars
PUSHER_MAX_BYTES = 9500  # Pusher limit is 10240; leave margin for JSON envelope


def _send_answer(channel, session_id, response_html, chart_url, tools_used, elapsed_ms):
    """Send answer via Pusher, chunking if it exceeds the 10KB limit."""
    payload = {
        'session_id': session_id,
        'status': 'ok',
        'response_html': response_html,
        'chart_url': chart_url,
        'tools_used': tools_used,
        'elapsed_ms': elapsed_ms,
    }
    # Check if payload fits in a single Pusher message
    payload_size = len(json.dumps(payload).encode('utf-8'))
    if payload_size <= PUSHER_MAX_BYTES:
        pusher_server.trigger(channel, 'answer', payload)
        return

    # Chunk the HTML — split into parts that fit
    overhead = payload_size - len(response_html.encode('utf-8')) + 200  # envelope + chunk fields
    chunk_size = PUSHER_MAX_BYTES - overhead
    html_bytes = response_html.encode('utf-8')
    chunks = []
    for i in range(0, len(html_bytes), chunk_size):
        chunks.append(html_bytes[i:i + chunk_size].decode('utf-8', errors='ignore'))

    total = len(chunks)
    log.info(f"[{session_id}] Response too large ({payload_size}B), sending in {total} chunks")

    for idx, chunk in enumerate(chunks):
        pusher_server.trigger(channel, 'answer_chunk', {
            'session_id': session_id,
            'status': 'ok',
            'chunk': chunk,
            'chunk_index': idx,
            'total_chunks': total,
            'chart_url': chart_url if idx == 0 else None,
            'tools_used': tools_used if idx == 0 else None,
            'elapsed_ms': elapsed_ms if idx == total - 1 else None,
        })
        time.sleep(0.1)  # small delay between chunks


QUESTION_QUEUE = queue.Queue(maxsize=20)


def enqueue_question(data):
    """Parse incoming Pusher message and add to queue (or handle instantly for cache/clear)."""
    try:
        msg = json.loads(data)
    except (json.JSONDecodeError, TypeError):
        log.error(f"Invalid message: {data}")
        return

    session_id = msg.get('session_id', 'default')
    question = msg.get('question', '').strip()
    mode = msg.get('mode', 'INSIGHTS').upper()

    if not question:
        return

    # Handle session clear request immediately (no queue needed)
    if question == '__clear_session__' or mode == 'CLEAR':
        if session_id in SESSION_HISTORY:
            del SESSION_HISTORY[session_id]
            log.info(f"[{session_id}] Session history cleared")
        return

    # Check exact cache — respond immediately without queue
    cached = get_cached(question, mode)
    if cached:
        response_channel = f'wf-responses-{session_id}'
        log.info(f"[{session_id}] Cache hit for: {question[:60]}")
        _send_answer(response_channel, session_id, cached, None, ['cache'], 0)
        log_conversation(session_id, question, mode, ['cache'], len(cached), 0, cached=True)
        if session_id not in SESSION_HISTORY:
            SESSION_HISTORY[session_id] = []
        SESSION_HISTORY[session_id].append({'q': question, 'a': cached})
        return

    # Send immediate "thinking" acknowledgment
    response_channel = f'wf-responses-{session_id}'
    try:
        qsize = QUESTION_QUEUE.qsize()
        think_msg = 'Received your question, starting analysis...'
        if qsize > 0:
            think_msg = f'Received your question (#{qsize + 1} in queue), will process shortly...'
        pusher_server.trigger(response_channel, 'thinking', {'message': think_msg})
    except Exception:
        pass

    # Add to queue
    try:
        QUESTION_QUEUE.put_nowait({
            'session_id': session_id,
            'question': question,
            'mode': mode,
            'enqueued_at': time.time(),
        })
        log.info(f"[{session_id}] Queued: {question[:80]} (mode={mode}, queue_size={QUESTION_QUEUE.qsize()})")
    except queue.Full:
        log.error(f"[{session_id}] Queue full, dropping: {question[:60]}")
        pusher_server.trigger(response_channel, 'answer', {
            'session_id': session_id, 'status': 'error',
            'response_html': '<p class="chat-error">Server is busy. Please try again in a minute.</p>',
            'chart_url': None, 'tools_used': ['queue_full'], 'elapsed_ms': 0,
        })


def process_question(item):
    """Process a single question from the queue. Runs in the worker thread."""
    session_id = item['session_id']
    question = item['question']
    mode = item['mode']
    start = item['enqueued_at']
    response_channel = f'wf-responses-{session_id}'

    log.info(f"[{session_id}] Processing: {question[:80]} (mode={mode})")

    # Find similar prior answer as context
    prior_q, prior_a = find_similar_context(question, mode)

    # Build conversation history for this session
    history = SESSION_HISTORY.get(session_id, [])
    compact_history = []
    for turn in history[-SESSION_HISTORY_MAX:]:
        compact_history.append({
            'q': turn['q'],
            'a': turn['a'][:SESSION_HISTORY_ANSWER_CAP]
        })

    # Write question for Claude Code session to pick up
    pending = {
        'session_id': session_id,
        'question': question,
        'mode': mode,
        'ts': datetime.now().isoformat(timespec='seconds'),
    }
    if compact_history:
        pending['conversation_history'] = compact_history
        log.info(f"[{session_id}] Including {len(compact_history)} prior turns as context")
    if prior_q:
        pending['prior_question'] = prior_q
        pending['prior_answer'] = prior_a

    # Clear any old answer file
    if PENDING_A_FILE.exists():
        PENDING_A_FILE.unlink()

    PENDING_Q_FILE.write_text(json.dumps(pending, indent=2, ensure_ascii=False), encoding='utf-8')
    log.info(f"[{session_id}] Question written to {PENDING_Q_FILE.name}, waiting for answer...")

    # Poll for answer file, send periodic thinking updates
    poll_start = time.time()
    last_thinking = time.time()
    thinking_msgs = [
        'Querying database...',
        'Analyzing patterns...',
        'Building insights...',
        'Running calculations...',
        'Compiling results...',
        'Formatting response...',
        'Almost done...',
    ]
    thinking_idx = 0
    while time.time() - poll_start < ANSWER_TIMEOUT:
        if time.time() - last_thinking > 15 and thinking_idx < len(thinking_msgs):
            try:
                pusher_server.trigger(response_channel, 'thinking', {
                    'message': thinking_msgs[thinking_idx]
                })
                thinking_idx += 1
                last_thinking = time.time()
            except Exception:
                pass
        if PENDING_A_FILE.exists():
            try:
                answer = json.loads(PENDING_A_FILE.read_text(encoding='utf-8'))
                PENDING_A_FILE.unlink()
                if PENDING_Q_FILE.exists():
                    PENDING_Q_FILE.unlink()

                elapsed_ms = int((time.time() - start) * 1000)
                response_html = answer.get('response_html', '')

                set_cache(question, mode, response_html)

                tools_used = answer.get('tools_used', ['claude_code'])
                log.info(f"[{session_id}] Answer received ({elapsed_ms}ms, {len(response_html)} chars)")

                _send_answer(response_channel, session_id, response_html,
                             answer.get('chart_url'), tools_used, elapsed_ms)
                log_conversation(session_id, question, mode, tools_used,
                                 len(response_html), elapsed_ms)
                if session_id not in SESSION_HISTORY:
                    SESSION_HISTORY[session_id] = []
                SESSION_HISTORY[session_id].append({'q': question, 'a': response_html})
                if len(SESSION_HISTORY[session_id]) > SESSION_HISTORY_MAX:
                    SESSION_HISTORY[session_id] = SESSION_HISTORY[session_id][-SESSION_HISTORY_MAX:]
                return
            except Exception as e:
                log.error(f"[{session_id}] Error reading answer: {e}")
                break
        time.sleep(0.5)

    # Timeout
    elapsed_ms = int((time.time() - start) * 1000)
    log.error(f"[{session_id}] Timeout waiting for answer ({elapsed_ms}ms)")
    pusher_server.trigger(response_channel, 'answer', {
        'session_id': session_id, 'status': 'error',
        'response_html': '<p class="chat-error">Request timed out. Please try again.</p>',
        'chart_url': None, 'tools_used': ['timeout'], 'elapsed_ms': elapsed_ms,
    })


def queue_worker():
    """Single worker thread that processes questions sequentially from the queue."""
    log.info("Queue worker started")
    while True:
        item = QUESTION_QUEUE.get()  # blocks until a question is available
        try:
            process_question(item)
        except Exception as e:
            log.error(f"[{item.get('session_id','?')}] Worker error: {e}")
        finally:
            QUESTION_QUEUE.task_done()


# ─── Section H: Main ──────────────────────────────────────────────────────────

def main():
    log.info("=" * 60)
    log.info("Tasknova WF Intelligence Chatbot")
    log.info(f"  DB: {DB_PATH}")
    log.info(f"  Pusher cluster: {PUSHER_CLUSTER}")
    log.info("=" * 60)

    # Start queue worker thread
    worker = threading.Thread(target=queue_worker, daemon=True)
    worker.start()

    last_event_time = [time.time()]  # mutable for closure access

    def create_client():
        client = pysher.Pusher(PUSHER_KEY, cluster=PUSHER_CLUSTER)

        def on_question(data):
            last_event_time[0] = time.time()
            enqueue_question(data)

        def on_connect(data):
            last_event_time[0] = time.time()
            log.info("Connected to Pusher")
            channel = client.subscribe('wf-queries')
            channel.bind('question', on_question)
            log.info("Subscribed to wf-queries channel — listening for questions...")

        def on_disconnect(data):
            log.warning("Pusher disconnected! Will auto-reconnect...")

        client.connection.bind('pusher:connection_established', on_connect)
        client.connection.bind('pusher:connection_closed', on_disconnect)
        client.connect()
        return client

    pysher_client = create_client()
    log.info("Waiting for Pusher connection...")

    HEARTBEAT_INTERVAL = 120  # check every 2 minutes
    STALE_THRESHOLD = 300  # reconnect if no activity for 5 minutes

    try:
        while True:
            time.sleep(HEARTBEAT_INTERVAL)
            age = time.time() - last_event_time[0]
            conn_state = getattr(pysher_client.connection, 'state', 'unknown')
            if age > STALE_THRESHOLD or conn_state not in ('connected', 'unknown'):
                log.warning(f"Connection stale ({age:.0f}s, state={conn_state}), reconnecting...")
                try:
                    pysher_client.disconnect()
                except Exception:
                    pass
                time.sleep(2)
                pysher_client = create_client()
                last_event_time[0] = time.time()
            else:
                log.debug(f"Heartbeat OK (last_event={age:.0f}s ago, state={conn_state})")
    except KeyboardInterrupt:
        log.info("\nShutting down...")
        pysher_client.disconnect()


if __name__ == '__main__':
    main()
