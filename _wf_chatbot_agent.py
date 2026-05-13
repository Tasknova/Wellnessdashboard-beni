"""
Tasknova — WF Chatbot Agent
==============================
Polls chatbot_query.txt for questions, answers them using
pre-computed insights, SQLite, and industry knowledge base.
Outputs rich HTML responses with tables and charts.

Run: python _wf_chatbot_agent.py
"""

import json
import re
import sqlite3
import time
import io
import base64
from pathlib import Path
from datetime import datetime, timedelta

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker

try:
    import ollama as ollama_client
    import numpy as np
    OLLAMA_AVAILABLE = True
except ImportError:
    OLLAMA_AVAILABLE = False
    print("  [warn] ollama/numpy not installed — using regex routing only")

ROOT = Path(__file__).parent
DB_PATH = ROOT / 'data' / 'wf_intelligence.db'
KPI_PATH = ROOT / 'analysis' / 'kpi_metrics.json'
NARRATIVE_PATH = ROOT / 'analysis' / 'insights_narrative.md'
QUERY_FILE = ROOT / 'chatbot_query.txt'
RESPONSE_FILE = ROOT / 'chatbot_response.txt'
KB_DIR = ROOT / 'analysis'
EMBED_CACHE_PATH = ROOT / '_embed_cache.json'

# Global intent embeddings index
_intent_index = None  # {'handlers': [...], 'embeddings': np.array}

POLL_INTERVAL = 2  # seconds

# === SESSION CONTEXT (follow-up resolution) ===
_session_context = {'last_question': None, 'last_handler': None, 'last_entities': {}}

FOLLOWUP_SIGNALS = re.compile(
    r'^(and |but |what about |how about |based on |by |show me |'
    r'in |for |with |same |also |versus |vs |compared|'
    r'now |ok |okay |how |what |which |why )\b', re.IGNORECASE)


def is_followup(question):
    """Detect if a question is a follow-up to the previous one."""
    if not _session_context['last_handler']:
        return False
    q = question.strip()
    if len(q.split()) <= 8 and FOLLOWUP_SIGNALS.search(q):
        return True
    if len(q.split()) <= 3:
        return True
    return False

# Load pre-computed data
with open(KPI_PATH, 'r', encoding='utf-8') as f:
    kpis = json.load(f)

narrative = NARRATIVE_PATH.read_text(encoding='utf-8')

# Load industry knowledge base snippets for benchmark context
KB = {}
for kb_file in ['pharmacy_revenue_economics.md', 'pharmacy_supply_chain.md',
                 'pharmacy_crm_customers.md', 'pharmacy_omnichannel.md',
                 'pharmacy_market_landscape.md', 'pharmacy_retail_kpi_benchmarks.md']:
    path = KB_DIR / kb_file
    if path.exists():
        KB[kb_file.replace('pharmacy_', '').replace('.md', '')] = path.read_text(encoding='utf-8')
print(f"  Loaded {len(KB)} knowledge base files")


# === EMBEDDING-BASED INTENT ROUTING ===
# Each handler gets multiple representative phrases. At query time we embed the
# question with nomic-embed-text (via Ollama) and find the closest match using
# cosine similarity. No LLM calls needed — instant routing.

INTENT_PHRASES = {
    'seasonal_readiness': [
        'monsoon readiness', 'summer preparedness', 'winter planning',
        'festive season stock', 'rainy season impact', 'diwali preparation',
        'are we ready for monsoon', 'seasonal demand planning',
        'prepared for summer', 'ready for winter',
    ],
    'drug_interest': [
        'interest in drugs', 'demand for medicines', 'GLP-1 demand',
        'ozempic sales', 'diabetes medicine trend', 'blood pressure drugs',
        'antibiotic demand', 'cardiac medicine sales', 'vitamin supplement trend',
        'which therapeutic area sells most', 'derma product demand',
        'respiratory medicine interest', 'painkiller sales',
    ],
    'stores_bleeding': [
        'stores bleeding revenue', 'stores losing money', 'worst performing stores',
        'underperforming stores', 'struggling stores', 'which stores are failing',
        'store losses', 'problem stores',
    ],
    'slow_moving_stock': [
        'slow moving inventory', 'dead stock', 'expired products',
        'stuck inventory', 'shelf life issues', 'waste from expiry',
        'stagnant inventory', 'near-expiry stock',
    ],
    'day_of_week': [
        'best day for sales', 'busiest day of week', 'weekly revenue pattern',
        'weekend vs weekday sales', 'which day has most revenue',
        'daily sales pattern',
    ],
    'store_city_performance': [
        'how are stores in Mumbai performing', 'store performance by city',
        'city store comparison', 'stores in Pune',
        'store performance in Bengaluru', 'how is the Thane store doing',
    ],
    'city_revenue_specific': [
        'revenue in Mumbai', 'sales in Pune', 'Thane revenue',
        'how much does Bengaluru make', 'Nashik sales figures',
        'how much revenue from Goa', 'specific city revenue drilldown',
        'revenue for a particular city', 'city specific revenue numbers',
    ],
    'total_revenue': [
        'total revenue', 'overall sales', 'how much revenue',
        'how much money did we make', 'total sales figure',
        'what is our revenue', 'earnings overview',
    ],
    'yoy': [
        'year over year growth', 'annual growth rate', 'YoY revenue',
        'revenue growth trend', 'compared to last year',
        'fiscal year comparison',
    ],
    'categories': [
        'top product categories', 'revenue by category', 'which category sells most',
        'category breakdown', 'product mix', 'what sells the most',
        'category wise revenue',
    ],
    'city_revenue': [
        'revenue by city', 'which city generates most revenue',
        'top cities by sales', 'city wise revenue comparison',
        'geographic revenue breakdown',
    ],
    'top_stores': [
        'top performing stores', 'best stores by revenue', 'winning stores',
        'highest revenue stores', 'store ranking', 'store leaderboard',
        'top stores', 'which stores make the most',
        'top stores by revenue', 'store performance ranking',
        'best performing store locations',
    ],
    'top_products': [
        'top selling products', 'best sellers', 'most popular products',
        'highest selling products', 'product ranking', 'top SKUs',
        'best selling products', 'which products sell the most',
        'product leaderboard', 'top products by revenue',
    ],
    'top_brands': [
        'top brands by revenue', 'best selling brands', 'brand ranking',
        'which brands sell most', 'popular brands',
    ],
    'customers': [
        'how many customers', 'total customers', 'customer base',
        'customer count', 'buyer overview', 'customer demographics',
    ],
    'churn': [
        'customer churn', 'customers leaving', 'customer attrition',
        'stopped buying', 'inactive customers', 'lost customers',
        'customer retention rate', 'not coming back',
        'what is our customer retention like',
    ],
    'loyal_customers': [
        'loyal customers', 'champion customers', 'best customers',
        'VIP customers', 'top spenders', 'high value customers',
        'repeat buyers',
    ],
    'margin': [
        'profit margin', 'how profitable are we', 'gross margin',
        'profitability', 'EBITDA', 'bottom line', 'net margin',
        'how much profit',
    ],
    'generic_branded': [
        'generic vs branded', 'branded vs generic margin',
        'generic medicine margin', 'private label performance',
        'generic substitution',
    ],
    'leakage': [
        'revenue leakage', 'where is revenue leaking', 'money left on table',
        'revenue loss', 'losing money', 'revenue gap', 'missed revenue',
        'where are we leaking',
    ],
    'cancellations': [
        'order cancellations', 'why orders cancelled', 'cancellation rate',
        'cancelled orders', 'why are orders being cancelled',
    ],
    'returns': [
        'product returns', 'refund rate', 'return rate',
        'returned orders', 'products sent back',
    ],
    'stockouts': [
        'out of stock', 'stockout rate', 'empty shelves',
        'product availability', 'OOS rate', 'missing products',
        'can not find products', 'stock out problem',
    ],
    'delivery': [
        'delivery performance', 'on-time delivery', 'SLA compliance',
        'late deliveries', 'delivery delays', 'how fast is delivery',
        'delivery speed', 'shipping performance',
    ],
    'online': [
        'online sales', 'digital channel', 'e-commerce performance',
        'omnichannel', 'online vs offline', 'digital sales share',
        'app sales', 'website orders',
    ],
    'payments': [
        'payment methods', 'UPI usage', 'cash vs digital',
        'payment mode breakdown', 'how do customers pay',
        'digital payment share', 'COD orders',
    ],
    'session_history': [
        'conversation history', 'what did we discuss', 'recent questions',
        'what was discussed', 'previous questions', 'session history',
    ],
    'popular_questions': [
        'most common questions', 'frequently asked', 'FAQ',
        'what do people ask', 'popular topics', 'top questions',
    ],
    'learned_insights': [
        'what has system learned', 'accumulated intelligence',
        'system knowledge', 'learned insights', 'what do you know',
    ],
    'summary': [
        'business overview', 'big picture', 'how is business doing',
        'executive summary', 'overall performance', 'KPI summary',
        'health check', 'dashboard overview',
    ],
    'aov': [
        'average order value', 'order size', 'basket size',
        'what is our AOV', 'how much per order', 'average basket',
        'average transaction value', 'mean order amount',
        'typical order value', 'AOV trend',
    ],
}

# Similarity threshold — below this we fall back to regex
EMBED_SIMILARITY_THRESHOLD = 0.35


def _cosine_sim(a, b):
    """Cosine similarity between vector a and matrix b."""
    # a: (dim,), b: (n, dim) -> (n,)
    dot = b @ a
    norm_a = np.linalg.norm(a)
    norm_b = np.linalg.norm(b, axis=1)
    return dot / (norm_a * norm_b + 1e-10)


def _embed_texts(texts):
    """Embed a list of texts using Ollama nomic-embed-text. Returns np.array."""
    resp = ollama_client.embed(model="nomic-embed-text", input=texts)
    return np.array(resp.embeddings, dtype=np.float32)


def build_intent_index():
    """Build or load the intent embedding index.

    Each phrase is prefixed with context to avoid short-phrase bias
    (e.g., "AOV" alone is too generic, but "average order value: AOV" is specific).

    Returns {'handlers': [name, ...], 'phrase_to_handler': [idx, ...], 'embeddings': np.array}
    """
    # Check cache (v2 has contextualized phrases)
    if EMBED_CACHE_PATH.exists():
        try:
            cache = json.loads(EMBED_CACHE_PATH.read_text(encoding='utf-8'))
            if cache.get('version') == 2:
                idx = {
                    'handlers': cache['handlers'],
                    'phrase_to_handler': cache['phrase_to_handler'],
                    'embeddings': np.array(cache['embeddings'], dtype=np.float32),
                }
                print(f"  Loaded intent embeddings from cache ({idx['embeddings'].shape[0]} phrases)")
                return idx
        except Exception:
            pass

    print("  Building intent embeddings (one-time, ~10s)...")
    all_phrases = []
    phrase_to_handler = []
    handlers = list(INTENT_PHRASES.keys())

    # Contextualize short phrases to avoid false matches
    for handler_name, phrases in INTENT_PHRASES.items():
        handler_idx = handlers.index(handler_name)
        context = handler_name.replace('_', ' ')
        for phrase in phrases:
            # Prefix short phrases with handler context for better discrimination
            if len(phrase.split()) <= 2:
                contextualized = f"{context}: {phrase}"
            else:
                contextualized = phrase
            all_phrases.append(contextualized)
            phrase_to_handler.append(handler_idx)

    embeddings = _embed_texts(all_phrases)

    # Cache to disk
    cache = {
        'version': 2,
        'handlers': handlers,
        'phrase_to_handler': phrase_to_handler,
        'embeddings': embeddings.tolist(),
    }
    EMBED_CACHE_PATH.write_text(json.dumps(cache, ensure_ascii=False), encoding='utf-8')
    print(f"  Indexed {len(all_phrases)} phrases for {len(handlers)} handlers")
    return {
        'handlers': handlers,
        'phrase_to_handler': phrase_to_handler,
        'embeddings': embeddings,
    }


# === CHART GENERATION ===
plt.rcParams.update({
    'figure.facecolor': '#1a1a2e', 'axes.facecolor': '#16213e',
    'axes.edgecolor': '#e0e0e0', 'axes.labelcolor': '#e0e0e0',
    'text.color': '#e0e0e0', 'xtick.color': '#e0e0e0', 'ytick.color': '#e0e0e0',
    'grid.color': '#2a2a4a', 'grid.alpha': 0.3, 'font.size': 10,
})
CHART_COLORS = ['#4fc3f7', '#81c784', '#ffb74d', '#e57373', '#ba68c8',
                '#4dd0e1', '#fff176', '#a1887f', '#90a4ae', '#f48fb1']


def fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    return base64.b64encode(buf.getvalue()).decode()


def make_chart_img(fig, alt='Chart'):
    b64 = fig_to_b64(fig)
    return f'<img class="chat-chart" src="data:image/png;base64,{b64}" alt="{alt}">'


def inr_fmt(x, _pos=None):
    if abs(x) >= 1e7: return f'{x/1e7:.1f} Cr'
    if abs(x) >= 1e5: return f'{x/1e5:.0f} L'
    return f'{x:,.0f}'


# === MODE PARSING ===
def parse_mode(raw_question):
    """Extract mode tag and clean question."""
    m = re.match(r'\[(BRIEF|INSIGHTS|DEEP)\]\s*(.*)', raw_question, re.IGNORECASE)
    if m:
        return m.group(1).upper(), m.group(2).strip()
    return 'INSIGHTS', raw_question.strip()


# === HTML FORMATTING HELPERS ===
def html_table(headers, rows):
    """Build an HTML table from headers and row tuples."""
    h = ''.join(f'<th>{h}</th>' for h in headers)
    body = ''
    for row in rows:
        cells = ''.join(f'<td>{c}</td>' for c in row)
        body += f'<tr>{cells}</tr>'
    return f'<table class="chat-table"><tr>{h}</tr>{body}</table>'


def html_action(text):
    return f'<p class="chat-action"><strong>What to do:</strong> {text}</p>'


def html_p(text):
    return f'<p>{text}</p>'


def html_benchmark(wf_value, wf_label, bench_value, bench_label):
    """Show a WF metric vs industry benchmark comparison."""
    return (f'<p><strong>{wf_label}:</strong> {wf_value} '
            f'(Industry benchmark: {bench_value} — {bench_label})</p>')


def html_drilldowns(options):
    """Render drill-down buttons. options: list of (label, query) tuples."""
    btns = ''.join(
        f'<button class="chat-drill-btn" data-query="{q}">{label}</button>'
        for label, q in options
    )
    return f'<div class="chat-drilldowns">{btns}</div>'


# === MEMORY SYSTEM ===
CACHE_FILE = ROOT / 'analysis' / 'response_cache.json'
LOG_FILE = ROOT / 'analysis' / 'conversation_log.jsonl'
INSIGHTS_FILE = ROOT / 'analysis' / 'learned_insights.json'
CACHE_TTL_HOURS = 2


def init_memory():
    """Create memory files if they don't exist."""
    if not CACHE_FILE.exists():
        CACHE_FILE.write_text('{}', encoding='utf-8')
    if not LOG_FILE.exists():
        LOG_FILE.write_text('', encoding='utf-8')
    if not INSIGHTS_FILE.exists():
        INSIGHTS_FILE.write_text(json.dumps({"insights": [], "next_id": 1}, indent=2),
                                  encoding='utf-8')


def load_cache():
    try:
        return json.loads(CACHE_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {}


def get_cached(key):
    """Return cached response if key exists and is fresh (< TTL)."""
    cache = load_cache()
    entry = cache.get(key)
    if not entry:
        return None
    cached_at = datetime.fromisoformat(entry['cached_at'])
    if datetime.now() - cached_at > timedelta(hours=CACHE_TTL_HOURS):
        return None
    # Bump hit count
    entry['hit_count'] = entry.get('hit_count', 0) + 1
    cache[key] = entry
    try:
        CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass
    return entry['response']


def set_cache(key, response):
    """Cache a handler response."""
    cache = load_cache()
    cache[key] = {
        'response': response,
        'cached_at': datetime.now().isoformat(timespec='seconds'),
        'hit_count': 0,
    }
    try:
        CACHE_FILE.write_text(json.dumps(cache, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass


def log_conversation(query, mode, handler, response, entities=None, cached=False):
    """Append a conversation entry to the JSONL log."""
    entry = {
        'ts': datetime.now().isoformat(timespec='seconds'),
        'query': query,
        'mode': mode,
        'handler': handler,
        'entities': entities or {},
        'response_len': len(response) if response else 0,
        'cached': cached,
    }
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(json.dumps(entry, ensure_ascii=False) + '\n')
    except Exception:
        pass


def load_insights():
    try:
        return json.loads(INSIGHTS_FILE.read_text(encoding='utf-8'))
    except Exception:
        return {"insights": [], "next_id": 1}


def save_insight(topic, summary, tags, source='analysis'):
    """Add a new learned insight."""
    data = load_insights()
    data['insights'].append({
        'id': data['next_id'],
        'topic': topic,
        'summary': summary,
        'tags': tags,
        'created': datetime.now().isoformat(timespec='seconds'),
        'source': source,
        'referenced_count': 0,
    })
    data['next_id'] += 1
    try:
        INSIGHTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
    except Exception:
        pass


def find_relevant_insights(tags):
    """Find insights matching any of the given tags."""
    data = load_insights()
    matched = []
    tag_set = set(t.lower() for t in tags)
    for ins in data['insights']:
        if tag_set & set(t.lower() for t in ins.get('tags', [])):
            ins['referenced_count'] = ins.get('referenced_count', 0) + 1
            matched.append(ins)
    if matched:
        try:
            INSIGHTS_FILE.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding='utf-8')
        except Exception:
            pass
    return matched


def read_log_entries(limit=50):
    """Read last N entries from conversation log."""
    try:
        lines = LOG_FILE.read_text(encoding='utf-8').strip().split('\n')
        lines = [l for l in lines if l.strip()]
        entries = [json.loads(l) for l in lines[-limit:]]
        return entries
    except Exception:
        return []


# Known entities for extraction
CITIES = ['Mumbai', 'Pune', 'Thane', 'Bengaluru', 'Navi Mumbai', 'Nashik', 'Goa']
CITY_ALIASES = {
    'chinchwad': 'Pune', 'pimpri': 'Pune', 'pcmc': 'Pune',
    'bangalore': 'Bengaluru', 'blr': 'Bengaluru',
    'bombay': 'Mumbai', 'bom': 'Mumbai',
    'navi mumbai': 'Navi Mumbai', 'navimumbai': 'Navi Mumbai',
}
THERAPEUTIC_AREAS = [
    'Anti-diabetic', 'Anti-hypertensive', 'Anti-inflammatory', 'Anti-viral',
    'Anti-allergic', 'Antibiotic', 'Cardiac', 'Dermatological',
    'Gastrointestinal', 'Hormonal', 'Musculoskeletal', 'Neurological',
    'Pain Management', 'Respiratory', 'Vitamin/Supplement',
]
DRUG_ALIASES = {
    'glp-1': 'Anti-diabetic', 'glp1': 'Anti-diabetic', 'semaglutide': 'Anti-diabetic',
    'ozempic': 'Anti-diabetic', 'wegovy': 'Anti-diabetic', 'liraglutide': 'Anti-diabetic',
    'mounjaro': 'Anti-diabetic', 'tirzepatide': 'Anti-diabetic',
    'diabetes': 'Anti-diabetic', 'diabetic': 'Anti-diabetic', 'sugar': 'Anti-diabetic',
    'bp medicine': 'Anti-hypertensive', 'blood pressure': 'Anti-hypertensive',
    'hypertension': 'Anti-hypertensive',
    'pain': 'Pain Management', 'painkiller': 'Pain Management',
    'antibiotic': 'Antibiotic', 'infection': 'Antibiotic',
    'heart': 'Cardiac', 'cardiac': 'Cardiac',
    'skin': 'Dermatological', 'derma': 'Dermatological',
    'stomach': 'Gastrointestinal', 'gastro': 'Gastrointestinal', 'acidity': 'Gastrointestinal',
    'vitamin': 'Vitamin/Supplement', 'supplement': 'Vitamin/Supplement',
    'allergy': 'Anti-allergic', 'allergic': 'Anti-allergic',
    'breathing': 'Respiratory', 'asthma': 'Respiratory', 'respiratory': 'Respiratory',
}
SEASONS = {
    'monsoon': ('06', '07', '08'), 'rainy': ('06', '07', '08'),
    'summer': ('03', '04', '05'), 'winter': ('12', '01', '02'),
    'festive': ('10', '11'), 'diwali': ('10', '11'),
}
DOW_NAMES = ['Sunday', 'Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday']


def inr_label(val):
    """Format value in Indian number system."""
    if abs(val) >= 1e7:
        return f'\u20b9{val/1e7:.2f} Cr'
    elif abs(val) >= 1e5:
        return f'\u20b9{val/1e5:.2f} L'
    return f'\u20b9{val:,.0f}'


def query_db(sql, params=None):
    """Execute a SQL query and return results as list of dicts."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    try:
        if params:
            rows = conn.execute(sql, params).fetchall()
        else:
            rows = conn.execute(sql).fetchall()
        return [dict(r) for r in rows]
    except Exception as e:
        return f"Error: {e}"
    finally:
        conn.close()


# === ENTITY EXTRACTION ===

def extract_city(q):
    """Extract a city name from the question."""
    ql = q.lower()
    # Check aliases first
    for alias, city in CITY_ALIASES.items():
        if alias in ql:
            return city
    # Check exact city names
    for city in CITIES:
        if city.lower() in ql:
            return city
    return None


def extract_store(q):
    """Extract a store identifier from the question."""
    m = re.search(r'(wf-?\d+|sta-?\d+|fla-?\d+|nei-?\d+)', q.lower())
    if m:
        return m.group(1).upper().replace('WF', 'WF-')
    return None


def extract_therapeutic(q):
    """Extract a therapeutic area from the question."""
    ql = q.lower()
    for alias, area in DRUG_ALIASES.items():
        if alias in ql:
            return area
    for area in THERAPEUTIC_AREAS:
        if area.lower() in ql:
            return area
    return None


def extract_season(q):
    """Extract a season from the question."""
    ql = q.lower()
    for season, months in SEASONS.items():
        if season in ql:
            return season, months
    return None, None


# === PATTERN ROUTING (order matters — more specific patterns first) ===

PATTERNS = [
    # Seasonal readiness
    (r'(ready|readiness|prepared|prepar).*(monsoon|summer|winter|festive|rainy|diwali)', 'seasonal_readiness'),
    (r'(monsoon|summer|winter|festive|rainy|diwali).*(ready|readiness|prepared|prepar|impact|perform)', 'seasonal_readiness'),

    # Interest/demand for specific drugs/therapeutic areas
    (r'(interest|demand|buying|selling|popular).*(glp|ozempic|wegovy|semaglutide|diabet|bp|blood pressure|pain|antibiotic|heart|skin|vitamin|allergy|asthma|respiratory|stomach)', 'drug_interest'),
    (r'(glp|ozempic|wegovy|semaglutide).*(interest|demand|trend|sale)', 'drug_interest'),

    # Stores bleeding / losing revenue
    (r'(store|stores).*(bleed|losing|lost|leak|worst|underperform|struggling)', 'stores_bleeding'),
    (r'(bleed|losing|leak).*(store|stores)', 'stores_bleeding'),

    # Expired / slow-moving / dead stock
    (r'(expir|dead.stock|slow.mov|sitting|stuck|shelf.life|waste)', 'slow_moving_stock'),

    # Day of week
    (r'(day|week|weekday|weekend).*(revenue|sales|busiest|highest|most)', 'day_of_week'),
    (r'(busiest|highest|most).*(day|week)', 'day_of_week'),

    # Store-specific performance (with city or store ID)
    (r'(how|what).*(store|stores).*(mumbai|pune|thane|bengaluru|nashik|goa|navi mumbai|chinchwad|pimpri)', 'store_city_performance'),
    (r'(mumbai|pune|thane|bengaluru|nashik|goa|navi mumbai|chinchwad|pimpri).*(store|stores|performance|doing)', 'store_city_performance'),

    # Revenue by city
    (r'(revenue|sales).*(mumbai|pune|thane|bengaluru|nashik|goa|navi mumbai|chinchwad|pimpri)', 'city_revenue_specific'),
    (r'(mumbai|pune|thane|bengaluru|nashik|goa|navi mumbai|chinchwad|pimpri).*(revenue|sales)', 'city_revenue_specific'),

    # Revenue questions
    (r'total revenue', 'total_revenue'),
    (r'how much.*(revenue|sales|money)', 'total_revenue'),
    (r'revenue.*year|yoy|year.over.year|growth', 'yoy'),
    (r'(which|what|top).*(category|categories)', 'categories'),
    (r'(which|what|top).*(city|cities)', 'city_revenue'),
    (r'(which|what|top).*(store|stores).*(revenue|best|winning|performing)', 'top_stores'),
    (r'(which|what|top).*(product|products)', 'top_products'),
    (r'(which|what|top).*(brand|brands)', 'top_brands'),

    # Customer questions
    (r'(how many|total).*(customer|buyers)', 'customers'),
    (r'churn|leaving|walking away|stopped buying', 'churn'),
    (r'(loyal|champion|best).*(customer|buyers)', 'loyal_customers'),

    # Margin / profit
    (r'margin|profit', 'margin'),
    (r'generic.vs.branded|branded.vs.generic', 'generic_branded'),

    # Leakage
    (r'leakage|leaking|losing|lost.*revenue|money.*table|revenue.*leak', 'leakage'),
    (r'cancel|cancellation', 'cancellations'),
    (r'return|refund', 'returns'),

    # Inventory
    (r'stock.?out|out.of.stock|empty.shelf|oos', 'stockouts'),

    # Operations
    (r'delivery|on.time|sla|late|delay', 'delivery'),
    (r'online|digital|channel', 'online'),
    (r'payment|upi|cash|card', 'payments'),

    # Memory / meta
    (r'(what|show).*(discussed|conversation|history|recent question)', 'session_history'),
    (r'(common|popular|frequently|faq|people.*(ask|question)|what do.*(ask|question))', 'popular_questions'),
    (r'(what.*(learn|know|accumulated)|system.*(knowledge|intelligence|insight)|learned.insight)', 'learned_insights'),

    # General
    (r'how.*doing|performance|overview|summary|big picture', 'summary'),
    (r'aov|average.order|order.value', 'aov'),
]


def resolve_intent(question, intent_index):
    """Find the best handler using embedding similarity with per-handler voting.

    Aggregates top-2 phrase scores per handler to avoid single-phrase flukes.
    Returns (handler_name, similarity_score) or (None, 0.0).
    """
    if intent_index is None:
        return None, 0.0

    q_emb = _embed_texts([question])[0]
    sims = _cosine_sim(q_emb, intent_index['embeddings'])

    # Aggregate: for each handler, take the mean of its top-2 phrase scores
    handlers = intent_index['handlers']
    p2h = intent_index['phrase_to_handler']
    handler_scores = {}
    for i, sim in enumerate(sims):
        h = handlers[p2h[i]]
        if h not in handler_scores:
            handler_scores[h] = []
        handler_scores[h].append(float(sim))

    best_handler = None
    best_score = 0.0
    for h, scores in handler_scores.items():
        scores.sort(reverse=True)
        # Average of top 2 (or top 1 if only 1 phrase)
        avg = sum(scores[:2]) / min(len(scores), 2)
        if avg > best_score:
            best_score = avg
            best_handler = h

    if best_score < EMBED_SIMILARITY_THRESHOLD:
        return None, best_score

    return best_handler, best_score


def _run_handler(handler_name, entities, question, resolved, q, mode):
    """Execute a handler and return the HTML result (shared by RAG and regex paths)."""
    fn = HANDLERS.get(handler_name)
    if not fn:
        return None

    cache_key = f"{handler_name}|{mode}"
    if not entities:
        cached = get_cached(cache_key)
        if cached:
            _session_context.update(last_question=question, last_handler=handler_name, last_entities=entities)
            log_conversation(question, mode, handler_name, cached, entities, cached=True)
            return cached

    # Run handler with resolved question for full context
    result = fn(resolved if resolved != q else question, mode)

    # Enrich with relevant learned insights
    tags = [handler_name] + list(entities.values())
    relevant = find_relevant_insights(tags)
    if relevant:
        insight_text = relevant[0]['summary']
        result += html_p(f'<em>Related insight: {insight_text}</em>')

    # Save session context
    _session_context.update(last_question=question, last_handler=handler_name, last_entities=entities)

    # Cache and log
    if not entities:
        set_cache(cache_key, result)
    log_conversation(question, mode, handler_name, result, entities, cached=False)
    return result


def _regex_route(q):
    """Match question against PATTERNS. Returns (handler_name, None) or (None, None)."""
    for pattern, handler_name in PATTERNS:
        if re.search(pattern, q):
            return handler_name
    return None


def find_answer(question, mode='INSIGHTS'):
    """Match question to a handler and return HTML answer."""
    q = question.lower().strip()

    # Follow-up resolution: combine with previous question for pattern matching
    resolved = q
    if is_followup(question) and _session_context['last_question']:
        resolved = _session_context['last_question'].lower().strip() + ' ' + q

    handler_name = None
    rag_entities = {}

    # Try embedding-based routing first
    if _intent_index is not None:
        try:
            handler_name, sim_score = resolve_intent(question, _intent_index)
            if handler_name:
                print(f"  [embed] resolved -> {handler_name} (sim: {sim_score:.3f})")
        except Exception as e:
            print(f"  [embed] error: {e} — falling back to regex")
            handler_name = None

    # Fall back to regex routing
    if not handler_name:
        handler_name = _regex_route(q)
        if handler_name:
            print(f"  [regex] matched -> {handler_name}")

    if handler_name:
        # Extract entities using rule-based functions
        entities = {}
        city = extract_city(resolved)
        therapeutic = extract_therapeutic(resolved)
        if city:
            entities['city'] = city
        if therapeutic:
            entities['therapeutic'] = therapeutic

        result = _run_handler(handler_name, entities, question, resolved, q, mode)
        if result:
            return result

    # Fallback: try entity-based answer (use resolved question for follow-ups)
    return smart_fallback(resolved if resolved != q else question, mode)


def smart_fallback(question, mode='INSIGHTS'):
    """Try to extract entities and give a useful answer even for unrecognized patterns."""
    q = question.lower()
    city = extract_city(q)
    therapeutic = extract_therapeutic(q)

    if city:
        result = h_store_city_performance(question, mode)
        _session_context.update(last_question=question, last_handler='store_city_performance', last_entities={'city': city})
        log_conversation(question, mode, 'store_city_performance', result, {'city': city})
        return result
    if therapeutic:
        result = h_drug_interest(question, mode)
        _session_context.update(last_question=question, last_handler='drug_interest', last_entities={'therapeutic': therapeutic})
        log_conversation(question, mode, 'drug_interest', result, {'therapeutic': therapeutic})
        return result

    # Check learned insights for keyword matches
    words = [w for w in re.findall(r'\w+', q) if len(w) > 3]
    relevant = find_relevant_insights(words)
    if relevant:
        parts = [html_p('<strong>From accumulated intelligence:</strong>')]
        for ins in relevant[:3]:
            parts.append(html_p(f'<strong>{ins["topic"]}:</strong> {ins["summary"]}'))
        parts.append(html_p('You can also try one of these:'))
        parts.append(html_drilldowns([
            ('Total Revenue', 'What is our total revenue?'),
            ('Stores Bleeding', 'Which stores are bleeding revenue?'),
            ('System Knowledge', 'What has the system learned?'),
        ]))
        log_conversation(question, mode, None, ''.join(parts), {})
        return ''.join(parts)

    parts = [
        '<p>I can help with a wide range of questions about your business. Try one of these:</p>'
    ]
    parts.append(html_drilldowns([
        ('Total Revenue', 'What is our total revenue?'),
        ('Stores Bleeding', 'Which stores are bleeding revenue?'),
        ('Stockouts', 'How bad is our stockout problem?'),
        ('Monsoon Ready', 'Are we ready for monsoon in Mumbai?'),
    ]))
    log_conversation(question, mode, None, ''.join(parts), {})
    return ''.join(parts)


# === HANDLER FUNCTIONS ===
# All handlers accept the original question for entity extraction

def h_total_revenue(_q='', mode='INSIGHTS'):
    rev = inr_label(kpis['total_revenue'])
    if mode == 'BRIEF':
        return html_p(f'<strong>Total revenue: {rev}</strong> across 30 stores over 24 months (+{kpis["yoy_growth_pct"]:.1f}% YoY).')

    parts = [html_p(f'<strong>Total revenue: {rev}</strong> across 30 stores, {kpis["total_delivered_orders"]:,} orders over 24 months.')]
    parts.append(html_table(
        ['Period', 'Revenue', 'Growth'],
        [('FY25', inr_label(kpis['fy25_revenue']), '—'),
         ('FY26', inr_label(kpis['fy26_revenue']), f'+{kpis["yoy_growth_pct"]:.1f}%'),
         ('<strong>Total</strong>', f'<strong>{rev}</strong>', '')]
    ))
    parts.append(html_p(f'Average order value: <strong>{inr_label(kpis["aov"])}</strong>. Margin: <strong>{kpis["overall_margin_pct"]:.1f}%</strong> ({inr_label(kpis["total_margin"])}).'))

    if mode == 'DEEP':
        # Add chart
        rows = query_db("""SELECT strftime('%Y-%m', o.order_date) as month, SUM(li.line_total) as revenue
            FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
            WHERE o.status = 'Delivered' GROUP BY month ORDER BY month""")
        if isinstance(rows, list) and rows:
            fig, ax = plt.subplots(figsize=(8, 3.5))
            months = [r['month'] for r in rows]
            revs = [r['revenue'] for r in rows]
            ax.fill_between(range(len(months)), revs, alpha=0.3, color=CHART_COLORS[0])
            ax.plot(range(len(months)), revs, 'o-', color=CHART_COLORS[0], markersize=3, linewidth=2)
            ax.set_xticks(range(0, len(months), 3))
            ax.set_xticklabels([months[i] for i in range(0, len(months), 3)], rotation=45, ha='right', fontsize=8)
            ax.set_title('Monthly Revenue Trend', fontsize=11, fontweight='bold')
            ax.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
            ax.grid(alpha=0.2)
            fig.tight_layout()
            parts.append(make_chart_img(fig, 'Monthly Revenue Trend'))
        parts.append(html_benchmark(f'{kpis["yoy_growth_pct"]:.1f}%', 'WF YoY Growth', '8-10%', 'industry avg for Indian pharmacy chains'))

    parts.append(html_action('Revenue is growing at a healthy rate. Focus on reducing the {:.1f}% revenue leakage (cancellations, returns, stockouts) to push effective revenue even higher.'.format(kpis['leakage_pct'])))
    parts.append(html_drilldowns([
        ('By Category', 'Revenue by category'),
        ('By City', 'Revenue by city'),
        ('Stores Bleeding', 'Which stores are bleeding revenue?'),
        ('Leakage', 'Where is revenue leaking?'),
    ]))
    return ''.join(parts)


def h_yoy(_q='', mode='INSIGHTS'):
    if mode == 'BRIEF':
        return html_p(f'YoY growth: <strong>+{kpis["yoy_growth_pct"]:.1f}%</strong>. FY26 revenue {inr_label(kpis["fy26_revenue"])} vs FY25 {inr_label(kpis["fy25_revenue"])}.')
    return h_total_revenue(_q, mode)


def h_categories(_q='', mode='INSIGHTS'):
    rows = query_db("""SELECT p.category, SUM(li.line_total) as revenue
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
        JOIN products p ON li.product_id = p.product_id
        WHERE o.status = 'Delivered' GROUP BY p.category ORDER BY revenue DESC""")
    if isinstance(rows, str):
        return html_p(rows)
    total = sum(r['revenue'] for r in rows)

    if mode == 'BRIEF':
        top = rows[0]
        return html_p(f'<strong>{top["category"]}</strong> leads with {inr_label(top["revenue"])} ({top["revenue"]/total*100:.0f}% of revenue).')

    parts = [html_p('Revenue by product category:')]
    parts.append(html_table(
        ['Category', 'Revenue', 'Share'],
        [(r['category'], inr_label(r['revenue']), f'{r["revenue"]/total*100:.1f}%') for r in rows]
    ))

    if mode == 'DEEP':
        fig, ax = plt.subplots(figsize=(8, 4))
        cats = [r['category'][:15] for r in rows]
        vals = [r['revenue'] for r in rows]
        bars = ax.barh(range(len(cats)), vals, color=CHART_COLORS[:len(cats)], edgecolor='white', linewidth=0.3)
        ax.set_yticks(range(len(cats)))
        ax.set_yticklabels(cats, fontsize=9)
        ax.invert_yaxis()
        ax.set_title('Revenue by Category', fontsize=11, fontweight='bold')
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
        ax.grid(axis='x', alpha=0.2)
        fig.tight_layout()
        parts.append(make_chart_img(fig, 'Revenue by Category'))
        parts.append(html_p('<strong>Industry context:</strong> Indian pharmacy chains typically get 55-65% from Rx medicines, 12-18% OTC, 8-12% nutraceuticals. Nutraceuticals are the fastest-growing category at 10% CAGR nationally.'))

    parts.append(html_action('Rx medicines dominate. Consider growing the nutraceuticals and wellness categories — they carry higher margins (15-25%) and are the fastest-growing segment in Indian pharmacy retail.'))
    parts.append(html_drilldowns([
        ('Top Products', 'Top selling products'),
        ('Generic vs Branded', 'Generic vs branded margin'),
        ('Top Brands', 'Top brands by revenue'),
    ]))
    return ''.join(parts)


def h_city_revenue(_q='', mode='INSIGHTS'):
    rows = query_db("""SELECT s.city, SUM(li.line_total) as revenue, COUNT(DISTINCT s.store_id) as stores
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
        JOIN stores s ON o.store_id = s.store_id
        WHERE o.status = 'Delivered' GROUP BY s.city ORDER BY revenue DESC""")
    if isinstance(rows, str):
        return html_p(rows)

    if mode == 'BRIEF':
        return html_p(f'<strong>{rows[0]["city"]}</strong> leads with {inr_label(rows[0]["revenue"])} from {rows[0]["stores"]} stores.')

    parts = [html_p('Revenue by city:')]
    parts.append(html_table(
        ['City', 'Stores', 'Revenue', 'Rev/Store'],
        [(r['city'], r['stores'], inr_label(r['revenue']),
          inr_label(r['revenue'] / r['stores'])) for r in rows]
    ))
    if mode == 'DEEP':
        fig, ax = plt.subplots(figsize=(8, 4))
        ax.barh([r['city'] for r in reversed(rows)], [r['revenue'] for r in reversed(rows)],
                color=CHART_COLORS[:len(rows)], edgecolor='white', linewidth=0.3)
        ax.set_title('Revenue by City', fontsize=11, fontweight='bold')
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
        ax.grid(axis='x', alpha=0.2)
        fig.tight_layout()
        parts.append(make_chart_img(fig, 'Revenue by City'))
    parts.append(html_action(f'{rows[0]["city"]} dominates. Study what top-performing cities do differently and replicate in weaker markets.'))
    return ''.join(parts)


def h_city_revenue_specific(question, mode='INSIGHTS'):
    city = extract_city(question)
    if not city:
        return h_city_revenue(question, mode)
    rows = query_db("""SELECT s.store_name, SUM(li.line_total) as revenue, COUNT(DISTINCT o.order_id) as orders
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
        JOIN stores s ON o.store_id = s.store_id
        WHERE o.status = 'Delivered' AND s.city = ? GROUP BY o.store_id ORDER BY revenue DESC""", (city,))
    if isinstance(rows, str):
        return html_p(rows)
    if not rows:
        return html_p(f'No data found for {city}.')
    total = sum(r['revenue'] for r in rows)
    if mode == 'BRIEF':
        return html_p(f'<strong>{city}:</strong> {inr_label(total)} from {len(rows)} stores. Top: {rows[0]["store_name"]} ({inr_label(rows[0]["revenue"])}).')
    parts = [html_p(f'<strong>{city}</strong> — {len(rows)} stores, {inr_label(total)} total revenue:')]
    parts.append(html_table(
        ['Store', 'Revenue', 'Orders'],
        [(r['store_name'], inr_label(r['revenue']), f'{r["orders"]:,}') for r in rows]
    ))
    return ''.join(parts)


def h_top_stores(_q='', mode='INSIGHTS'):
    rows = query_db("""SELECT s.store_name, s.city, SUM(li.line_total) as revenue
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
        JOIN stores s ON o.store_id = s.store_id WHERE o.status = 'Delivered'
        GROUP BY o.store_id ORDER BY revenue DESC LIMIT 10""")
    if isinstance(rows, str):
        return html_p(rows)
    if mode == 'BRIEF':
        return html_p(f'Top store: <strong>{rows[0]["store_name"]}</strong> ({rows[0]["city"]}) with {inr_label(rows[0]["revenue"])}.')
    parts = [html_p('Top 10 stores by revenue:')]
    parts.append(html_table(
        ['#', 'Store', 'City', 'Revenue'],
        [(i+1, r['store_name'], r['city'], inr_label(r['revenue'])) for i, r in enumerate(rows)]
    ))
    if mode == 'DEEP':
        parts.append(html_p('<strong>Industry context:</strong> A well-performing organized pharmacy store in a Tier 1 city should earn ₹12-15 L/month. Flagship stores can reach ₹30 L/month. Hospital-adjacent pharmacies can hit ₹2-3 L/day.'))
    parts.append(html_action('Study what top stores do differently (staffing, layout, product mix) and replicate in lower-performing locations.'))
    return ''.join(parts)


def h_top_products(_q='', mode='INSIGHTS'):
    rows = query_db("""SELECT p.product_name, p.brand, SUM(li.line_total) as revenue
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
        JOIN products p ON li.product_id = p.product_id WHERE o.status = 'Delivered'
        GROUP BY li.product_id ORDER BY revenue DESC LIMIT 10""")
    if isinstance(rows, str):
        return html_p(rows)
    if mode == 'BRIEF':
        return html_p(f'Top product: <strong>{rows[0]["product_name"]}</strong> ({rows[0]["brand"]}) — {inr_label(rows[0]["revenue"])}.')
    parts = [html_p('Top 10 products by revenue:')]
    parts.append(html_table(
        ['#', 'Product', 'Brand', 'Revenue'],
        [(i+1, r['product_name'], r['brand'], inr_label(r['revenue'])) for i, r in enumerate(rows)]
    ))
    parts.append(html_action('These top sellers must never face stockouts. Set up automatic reorder alerts for all of them.'))
    return ''.join(parts)


def h_top_brands(_q='', mode='INSIGHTS'):
    rows = query_db("""SELECT p.brand, SUM(li.line_total) as revenue
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
        JOIN products p ON li.product_id = p.product_id WHERE o.status = 'Delivered'
        GROUP BY p.brand ORDER BY revenue DESC LIMIT 10""")
    if isinstance(rows, str):
        return html_p(rows)
    if mode == 'BRIEF':
        return html_p(f'Top brand: <strong>{rows[0]["brand"]}</strong> — {inr_label(rows[0]["revenue"])}.')
    parts = [html_p('Top 10 brands by revenue:')]
    parts.append(html_table(['#', 'Brand', 'Revenue'],
        [(i+1, r['brand'], inr_label(r['revenue'])) for i, r in enumerate(rows)]))
    return ''.join(parts)


def h_customers(_q='', mode='INSIGHTS'):
    if mode == 'BRIEF':
        return html_p(f'<strong>{kpis["total_customers"]:,}</strong> active customers. <strong>{kpis["churn_rate_pct"]:.1f}%</strong> at risk of leaving (90+ days inactive).')
    parts = [html_p(f'We have <strong>{kpis["total_customers"]:,}</strong> active customers.')]
    parts.append(html_table(
        ['Metric', 'Value'],
        [('Total Customers', f'{kpis["total_customers"]:,}'),
         ('At-Risk (90+ days inactive)', f'{kpis["at_risk_customers"]:,}'),
         ('Churn Rate', f'{kpis["churn_rate_pct"]:.1f}%'),
         ('Champions', f'{kpis["rfm_champions_pct"]:.1f}%'),
         ('Loyal', f'{kpis["rfm_loyal_pct"]:.1f}%'),
         ('Needs Attention', f'{kpis["rfm_needs_attention_pct"]:.1f}%'),
         ('At Risk', f'{kpis["rfm_at_risk_pct"]:.1f}%')]
    ))
    if mode == 'DEEP':
        parts.append(html_p('<strong>Industry context:</strong> Tata 1mg achieves 70% retention. Chronic patients (60-70% of repeat orders) have CLV of ₹1.2L-12L. Acquiring a new customer costs 5-7x more than retaining. Pharmacy churn benchmarks: &lt;25% is good.'))
    parts.append(html_action(f'{kpis["at_risk_customers"]:,} customers need re-engagement. Launch personalized win-back campaigns (WhatsApp reminders 3-5 days before expected refill date are most effective in India).'))
    parts.append(html_drilldowns([
        ('Top Spenders', 'Who are our most loyal customers?'),
        ('Churn Analysis', 'What is our churn rate?'),
        ('Revenue per Customer', 'What is our average order value?'),
    ]))
    return ''.join(parts)


def h_churn(_q='', mode='INSIGHTS'):
    if mode == 'BRIEF':
        return html_p(f'Churn rate: <strong>{kpis["churn_rate_pct"]:.1f}%</strong> — {kpis["at_risk_customers"]:,} customers inactive 90+ days.')
    return h_customers(_q, mode)


def h_loyal_customers(_q='', mode='INSIGHTS'):
    return h_customers(_q, mode)


def h_margin(_q='', mode='INSIGHTS'):
    if mode == 'BRIEF':
        return html_p(f'Profit margin: <strong>{kpis["overall_margin_pct"]:.1f}%</strong> ({inr_label(kpis["total_margin"])} on {inr_label(kpis["total_revenue"])}).')
    parts = [html_p(f'Overall margin: <strong>{kpis["overall_margin_pct"]:.1f}%</strong>, generating {inr_label(kpis["total_margin"])} on {inr_label(kpis["total_revenue"])} revenue.')]
    if mode in ('INSIGHTS', 'DEEP'):
        parts.append(html_table(
            ['Metric', 'WF', 'Industry Benchmark'],
            [('Gross Margin', f'{kpis["overall_margin_pct"]:.1f}%', '20-26% (organized chains)'),
             ('Rx Branded Margin', '16-22%', '16-22%'),
             ('Generic Margin', '20-50%', '20-50% (private label: 2x branded)'),
             ('EBITDA (mature store)', '10-12%', '10-12% (MedPlus benchmark)')]
        ))
    if mode == 'DEEP':
        parts.append(html_p('<strong>Industry context:</strong> MedPlus achieves 26.1% gross margin with private label at 22% of revenue. Generic medicines offer 2-5x the margin of branded. Jan Aushadhi generics are 50-90% cheaper but face adoption barriers.'))
    parts.append(html_action('Push generic/private label share — MedPlus targets 50-60% revenue from store generics. Even modest generic substitution can significantly boost margins.'))
    parts.append(html_drilldowns([
        ('By Category', 'Revenue by category'),
        ('Top Products', 'Top selling products'),
        ('Leakage', 'Where is revenue leaking?'),
    ]))
    return ''.join(parts)


def h_generic_branded(_q='', mode='INSIGHTS'):
    return h_margin(_q, mode)


def h_leakage(_q='', mode='INSIGHTS'):
    if mode == 'BRIEF':
        return html_p(f'Revenue leakage: <strong>{kpis["leakage_pct"]:.1f}%</strong> — {inr_label(kpis["total_leakage"])} lost to cancellations, returns, stockouts, and delays.')
    parts = [html_p(f'We\'re leaving <strong>{inr_label(kpis["total_leakage"])}</strong> on the table — {kpis["leakage_pct"]:.1f}% of potential revenue.')]
    parts.append(html_table(
        ['Leakage Source', 'Amount', 'Impact'],
        [('Cancellations', inr_label(kpis['cancellation_loss']), 'Biggest leak — address first'),
         ('Returns', inr_label(kpis['return_loss']), 'Improve order accuracy'),
         ('Stockouts', '~₹2.42 Cr (est.)', 'Empty shelves = lost customers'),
         ('Late Deliveries', '~₹16 L (est.)', 'Tighten delivery ops')]
    ))
    if mode == 'DEEP':
        rows = query_db("""SELECT cancellation_reason as reason, COUNT(*) as cnt
            FROM orders WHERE status = 'Cancelled' AND cancellation_reason IS NOT NULL
            GROUP BY cancellation_reason ORDER BY cnt DESC LIMIT 5""")
        if isinstance(rows, list) and rows:
            parts.append(html_p('<strong>Top cancellation reasons:</strong>'))
            parts.append(html_table(['Reason', 'Orders'],
                [(r['reason'], f'{r["cnt"]:,}') for r in rows]))
        parts.append(html_p('<strong>Industry context:</strong> Pharmacy cancellation rate benchmark is &lt;3%. Return rate for pharmacy is 2-5% (vs 16.9% for general e-commerce). 30-40% of customers switch pharmacies after a stockout.'))
    parts.append(html_action('Tackle cancellations first (highest impact). Identify top 3 cancellation reasons and create action plans for each. Industry target: under 3% cancellation rate.'))
    parts.append(html_drilldowns([
        ('Stockouts', 'How bad is our stockout problem?'),
        ('Delivery SLA', 'How is our delivery performance?'),
        ('Stores Bleeding', 'Which stores are bleeding revenue?'),
    ]))
    return ''.join(parts)


def h_cancellations(_q='', mode='INSIGHTS'):
    return h_leakage(_q, mode)


def h_returns(_q='', mode='INSIGHTS'):
    if mode == 'BRIEF':
        return html_p(f'Returns cost us <strong>{inr_label(kpis["return_loss"])}</strong>. Improve product descriptions and order accuracy to reduce.')
    return h_leakage(_q, mode)


def h_stockouts(_q='', mode='INSIGHTS'):
    if mode == 'BRIEF':
        return html_p(f'Stockout rate: <strong>{kpis["avg_oos_rate_pct"]:.1f}%</strong> (target: &lt;5%). Estimated cost: ~₹2.42 Cr in lost sales.')

    parts = [html_p(f'Stockout rate: <strong>{kpis["avg_oos_rate_pct"]:.1f}%</strong> — above the 5% target.')]
    rows = query_db("""SELECT p.product_name, p.category, AVG(i.is_out_of_stock)*100 as oos_rate
        FROM inventory i JOIN products p ON i.product_id = p.product_id
        GROUP BY i.product_id HAVING oos_rate > 8 ORDER BY oos_rate DESC LIMIT 8""")
    if isinstance(rows, list) and rows:
        parts.append(html_table(['Product', 'Category', 'OOS Rate'],
            [(r['product_name'], r['category'], f'{r["oos_rate"]:.1f}%') for r in rows]))

    if mode == 'DEEP':
        parts.append(html_p('<strong>Industry context:</strong> Indian pharmacies average 5-10% stockout rate. 75% of retailers experience frequent stockouts. 30-40% of customers switch to competitors after a stockout. Each stockout reduces return visit probability by ~9%. Industry target: under 3% (best-in-class under 2%).'))
        parts.append(html_p('<strong>Root causes:</strong> Manual tracking errors, vendor near-expiry dumps, no demand forecasting (most pharmacies use intuition), limited SKU capacity (6K-8K offline vs 50K+ online).'))

    parts.append(html_action('Increase safety stock on the top OOS products above. Set up automated reorder triggers. Use ABC-VED analysis: Category A items (14% of drugs, 70% of budget) need strict monitoring.'))
    parts.append(html_drilldowns([
        ('Slow Moving Stock', 'Show slow moving inventory'),
        ('By Store', 'Stockout rate by store'),
        ('Supply Chain', 'How does our supply chain work?'),
    ]))
    return ''.join(parts)


def h_delivery(_q='', mode='INSIGHTS'):
    if mode == 'BRIEF':
        return html_p(f'On-time delivery: <strong>{kpis["sla_compliance_pct"]:.1f}%</strong>. Average: {kpis["avg_delivery_days"]:.1f} days.')
    parts = [html_p(f'On-time delivery: <strong>{kpis["sla_compliance_pct"]:.1f}%</strong>, avg {kpis["avg_delivery_days"]:.1f} days.')]
    if mode == 'DEEP':
        rows = query_db("""SELECT delivery_days, COUNT(*) as cnt FROM orders
            WHERE channel='Online' AND status='Delivered' GROUP BY delivery_days ORDER BY delivery_days""")
        if isinstance(rows, list) and rows:
            fig, ax = plt.subplots(figsize=(7, 3.5))
            days = [r['delivery_days'] for r in rows]
            counts = [r['cnt'] for r in rows]
            colors = ['#81c784' if d <= 2 else '#e57373' for d in days]
            ax.bar([str(d) for d in days], counts, color=colors, edgecolor='white')
            ax.axvline(2.5, color='#ffb74d', linestyle='--', linewidth=2, label='SLA Threshold')
            ax.set_title(f'Delivery Distribution ({kpis["sla_compliance_pct"]:.1f}% on-time)', fontsize=11, fontweight='bold')
            ax.set_xlabel('Days')
            ax.legend(framealpha=0.3)
            ax.grid(axis='y', alpha=0.2)
            fig.tight_layout()
            parts.append(make_chart_img(fig, 'Delivery SLA'))
        parts.append(html_p('<strong>Industry context:</strong> Benchmark is 95%+ on-time. Quick commerce (Zepto, Blinkit) now delivers medicines in 10-19 minutes in metros. Apollo 24/7 does 19-minute delivery in 4 cities.'))
    parts.append(html_action(f'Focus on the {100-kpis["sla_compliance_pct"]:.1f}% of late deliveries — identify problem routes and peak-hour bottlenecks to push above 95%.'))
    return ''.join(parts)


def h_online(_q='', mode='INSIGHTS'):
    if mode == 'BRIEF':
        return html_p(f'Online share: <strong>{kpis["online_share_pct"]:.1f}%</strong> of revenue. Growing trend.')
    parts = [html_p(f'Online sales: <strong>{kpis["online_share_pct"]:.1f}%</strong> of revenue.')]
    if mode in ('INSIGHTS', 'DEEP'):
        parts.append(html_table(
            ['Metric', 'WF', 'Industry'],
            [('Online Revenue Share', f'{kpis["online_share_pct"]:.1f}%', '~25% market (growing 16% CAGR)'),
             ('E-pharmacy Market', '—', 'USD 3.18 Bn (2024), 16% CAGR'),
             ('Online Discounts', '—', '15-25% off MRP (standard)'),
             ('Medicine AOV (online)', '—', '₹1,000+ per order')]
        ))
    if mode == 'DEEP':
        parts.append(html_p('<strong>Industry context:</strong> E-pharmacy user penetration is 7.5% (2025). 73% of online pharmacy orders come via mobile apps. Tata 1mg leads with 31% online market share. Quick commerce (Zepto, Blinkit) entering pharmacy — OTC delivery in 10 minutes.'))
    parts.append(html_action('Significant room to grow digital. Consider WhatsApp ordering (most effective channel in India for pharmacy), chronic care auto-refill programs, and store-to-door delivery using existing locations as fulfillment points.'))
    return ''.join(parts)


def h_payments(_q='', mode='INSIGHTS'):
    rows = query_db("""SELECT payment_mode, COUNT(*) as cnt FROM orders WHERE status = 'Delivered'
        GROUP BY payment_mode ORDER BY cnt DESC""")
    if isinstance(rows, str):
        return html_p(rows)
    total = sum(r['cnt'] for r in rows)
    if mode == 'BRIEF':
        return html_p(f'Top payment: <strong>{rows[0]["payment_mode"]}</strong> ({rows[0]["cnt"]/total*100:.0f}% of orders).')
    parts = [html_p('Payment mode breakdown:')]
    parts.append(html_table(['Mode', 'Orders', 'Share'],
        [(r['payment_mode'], f'{r["cnt"]:,}', f'{r["cnt"]/total*100:.1f}%') for r in rows]))
    parts.append(html_p('UPI dominance reflects India\'s digital payments shift.'))
    return ''.join(parts)


def h_summary(_q='', mode='INSIGHTS'):
    if mode == 'BRIEF':
        return html_p(f'WF: {inr_label(kpis["total_revenue"])} revenue, +{kpis["yoy_growth_pct"]:.1f}% YoY, {kpis["overall_margin_pct"]:.1f}% margin, {kpis["leakage_pct"]:.1f}% leakage.')
    parts = [html_p('<strong>Wellness Forever — Big Picture</strong> (30 stores, 24 months):')]
    parts.append(html_table(
        ['KPI', 'Value', 'Status'],
        [('Total Revenue', inr_label(kpis['total_revenue']), ''),
         ('YoY Growth', f'+{kpis["yoy_growth_pct"]:.1f}%', '✓ Growing'),
         ('Orders Fulfilled', f'{kpis["total_delivered_orders"]:,}', ''),
         ('Profit Margin', f'{kpis["overall_margin_pct"]:.1f}%', '~Industry avg'),
         ('Revenue Leakage', f'{kpis["leakage_pct"]:.1f}%', '⚠ Fix'),
         ('Stockout Rate', f'{kpis["avg_oos_rate_pct"]:.1f}%', '⚠ Above 5% target'),
         ('On-Time Delivery', f'{kpis["sla_compliance_pct"]:.1f}%', '✓ Strong'),
         ('Customer Churn', f'{kpis["churn_rate_pct"]:.1f}%', '⚠ Monitor'),
         ('Online Share', f'{kpis["online_share_pct"]:.1f}%', 'Room to grow')]
    ))
    if mode == 'DEEP':
        parts.append(html_p('<strong>Industry context:</strong> India pharmacy retail is USD 24 Bn (2024), growing 10% CAGR. Organized chains hold ~8.5% share, projected 25-30% by 2030. WF is India\'s 3rd-largest chain (430+ stores, ₹1,570 Cr FY25 revenue). Key competitors: Apollo (6,360 stores), MedPlus (5,112 stores).'))
    parts.append(html_action('Business is growing steadily. Two priorities: (1) Plug revenue leakage — cancellations and stockouts are the biggest drains. (2) Grow online channel — currently below industry average.'))
    return ''.join(parts)


def h_aov(_q='', mode='INSIGHTS'):
    if mode == 'BRIEF':
        return html_p(f'Average order value: <strong>{inr_label(kpis["aov"])}</strong>.')
    parts = [html_p(f'AOV: <strong>{inr_label(kpis["aov"])}</strong> across {kpis["total_delivered_orders"]:,} delivered orders.')]
    if mode == 'DEEP':
        parts.append(html_table(
            ['Channel', 'AOV Benchmark'],
            [('Offline pharmacy', '₹200-500 (typical)'),
             ('Online pharmacy', '₹600-1,500'),
             ('WF (blended)', inr_label(kpis['aov']))]
        ))
    return ''.join(parts)


# === NEW COMPLEX HANDLERS ===

def h_seasonal_readiness(question, mode='INSIGHTS'):
    city = extract_city(question)
    season_name, months = extract_season(question)
    if not months:
        months = ('06', '07', '08')
        season_name = 'monsoon'
    month_clause = ' OR '.join([f"strftime('%m', o.order_date) = '{m}'" for m in months])
    city_clause = f"AND s.city = '{city}'" if city else ''
    location = f' in {city}' if city else ' across all stores'

    rows = query_db(f"""SELECT strftime('%Y', o.order_date) as year, SUM(li.line_total) as revenue,
        COUNT(DISTINCT o.order_id) as orders, COUNT(DISTINCT o.store_id) as stores
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
        JOIN stores s ON o.store_id = s.store_id
        WHERE o.status = 'Delivered' AND ({month_clause}) {city_clause} GROUP BY year ORDER BY year""")
    oos_rows = query_db(f"""SELECT AVG(i.is_out_of_stock)*100 as oos_rate FROM inventory i
        JOIN stores s ON i.store_id = s.store_id WHERE 1=1 {city_clause}""")
    oos_products = query_db(f"""SELECT p.product_name, p.category, AVG(i.is_out_of_stock)*100 as oos_rate
        FROM inventory i JOIN stores s ON i.store_id = s.store_id JOIN products p ON i.product_id = p.product_id
        WHERE 1=1 {city_clause} GROUP BY i.product_id HAVING oos_rate > 10 ORDER BY oos_rate DESC LIMIT 6""")

    if mode == 'BRIEF':
        oos = oos_rows[0]['oos_rate'] if isinstance(oos_rows, list) and oos_rows and oos_rows[0]['oos_rate'] else 0
        verdict = 'Not fully ready' if oos > 5 else 'Reasonably prepared'
        return html_p(f'<strong>{season_name.title()} readiness{location}: {verdict}.</strong> Stockout rate: {oos:.1f}% (target: &lt;5%).')

    parts = [html_p(f'<strong>{season_name.title()} readiness{location}:</strong>')]
    if isinstance(rows, list) and rows:
        parts.append(html_table(['Year', 'Revenue', 'Orders', 'Stores'],
            [(r['year'], inr_label(r['revenue']), f'{r["orders"]:,}', r['stores']) for r in rows]))
    if isinstance(oos_rows, list) and oos_rows and oos_rows[0]['oos_rate'] is not None:
        oos = oos_rows[0]['oos_rate']
        status = '⚠ Above target' if oos > 5 else '✓ Acceptable'
        parts.append(html_p(f'Current stockout rate{location}: <strong>{oos:.1f}%</strong> — {status} (target: &lt;5%)'))
    if isinstance(oos_products, list) and oos_products:
        parts.append(html_p(f'<strong>At-risk products:</strong>'))
        parts.append(html_table(['Product', 'Category', 'OOS Rate'],
            [(p['product_name'], p['category'], f'{p["oos_rate"]:.1f}%') for p in oos_products]))
    if mode == 'DEEP':
        season_map = {'monsoon': 'Respiratory, anti-infectives, anti-malarials, decongestants',
                      'summer': 'ORS, antidiarrheals, electrolytes, gastro',
                      'winter': 'Cold/flu remedies, cardiac drugs, respiratory',
                      'festive': 'Wellness, vitamins, supplements, dermatological'}
        expected = season_map.get(season_name, 'Various seasonal products')
        parts.append(html_p(f'<strong>Expected {season_name} demand categories:</strong> {expected}'))
        parts.append(html_p(f'<strong>Industry context:</strong> Monsoon months typically see a 15-20% revenue dip vs non-monsoon. Indian pharmacies lose 3-10% revenue annually from stockouts alone. 30-40% of customers switch pharmacies when they can\'t find their medicine.'))
    parts.append(html_action(f'(1) Increase safety stock on the {len(oos_products) if isinstance(oos_products, list) else 0} high-OOS products above — especially {season_name}-demand medicines. (2) Pre-position extra inventory before the season. (3) Brief delivery partners on contingency routes.'))
    return ''.join(parts)


def h_drug_interest(question, mode='INSIGHTS'):
    therapeutic = extract_therapeutic(question) or 'Anti-diabetic'
    city = extract_city(question)
    city_clause = f"AND s.city = '{city}'" if city else ''
    location = f' in {city}' if city else ''

    rows = query_db(f"""SELECT COUNT(DISTINCT p.product_id) as product_count, SUM(li.line_total) as revenue,
        COUNT(DISTINCT o.order_id) as orders, COUNT(DISTINCT o.customer_id) as unique_customers
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
        JOIN products p ON li.product_id = p.product_id JOIN stores s ON o.store_id = s.store_id
        WHERE o.status = 'Delivered' AND p.therapeutic_area = '{therapeutic}' {city_clause}""")
    top_prods = query_db(f"""SELECT p.product_name, p.brand, SUM(li.line_total) as revenue
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
        JOIN products p ON li.product_id = p.product_id JOIN stores s ON o.store_id = s.store_id
        WHERE o.status = 'Delivered' AND p.therapeutic_area = '{therapeutic}' {city_clause}
        GROUP BY li.product_id ORDER BY revenue DESC LIMIT 5""")

    if mode == 'BRIEF' and isinstance(rows, list) and rows and rows[0]['revenue']:
        r = rows[0]
        return html_p(f'<strong>{therapeutic}{location}:</strong> {inr_label(r["revenue"])} revenue, {r["orders"]:,} orders, {r["product_count"]} products.')

    parts = [html_p(f'<strong>{therapeutic} products{location}:</strong>')]
    if isinstance(rows, list) and rows and rows[0]['revenue']:
        r = rows[0]
        parts.append(html_table(['Metric', 'Value'],
            [('Products in catalog', r['product_count']), ('Total revenue', inr_label(r['revenue'])),
             ('Orders', f'{r["orders"]:,}'), ('Unique customers', f'{r["unique_customers"]:,}')]))
    if isinstance(top_prods, list) and top_prods:
        parts.append(html_p(f'<strong>Top {therapeutic} products:</strong>'))
        parts.append(html_table(['#', 'Product', 'Brand', 'Revenue'],
            [(i+1, p['product_name'], p['brand'], inr_label(p['revenue'])) for i, p in enumerate(top_prods)]))
    if mode == 'DEEP':
        parts.append(html_p(f'<strong>Industry context:</strong> Top therapeutic segments in India by turnover: Cardiac > Gastrointestinal > Anti-diabetic, with 8-9% volume growth. India has 77M diabetics — the chronic patient base is massive and growing. Chronic patients have CLV of ₹1.2L-12L.'))
    return ''.join(parts)


def h_stores_bleeding(question, mode='INSIGHTS'):
    city = extract_city(question)
    city_clause = f"AND s.city = '{city}'" if city else ''
    location = f' in {city}' if city else ''

    rows = query_db(f"""SELECT s.store_name, s.city,
        SUM(CASE WHEN o.status='Cancelled' THEN li.line_total ELSE 0 END) as cancel_loss,
        SUM(CASE WHEN o.status='Returned' THEN li.line_total ELSE 0 END) as return_loss,
        SUM(CASE WHEN o.status IN ('Cancelled','Returned') THEN li.line_total ELSE 0 END) as total_loss,
        COUNT(CASE WHEN o.status='Cancelled' THEN 1 END) as cancel_orders,
        COUNT(CASE WHEN o.status='Returned' THEN 1 END) as return_orders
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
        JOIN stores s ON o.store_id = s.store_id
        WHERE o.status IN ('Cancelled','Returned') {city_clause}
        GROUP BY o.store_id ORDER BY total_loss DESC LIMIT 10""")
    if isinstance(rows, str):
        return html_p(rows)
    if not rows:
        return html_p(f'No data found{location}.')

    if mode == 'BRIEF':
        return html_p(f'Top bleeding store{location}: <strong>{rows[0]["store_name"]}</strong> ({rows[0]["city"]}) — {inr_label(rows[0]["total_loss"])} lost.')

    total_lost = sum(r['total_loss'] for r in rows)
    parts = [html_p(f'<strong>Stores bleeding revenue{location}:</strong> {inr_label(total_lost)} total loss from top {len(rows)} stores.')]
    parts.append(html_table(
        ['Store', 'City', 'Cancellations', 'Returns', 'Total Loss'],
        [(r['store_name'], r['city'], f'{inr_label(r["cancel_loss"])} ({r["cancel_orders"]})',
          f'{inr_label(r["return_loss"])} ({r["return_orders"]})', inr_label(r['total_loss'])) for r in rows]
    ))

    if mode == 'DEEP':
        fig, ax = plt.subplots(figsize=(8, 4))
        names = [r['store_name'][:20] for r in rows[:8]]
        cancels = [r['cancel_loss'] for r in rows[:8]]
        returns = [r['return_loss'] for r in rows[:8]]
        y = range(len(names))
        ax.barh(y, cancels, color='#e57373', label='Cancellations', edgecolor='white', linewidth=0.3)
        ax.barh(y, returns, left=cancels, color='#ffb74d', label='Returns', edgecolor='white', linewidth=0.3)
        ax.set_yticks(y)
        ax.set_yticklabels(names, fontsize=8)
        ax.invert_yaxis()
        ax.set_title('Revenue Loss by Store', fontsize=11, fontweight='bold')
        ax.xaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
        ax.legend(framealpha=0.3, fontsize=9)
        ax.grid(axis='x', alpha=0.2)
        fig.tight_layout()
        parts.append(make_chart_img(fig, 'Revenue Loss by Store'))
        parts.append(html_p('<strong>Industry context:</strong> Pharmacy cancellation benchmark is under 3%. Return rate is 2-5% for pharmacy (vs 16.9% general e-commerce). Each lost customer costs 5-7x more to re-acquire.'))

    parts.append(html_action('Investigate cancellation reasons at the top 3 stores. Are they stock-related (unavailability), delivery-related, or customer-side? Targeted fixes at the top stores recover the most revenue fastest.'))
    top_city = rows[0]['city'] if rows else 'Mumbai'
    parts.append(html_drilldowns([
        (f'{top_city} Deep Dive', f'How are stores in {top_city} performing?'),
        ('Leakage Analysis', 'Where is revenue leaking?'),
        ('Cancellation Reasons', 'Why are orders being cancelled?'),
    ]))
    return ''.join(parts)


def h_slow_moving_stock(question, mode='INSIGHTS'):
    city = extract_city(question)
    city_clause = f"AND s.city = '{city}'" if city else ''
    location = f' in {city}' if city else ''

    rows = query_db(f"""SELECT p.product_name, p.brand, s.store_name, i.days_out_of_stock
        FROM inventory i JOIN stores s ON i.store_id = s.store_id
        JOIN products p ON i.product_id = p.product_id
        WHERE i.days_out_of_stock > 15 {city_clause}
        ORDER BY i.days_out_of_stock DESC LIMIT 10""")

    if mode == 'BRIEF':
        count = len(rows) if isinstance(rows, list) else 0
        return html_p(f'<strong>{count} products</strong>{location} have been out of stock for 15+ days — likely expiry/dead stock risk.')

    parts = [html_p(f'<strong>Inventory stagnation risk{location}:</strong>')]
    if isinstance(rows, list) and rows:
        parts.append(html_table(['Product', 'Brand', 'Store', 'Days OOS'],
            [(r['product_name'], r['brand'], r['store_name'], r['days_out_of_stock']) for r in rows]))
    if mode == 'DEEP':
        parts.append(html_p('<strong>Industry context:</strong> Indian pharmacies lose ₹20K-50K/month per store from expired stock. Industry benchmark: 3% of inventory value. Common causes: unpredictable demand, vendors dumping near-expiry goods, manual tracking, lack of FEFO (First Expiry First Out) discipline.'))
    parts.append(html_action('Run an expiry audit on slow-moving products. Consider clearance pricing or inter-store transfers. Implement FEFO discipline and automated expiry alerts.'))
    return ''.join(parts)


def h_day_of_week(question, mode='INSIGHTS'):
    city = extract_city(question)
    city_clause = f"JOIN stores s ON o.store_id = s.store_id WHERE s.city = '{city}' AND o.status = 'Delivered'" if city else "WHERE o.status = 'Delivered'"
    location = f' in {city}' if city else ''

    rows = query_db(f"""SELECT CAST(strftime('%w', o.order_date) AS INTEGER) as dow,
        SUM(li.line_total) as revenue, COUNT(DISTINCT o.order_id) as orders
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id {city_clause}
        GROUP BY dow ORDER BY revenue DESC""")
    if isinstance(rows, str):
        return html_p(rows)

    if mode == 'BRIEF' and rows:
        return html_p(f'Best day{location}: <strong>{DOW_NAMES[rows[0]["dow"]]}</strong> ({inr_label(rows[0]["revenue"])}). Slowest: {DOW_NAMES[rows[-1]["dow"]]}.')

    parts = [html_p(f'<strong>Revenue by day of week{location}:</strong>')]
    parts.append(html_table(['Day', 'Revenue', 'Orders'],
        [(DOW_NAMES[r['dow']], inr_label(r['revenue']), f'{r["orders"]:,}') for r in rows]))

    if mode == 'DEEP' and rows:
        fig, ax = plt.subplots(figsize=(7, 3.5))
        sorted_rows = sorted(rows, key=lambda r: r['dow'])
        days = [DOW_NAMES[r['dow']][:3] for r in sorted_rows]
        revs = [r['revenue'] for r in sorted_rows]
        ax.bar(days, revs, color=CHART_COLORS[:7], edgecolor='white')
        ax.set_title(f'Revenue by Day of Week{location}', fontsize=11, fontweight='bold')
        ax.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
        ax.grid(axis='y', alpha=0.2)
        fig.tight_layout()
        parts.append(make_chart_img(fig, 'Day of Week Revenue'))

    if rows:
        best = DOW_NAMES[rows[0]['dow']]
        worst = DOW_NAMES[rows[-1]['dow']]
        parts.append(html_action(f'Run promotions on {worst} (slowest day) to boost traffic. Ensure staffing and inventory are optimized for {best} (peak day).'))
    return ''.join(parts)


def h_store_city_performance(question, mode='INSIGHTS'):
    city = extract_city(question)
    if not city:
        return h_top_stores(question, mode)

    rows = query_db("""SELECT s.store_name, s.store_type, s.size_sqft,
        SUM(CASE WHEN o.status='Delivered' THEN li.line_total ELSE 0 END) as revenue,
        SUM(CASE WHEN o.status='Delivered' THEN li.margin_amount ELSE 0 END) as margin,
        COUNT(DISTINCT CASE WHEN o.status='Delivered' THEN o.order_id END) as orders,
        COUNT(DISTINCT CASE WHEN o.status='Cancelled' THEN o.order_id END) as cancellations
        FROM order_line_items li JOIN orders o ON li.order_id = o.order_id
        JOIN stores s ON o.store_id = s.store_id WHERE s.city = ?
        GROUP BY o.store_id ORDER BY revenue DESC""", (city,))
    if isinstance(rows, str):
        return html_p(rows)
    if not rows:
        return html_p(f'No stores found in {city}.')

    total_rev = sum(r['revenue'] for r in rows)
    if mode == 'BRIEF':
        return html_p(f'<strong>{city}:</strong> {len(rows)} stores, {inr_label(total_rev)} total. Top: {rows[0]["store_name"]} ({inr_label(rows[0]["revenue"])}).')

    parts = [html_p(f'<strong>{city}</strong> — {len(rows)} stores, {inr_label(total_rev)} total revenue:')]
    table_rows = []
    for r in rows:
        margin_pct = r['margin'] / r['revenue'] * 100 if r['revenue'] > 0 else 0
        cancel_pct = r['cancellations'] / (r['orders'] + r['cancellations']) * 100 if (r['orders'] + r['cancellations']) > 0 else 0
        table_rows.append((r['store_name'], r['store_type'], f'{r["size_sqft"]:,} sqft',
            inr_label(r['revenue']), f'{margin_pct:.1f}%', f'{cancel_pct:.1f}%'))
    parts.append(html_table(['Store', 'Type', 'Size', 'Revenue', 'Margin', 'Cancel %'], table_rows))
    if mode == 'DEEP':
        parts.append(html_p(f'<strong>Industry context:</strong> Tier 1 city store should earn ₹12-15 L/month. Revenue per sqft for organized chains: ₹20K-60K/year. Wellness Forever averages ₹30 L/month per store.'))
    return ''.join(parts)


# === MEMORY HANDLERS ===

def h_session_history(_q='', mode='INSIGHTS'):
    """Show recent conversation history."""
    entries = read_log_entries(20)
    if not entries:
        return html_p('No conversation history yet. Start asking questions and I\'ll remember them!')

    parts = [html_p(f'<strong>Recent conversation history</strong> ({len(entries)} entries):')]
    table_rows = []
    for e in reversed(entries):
        ts = e.get('ts', '?')[:16].replace('T', ' ')
        query = e.get('query', '?')
        if len(query) > 60:
            query = query[:57] + '...'
        handler = e.get('handler') or '<em>unmatched</em>'
        cached = 'Yes' if e.get('cached') else ''
        table_rows.append((ts, query, handler, cached))
    parts.append(html_table(['Time', 'Question', 'Handler', 'Cached'], table_rows))

    # Stats
    total = len(entries)
    cached_count = sum(1 for e in entries if e.get('cached'))
    unmatched = sum(1 for e in entries if not e.get('handler'))
    parts.append(html_p(f'<strong>Stats:</strong> {total} queries, {cached_count} served from cache, {unmatched} unmatched (fallback).'))
    return ''.join(parts)


def h_popular_questions(_q='', mode='INSIGHTS'):
    """Show most popular question topics from conversation log."""
    entries = read_log_entries(500)
    if not entries:
        return html_p('No conversation data yet. As people ask questions, I\'ll track the most popular topics.')

    # Aggregate by handler
    handler_counts = {}
    unmatched_queries = []
    for e in entries:
        h = e.get('handler')
        if h:
            handler_counts[h] = handler_counts.get(h, 0) + 1
        else:
            unmatched_queries.append(e.get('query', '?'))

    parts = [html_p('<strong>Most popular topics:</strong>')]
    sorted_handlers = sorted(handler_counts.items(), key=lambda x: -x[1])[:10]
    parts.append(html_table(
        ['#', 'Topic', 'Times Asked'],
        [(i+1, h.replace('_', ' ').title(), count) for i, (h, count) in enumerate(sorted_handlers)]
    ))

    if unmatched_queries:
        parts.append(html_p(f'<strong>Unmatched queries ({len(unmatched_queries)}):</strong> These questions didn\'t match any handler — potential coverage gaps:'))
        for uq in unmatched_queries[-5:]:
            parts.append(html_p(f'&bull; <em>"{uq}"</em>'))

    return ''.join(parts)


def h_learned_insights(_q='', mode='INSIGHTS'):
    """Show accumulated learned insights."""
    data = load_insights()
    insights = data.get('insights', [])
    if not insights:
        return html_p('No learned insights yet. As I analyze data and answer complex questions, I\'ll accumulate intelligence here.')

    parts = [html_p(f'<strong>Accumulated Intelligence</strong> ({len(insights)} insights):')]
    table_rows = []
    for ins in insights:
        tags = ', '.join(ins.get('tags', []))
        refs = ins.get('referenced_count', 0)
        table_rows.append((ins['topic'], ins['summary'], tags, refs))
    parts.append(html_table(['Topic', 'Finding', 'Tags', 'References'], table_rows))

    parts.append(html_p('These insights are automatically applied when answering related questions, making future responses richer.'))
    return ''.join(parts)


HANDLERS = {
    'total_revenue': h_total_revenue,
    'yoy': h_yoy,
    'categories': h_categories,
    'city_revenue': h_city_revenue,
    'city_revenue_specific': h_city_revenue_specific,
    'top_stores': h_top_stores,
    'top_products': h_top_products,
    'top_brands': h_top_brands,
    'customers': h_customers,
    'churn': h_churn,
    'loyal_customers': h_loyal_customers,
    'margin': h_margin,
    'generic_branded': h_generic_branded,
    'leakage': h_leakage,
    'cancellations': h_cancellations,
    'returns': h_returns,
    'stockouts': h_stockouts,
    'delivery': h_delivery,
    'online': h_online,
    'payments': h_payments,
    'summary': h_summary,
    'aov': h_aov,
    # New complex handlers
    'seasonal_readiness': h_seasonal_readiness,
    'drug_interest': h_drug_interest,
    'stores_bleeding': h_stores_bleeding,
    'slow_moving_stock': h_slow_moving_stock,
    'day_of_week': h_day_of_week,
    'store_city_performance': h_store_city_performance,
    # Memory handlers
    'session_history': h_session_history,
    'popular_questions': h_popular_questions,
    'learned_insights': h_learned_insights,
}


def main():
    global _intent_index
    print("Tasknova Chatbot Agent started.")
    init_memory()
    print(f"  Memory system initialized (cache, log, insights)")

    # Initialize embedding-based intent routing
    if OLLAMA_AVAILABLE:
        try:
            _intent_index = build_intent_index()
            print("  Semantic routing ready (embedding similarity + regex fallback)")
        except Exception as e:
            print(f"  [warn] Embedding init failed: {e} — using regex routing only")
            _intent_index = None
    else:
        print("  Ollama not available — using regex routing only")

    print(f"Polling {QUERY_FILE} every {POLL_INTERVAL}s...")
    print("Press Ctrl+C to stop.\n")

    # Clean up any stale files
    if QUERY_FILE.exists():
        QUERY_FILE.unlink()
    if RESPONSE_FILE.exists():
        RESPONSE_FILE.unlink()

    while True:
        try:
            if QUERY_FILE.exists():
                question = QUERY_FILE.read_text(encoding='utf-8').strip()
                if question:
                    QUERY_FILE.unlink()
                    # Handle clear signal
                    if question == '[CLEAR]':
                        _session_context.update(last_question=None, last_handler=None, last_entities={})
                        if RESPONSE_FILE.exists():
                            RESPONSE_FILE.unlink()
                        print("[clear] Session context reset")
                    else:
                        print(f"[question] {question}")
                        mode, clean_question = parse_mode(question)
                        print(f"[mode] {mode}")
                        answer = find_answer(clean_question, mode)
                        RESPONSE_FILE.write_text(answer, encoding='utf-8')
                        print(f"[answer] {answer[:120]}...")
            time.sleep(POLL_INTERVAL)
        except KeyboardInterrupt:
            print("\nAgent stopped.")
            break
        except Exception as e:
            print(f"[error] {e}")
            time.sleep(POLL_INTERVAL)


if __name__ == '__main__':
    main()
