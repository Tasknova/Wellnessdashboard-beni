# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Tasknova (revai)** is a research and prototyping repository for an AI-powered Revenue Intelligence platform targeting B2B SaaS companies (India-focused). This is NOT a production SaaS codebase — it's a research lab containing product documentation, data science notebooks, and showcase generators.

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
```

No package manager, no tests, no CI/CD. Python dependencies (pandas, numpy, matplotlib, seaborn, kagglehub, datasets) are managed manually. Notebooks may require `HF_TOKEN` env var and Kaggle API credentials.

## Architecture

### Showcase Generation Pipeline
```
Jupyter Notebooks → _generate_charts.py → _all_charts.json → _build_showcase.py → single-file HTML
```
Charts are rendered to base64-encoded PNGs, serialized to JSON, then embedded into self-contained HTML dashboards.

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

## WF Revenue Intelligence Agent

### Database & Pre-computed Insights

- **SQLite DB:** `data/wf_intelligence.db` — 6 tables, ~30 MB
- **Pre-computed insights:** `analysis/insights_narrative.md` (executive summary), `analysis/insights_summary.json` (structured data), `analysis/kpi_metrics.json` (flat KPIs)
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

### Example Queries

```sql
-- Total revenue
SELECT SUM(li.line_total) FROM order_line_items li JOIN orders o ON li.order_id = o.order_id WHERE o.status = 'Delivered';

-- Revenue by category
SELECT p.category, SUM(li.line_total) as revenue FROM order_line_items li JOIN orders o ON li.order_id = o.order_id JOIN products p ON li.product_id = p.product_id WHERE o.status = 'Delivered' GROUP BY p.category ORDER BY revenue DESC;

-- Monthly revenue trend
SELECT strftime('%Y-%m', o.order_date) as month, SUM(li.line_total) as revenue FROM order_line_items li JOIN orders o ON li.order_id = o.order_id WHERE o.status = 'Delivered' GROUP BY month ORDER BY month;

-- Top 10 products by revenue
SELECT p.product_name, p.brand, SUM(li.line_total) as revenue FROM order_line_items li JOIN orders o ON li.order_id = o.order_id JOIN products p ON li.product_id = p.product_id WHERE o.status = 'Delivered' GROUP BY li.product_id ORDER BY revenue DESC LIMIT 10;

-- Store with highest cancellation rate
SELECT s.store_name, s.city, COUNT(CASE WHEN o.status = 'Cancelled' THEN 1 END) * 100.0 / COUNT(*) as cancel_rate FROM orders o JOIN stores s ON o.store_id = s.store_id GROUP BY o.store_id ORDER BY cancel_rate DESC LIMIT 5;

-- Customer RFM: top spenders
SELECT customer_id, COUNT(DISTINCT order_id) as frequency, SUM(li.line_total) as monetary FROM order_line_items li JOIN orders o ON li.order_id = o.order_id WHERE o.status = 'Delivered' GROUP BY customer_id ORDER BY monetary DESC LIMIT 10;

-- OOS rate by store
SELECT s.store_name, AVG(i.is_out_of_stock) * 100 as oos_rate FROM inventory i JOIN stores s ON i.store_id = s.store_id GROUP BY i.store_id ORDER BY oos_rate DESC;

-- Online vs Offline revenue
SELECT o.channel, SUM(li.line_total) as revenue FROM order_line_items li JOIN orders o ON li.order_id = o.order_id WHERE o.status = 'Delivered' GROUP BY o.channel;

-- Delivery delay analysis
SELECT delivery_days, COUNT(*) as orders FROM orders WHERE channel = 'Online' AND status = 'Delivered' GROUP BY delivery_days ORDER BY delivery_days;

-- Generic vs branded margin
SELECT CASE WHEN p.is_generic = 1 THEN 'Generic' ELSE 'Branded' END as type, SUM(li.margin_amount) / SUM(li.line_total) * 100 as margin_pct FROM order_line_items li JOIN orders o ON li.order_id = o.order_id JOIN products p ON li.product_id = p.product_id WHERE o.status = 'Delivered' GROUP BY type;
```

### Running the Pipeline

```bash
# Regenerate synthetic data
python data/generate_synthetic_data.py

# Re-run analysis
python notebooks/20_wf_master_analysis.py

# Rebuild dashboard
python _build_wf_dashboard.py
```
