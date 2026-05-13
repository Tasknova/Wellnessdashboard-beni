# Tasknova — WF Revenue Intelligence

AI-powered Revenue Intelligence platform for Wellness Forever pharmacy chain. Claude Code acts as the live analysis engine — querying a SQLite database, generating insights, and serving responses through a real-time chatbot dashboard.

## Architecture

```
User (browser) → Dashboard (HTML) → HTTP Server (Python) → chatbot_query.txt
                                                                 ↓
Claude Code reads query → queries SQLite DB → writes HTML → chatbot_response.txt
                                                                 ↓
Dashboard polls /response → renders answer ← HTTP Server reads file
```

## Quick Start

```bash
# 1. Start the HTTP server (serves dashboard + bridges chatbot)
python _wf_chatbot_server.py

# 2. Open browser to http://localhost:8765

# 3. In Claude Code, start the watcher loop
python _wf_chatbot_watcher.py
```

Claude Code reads the question from `chatbot_query.txt`, runs SQL analysis against `data/wf_intelligence.db`, and writes the HTML response to `chatbot_response.txt`.

## Project Structure

```
├── _wf_chatbot_server.py          # HTTP server (port 8765) — serves dashboard + query/response bridge
├── _wf_chatbot_watcher.py         # File poller — watches for new chatbot queries
├── _build_wf_dashboard.py         # Dashboard HTML generator (rebuilds the dashboard)
├── wf-revenue-intelligence-dashboard.html  # Self-contained dashboard (20 charts + chatbot)
├── wf-synthetic-brain.md           # Structured synthetic knowledge base (1,900 lines)
├── inventory-intelligence-report.txt  # Sample comprehensive analysis output
├── CLAUDE.md                       # Claude Code project instructions
│
├── data/
│   ├── wf_intelligence.db         # SQLite database (30 stores, 1K products, 52K orders)
│   ├── generate_synthetic_data.py # Regenerate synthetic data
│   └── *.csv                      # Raw CSV exports
│
├── analysis/
│   ├── insights_narrative.md      # Pre-computed executive summary
│   ├── kpi_metrics.json           # Flat KPIs (revenue, margin, churn, etc.)
│   ├── insights_summary.json      # Structured analysis data
│   ├── saved_analyses.json        # Persisted SQL workflows from chatbot sessions
│   ├── conversation_log.jsonl     # All chatbot Q&A history
│   └── pharmacy_*.md              # Domain knowledge documents
│
└── notebooks/
    ├── 20_wf_master_analysis.ipynb # Master analysis notebook
    ├── 20_wf_master_analysis.py    # Script version
    └── insight_utils.py            # Reusable analysis framework
```

## Database Schema

```sql
stores (30 rows)        — store_id, store_name, city, pincode, store_type, size_sqft
products (1K rows)      — product_id, product_name, brand, category, therapeutic_area, mrp, margin_pct
customers (5K rows)     — customer_id, city, gender, age, loyalty_tier
orders (52K rows)       — order_id, order_date, customer_id, store_id, channel, status
order_line_items (152K) — line_item_id, order_id, product_id, quantity, line_total, margin_amount
inventory (78K rows)    — store_id, product_id, stock_on_hand, is_out_of_stock
```

## Key Metrics

| Metric | Value |
|--------|-------|
| Total Revenue | Rs 78.67 Cr |
| YoY Growth | 11.05% |
| Overall Margin | 25.38% |
| Avg OOS Rate | 6.14% |
| Online Share | 30.18% |

## Dependencies

Python 3.10+, sqlite3 (built-in). No external packages needed for the chatbot server.

For notebooks: `pandas`, `numpy`, `matplotlib`, `seaborn`
