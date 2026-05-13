"""Generate chart data for the showcase webpage."""
import sys, os, json
sys.stdout.reconfigure(encoding='utf-8')
sys.path.insert(0, 'notebooks')
os.environ['MPLBACKEND'] = 'Agg'

import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
import base64
from io import BytesIO
import warnings
warnings.filterwarnings('ignore')

import seaborn as sns
sns.set_theme(style='whitegrid')

from insight_utils import (
    detect_schema, pareto_analysis, revenue_trend, compute_rfm,
    detect_anomalies_iqr, detect_seasonality, InsightCollector
)

# Dark theme for charts
plt.rcParams.update({
    'figure.facecolor': '#1a1a2e',
    'axes.facecolor': '#1a1a2e',
    'text.color': 'white',
    'axes.labelcolor': 'white',
    'xtick.color': 'white',
    'ytick.color': 'white',
    'axes.edgecolor': '#333',
    'grid.color': '#333',
    'grid.alpha': 0.3,
})

all_charts = []

def save_fig(label, section):
    buf = BytesIO()
    plt.savefig(buf, format='png', dpi=110, bbox_inches='tight')
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    all_charts.append({'label': label, 'section': section, 'data': b64})
    plt.close('all')
    print(f"  Saved: {label}")


# =============================================================================
# PHARMA DATA
# =============================================================================
print("\n=== PHARMA DATASET ===")
import kagglehub
path = kagglehub.dataset_download("milanzdravkovic/pharma-sales-data")
df_pharma = pd.read_csv(os.path.join(path, 'salesdaily.csv'))
df_pharma['datum'] = pd.to_datetime(df_pharma['datum'])
df_pharma = df_pharma.sort_values('datum').reset_index(drop=True)
drug_cols = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']

daily_pharma = df_pharma.groupby(df_pharma['datum'].dt.date)[drug_cols].sum().reset_index()
daily_pharma.columns = ['date'] + drug_cols
daily_pharma['date'] = pd.to_datetime(daily_pharma['date'])
daily_pharma['total'] = daily_pharma[drug_cols].sum(axis=1)

print(f"  Loaded: {len(df_pharma):,} records, {len(daily_pharma)} days")

# Pharma Chart 1: Monthly volume trends
monthly_pharma = daily_pharma.set_index('date').resample('M')[drug_cols].sum()
fig, axes = plt.subplots(2, 2, figsize=(14, 10))
groups = [
    ('Anti-inflammatory', ['M01AB', 'M01AE'], ['#74b9ff', '#a29bfe']),
    ('Analgesics', ['N02BA', 'N02BE'], ['#fdcb6e', '#e94560']),
    ('Sedatives/Hypnotics', ['N05B', 'N05C'], ['#00b894', '#55efc4']),
    ('Respiratory', ['R03', 'R06'], ['#ff7675', '#fab1a0']),
]
for i, (title, cols, colors) in enumerate(groups):
    ax = axes[i//2][i%2]
    for col, color in zip(cols, colors):
        ax.plot(monthly_pharma.index, monthly_pharma[col], label=col, linewidth=2, color=color)
    ax.set_title(title, fontsize=12, fontweight='bold')
    ax.legend(fontsize=9)
    ax.set_ylabel('Monthly Units')
plt.suptitle('Pharma Drug Category Trends (2014-2019)', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
save_fig('Drug Category Volume Trends (Monthly)', 'pharma')

# Pharma Chart 2: Seasonality - Day of Week
dow_pharma = df_pharma.copy()
dow_pharma['dow'] = dow_pharma['datum'].dt.day_name()
dow_avg = dow_pharma.groupby('dow')[drug_cols].mean()
dow_avg = dow_avg.reindex(['Monday','Tuesday','Wednesday','Thursday','Friday','Saturday','Sunday'])

fig, ax = plt.subplots(figsize=(12, 6))
dow_avg.plot(kind='bar', ax=ax, width=0.75, colormap='Set2')
ax.set_title('Average Hourly Sales by Day of Week', fontsize=14, fontweight='bold')
ax.set_ylabel('Avg Units/Hour')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
ax.set_xticklabels(ax.get_xticklabels(), rotation=45, ha='right')
plt.tight_layout()
save_fig('Day-of-Week Seasonality Pattern', 'pharma')

# Pharma Chart 3: Monthly seasonality
monthly_pattern = daily_pharma.copy()
monthly_pattern['month'] = monthly_pattern['date'].dt.month
month_avg = monthly_pattern.groupby('month')[drug_cols].mean()

fig, ax = plt.subplots(figsize=(12, 6))
for col, color in zip(drug_cols, ['#74b9ff','#a29bfe','#fdcb6e','#e94560','#00b894','#55efc4','#ff7675','#fab1a0']):
    ax.plot(month_avg.index, month_avg[col], '-o', label=col, linewidth=2, markersize=5, color=color)
ax.set_title('Monthly Seasonal Pattern (Avg Daily Volume by Month)', fontsize=14, fontweight='bold')
ax.set_xlabel('Month')
ax.set_ylabel('Avg Daily Units')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
ax.set_xticks(range(1, 13))
ax.set_xticklabels(['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec'])
plt.tight_layout()
save_fig('Monthly Seasonal Patterns', 'pharma')

# Pharma Chart 4: SARIMA Forecast
from statsmodels.tsa.statespace.sarimax import SARIMAX
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

top_drug = 'N02BE'
series = daily_pharma.set_index('date')[top_drug].asfreq('D').ffill()
train = series[:-90]
test = series[-90:]

model = SARIMAX(train, order=(1,1,1), seasonal_order=(1,1,1,7),
                enforce_stationarity=False, enforce_invertibility=False)
fitted = model.fit(disp=False, maxiter=200)
pred = fitted.forecast(steps=90)
mae = mean_absolute_error(test, pred)
mape = mean_absolute_percentage_error(test, pred) * 100

fig, ax = plt.subplots(figsize=(14, 6))
ax.plot(train.index[-180:], train.values[-180:], color='#74b9ff', alpha=0.7, linewidth=1, label='Training Data')
ax.plot(test.index, test.values, color='#00b894', linewidth=2, label='Actual (Holdout)')
ax.plot(test.index, pred.values, color='#e94560', linewidth=2, linestyle='--', label=f'SARIMA Forecast (MAPE={mape:.1f}%)')
ax.axvline(test.index[0], color='white', linestyle=':', alpha=0.5)
ax.fill_between(test.index, pred.values * 0.7, pred.values * 1.3, alpha=0.1, color='#e94560')
ax.set_title(f'N02BE (Paracetamol) — SARIMA(1,1,1)(1,1,1,7) 90-Day Forecast', fontsize=14, fontweight='bold')
ax.set_ylabel('Daily Units')
ax.legend(fontsize=11)
plt.tight_layout()
save_fig('SARIMA Demand Forecast — N02BE', 'pharma')

# Pharma Chart 5: Anomaly detection
fig, axes = plt.subplots(2, 4, figsize=(18, 8))
axes = axes.flatten()
anomaly_counts = {}
for i, drug in enumerate(drug_cols):
    s = daily_pharma.set_index('date')[drug]
    anom = detect_anomalies_iqr(s, factor=2.0)
    anomaly_counts[drug] = int(anom.sum())
    axes[i].plot(s.index, s.values, color='#74b9ff', alpha=0.5, linewidth=0.5)
    if anom.sum() > 0:
        axes[i].scatter(s[anom].index, s[anom].values, color='#e94560', s=15, zorder=5)
    axes[i].set_title(f'{drug} ({anom.sum()} anomalies)', fontsize=10)
plt.suptitle('Anomaly Detection — All Drug Categories (IQR Method, factor=2.0)', fontsize=13, fontweight='bold', y=1.01)
plt.tight_layout()
save_fig('Anomaly Detection (All Drugs)', 'pharma')

# Pharma Chart 6: Co-prescription correlation
daily_corr = daily_pharma[drug_cols].corr()
fig, ax = plt.subplots(figsize=(9, 8))
mask = np.triu(np.ones_like(daily_corr, dtype=bool))
sns.heatmap(daily_corr, mask=mask, annot=True, fmt='.3f', cmap='RdBu_r',
            center=0, ax=ax, square=True, linewidths=0.5,
            cbar_kws={'shrink': 0.8})
ax.set_title('Drug Co-Prescription Correlation Matrix', fontsize=14, fontweight='bold')
plt.tight_layout()
save_fig('Co-Prescription Correlation Matrix', 'pharma')

# Pharma Chart 7: Lifecycle classification
lifecycle_data = []
for drug in drug_cols:
    s = daily_pharma.set_index('date')[drug].resample('M').sum()
    first_year = s.iloc[:12].mean()
    last_year = s.iloc[-12:].mean()
    growth = (last_year - first_year) / first_year * 100
    slope_recent = np.polyfit(np.arange(12), s.iloc[-12:].values, 1)[0]
    if slope_recent > 0 and growth > 10:
        stage = 'Growth'
    elif abs(growth) <= 10 or (slope_recent < 0 and growth > 0):
        stage = 'Maturity'
    else:
        stage = 'Decline'
    lifecycle_data.append({'drug': drug, 'growth': growth, 'avg_vol': s.mean(), 'stage': stage})

lc_df = pd.DataFrame(lifecycle_data)
colors_lc = {'Growth': '#00b894', 'Maturity': '#74b9ff', 'Decline': '#e94560'}

fig, ax = plt.subplots(figsize=(12, 7))
for stage, color in colors_lc.items():
    subset = lc_df[lc_df['stage'] == stage]
    ax.scatter(subset['avg_vol'], subset['growth'], c=color, s=200, label=stage, edgecolors='white', linewidth=1.5, zorder=5)
    for _, row in subset.iterrows():
        ax.annotate(row['drug'], (row['avg_vol'], row['growth']), fontsize=10,
                   ha='center', va='bottom', color='white', fontweight='bold',
                   xytext=(0, 8), textcoords='offset points')
ax.axhline(0, color='white', linestyle='--', alpha=0.3)
ax.axhline(10, color='#00b894', linestyle=':', alpha=0.3)
ax.axhline(-10, color='#e94560', linestyle=':', alpha=0.3)
ax.set_xlabel('Avg Monthly Volume', fontsize=12)
ax.set_ylabel('Total Growth (%)', fontsize=12)
ax.set_title('Drug Lifecycle Map — Growth vs Volume', fontsize=14, fontweight='bold')
ax.legend(fontsize=12, framealpha=0.3)
plt.tight_layout()
save_fig('Drug Lifecycle Map', 'pharma')

# Pharma Chart 8: YoY Growth
yearly = daily_pharma.set_index('date').resample('YE')[drug_cols].sum()
yearly.index = yearly.index.year
yoy = yearly.pct_change() * 100
yoy = yoy.dropna()

fig, ax = plt.subplots(figsize=(14, 6))
x = np.arange(len(yoy))
width = 0.1
for i, (drug, color) in enumerate(zip(drug_cols, ['#74b9ff','#a29bfe','#fdcb6e','#e94560','#00b894','#55efc4','#ff7675','#fab1a0'])):
    ax.bar(x + i*width, yoy[drug], width, label=drug, color=color)
ax.set_xticks(x + width*3.5)
ax.set_xticklabels(yoy.index.astype(int))
ax.axhline(0, color='white', linewidth=0.5)
ax.set_title('Year-over-Year Volume Growth by Drug (%)', fontsize=14, fontweight='bold')
ax.set_ylabel('YoY Growth (%)')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9)
plt.tight_layout()
save_fig('Year-over-Year Growth', 'pharma')

# =============================================================================
# OLIST DATA
# =============================================================================
print("\n=== OLIST DATASET ===")
path = kagglehub.dataset_download('olistbr/brazilian-ecommerce')
orders = pd.read_csv(os.path.join(path, 'olist_orders_dataset.csv'))
items = pd.read_csv(os.path.join(path, 'olist_order_items_dataset.csv'))
products = pd.read_csv(os.path.join(path, 'olist_products_dataset.csv'))
customers = pd.read_csv(os.path.join(path, 'olist_customers_dataset.csv'))

df = items.merge(orders[['order_id','customer_id','order_purchase_timestamp','order_status']], on='order_id', how='left')
df = df.merge(products[['product_id','product_category_name']], on='product_id', how='left')
df = df.merge(customers[['customer_id','customer_unique_id','customer_state','customer_city']], on='customer_id', how='left')
df['order_date'] = pd.to_datetime(df['order_purchase_timestamp'])
df['revenue'] = df['price'] + df['freight_value']
df = df[df['order_status'] == 'delivered'].copy()
print(f"  Loaded: {len(df):,} rows, R${df['revenue'].sum():,.0f} revenue")

# Olist Chart 1: Monthly revenue
monthly_ol = df.set_index('order_date').resample('M')['revenue'].sum().reset_index()
monthly_ol.columns = ['period', 'revenue']
monthly_ol = monthly_ol.iloc[1:-1]
monthly_ol['growth'] = monthly_ol['revenue'].pct_change() * 100

fig, ax1 = plt.subplots(figsize=(14, 6))
ax1.plot(monthly_ol['period'], monthly_ol['revenue'], 'o-', color='#74b9ff', linewidth=2.5, markersize=6)
ax1.fill_between(monthly_ol['period'], monthly_ol['revenue'], alpha=0.1, color='#74b9ff')
ax1.set_title('Olist Monthly Revenue — Growth Trajectory', fontsize=14, fontweight='bold')
ax1.set_ylabel('Revenue (R$)', fontsize=12)
ax2 = ax1.twinx()
colors_bar = ['#00b894' if g > 0 else '#e94560' for g in monthly_ol['growth'].fillna(0)]
ax2.bar(monthly_ol['period'], monthly_ol['growth'].fillna(0), width=20, alpha=0.3, color=colors_bar)
ax2.set_ylabel('MoM Growth %', fontsize=12, color='#aaa')
ax2.axhline(0, color='white', linewidth=0.3)
plt.tight_layout()
save_fig('Monthly Revenue with Growth Rate', 'olist')

# Olist Chart 2: Top categories
cat_rev = df.groupby('product_category_name')['revenue'].sum().sort_values(ascending=True).tail(15)
fig, ax = plt.subplots(figsize=(12, 7))
bars = ax.barh(range(len(cat_rev)), cat_rev.values, color='#74b9ff', edgecolor='none')
ax.set_yticks(range(len(cat_rev)))
ax.set_yticklabels(cat_rev.index, fontsize=9)
ax.set_title('Top 15 Product Categories by Revenue', fontsize=14, fontweight='bold')
ax.set_xlabel('Revenue (R$)')
for i, v in enumerate(cat_rev.values):
    ax.text(v + cat_rev.max()*0.01, i, f'R${v:,.0f}', va='center', fontsize=8, color='white')
plt.tight_layout()
save_fig('Top Product Categories', 'olist')

# Olist Chart 3: Geographic map (states)
state_rev = df.groupby('customer_state')['revenue'].sum().sort_values(ascending=True).tail(20)
state_share = state_rev / df['revenue'].sum() * 100

fig, ax = plt.subplots(figsize=(12, 8))
colors_geo = plt.cm.YlOrRd(np.linspace(0.2, 0.9, len(state_rev)))
ax.barh(range(len(state_rev)), state_rev.values, color=colors_geo, edgecolor='none')
ax.set_yticks(range(len(state_rev)))
ax.set_yticklabels(state_rev.index, fontsize=10)
ax.set_title('Revenue by Brazilian State (Heat-Encoded)', fontsize=14, fontweight='bold')
ax.set_xlabel('Revenue (R$)')
for i, (v, pct) in enumerate(zip(state_rev.values, state_share.values)):
    ax.text(v + state_rev.max()*0.01, i, f'{pct:.1f}%', va='center', fontsize=9, color='white')
plt.tight_layout()
save_fig('Geographic Revenue Heatmap', 'olist')

# Olist Chart 4: Pareto
product_rev = df.groupby('product_id')['revenue'].sum().sort_values(ascending=False)
cum = product_rev.cumsum() / product_rev.sum() * 100
n_80 = int((cum <= 80).sum())

fig, ax1 = plt.subplots(figsize=(14, 6))
ax1.bar(range(min(150, len(product_rev))), product_rev.values[:150], color='#74b9ff', alpha=0.7, width=1)
ax1.set_ylabel('Revenue (R$)', color='#74b9ff')
ax2 = ax1.twinx()
ax2.plot(range(min(150, len(cum))), cum.values[:150], color='#e94560', linewidth=2.5)
ax2.axhline(80, color='#e94560', linestyle='--', alpha=0.7)
ax2.axvline(n_80, color='#fdcb6e', linestyle='--', alpha=0.7)
ax2.set_ylabel('Cumulative %', color='#e94560')
ax2.set_ylim(0, 105)
ax1.set_xlabel('Product Rank')
ax1.set_title(f'Product Revenue Pareto — {n_80:,} products ({n_80/len(product_rev)*100:.1f}%) drive 80% of revenue', fontsize=13, fontweight='bold')
plt.tight_layout()
save_fig('Pareto Analysis (80/20 Rule)', 'olist')

# Olist Chart 5: Anomaly detection
daily_rev = df.set_index('order_date').resample('D')['revenue'].sum()
daily_rev = daily_rev[daily_rev > 0]
anomalies = detect_anomalies_iqr(daily_rev, factor=2.0)

fig, ax = plt.subplots(figsize=(14, 5))
ax.plot(daily_rev.index, daily_rev.values, color='#74b9ff', alpha=0.6, linewidth=0.8)
ax.scatter(daily_rev[anomalies].index, daily_rev[anomalies].values, color='#e94560', s=50, zorder=5, label=f'Anomalies ({anomalies.sum()})')
# Add mean and bands
mean_val = daily_rev.mean()
std_val = daily_rev.std()
ax.axhline(mean_val, color='#00b894', linestyle='-', alpha=0.5, label=f'Mean: R${mean_val:,.0f}')
ax.axhline(mean_val + 2*std_val, color='#fdcb6e', linestyle='--', alpha=0.5, label=f'+2 Std: R${mean_val+2*std_val:,.0f}')
ax.set_title(f'Daily Revenue — Anomaly Detection ({anomalies.sum()} days flagged)', fontsize=14, fontweight='bold')
ax.set_ylabel('Revenue (R$)')
ax.legend(fontsize=10)
plt.tight_layout()
save_fig('Revenue Anomaly Detection', 'olist')

# Olist Chart 6: RFM Segmentation
rfm = compute_rfm(df, 'customer_unique_id', 'order_date', 'revenue')
seg_counts = rfm['segment'].value_counts()
seg_revenue = rfm.groupby('segment')['monetary'].sum().sort_values(ascending=False)

fig, axes = plt.subplots(1, 2, figsize=(14, 5))
colors_rfm = ['#00b894','#74b9ff','#a29bfe','#fdcb6e','#e94560','#636e72']
seg_counts.plot(kind='bar', ax=axes[0], color=colors_rfm[:len(seg_counts)], edgecolor='none')
axes[0].set_title('Customer Count by Segment', fontsize=12, fontweight='bold')
axes[0].set_ylabel('Customers')
axes[0].tick_params(axis='x', rotation=45)

seg_revenue.plot(kind='bar', ax=axes[1], color=colors_rfm[:len(seg_revenue)], edgecolor='none')
axes[1].set_title('Revenue by Segment', fontsize=12, fontweight='bold')
axes[1].set_ylabel('Revenue (R$)')
axes[1].tick_params(axis='x', rotation=45)
plt.suptitle('RFM Customer Segmentation', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
save_fig('RFM Customer Segmentation', 'olist')

# Olist Chart 7: Geo expansion scoring
state_pop = {
    'SP': 46.6, 'MG': 21.4, 'RJ': 17.5, 'BA': 14.9, 'PR': 11.6,
    'RS': 11.4, 'PE': 9.6, 'CE': 9.2, 'PA': 8.7, 'MA': 7.1,
    'SC': 7.3, 'GO': 7.1, 'PB': 4.1, 'AM': 4.2, 'ES': 4.1,
    'RN': 3.5, 'AL': 3.4, 'MT': 3.6, 'PI': 3.3, 'DF': 3.1,
}
geo_df = df.groupby('customer_state')['revenue'].sum().reset_index()
geo_df.columns = ['state', 'revenue']
geo_df['population'] = geo_df['state'].map(state_pop)
geo_df = geo_df.dropna()
geo_df['rev_per_capita'] = geo_df['revenue'] / (geo_df['population'] * 1e6)
geo_df['penetration'] = geo_df['rev_per_capita'] / geo_df['rev_per_capita'].max()
geo_df['opportunity'] = (1 - geo_df['penetration']) * geo_df['population']
geo_df = geo_df.sort_values('opportunity', ascending=False)

fig, ax = plt.subplots(figsize=(12, 7))
top_opp = geo_df.head(12)
colors_opp = plt.cm.YlOrRd(1 - top_opp['penetration'].values)
ax.barh(range(len(top_opp)), top_opp['opportunity'], color=colors_opp, edgecolor='none')
ax.set_yticks(range(len(top_opp)))
labels = [f"{row['state']} (Pop: {row['population']:.1f}M, Pen: {row['penetration']:.0%})" for _, row in top_opp.iterrows()]
ax.set_yticklabels(labels, fontsize=9)
ax.set_title('Geo-Expansion Opportunity Score (Higher = More Opportunity)', fontsize=14, fontweight='bold')
ax.set_xlabel('Opportunity Score')
ax.invert_yaxis()
plt.tight_layout()
save_fig('Geo-Expansion Opportunity Scoring', 'olist')

# =============================================================================
# SAVE ALL
# =============================================================================
print(f"\n=== TOTAL: {len(all_charts)} charts generated ===")
with open('_all_charts.json', 'w', encoding='utf-8') as f:
    json.dump(all_charts, f)
print("Saved to _all_charts.json")
