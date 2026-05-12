"""
Tasknova — WF Master Analysis
==============================
Comprehensive analysis of WF synthetic data across Descriptive, Predictive, and Strategic layers.
Outputs: insights_summary.json, kpi_metrics.json, insights_narrative.md

Run: python notebooks/20_wf_master_analysis.py
"""

import pandas as pd
import numpy as np
import sqlite3
import json
import os
import sys
from pathlib import Path
from datetime import datetime, timedelta

sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, str(Path(__file__).parent))
from insight_utils import (
    pareto_analysis, revenue_trend, compute_rfm, detect_anomalies_iqr,
    generate_trend_narrative, generate_pareto_narrative, generate_rfm_narrative,
    InsightCollector
)

ROOT = Path(__file__).parent.parent
DATA_DIR = ROOT / 'data'
ANALYSIS_DIR = ROOT / 'analysis'
DB_PATH = DATA_DIR / 'wf_intelligence.db'

ANALYSIS_DIR.mkdir(exist_ok=True)

# INR formatting
def inr(val):
    if abs(val) >= 1e7:
        return f"INR {val/1e7:.2f} Cr"
    elif abs(val) >= 1e5:
        return f"INR {val/1e5:.2f} L"
    elif abs(val) >= 1e3:
        return f"INR {val/1e3:.1f}K"
    else:
        return f"INR {val:.0f}"

def pct(val):
    return f"{val:.1f}%"


# =============================================================================
# LOAD DATA
# =============================================================================

def load_data():
    print("Loading data from SQLite...")
    conn = sqlite3.connect(str(DB_PATH))
    stores = pd.read_sql('SELECT * FROM stores', conn)
    products = pd.read_sql('SELECT * FROM products', conn)
    customers = pd.read_sql('SELECT * FROM customers', conn)
    orders = pd.read_sql('SELECT * FROM orders', conn)
    items = pd.read_sql('SELECT * FROM order_line_items', conn)
    inventory = pd.read_sql('SELECT * FROM inventory', conn)
    conn.close()

    orders['order_date'] = pd.to_datetime(orders['order_date'])
    orders['order_month'] = orders['order_date'].dt.to_period('M').astype(str)
    orders['order_week'] = orders['order_date'].dt.to_period('W').astype(str)

    # Merge items with products and orders
    items_full = items.merge(products[['product_id', 'category', 'brand', 'is_generic',
                                        'therapeutic_area', 'requires_prescription']], on='product_id')
    items_full = items_full.merge(orders[['order_id', 'order_date', 'order_month',
                                           'customer_id', 'store_id', 'channel', 'status']], on='order_id')

    print(f"  Loaded: {len(orders):,} orders, {len(items):,} line items")
    return stores, products, customers, orders, items, items_full, inventory


# =============================================================================
# DESCRIPTIVE LAYER
# =============================================================================

def descriptive_analysis(stores, products, customers, orders, items, items_full, collector):
    print("\n=== DESCRIPTIVE ANALYSIS ===")
    results = {}

    # --- Revenue trends ---
    delivered = items_full[items_full['status'] == 'Delivered'].copy()
    monthly_rev = delivered.groupby('order_month')['line_total'].sum().reset_index()
    monthly_rev.columns = ['period', 'revenue']
    monthly_rev['growth_pct'] = monthly_rev['revenue'].pct_change() * 100
    results['monthly_revenue'] = monthly_rev.to_dict('records')

    total_rev = delivered['line_total'].sum()
    total_orders = orders[orders['status'] == 'Delivered'].shape[0]
    aov = total_rev / total_orders if total_orders > 0 else 0

    # YoY: FY25 (May24-Apr25) vs FY26 (May25-Apr26)
    delivered['fy'] = delivered['order_date'].apply(
        lambda d: 'FY25' if d < datetime(2025, 5, 1) else 'FY26'
    )
    fy_rev = delivered.groupby('fy')['line_total'].sum()
    fy25 = fy_rev.get('FY25', 0)
    fy26 = fy_rev.get('FY26', 0)
    yoy_growth = (fy26 - fy25) / fy25 * 100 if fy25 > 0 else 0

    results['revenue_summary'] = {
        'total_revenue': total_rev,
        'fy25_revenue': fy25,
        'fy26_revenue': fy26,
        'yoy_growth_pct': yoy_growth,
        'total_delivered_orders': int(total_orders),
        'aov': aov,
    }

    narrative = generate_trend_narrative(monthly_rev)
    collector.add('Revenue', 'Revenue Trend', narrative, 'info',
                  {'total': total_rev, 'yoy': yoy_growth})

    # --- Category analysis ---
    cat_rev = delivered.groupby('category').agg(
        revenue=('line_total', 'sum'),
        orders=('order_id', 'nunique'),
        items=('line_item_id', 'count'),
        margin=('margin_amount', 'sum'),
    ).reset_index()
    cat_rev['revenue_pct'] = cat_rev['revenue'] / cat_rev['revenue'].sum() * 100
    cat_rev['margin_pct'] = cat_rev['margin'] / cat_rev['revenue'] * 100
    cat_rev = cat_rev.sort_values('revenue', ascending=False)
    results['category_analysis'] = cat_rev.to_dict('records')

    top_cat = cat_rev.iloc[0]
    collector.add('Revenue', 'Category Dominance',
                  f"{top_cat['category']} leads with {pct(top_cat['revenue_pct'])} of revenue "
                  f"({inr(top_cat['revenue'])}), margin {pct(top_cat['margin_pct'])}.",
                  'info')

    # --- Product Pareto ---
    prod_rev = delivered.groupby('product_id')['line_total'].sum()
    pareto_df, n_80, pct_80 = pareto_analysis(prod_rev, 'product_id')
    results['product_pareto'] = {'n_80': int(n_80), 'pct_80': float(pct_80),
                                  'total_products': len(prod_rev)}
    narrative = generate_pareto_narrative(n_80, pct_80, len(prod_rev), 'products')
    collector.add('Products', 'Product Concentration', narrative,
                  'warning' if pct_80 < 25 else 'info')

    # --- Brand rankings ---
    brand_rev = delivered.groupby('brand')['line_total'].sum().sort_values(ascending=False)
    results['top_brands'] = [{'brand': b, 'revenue': float(r)} for b, r in brand_rev.head(15).items()]

    # --- Store performance ---
    store_rev = delivered.groupby('store_id').agg(
        revenue=('line_total', 'sum'),
        orders=('order_id', 'nunique'),
        margin=('margin_amount', 'sum'),
    ).reset_index()
    store_rev = store_rev.merge(stores[['store_id', 'store_name', 'city', 'store_type']], on='store_id')
    store_rev['margin_pct'] = store_rev['margin'] / store_rev['revenue'] * 100
    store_rev = store_rev.sort_values('revenue', ascending=False)
    results['store_performance'] = store_rev.to_dict('records')

    # City revenue
    city_rev = store_rev.groupby('city').agg(
        revenue=('revenue', 'sum'),
        stores=('store_id', 'count'),
    ).reset_index()
    city_rev['rev_per_store'] = city_rev['revenue'] / city_rev['stores']
    city_rev = city_rev.sort_values('revenue', ascending=False)
    results['city_revenue'] = city_rev.to_dict('records')

    # Store type comparison
    type_rev = store_rev.groupby('store_type').agg(
        revenue=('revenue', 'sum'),
        stores=('store_id', 'count'),
        margin_pct=('margin_pct', 'mean'),
    ).reset_index()
    type_rev['rev_per_store'] = type_rev['revenue'] / type_rev['stores']
    results['store_type_comparison'] = type_rev.to_dict('records')

    # --- Channel mix ---
    channel_rev = delivered.groupby('channel')['line_total'].sum()
    online_share = channel_rev.get('Online', 0) / channel_rev.sum() * 100
    results['channel_mix'] = {
        'online_revenue': float(channel_rev.get('Online', 0)),
        'offline_revenue': float(channel_rev.get('Offline', 0)),
        'online_share_pct': float(online_share),
    }

    # Monthly channel trend
    channel_monthly = delivered.groupby(['order_month', 'channel'])['line_total'].sum().unstack(fill_value=0)
    if 'Online' in channel_monthly.columns:
        channel_monthly['online_pct'] = channel_monthly['Online'] / (channel_monthly['Online'] + channel_monthly.get('Offline', 0)) * 100
        results['channel_trend'] = channel_monthly.reset_index().to_dict('records')

    # --- Payment modes ---
    payment_dist = orders[orders['status'] == 'Delivered']['payment_mode'].value_counts()
    results['payment_modes'] = [{'mode': m, 'count': int(c)} for m, c in payment_dist.items()]

    # --- Rx vs OTC + Generic vs Branded ---
    rx_rev = delivered[delivered['requires_prescription'] == True]['line_total'].sum()
    non_rx_rev = delivered[delivered['requires_prescription'] == False]['line_total'].sum()
    results['rx_vs_otc'] = {
        'rx_revenue': float(rx_rev),
        'non_rx_revenue': float(non_rx_rev),
        'rx_share_pct': float(rx_rev / total_rev * 100),
    }

    generic_items = delivered[delivered['is_generic'] == True]
    branded_items = delivered[delivered['is_generic'] == False]
    if len(generic_items) > 0:
        generic_margin = generic_items['margin_amount'].sum() / generic_items['line_total'].sum() * 100
    else:
        generic_margin = 0
    branded_margin = branded_items['margin_amount'].sum() / branded_items['line_total'].sum() * 100
    results['generic_vs_branded'] = {
        'generic_revenue': float(generic_items['line_total'].sum()),
        'branded_revenue': float(branded_items['line_total'].sum()),
        'generic_margin_pct': float(generic_margin),
        'branded_margin_pct': float(branded_margin),
    }

    collector.add('Products', 'Generic Opportunity',
                  f"Generic products show {pct(generic_margin)} margin vs branded {pct(branded_margin)}. "
                  f"Increasing generic share could improve overall margins.",
                  'opportunity')

    print("  Descriptive analysis complete.")
    return results


# =============================================================================
# PREDICTIVE LAYER
# =============================================================================

def predictive_analysis(stores, products, customers, orders, items, items_full, collector):
    print("\n=== PREDICTIVE ANALYSIS ===")
    results = {}

    delivered = items_full[items_full['status'] == 'Delivered'].copy()

    # --- RFM Segmentation ---
    order_customer_rev = delivered.groupby(['order_id', 'customer_id', 'order_date']).agg(
        revenue=('line_total', 'sum')
    ).reset_index()

    rfm = compute_rfm(order_customer_rev, 'customer_id', 'order_date', 'revenue')
    seg_dist = rfm['segment'].value_counts()
    seg_pct = (seg_dist / len(rfm) * 100).to_dict()
    results['rfm_segments'] = {seg: {'count': int(cnt), 'pct': float(seg_pct.get(seg, 0))}
                                for seg, cnt in seg_dist.items()}

    # CLV by segment
    seg_clv = rfm.groupby('segment')['monetary'].agg(['mean', 'median', 'sum'])
    results['clv_by_segment'] = seg_clv.reset_index().to_dict('records')

    narrative = generate_rfm_narrative(rfm)
    collector.add('Customers', 'Customer Segmentation', narrative, 'info')

    # --- Churn signals ---
    churn_threshold = 90  # days
    at_risk = rfm[rfm['recency'] > churn_threshold]
    churn_rate = len(at_risk) / len(rfm) * 100
    at_risk_revenue = at_risk['monetary'].sum()
    results['churn_signals'] = {
        'at_risk_customers': int(len(at_risk)),
        'churn_rate_pct': float(churn_rate),
        'at_risk_revenue': float(at_risk_revenue),
    }

    if churn_rate > 20:
        collector.add('Customers', 'Churn Risk',
                      f"{pct(churn_rate)} of customers haven't ordered in 90+ days, "
                      f"putting {inr(at_risk_revenue)} in annual revenue at risk.",
                      'risk')

    # --- Retention cohorts ---
    order_dates = orders[orders['status'] == 'Delivered'][['customer_id', 'order_date']].copy()
    order_dates['cohort'] = order_dates.groupby('customer_id')['order_date'].transform('min').dt.to_period('M')
    order_dates['order_period'] = order_dates['order_date'].dt.to_period('M')
    order_dates['period_offset'] = (order_dates['order_period'] - order_dates['cohort']).apply(lambda x: x.n)

    cohort_data = order_dates.groupby(['cohort', 'period_offset'])['customer_id'].nunique().reset_index()
    cohort_data.columns = ['cohort', 'period_offset', 'customers']
    cohort_pivot = cohort_data.pivot(index='cohort', columns='period_offset', values='customers').fillna(0)

    # Retention rates
    if 0 in cohort_pivot.columns:
        retention = cohort_pivot.div(cohort_pivot[0], axis=0) * 100
        # Take first 12 cohorts and first 12 periods for heatmap
        retention_summary = retention.iloc[:12, :12]
        results['retention_cohorts'] = {
            'cohorts': [str(c) for c in retention_summary.index],
            'periods': [int(p) for p in retention_summary.columns],
            'rates': retention_summary.values.tolist(),
        }

    # --- Subscription/refill prediction ---
    rx_customers = customers[customers['has_rx_upload'] == True]
    sub_customers = customers[customers['has_subscription'] == True]
    results['subscription_stats'] = {
        'rx_upload_customers': int(len(rx_customers)),
        'subscription_customers': int(len(sub_customers)),
        'rx_upload_pct': float(len(rx_customers) / len(customers) * 100),
        'subscription_pct': float(len(sub_customers) / len(customers) * 100),
    }

    # --- Anomaly detection on monthly revenue ---
    monthly = delivered.groupby('order_month')['line_total'].sum()
    anomalies = detect_anomalies_iqr(monthly)
    anomaly_months = monthly[anomalies]
    results['revenue_anomalies'] = [{'month': str(m), 'revenue': float(r)}
                                     for m, r in anomaly_months.items()]

    if len(anomaly_months) > 0:
        collector.add('Revenue', 'Revenue Anomalies',
                      f"Detected {len(anomaly_months)} anomalous months in revenue. "
                      f"Investigate for underlying causes.",
                      'warning')

    # --- Customer Pareto ---
    cust_rev = delivered.groupby('customer_id')['line_total'].sum()
    _, n_80_c, pct_80_c = pareto_analysis(cust_rev, 'customer_id')
    results['customer_pareto'] = {'n_80': int(n_80_c), 'pct_80': float(pct_80_c),
                                   'total_customers': int(len(cust_rev))}
    narrative = generate_pareto_narrative(n_80_c, pct_80_c, len(cust_rev), 'customers')
    collector.add('Customers', 'Customer Concentration', narrative,
                  'warning' if pct_80_c < 25 else 'info')

    print("  Predictive analysis complete.")
    return results


# =============================================================================
# STRATEGIC LAYER
# =============================================================================

def strategic_analysis(stores, products, customers, orders, items, items_full, inventory, collector):
    print("\n=== STRATEGIC ANALYSIS ===")
    results = {}

    delivered = items_full[items_full['status'] == 'Delivered'].copy()
    total_rev = delivered['line_total'].sum()

    # --- Revenue leakage waterfall ---
    cancelled = items_full[items_full['status'] == 'Cancelled']
    returned = items_full[items_full['status'] == 'Returned']
    cancel_loss = cancelled['line_total'].sum()
    return_loss = returned['line_total'].sum()

    # Stockout loss estimation: OOS rate × potential daily revenue
    oos_rate = inventory['is_out_of_stock'].mean()
    daily_rev = total_rev / 730  # 2 years
    stockout_loss = oos_rate * daily_rev * 730 * 0.5  # 50% of OOS translates to lost sales

    # Delay-related churn loss
    delayed_orders = orders[orders['is_delayed'] == True]
    delay_loss = delayed_orders.shape[0] * (total_rev / orders[orders['status'] == 'Delivered'].shape[0]) * 0.1

    gross_potential = total_rev + cancel_loss + return_loss + stockout_loss + delay_loss
    results['revenue_leakage'] = {
        'gross_potential': float(gross_potential),
        'delivered_revenue': float(total_rev),
        'cancellation_loss': float(cancel_loss),
        'return_loss': float(return_loss),
        'stockout_loss': float(stockout_loss),
        'delay_loss': float(delay_loss),
        'total_leakage': float(cancel_loss + return_loss + stockout_loss + delay_loss),
        'leakage_pct': float((cancel_loss + return_loss + stockout_loss + delay_loss) / gross_potential * 100),
    }

    leakage_total = cancel_loss + return_loss + stockout_loss + delay_loss
    collector.add('Revenue', 'Revenue Leakage',
                  f"Total leakage: {inr(leakage_total)} ({pct(leakage_total/gross_potential*100)} of potential). "
                  f"Cancellations: {inr(cancel_loss)}, Returns: {inr(return_loss)}, "
                  f"Stockouts: {inr(stockout_loss)}, Delays: {inr(delay_loss)}.",
                  'risk')

    # Cancellation reasons
    cancel_reasons = orders[orders['status'] == 'Cancelled']['cancellation_reason'].value_counts()
    results['cancellation_reasons'] = [{'reason': r, 'count': int(c)} for r, c in cancel_reasons.items()]

    # Return reasons
    return_reasons = orders[orders['status'] == 'Returned']['return_reason'].value_counts()
    results['return_reasons'] = [{'reason': r, 'count': int(c)} for r, c in return_reasons.items()]

    # --- Margin optimization ---
    total_margin = delivered['margin_amount'].sum()
    overall_margin_pct = total_margin / total_rev * 100

    # Generic substitution opportunity
    branded_rx = delivered[(delivered['category'] == 'Rx Medicines') & (delivered['is_generic'] == False)]
    generic_rx = delivered[(delivered['category'] == 'Rx Medicines') & (delivered['is_generic'] == True)]
    branded_rx_margin = branded_rx['margin_amount'].sum() / branded_rx['line_total'].sum() * 100 if len(branded_rx) > 0 else 0
    generic_rx_margin = generic_rx['margin_amount'].sum() / generic_rx['line_total'].sum() * 100 if len(generic_rx) > 0 else 0

    # If 10% more branded converted to generic
    potential_margin_gain = branded_rx['line_total'].sum() * 0.10 * (generic_rx_margin - branded_rx_margin) / 100
    results['margin_optimization'] = {
        'overall_margin_pct': float(overall_margin_pct),
        'total_margin': float(total_margin),
        'branded_rx_margin_pct': float(branded_rx_margin),
        'generic_rx_margin_pct': float(generic_rx_margin),
        'generic_substitution_opportunity': float(potential_margin_gain),
    }

    collector.add('Products', 'Margin Optimization',
                  f"Overall margin: {pct(overall_margin_pct)}. Generic Rx margin ({pct(generic_rx_margin)}) "
                  f"vs branded Rx ({pct(branded_rx_margin)}). 10% generic substitution could add {inr(abs(potential_margin_gain))}.",
                  'opportunity')

    # --- Inventory optimization ---
    oos_by_product = inventory.groupby('product_id').agg(
        oos_rate=('is_out_of_stock', 'mean'),
        avg_days_oos=('days_out_of_stock', 'mean'),
    ).reset_index()
    oos_by_product = oos_by_product.merge(products[['product_id', 'product_name', 'category']], on='product_id')
    top_oos = oos_by_product.nlargest(20, 'oos_rate')
    results['top_stockout_products'] = top_oos.to_dict('records')

    oos_by_store = inventory.groupby('store_id').agg(
        oos_rate=('is_out_of_stock', 'mean'),
    ).reset_index()
    oos_by_store = oos_by_store.merge(stores[['store_id', 'store_name', 'city']], on='store_id')
    results['oos_by_store'] = oos_by_store.sort_values('oos_rate', ascending=False).to_dict('records')

    # Monthly OOS trend
    inventory['snapshot_month'] = pd.to_datetime(inventory['snapshot_date']).dt.to_period('M').astype(str)
    oos_trend = inventory.groupby('snapshot_month')['is_out_of_stock'].mean() * 100
    results['oos_trend'] = [{'month': m, 'oos_rate': float(r)} for m, r in oos_trend.items()]

    avg_oos = inventory['is_out_of_stock'].mean() * 100
    collector.add('Inventory', 'Stockout Rate',
                  f"Average OOS rate: {pct(avg_oos)}. "
                  f"Top stockout products need safety stock adjustments.",
                  'risk' if avg_oos > 5 else 'warning')

    # --- Store expansion scoring ---
    store_rev = delivered.groupby('store_id')['line_total'].sum().reset_index()
    store_rev.columns = ['store_id', 'revenue']
    store_rev = store_rev.merge(stores[['store_id', 'city', 'store_type', 'size_sqft']], on='store_id')
    store_rev['rev_per_sqft'] = store_rev['revenue'] / store_rev['size_sqft']
    results['store_expansion'] = store_rev.sort_values('rev_per_sqft', ascending=False).to_dict('records')

    # --- Delivery SLA compliance ---
    online_delivered = orders[(orders['channel'] == 'Online') & (orders['status'] == 'Delivered')]
    sla_compliance = (online_delivered['delivery_days'] <= 2).mean() * 100
    avg_delivery = online_delivered['delivery_days'].mean()
    results['delivery_sla'] = {
        'sla_compliance_pct': float(sla_compliance),
        'avg_delivery_days': float(avg_delivery),
        'delayed_orders': int(online_delivered['is_delayed'].sum()),
        'total_online_delivered': int(len(online_delivered)),
    }

    collector.add('Operations', 'Delivery SLA',
                  f"SLA compliance (<=2 days): {pct(sla_compliance)}. "
                  f"Average delivery: {avg_delivery:.1f} days. "
                  f"{int(online_delivered['is_delayed'].sum())} delayed orders.",
                  'warning' if sla_compliance < 85 else 'info')

    # --- Day of week pattern ---
    delivered['dow'] = delivered['order_date'].dt.day_name()
    dow_rev = delivered.groupby('dow')['line_total'].sum()
    dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    dow_rev = dow_rev.reindex(dow_order)
    results['day_of_week'] = [{'day': d, 'revenue': float(r)} for d, r in dow_rev.items()]

    print("  Strategic analysis complete.")
    return results


# =============================================================================
# KPI METRICS
# =============================================================================

def compute_kpis(desc, pred, strat):
    """Extract flat KPI values from analysis results."""
    kpis = {}

    # Revenue
    rs = desc['revenue_summary']
    kpis['total_revenue'] = rs['total_revenue']
    kpis['fy25_revenue'] = rs['fy25_revenue']
    kpis['fy26_revenue'] = rs['fy26_revenue']
    kpis['yoy_growth_pct'] = rs['yoy_growth_pct']
    kpis['aov'] = rs['aov']
    kpis['total_delivered_orders'] = rs['total_delivered_orders']

    # Channel
    kpis['online_share_pct'] = desc['channel_mix']['online_share_pct']

    # Margins
    kpis['overall_margin_pct'] = strat['margin_optimization']['overall_margin_pct']
    kpis['total_margin'] = strat['margin_optimization']['total_margin']

    # Leakage
    kpis['cancellation_loss'] = strat['revenue_leakage']['cancellation_loss']
    kpis['return_loss'] = strat['revenue_leakage']['return_loss']
    kpis['total_leakage'] = strat['revenue_leakage']['total_leakage']
    kpis['leakage_pct'] = strat['revenue_leakage']['leakage_pct']

    # Customers
    kpis['total_customers'] = pred['customer_pareto']['total_customers']
    kpis['churn_rate_pct'] = pred['churn_signals']['churn_rate_pct']
    kpis['at_risk_customers'] = pred['churn_signals']['at_risk_customers']

    # Inventory
    oos_rates = [x['oos_rate'] for x in strat['oos_trend']]
    kpis['avg_oos_rate_pct'] = float(np.mean(oos_rates)) if oos_rates else 0

    # Delivery
    kpis['sla_compliance_pct'] = strat['delivery_sla']['sla_compliance_pct']
    kpis['avg_delivery_days'] = strat['delivery_sla']['avg_delivery_days']

    # RFM
    for seg, data in pred['rfm_segments'].items():
        kpis[f'rfm_{seg.lower().replace(" ", "_")}_pct'] = data['pct']

    return kpis


# =============================================================================
# NARRATIVE GENERATION
# =============================================================================

def generate_narrative(kpis, desc, pred, strat, collector):
    """Generate executive narrative markdown."""
    lines = []
    lines.append("# WF Revenue Intelligence — Executive Summary\n")
    lines.append(f"*Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}*\n")
    lines.append(f"*Period: May 2024 – April 2026 (24 months)*\n")

    # Executive Summary
    lines.append("## Executive Summary\n")
    lines.append(f"Wellness Forever's 30-store sample generated **{inr(kpis['total_revenue'])}** in total revenue "
                 f"over 24 months (~{inr(kpis['total_revenue']/2)}/year). Year-over-year growth stands at "
                 f"**{kpis['yoy_growth_pct']:+.1f}%** (FY25→FY26). Average order value is **{inr(kpis['aov'])}** "
                 f"across **{kpis['total_delivered_orders']:,}** delivered orders.\n")

    # Revenue Intelligence
    lines.append("## Revenue Intelligence\n")
    lines.append(f"- **FY25 Revenue:** {inr(kpis['fy25_revenue'])}")
    lines.append(f"- **FY26 Revenue:** {inr(kpis['fy26_revenue'])}")
    lines.append(f"- **YoY Growth:** {kpis['yoy_growth_pct']:+.1f}%")
    lines.append(f"- **Online Share:** {kpis['online_share_pct']:.1f}%")
    lines.append(f"- **AOV:** {inr(kpis['aov'])}\n")

    # Category breakdown
    lines.append("### Category Revenue Mix\n")
    lines.append("| Category | Revenue | Share | Margin |")
    lines.append("|----------|---------|-------|--------|")
    for cat in desc['category_analysis']:
        lines.append(f"| {cat['category']} | {inr(cat['revenue'])} | {cat['revenue_pct']:.1f}% | {cat['margin_pct']:.1f}% |")
    lines.append("")

    # Customer Intelligence
    lines.append("## Customer Intelligence\n")
    lines.append(f"- **Active Customers:** {kpis['total_customers']:,}")
    lines.append(f"- **Churn Rate (90d):** {kpis['churn_rate_pct']:.1f}%")
    lines.append(f"- **At-Risk Customers:** {kpis['at_risk_customers']:,}\n")

    lines.append("### RFM Segments\n")
    lines.append("| Segment | Customers | Share |")
    lines.append("|---------|-----------|-------|")
    for seg, data in sorted(pred['rfm_segments'].items(), key=lambda x: -x[1]['count']):
        lines.append(f"| {seg} | {data['count']:,} | {data['pct']:.1f}% |")
    lines.append("")

    # Product Intelligence
    lines.append("## Product Intelligence\n")
    pp = desc['product_pareto']
    lines.append(f"- **Product Pareto:** Top {pp['n_80']} products ({pp['pct_80']:.1f}%) drive 80% of revenue")
    cp = pred['customer_pareto']
    lines.append(f"- **Customer Pareto:** Top {cp['n_80']} customers ({cp['pct_80']:.1f}%) drive 80% of revenue")
    gvb = desc['generic_vs_branded']
    lines.append(f"- **Generic Margin:** {gvb['generic_margin_pct']:.1f}% vs Branded: {gvb['branded_margin_pct']:.1f}%\n")

    # Top brands
    lines.append("### Top 10 Brands by Revenue\n")
    lines.append("| Brand | Revenue |")
    lines.append("|-------|---------|")
    for b in desc['top_brands'][:10]:
        lines.append(f"| {b['brand']} | {inr(b['revenue'])} |")
    lines.append("")

    # Revenue Leakage
    lines.append("## Revenue Leakage\n")
    rl = strat['revenue_leakage']
    lines.append(f"- **Total Leakage:** {inr(rl['total_leakage'])} ({rl['leakage_pct']:.1f}% of potential)")
    lines.append(f"  - Cancellations: {inr(rl['cancellation_loss'])}")
    lines.append(f"  - Returns: {inr(rl['return_loss'])}")
    lines.append(f"  - Stockouts: {inr(rl['stockout_loss'])}")
    lines.append(f"  - Delivery Delays: {inr(rl['delay_loss'])}\n")

    # Inventory Intelligence
    lines.append("## Inventory Intelligence\n")
    lines.append(f"- **Average OOS Rate:** {kpis['avg_oos_rate_pct']:.1f}%")
    lines.append(f"- **Stockout Revenue Impact:** {inr(rl['stockout_loss'])}\n")

    # Operational Intelligence
    lines.append("## Operational Intelligence\n")
    ds = strat['delivery_sla']
    lines.append(f"- **SLA Compliance (≤2 days):** {ds['sla_compliance_pct']:.1f}%")
    lines.append(f"- **Avg Delivery Time:** {ds['avg_delivery_days']:.1f} days")
    lines.append(f"- **Delayed Orders:** {ds['delayed_orders']:,}/{ds['total_online_delivered']:,}\n")

    # Margin
    lines.append("## Margin Analysis\n")
    mo = strat['margin_optimization']
    lines.append(f"- **Overall Margin:** {mo['overall_margin_pct']:.1f}%")
    lines.append(f"- **Total Margin:** {inr(mo['total_margin'])}")
    lines.append(f"- **Generic Substitution Opportunity:** {inr(abs(mo['generic_substitution_opportunity']))}\n")

    # Insights summary
    lines.append("## Key Insights\n")
    for ins in collector.insights:
        icon = {'info': 'ℹ️', 'warning': '⚠️', 'opportunity': '💡', 'risk': '🔴'}.get(ins['severity'], '')
        lines.append(f"- **{icon} {ins['title']}:** {ins['narrative']}")
    lines.append("")

    return "\n".join(lines)


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("TASKNOVA WF MASTER ANALYSIS")
    print("=" * 60)

    stores, products, customers, orders, items, items_full, inventory = load_data()
    collector = InsightCollector()

    desc = descriptive_analysis(stores, products, customers, orders, items, items_full, collector)
    pred = predictive_analysis(stores, products, customers, orders, items, items_full, collector)
    strat = strategic_analysis(stores, products, customers, orders, items, items_full, inventory, collector)

    kpis = compute_kpis(desc, pred, strat)

    # Save outputs
    print("\nSaving outputs...")

    # insights_summary.json
    all_results = {
        'descriptive': desc,
        'predictive': pred,
        'strategic': strat,
        'generated_at': datetime.now().isoformat(),
    }

    # Convert numpy types for JSON serialization
    def convert(obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, (np.bool_,)):
            return bool(obj)
        elif isinstance(obj, pd.Period):
            return str(obj)
        return obj

    with open(ANALYSIS_DIR / 'insights_summary.json', 'w', encoding='utf-8') as f:
        json.dump(all_results, f, default=convert, indent=2, ensure_ascii=False)
    print(f"  -> insights_summary.json ({(ANALYSIS_DIR / 'insights_summary.json').stat().st_size / 1024:.0f} KB)")

    # kpi_metrics.json
    with open(ANALYSIS_DIR / 'kpi_metrics.json', 'w', encoding='utf-8') as f:
        json.dump(kpis, f, default=convert, indent=2, ensure_ascii=False)
    print(f"  -> kpi_metrics.json")

    # insights_narrative.md
    narrative = generate_narrative(kpis, desc, pred, strat, collector)
    with open(ANALYSIS_DIR / 'insights_narrative.md', 'w', encoding='utf-8') as f:
        f.write(narrative)
    print(f"  -> insights_narrative.md")

    print("\n" + collector.summary())
    print("\nDone!")


if __name__ == '__main__':
    main()
