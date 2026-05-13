from weasyprint import HTML

html_content = """<!DOCTYPE html>
<html>
<head>
<meta charset="utf-8">
<style>
    @page { size: A4; margin: 2cm; }
    body { font-family: 'Segoe UI', Arial, sans-serif; color: #222; font-size: 11px; line-height: 1.5; }
    h1 { color: #0d47a1; font-size: 20px; border-bottom: 3px solid #0d47a1; padding-bottom: 6px; margin-top: 0; }
    h2 { color: #1565c0; font-size: 15px; margin-top: 20px; border-bottom: 1px solid #ccc; padding-bottom: 4px; }
    h3 { color: #1976d2; font-size: 13px; margin-top: 14px; }
    table { width: 100%; border-collapse: collapse; margin: 10px 0; font-size: 10px; }
    th { background: #0d47a1; color: white; padding: 6px 8px; text-align: left; font-weight: 600; }
    td { padding: 5px 8px; border-bottom: 1px solid #e0e0e0; }
    tr:nth-child(even) { background: #f5f5f5; }
    .critical { background: #ffebee !important; }
    .warning { background: #fff8e1 !important; }
    .good { background: #e8f5e9 !important; }
    .tag { display: inline-block; padding: 2px 8px; border-radius: 3px; font-size: 9px; font-weight: 700; }
    .tag-red { background: #ef5350; color: white; }
    .tag-amber { background: #ffa726; color: white; }
    .tag-green { background: #66bb6a; color: white; }
    .tag-blue { background: #42a5f5; color: white; }
    .summary-box { background: #e3f2fd; border-left: 4px solid #1565c0; padding: 10px 14px; margin: 12px 0; }
    .action-box { background: #fff3e0; border-left: 4px solid #ef6c00; padding: 10px 14px; margin: 12px 0; }
    .kpi-row { display: flex; gap: 12px; margin: 12px 0; }
    .kpi { flex: 1; background: #f5f5f5; border-radius: 6px; padding: 10px; text-align: center; border: 1px solid #e0e0e0; }
    .kpi .num { font-size: 18px; font-weight: 700; color: #0d47a1; }
    .kpi .label { font-size: 9px; color: #666; margin-top: 2px; }
    ol li { margin-bottom: 6px; }
    .footer { margin-top: 30px; border-top: 1px solid #ccc; padding-top: 8px; font-size: 9px; color: #999; text-align: center; }
</style>
</head>
<body>

<h1>Comprehensive Inventory Intelligence Report</h1>
<p style="color:#666; margin-top:-8px">Wellness Forever | Demand-Availability Mismatch, SKU Classification &amp; Profit Optimization</p>
<p style="color:#999; font-size:9px">Generated: May 2026 | Data Source: wf_intelligence.db (30 stores, 1K SKUs, 52K orders, 152K line items, 78K inventory snapshots)</p>

<div style="display:flex; gap:12px; margin:16px 0;">
    <div class="kpi"><div class="num">Rs 78.67 Cr</div><div class="label">Total Revenue</div></div>
    <div class="kpi"><div class="num">Rs 3.82 Cr</div><div class="label" style="color:#d32f2f">Capital Trapped</div></div>
    <div class="kpi"><div class="num">Rs 19.47 Cr</div><div class="label" style="color:#ef6c00">Capital At Risk</div></div>
    <div class="kpi"><div class="num">Rs 1.4-1.5 Cr</div><div class="label" style="color:#d32f2f">Est. Lost Sales</div></div>
    <div class="kpi"><div class="num">816</div><div class="label">SKUs to Phase Out</div></div>
</div>

<h2>1. SKU Decision Buckets</h2>
<p>All 1,000 SKUs classified into four action-oriented decision buckets based on revenue, margin, OOS rate, stock levels, and velocity trends.</p>

<table>
<tr><th>Bucket</th><th>SKU Count</th><th>Total Revenue</th><th>Action Required</th></tr>
<tr class="good"><td><span class="tag tag-green">PROTECT &amp; REPLENISH</span></td><td>12</td><td>Rs 18.99 Cr</td><td>High-revenue + high OOS. Immediate restocking priority</td></tr>
<tr class="warning"><td><span class="tag tag-amber">MONITOR &amp; REBALANCE</span></td><td>34</td><td>Rs 10.26 Cr</td><td>Good revenue but margin &lt;20%. Renegotiate or substitute</td></tr>
<tr><td><span class="tag tag-blue">SEASONAL HOLD</span></td><td>138</td><td>Rs 37.02 Cr</td><td>Revenue dropped &gt;70% recently. Hold stock, don't reorder</td></tr>
<tr class="critical"><td><span class="tag tag-red">PHASE OUT</span></td><td>816</td><td>Rs 12.41 Cr</td><td>Low revenue + low margin + excess stock. Liquidate</td></tr>
</table>

<h3>Top PROTECT &amp; REPLENISH SKUs</h3>
<table>
<tr><th>Product</th><th>Therapeutic</th><th>Revenue</th><th>OOS%</th><th>Action</th></tr>
<tr class="critical"><td>Sun Pharma Gel 349</td><td>Neurological</td><td>Rs 8.70 Cr</td><td>7.4%</td><td>CRITICAL: #1 revenue SKU at 7.4% OOS — est. Rs 64L lost sales</td></tr>
<tr><td>Aurobindo Drops 122</td><td>Dermatological</td><td>Rs 2.02 Cr</td><td>6.7%</td><td>High-demand derma SKU, increase safety stock</td></tr>
<tr><td>Abbott India Inhaler 394</td><td>Anti-diabetic</td><td>Rs 1.10 Cr</td><td>5.9%</td><td>Chronic-use product — OOS causes patient churn</td></tr>
<tr><td>Sun Pharma Ointment 845</td><td>Cardiac</td><td>Rs 1.04 Cr</td><td>5.9%</td><td>Cardiac anchor SKU, ensure 100% availability</td></tr>
<tr><td>Macleods Capsule 690</td><td>Antibiotic</td><td>Rs 1.01 Cr</td><td>5.4%</td><td>High prescription volume, reorder buffer needed</td></tr>
</table>

<h2>2. Working Capital Analysis</h2>

<table>
<tr><th>Status</th><th>SKUs</th><th>Capital Locked</th><th>Key Issue</th></tr>
<tr class="critical"><td><span class="tag tag-red">TRAPPED</span> (zero recent sales)</td><td>4</td><td>Rs 3.82 Cr</td><td>No movement in 30+ days. Immediate liquidation required</td></tr>
<tr class="warning"><td><span class="tag tag-amber">AT RISK</span> (&lt;5% recent velocity)</td><td>19</td><td>Rs 19.47 Cr</td><td>Velocity collapsing. Review and redistribute</td></tr>
<tr class="good"><td>HEALTHY</td><td colspan="3">Remaining SKUs have adequate demand-to-stock ratios</td></tr>
</table>

<h3>Trapped Capital Details</h3>
<table>
<tr><th>Product</th><th>Therapeutic</th><th>Capital Locked</th><th>Historical Qty</th><th>Recent Qty</th></tr>
<tr><td>Cipla Suspension 572</td><td>Pain Mgmt</td><td>Rs 1.15 Cr</td><td>122</td><td>0</td></tr>
<tr><td>Aurobindo Ointment 60</td><td>Neurological</td><td>Rs 95.1L</td><td>22</td><td>0</td></tr>
<tr><td>Torrent Suspension 626</td><td>Neurological</td><td>Rs 88.5L</td><td>38</td><td>0</td></tr>
<tr><td>Torrent Injection 406</td><td>Cardiac</td><td>Rs 83.1L</td><td>31</td><td>0</td></tr>
</table>

<div class="action-box">
<strong>ACTION:</strong> Write off or transfer to discount/clearance channel. Rs 3.82 Cr recoverable.
</div>

<h3>Top At-Risk Capital</h3>
<table>
<tr><th>Product</th><th>Therapeutic</th><th>Capital</th><th>Total Qty</th><th>Recent Qty</th></tr>
<tr><td>Zydus Injection 25</td><td>Anti-viral</td><td>Rs 1.90 Cr</td><td>326</td><td>1</td></tr>
<tr><td>Lupin Syrup 167</td><td>Anti-diabetic</td><td>Rs 1.61 Cr</td><td>634</td><td>17</td></tr>
<tr><td>Glenmark Tablet 224</td><td>Cardiac</td><td>Rs 1.54 Cr</td><td>62</td><td>2</td></tr>
<tr><td>Glenmark Gel 258</td><td>Anti-diabetic</td><td>Rs 1.20 Cr</td><td>113</td><td>3</td></tr>
<tr><td>Macleods Powder 665</td><td>Anti-viral</td><td>Rs 1.18 Cr</td><td>162</td><td>8</td></tr>
</table>

<h2>3. City-Category Demand vs Inventory</h2>

<table>
<tr><th>City</th><th>Category</th><th>Revenue</th><th>OOS%</th><th>Stock Value</th><th>Status</th></tr>
<tr class="critical"><td><strong>Mumbai</strong></td><td>Rx Medicines</td><td>Rs 15.84 Cr</td><td>6.4%</td><td>Rs 38.59 Cr</td><td>UNDERSTOCK (high demand + OOS)</td></tr>
<tr class="critical"><td><strong>Pune</strong></td><td>Rx Medicines</td><td>Rs 7.79 Cr</td><td>6.1%</td><td>Rs 19.58 Cr</td><td>UNDERSTOCK</td></tr>
<tr><td>Mumbai</td><td>Wellness</td><td>Rs 6.99 Cr</td><td>0.0%</td><td>--</td><td>Balanced</td></tr>
<tr><td>Thane</td><td>Rx Medicines</td><td>Rs 5.36 Cr</td><td>6.0%</td><td>Rs 12.90 Cr</td><td>Balanced</td></tr>
<tr><td>Mumbai</td><td>OTC Medicines</td><td>Rs 4.59 Cr</td><td>0.0%</td><td>--</td><td>Balanced</td></tr>
<tr class="warning"><td>Goa</td><td>Rx Medicines</td><td>Rs 1.40 Cr</td><td>7.4%</td><td>Rs 3.17 Cr</td><td>Highest OOS rate in network</td></tr>
</table>

<div class="summary-box">
<strong>KEY FINDING:</strong> Mumbai and Pune Rx Medicines are structurally understocked despite being the two largest revenue pools. The 6.1–6.4% OOS rate on Rs 23.6 Cr combined revenue implies Rs 1.4–1.5 Cr in estimated lost sales.
</div>

<h2>4. Store-Level Lost Sales (Top 10 Opportunities)</h2>

<table>
<tr><th>Store</th><th>City</th><th>Revenue</th><th>OOS%</th><th>Est. Lost Sales</th></tr>
<tr><td>Pune STA-13</td><td>Pune</td><td>Rs 1.56 Cr</td><td>6.7%</td><td>Rs 10.5L</td></tr>
<tr><td>Mumbai STA-12</td><td>Mumbai</td><td>Rs 1.45 Cr</td><td>7.2%</td><td>Rs 10.4L</td></tr>
<tr><td>Goa STA-28</td><td>Goa</td><td>Rs 1.40 Cr</td><td>7.4%</td><td>Rs 10.4L</td></tr>
<tr><td>Mumbai STA-4</td><td>Mumbai</td><td>Rs 1.45 Cr</td><td>7.1%</td><td>Rs 10.3L</td></tr>
<tr><td>Pune FLA-17</td><td>Pune</td><td>Rs 1.53 Cr</td><td>6.7%</td><td>Rs 10.2L</td></tr>
<tr><td>Mumbai STA-5</td><td>Mumbai</td><td>Rs 1.48 Cr</td><td>6.8%</td><td>Rs 10.0L</td></tr>
<tr><td>Mumbai STA-9</td><td>Mumbai</td><td>Rs 1.54 Cr</td><td>6.4%</td><td>Rs 9.9L</td></tr>
<tr><td>Thane NEI-22</td><td>Thane</td><td>Rs 1.52 Cr</td><td>6.3%</td><td>Rs 9.6L</td></tr>
<tr><td>Mumbai STA-2</td><td>Mumbai</td><td>Rs 1.51 Cr</td><td>6.2%</td><td>Rs 9.4L</td></tr>
<tr><td>Thane FLA-20</td><td>Thane</td><td>Rs 1.50 Cr</td><td>6.2%</td><td>Rs 9.2L</td></tr>
</table>

<h2>5. Category Profitability (Margin-Dilutive Alert)</h2>

<table>
<tr><th>Category</th><th>Therapeutic</th><th>Revenue</th><th>Margin%</th><th>Stock Value</th><th>Verdict</th></tr>
<tr class="critical"><td>Rx Medicines</td><td>Neurological</td><td>Rs 12.26 Cr</td><td>17.6%</td><td>Rs 7.78 Cr</td><td>MARGIN-DILUTIVE: Largest revenue but lowest margin. Stock = 63% of revenue.</td></tr>
<tr class="warning"><td>Rx Medicines</td><td>Cardiac</td><td>Rs 3.79 Cr</td><td>17.9%</td><td>Rs 10.13 Cr</td><td>CAPITAL TRAP: Stock value 2.7x revenue!</td></tr>
<tr class="warning"><td>Rx Medicines</td><td>Anti-hypertensive</td><td>Rs 95.4L</td><td>19.2%</td><td>Rs 8.61 Cr</td><td>CAPITAL TRAP: Stock value 9x revenue. Extreme overstocking.</td></tr>
<tr class="warning"><td>Rx Medicines</td><td>Anti-allergic</td><td>Rs 93.0L</td><td>18.5%</td><td>Rs 7.70 Cr</td><td>CAPITAL TRAP: Stock value 8.3x revenue.</td></tr>
<tr class="warning"><td>Rx Medicines</td><td>Anti-viral</td><td>Rs 2.19 Cr</td><td>19.2%</td><td>Rs 9.61 Cr</td><td>CAPITAL TRAP: Stock value 4.4x revenue.</td></tr>
</table>

<h2>6. Network-Wide Summary</h2>

<table style="width:auto">
<tr><td style="color:#666">Total Network Revenue</td><td><strong>Rs 78.67 Cr</strong></td></tr>
<tr><td style="color:#666">Total Working Capital Trapped</td><td style="color:#d32f2f"><strong>Rs 3.82 Cr</strong> (zero velocity)</td></tr>
<tr><td style="color:#666">Working Capital At Risk</td><td style="color:#ef6c00"><strong>Rs 19.47 Cr</strong> (near-zero velocity)</td></tr>
<tr><td style="color:#666">Total Estimated Lost Sales</td><td style="color:#d32f2f"><strong>Rs 1.4–1.5 Cr</strong> (from OOS)</td></tr>
<tr><td style="color:#666">Worst Capital Trap Category</td><td>Anti-hypertensive (stock 9x revenue)</td></tr>
<tr><td style="color:#666">Most Underserved Market</td><td>Mumbai Rx Medicines (Rs 15.84 Cr rev, 6.4% OOS)</td></tr>
<tr><td style="color:#666">Highest OOS Store-Node</td><td>Goa STA-28 (7.4% OOS)</td></tr>
<tr><td style="color:#666">SKUs to Phase Out</td><td>816 SKUs (Rs 12.41 Cr — low margin, excess stock)</td></tr>
</table>

<h2>7. Recommended Actions (Priority Order)</h2>
<ol>
<li><strong>Immediate:</strong> Restock 12 PROTECT SKUs (esp. Sun Pharma Gel 349 at 7.4% OOS) — recover Rs 64L+ in lost sales</li>
<li><strong>Immediate:</strong> Liquidate 4 TRAPPED capital SKUs — free Rs 3.82 Cr</li>
<li><strong>This Week:</strong> Review 19 AT-RISK capital SKUs (Rs 19.47 Cr) — redistribute or mark down</li>
<li><strong>This Month:</strong> Rebalance Anti-hypertensive, Anti-allergic, Anti-viral inventory (stock 4–9x revenue)</li>
<li><strong>This Month:</strong> Increase Mumbai &amp; Pune Rx safety stock — these cities drive 30% of revenue but are structurally understocked</li>
<li><strong>This Quarter:</strong> Phase out 816 low-performing SKUs, redirect shelf space to PROTECT tier</li>
<li><strong>This Quarter:</strong> Fix Goa STA-28 supply chain (highest OOS in network at 7.4%)</li>
</ol>

<div class="footer">
Wellness Forever Revenue Intelligence | Generated by Tasknova AI | May 2026
</div>

</body>
</html>"""

HTML(string=html_content).write_pdf('inventory-intelligence-report.pdf')
print("PDF generated successfully")
