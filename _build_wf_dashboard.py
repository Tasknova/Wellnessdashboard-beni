"""
Tasknova — WF Revenue Intelligence Dashboard Builder
======================================================
Generates charts + assembles single-file HTML dashboard.
Reads from analysis/ JSON outputs and data/ SQLite DB.

Run: python _build_wf_dashboard.py
Output: wf-revenue-intelligence-dashboard.html
"""

import sys, json, io, base64, sqlite3
from datetime import datetime as _dt
import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as mticker
import seaborn as sns
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')

ROOT = Path(__file__).parent
DB_PATH = ROOT / 'data' / 'wf_intelligence.db'
ANALYSIS_DIR = ROOT / 'analysis'

# Load analysis outputs
with open(ANALYSIS_DIR / 'insights_summary.json', 'r', encoding='utf-8') as f:
    insights = json.load(f)
with open(ANALYSIS_DIR / 'kpi_metrics.json', 'r', encoding='utf-8') as f:
    kpis = json.load(f)

desc = insights['descriptive']
pred = insights['predictive']
strat = insights['strategic']

# =============================================================================
# CHART GENERATION
# =============================================================================

# Dark-themed chart style
plt.rcParams.update({
    'figure.facecolor': '#1a1a2e',
    'axes.facecolor': '#16213e',
    'axes.edgecolor': '#e0e0e0',
    'axes.labelcolor': '#e0e0e0',
    'text.color': '#e0e0e0',
    'xtick.color': '#e0e0e0',
    'ytick.color': '#e0e0e0',
    'grid.color': '#2a2a4a',
    'grid.alpha': 0.3,
    'font.family': 'sans-serif',
    'font.size': 11,
})

COLORS = ['#4fc3f7', '#81c784', '#ffb74d', '#e57373', '#ba68c8',
          '#4dd0e1', '#fff176', '#a1887f', '#90a4ae', '#f06292']


def fig_to_b64(fig) -> str:
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=130, bbox_inches='tight', facecolor=fig.get_facecolor())
    plt.close(fig)
    buf.seek(0)
    return base64.b64encode(buf.read()).decode('utf-8')


def inr_fmt(val, pos=None):
    if abs(val) >= 1e7:
        return f'₹{val/1e7:.1f}Cr'
    elif abs(val) >= 1e5:
        return f'₹{val/1e5:.1f}L'
    elif abs(val) >= 1e3:
        return f'₹{val/1e3:.0f}K'
    return f'₹{val:.0f}'


def inr_label(val):
    if abs(val) >= 1e7:
        return f'INR {val/1e7:.2f} Cr'
    elif abs(val) >= 1e5:
        return f'INR {val/1e5:.2f} L'
    return f'INR {val:,.0f}'


charts = {}
print("Generating charts...")


# --- 1. Monthly Revenue Trend ---
def chart_monthly_revenue():
    data = desc['monthly_revenue']
    df = pd.DataFrame(data)
    fig, ax1 = plt.subplots(figsize=(14, 5.5))
    ax1.fill_between(range(len(df)), df['revenue'], alpha=0.3, color='#4fc3f7')
    ax1.plot(range(len(df)), df['revenue'], 'o-', color='#4fc3f7', markersize=4, linewidth=2)
    ax1.set_ylabel('Revenue')
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax1.set_xticks(range(0, len(df), 2))
    ax1.set_xticklabels([df['period'].iloc[i][:7] for i in range(0, len(df), 2)], rotation=45, ha='right', fontsize=9)
    ax1.set_title('How Is Revenue Trending? (May 2024 – Apr 2026)', fontsize=14, fontweight='bold')
    ax1.grid(True, alpha=0.2)

    if 'growth_pct' in df.columns:
        ax2 = ax1.twinx()
        colors = ['#81c784' if g >= 0 else '#e57373' for g in df['growth_pct'].fillna(0)]
        ax2.bar(range(len(df)), df['growth_pct'].fillna(0), alpha=0.4, color=colors, width=0.6)
        ax2.set_ylabel('MoM Growth %', fontsize=10)
        ax2.axhline(0, color='#e0e0e0', linestyle='--', alpha=0.3)

    fig.tight_layout()
    return fig

charts['monthly_revenue'] = fig_to_b64(chart_monthly_revenue())
print("  [1/20] Monthly revenue trend")


# --- 2. FY25 vs FY26 YoY ---
def chart_yoy():
    fig, ax = plt.subplots(figsize=(7, 5))
    vals = [kpis['fy25_revenue'], kpis['fy26_revenue']]
    bars = ax.bar(['FY25', 'FY26'], vals, color=['#4fc3f7', '#81c784'], width=0.5, edgecolor='white', linewidth=0.5)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + vals[0]*0.02,
                inr_label(v), ha='center', fontsize=11, fontweight='bold')
    ax.set_title(f'Year-over-Year Revenue (+{kpis["yoy_growth_pct"]:.1f}%)', fontsize=13, fontweight='bold')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax.set_ylim(0, max(vals) * 1.15)
    ax.grid(axis='y', alpha=0.2)
    fig.tight_layout()
    return fig

charts['yoy_revenue'] = fig_to_b64(chart_yoy())
print("  [2/20] YoY revenue")


# --- 3. Category Revenue Mix ---
def chart_category_mix():
    data = desc['category_analysis']
    df = pd.DataFrame(data).sort_values('revenue', ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5))
    bars = ax.barh(df['category'], df['revenue'], color=COLORS[:len(df)], edgecolor='white', linewidth=0.5)
    for bar, pct in zip(bars, df['revenue_pct']):
        ax.text(bar.get_width() + df['revenue'].max()*0.01, bar.get_y() + bar.get_height()/2,
                f'{pct:.1f}%', va='center', fontsize=10)
    ax.set_title('Revenue by Category', fontsize=13, fontweight='bold')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax.grid(axis='x', alpha=0.2)
    fig.tight_layout()
    return fig

charts['category_mix'] = fig_to_b64(chart_category_mix())
print("  [3/20] Category mix")


# --- 4. Category Stacked Area ---
def chart_category_trend():
    conn = sqlite3.connect(str(DB_PATH))
    q = """
    SELECT strftime('%Y-%m', o.order_date) as month, p.category,
           SUM(li.line_total) as revenue
    FROM order_line_items li
    JOIN orders o ON li.order_id = o.order_id
    JOIN products p ON li.product_id = p.product_id
    WHERE o.status = 'Delivered'
    GROUP BY month, p.category
    ORDER BY month
    """
    df = pd.read_sql(q, conn)
    conn.close()
    pivot = df.pivot(index='month', columns='category', values='revenue').fillna(0)

    fig, ax = plt.subplots(figsize=(14, 5.5))
    ax.stackplot(range(len(pivot)), *[pivot[c] for c in pivot.columns],
                 labels=pivot.columns, colors=COLORS[:len(pivot.columns)], alpha=0.8)
    ax.set_xticks(range(0, len(pivot), 2))
    ax.set_xticklabels([pivot.index[i] for i in range(0, len(pivot), 2)], rotation=45, ha='right', fontsize=9)
    ax.set_title('Category Revenue Trend (Stacked)', fontsize=13, fontweight='bold')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax.legend(loc='upper left', fontsize=9, framealpha=0.3)
    ax.grid(axis='y', alpha=0.2)
    fig.tight_layout()
    return fig

charts['category_trend'] = fig_to_b64(chart_category_trend())
print("  [4/20] Category trend")


# --- 5. RFM Segments ---
def chart_rfm():
    data = pred['rfm_segments']
    segs = sorted(data.items(), key=lambda x: -x[1]['count'])
    labels = [s[0] for s in segs]
    values = [s[1]['count'] for s in segs]
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(labels, values, color=COLORS[:len(labels)], edgecolor='white', linewidth=0.5)
    for bar, v, s in zip(bars, values, segs):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + max(values)*0.02,
                f'{s[1]["pct"]:.1f}%', ha='center', fontsize=10)
    ax.set_title('Customer Health Snapshot', fontsize=13, fontweight='bold')
    ax.set_ylabel('Customers')
    plt.xticks(rotation=30, ha='right')
    ax.grid(axis='y', alpha=0.2)
    fig.tight_layout()
    return fig

charts['rfm_segments'] = fig_to_b64(chart_rfm())
print("  [5/20] RFM segments")


# --- 6. Retention Cohort Heatmap ---
def chart_retention():
    data = pred.get('retention_cohorts')
    if not data:
        return None
    rates = np.array(data['rates'])
    cohorts = data['cohorts']
    periods = data['periods']

    fig, ax = plt.subplots(figsize=(12, 6))
    sns.heatmap(rates, annot=True, fmt='.0f', cmap='YlGnBu',
                xticklabels=periods, yticklabels=[c[:7] for c in cohorts],
                ax=ax, cbar_kws={'label': 'Retention %'}, linewidths=0.5)
    ax.set_title('Are Customers Coming Back?', fontsize=13, fontweight='bold')
    ax.set_xlabel('Months Since First Purchase')
    ax.set_ylabel('Cohort')
    fig.tight_layout()
    return fig

ret_fig = chart_retention()
if ret_fig:
    charts['retention_heatmap'] = fig_to_b64(ret_fig)
    print("  [6/20] Retention heatmap")


# --- 7. CLV Distribution ---
def chart_clv():
    data = pred['clv_by_segment']
    df = pd.DataFrame(data)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.bar(df['segment'], df['mean'], color=COLORS[:len(df)], edgecolor='white', linewidth=0.5)
    for bar, v in zip(bars, df['mean']):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + df['mean'].max()*0.02,
                inr_fmt(v), ha='center', fontsize=9)
    ax.set_title('Customer Lifetime Value by Health Segment', fontsize=13, fontweight='bold')
    ax.set_ylabel('Avg Lifetime Value')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    plt.xticks(rotation=30, ha='right')
    ax.grid(axis='y', alpha=0.2)
    fig.tight_layout()
    return fig

charts['clv_distribution'] = fig_to_b64(chart_clv())
print("  [7/20] CLV distribution")


# --- 8. Product Pareto ---
def chart_pareto():
    conn = sqlite3.connect(str(DB_PATH))
    q = """
    SELECT li.product_id, p.product_name, SUM(li.line_total) as revenue
    FROM order_line_items li
    JOIN orders o ON li.order_id = o.order_id
    JOIN products p ON li.product_id = p.product_id
    WHERE o.status = 'Delivered'
    GROUP BY li.product_id
    ORDER BY revenue DESC
    LIMIT 30
    """
    df = pd.read_sql(q, conn)
    conn.close()
    total = df['revenue'].sum()
    df['cum_pct'] = df['revenue'].cumsum() / total * 100

    fig, ax1 = plt.subplots(figsize=(14, 5.5))
    ax1.bar(range(len(df)), df['revenue'], color='#4fc3f7', alpha=0.7, edgecolor='white', linewidth=0.3)
    ax1.set_ylabel('Revenue')
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax1.set_xticks(range(len(df)))
    ax1.set_xticklabels([n[:12] for n in df['product_name']], rotation=60, ha='right', fontsize=7)
    ax1.set_title('Which Products Drive Our Revenue?', fontsize=13, fontweight='bold')

    ax2 = ax1.twinx()
    ax2.plot(range(len(df)), df['cum_pct'], 'o-', color='#e57373', markersize=4)
    ax2.axhline(80, color='#e57373', linestyle='--', alpha=0.5, label='80% Revenue Line')
    ax2.set_ylabel('Cumulative %')
    ax2.set_ylim(0, 105)
    ax1.grid(axis='y', alpha=0.2)
    fig.tight_layout()
    return fig

charts['product_pareto'] = fig_to_b64(chart_pareto())
print("  [8/20] Product Pareto")


# --- 9. Rx vs OTC Trend ---
def chart_rx_otc():
    conn = sqlite3.connect(str(DB_PATH))
    q = """
    SELECT strftime('%Y-%m', o.order_date) as month,
           CASE WHEN p.requires_prescription = 1 THEN 'Rx' ELSE 'Non-Rx' END as type,
           SUM(li.line_total) as revenue
    FROM order_line_items li
    JOIN orders o ON li.order_id = o.order_id
    JOIN products p ON li.product_id = p.product_id
    WHERE o.status = 'Delivered'
    GROUP BY month, type
    """
    df = pd.read_sql(q, conn)
    conn.close()
    pivot = df.pivot(index='month', columns='type', values='revenue').fillna(0)
    fig, ax = plt.subplots(figsize=(14, 5))
    for col, color in zip(pivot.columns, ['#4fc3f7', '#81c784']):
        ax.plot(range(len(pivot)), pivot[col], 'o-', label=col, color=color, markersize=3, linewidth=2)
    ax.set_xticks(range(0, len(pivot), 2))
    ax.set_xticklabels([pivot.index[i] for i in range(0, len(pivot), 2)], rotation=45, ha='right', fontsize=9)
    ax.set_title('Rx vs Non-Rx Revenue Trend', fontsize=13, fontweight='bold')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax.legend(framealpha=0.3)
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return fig

charts['rx_otc_trend'] = fig_to_b64(chart_rx_otc())
print("  [9/20] Rx vs OTC trend")


# --- 10. Generic vs Branded Margins ---
def chart_generic_branded():
    gvb = desc['generic_vs_branded']
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    # Revenue
    vals = [gvb['branded_revenue'], gvb['generic_revenue']]
    ax1.bar(['Branded', 'Generic'], vals, color=['#4fc3f7', '#81c784'], edgecolor='white')
    for i, v in enumerate(vals):
        ax1.text(i, v + max(vals)*0.02, inr_label(v), ha='center', fontsize=10)
    ax1.set_title('Revenue Split', fontsize=12, fontweight='bold')
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax1.grid(axis='y', alpha=0.2)
    # Margin
    margins = [gvb['branded_margin_pct'], gvb['generic_margin_pct']]
    ax2.bar(['Branded', 'Generic'], margins, color=['#4fc3f7', '#81c784'], edgecolor='white')
    for i, v in enumerate(margins):
        ax2.text(i, v + 0.5, f'{v:.1f}%', ha='center', fontsize=11, fontweight='bold')
    ax2.set_title('Margin Comparison', fontsize=12, fontweight='bold')
    ax2.set_ylabel('Margin %')
    ax2.grid(axis='y', alpha=0.2)
    fig.suptitle('Generic vs Branded Analysis', fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()
    return fig

charts['generic_branded'] = fig_to_b64(chart_generic_branded())
print("  [10/20] Generic vs Branded")


# --- 11. Store Rankings ---
def chart_store_rankings():
    data = desc['store_performance'][:15]
    df = pd.DataFrame(data)
    fig, ax = plt.subplots(figsize=(12, 6))
    bars = ax.barh(range(len(df)), df['revenue'], color=COLORS[0], alpha=0.8, edgecolor='white', linewidth=0.3)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels([f"{r['store_name'][:25]} ({r['city']})" for r in data], fontsize=9)
    ax.set_title('Top 15 Stores by Revenue', fontsize=13, fontweight='bold')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.2)
    fig.tight_layout()
    return fig

charts['store_rankings'] = fig_to_b64(chart_store_rankings())
print("  [11/20] Store rankings")


# --- 12. Revenue by City ---
def chart_city_revenue():
    data = desc['city_revenue']
    df = pd.DataFrame(data).sort_values('revenue', ascending=True)
    fig, ax = plt.subplots(figsize=(9, 5))
    bars = ax.barh(df['city'], df['revenue'], color=COLORS[:len(df)], edgecolor='white', linewidth=0.5)
    for bar, v in zip(bars, df['revenue']):
        ax.text(bar.get_width() + df['revenue'].max()*0.01, bar.get_y() + bar.get_height()/2,
                inr_label(v), va='center', fontsize=9)
    ax.set_title('Revenue by City', fontsize=13, fontweight='bold')
    ax.xaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax.grid(axis='x', alpha=0.2)
    fig.tight_layout()
    return fig

charts['city_revenue'] = fig_to_b64(chart_city_revenue())
print("  [12/20] City revenue")


# --- 13. Store Type Comparison ---
def chart_store_type():
    data = desc['store_type_comparison']
    df = pd.DataFrame(data)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 5))
    ax1.bar(df['store_type'], df['rev_per_store'], color=COLORS[:3], edgecolor='white')
    for i, v in enumerate(df['rev_per_store']):
        ax1.text(i, v + df['rev_per_store'].max()*0.02, inr_fmt(v), ha='center', fontsize=10)
    ax1.set_title('Revenue per Store', fontsize=12, fontweight='bold')
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax1.grid(axis='y', alpha=0.2)
    ax2.bar(df['store_type'], df['margin_pct'], color=COLORS[:3], edgecolor='white')
    for i, v in enumerate(df['margin_pct']):
        ax2.text(i, v + 0.3, f'{v:.1f}%', ha='center', fontsize=10)
    ax2.set_title('Avg Margin %', fontsize=12, fontweight='bold')
    ax2.grid(axis='y', alpha=0.2)
    fig.suptitle('Store Type Performance', fontsize=14, fontweight='bold', y=1.02)
    fig.tight_layout()
    return fig

charts['store_type'] = fig_to_b64(chart_store_type())
print("  [13/20] Store type comparison")


# --- 14. OOS Rate Trend ---
def chart_oos_trend():
    data = strat['oos_trend']
    df = pd.DataFrame(data)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.plot(df['month'], df['oos_rate'], 'o-', color='#e57373', markersize=6, linewidth=2)
    ax.fill_between(df['month'], df['oos_rate'], alpha=0.2, color='#e57373')
    ax.axhline(5.0, color='#81c784', linestyle='--', alpha=0.5, label='Target (5%)')
    ax.set_title('How Often Are Shelves Empty?', fontsize=13, fontweight='bold')
    ax.set_ylabel('Stockout Rate %')
    ax.legend(framealpha=0.3)
    plt.xticks(rotation=45, ha='right')
    ax.grid(alpha=0.2)
    fig.tight_layout()
    return fig

charts['oos_trend'] = fig_to_b64(chart_oos_trend())
print("  [14/20] OOS trend")


# --- 15. Top Stockout Products ---
def chart_top_stockouts():
    data = strat['top_stockout_products'][:15]
    df = pd.DataFrame(data)
    fig, ax = plt.subplots(figsize=(12, 6))
    ax.barh(range(len(df)), df['oos_rate'] * 100, color='#e57373', alpha=0.8, edgecolor='white', linewidth=0.3)
    ax.set_yticks(range(len(df)))
    ax.set_yticklabels([f"{r['product_name'][:25]}" for r in data], fontsize=9)
    ax.set_title('Products Most Often Out of Stock', fontsize=13, fontweight='bold')
    ax.set_xlabel('OOS Rate %')
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.2)
    fig.tight_layout()
    return fig

charts['top_stockouts'] = fig_to_b64(chart_top_stockouts())
print("  [15/20] Top stockouts")


# --- 16. Revenue Leakage Waterfall ---
def chart_leakage_waterfall():
    rl = strat['revenue_leakage']
    labels = ['Gross\nPotential', 'Cancellations', 'Returns', 'Stockouts', 'Delays', 'Net\nRevenue']
    values = [rl['gross_potential'], -rl['cancellation_loss'], -rl['return_loss'],
              -rl['stockout_loss'], -rl['delay_loss'], rl['delivered_revenue']]

    fig, ax = plt.subplots(figsize=(12, 5.5))
    cumulative = [0]
    for v in values[:-1]:
        cumulative.append(cumulative[-1] + v)

    colors = ['#4fc3f7'] + ['#e57373'] * 4 + ['#81c784']
    bottoms = [0] + [cumulative[i+1] for i in range(4)] + [0]

    for i, (label, val, bottom, color) in enumerate(zip(labels, values, bottoms, colors)):
        height = abs(val) if i > 0 and i < 5 else val
        b = bottom if i == 0 or i == 5 else bottom
        ax.bar(i, height, bottom=b if i == 0 or i == 5 else cumulative[i], color=color, edgecolor='white', width=0.6)
        ax.text(i, (b if i==0 or i==5 else cumulative[i]) + height/2, inr_fmt(abs(val)),
                ha='center', va='center', fontsize=9, fontweight='bold')

    ax.set_xticks(range(len(labels)))
    ax.set_xticklabels(labels, fontsize=10)
    ax.set_title(f'Revenue Leakage Waterfall ({rl["leakage_pct"]:.1f}% total leakage)', fontsize=13, fontweight='bold')
    ax.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax.grid(axis='y', alpha=0.2)
    fig.tight_layout()
    return fig

charts['leakage_waterfall'] = fig_to_b64(chart_leakage_waterfall())
print("  [16/20] Leakage waterfall")


# --- 17. Cancellation Reasons ---
def chart_cancel_reasons():
    data = strat['cancellation_reasons']
    df = pd.DataFrame(data)
    fig, ax = plt.subplots(figsize=(9, 5))
    ax.barh(df['reason'], df['count'], color='#ffb74d', edgecolor='white', linewidth=0.5)
    ax.set_title('Cancellation Reasons', fontsize=13, fontweight='bold')
    ax.set_xlabel('Count')
    ax.invert_yaxis()
    ax.grid(axis='x', alpha=0.2)
    fig.tight_layout()
    return fig

charts['cancel_reasons'] = fig_to_b64(chart_cancel_reasons())
print("  [17/20] Cancellation reasons")


# --- 18. Delivery SLA ---
def chart_delivery_sla():
    conn = sqlite3.connect(str(DB_PATH))
    q = """
    SELECT delivery_days, COUNT(*) as cnt
    FROM orders WHERE channel = 'Online' AND status = 'Delivered'
    GROUP BY delivery_days ORDER BY delivery_days
    """
    df = pd.read_sql(q, conn)
    conn.close()

    fig, ax = plt.subplots(figsize=(9, 5))
    colors = ['#81c784' if d <= 2 else '#e57373' for d in df['delivery_days']]
    ax.bar(df['delivery_days'].astype(str), df['cnt'], color=colors, edgecolor='white', linewidth=0.5)
    ax.axvline(2.5, color='#ffb74d', linestyle='--', linewidth=2, label='Promise Threshold (2 days)')
    ax.set_title(f'Are We Delivering On Time? ({kpis["sla_compliance_pct"]:.1f}% on-time)', fontsize=13, fontweight='bold')
    ax.set_xlabel('Delivery Days')
    ax.set_ylabel('Orders')
    ax.legend(framealpha=0.3)
    ax.grid(axis='y', alpha=0.2)
    fig.tight_layout()
    return fig

charts['delivery_sla'] = fig_to_b64(chart_delivery_sla())
print("  [18/20] Delivery SLA")


# --- 19. Channel Mix Trend ---
def chart_channel_trend():
    conn = sqlite3.connect(str(DB_PATH))
    q = """
    SELECT strftime('%Y-%m', o.order_date) as month, o.channel,
           SUM(li.line_total) as revenue
    FROM order_line_items li
    JOIN orders o ON li.order_id = o.order_id
    WHERE o.status = 'Delivered'
    GROUP BY month, o.channel
    """
    df = pd.read_sql(q, conn)
    conn.close()
    pivot = df.pivot(index='month', columns='channel', values='revenue').fillna(0)
    if 'Online' in pivot.columns and 'Offline' in pivot.columns:
        pivot['online_pct'] = pivot['Online'] / (pivot['Online'] + pivot['Offline']) * 100

    fig, ax1 = plt.subplots(figsize=(14, 5))
    ax1.stackplot(range(len(pivot)), pivot.get('Offline', 0), pivot.get('Online', 0),
                  labels=['Offline', 'Online'], colors=['#4fc3f7', '#81c784'], alpha=0.8)
    ax1.set_xticks(range(0, len(pivot), 2))
    ax1.set_xticklabels([pivot.index[i] for i in range(0, len(pivot), 2)], rotation=45, ha='right', fontsize=9)
    ax1.set_title('Channel Revenue Mix Trend', fontsize=13, fontweight='bold')
    ax1.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax1.legend(loc='upper left', framealpha=0.3)

    if 'online_pct' in pivot.columns:
        ax2 = ax1.twinx()
        ax2.plot(range(len(pivot)), pivot['online_pct'], 'o--', color='#fff176', markersize=3, linewidth=1.5)
        ax2.set_ylabel('Online %', fontsize=10)
        ax2.set_ylim(0, 50)

    ax1.grid(axis='y', alpha=0.2)
    fig.tight_layout()
    return fig

charts['channel_trend'] = fig_to_b64(chart_channel_trend())
print("  [19/20] Channel trend")


# --- 20. Payment Modes + Day of Week ---
def chart_payment_dow():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 5))
    # Payment modes
    pm = desc['payment_modes']
    df_pm = pd.DataFrame(pm)
    ax1.pie(df_pm['count'], labels=df_pm['mode'], autopct='%1.1f%%', colors=COLORS[:len(df_pm)],
            textprops={'fontsize': 9, 'color': '#e0e0e0'})
    ax1.set_title('Payment Mode Distribution', fontsize=12, fontweight='bold')

    # Day of week
    dow = strat['day_of_week']
    df_dow = pd.DataFrame(dow)
    ax2.bar(df_dow['day'].str[:3], df_dow['revenue'], color=COLORS[:7], edgecolor='white', linewidth=0.5)
    ax2.set_title('Revenue by Day of Week', fontsize=12, fontweight='bold')
    ax2.yaxis.set_major_formatter(mticker.FuncFormatter(inr_fmt))
    ax2.grid(axis='y', alpha=0.2)

    fig.tight_layout()
    return fig

charts['payment_dow'] = fig_to_b64(chart_payment_dow())
print("  [20/20] Payment + Day of week")

print(f"\nTotal charts generated: {len(charts)}")


# =============================================================================
# HTML DASHBOARD
# =============================================================================

def img(key):
    if key in charts:
        return f'<img src="data:image/png;base64,{charts[key]}" alt="{key}" class="chart-img">'
    return f'<!-- chart not found: {key} -->'

# Format KPI values
def kpi_val(key, fmt='inr'):
    v = kpis.get(key, 0)
    if fmt == 'inr':
        return inr_label(v)
    elif fmt == 'pct':
        return f'{v:.1f}%'
    elif fmt == 'int':
        return f'{int(v):,}'
    elif fmt == 'days':
        return f'{v:.1f} days'
    return str(v)


page = f'''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tasknova — WF Revenue Intelligence Dashboard</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {{
    --bg: #fafaf9;
    --surface: #ffffff;
    --border: rgba(0,0,0,0.06);
    --text: #1a1a1a;
    --muted: #6b7280;
    --accent: #1e3a5f;
    --tn-blue: #2b6cb0;
    --tn-light: #ebf4ff;
    --green: #059669;
    --red: #dc2626;
    --amber: #92400e;
    --amber-bg: #fffbeb;
}}
* {{ margin:0; padding:0; box-sizing:border-box; }}
html {{ scroll-behavior: smooth; }}
body {{
    font-family: 'Inter', -apple-system, sans-serif;
    background: var(--bg); color: var(--text);
    line-height: 1.8; font-size: 15px;
    -webkit-font-smoothing: antialiased;
}}
::selection {{ background: rgba(43,108,176,0.15); }}

nav {{
    position: sticky; top: 0; z-index: 100;
    background: rgba(255,255,255,0.92);
    backdrop-filter: blur(20px) saturate(180%);
    border-bottom: 1px solid var(--border);
    padding: 1rem 0;
}}
nav .inner {{
    max-width: 1400px; margin: 0 auto; padding: 0 2rem;
    display: flex; justify-content: space-between; align-items: center;
}}
nav .logo {{ font-weight: 800; font-size: 0.95rem; color: var(--accent); letter-spacing: -0.02em; }}
nav .logo span {{ font-weight: 400; color: var(--muted); font-size: 0.78rem; margin-left: 0.6rem; }}
nav .links {{ display: flex; gap: 1.5rem; list-style: none; flex-wrap: wrap; }}
nav .links a {{
    color: var(--muted); text-decoration: none; font-size: 0.75rem;
    font-weight: 500; letter-spacing: 0.02em; text-transform: uppercase;
    transition: color 0.2s;
}}
nav .links a:hover {{ color: var(--accent); }}

.app-layout {{
    display: grid; grid-template-columns: 1fr minmax(370px, 480px);
    min-height: calc(100vh - 60px);
}}
.dashboard-main {{
    overflow-y: auto; max-height: calc(100vh - 60px);
    scrollbar-width: thin;
}}
.container {{ max-width: 1100px; margin: 0 auto; padding: 0 2rem; }}

.hero {{
    padding: 5rem 0 4rem; text-align: center;
    border-bottom: 1px solid var(--border);
}}
.hero .eyebrow {{
    font-size: 0.7rem; font-weight: 600; letter-spacing: 0.15em;
    text-transform: uppercase; color: var(--tn-blue); margin-bottom: 1.5rem;
}}
.hero h1 {{
    font-size: 2.8rem; font-weight: 800; letter-spacing: -0.03em;
    color: var(--accent); margin-bottom: 1.2rem; line-height: 1.15;
}}
.hero p {{
    color: var(--muted); font-size: 1.05rem; max-width: 560px;
    margin: 0 auto; line-height: 1.7; font-weight: 300;
}}

.kpi-grid {{
    display: grid; grid-template-columns: repeat(5, 1fr); gap: 1.2rem;
    margin-top: 3rem; padding-top: 2.5rem; border-top: 1px solid var(--border);
}}
.kpi-card {{
    text-align: center; padding: 1.2rem 0.5rem;
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px;
}}
.kpi-card .value {{ font-size: 1.5rem; font-weight: 700; color: var(--accent); letter-spacing: -0.02em; }}
.kpi-card .label {{ font-size: 0.68rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.3rem; font-weight: 500; }}
.kpi-card.green .value {{ color: var(--green); }}
.kpi-card.red .value {{ color: var(--red); }}

section {{ padding: 4rem 0; border-bottom: 1px solid var(--border); }}
section:last-of-type {{ border-bottom: none; }}
.section-header {{ margin-bottom: 3rem; }}
.section-header .eyebrow {{ font-size: 0.7rem; font-weight: 600; letter-spacing: 0.15em; text-transform: uppercase; color: var(--tn-blue); margin-bottom: 0.8rem; }}
.section-header h2 {{ font-size: 1.8rem; font-weight: 700; letter-spacing: -0.02em; color: var(--accent); margin-bottom: 0.6rem; }}
.section-header p {{ color: var(--muted); font-size: 0.95rem; max-width: 600px; }}

.chart-block {{ margin-bottom: 3.5rem; }}
.chart-block:last-child {{ margin-bottom: 0; }}
.chart-block h3 {{ font-size: 1.05rem; font-weight: 600; color: var(--accent); margin-bottom: 1.5rem; letter-spacing: -0.01em; }}
.chart-img {{
    width: 100%; border-radius: 8px; border: 1px solid var(--border);
    box-shadow: 0 1px 3px rgba(0,0,0,0.04), 0 8px 24px rgba(0,0,0,0.03);
}}

.analysis {{
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 10px; padding: 1.6rem 1.8rem; margin-top: 1.5rem;
    box-shadow: 0 1px 2px rgba(0,0,0,0.02);
}}
.analysis.tn {{ border-left: 3px solid var(--tn-blue); background: var(--tn-light); }}
.analysis.risk {{ border-left: 3px solid var(--red); background: rgba(220,38,38,0.02); }}
.analysis.opportunity {{ border-left: 3px solid var(--green); background: rgba(5,150,105,0.02); }}
.analysis.amber {{ border-left: 3px solid var(--amber); background: var(--amber-bg); }}
.analysis h4 {{ font-size: 0.85rem; font-weight: 600; color: var(--text); margin-bottom: 0.6rem; }}
.analysis p {{ color: var(--muted); font-size: 0.86rem; margin-bottom: 0.5rem; line-height: 1.75; }}
.analysis strong {{ color: var(--text); font-weight: 600; }}
.analysis ul {{ margin: 0.5rem 0 0.5rem 1.2rem; color: var(--muted); font-size: 0.84rem; }}
.analysis li {{ margin-bottom: 0.4rem; line-height: 1.7; }}

.data-grid {{ display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin: 2rem 0; }}

.chart-block {{ opacity: 0; transform: translateY(20px); animation: fadeUp 0.6s forwards; }}
.chart-block:nth-child(1) {{ animation-delay: 0.1s; }}
.chart-block:nth-child(2) {{ animation-delay: 0.15s; }}
.chart-block:nth-child(3) {{ animation-delay: 0.2s; }}
@keyframes fadeUp {{ to {{ opacity: 1; transform: translateY(0); }} }}

@media (max-width: 768px) {{
    .hero h1 {{ font-size: 2rem; }}
    .kpi-grid {{ grid-template-columns: repeat(2, 1fr); }}
    .data-grid {{ grid-template-columns: 1fr; }}
}}

footer {{ text-align: center; padding: 3rem 2rem; color: var(--muted); font-size: 0.75rem; }}
footer strong {{ color: var(--accent); }}

/* ===== CHAT SIDEBAR ===== */
.chat-sidebar {{
    position: sticky; top: 60px; height: calc(100vh - 60px);
    display: flex; flex-direction: column;
    border-left: 1px solid var(--border);
    background: var(--surface);
}}
.chat-sidebar-header {{
    padding: 1.2rem 1.2rem 0.8rem;
    background: var(--accent); color: white;
}}
.chat-sidebar-header h2 {{
    font-size: 1.1rem; font-weight: 700; margin-bottom: 0.2rem;
}}
.chat-sidebar-header p {{
    font-size: 0.72rem; opacity: 0.7; font-weight: 400;
}}
.mode-pills {{
    display: flex; gap: 0.4rem; padding: 0.8rem 1.2rem;
    background: #f8f9fa; border-bottom: 1px solid var(--border);
}}
.mode-pill {{
    flex: 1; padding: 0.45rem 0.5rem; border: 1px solid var(--border);
    border-radius: 6px; background: white; color: var(--muted);
    font-size: 0.72rem; font-weight: 600; cursor: pointer;
    text-align: center; transition: all 0.2s; font-family: inherit;
}}
.mode-pill:hover {{ border-color: var(--tn-blue); color: var(--tn-blue); }}
.mode-pill.active {{
    background: var(--tn-blue); color: white; border-color: var(--tn-blue);
}}
#chat-messages {{
    flex: 1; overflow-y: auto; padding: 1rem 1.2rem;
    display: flex; flex-direction: column; gap: 0.8rem;
    scrollbar-width: thin;
}}
.chat-msg {{
    max-width: 92%; padding: 0.7rem 1rem; border-radius: 12px;
    font-size: 0.84rem; line-height: 1.6; word-wrap: break-word;
}}
.chat-msg.user {{
    align-self: flex-end; background: var(--tn-blue); color: white;
    border-bottom-right-radius: 4px;
}}
.chat-msg.bot {{
    align-self: flex-start; background: #f3f4f6; color: var(--text);
    border-bottom-left-radius: 4px; white-space: normal;
    max-width: 100%; min-width: 0; overflow: hidden;
}}
.chat-msg.bot p {{ margin-bottom: 0.5rem; }}
.chat-msg.bot p:last-child {{ margin-bottom: 0; }}
.chat-msg.bot .table-scroll {{
    overflow-x: auto; margin: 0.6rem -0.4rem; padding: 0 0.4rem;
    scrollbar-width: thin;
}}
.chat-msg.typing {{
    align-self: flex-start; background: #f3f4f6; color: var(--muted);
    font-style: italic;
}}
.chat-table {{
    width: 100%; border-collapse: collapse; font-size: 0.74rem;
    margin: 0; border-radius: 6px; overflow: hidden;
    min-width: 280px;
}}
.chat-table th {{
    background: var(--accent); color: white; padding: 0.4rem 0.5rem;
    text-align: left; font-weight: 600; font-size: 0.68rem;
    text-transform: uppercase; letter-spacing: 0.03em;
    white-space: nowrap;
}}
.chat-table td {{
    padding: 0.35rem 0.5rem; border-bottom: 1px solid var(--border);
    white-space: nowrap;
}}
.chat-table tr:nth-child(even) td {{ background: #f8f9fa; }}
.chat-table tr:hover td {{ background: #eef2f7; }}
.chat-chart {{
    max-width: 100%; border-radius: 6px; margin: 0.6rem 0;
    border: 1px solid var(--border);
}}
.chat-action {{
    background: #eef6ee; border-left: 3px solid var(--green);
    padding: 0.6rem 0.8rem; border-radius: 0 6px 6px 0;
    margin: 0.6rem 0; font-size: 0.82rem;
}}
.chat-drilldowns {{
    display: flex; flex-wrap: wrap; gap: 0.35rem; margin: 0.6rem 0 0.2rem;
}}
.chat-drill-btn {{
    padding: 0.35rem 0.7rem; border: 1px solid var(--tn-blue);
    border-radius: 16px; background: var(--tn-light); color: var(--tn-blue);
    font-size: 0.7rem; font-weight: 600; cursor: pointer;
    transition: all 0.2s; font-family: inherit;
}}
.chat-drill-btn:hover {{
    background: var(--tn-blue); color: white;
}}
.chat-msg.typing .typing-dots {{
    display: inline-block;
}}
.chat-msg.typing .typing-dots::after {{
    content: ''; animation: dots 1.4s steps(4, end) infinite;
}}
@keyframes dots {{
    0%, 20% {{ content: ''; }}
    40% {{ content: '.'; }}
    60% {{ content: '..'; }}
    80%, 100% {{ content: '...'; }}
}}
.typing-status {{
    font-size: 0.72rem; color: var(--muted); font-style: normal;
    margin-top: 0.3rem;
}}
.suggested-qs {{
    display: flex; flex-wrap: wrap; gap: 0.4rem;
    padding: 0 1.2rem 0.8rem;
}}
.suggested-q {{
    padding: 0.4rem 0.8rem; border: 1px solid var(--border);
    border-radius: 16px; background: white; color: var(--muted);
    font-size: 0.72rem; cursor: pointer; transition: all 0.2s;
    font-family: inherit;
}}
.suggested-q:hover {{
    border-color: var(--tn-blue); color: var(--tn-blue); background: var(--tn-light);
}}
#chat-input-area {{
    display: flex; gap: 0.5rem; padding: 0.8rem 1.2rem;
    border-top: 1px solid var(--border); background: white;
}}
#chat-input {{
    flex: 1; border: 1px solid var(--border); border-radius: 8px;
    padding: 0.6rem 0.8rem; font-size: 0.84rem; font-family: inherit;
    outline: none; resize: none;
}}
#chat-input:focus {{ border-color: var(--tn-blue); }}
#chat-send {{
    background: var(--tn-blue); color: white; border: none;
    border-radius: 8px; padding: 0.6rem 1rem; font-size: 0.84rem;
    font-weight: 600; cursor: pointer; transition: background 0.2s;
    font-family: inherit;
}}
#chat-send:hover {{ background: var(--accent); }}
#chat-send:disabled {{ opacity: 0.5; cursor: not-allowed; }}

/* Mobile: chat below dashboard */
@media (max-width: 1024px) {{
    .app-layout {{ grid-template-columns: 1fr; }}
    .dashboard-main {{ max-height: none; overflow: visible; }}
    .chat-sidebar {{
        position: relative; top: 0; height: auto;
        min-height: 500px; border-left: none; border-top: 2px solid var(--border);
    }}
    #chat-messages {{ min-height: 300px; }}
}}
@media (max-width: 768px) {{
    .mode-pills {{ gap: 0.3rem; }}
    .mode-pill {{ font-size: 0.68rem; padding: 0.4rem; }}
}}
</style>
</head>
<body>

<nav><div class="inner">
<div class="logo">Tasknova<span>Revenue Intelligence</span></div>
<ul class="links">
<li><a href="#big-picture">Big Picture</a></li>
<li><a href="#revenue">Revenue</a></li>
<li><a href="#customers">Customers</a></li>
<li><a href="#products">Products</a></li>
<li><a href="#stores">Stores</a></li>
<li><a href="#inventory">Inventory</a></li>
<li><a href="#leakage">Leakage</a></li>
<li><a href="#operations">Delivery</a></li>
</ul>
</div></nav>

<div class="app-layout">
<div class="dashboard-main">
<div class="container">

<!-- ===== HERO ===== -->
<div class="hero">
<div class="eyebrow">Wellness Forever &mdash; Revenue Intelligence</div>
<h1>How Is Our<br>Business Doing?</h1>
<p>A clear view of 30 stores, 52K+ orders, and 150K+ line items across 24 months &mdash; what's working, what's not, and where to act.</p>

<div class="kpi-grid">
<div class="kpi-card"><div class="value">{kpi_val('total_revenue')}</div><div class="label">Total Revenue (2yr)</div></div>
<div class="kpi-card green"><div class="value">+{kpis['yoy_growth_pct']:.1f}%</div><div class="label">YoY Growth</div></div>
<div class="kpi-card"><div class="value">{kpi_val('total_delivered_orders', 'int')}</div><div class="label">Orders Fulfilled</div></div>
<div class="kpi-card"><div class="value">{kpi_val('aov')}</div><div class="label">Avg Order Value</div></div>
<div class="kpi-card"><div class="value">{kpi_val('total_customers', 'int')}</div><div class="label">Active Customers</div></div>
<div class="kpi-card"><div class="value">{kpi_val('overall_margin_pct', 'pct')}</div><div class="label">Profit Margin</div></div>
<div class="kpi-card red"><div class="value">{kpi_val('leakage_pct', 'pct')}</div><div class="label">Revenue Lost</div></div>
<div class="kpi-card red"><div class="value">{kpi_val('avg_oos_rate_pct', 'pct')}</div><div class="label">Stockout Rate</div></div>
<div class="kpi-card"><div class="value">{kpi_val('online_share_pct', 'pct')}</div><div class="label">Online Share</div></div>
<div class="kpi-card green"><div class="value">{kpi_val('sla_compliance_pct', 'pct')}</div><div class="label">On-Time Delivery</div></div>
</div>
</div>

<!-- ===== 1. THE BIG PICTURE ===== -->
<section id="big-picture">
<div class="section-header">
<div class="eyebrow">At a Glance</div>
<h2>The Big Picture</h2>
<p>Here's what you need to know about Wellness Forever's performance across 30 stores over the past two years.</p>
</div>

<div class="analysis tn">
<h4>Where We Stand</h4>
<p>Across 30 stores, we brought in <strong>{kpi_val('total_revenue')}</strong> over 24 months &mdash; roughly <strong>{inr_label(kpis['total_revenue']/2)}</strong> per year.
Revenue grew <strong>+{kpis['yoy_growth_pct']:.1f}%</strong> year-over-year, and the average customer spends <strong>{kpi_val('aov')}</strong> per order.</p>
<ul>
<li><strong>{kpi_val('online_share_pct', 'pct')}</strong> of sales happen online &mdash; room to grow digital</li>
<li>We keep <strong>{kpi_val('overall_margin_pct', 'pct')}</strong> as profit ({kpi_val('total_margin')} total)</li>
<li>But we're losing <strong>{kpi_val('leakage_pct', 'pct')}</strong> of potential revenue to cancellations, returns, stockouts, and late deliveries</li>
<li><strong>{kpi_val('churn_rate_pct', 'pct')}</strong> of customers haven't come back in 90+ days &mdash; they may be walking away</li>
</ul>
</div>
</section>

<!-- ===== 2. WHERE THE MONEY COMES FROM ===== -->
<section id="revenue">
<div class="section-header">
<div class="eyebrow">Revenue</div>
<h2>Where the Money Comes From</h2>
<p>Monthly trends, year-over-year growth, and which product categories are driving sales.</p>
</div>

<div class="chart-block">
<h3>How Is Revenue Trending Month by Month?</h3>
{img('monthly_revenue')}
</div>

<div class="data-grid">
<div class="chart-block">
<h3>Are We Growing Year over Year?</h3>
{img('yoy_revenue')}
</div>
<div class="chart-block">
<h3>Which Categories Bring in the Most?</h3>
{img('category_mix')}
</div>
</div>

<div class="chart-block">
<h3>How Are Categories Performing Over Time?</h3>
{img('category_trend')}
</div>

<div class="analysis tn">
<h4>What This Means</h4>
<p>Revenue is on a <strong>steady upward path</strong>. We see a dip during monsoon months (Jun&ndash;Aug) and a spike around
festive season (Oct&ndash;Nov) &mdash; that's expected. FY26 came in at <strong>{inr_label(kpis['fy26_revenue'])}</strong>,
which is <strong>+{kpis['yoy_growth_pct']:.1f}%</strong> higher than FY25. <strong>What to do:</strong>
Plan inventory and staffing around seasonal patterns to capture even more of the festive demand.</p>
</div>
</section>

<!-- ===== 3. WHO'S BUYING — AND WHO STOPPED ===== -->
<section id="customers">
<div class="section-header">
<div class="eyebrow">Customers</div>
<h2>Who's Buying &mdash; And Who Stopped</h2>
<p>A health check on our customer base: who's loyal, who needs attention, and who we're at risk of losing.</p>
</div>

<div class="data-grid">
<div class="chart-block">
<h3>Customer Health Snapshot</h3>
{img('rfm_segments')}
</div>
<div class="chart-block">
<h3>How Much Are Different Customer Groups Worth?</h3>
{img('clv_distribution')}
</div>
</div>

<div class="chart-block">
<h3>Are Customers Coming Back?</h3>
{img('retention_heatmap')}
</div>

<div class="analysis risk">
<h4>Customers Walking Away</h4>
<p><strong>{kpi_val('churn_rate_pct', 'pct')}</strong> of our customers haven't placed an order in over 90 days.
That puts <strong>{inr_label(pred['churn_signals']['at_risk_revenue'])}</strong> in annual revenue at risk &mdash;
money we could lose if we don't act. <strong>{kpi_val('at_risk_customers', 'int')}</strong> customers
need a reason to come back. <strong>What to do:</strong> Launch re-engagement campaigns (personalized offers,
reminders) for at-risk customers before they're gone for good.</p>
</div>

<div class="analysis opportunity">
<h4>Our Best Customers Are a Growth Engine</h4>
<p>Champions ({kpis['rfm_champions_pct']:.1f}%) and Loyal ({kpis['rfm_loyal_pct']:.1f}%) customers
are the backbone of our revenue. Meanwhile, {kpis['rfm_needs_attention_pct']:.1f}% "Need Attention" and
{kpis['rfm_at_risk_pct']:.1f}% are "At Risk." <strong>What to do:</strong> Reward loyal customers to keep them
engaged, and run targeted win-back offers for the at-risk group before they slip into the "Lost" category.</p>
</div>
</section>

<!-- ===== 4. WHAT SELLS, WHAT DOESN'T ===== -->
<section id="products">
<div class="section-header">
<div class="eyebrow">Products</div>
<h2>What Sells, What Doesn't</h2>
<p>Which products drive the business, and where there's room to improve profitability.</p>
</div>

<div class="chart-block">
<h3>Which Products Drive Our Revenue?</h3>
{img('product_pareto')}
</div>

<div class="chart-block">
<h3>Prescription vs Over-the-Counter Revenue</h3>
{img('rx_otc_trend')}
</div>

<div class="chart-block">
<h3>Generic vs Branded &mdash; Revenue and Profit</h3>
{img('generic_branded')}
</div>

<div class="analysis tn">
<h4>A Few Products Carry Most of the Weight</h4>
<p>Just <strong>{desc['product_pareto']['n_80']}</strong> products out of 1,000 ({desc['product_pareto']['pct_80']:.1f}% of our catalog)
bring in 80% of our revenue. If even a few of these go out of stock, the revenue impact is significant.
Prescription medicines account for <strong>{desc['rx_vs_otc']['rx_share_pct']:.1f}%</strong> of total sales.
<strong>What to do:</strong> Ensure these top sellers never face stockouts. Set up automatic reorder alerts for the top 131 products.</p>
</div>

<div class="analysis opportunity">
<h4>Generics Could Boost Our Profits</h4>
<p>Generic medicines earn a {desc['generic_vs_branded']['generic_margin_pct']:.1f}% margin vs {desc['generic_vs_branded']['branded_margin_pct']:.1f}%
for branded. By strategically promoting generics where clinically appropriate, we can improve overall profitability
without sacrificing quality. <strong>What to do:</strong> Train pharmacists to recommend generic alternatives, especially for
high-volume branded products.</p>
</div>
</section>

<!-- ===== 5. WHICH STORES ARE WINNING ===== -->
<section id="stores">
<div class="section-header">
<div class="eyebrow">Stores</div>
<h2>Which Stores Are Winning</h2>
<p>Performance by location, city, and store type &mdash; who's leading and who needs help.</p>
</div>

<div class="chart-block">
<h3>Our Top 15 Revenue-Generating Stores</h3>
{img('store_rankings')}
</div>

<div class="data-grid">
<div class="chart-block">
<h3>Which Cities Bring in the Most Revenue?</h3>
{img('city_revenue')}
</div>
<div class="chart-block">
<h3>How Do Store Types Compare?</h3>
{img('store_type')}
</div>
</div>

<div class="analysis tn">
<h4>Mumbai Leads, But There Are Gaps</h4>
<p>Mumbai dominates both in store count and revenue. Flagship stores generate significantly more revenue per location,
validating the larger format investment. But underperforming stores represent untapped potential.
<strong>What to do:</strong> Study what top stores do differently (staffing, layout, product mix) and replicate
those practices in lower-performing locations.</p>
</div>
</section>

<!-- ===== 6. EMPTY SHELVES, LOST SALES ===== -->
<section id="inventory">
<div class="section-header">
<div class="eyebrow">Inventory</div>
<h2>Empty Shelves, Lost Sales</h2>
<p>When products aren't on the shelf, customers walk away. Here's how often that's happening.</p>
</div>

<div class="chart-block">
<h3>How Often Are Shelves Empty?</h3>
{img('oos_trend')}
</div>

<div class="chart-block">
<h3>Products Most Often Out of Stock</h3>
{img('top_stockouts')}
</div>

<div class="analysis risk">
<h4>Stockouts Are Costing Us Real Money</h4>
<p>Our stockout rate is <strong>{kpi_val('avg_oos_rate_pct', 'pct')}</strong> &mdash; above the 5% target.
Every empty shelf is a customer who might not come back. We estimate stockouts alone cost us
<strong>{inr_label(strat['revenue_leakage']['stockout_loss'])}</strong> in lost sales.
<strong>What to do:</strong> Increase safety stock on the 15 most frequently out-of-stock products and
set up automated reorder triggers.</p>
</div>
</section>

<!-- ===== 7. MONEY LEFT ON THE TABLE ===== -->
<section id="leakage">
<div class="section-header">
<div class="eyebrow">Revenue Leakage</div>
<h2>Money Left on the Table</h2>
<p>Revenue we should have earned but lost to cancellations, returns, stockouts, and late deliveries.</p>
</div>

<div class="chart-block">
<h3>Where Is Revenue Leaking?</h3>
{img('leakage_waterfall')}
</div>

<div class="chart-block">
<h3>Why Are Customers Cancelling?</h3>
{img('cancel_reasons')}
</div>

<div class="analysis risk">
<h4>We're Leaving {inr_label(strat['revenue_leakage']['total_leakage'])} on the Table</h4>
<p>Out of every 100 rupees in potential revenue, we lose <strong>{strat['revenue_leakage']['leakage_pct']:.1f} rupees</strong>
before it reaches the bank. Here's where it goes:</p>
<ul>
<li><strong>Cancellations: {inr_label(strat['revenue_leakage']['cancellation_loss'])}</strong> &mdash; the biggest leak. Address the top cancellation reasons to plug this first</li>
<li><strong>Returns: {inr_label(strat['revenue_leakage']['return_loss'])}</strong> &mdash; improve product descriptions and order accuracy</li>
<li><strong>Stockouts: {inr_label(strat['revenue_leakage']['stockout_loss'])}</strong> &mdash; customers can't buy what's not on the shelf</li>
<li><strong>Late deliveries: {inr_label(strat['revenue_leakage']['delay_loss'])}</strong> &mdash; tighten delivery operations</li>
</ul>
<p><strong>What to do:</strong> Tackle cancellations first (highest impact). Identify the top 3 cancellation reasons and create action plans for each.</p>
</div>
</section>

<!-- ===== 8. HOW WELL WE DELIVER ===== -->
<section id="operations">
<div class="section-header">
<div class="eyebrow">Operations</div>
<h2>How Well We Deliver</h2>
<p>Are we keeping our delivery promise? How are customers choosing to pay? When do they shop?</p>
</div>

<div class="chart-block">
<h3>Are We Delivering on Time?</h3>
{img('delivery_sla')}
</div>

<div class="chart-block">
<h3>Online vs In-Store Revenue Trend</h3>
{img('channel_trend')}
</div>

<div class="chart-block">
<h3>How Do Customers Pay &amp; When Do They Shop?</h3>
{img('payment_dow')}
</div>

<div class="analysis tn">
<h4>Operations Are Strong &mdash; With Room to Improve</h4>
<p>We deliver on time <strong>{kpi_val('sla_compliance_pct', 'pct')}</strong> of the time, with an average delivery
of just <strong>{kpi_val('avg_delivery_days', 'days')}</strong>. Online sales make up <strong>{kpi_val('online_share_pct', 'pct')}</strong>
of revenue and trending upward. UPI is the most popular payment method, reflecting India's digital shift.
<strong>What to do:</strong> Focus on the 6.7% of late deliveries &mdash; identify problem routes and peak-hour bottlenecks to push on-time delivery above 95%.</p>
</div>
</section>

</div>

<footer>
<p>Built with <strong>Tasknova</strong> Revenue Intelligence Platform &mdash; Powered by AI</p>
<p>Data period: May 2024 &ndash; April 2026 &bull; 30 stores &bull; 52K+ orders &bull; Generated {_dt.now().strftime('%Y-%m-%d')}</p>
</footer>
</div><!-- end .dashboard-main -->

<!-- ===== CHAT SIDEBAR ===== -->
<aside class="chat-sidebar">
<div class="chat-sidebar-header">
    <h2>Ask Anything</h2>
    <p>AI-powered answers from your data</p>
</div>
<div class="mode-pills">
    <button class="mode-pill" data-mode="BRIEF" title="2-3 sentences, just the number">Brief</button>
    <button class="mode-pill active" data-mode="INSIGHTS" title="Key findings + context + actions">Insights</button>
    <button class="mode-pill" data-mode="DEEP" title="Full analysis with charts and data">Deep Dive</button>
</div>
<div id="chat-messages"></div>
<div class="suggested-qs" id="suggested-qs">
    <button class="suggested-q">What is our total revenue?</button>
    <button class="suggested-q">Which stores are bleeding revenue?</button>
    <button class="suggested-q">How bad is our stockout problem?</button>
    <button class="suggested-q">Are we ready for monsoon in Mumbai?</button>
    <button class="suggested-q">Generic vs branded margin</button>
    <button class="suggested-q">Best day of the week for sales?</button>
    <button class="suggested-q">What has the system learned?</button>
</div>
<div id="chat-input-area">
    <input type="text" id="chat-input" placeholder="Ask about revenue, stores, customers..." onkeydown="if(event.key==='Enter')sendChat()">
    <button id="chat-send" onclick="sendChat()">Ask</button>
</div>
</aside>
</div><!-- end .app-layout -->

<script>
let currentMode = 'INSIGHTS';
let pollTimer = null;

// Mode pill switching
document.querySelectorAll('.mode-pill').forEach(function(pill) {{
    pill.addEventListener('click', function() {{
        document.querySelectorAll('.mode-pill').forEach(function(p) {{ p.classList.remove('active'); }});
        pill.classList.add('active');
        currentMode = pill.dataset.mode;
    }});
}});

// Suggested questions
document.querySelectorAll('.suggested-q').forEach(function(btn) {{
    btn.addEventListener('click', function() {{
        document.getElementById('chat-input').value = btn.textContent;
        sendChat();
    }});
}});

function sendChat() {{
    const input = document.getElementById('chat-input');
    const msg = input.value.trim();
    if (!msg) return;

    // Hide suggested questions once conversation starts
    const sq = document.getElementById('suggested-qs');
    if (sq) sq.style.display = 'none';

    const msgs = document.getElementById('chat-messages');

    // User message (escaped)
    const userDiv = document.createElement('div');
    userDiv.className = 'chat-msg user';
    userDiv.textContent = msg;
    msgs.appendChild(userDiv);

    input.value = '';
    document.getElementById('chat-send').disabled = true;

    // Typing indicator with progress updates
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-msg typing';
    const modeLabel = currentMode === 'DEEP' ? 'Deep Dive' : currentMode === 'BRIEF' ? 'Brief' : 'Insights';
    typingDiv.innerHTML = '<span class="typing-dots">Thinking</span>';
    msgs.appendChild(typingDiv);
    msgs.scrollTop = msgs.scrollHeight;

    // Progress messages based on time elapsed
    const progressMsgs = currentMode === 'DEEP'
        ? ['Querying database<span class="typing-dots"></span>',
           'Running analysis &amp; generating charts<span class="typing-dots"></span>',
           'Comparing against industry benchmarks<span class="typing-dots"></span>',
           'Building detailed report<span class="typing-dots"></span>']
        : ['Querying your data<span class="typing-dots"></span>',
           'Preparing ' + modeLabel.toLowerCase() + ' response<span class="typing-dots"></span>'];
    let progressIdx = 0;
    const progressTimer = setInterval(function() {{
        if (progressIdx < progressMsgs.length) {{
            typingDiv.innerHTML = progressMsgs[progressIdx];
            progressIdx++;
        }}
    }}, 3000);

    // Prepend mode tag and send
    const taggedMsg = '[' + currentMode + '] ' + msg;
    fetch('/query', {{
        method: 'POST',
        headers: {{'Content-Type': 'text/plain'}},
        body: taggedMsg
    }}).catch(function() {{}});

    // Poll for response
    let attempts = 0;
    if (pollTimer) clearInterval(pollTimer);
    pollTimer = setInterval(function() {{
        attempts++;
        fetch('/response').then(function(r) {{ return r.json(); }}).then(function(data) {{
            if (data.status === 'ready') {{
                clearInterval(pollTimer);
                clearInterval(progressTimer);
                pollTimer = null;
                typingDiv.remove();
                const botDiv = document.createElement('div');
                botDiv.className = 'chat-msg bot';
                botDiv.innerHTML = data.response;
                // Wrap standalone tables in scroll container
                botDiv.querySelectorAll('table.chat-table').forEach(function(tbl) {{
                    if (!tbl.parentElement.classList.contains('table-scroll')) {{
                        const wrapper = document.createElement('div');
                        wrapper.className = 'table-scroll';
                        tbl.parentNode.insertBefore(wrapper, tbl);
                        wrapper.appendChild(tbl);
                    }}
                }});
                // Wire up drill-down buttons
                botDiv.querySelectorAll('.chat-drill-btn').forEach(function(btn) {{
                    btn.addEventListener('click', function() {{
                        document.getElementById('chat-input').value = btn.dataset.query;
                        sendChat();
                    }});
                }});
                msgs.appendChild(botDiv);
                msgs.scrollTop = msgs.scrollHeight;
                document.getElementById('chat-send').disabled = false;
            }} else if (attempts > 60) {{
                clearInterval(pollTimer);
                clearInterval(progressTimer);
                pollTimer = null;
                typingDiv.remove();
                const errDiv = document.createElement('div');
                errDiv.className = 'chat-msg bot';
                errDiv.textContent = 'Sorry, the request timed out. Please try again.';
                msgs.appendChild(errDiv);
                msgs.scrollTop = msgs.scrollHeight;
                document.getElementById('chat-send').disabled = false;
            }}
        }}).catch(function() {{}});
    }}, 2000);
}}
</script>

</body>
</html>'''

# Write output
from datetime import datetime as _dt
output_path = ROOT / 'wf-revenue-intelligence-dashboard.html'
with open(output_path, 'w', encoding='utf-8') as f:
    f.write(page)

size_kb = output_path.stat().st_size / 1024
print(f"\nDashboard written: {output_path}")
print(f"Size: {size_kb:.0f} KB ({size_kb/1024:.1f} MB)")
print(f"Charts embedded: {len(charts)}")
print("Done!")
