# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Tasknova (revai)** is a research and prototyping repository for an AI-powered Revenue Intelligence platform targeting B2B SaaS companies (India-focused). This is NOT a production SaaS codebase — it's a research lab containing product documentation, data science notebooks, and showcase generators.

## Chatbot Operations — IMPORTANT

When the user runs `/start-chatbot` or asks to start the chatbot:

1. **You ARE the answering engine.** The chatbot backend (`wf_chatbot_ws.py`) writes questions to `analysis/_pending_question.json` and polls for `analysis/_pending_answer.json`. This Claude session must monitor that file and write answers.
2. **Refresh cache on startup.** The response cache (`analysis/response_cache.json`) has a 2-hour TTL. Refresh all `cached_at` timestamps immediately so cached answers don't expire mid-session.
3. **Monitor proactively.** After starting the backend, poll `analysis/_pending_question.json` every ~10 seconds. Don't wait for the user to tell you a question arrived.
4. **Answer format**: Write `analysis/_pending_answer.json` with `{"response_html": "<div>...</div>", "chart_url": null, "tools_used": ["claude_session"]}`. HTML must use inline styles, Indian currency formatting (₹ Cr/L).

## Running Things

```bash
# Notebooks — run individually via Jupyter
jupyter notebook notebooks/01_callcenter_en_analysis.ipynb

# Showcase generation pipeline (run in order)
python _generate_charts.py          # Renders matplotlib charts → _all_charts.json
python _build_showcase.py           # Injects charts into HTML → insight-framework-showcase.html

# Executive variant
python _generate_exec_charts.py     # → _exec_charts.json
python _build_exec_showcase.py      # → pharma-executive-report.html

# Instacart package
python _build_instacart_zip.py      # → instacart-refill-intelligence.zip

# WF chatbot backend (requires .env with Pusher creds)
python wf_chatbot_ws.py

# WF pipeline: regenerate data → analyze → build dashboard
python data/generate_synthetic_data.py
python notebooks/20_wf_master_analysis.py
python _build_wf_dashboard.py
```

No package manager, no tests, no CI/CD. Python dependencies (pandas, numpy, matplotlib, seaborn, kagglehub, datasets, pusher, pysher, python-dotenv, requests) are managed manually. Notebooks may require `HF_TOKEN` env var and Kaggle API credentials.

### Environment Setup

Copy `.env.example` to `.env` and fill in Pusher credentials (PUSHER_APP_ID, PUSHER_KEY, PUSHER_SECRET). PUSHER_CLUSTER defaults to `ap2`. IMGBB_API_KEY is optional (chart image hosting).

## Architecture

### Showcase Generation Pipeline
```
Jupyter Notebooks → _generate_charts.py → _all_charts.json → _build_showcase.py → single-file HTML
```
Charts are rendered to base64-encoded PNGs, serialized to JSON, then embedded into self-contained HTML dashboards.

### WF Chatbot Backend (`wf_chatbot_ws.py`)

Real-time chatbot for Wellness Forever pharmacy revenue intelligence:
```
Vercel frontend → Pusher (wf-queries channel) → Python backend → Claude CLI subprocess → Pusher (wf-responses-{session}) → frontend
```

Key design decisions:
- **LLM routing**: All question answering via `claude` CLI subprocess (not Anthropic API). No API key needed — uses local Claude Code installation
- **Prompt delivery**: Writes prompt to `analysis/_prompt.txt` then pipes via `cat analysis/_prompt.txt | claude -p ...` to avoid Windows 8191 char argument limit
- **Data strategy**: Pre-computed data from `analysis/precomputed_data.json` (29 datasets) with dynamic relevance-mapped selection per question, 8K char budget cap
- **Caching**: MD5-keyed response cache in `analysis/response_cache.json` with keyword-similarity matching (overlap coefficient, 0.40 threshold) and 2-hour TTL
- **Knowledge base**: 6 domain files in `analysis/pharmacy_*.md` (revenue economics, supply chain, CRM, omnichannel, market landscape, retail KPI benchmarks)
- **Windows gotcha**: Requires `PYTHONIOENCODING=utf-8` and `env.pop('CLAUDECODE', None)` for nested Claude sessions

### Shared Utilities (`notebooks/insight_utils.py`)
Reusable analysis framework used across all notebooks:
- `detect_schema()` — auto-classifies DataFrame columns into semantic roles
- `pareto_analysis()` — 80/20 revenue concentration
- `rfm_segment()` — customer value lifecycle segmentation
- `detect_seasonality()` — time series pattern detection (STL decomposition)
- `detect_anomalies()` — Z-score and IQR methods
- `InsightCollector` — aggregates findings with narrative generation

### Key Document: Tasknova Bible
`Tn Bible 2026 v3.pdf` (300 pages) defines the full product vision. Summarized in `tn-bible-summary.md` with a navigable Q&A index in `tn-bible-index.md`.

### Synthetic Knowledge Base Pattern
`wf-intelligence-hub/wf-synthetic-brain.md` is a structured synthetic dataset (1,900 lines) designed to be uploaded to Claude.ai, turning it into a domain-expert AI for Wellness Forever pharmacy demos.

## Conventions

- Notebooks are numbered sequentially (`01_`, `02_`, etc.)
- Internal/temporary scripts are prefixed with underscore (`_build_showcase.py`, `_generate_charts.py`)
- Generated HTML dashboards are single-file, self-contained (all assets base64-embedded)
- Chart styling uses matplotlib dark theme with seaborn whitegrid
- Dataset licensing matters: Tier 1 (MIT/CC0) for commercial use, Tier 2 (CC-BY-NC) for research only
- Indian currency formatting: ₹ with Cr (crore = 10M) and L (lakh = 100K) suffixes — see `inr_fmt()` in `wf_chatbot_ws.py`

## WF Revenue Intelligence Agent

### Database & Pre-computed Insights

- **SQLite DB:** `data/wf_intelligence.db` — 6 tables, ~30 MB
- **Pre-computed insights:** `analysis/insights_narrative.md` (executive summary), `analysis/insights_summary.json` (structured data), `analysis/kpi_metrics.json` (flat KPIs)
- **Pre-computed query results:** `analysis/precomputed_data.json` — 29 named datasets used by chatbot
- **Dashboard:** `wf-revenue-intelligence-dashboard.html` (self-contained, 20 charts)

### Answering WF Questions

1. **First** check `analysis/insights_narrative.md` and `analysis/kpi_metrics.json` — most common questions are already answered
2. **If not found**, query `data/wf_intelligence.db` using Python + sqlite3
3. **For deeper analysis**, use functions from `notebooks/insight_utils.py`

### Database Schema

```sql
-- stores (30 rows): store_id, store_name, city, pincode, store_type, size_sqft, online_enabled, delivery_radius_km, opened_date
-- products (1K rows): product_id, product_name, brand, category, sub_type, therapeutic_area, is_generic, mrp, cost_price, margin_pct, requires_prescription, is_scheduled
-- customers (5K rows): customer_id, city, pincode, gender, age, registration_date, has_rx_upload, has_subscription, preferred_store, loyalty_tier
-- orders (52K rows): order_id, order_date, customer_id, store_id, channel, status, payment_mode, delivery_days, is_delayed, cancellation_reason, return_reason
-- order_line_items (152K rows): line_item_id, order_id, product_id, quantity, unit_price, discount_pct, line_total, cost_amount, margin_amount
-- inventory (78K rows): store_id, product_id, snapshot_date, stock_on_hand, reorder_point, is_out_of_stock, days_out_of_stock
```

### Common Query Patterns

All revenue queries filter on `o.status = 'Delivered'`. Key joins:

```sql
-- Revenue with product details
SELECT ... FROM order_line_items li
  JOIN orders o ON li.order_id = o.order_id
  JOIN products p ON li.product_id = p.product_id
WHERE o.status = 'Delivered'

-- Store performance
SELECT ... FROM orders o JOIN stores s ON o.store_id = s.store_id

-- Monthly trends
SELECT strftime('%Y-%m', o.order_date) as month, SUM(li.line_total) as revenue ...

-- Margin analysis
SUM(li.margin_amount) / SUM(li.line_total) * 100 as margin_pct

-- OOS rate by store
SELECT s.store_name, AVG(i.is_out_of_stock) * 100 as oos_rate
FROM inventory i JOIN stores s ON i.store_id = s.store_id GROUP BY i.store_id
```

See full example queries in `_build_answer.py` and `analysis/precomputed_data.json`.
