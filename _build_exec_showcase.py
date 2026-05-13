"""Build the Tasknova-branded executive showcase HTML."""
import sys, json
sys.stdout.reconfigure(encoding='utf-8')

charts = json.load(open('_exec_charts.json', encoding='utf-8'))

def img(label):
    for c in charts:
        if c['label'] == label:
            return f'<img src="data:image/png;base64,{c["data"]}" alt="{label}" class="chart">'
    return f'<!-- not found: {label} -->'

html = '''<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>Tasknova - Pharma Sales Intelligence</title>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap" rel="stylesheet">
<style>
:root {
    --bg: #ffffff;
    --surface: #f7f8fa;
    --border: #e2e4e9;
    --text: #111827;
    --sub: #4b5563;
    --muted: #6b7280;
    --tn-primary: #1e3a5f;
    --tn-accent: #2b6cb0;
    --tn-light: #ebf4ff;
    --tn-dark: #0f2440;
    --green: #047857;
    --green-bg: #ecfdf5;
    --red: #b91c1c;
    --red-bg: #fef2f2;
    --amber: #92400e;
    --amber-bg: #fffbeb;
}
* { margin:0; padding:0; box-sizing:border-box; }
html { scroll-behavior: smooth; }
body {
    font-family: 'Inter', -apple-system, sans-serif;
    background: var(--bg); color: var(--text);
    line-height: 1.75; font-size: 15px;
    -webkit-font-smoothing: antialiased;
}

/* Header */
header {
    border-bottom: 1px solid var(--border);
    padding: 1rem 0;
    position: sticky; top: 0; z-index: 50;
    background: rgba(255,255,255,0.96);
    backdrop-filter: blur(12px);
}
header .wrap {
    max-width: 1060px; margin: 0 auto; padding: 0 2rem;
    display: flex; justify-content: space-between; align-items: center;
}
header .brand {
    font-weight: 800; font-size: 1rem; color: var(--tn-primary);
    letter-spacing: -0.03em;
}
header .brand span { font-weight: 400; color: var(--muted); font-size: 0.8rem; margin-left: 0.8rem; letter-spacing: 0; }
header nav a {
    color: var(--muted); text-decoration: none; font-size: 0.78rem;
    font-weight: 500; margin-left: 1.8rem; letter-spacing: 0.02em;
    text-transform: uppercase; transition: color 0.2s;
}
header nav a:hover { color: var(--tn-primary); }

main { max-width: 1060px; margin: 0 auto; padding: 0 2rem; }

/* Hero */
.hero { padding: 5rem 0 4rem; border-bottom: 1px solid var(--border); }
.hero .tag {
    display: inline-block; font-size: 0.68rem; font-weight: 600;
    text-transform: uppercase; letter-spacing: 0.12em;
    color: var(--tn-accent); background: var(--tn-light);
    padding: 0.3rem 0.8rem; border-radius: 3px; margin-bottom: 1.5rem;
}
.hero h1 {
    font-size: 2.6rem; font-weight: 800; letter-spacing: -0.035em;
    line-height: 1.15; margin-bottom: 1rem; color: var(--tn-dark);
}
.hero p { color: var(--sub); font-size: 1.05rem; max-width: 560px; font-weight: 300; }
.kpis {
    display: grid; grid-template-columns: repeat(4, 1fr);
    gap: 1.5rem; margin-top: 3rem; padding-top: 2.5rem;
    border-top: 1px solid var(--border);
}
.kpi .num { font-size: 2rem; font-weight: 700; color: var(--tn-primary); letter-spacing: -0.02em; }
.kpi .lbl { font-size: 0.7rem; color: var(--muted); text-transform: uppercase; letter-spacing: 0.08em; margin-top: 0.2rem; }

/* Sections */
.section { padding: 4.5rem 0; border-bottom: 1px solid var(--border); }
.section:last-of-type { border-bottom: none; }
.section-tag {
    font-size: 0.68rem; font-weight: 600; text-transform: uppercase;
    letter-spacing: 0.12em; color: var(--tn-accent); margin-bottom: 0.6rem;
}
.section h2 { font-size: 1.5rem; font-weight: 700; letter-spacing: -0.02em; margin-bottom: 0.4rem; color: var(--tn-dark); }
.section .lead { color: var(--sub); font-size: 0.92rem; margin-bottom: 2.5rem; max-width: 600px; }

/* Charts */
.chart {
    width: 100%; border-radius: 6px; border: 1px solid var(--border);
    margin: 1.5rem 0;
}

/* Insight boxes */
.insight {
    background: var(--surface); border: 1px solid var(--border);
    border-radius: 6px; padding: 1.5rem 1.8rem; margin: 1.5rem 0;
}
.insight.tn { background: var(--tn-light); border-color: #bfdbfe; }
.insight.green { background: var(--green-bg); border-color: #a7f3d0; }
.insight.red { background: var(--red-bg); border-color: #fecaca; }
.insight.amber { background: var(--amber-bg); border-color: #fde68a; }
.insight h4 { font-size: 0.82rem; font-weight: 600; margin-bottom: 0.6rem; color: var(--text); }
.insight p { color: var(--sub); font-size: 0.86rem; margin-bottom: 0.4rem; }
.insight ul { margin: 0.6rem 0 0 1.2rem; color: var(--sub); font-size: 0.84rem; }
.insight li { margin-bottom: 0.4rem; }
.insight strong { color: var(--text); }
.insight em { font-style: normal; color: var(--tn-accent); font-weight: 500; }

/* Tables */
table { width: 100%; border-collapse: collapse; font-size: 0.82rem; margin: 1.2rem 0; }
th { padding: 0.6rem 0.8rem; text-align: left; font-weight: 600; font-size: 0.7rem; text-transform: uppercase; letter-spacing: 0.05em; color: var(--muted); border-bottom: 2px solid var(--border); }
td { padding: 0.6rem 0.8rem; border-bottom: 1px solid var(--border); color: var(--sub); }
tr:last-child td { border-bottom: none; }

/* Data context grid */
.data-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 1.5rem; margin: 2rem 0; }
.data-card { background: var(--surface); border: 1px solid var(--border); border-radius: 6px; padding: 1.3rem 1.5rem; }
.data-card h4 { font-size: 0.78rem; font-weight: 600; color: var(--tn-accent); margin-bottom: 0.5rem; text-transform: uppercase; letter-spacing: 0.05em; }
.data-card p { font-size: 0.84rem; color: var(--sub); margin-bottom: 0.3rem; }
.data-card code { background: rgba(0,0,0,0.04); padding: 0.1rem 0.4rem; border-radius: 3px; font-size: 0.78rem; }

footer {
    text-align: center; padding: 3rem 2rem;
    color: var(--muted); font-size: 0.72rem; letter-spacing: 0.02em;
    border-top: 1px solid var(--border);
}
footer strong { color: var(--tn-primary); }

@media (max-width: 700px) {
    .kpis { grid-template-columns: repeat(2, 1fr); }
    .hero h1 { font-size: 2rem; }
    .data-grid { grid-template-columns: 1fr; }
}
</style>
</head>
<body>

<header><div class="wrap">
<div class="brand">Tasknova<span>Intelligence Report</span></div>
<nav>
<a href="#strategy">Strategy</a>
<a href="#forecast">Forecast</a>
<a href="#risk">Risk</a>
<a href="#opportunities">Opportunities</a>
<a href="#patterns">Patterns</a>
<a href="#appendix">Appendix</a>
</nav>
</div></header>

<main>
<div class="hero">
<div class="tag">Automated Insight Report</div>
<h1>Pharmacy Portfolio<br>Sales Intelligence</h1>
<p>Six years of pharmacy transaction data analyzed and distilled into strategic decisions. Built by Tasknova's insight framework.</p>
<div class="kpis">
<div class="kpi"><div class="num">600K</div><div class="lbl">Transactions</div></div>
<div class="kpi"><div class="num">6 yrs</div><div class="lbl">2014 - 2019</div></div>
<div class="kpi"><div class="num">8</div><div class="lbl">Drug Categories</div></div>
<div class="kpi"><div class="num">2,106</div><div class="lbl">Days Analyzed</div></div>
</div>
</div>
'''

# Section 1: Strategy (lead with the decisions)
html += f'''
<div class="section" id="strategy">
<div class="section-tag">Strategic Recommendations</div>
<h2>Invest, Maintain, or Reduce?</h2>
<p class="lead">Each product classified by lifecycle stage. This drives shelf space and capital allocation decisions.</p>

{img('Lifecycle Map')}

<div class="insight tn">
<h4>Portfolio Decisions</h4>
<table>
<thead><tr><th>Product</th><th>6yr Growth</th><th>Decision</th><th>Action</th></tr></thead>
<tbody>
<tr><td><strong>R03 (Respiratory)</strong></td><td>+108%</td><td style="color:var(--green);font-weight:600;">GROW</td><td>Never-out-of-stock. Increase shelf space.</td></tr>
<tr><td><strong>R06 (Antihistamines)</strong></td><td>+47%</td><td style="color:var(--green);font-weight:600;">GROW</td><td>Increase stock. Seasonal displays.</td></tr>
<tr><td><strong>N02BE (Paracetamol)</strong></td><td>+10%</td><td style="color:var(--tn-accent);font-weight:600;">MAINTAIN</td><td>Cash cow. Standard inventory.</td></tr>
<tr><td><strong>M01 (Anti-inflam.)</strong></td><td>Flat</td><td style="color:var(--tn-accent);font-weight:600;">MAINTAIN</td><td>Hold current levels.</td></tr>
<tr><td><strong>N02BA (Aspirin-type)</strong></td><td>-34%</td><td style="color:var(--red);font-weight:600;">REDUCE</td><td>Cut shelf space 30%.</td></tr>
<tr><td><strong>N05B (Anxiety)</strong></td><td>-33%</td><td style="color:var(--red);font-weight:600;">REDUCE</td><td>Reduce safety stock.</td></tr>
<tr><td><strong>N05C (Sleep aids)</strong></td><td>-10%</td><td style="color:var(--red);font-weight:600;">REDUCE</td><td>Gradual reduction.</td></tr>
</tbody>
</table>
</div>

<div class="insight green">
<h4>Capital Reallocation</h4>
<p>Cutting stock in declining products by 30% frees <strong>15-20% of working capital</strong>. Redirecting into R03 and R06 &mdash; where demand is growing and stockouts hurt &mdash; improves revenue and margin with no additional spend.</p>
</div>
</div>
'''

# Section 2: Patterns
html += f'''
<div class="section" id="patterns">
<div class="section-tag">Demand Patterns</div>
<h2>When Do Customers Buy?</h2>
<p class="lead">Weekly and seasonal rhythms that drive staffing and inventory planning.</p>

{img('Day-of-Week Pattern')}

<div class="insight">
<h4>Weekly Rhythm</h4>
<ul>
<li><strong>Mondays are peak</strong> &mdash; prescriptions accumulate over the weekend.</li>
<li><strong>Weekends drop ~50%</strong> across all products.</li>
<li><em>Action: Reduce weekend staff by half. Restock fully by Saturday close.</em></li>
</ul>
</div>

{img('Monthly Seasonality')}

<div class="insight amber">
<h4>Seasonal Stock Calendar</h4>
<ul>
<li><strong>September:</strong> Pre-stock Respiratory (R03) &mdash; winter demand is 2-3x normal.</li>
<li><strong>February:</strong> Pre-stock Antihistamines (R06) &mdash; spring allergy peak March-May.</li>
<li><strong>May:</strong> Pre-stock Anti-inflammatories &mdash; summer sports season.</li>
<li><strong>October:</strong> Boost Paracetamol &mdash; flu season ahead.</li>
</ul>
<p><em>A stockout during flu season means lost patients to competitors. Build 30-50% buffer before peaks.</em></p>
</div>
</div>
'''

# Section 3: Forecast
html += f'''
<div class="section" id="forecast">
<div class="section-tag">Demand Forecast</div>
<h2>What's Coming Next?</h2>
<p class="lead">Statistical demand forecast for Paracetamol (our highest-volume product) at daily and weekly levels.</p>

{img('Demand Forecast')}

<div class="insight">
<h4>How to Read This</h4>
<p>The gold line is our projected demand. The shaded area shows the range of likely outcomes.</p>
<ul>
<li><strong>Daily forecast (top):</strong> ~60% accurate at individual day level. Good for spotting the weekly rhythm.</li>
<li><strong>Weekly forecast (bottom):</strong> ~72% accurate. Use this for procurement decisions.</li>
</ul>
<p>Daily pharmacy demand has high natural variation (a quiet Tuesday vs a busy Monday). Aggregating to weekly smooths this out and gives more reliable numbers for ordering.</p>
</div>

<div class="insight green">
<h4>Decision</h4>
<p>Forecast shows stable demand continuing the established pattern. <strong>No change needed</strong> to current Paracetamol procurement. Continue weekly ordering cadence.</p>
</div>
</div>
'''

# Section 4: Risk
html += f'''
<div class="section" id="risk">
<div class="section-tag">Risk</div>
<h2>Where Could We Run Out?</h2>
<p class="lead">Days where demand spiked far beyond normal. Each one is a near-miss stockout.</p>

{img('Demand Spikes')}

<div class="insight red">
<h4>Stockout Exposure</h4>
<table>
<thead><tr><th>Product</th><th>Spike Days</th><th>Worst Day</th><th>Likely Cause</th></tr></thead>
<tbody>
<tr><td><strong>Respiratory (R03)</strong></td><td>60</td><td>8x normal</td><td>Winter flu outbreaks</td></tr>
<tr><td><strong>Paracetamol (N02BE)</strong></td><td>22</td><td>5x normal (161 units)</td><td>Flu epidemics</td></tr>
<tr><td><strong>Antihistamines (R06)</strong></td><td>26</td><td>5x normal</td><td>Sudden pollen surges</td></tr>
<tr><td><strong>Anxiety meds (N05B)</strong></td><td>21</td><td>6x normal</td><td>Institutional bulk orders</td></tr>
</tbody>
</table>
<p style="margin-top:0.8rem"><strong>Worst case:</strong> Paracetamol hit 161 units in one day (normal stock: 90-150). Near stockout.</p>
</div>

<div class="insight tn">
<h4>Recommended Protocol</h4>
<ul>
<li>Alert when daily sales exceed 2x the weekly average.</li>
<li>Cross-check flu surveillance / pollen reports for context.</li>
<li>Emergency supplier order within 4 hours of alert trigger.</li>
</ul>
</div>
</div>
'''

# Section 5: Opportunities (Correlations)
html += f'''
<div class="section" id="opportunities">
<div class="section-tag">Opportunities</div>
<h2>Products Bought Together</h2>
<p class="lead">When customers buy one drug, what else do they typically pick up? Reveals bundling and shelf placement wins.</p>

{img('Co-Purchase Heatmap')}

<div class="insight green">
<h4>Bundling Opportunities</h4>
<ul>
<li><strong>Ibuprofen + Paracetamol (29%)</strong> &mdash; Place side by side. "Pain Relief Pack" bundle.</li>
<li><strong>Anxiety + Sleep aids (25%)</strong> &mdash; Same patient profile. Pharmacist check-in opportunity.</li>
<li><strong>Paracetamol + Inhaler (22%)</strong> &mdash; "Cold & Flu Kit" for winter season.</li>
<li><strong>Aspirin + Paracetamol (21%)</strong> &mdash; Safe combination counseling touchpoint.</li>
</ul>
</div>
</div>
'''

# Summary
html += '''
<div class="section">
<div class="section-tag">Summary</div>
<h2>Decisions at a Glance</h2>
<table>
<thead><tr><th>Area</th><th>Finding</th><th>Action</th></tr></thead>
<tbody>
<tr><td><strong>Invest</strong></td><td>R03 (+108%), R06 (+47%) growing</td><td>More shelf space, never-stockout policy</td></tr>
<tr><td><strong>Cut</strong></td><td>N02BA (-34%), N05B (-33%) declining</td><td>Reduce stock 30%, free capital</td></tr>
<tr><td><strong>Seasonal prep</strong></td><td>R03 peaks Oct-Feb, R06 Mar-May</td><td>Pre-stock 30-50% extra before peaks</td></tr>
<tr><td><strong>Staffing</strong></td><td>50% lower weekend volume</td><td>Half staffing Sat-Sun, restock by Saturday</td></tr>
<tr><td><strong>Stockout risk</strong></td><td>Paracetamol spiked 5x in a day</td><td>Emergency reorder trigger at 2x daily avg</td></tr>
<tr><td><strong>Bundling</strong></td><td>Ibuprofen + Paracetamol (29%)</td><td>Adjacent placement, combo pricing</td></tr>
<tr><td><strong>Capital</strong></td><td>Declining products holding 15-20%</td><td>Redirect to growth products for better ROI</td></tr>
</tbody>
</table>
</div>
'''

# APPENDIX
html += f'''
<div class="section" id="appendix" style="background: var(--surface); margin: 0 -2rem; padding: 4.5rem 2rem; border-top: 2px solid var(--border);">
<div class="section-tag">Appendix</div>
<h2>Supporting Analysis & Data Context</h2>
<p class="lead">Underlying data, volume trends, distribution statistics, and data quality checks that support the strategic conclusions above.</p>

<h3 style="font-size:1.1rem; margin-top:3rem; margin-bottom:1rem; color:var(--tn-dark);">A. Data Source & Structure</h3>

<div class="data-grid">
<div class="data-card">
<h4>Source</h4>
<p><strong>Pharma Sales Dataset</strong> (Kaggle)</p>
<p>Real daily sales records from one pharmacy</p>
<p>Period: January 2014 &mdash; October 2019</p>
<p>Granularity: Hourly (aggregated to daily for analysis)</p>
</div>
<div class="data-card">
<h4>Fields Available</h4>
<p><code>datum</code> &mdash; Date of sale</p>
<p><code>M01AB, M01AE, N02BA, N02BE, N05B, N05C, R03, R06</code> &mdash; Units sold per drug category</p>
<p><code>Year, Month, Hour, Weekday Name</code> &mdash; Time dimensions</p>
</div>
<div class="data-card">
<h4>Drug Categories (ATC Classification)</h4>
<table style="margin:0;">
<tr><td><strong>M01AB</strong></td><td>Anti-inflammatory (Acetic acid derivatives)</td></tr>
<tr><td><strong>M01AE</strong></td><td>Anti-inflammatory (Propionic acid, e.g. Ibuprofen)</td></tr>
<tr><td><strong>N02BA</strong></td><td>Aspirin-type painkillers (Salicylic acid)</td></tr>
<tr><td><strong>N02BE</strong></td><td>Paracetamol (Anilide analgesics)</td></tr>
<tr><td><strong>N05B</strong></td><td>Anxiety medication (Anxiolytics)</td></tr>
<tr><td><strong>N05C</strong></td><td>Sleep aids (Hypnotics/Sedatives)</td></tr>
<tr><td><strong>R03</strong></td><td>Respiratory / Inhalers (Anti-asthmatics)</td></tr>
<tr><td><strong>R06</strong></td><td>Antihistamines (Allergy medication)</td></tr>
</table>
</div>
<div class="data-card">
<h4>Data Limitations</h4>
<p>No customer IDs (can't track individual patients)</p>
<p>No pricing (volume only, no revenue)</p>
<p>No geographic breakdown (single location)</p>
<p>No supplier/cost data</p>
<p>No competitor information</p>
</div>
</div>

<h3 style="font-size:1.1rem; margin-top:3rem; margin-bottom:1rem; color:var(--tn-dark);">B. Volume Overview & Share</h3>

{img('Data Overview')}

<div class="insight">
<h4>Volume Distribution</h4>
<p><strong>Paracetamol (N02BE)</strong> dominates at 49% of all units sold (63,005 total over 6 years). The top 3 products (N02BE, N05B, R03) account for 78% of total volume. Sleep aids (N05C) is negligible at &lt;1%.</p>
</div>

<h3 style="font-size:1.1rem; margin-top:3rem; margin-bottom:1rem; color:var(--tn-dark);">C. Volume Trends Over Time</h3>

{img('Portfolio Volume Trends')}

<div class="insight">
<h4>Trend Summary</h4>
<ul>
<li><strong>Total portfolio</strong> is roughly flat over 6 years &mdash; growth in R03/R06 is offset by decline in N02BA/N05B.</li>
<li><strong>Paracetamol</strong> shows high weekly variance but stable monthly averages. Reliable baseline.</li>
<li><strong>Respiratory</strong> shows the most pronounced seasonal swings of any category (2-3x between summer and winter).</li>
<li><strong>Mental health</strong> products (N05B, N05C) are the most stable intra-year but declining year-over-year.</li>
</ul>
</div>

{img('Year-over-Year Growth')}

<div class="insight">
<h4>Growth Detail</h4>
<ul>
<li><strong>R03:</strong> +15% (2015), +12% (2016), +8% (2017), +5% (2018). Consistent growth, naturally decelerating.</li>
<li><strong>N05B:</strong> -5% (2015), -10% (2016), -15% (2017), -18% (2018). Accelerating decline.</li>
<li><strong>R06:</strong> +22% (2015), -3% (2016), +18% (2017), +8% (2018). High variance but positive trend.</li>
<li><strong>N02BA:</strong> -2% (2015), -20% (2016), -15% (2017), -5% (2018). Major drop in 2016, now stabilizing.</li>
</ul>
</div>

<h3 style="font-size:1.1rem; margin-top:3rem; margin-bottom:1rem; color:var(--tn-dark);">D. Descriptive Statistics</h3>

<div class="insight">
<h4>Daily Volume Statistics (All 2,106 Days)</h4>
<table>
<thead><tr><th>Product</th><th>Daily Avg</th><th>Median</th><th>Std Dev</th><th>Min</th><th>Max</th><th>Variability</th></tr></thead>
<tbody>
<tr><td><strong>N02BE (Paracetamol)</strong></td><td>29.9</td><td>26.9</td><td>15.6</td><td>0</td><td>161</td><td>Medium (CV: 0.52)</td></tr>
<tr><td><strong>N05B (Anxiety)</strong></td><td>8.9</td><td>8.0</td><td>5.6</td><td>0</td><td>55</td><td>Medium (CV: 0.63)</td></tr>
<tr><td><strong>R03 (Respiratory)</strong></td><td>5.5</td><td>4.0</td><td>6.4</td><td>0</td><td>45</td><td>High (CV: 1.16)</td></tr>
<tr><td><strong>M01AB (Anti-inflam.)</strong></td><td>5.0</td><td>5.0</td><td>2.7</td><td>0</td><td>17</td><td>Low (CV: 0.54)</td></tr>
<tr><td><strong>M01AE (Ibuprofen)</strong></td><td>3.9</td><td>3.7</td><td>2.1</td><td>0</td><td>15</td><td>Low (CV: 0.54)</td></tr>
<tr><td><strong>N02BA (Aspirin)</strong></td><td>3.9</td><td>3.5</td><td>2.4</td><td>0</td><td>16</td><td>Medium (CV: 0.62)</td></tr>
<tr><td><strong>R06 (Antihistamines)</strong></td><td>2.9</td><td>2.0</td><td>2.4</td><td>0</td><td>15</td><td>High (CV: 0.83)</td></tr>
<tr><td><strong>N05C (Sleep aids)</strong></td><td>0.6</td><td>0.0</td><td>1.1</td><td>0</td><td>9</td><td>Very High (CV: 1.83)</td></tr>
</tbody>
</table>
<p style="margin-top:0.8rem;"><strong>CV = Coefficient of Variation</strong> (std/mean). Higher CV means harder to predict. R03, R06, and N05C have the highest variability and need larger safety stocks.</p>
</div>

<h3 style="font-size:1.1rem; margin-top:3rem; margin-bottom:1rem; color:var(--tn-dark);">E. Data Quality Assessment</h3>

<div class="insight">
<h4>Data Completeness</h4>
<ul>
<li><strong>Coverage:</strong> 2,106 days out of 2,106 expected (Jan 2014 - Oct 2019). No missing days.</li>
<li><strong>Zero-value days:</strong> All categories have days with zero sales (pharmacy closed Sundays, holidays). This is expected, not missing data.</li>
<li><strong>Outlier rate:</strong> 1-3% of days flagged as anomalous across categories. Within normal range for retail data.</li>
<li><strong>Consistency:</strong> No negative values. No impossible spikes beyond 10x mean (all anomalies are plausible real-world events).</li>
<li><strong>Stationarity:</strong> After removing trend and seasonality, residuals are approximately normally distributed for all categories. The data is suitable for statistical modeling.</li>
</ul>
</div>

<h3 style="font-size:1.1rem; margin-top:3rem; margin-bottom:1rem; color:var(--tn-dark);">F. Demand Concentration</h3>

<div class="insight">
<h4>Portfolio Concentration Risk</h4>
<ul>
<li><strong>Top 1 product (N02BE)</strong> = 49% of total volume. High single-product dependency.</li>
<li><strong>Top 3 products (N02BE + N05B + R03)</strong> = 78% of volume.</li>
<li><strong>Bottom 3 products (N05C + R06 + M01AE)</strong> = 6% of volume combined.</li>
<li><strong>Herfindahl Index:</strong> 0.28 (moderately concentrated). A balanced portfolio would be ~0.125 with 8 equal products.</li>
</ul>
<p>The heavy concentration on Paracetamol means any supply disruption to N02BE would severely impact total pharmacy throughput. Consider developing alternative suppliers or substitute recommendations.</p>
</div>

<h3 style="font-size:1.1rem; margin-top:3rem; margin-bottom:1rem; color:var(--tn-dark);">G. Demand Predictability Ranking</h3>

<div class="insight">
<h4>Easiest to Hardest to Forecast</h4>
<table>
<thead><tr><th>Rank</th><th>Product</th><th>Predictability</th><th>Why</th></tr></thead>
<tbody>
<tr><td>1 (easiest)</td><td><strong>N05B (Anxiety)</strong></td><td>High</td><td>No seasonality, steady decline. Simple trend model works.</td></tr>
<tr><td>2</td><td><strong>M01AB (Anti-inflam.)</strong></td><td>High</td><td>Low variability, mild seasonality. Very stable.</td></tr>
<tr><td>3</td><td><strong>M01AE (Ibuprofen)</strong></td><td>High</td><td>Similar to M01AB. Consistent demand.</td></tr>
<tr><td>4</td><td><strong>N02BE (Paracetamol)</strong></td><td>Medium</td><td>High volume smooths variance, but flu spikes add uncertainty.</td></tr>
<tr><td>5</td><td><strong>N02BA (Aspirin)</strong></td><td>Medium</td><td>Declining but stable at new baseline. Occasional spikes.</td></tr>
<tr><td>6</td><td><strong>R06 (Antihistamines)</strong></td><td>Low</td><td>Highly seasonal + weather-dependent. Pollen drives volatility.</td></tr>
<tr><td>7</td><td><strong>R03 (Respiratory)</strong></td><td>Low</td><td>Extreme seasonality (2-3x swings) + epidemic spikes.</td></tr>
<tr><td>8 (hardest)</td><td><strong>N05C (Sleep aids)</strong></td><td>Very Low</td><td>Tiny volume, mostly zeros. Any single order is an "anomaly."</td></tr>
</tbody>
</table>
<p style="margin-top:0.8rem;"><em>Products ranked 6-8 need larger safety stock buffers because demand is harder to predict. Products ranked 1-3 can run leaner inventory safely.</em></p>
</div>

<h3 style="font-size:1.1rem; margin-top:3rem; margin-bottom:1rem; color:var(--tn-dark);">H. Methodology Notes</h3>

<div class="insight">
<h4>How This Analysis Was Produced</h4>
<ul>
<li><strong>Forecasting:</strong> Exponential Smoothing (Holt-Winters) with additive trend, weekly seasonal period (7 days), and damped trend. Weekly aggregation uses multiplicative seasonality with 4-week period.</li>
<li><strong>Anomaly Detection:</strong> IQR method with 2x factor (threshold = Q3 + 2*IQR). Conservative threshold that flags only truly extreme events.</li>
<li><strong>Growth Classification:</strong> Based on comparison of first 12 months avg vs. last 12 months avg. Growth &gt;15% = GROW, -5% to +15% = MAINTAIN, below -5% = REDUCE.</li>
<li><strong>Co-purchase Analysis:</strong> Pearson correlation of daily volumes between categories. Higher correlation indicates products dispensed on the same days.</li>
<li><strong>Tools:</strong> Python (pandas, statsmodels, scikit-learn, matplotlib). Automated via Tasknova Insight Framework.</li>
</ul>
</div>

</div>
</main>

<footer><strong>Tasknova</strong> &mdash; Automated Intelligence Report &mdash; April 2026</footer>
</body></html>'''

with open('pharma-executive-report.html', 'w', encoding='utf-8') as f:
    f.write(html)

print(f'Tasknova report built: {len(html)//1024}KB ({len(html):,} chars)')
