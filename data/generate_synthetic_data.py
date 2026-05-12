"""
Tasknova — WF Revenue Intelligence Synthetic Data Generator
============================================================
Generates 6 calibrated datasets for Wellness Forever pharmacy chain analysis.
Outputs: 6 CSVs + SQLite database (wf_intelligence.db)

Revenue calibrated to ~INR 42.5 Cr/year (30/312 stores ≈ 10% of WF's INR 847 Cr).
Time range: May 2024 – April 2026 (24 months).
"""

import pandas as pd
import numpy as np
import sqlite3
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.stdout.reconfigure(encoding='utf-8')
np.random.seed(42)

OUT_DIR = Path(__file__).parent
DB_PATH = OUT_DIR / 'wf_intelligence.db'

# =============================================================================
# CONSTANTS & REFERENCE DATA
# =============================================================================

CITIES = {
    'Mumbai':     {'stores': 12, 'population_weight': 0.35},
    'Pune':       {'stores': 6,  'population_weight': 0.18},
    'Thane':      {'stores': 4,  'population_weight': 0.12},
    'Navi Mumbai':{'stores': 3,  'population_weight': 0.10},
    'Nashik':     {'stores': 2,  'population_weight': 0.08},
    'Goa':        {'stores': 1,  'population_weight': 0.07},
    'Bengaluru':  {'stores': 2,  'population_weight': 0.10},
}

STORE_TYPES = {
    'Flagship':    {'count': 5,  'size_range': (4000, 6000), 'revenue_mult': 1.8},
    'Standard':    {'count': 18, 'size_range': (1500, 3500), 'revenue_mult': 1.0},
    'Neighborhood':{'count': 7,  'size_range': (500, 1200),  'revenue_mult': 0.55},
}

PINCODES = {
    'Mumbai':      ['400001','400050','400053','400058','400064','400069','400072','400076','400080','400086','400092','400097'],
    'Pune':        ['411001','411004','411014','411021','411038','411045'],
    'Thane':       ['400601','400602','400607','400610'],
    'Navi Mumbai': ['400703','400706','400709'],
    'Nashik':      ['422001','422005'],
    'Goa':         ['403001'],
    'Bengaluru':   ['560001','560034'],
}

# Product categories with margin and mix targets
CATEGORIES = {
    'Rx Medicines':    {'mix': 0.42, 'margin_range': (0.18, 0.22), 'avg_price': 280},
    'OTC Medicines':   {'mix': 0.23, 'margin_range': (0.28, 0.35), 'avg_price': 120},
    'Wellness':        {'mix': 0.15, 'margin_range': (0.32, 0.40), 'avg_price': 350},
    'Beauty & Personal Care': {'mix': 0.12, 'margin_range': (0.30, 0.38), 'avg_price': 220},
    'FMCG':            {'mix': 0.08, 'margin_range': (0.15, 0.22), 'avg_price': 90},
}

# Real Indian pharma brands — mapped to their actual product sub-types
# Each brand maps to the sub-types it actually manufactures
BRAND_SUBTYPES = {
    'Rx Medicines': {
        'Cipla':          ['Tablet', 'Capsule', 'Syrup', 'Inhaler', 'Drops'],
        'Sun Pharma':     ['Tablet', 'Capsule', 'Ointment', 'Gel', 'Injection'],
        'Dr. Reddys':     ['Tablet', 'Capsule', 'Injection', 'Ointment'],
        'Lupin':          ['Tablet', 'Capsule', 'Syrup', 'Suspension'],
        'Zydus':          ['Tablet', 'Capsule', 'Gel', 'Syrup'],
        'Torrent Pharma': ['Tablet', 'Capsule', 'Syrup', 'Injection'],
        'Mankind':        ['Tablet', 'Capsule', 'Injection', 'Powder'],
        'Alkem':          ['Tablet', 'Capsule', 'Syrup', 'Drops'],
        'Glenmark':       ['Tablet', 'Capsule', 'Gel', 'Ointment'],
        'Cadila':         ['Tablet', 'Capsule', 'Gel', 'Syrup'],
        'Ipca':           ['Tablet', 'Capsule', 'Suspension', 'Gel'],
        'Abbott India':   ['Tablet', 'Capsule', 'Syrup', 'Inhaler', 'Powder'],
        'Biocon':         ['Injection', 'Tablet', 'Capsule', 'Powder'],
        'Natco':          ['Tablet', 'Capsule', 'Ointment', 'Drops'],
        'Aurobindo':      ['Tablet', 'Capsule', 'Drops', 'Suspension'],
        'Hetero':         ['Tablet', 'Capsule', 'Injection', 'Powder'],
        'Intas':          ['Tablet', 'Capsule', 'Syrup', 'Drops', 'Injection'],
        'Macleods':       ['Tablet', 'Capsule', 'Syrup', 'Inhaler'],
    },
    'OTC Medicines': {
        'Cipla':      ['Tablet', 'Syrup', 'Drops'],
        'Himalaya':   ['Tablet', 'Syrup', 'Cream', 'Powder', 'Gel'],
        'Dabur':      ['Syrup', 'Drops', 'Balm', 'Oil', 'Gel'],
        'Zandu':      ['Balm', 'Syrup', 'Tablet', 'Ointment'],
        'Vicks':      ['Balm', 'Drops', 'Syrup', 'Lozenges', 'Spray'],
        'Crocin':     ['Tablet', 'Syrup', 'Drops'],
        'Volini':     ['Spray', 'Gel', 'Cream', 'Balm'],
        'Moov':       ['Cream', 'Spray', 'Gel', 'Balm'],
        'Benadryl':   ['Syrup', 'Tablet', 'Drops'],
        'Strepsils':  ['Lozenges', 'Spray'],
        'Burnol':     ['Cream', 'Ointment'],
        'Dettol':     ['Cream', 'Ointment', 'Spray'],
    },
    'Wellness': {
        'Himalaya':            ['Tablet', 'Capsule', 'Powder', 'Oil'],
        'Patanjali':           ['Capsule', 'Powder', 'Oil', 'Syrup'],
        'Amway':               ['Tablet', 'Capsule', 'Protein Bar', 'Drink Mix'],
        'Herbalife':           ['Powder', 'Capsule', 'Drink Mix', 'Tablet'],
        'HealthKart':          ['Powder', 'Capsule', 'Drink Mix', 'Gummies'],
        'MuscleBlaze':         ['Powder', 'Protein Bar', 'Drink Mix', 'Capsule'],
        'Oziva':               ['Capsule', 'Powder', 'Drink Mix', 'Gummies'],
        'Wellbeing Nutrition': ['Capsule', 'Drink Mix', 'Gummies', 'Tablet'],
        'Kapiva':              ['Syrup', 'Drink Mix', 'Capsule', 'Oil'],
        'Setu':                ['Tablet', 'Capsule', 'Gummies', 'Powder'],
    },
    'Beauty & Personal Care': {
        'Lakme':      ['Face Wash', 'Moisturizer', 'Sunscreen', 'Face Mask', 'Serum'],
        'Nivea':      ['Body Lotion', 'Moisturizer', 'Lip Balm', 'Face Wash', 'Sunscreen'],
        'LOreal':     ['Shampoo', 'Conditioner', 'Serum', 'Face Wash', 'Sunscreen'],
        'Biotique':   ['Face Wash', 'Shampoo', 'Conditioner', 'Body Lotion', 'Toner'],
        'Mamaearth':  ['Face Wash', 'Shampoo', 'Body Lotion', 'Sunscreen', 'Serum'],
        'WOW':        ['Shampoo', 'Conditioner', 'Face Wash', 'Body Lotion', 'Serum'],
        'mCaffeine':  ['Face Wash', 'Body Lotion', 'Serum', 'Face Mask', 'Shampoo'],
        'Plum':       ['Face Wash', 'Moisturizer', 'Sunscreen', 'Lip Balm', 'Toner'],
        'Cetaphil':   ['Face Wash', 'Moisturizer', 'Body Lotion', 'Sunscreen'],
        'Neutrogena': ['Face Wash', 'Sunscreen', 'Moisturizer', 'Body Lotion', 'Lip Balm'],
    },
    'FMCG': {
        'Colgate':    ['Toothpaste', 'Toothbrush'],
        'Oral-B':     ['Toothpaste', 'Toothbrush'],
        'Dettol':     ['Hand Wash', 'Sanitizer', 'Soap', 'Wipes'],
        'Savlon':     ['Hand Wash', 'Sanitizer', 'Wipes'],
        'Lifebuoy':   ['Soap', 'Hand Wash', 'Sanitizer'],
        'Pampers':    ['Diaper', 'Wipes'],
        'Huggies':    ['Diaper', 'Wipes'],
        'MamyPoko':   ['Diaper'],
        'Whisper':    ['Sanitary Pad'],
        'Stayfree':   ['Sanitary Pad'],
        'Sofy':       ['Sanitary Pad'],
        'Johnson & Johnson': ['Cotton', 'Bandage', 'Band-Aid'],
        'Himalaya':   ['Soap', 'Wipes', 'Cotton'],
        'Pigeon':     ['Wipes', 'Cotton'],
    },
}

# Flat brand lists (for backward compat)
BRANDS = {cat: list(brands.keys()) for cat, brands in BRAND_SUBTYPES.items()}

# All possible sub-types per category (union of all brand sub-types)
PRODUCT_TYPES = {}
for cat, brands in BRAND_SUBTYPES.items():
    all_types = set()
    for types in brands.values():
        all_types.update(types)
    PRODUCT_TYPES[cat] = sorted(all_types)

# Rx therapeutic areas
RX_THERAPEUTIC = [
    'Anti-diabetic', 'Anti-hypertensive', 'Antibiotic', 'Anti-inflammatory',
    'Gastrointestinal', 'Cardiac', 'Respiratory', 'Dermatological',
    'Neurological', 'Musculoskeletal', 'Hormonal', 'Anti-allergic',
    'Vitamin/Supplement', 'Pain Management', 'Anti-viral',
]

PAYMENT_MODES = ['Cash', 'UPI', 'Credit Card', 'Debit Card', 'Net Banking', 'Wallet']
PAYMENT_WEIGHTS = [0.25, 0.35, 0.15, 0.12, 0.08, 0.05]

CANCELLATION_REASONS = [
    'Customer changed mind', 'Duplicate order', 'Price issue',
    'Product unavailable', 'Delivery delay', 'Wrong item ordered',
]
RETURN_REASONS = [
    'Damaged product', 'Wrong item received', 'Expired product',
    'Quality issue', 'Changed mind', 'Allergic reaction',
]

START_DATE = datetime(2024, 5, 1)
END_DATE = datetime(2026, 4, 30)
TOTAL_DAYS = (END_DATE - START_DATE).days + 1


# =============================================================================
# 1. STORE MASTER
# =============================================================================

def generate_stores() -> pd.DataFrame:
    """Generate 30-row store master."""
    print("Generating Store Master...")
    rows = []
    store_id = 1
    type_pool = []
    for stype, info in STORE_TYPES.items():
        type_pool.extend([stype] * info['count'])
    np.random.shuffle(type_pool)

    city_pool = []
    for city, info in CITIES.items():
        city_pool.extend([city] * info['stores'])

    for i in range(30):
        city = city_pool[i]
        stype = type_pool[i]
        size_lo, size_hi = STORE_TYPES[stype]['size_range']
        size_sqft = np.random.randint(size_lo, size_hi)
        pincode = np.random.choice(PINCODES[city])
        online = True if stype == 'Flagship' else (np.random.random() < 0.6)
        delivery_km = np.random.choice([3, 5, 7, 10]) if online else 0

        rows.append({
            'store_id': f'WF-{store_id:03d}',
            'store_name': f'Wellness Forever {city} {stype[:3].upper()}-{store_id}',
            'city': city,
            'pincode': pincode,
            'store_type': stype,
            'size_sqft': size_sqft,
            'online_enabled': online,
            'delivery_radius_km': delivery_km,
            'opened_date': (START_DATE - timedelta(days=np.random.randint(180, 1800))).strftime('%Y-%m-%d'),
        })
        store_id += 1

    df = pd.DataFrame(rows)
    print(f"  -> {len(df)} stores generated")
    return df


# =============================================================================
# 2. PRODUCT MASTER
# =============================================================================

def generate_products(n=1000) -> pd.DataFrame:
    """Generate ~1K product master with real brand names."""
    print("Generating Product Master...")
    rows = []
    pid = 1

    for cat, info in CATEGORIES.items():
        n_cat = int(n * info['mix'])
        brands = BRANDS[cat]
        brand_subtypes = BRAND_SUBTYPES[cat]
        margin_lo, margin_hi = info['margin_range']

        for _ in range(n_cat):
            brand = np.random.choice(brands)
            ptype = np.random.choice(brand_subtypes[brand])
            is_generic = cat == 'Rx Medicines' and np.random.random() < 0.35
            therapeutic = np.random.choice(RX_THERAPEUTIC) if cat == 'Rx Medicines' else ''

            base_price = np.random.lognormal(
                np.log(info['avg_price']), 0.5
            )
            base_price = max(10, min(5000, base_price))
            mrp = round(base_price, 2)
            margin = np.random.uniform(margin_lo, margin_hi)
            cost = round(mrp * (1 - margin), 2)

            name_prefix = 'Generic ' if is_generic else ''
            suffix = np.random.randint(10, 999)
            product_name = f"{name_prefix}{brand} {ptype} {suffix}"

            rows.append({
                'product_id': f'P-{pid:05d}',
                'product_name': product_name,
                'brand': brand,
                'category': cat,
                'sub_type': ptype,
                'therapeutic_area': therapeutic,
                'is_generic': is_generic,
                'mrp': mrp,
                'cost_price': cost,
                'margin_pct': round(margin * 100, 1),
                'requires_prescription': cat == 'Rx Medicines',
                'is_scheduled': cat == 'Rx Medicines' and np.random.random() < 0.2,
            })
            pid += 1

    df = pd.DataFrame(rows)
    # Ensure we hit ~1K
    if len(df) < n:
        extra = n - len(df)
        extras = df.sample(extra, replace=True).copy()
        extras['product_id'] = [f'P-{pid+i:05d}' for i in range(extra)]
        df = pd.concat([df, extras], ignore_index=True)

    print(f"  -> {len(df)} products generated")
    cat_dist = df['category'].value_counts(normalize=True) * 100
    for c, pct in cat_dist.items():
        print(f"     {c}: {pct:.1f}%")
    return df


# =============================================================================
# 3. CUSTOMER MASTER
# =============================================================================

def generate_customers(n=5000, stores_df=None) -> pd.DataFrame:
    """Generate ~5K customer master."""
    print("Generating Customer Master...")
    rows = []
    city_weights = [CITIES[c]['population_weight'] for c in CITIES]
    cities = list(CITIES.keys())

    for i in range(n):
        city = np.random.choice(cities, p=city_weights)
        gender = np.random.choice(['M', 'F', 'Other'], p=[0.52, 0.46, 0.02])
        age = int(np.random.normal(38, 14))
        age = max(18, min(80, age))
        has_rx_upload = np.random.random() < 0.15
        has_subscription = np.random.random() < 0.08
        preferred_store = np.random.choice(
            stores_df[stores_df['city'] == city]['store_id'].values
        ) if stores_df is not None and city in stores_df['city'].values else None

        # Registration date within the 24-month window
        reg_offset = np.random.randint(0, TOTAL_DAYS)
        reg_date = START_DATE + timedelta(days=reg_offset)
        # 40% registered before the analysis period
        if np.random.random() < 0.4:
            reg_date = START_DATE - timedelta(days=np.random.randint(30, 365))

        rows.append({
            'customer_id': f'C-{i+1:06d}',
            'city': city,
            'pincode': np.random.choice(PINCODES[city]),
            'gender': gender,
            'age': age,
            'registration_date': reg_date.strftime('%Y-%m-%d'),
            'has_rx_upload': has_rx_upload,
            'has_subscription': has_subscription,
            'preferred_store': preferred_store,
            'loyalty_tier': np.random.choice(
                ['Bronze', 'Silver', 'Gold', 'Platinum'],
                p=[0.50, 0.30, 0.15, 0.05]
            ),
        })

    df = pd.DataFrame(rows)
    print(f"  -> {len(df)} customers generated")
    print(f"     Rx uploads: {df['has_rx_upload'].mean()*100:.1f}%")
    print(f"     Subscriptions: {df['has_subscription'].mean()*100:.1f}%")
    return df


# =============================================================================
# 4. ORDERS
# =============================================================================

def _seasonality_factor(date: datetime) -> float:
    """Return a multiplier based on seasonal patterns."""
    month = date.month
    day_of_week = date.weekday()

    # Base monthly seasonality
    monthly = {
        1: 1.05, 2: 0.95, 3: 1.00, 4: 1.02,
        5: 0.98, 6: 0.90, 7: 0.85, 8: 0.88,   # monsoon dip
        9: 0.92, 10: 1.15, 11: 1.25, 12: 1.10,  # Diwali + festive spike
    }
    factor = monthly.get(month, 1.0)

    # Weekend boost
    if day_of_week >= 5:
        factor *= 1.12

    # Diwali spike (around Oct 20–Nov 5)
    if (month == 10 and date.day >= 15) or (month == 11 and date.day <= 10):
        factor *= 1.3

    return factor


def generate_orders(n=50000, stores_df=None, customers_df=None) -> pd.DataFrame:
    """Generate ~50K orders over 24 months."""
    print("Generating Orders...")
    rows = []

    store_ids = stores_df['store_id'].values
    store_types = dict(zip(stores_df['store_id'], stores_df['store_type']))
    store_cities = dict(zip(stores_df['store_id'], stores_df['city']))
    online_stores = stores_df[stores_df['online_enabled']]['store_id'].values
    customer_ids = customers_df['customer_id'].values
    customer_cities = dict(zip(customers_df['customer_id'], customers_df['city']))

    # Pre-compute daily order targets
    dates = [START_DATE + timedelta(days=d) for d in range(TOTAL_DAYS)]
    base_daily = n / TOTAL_DAYS
    daily_targets = [int(base_daily * _seasonality_factor(d)) for d in dates]
    # Scale to hit target total
    scale = n / sum(daily_targets)
    daily_targets = [max(1, int(t * scale)) for t in daily_targets]

    # YoY growth: +12% in year 2
    for i, d in enumerate(dates):
        if d >= datetime(2025, 5, 1):
            daily_targets[i] = int(daily_targets[i] * 1.12)

    oid = 1
    for day_idx, date in enumerate(dates):
        n_orders = daily_targets[day_idx]
        for _ in range(n_orders):
            # Channel
            is_online = np.random.random() < 0.30
            if is_online:
                store = np.random.choice(online_stores)
            else:
                store = np.random.choice(store_ids)

            customer = np.random.choice(customer_ids)

            # Status
            r = np.random.random()
            if r < 0.05:
                status = 'Cancelled'
            elif r < 0.08:
                status = 'Returned'
            else:
                status = 'Delivered'

            # Delivery delay for online orders
            delivery_days = 0
            is_delayed = False
            if is_online and status == 'Delivered':
                delivery_days = np.random.choice([0, 1, 1, 2, 2, 3, 4, 5], p=[0.3, 0.25, 0.2, 0.1, 0.08, 0.04, 0.02, 0.01])
                is_delayed = delivery_days > 2

            # Order time
            hour = int(np.random.normal(14, 4))
            hour = max(8, min(22, hour))
            order_dt = date.replace(hour=hour, minute=np.random.randint(0, 60))

            payment = np.random.choice(PAYMENT_MODES, p=PAYMENT_WEIGHTS)
            if not is_online and payment == 'Net Banking':
                payment = 'Cash'

            cancel_reason = np.random.choice(CANCELLATION_REASONS) if status == 'Cancelled' else ''
            return_reason = np.random.choice(RETURN_REASONS) if status == 'Returned' else ''

            rows.append({
                'order_id': f'ORD-{oid:07d}',
                'order_date': order_dt.strftime('%Y-%m-%d %H:%M:%S'),
                'customer_id': customer,
                'store_id': store,
                'channel': 'Online' if is_online else 'Offline',
                'status': status,
                'payment_mode': payment,
                'delivery_days': delivery_days,
                'is_delayed': is_delayed,
                'cancellation_reason': cancel_reason,
                'return_reason': return_reason,
            })
            oid += 1

    df = pd.DataFrame(rows)
    print(f"  -> {len(df)} orders generated")
    print(f"     Online: {(df['channel']=='Online').mean()*100:.1f}%")
    print(f"     Cancelled: {(df['status']=='Cancelled').mean()*100:.1f}%")
    print(f"     Returned: {(df['status']=='Returned').mean()*100:.1f}%")
    print(f"     Delayed: {df['is_delayed'].mean()*100:.1f}%")
    return df


# =============================================================================
# 5. ORDER LINE ITEMS
# =============================================================================

def generate_line_items(orders_df: pd.DataFrame, products_df: pd.DataFrame) -> pd.DataFrame:
    """Generate ~150K line items (~3 items/order) with category-aware Pareto distribution."""
    print("Generating Order Line Items...")

    # Build per-category product pools with Pareto weights
    cat_products = {}
    cat_weights = {}
    for cat in CATEGORIES:
        cat_df = products_df[products_df['category'] == cat].reset_index(drop=True)
        pids = cat_df['product_id'].values
        n = len(pids)
        w = np.array([(i+1)**(-1.2) for i in range(n)])
        w /= w.sum()
        cat_products[cat] = pids
        cat_weights[cat] = w

    # Category selection weights (matching mix targets)
    cat_names = list(CATEGORIES.keys())
    cat_mix = np.array([CATEGORIES[c]['mix'] for c in cat_names])
    cat_mix /= cat_mix.sum()

    product_prices = dict(zip(products_df['product_id'], products_df['mrp']))
    product_costs = dict(zip(products_df['product_id'], products_df['cost_price']))

    rows = []
    lid = 1

    # Target: ~85 Cr over 2 years → ~150K items → avg ~567 INR/item
    # We'll use a price multiplier to calibrate
    PRICE_MULT = 17.8  # scale factor to hit revenue target

    order_ids = orders_df['order_id'].values
    n_orders = len(order_ids)

    for i in range(n_orders):
        oid = order_ids[i]
        n_items = np.random.choice([1, 2, 3, 4, 5, 6], p=[0.15, 0.30, 0.25, 0.15, 0.10, 0.05])

        # Pick primary category, then allow cross-category items
        primary_cat = np.random.choice(cat_names, p=cat_mix)

        for j in range(n_items):
            # 70% chance same category, 30% cross-category
            if j == 0 or np.random.random() < 0.70:
                cat = primary_cat
            else:
                cat = np.random.choice(cat_names, p=cat_mix)

            pool = cat_products[cat]
            weights = cat_weights[cat]
            pid = np.random.choice(pool, p=weights)

            qty = np.random.choice([1, 1, 1, 2, 2, 3], p=[0.40, 0.20, 0.15, 0.12, 0.08, 0.05])
            mrp = product_prices[pid] * PRICE_MULT
            cost = product_costs[pid] * PRICE_MULT

            # Small random discount (0-10%)
            discount_pct = np.random.choice([0, 0, 0, 0.05, 0.08, 0.10], p=[0.50, 0.15, 0.10, 0.12, 0.08, 0.05])
            unit_price = round(mrp * (1 - discount_pct), 2)
            line_total = round(unit_price * qty, 2)
            line_cost = round(cost * qty, 2)

            rows.append({
                'line_item_id': f'LI-{lid:08d}',
                'order_id': oid,
                'product_id': pid,
                'quantity': qty,
                'unit_price': unit_price,
                'discount_pct': round(discount_pct * 100, 1),
                'line_total': line_total,
                'cost_amount': line_cost,
                'margin_amount': round(line_total - line_cost, 2),
            })
            lid += 1

    df = pd.DataFrame(rows)
    total_rev = df['line_total'].sum()
    print(f"  -> {len(df)} line items generated")
    print(f"     Total revenue: INR {total_rev/1e7:.2f} Cr")
    print(f"     Avg items/order: {len(df)/len(orders_df):.1f}")
    print(f"     Avg item value: INR {df['line_total'].mean():.0f}")

    # Revenue calibration check
    annual_rev = total_rev / 2  # 2 years
    target = 42.5e7  # 42.5 Cr
    print(f"     Annual revenue: INR {annual_rev/1e7:.2f} Cr (target: 42.5 Cr)")

    return df


# =============================================================================
# 6. INVENTORY SNAPSHOTS
# =============================================================================

def generate_inventory(stores_df: pd.DataFrame, products_df: pd.DataFrame,
                       n_top_products=200) -> pd.DataFrame:
    """Generate ~180K inventory rows (30 stores × 200 products × last 90 days, sampled)."""
    print("Generating Inventory Snapshots...")

    # Take top 200 products by a synthetic popularity score
    top_products = products_df.head(n_top_products)['product_id'].values
    store_ids = stores_df['store_id'].values

    # Generate weekly snapshots for last 90 days (13 weeks)
    snapshot_dates = [END_DATE - timedelta(weeks=w) for w in range(13)]
    snapshot_dates.sort()

    rows = []
    for snap_date in snapshot_dates:
        month = snap_date.month
        # OOS rate varies by season (higher in monsoon)
        base_oos_rate = 0.042
        if month in [6, 7, 8]:
            base_oos_rate = 0.065
        elif month in [10, 11]:
            base_oos_rate = 0.055

        for store_id in store_ids:
            for pid in top_products:
                stock_on_hand = max(0, int(np.random.exponential(50)))
                reorder_point = np.random.randint(10, 30)
                is_oos = stock_on_hand == 0 or np.random.random() < base_oos_rate
                if is_oos:
                    stock_on_hand = 0
                    days_oos = np.random.randint(1, 14)
                else:
                    days_oos = 0

                rows.append({
                    'store_id': store_id,
                    'product_id': pid,
                    'snapshot_date': snap_date.strftime('%Y-%m-%d'),
                    'stock_on_hand': stock_on_hand,
                    'reorder_point': reorder_point,
                    'is_out_of_stock': is_oos,
                    'days_out_of_stock': days_oos,
                })

    df = pd.DataFrame(rows)
    oos_rate = df['is_out_of_stock'].mean() * 100
    print(f"  -> {len(df)} inventory rows generated")
    print(f"     OOS rate: {oos_rate:.1f}%")
    return df


# =============================================================================
# VALIDATION
# =============================================================================

def validate(stores, products, customers, orders, items, inventory):
    """Run referential integrity and calibration checks."""
    print("\n" + "=" * 60)
    print("VALIDATION CHECKS")
    print("=" * 60)
    errors = []

    # Row counts
    checks = [
        ('Stores', len(stores), 30, 30),
        ('Products', len(products), 950, 1050),
        ('Customers', len(customers), 4900, 5100),
        ('Orders', len(orders), 45000, 65000),
        ('Line Items', len(items), 100000, 250000),
        ('Inventory', len(inventory), 50000, 300000),
    ]
    for name, actual, lo, hi in checks:
        ok = lo <= actual <= hi
        status = 'OK' if ok else 'WARN'
        print(f"  [{status}] {name}: {actual:,} rows (expected {lo:,}-{hi:,})")
        if not ok:
            errors.append(f"{name} count out of range")

    # Referential integrity
    order_stores = set(orders['store_id'])
    valid_stores = set(stores['store_id'])
    orphan_stores = order_stores - valid_stores
    print(f"  [{'OK' if not orphan_stores else 'FAIL'}] Order->Store integrity: {len(orphan_stores)} orphans")

    order_customers = set(orders['customer_id'])
    valid_customers = set(customers['customer_id'])
    orphan_custs = order_customers - valid_customers
    print(f"  [{'OK' if not orphan_custs else 'FAIL'}] Order->Customer integrity: {len(orphan_custs)} orphans")

    item_orders = set(items['order_id'])
    valid_orders = set(orders['order_id'])
    orphan_items = item_orders - valid_orders
    print(f"  [{'OK' if not orphan_items else 'FAIL'}] LineItem->Order integrity: {len(orphan_items)} orphans")

    item_products = set(items['product_id'])
    valid_products = set(products['product_id'])
    orphan_prods = item_products - valid_products
    print(f"  [{'OK' if not orphan_prods else 'FAIL'}] LineItem->Product integrity: {len(orphan_prods)} orphans")

    # Revenue calibration
    total_rev = items['line_total'].sum()
    annual_rev = total_rev / 2
    target = 42.5e7
    pct_off = abs(annual_rev - target) / target * 100
    print(f"  [{'OK' if pct_off < 30 else 'WARN'}] Revenue calibration: INR {annual_rev/1e7:.2f} Cr/yr (target 42.5 Cr, {pct_off:.1f}% off)")

    # Category mix
    cat_rev = items.merge(products[['product_id', 'category']], on='product_id')
    cat_mix = cat_rev.groupby('category')['line_total'].sum() / cat_rev['line_total'].sum() * 100
    print("  Category mix:")
    for cat, pct in cat_mix.sort_values(ascending=False).items():
        target_pct = CATEGORIES.get(cat, {}).get('mix', 0) * 100
        print(f"    {cat}: {pct:.1f}% (target {target_pct:.0f}%)")

    # Cancellation/return rates
    cancel_rate = (orders['status'] == 'Cancelled').mean() * 100
    return_rate = (orders['status'] == 'Returned').mean() * 100
    print(f"  Cancellation rate: {cancel_rate:.1f}% (target ~5%)")
    print(f"  Return rate: {return_rate:.1f}% (target ~3%)")

    # Online share
    online_pct = (orders['channel'] == 'Online').mean() * 100
    print(f"  Online share: {online_pct:.1f}% (target ~30%)")

    if errors:
        print(f"\n  {len(errors)} warnings found")
    else:
        print("\n  All checks passed!")

    return len(errors) == 0


# =============================================================================
# SAVE TO SQLITE
# =============================================================================

def save_to_sqlite(stores, products, customers, orders, items, inventory):
    """Save all tables to SQLite database."""
    print(f"\nSaving to SQLite: {DB_PATH}")
    if DB_PATH.exists():
        DB_PATH.unlink()

    conn = sqlite3.connect(str(DB_PATH))

    stores.to_sql('stores', conn, index=False, if_exists='replace')
    products.to_sql('products', conn, index=False, if_exists='replace')
    customers.to_sql('customers', conn, index=False, if_exists='replace')
    orders.to_sql('orders', conn, index=False, if_exists='replace')
    items.to_sql('order_line_items', conn, index=False, if_exists='replace')
    inventory.to_sql('inventory', conn, index=False, if_exists='replace')

    # Create indexes
    conn.execute('CREATE INDEX idx_orders_date ON orders(order_date)')
    conn.execute('CREATE INDEX idx_orders_store ON orders(store_id)')
    conn.execute('CREATE INDEX idx_orders_customer ON orders(customer_id)')
    conn.execute('CREATE INDEX idx_items_order ON order_line_items(order_id)')
    conn.execute('CREATE INDEX idx_items_product ON order_line_items(product_id)')
    conn.execute('CREATE INDEX idx_inventory_store ON inventory(store_id)')
    conn.execute('CREATE INDEX idx_inventory_product ON inventory(product_id)')
    conn.commit()

    # Verify
    for table in ['stores', 'products', 'customers', 'orders', 'order_line_items', 'inventory']:
        count = conn.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
        print(f"  {table}: {count:,} rows")

    conn.close()
    print(f"  Database size: {DB_PATH.stat().st_size / 1024 / 1024:.1f} MB")


# =============================================================================
# MAIN
# =============================================================================

def main():
    print("=" * 60)
    print("TASKNOVA WF SYNTHETIC DATA GENERATOR")
    print("=" * 60)
    print(f"Time range: {START_DATE.date()} to {END_DATE.date()}")
    print(f"Output dir: {OUT_DIR}\n")

    # Generate in dependency order
    stores = generate_stores()
    products = generate_products(n=1000)
    customers = generate_customers(n=5000, stores_df=stores)
    orders = generate_orders(n=50000, stores_df=stores, customers_df=customers)
    items = generate_line_items(orders, products)
    inventory = generate_inventory(stores, products)

    # Save CSVs
    print("\nSaving CSVs...")
    stores.to_csv(OUT_DIR / 'stores.csv', index=False)
    products.to_csv(OUT_DIR / 'products.csv', index=False)
    customers.to_csv(OUT_DIR / 'customers.csv', index=False)
    orders.to_csv(OUT_DIR / 'orders.csv', index=False)
    items.to_csv(OUT_DIR / 'order_line_items.csv', index=False)
    inventory.to_csv(OUT_DIR / 'inventory.csv', index=False)
    print("  CSVs saved.")

    # Save to SQLite
    save_to_sqlite(stores, products, customers, orders, items, inventory)

    # Validate
    validate(stores, products, customers, orders, items, inventory)

    print("\nDone!")


if __name__ == '__main__':
    main()
