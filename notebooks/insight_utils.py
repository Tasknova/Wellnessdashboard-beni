"""
Insight Generator Framework — Shared Utilities
================================================
Reusable helper functions for the Invoice Data Insight Generator POC.
Provides schema detection, insight formatters, narrative generators,
and common chart templates across all analysis notebooks.
"""

import pandas as pd
import numpy as np
from typing import Optional
import warnings
warnings.filterwarnings('ignore')


# =============================================================================
# SCHEMA DETECTION & COLUMN CLASSIFICATION
# =============================================================================

COLUMN_ROLES = [
    'date', 'order_id', 'customer_id', 'product_id', 'product_name',
    'category', 'quantity', 'unit_price', 'revenue', 'geo_country',
    'geo_region', 'geo_city', 'latitude', 'longitude'
]


def detect_schema(df: pd.DataFrame) -> dict:
    """
    Auto-classify DataFrame columns into semantic roles.
    Returns a dict mapping role -> column_name (or None).
    """
    schema = {role: None for role in COLUMN_ROLES}
    cols_lower = {c: c.lower().replace(' ', '_').replace('-', '_') for c in df.columns}

    # Date columns
    for col, norm in cols_lower.items():
        if df[col].dtype == 'datetime64[ns]' or 'date' in norm or 'time' in norm:
            if schema['date'] is None:
                try:
                    pd.to_datetime(df[col].head(100))
                    schema['date'] = col
                except Exception:
                    pass

    # ID columns
    id_patterns = {
        'order_id': ['order_id', 'orderid', 'invoice', 'invoiceno', 'invoice_no', 'transaction_id'],
        'customer_id': ['customer_id', 'customerid', 'cust_id', 'client_id', 'buyer_id'],
        'product_id': ['product_id', 'productid', 'stockcode', 'stock_code', 'sku', 'item_id', 'drug'],
    }
    for role, patterns in id_patterns.items():
        for col, norm in cols_lower.items():
            if any(p in norm for p in patterns):
                schema[role] = col
                break

    # Product name / category
    name_patterns = ['product_name', 'description', 'item_name', 'drug_name']
    cat_patterns = ['category', 'product_category', 'department', 'aisle', 'atc', 'drug_category']
    for col, norm in cols_lower.items():
        if any(p in norm for p in name_patterns) and schema['product_name'] is None:
            schema['product_name'] = col
        if any(p in norm for p in cat_patterns) and schema['category'] is None:
            schema['category'] = col

    # Numeric columns
    price_patterns = ['unit_price', 'unitprice', 'price', 'selling_price']
    qty_patterns = ['quantity', 'qty', 'units', 'volume', 'count']
    rev_patterns = ['revenue', 'total', 'amount', 'sales', 'payment_value', 'totalcharges']
    for col, norm in cols_lower.items():
        if df[col].dtype in ['float64', 'int64', 'float32', 'int32']:
            if any(p in norm for p in price_patterns) and schema['unit_price'] is None:
                schema['unit_price'] = col
            elif any(p in norm for p in qty_patterns) and schema['quantity'] is None:
                schema['quantity'] = col
            elif any(p in norm for p in rev_patterns) and schema['revenue'] is None:
                schema['revenue'] = col

    # Geography columns
    geo_country_patterns = ['country', 'nation']
    geo_region_patterns = ['state', 'region', 'province', 'county']
    geo_city_patterns = ['city', 'town', 'municipality']
    lat_patterns = ['lat', 'latitude']
    lng_patterns = ['lng', 'longitude', 'lon']
    for col, norm in cols_lower.items():
        if any(p in norm for p in geo_country_patterns) and schema['geo_country'] is None:
            schema['geo_country'] = col
        if any(p in norm for p in geo_region_patterns) and schema['geo_region'] is None:
            schema['geo_region'] = col
        if any(p in norm for p in geo_city_patterns) and schema['geo_city'] is None:
            schema['geo_city'] = col
        if any(p == norm for p in lat_patterns) and schema['latitude'] is None:
            schema['latitude'] = col
        if any(p == norm for p in lng_patterns) and schema['longitude'] is None:
            schema['longitude'] = col

    return schema


def print_schema(schema: dict):
    """Pretty-print detected schema mapping."""
    print("=" * 60)
    print("DETECTED SCHEMA")
    print("=" * 60)
    for role, col in schema.items():
        status = f"→ '{col}'" if col else "  (not found)"
        print(f"  {role:15s} {status}")
    print()


# =============================================================================
# DATA PROFILING
# =============================================================================

def data_profile(df: pd.DataFrame) -> pd.DataFrame:
    """Generate a concise data profile summary."""
    profile = pd.DataFrame({
        'dtype': df.dtypes,
        'non_null': df.notnull().sum(),
        'null_pct': (df.isnull().sum() / len(df) * 100).round(1),
        'nunique': df.nunique(),
        'sample': df.iloc[0] if len(df) > 0 else None,
    })
    return profile


# =============================================================================
# DESCRIPTIVE INSIGHT HELPERS
# =============================================================================

def pareto_analysis(series: pd.Series, label: str = "item") -> pd.DataFrame:
    """
    Compute Pareto (80/20) analysis on a value series.
    Returns DataFrame with cumulative contribution.
    """
    sorted_vals = series.sort_values(ascending=False).reset_index()
    sorted_vals.columns = [label, 'value']
    sorted_vals['cumulative'] = sorted_vals['value'].cumsum()
    sorted_vals['cum_pct'] = sorted_vals['cumulative'] / sorted_vals['value'].sum() * 100
    sorted_vals['rank'] = range(1, len(sorted_vals) + 1)
    sorted_vals['rank_pct'] = sorted_vals['rank'] / len(sorted_vals) * 100

    # Find 80% threshold
    threshold_idx = (sorted_vals['cum_pct'] >= 80).idxmax()
    n_80 = sorted_vals.loc[threshold_idx, 'rank']
    pct_80 = sorted_vals.loc[threshold_idx, 'rank_pct']

    return sorted_vals, n_80, pct_80


def revenue_trend(df: pd.DataFrame, date_col: str, revenue_col: str,
                  freq: str = 'M') -> pd.DataFrame:
    """Aggregate revenue by time period."""
    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col])
    trend = df_copy.set_index(date_col).resample(freq)[revenue_col].sum().reset_index()
    trend.columns = ['period', 'revenue']
    # Growth rates
    trend['growth_pct'] = trend['revenue'].pct_change() * 100
    return trend


def top_bottom_items(df: pd.DataFrame, group_col: str, value_col: str,
                     n: int = 10, agg: str = 'sum') -> tuple:
    """Get top and bottom N items by aggregated value."""
    grouped = df.groupby(group_col)[value_col].agg(agg).sort_values(ascending=False)
    return grouped.head(n), grouped.tail(n)


# =============================================================================
# RFM SEGMENTATION
# =============================================================================

def compute_rfm(df: pd.DataFrame, customer_col: str, date_col: str,
                revenue_col: str, reference_date=None) -> pd.DataFrame:
    """
    Compute RFM (Recency, Frequency, Monetary) scores.
    Returns DataFrame with customer-level RFM metrics and segment labels.
    """
    df_copy = df.copy()
    df_copy[date_col] = pd.to_datetime(df_copy[date_col])

    if reference_date is None:
        reference_date = df_copy[date_col].max() + pd.Timedelta(days=1)

    rfm = df_copy.groupby(customer_col).agg(
        recency=(date_col, lambda x: (reference_date - x.max()).days),
        frequency=(date_col, 'nunique'),
        monetary=(revenue_col, 'sum')
    ).reset_index()

    # Score 1-5 using quantiles
    for col in ['recency', 'frequency', 'monetary']:
        try:
            if col == 'recency':
                rfm[f'{col}_score'] = pd.qcut(rfm[col], 5, labels=False, duplicates='drop') + 1
                rfm[f'{col}_score'] = rfm[f'{col}_score'].max() + 1 - rfm[f'{col}_score']
            else:
                rfm[f'{col}_score'] = pd.qcut(rfm[col], 5, labels=False, duplicates='drop') + 1
        except Exception:
            rfm[f'{col}_score'] = pd.cut(rfm[col], 5, labels=False, duplicates='drop') + 1

    rfm['rfm_score'] = (rfm['recency_score'].astype(int) +
                         rfm['frequency_score'].astype(int) +
                         rfm['monetary_score'].astype(int))

    # Segment labels
    def segment(row):
        r, f, m = int(row['recency_score']), int(row['frequency_score']), int(row['monetary_score'])
        if r >= 4 and f >= 4 and m >= 4:
            return 'Champions'
        elif r >= 3 and f >= 3:
            return 'Loyal'
        elif r >= 4 and f <= 2:
            return 'New Customers'
        elif r <= 2 and f >= 3:
            return 'At Risk'
        elif r <= 2 and f <= 2:
            return 'Lost'
        else:
            return 'Needs Attention'

    rfm['segment'] = rfm.apply(segment, axis=1)
    return rfm


# =============================================================================
# SEASONALITY & TIME SERIES
# =============================================================================

def detect_seasonality(series: pd.Series, period: int = 7) -> dict:
    """
    Simple seasonality detection using autocorrelation.
    Returns dict with detected seasonal periods and strengths.
    """
    from statsmodels.tsa.stattools import acf

    if len(series) < period * 3:
        return {'detected': False, 'reason': 'Insufficient data'}

    # Compute ACF
    nlags = min(len(series) // 2 - 1, period * 4)
    if nlags < period:
        return {'detected': False, 'reason': 'Series too short for period'}

    acf_vals = acf(series.dropna(), nlags=nlags, fft=True)

    # Check for significant peaks at expected periods
    results = {'detected': False, 'periods': []}
    for p in [7, 30, 90, 365]:
        if p < len(acf_vals) and acf_vals[p] > 0.3:
            results['periods'].append({'period': p, 'strength': float(acf_vals[p])})
            results['detected'] = True

    return results


def stl_decompose(series: pd.Series, period: int = 30):
    """Perform STL decomposition. Returns decomposition result."""
    from statsmodels.tsa.seasonal import STL

    series_clean = series.dropna()
    if len(series_clean) < period * 2:
        return None

    stl = STL(series_clean, period=period, robust=True)
    result = stl.fit()
    return result


# =============================================================================
# ANOMALY DETECTION
# =============================================================================

def detect_anomalies_zscore(series: pd.Series, threshold: float = 3.0) -> pd.Series:
    """Detect anomalies using Z-score method. Returns boolean mask."""
    mean = series.mean()
    std = series.std()
    if std == 0:
        return pd.Series(False, index=series.index)
    z_scores = np.abs((series - mean) / std)
    return z_scores > threshold


def detect_anomalies_iqr(series: pd.Series, factor: float = 1.5) -> pd.Series:
    """Detect anomalies using IQR method. Returns boolean mask."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower = q1 - factor * iqr
    upper = q3 + factor * iqr
    return (series < lower) | (series > upper)


# =============================================================================
# NARRATIVE GENERATION
# =============================================================================

def format_currency(val: float) -> str:
    """Format value as currency string."""
    if abs(val) >= 1e6:
        return f"${val/1e6:.1f}M"
    elif abs(val) >= 1e3:
        return f"${val/1e3:.1f}K"
    else:
        return f"${val:.2f}"


def format_pct(val: float) -> str:
    """Format as percentage."""
    return f"{val:+.1f}%" if val != 0 else "0.0%"


def generate_trend_narrative(trend_df: pd.DataFrame) -> str:
    """Generate a narrative sentence from a revenue trend DataFrame."""
    if len(trend_df) < 2:
        return "Insufficient data for trend analysis."

    latest = trend_df.iloc[-1]
    first = trend_df.iloc[0]
    total_growth = (latest['revenue'] - first['revenue']) / first['revenue'] * 100

    avg_growth = trend_df['growth_pct'].mean()
    volatility = trend_df['growth_pct'].std()

    peak_idx = trend_df['revenue'].idxmax()
    peak_period = trend_df.loc[peak_idx, 'period']
    peak_rev = trend_df.loc[peak_idx, 'revenue']

    direction = "grew" if total_growth > 0 else "declined"
    narrative = (
        f"Revenue {direction} {abs(total_growth):.1f}% over the period, "
        f"with average period-over-period growth of {format_pct(avg_growth)}. "
        f"Peak revenue of {format_currency(peak_rev)} was reached in {peak_period}. "
    )

    if volatility > 20:
        narrative += "High volatility suggests significant seasonality or irregular demand patterns."
    elif volatility > 10:
        narrative += "Moderate volatility indicates some seasonal effects."
    else:
        narrative += "Low volatility suggests stable, predictable demand."

    return narrative


def generate_pareto_narrative(n_80: int, pct_80: float, total: int,
                              entity: str = "SKUs") -> str:
    """Generate Pareto analysis narrative."""
    return (
        f"Top {n_80} {entity} ({pct_80:.1f}% of total) account for 80% of revenue. "
        f"This {'high' if pct_80 < 25 else 'moderate' if pct_80 < 50 else 'low'} "
        f"concentration suggests "
        f"{'significant dependency risk on a few key {}'.format(entity) if pct_80 < 25 else 'a relatively diversified portfolio'}."
    )


def generate_rfm_narrative(rfm: pd.DataFrame) -> str:
    """Generate RFM segmentation narrative."""
    seg_counts = rfm['segment'].value_counts()
    total = len(rfm)

    champions_pct = seg_counts.get('Champions', 0) / total * 100
    at_risk_pct = seg_counts.get('At Risk', 0) / total * 100
    lost_pct = seg_counts.get('Lost', 0) / total * 100

    narrative = (
        f"Customer segmentation reveals {champions_pct:.1f}% Champions, "
        f"{at_risk_pct:.1f}% At Risk, and {lost_pct:.1f}% Lost customers. "
    )

    if at_risk_pct > 20:
        narrative += "High at-risk proportion demands immediate retention interventions."
    if champions_pct > 20:
        narrative += "Strong champion base provides stable revenue foundation."

    return narrative


def generate_forecast_narrative(actual: pd.Series, predicted: pd.Series,
                                 periods_ahead: int = 3) -> str:
    """Generate forecasting narrative."""
    last_actual = actual.iloc[-1]
    last_predicted = predicted.iloc[-1] if len(predicted) > 0 else last_actual

    direction = "growth" if last_predicted > last_actual else "decline"
    change_pct = (last_predicted - last_actual) / last_actual * 100

    return (
        f"Forecast indicates {abs(change_pct):.1f}% {direction} "
        f"over the next {periods_ahead} periods. "
    )


# =============================================================================
# CHART TEMPLATES
# =============================================================================

def setup_plotting():
    """Configure common plot settings."""
    import matplotlib.pyplot as plt
    import seaborn as sns
    sns.set_theme(style="whitegrid")
    plt.rcParams['figure.figsize'] = (12, 6)
    plt.rcParams['font.size'] = 11
    return plt, sns


def plot_revenue_trend(trend_df: pd.DataFrame, title: str = "Revenue Trend"):
    """Standard revenue trend chart with growth annotations."""
    plt, sns = setup_plotting()

    fig, ax1 = plt.subplots(figsize=(14, 6))
    ax1.plot(trend_df['period'], trend_df['revenue'], 'b-o', linewidth=2, markersize=4)
    ax1.fill_between(trend_df['period'], trend_df['revenue'], alpha=0.1, color='blue')
    ax1.set_xlabel('Period')
    ax1.set_ylabel('Revenue', color='blue')
    ax1.set_title(title, fontsize=14)
    ax1.tick_params(axis='x', rotation=45)

    # Growth rate on secondary axis
    if 'growth_pct' in trend_df.columns:
        ax2 = ax1.twinx()
        ax2.bar(trend_df['period'], trend_df['growth_pct'], alpha=0.3, color='green', width=20)
        ax2.set_ylabel('Growth %', color='green')
        ax2.axhline(0, color='gray', linestyle='--', alpha=0.5)

    plt.tight_layout()
    plt.show()
    return fig


def plot_pareto(sorted_df: pd.DataFrame, title: str = "Pareto Analysis",
                entity_col: str = "item", n_show: int = 20):
    """Standard Pareto chart (bar + cumulative line)."""
    plt, sns = setup_plotting()

    show_df = sorted_df.head(n_show)
    fig, ax1 = plt.subplots(figsize=(14, 6))

    ax1.bar(range(len(show_df)), show_df['value'], color='steelblue', alpha=0.7)
    ax1.set_xlabel(entity_col)
    ax1.set_ylabel('Value')
    ax1.set_title(title, fontsize=14)
    ax1.set_xticks(range(len(show_df)))
    ax1.set_xticklabels(show_df[entity_col].astype(str).str[:15], rotation=45, ha='right')

    ax2 = ax1.twinx()
    ax2.plot(range(len(show_df)), show_df['cum_pct'], 'r-o', markersize=4)
    ax2.set_ylabel('Cumulative %', color='red')
    ax2.axhline(80, color='red', linestyle='--', alpha=0.5)
    ax2.set_ylim(0, 105)

    plt.tight_layout()
    plt.show()
    return fig


def plot_heatmap_geo(df: pd.DataFrame, geo_col: str, value_col: str,
                     title: str = "Geographic Revenue Distribution"):
    """Plot geographic heatmap as horizontal bar chart (works without map libraries)."""
    plt, sns = setup_plotting()

    geo_revenue = df.groupby(geo_col)[value_col].sum().sort_values(ascending=True)

    fig, ax = plt.subplots(figsize=(10, max(6, len(geo_revenue) * 0.3)))
    geo_revenue.plot(kind='barh', ax=ax, color='steelblue', edgecolor='white')
    ax.set_title(title, fontsize=14)
    ax.set_xlabel('Revenue')
    plt.tight_layout()
    plt.show()
    return fig


# =============================================================================
# INSIGHT SUMMARY COLLECTOR
# =============================================================================

class InsightCollector:
    """Collect and organize insights throughout analysis."""

    def __init__(self):
        self.insights = []

    def add(self, category: str, title: str, narrative: str,
            severity: str = "info", data: dict = None):
        """
        Add an insight.
        severity: 'info', 'warning', 'opportunity', 'risk'
        """
        self.insights.append({
            'category': category,
            'title': title,
            'narrative': narrative,
            'severity': severity,
            'data': data or {}
        })

    def summary(self) -> str:
        """Generate formatted insight summary."""
        lines = []
        lines.append("=" * 70)
        lines.append("INSIGHT SUMMARY")
        lines.append("=" * 70)

        severity_icons = {
            'info': '[INFO]',
            'warning': '[WARNING]',
            'opportunity': '[OPPORTUNITY]',
            'risk': '[RISK]'
        }

        by_category = {}
        for ins in self.insights:
            cat = ins['category']
            if cat not in by_category:
                by_category[cat] = []
            by_category[cat].append(ins)

        for cat, items in by_category.items():
            lines.append(f"\n--- {cat.upper()} ---")
            for item in items:
                icon = severity_icons.get(item['severity'], '')
                lines.append(f"  {icon} {item['title']}")
                lines.append(f"     {item['narrative']}")

        lines.append("\n" + "=" * 70)
        lines.append(f"Total insights generated: {len(self.insights)}")
        return "\n".join(lines)

    def to_dataframe(self) -> pd.DataFrame:
        """Export insights as DataFrame."""
        return pd.DataFrame(self.insights)
