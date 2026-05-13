"""Generate charts from the executive notebook perspective - clean, minimal style."""
import sys, json, os
sys.stdout.reconfigure(encoding='utf-8')

import pandas as pd
import numpy as np
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import seaborn as sns
import warnings
warnings.filterwarnings('ignore')
from io import BytesIO
import base64

# Style
plt.rcParams.update({
    'figure.facecolor': '#fafaf9',
    'axes.facecolor': '#fafaf9',
    'axes.grid': True,
    'grid.alpha': 0.25,
    'grid.color': '#e5e5e5',
    'axes.spines.top': False,
    'axes.spines.right': False,
    'font.size': 11,
    'axes.titlesize': 13,
    'axes.labelsize': 11,
    'font.family': 'sans-serif',
})

COLORS = {
    'primary': '#18181b',
    'gold': '#b8860b',
    'green': '#059669',
    'red': '#dc2626',
    'blue': '#2563eb',
    'muted': '#6b7280',
    'light': '#e5e7eb',
}

DRUG_NAMES = {
    'M01AB': 'Anti-inflammatory (Acetic)',
    'M01AE': 'Anti-inflammatory (Propionic)',
    'N02BA': 'Aspirin-type painkillers',
    'N02BE': 'Paracetamol',
    'N05B': 'Anxiety medication',
    'N05C': 'Sleep aids',
    'R03': 'Respiratory / Inhalers',
    'R06': 'Antihistamines (Allergy)'
}

drug_cols = ['M01AB', 'M01AE', 'N02BA', 'N02BE', 'N05B', 'N05C', 'R03', 'R06']

charts = []

def save_chart(fig, label):
    buf = BytesIO()
    fig.savefig(buf, format='png', dpi=150, bbox_inches='tight', facecolor=fig.get_facecolor())
    buf.seek(0)
    charts.append({'label': label, 'data': base64.b64encode(buf.read()).decode()})
    plt.close(fig)
    print(f'  [OK] {label}')

# Load data
import kagglehub
path = kagglehub.dataset_download('milanzdravkovic/pharma-sales-data')
df = pd.read_csv(os.path.join(path, 'salesdaily.csv'))
df['datum'] = pd.to_datetime(df['datum'])
df = df.sort_values('datum').reset_index(drop=True)

daily = df.groupby(df['datum'].dt.date)[drug_cols].sum().reset_index()
daily.columns = ['date'] + drug_cols
daily['date'] = pd.to_datetime(daily['date'])
daily['total'] = daily[drug_cols].sum(axis=1)

monthly = daily.set_index('date').resample('M')[drug_cols].sum()

print('Generating executive charts...')

# 0. Data overview - volume breakdown by category
fig, axes = plt.subplots(1, 2, figsize=(14, 5))

# Pie chart of total volume share
total_vol = daily[drug_cols].sum().sort_values(ascending=False)
labels = [f'{DRUG_NAMES[d]}\n({d})' for d in total_vol.index]
colors_pie = ['#b8860b', '#d4a847', '#2563eb', '#059669', '#6b7280', '#9ca3af', '#dc2626', '#f87171']
wedges, texts, autotexts = axes[0].pie(total_vol.values, labels=None, autopct='%1.0f%%',
    colors=colors_pie, pctdistance=0.8, startangle=90,
    textprops={'fontsize': 9})
axes[0].set_title('Volume Share by Product', fontweight='bold')
axes[0].legend(labels, loc='center left', bbox_to_anchor=(-0.3, 0.5), fontsize=8, framealpha=0)

# Bar chart of daily averages
drug_order = total_vol.index.tolist()
avg_vals = [daily[d].mean() for d in drug_order]
bar_colors = [COLORS['green'] if cagr_val > 3 else COLORS['gold'] if cagr_val > -3 else COLORS['red']
              for d in drug_order
              for cagr_val in [((daily.set_index('date')[d].resample('Y').sum().iloc[-1] /
                                 daily.set_index('date')[d].resample('Y').sum().iloc[0]) ** (1/5) - 1) * 100]]
axes[1].barh(range(len(drug_order)), avg_vals, color=bar_colors, edgecolor='white')
axes[1].set_yticks(range(len(drug_order)))
axes[1].set_yticklabels([f'{d} - {DRUG_NAMES[d]}' for d in drug_order], fontsize=9)
axes[1].set_xlabel('Avg units / day')
axes[1].set_title('Daily Volume (colored by growth trend)', fontweight='bold')
axes[1].invert_yaxis()

plt.tight_layout()
save_chart(fig, 'Data Overview')

# 1. Monthly volume by group
fig, axes = plt.subplots(2, 2, figsize=(14, 9))
axes = axes.flatten()
groups = [
    ('Pain & Inflammation', ['M01AB', 'M01AE', 'N02BA', 'N02BE']),
    ('Respiratory & Allergy', ['R03', 'R06']),
    ('Mental Health', ['N05B', 'N05C']),
    ('Total Portfolio', drug_cols)
]
for i, (title, cols) in enumerate(groups):
    if title == 'Total Portfolio':
        axes[i].plot(monthly.index, monthly[cols].sum(axis=1),
                     color=COLORS['primary'], linewidth=2)
        axes[i].fill_between(monthly.index, monthly[cols].sum(axis=1),
                             alpha=0.05, color=COLORS['primary'])
    else:
        for col in cols:
            axes[i].plot(monthly.index, monthly[col], label=DRUG_NAMES.get(col, col), linewidth=1.5)
        axes[i].legend(fontsize=9, framealpha=0)
    axes[i].set_title(title, fontweight='bold')
    axes[i].set_ylabel('Units sold')
plt.suptitle('Monthly Sales Volume by Category', fontsize=15, fontweight='bold', y=1.01)
plt.tight_layout()
save_chart(fig, 'Portfolio Volume Trends')

# 2. YoY growth
yearly = daily.set_index('date').resample('Y')[drug_cols].sum()
yearly.index = yearly.index.year
yoy = yearly.pct_change().dropna() * 100

fig, ax = plt.subplots(figsize=(14, 6))
x = np.arange(len(yoy))
width = 0.1
for i, drug in enumerate(drug_cols):
    ax.bar(x + i*width, yoy[drug], width, label=drug, alpha=0.85)
ax.axhline(0, color='black', linewidth=0.8)
ax.set_xticks(x + width * len(drug_cols) / 2)
ax.set_xticklabels(yoy.index.astype(int))
ax.set_ylabel('Growth (%)')
ax.set_title('Year-over-Year Growth by Product', fontweight='bold')
ax.legend(bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=9, framealpha=0)
plt.tight_layout()
save_chart(fig, 'Year-over-Year Growth')

# 3. Day of week
daily_dow = daily.copy()
daily_dow['dow'] = daily_dow['date'].dt.day_name()
dow_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
dow_avg = daily_dow.groupby('dow')[drug_cols].mean().reindex(dow_order)

fig, ax = plt.subplots(figsize=(12, 5))
dow_avg.sum(axis=1).plot(kind='bar', ax=ax, color=COLORS['gold'], edgecolor='white', width=0.7)
ax.set_title('Average Daily Sales by Day of Week', fontweight='bold')
ax.set_ylabel('Total units')
ax.set_xlabel('')
ax.tick_params(axis='x', rotation=0)
weekday_avg = dow_avg.sum(axis=1).iloc[:5].mean()
weekend_avg = dow_avg.sum(axis=1).iloc[5:].mean()
ax.axhline(weekday_avg, color=COLORS['green'], linestyle='--', alpha=0.5)
ax.axhline(weekend_avg, color=COLORS['red'], linestyle='--', alpha=0.5)
plt.tight_layout()
save_chart(fig, 'Day-of-Week Pattern')

# 4. Monthly seasonal
daily_month = daily.copy()
daily_month['month'] = daily_month['date'].dt.month
month_avg = daily_month.groupby('month')[drug_cols].mean()
seasonal_drugs = ['R03', 'R06', 'M01AB', 'N02BE']

fig, ax = plt.subplots(figsize=(12, 5))
month_names = ['Jan','Feb','Mar','Apr','May','Jun','Jul','Aug','Sep','Oct','Nov','Dec']
for drug in seasonal_drugs:
    ax.plot(range(1,13), month_avg[drug], marker='o', linewidth=2, label=DRUG_NAMES[drug], markersize=6)
ax.set_xticks(range(1,13))
ax.set_xticklabels(month_names)
ax.set_title('Monthly Seasonal Patterns (Key Products)', fontweight='bold')
ax.set_ylabel('Avg daily units')
ax.legend(framealpha=0)
plt.tight_layout()
save_chart(fig, 'Monthly Seasonality')

# 5. Forecast - Exponential Smoothing (Holt-Winters) with weekly seasonality
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

series = daily.set_index('date')['N02BE'].asfreq('D').fillna(method='ffill')
train = series[:-90]
test = series[-90:]

# Holt-Winters: handles trend + weekly seasonality naturally
hw_model = ExponentialSmoothing(train, trend='add', seasonal='add', seasonal_periods=7,
                                 damped_trend=True).fit(optimized=True)
pred_hw = hw_model.forecast(90)

# Also compute a 7-day rolling average forecast as simple baseline
rolling_baseline = train.rolling(7).mean().iloc[-1]

mae = mean_absolute_error(test, pred_hw)
mape = mean_absolute_percentage_error(test, pred_hw) * 100

# Confidence band via residual std
resid_std = (train - hw_model.fittedvalues).std()
lower = pred_hw - 1.65 * resid_std
upper = pred_hw + 1.65 * resid_std

# Weekly aggregation forecast (much more accurate for decision-making)
weekly_series = daily.set_index('date')['N02BE'].resample('W').sum()
weekly_series = weekly_series.asfreq('W').fillna(method='ffill')
train_w = weekly_series[:-13]  # hold out last 13 weeks (~90 days)
test_w = weekly_series[-13:]

hw_weekly = ExponentialSmoothing(train_w, trend='add', seasonal='mul', seasonal_periods=4,
                                  damped_trend=True).fit(optimized=True)
pred_weekly = hw_weekly.forecast(13)
mape_weekly = mean_absolute_percentage_error(test_w, pred_weekly) * 100

# Also daily level
fig, axes = plt.subplots(2, 1, figsize=(14, 8))

# Daily forecast
axes[0].plot(train.index[-120:], train.values[-120:], color=COLORS['muted'], linewidth=0.8, alpha=0.7, label='Historical')
axes[0].plot(test.index, test.values, color=COLORS['primary'], linewidth=1.2, label='Actual')
axes[0].plot(test.index, pred_hw.values, color=COLORS['gold'], linewidth=2, label=f'Forecast')
axes[0].fill_between(test.index, lower, upper, alpha=0.12, color=COLORS['gold'])
axes[0].axvline(test.index[0], color=COLORS['light'], linestyle='--', linewidth=1)
axes[0].set_title(f'Daily Forecast (accuracy: {100-mape:.0f}%)', fontweight='bold')
axes[0].set_ylabel('Units / day')
axes[0].legend(framealpha=0)

# Weekly forecast
resid_w_std = (train_w - hw_weekly.fittedvalues).std()
lower_w = pred_weekly - 1.65 * resid_w_std
upper_w = pred_weekly + 1.65 * resid_w_std

axes[1].plot(train_w.index[-26:], train_w.values[-26:], color=COLORS['muted'], linewidth=1, alpha=0.7, label='Historical')
axes[1].plot(test_w.index, test_w.values, color=COLORS['primary'], linewidth=1.5, label='Actual')
axes[1].plot(test_w.index, pred_weekly.values, color=COLORS['gold'], linewidth=2.5, label=f'Forecast')
axes[1].fill_between(test_w.index, lower_w, upper_w, alpha=0.12, color=COLORS['gold'])
axes[1].axvline(test_w.index[0], color=COLORS['light'], linestyle='--', linewidth=1)
axes[1].set_title(f'Weekly Forecast (accuracy: {100-mape_weekly:.0f}%)', fontweight='bold')
axes[1].set_ylabel('Units / week')
axes[1].legend(framealpha=0)

plt.suptitle('Paracetamol Demand Forecast (Exponential Smoothing)', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
save_chart(fig, 'Demand Forecast')
print(f'    Daily MAPE: {mape:.1f}% | Weekly MAPE: {mape_weekly:.1f}%')

# 6. Anomaly detection
fig, axes = plt.subplots(2, 2, figsize=(14, 8))
axes = axes.flatten()
risk_drugs = ['R03', 'N02BE', 'R06', 'N05B']

for i, drug in enumerate(risk_drugs):
    s = daily.set_index('date')[drug]
    q1, q3 = s.quantile(0.25), s.quantile(0.75)
    iqr = q3 - q1
    threshold = q3 + 2 * iqr
    anomalies = s[s > threshold]

    axes[i].plot(s.index, s.values, color=COLORS['muted'], linewidth=0.5, alpha=0.7)
    axes[i].scatter(anomalies.index, anomalies.values, color=COLORS['red'], s=20, zorder=5)
    axes[i].axhline(threshold, color=COLORS['gold'], linestyle='--', linewidth=1, alpha=0.7)
    axes[i].set_title(f'{DRUG_NAMES[drug]} ({len(anomalies)} spike days)', fontweight='bold')
    axes[i].set_ylabel('Units')

plt.suptitle('Demand Spike Detection - Stockout Risk', fontsize=14, fontweight='bold', y=1.01)
plt.tight_layout()
save_chart(fig, 'Demand Spikes')

# 7. Co-purchase heatmap
corr = daily[drug_cols].corr()
fig, ax = plt.subplots(figsize=(9, 7))
mask = np.triu(np.ones_like(corr, dtype=bool))
labels = [DRUG_NAMES.get(c, c).split('(')[0].strip() for c in drug_cols]
sns.heatmap(corr, mask=mask, annot=True, fmt='.2f', cmap='YlOrBr',
            center=0.15, ax=ax, square=True, linewidths=0.5,
            xticklabels=labels, yticklabels=labels,
            cbar_kws={'label': 'Co-purchase strength'})
ax.set_title('Products Bought Together', fontweight='bold', pad=15)
plt.tight_layout()
save_chart(fig, 'Co-Purchase Heatmap')

# 8. Lifecycle map
lifecycle = []
for drug in drug_cols:
    series_m = daily.set_index('date')[drug].resample('M').sum()
    first_12 = series_m.iloc[:12].mean()
    last_12 = series_m.iloc[-12:].mean()
    growth = (last_12 - first_12) / first_12 * 100
    if growth > 15:
        stage = 'GROW'
    elif growth > -5:
        stage = 'MAINTAIN'
    else:
        stage = 'REDUCE'
    lifecycle.append({'drug': drug, 'growth': growth, 'stage': stage, 'volume': daily[drug].mean()})

lf_df = pd.DataFrame(lifecycle)

fig, ax = plt.subplots(figsize=(10, 6))
colors_map = {'GROW': COLORS['green'], 'MAINTAIN': COLORS['gold'], 'REDUCE': COLORS['red']}
c = [colors_map[d] for d in lf_df['stage']]
ax.scatter(lf_df['volume'], lf_df['growth'], c=c, s=200, edgecolors='white', linewidth=2, zorder=5)
for _, row in lf_df.iterrows():
    ax.annotate(row['drug'], (row['volume'], row['growth']),
                fontsize=9, ha='center', va='bottom', fontweight='bold',
                xytext=(0, 8), textcoords='offset points')
ax.axhline(0, color=COLORS['muted'], linestyle='-', linewidth=0.5)
ax.axhline(15, color=COLORS['green'], linestyle='--', linewidth=0.8, alpha=0.5)
ax.axhline(-5, color=COLORS['red'], linestyle='--', linewidth=0.8, alpha=0.5)
ax.set_xlabel('Average Daily Volume (market size)')
ax.set_ylabel('6-Year Growth %')
ax.set_title('Product Lifecycle: Where to Invest', fontweight='bold')
from matplotlib.patches import Patch
legend_elements = [
    Patch(facecolor=COLORS['green'], label='GROW - Increase investment'),
    Patch(facecolor=COLORS['gold'], label='MAINTAIN - Hold steady'),
    Patch(facecolor=COLORS['red'], label='REDUCE - Cut & redirect'),
]
ax.legend(handles=legend_elements, loc='upper left', framealpha=0)
plt.tight_layout()
save_chart(fig, 'Lifecycle Map')

# Save
with open('_exec_charts.json', 'w', encoding='utf-8') as f:
    json.dump(charts, f)

print(f'\nDone: {len(charts)} charts saved to _exec_charts.json')
