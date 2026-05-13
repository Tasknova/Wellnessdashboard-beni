import json, datetime

html = """<div style="font-family:inherit;color:#1f2937;font-size:13px;line-height:1.6">

<p style="font-size:16px;font-weight:700;color:#1e3a5f;margin:0 0 2px">Inventory Intelligence Report</p>
<p style="font-size:11px;color:#6b7280;margin:0 0 12px">Demand-availability mismatch, SKU classification &amp; profit optimization across 30 stores</p>

<div style="display:flex;gap:8px;flex-wrap:wrap;margin-bottom:14px">
  <div style="flex:1;min-width:90px;background:white;border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;text-align:center">
    <div style="font-size:15px;font-weight:700;color:#1e3a5f">Rs 78.67 Cr</div>
    <div style="font-size:10px;color:#6b7280">Total Revenue</div>
  </div>
  <div style="flex:1;min-width:90px;background:white;border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;text-align:center">
    <div style="font-size:15px;font-weight:700;color:#dc2626">Rs 3.82 Cr</div>
    <div style="font-size:10px;color:#6b7280">Capital Trapped</div>
  </div>
  <div style="flex:1;min-width:90px;background:white;border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;text-align:center">
    <div style="font-size:15px;font-weight:700;color:#d97706">Rs 19.47 Cr</div>
    <div style="font-size:10px;color:#6b7280">Capital At Risk</div>
  </div>
  <div style="flex:1;min-width:90px;background:white;border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;text-align:center">
    <div style="font-size:15px;font-weight:700;color:#dc2626">Rs 1.5 Cr</div>
    <div style="font-size:10px;color:#6b7280">Est. Lost Sales</div>
  </div>
  <div style="flex:1;min-width:90px;background:white;border:1px solid #e5e7eb;border-radius:8px;padding:8px 10px;text-align:center">
    <div style="font-size:15px;font-weight:700;color:#6b7280">816</div>
    <div style="font-size:10px;color:#6b7280">SKUs to Phase Out</div>
  </div>
</div>

<p style="font-size:13px;font-weight:700;color:#1e3a5f;margin:14px 0 6px;border-bottom:2px solid #e5e7eb;padding-bottom:4px">1. SKU Decision Buckets</p>

<table class="chat-table">
<tr><th>Bucket</th><th>SKUs</th><th>Revenue</th><th>Action</th></tr>
<tr><td><span style="background:#059669;color:white;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:600">PROTECT</span></td><td>12</td><td>Rs 18.99 Cr</td><td>High-revenue + high OOS. Restock immediately</td></tr>
<tr><td><span style="background:#d97706;color:white;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:600">MONITOR</span></td><td>34</td><td>Rs 10.26 Cr</td><td>Good revenue, margin &lt;20%. Renegotiate or substitute</td></tr>
<tr><td><span style="background:#3b82f6;color:white;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:600">SEASONAL</span></td><td>138</td><td>Rs 37.02 Cr</td><td>Revenue dropped &gt;70%. Hold stock, don't reorder</td></tr>
<tr><td><span style="background:#dc2626;color:white;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:600">PHASE OUT</span></td><td>816</td><td>Rs 12.41 Cr</td><td>Low revenue + low margin + excess stock. Liquidate</td></tr>
</table>

<details style="margin:8px 0">
<summary style="cursor:pointer;color:#1e3a5f;font-weight:600;font-size:12px;padding:4px 0">Top PROTECT &amp; REPLENISH SKUs</summary>
<table class="chat-table" style="margin-top:6px">
<tr><th>Product</th><th>Therapeutic</th><th>Revenue</th><th>OOS%</th><th>Action</th></tr>
<tr style="background:#fef2f2"><td><strong>Sun Pharma Gel 349</strong></td><td>Neurological</td><td>Rs 8.70 Cr</td><td style="color:#dc2626;font-weight:600">7.4%</td><td>#1 revenue SKU — est. Rs 64L lost</td></tr>
<tr><td>Aurobindo Drops 122</td><td>Dermatological</td><td>Rs 2.02 Cr</td><td style="color:#dc2626">6.7%</td><td>Increase safety stock</td></tr>
<tr><td>Abbott India Inhaler 394</td><td>Anti-diabetic</td><td>Rs 1.10 Cr</td><td style="color:#d97706">5.9%</td><td>Chronic-use, OOS = patient churn</td></tr>
<tr><td>Sun Pharma Ointment 845</td><td>Cardiac</td><td>Rs 1.04 Cr</td><td style="color:#d97706">5.9%</td><td>Cardiac anchor, 100% availability</td></tr>
<tr><td>Macleods Capsule 690</td><td>Antibiotic</td><td>Rs 1.01 Cr</td><td style="color:#d97706">5.4%</td><td>High Rx volume, buffer needed</td></tr>
</table>
</details>

<p style="font-size:13px;font-weight:700;color:#1e3a5f;margin:14px 0 6px;border-bottom:2px solid #e5e7eb;padding-bottom:4px">2. Working Capital</p>

<table class="chat-table">
<tr><th>Status</th><th>SKUs</th><th>Capital</th><th>Issue</th></tr>
<tr style="background:#fef2f2"><td><span style="background:#dc2626;color:white;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:600">TRAPPED</span></td><td>4</td><td>Rs 3.82 Cr</td><td>Zero movement in 30+ days</td></tr>
<tr style="background:#fffbeb"><td><span style="background:#d97706;color:white;padding:2px 8px;border-radius:3px;font-size:10px;font-weight:600">AT RISK</span></td><td>19</td><td>Rs 19.47 Cr</td><td>Velocity collapsing (&lt;5% of historical)</td></tr>
<tr><td>HEALTHY</td><td colspan="3">Remaining SKUs have adequate demand-to-stock ratios</td></tr>
</table>

<details style="margin:8px 0">
<summary style="cursor:pointer;color:#1e3a5f;font-weight:600;font-size:12px;padding:4px 0">Trapped Capital Details (Rs 3.82 Cr)</summary>
<table class="chat-table" style="margin-top:6px">
<tr><th>Product</th><th>Therapeutic</th><th>Capital</th><th>Hist Qty</th><th>Recent</th></tr>
<tr><td>Cipla Suspension 572</td><td>Pain Mgmt</td><td>Rs 1.15 Cr</td><td>122</td><td style="color:#dc2626;font-weight:600">0</td></tr>
<tr><td>Aurobindo Ointment 60</td><td>Neurological</td><td>Rs 95.1L</td><td>22</td><td style="color:#dc2626;font-weight:600">0</td></tr>
<tr><td>Torrent Suspension 626</td><td>Neurological</td><td>Rs 88.5L</td><td>38</td><td style="color:#dc2626;font-weight:600">0</td></tr>
<tr><td>Torrent Injection 406</td><td>Cardiac</td><td>Rs 83.1L</td><td>31</td><td style="color:#dc2626;font-weight:600">0</td></tr>
</table>
</details>

<details style="margin:8px 0">
<summary style="cursor:pointer;color:#1e3a5f;font-weight:600;font-size:12px;padding:4px 0">Top At-Risk Capital (Rs 19.47 Cr)</summary>
<table class="chat-table" style="margin-top:6px">
<tr><th>Product</th><th>Therapeutic</th><th>Capital</th><th>Total Qty</th><th>Recent</th></tr>
<tr><td>Zydus Injection 25</td><td>Anti-viral</td><td>Rs 1.90 Cr</td><td>326</td><td style="color:#d97706;font-weight:600">1</td></tr>
<tr><td>Lupin Syrup 167</td><td>Anti-diabetic</td><td>Rs 1.61 Cr</td><td>634</td><td style="color:#d97706;font-weight:600">17</td></tr>
<tr><td>Glenmark Tablet 224</td><td>Cardiac</td><td>Rs 1.54 Cr</td><td>62</td><td style="color:#d97706;font-weight:600">2</td></tr>
<tr><td>Glenmark Gel 258</td><td>Anti-diabetic</td><td>Rs 1.20 Cr</td><td>113</td><td style="color:#d97706;font-weight:600">3</td></tr>
<tr><td>Macleods Powder 665</td><td>Anti-viral</td><td>Rs 1.18 Cr</td><td>162</td><td style="color:#d97706;font-weight:600">8</td></tr>
</table>
</details>

<p style="font-size:13px;font-weight:700;color:#1e3a5f;margin:14px 0 6px;border-bottom:2px solid #e5e7eb;padding-bottom:4px">3. City-Category Demand vs Inventory</p>

<table class="chat-table">
<tr><th>City</th><th>Category</th><th>Revenue</th><th>OOS%</th><th>Stock Value</th><th>Status</th></tr>
<tr style="background:#fef2f2"><td><strong>Mumbai</strong></td><td>Rx Medicines</td><td>Rs 15.84 Cr</td><td style="color:#dc2626">6.4%</td><td>Rs 38.59 Cr</td><td style="color:#dc2626;font-weight:600">UNDERSTOCK</td></tr>
<tr style="background:#fef2f2"><td><strong>Pune</strong></td><td>Rx Medicines</td><td>Rs 7.79 Cr</td><td style="color:#dc2626">6.1%</td><td>Rs 19.58 Cr</td><td style="color:#dc2626;font-weight:600">UNDERSTOCK</td></tr>
<tr><td>Mumbai</td><td>Wellness</td><td>Rs 6.99 Cr</td><td style="color:#059669">0.0%</td><td>--</td><td style="color:#059669">Balanced</td></tr>
<tr><td>Thane</td><td>Rx Medicines</td><td>Rs 5.36 Cr</td><td style="color:#d97706">6.0%</td><td>Rs 12.90 Cr</td><td>Balanced</td></tr>
<tr style="background:#fffbeb"><td>Goa</td><td>Rx Medicines</td><td>Rs 1.40 Cr</td><td style="color:#dc2626;font-weight:600">7.4%</td><td>Rs 3.17 Cr</td><td style="color:#dc2626;font-weight:600">Highest OOS</td></tr>
</table>

<div class="chat-action" style="margin:10px 0">
<strong>Key Finding:</strong> Mumbai + Pune Rx are structurally understocked. 6.1-6.4% OOS on Rs 23.6 Cr combined revenue = Rs 1.4-1.5 Cr lost sales.
</div>

<p style="font-size:13px;font-weight:700;color:#1e3a5f;margin:14px 0 6px;border-bottom:2px solid #e5e7eb;padding-bottom:4px">4. Store-Level Lost Sales (Top 10)</p>

<table class="chat-table">
<tr><th>Store</th><th>City</th><th>Revenue</th><th>OOS%</th><th>Est. Lost</th></tr>
<tr><td>Pune STA-13</td><td>Pune</td><td>Rs 1.56 Cr</td><td style="color:#dc2626">6.7%</td><td style="font-weight:600">Rs 10.5L</td></tr>
<tr><td>Mumbai STA-12</td><td>Mumbai</td><td>Rs 1.45 Cr</td><td style="color:#dc2626">7.2%</td><td style="font-weight:600">Rs 10.4L</td></tr>
<tr><td>Goa STA-28</td><td>Goa</td><td>Rs 1.40 Cr</td><td style="color:#dc2626">7.4%</td><td style="font-weight:600">Rs 10.4L</td></tr>
<tr><td>Mumbai STA-4</td><td>Mumbai</td><td>Rs 1.45 Cr</td><td style="color:#dc2626">7.1%</td><td style="font-weight:600">Rs 10.3L</td></tr>
<tr><td>Pune FLA-17</td><td>Pune</td><td>Rs 1.53 Cr</td><td style="color:#dc2626">6.7%</td><td style="font-weight:600">Rs 10.2L</td></tr>
<tr><td>Mumbai STA-5</td><td>Mumbai</td><td>Rs 1.48 Cr</td><td style="color:#dc2626">6.8%</td><td style="font-weight:600">Rs 10.0L</td></tr>
<tr><td>Mumbai STA-9</td><td>Mumbai</td><td>Rs 1.54 Cr</td><td style="color:#d97706">6.4%</td><td style="font-weight:600">Rs 9.9L</td></tr>
<tr><td>Thane NEI-22</td><td>Thane</td><td>Rs 1.52 Cr</td><td style="color:#d97706">6.3%</td><td style="font-weight:600">Rs 9.6L</td></tr>
<tr><td>Mumbai STA-2</td><td>Mumbai</td><td>Rs 1.51 Cr</td><td style="color:#d97706">6.2%</td><td style="font-weight:600">Rs 9.4L</td></tr>
<tr><td>Thane FLA-20</td><td>Thane</td><td>Rs 1.50 Cr</td><td style="color:#d97706">6.2%</td><td style="font-weight:600">Rs 9.2L</td></tr>
</table>

<p style="font-size:13px;font-weight:700;color:#1e3a5f;margin:14px 0 6px;border-bottom:2px solid #e5e7eb;padding-bottom:4px">5. Category Profitability Alerts</p>

<table class="chat-table">
<tr><th>Therapeutic</th><th>Revenue</th><th>Margin%</th><th>Stock Val</th><th>Verdict</th></tr>
<tr style="background:#fef2f2"><td>Neurological</td><td>Rs 12.26 Cr</td><td style="color:#dc2626">17.6%</td><td>Rs 7.78 Cr</td><td style="color:#dc2626;font-weight:600">Margin-dilutive (stock 63% of rev)</td></tr>
<tr style="background:#fffbeb"><td>Cardiac</td><td>Rs 3.79 Cr</td><td style="color:#d97706">17.9%</td><td>Rs 10.13 Cr</td><td style="color:#d97706;font-weight:600">Capital trap (stock 2.7x rev)</td></tr>
<tr style="background:#fffbeb"><td>Anti-hypertensive</td><td>Rs 95.4L</td><td>19.2%</td><td>Rs 8.61 Cr</td><td style="color:#dc2626;font-weight:600">Capital trap (stock 9x rev!)</td></tr>
<tr style="background:#fffbeb"><td>Anti-allergic</td><td>Rs 93.0L</td><td>18.5%</td><td>Rs 7.70 Cr</td><td style="color:#dc2626;font-weight:600">Capital trap (stock 8.3x rev)</td></tr>
<tr style="background:#fffbeb"><td>Anti-viral</td><td>Rs 2.19 Cr</td><td>19.2%</td><td>Rs 9.61 Cr</td><td style="color:#d97706;font-weight:600">Capital trap (stock 4.4x rev)</td></tr>
</table>

<p style="font-size:13px;font-weight:700;color:#1e3a5f;margin:14px 0 6px;border-bottom:2px solid #e5e7eb;padding-bottom:4px">6. Recommended Actions</p>

<div style="background:white;border:1px solid #e5e7eb;border-radius:8px;padding:10px 14px;margin:6px 0">
<ol style="margin:0;padding-left:18px;color:#374151;font-size:12px">
<li style="margin-bottom:6px"><span style="background:#dc2626;color:white;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;margin-right:4px">NOW</span> Restock 12 PROTECT SKUs (Sun Pharma Gel 349 priority) — recover Rs 64L+</li>
<li style="margin-bottom:6px"><span style="background:#dc2626;color:white;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;margin-right:4px">NOW</span> Liquidate 4 trapped-capital SKUs — free Rs 3.82 Cr</li>
<li style="margin-bottom:6px"><span style="background:#d97706;color:white;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;margin-right:4px">WEEK</span> Review 19 at-risk SKUs (Rs 19.47 Cr) — redistribute or mark down</li>
<li style="margin-bottom:6px"><span style="background:#d97706;color:white;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;margin-right:4px">MONTH</span> Rebalance Anti-hypertensive/Anti-allergic/Anti-viral (stock 4-9x revenue)</li>
<li style="margin-bottom:6px"><span style="background:#3b82f6;color:white;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;margin-right:4px">MONTH</span> Increase Mumbai &amp; Pune Rx safety stock (30% of revenue, understocked)</li>
<li style="margin-bottom:6px"><span style="background:#6b7280;color:white;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;margin-right:4px">QTR</span> Phase out 816 low-performing SKUs, redirect shelf space to PROTECT tier</li>
<li><span style="background:#6b7280;color:white;padding:1px 6px;border-radius:3px;font-size:9px;font-weight:700;margin-right:4px">QTR</span> Fix Goa STA-28 supply chain (7.4% OOS, highest in network)</li>
</ol>
</div>

</div>"""

# Write response
with open('chatbot_response.txt', 'w', encoding='utf-8') as f:
    f.write(html)

# Log
log_entry = {
    "ts": datetime.datetime.now().isoformat(),
    "query": "Restyled inventory intelligence report (light-theme fix)",
    "mode": "INSIGHTS",
    "handler": "claude_code",
    "entities": {},
    "response_len": len(html),
    "cached": False
}
with open('analysis/conversation_log.jsonl', 'a', encoding='utf-8') as f:
    f.write(json.dumps(log_entry) + '\n')

print(f"Response written ({len(html)} chars)")
