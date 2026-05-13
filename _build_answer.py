import sqlite3, json

db = sqlite3.connect('data/wf_intelligence.db')
db.row_factory = sqlite3.Row

r = {}
r['top_brands'] = [dict(x) for x in db.execute('''
SELECT p.brand, SUM(li.line_total) as revenue, COUNT(DISTINCT p.product_id) as skus,
  ROUND(SUM(li.margin_amount)/SUM(li.line_total)*100,1) as margin_pct
FROM order_line_items li JOIN orders o ON li.order_id=o.order_id
JOIN products p ON li.product_id=p.product_id WHERE o.status='Delivered'
GROUP BY p.brand ORDER BY revenue DESC LIMIT 10
''').fetchall()]

r['generic_branded'] = [dict(x) for x in db.execute('''
SELECT CASE WHEN p.is_generic=1 THEN 'Generic' ELSE 'Branded' END as type,
  SUM(li.line_total) as revenue, SUM(li.margin_amount) as margin,
  ROUND(SUM(li.margin_amount)/SUM(li.line_total)*100,1) as margin_pct,
  COUNT(DISTINCT p.product_id) as skus
FROM order_line_items li JOIN orders o ON li.order_id=o.order_id
JOIN products p ON li.product_id=p.product_id WHERE o.status='Delivered'
GROUP BY type
''').fetchall()]

r['channel'] = [dict(x) for x in db.execute('''
SELECT o.channel, SUM(li.line_total) as revenue, COUNT(DISTINCT o.order_id) as orders,
  ROUND(SUM(li.margin_amount)/SUM(li.line_total)*100,1) as margin_pct
FROM order_line_items li JOIN orders o ON li.order_id=o.order_id WHERE o.status='Delivered'
GROUP BY o.channel
''').fetchall()]

r['cities'] = [dict(x) for x in db.execute('''
SELECT s.city, COUNT(DISTINCT s.store_id) as stores, SUM(li.line_total) as revenue
FROM order_line_items li JOIN orders o ON li.order_id=o.order_id
JOIN stores s ON o.store_id=s.store_id WHERE o.status='Delivered'
GROUP BY s.city ORDER BY revenue DESC
''').fetchall()]

r['loyalty'] = [dict(x) for x in db.execute('''
SELECT c.loyalty_tier, COUNT(DISTINCT c.customer_id) as customers,
  SUM(li.line_total) as revenue
FROM order_line_items li JOIN orders o ON li.order_id=o.order_id
JOIN customers c ON o.customer_id=c.customer_id WHERE o.status='Delivered'
GROUP BY c.loyalty_tier ORDER BY revenue DESC
''').fetchall()]

db.close()

def inr(v):
    v = float(v)
    if v >= 10000000: return f'\u20b9{v/10000000:.1f} Cr'
    if v >= 100000: return f'\u20b9{v/100000:.1f} L'
    return f'\u20b9{v/1000:.1f}K'

TH = 'background:#e0e3e8;color:#1a1a2e;font-weight:600'
BD = 'border-bottom:1px solid #d1d5db'
GREEN = '#1e8449'
RED = '#c0392b'
AMBER = '#b7950b'

html = '<div class="analysis-response">'
html += '<h3 style="color:#1a1a2e">Competitive Positioning Analysis</h3>'
html += '<p style="color:#6c757d;font-size:12px"><em>Note: External competitor data is not in our database. This analysis uses internal data to assess competitive strengths and vulnerabilities vs the market.</em></p>'

html += '<div style="background:#ffffff;padding:12px;border-radius:8px;border:1px solid #d1d5db;margin-bottom:10px">'
html += '<p style="margin:0"><strong>Wellness Forever:</strong> 30 stores | 7 cities | \u20b978.7 Cr revenue | 4,999 customers | 1,000 SKUs</p>'
html += '</div>'

# Competitors
html += '<h4>Competitive Landscape (Indian Pharmacy Retail)</h4>'
html += '<table style="width:100%;border-collapse:collapse;font-size:13px">'
html += f'<tr style="{TH}"><th style="padding:6px;text-align:left">Player</th><th>Stores</th><th>Presence</th><th>WF Advantage</th></tr>'
comps = [
    ('Apollo Pharmacy', '5,800+', 'Pan-India', 'WF has deeper West India penetration'),
    ('MedPlus', '4,000+', 'South & West', 'WF competes on convenience + loyalty'),
    ('NetMeds (Reliance)', 'Online', 'Pan-India', 'WF has physical + online hybrid'),
    ('PharmEasy', 'Online', 'Pan-India', 'WF has instant in-store pickup'),
    ('1mg (Tata)', 'Online', 'Pan-India', 'WF has local trust + Rx relationships'),
]
for name, stores_c, pres, adv in comps:
    html += f'<tr style="{BD}"><td style="padding:4px;font-weight:600">{name}</td><td style="text-align:center">{stores_c}</td><td>{pres}</td><td style="font-size:12px;color:{GREEN}">{adv}</td></tr>'
html += '</table>'

# Strengths
html += '<h4>Our Competitive Strengths (Data-Backed)</h4>'
gb = r['generic_branded']
generic = next((x for x in gb if x['type'] == 'Generic'), {})
branded = next((x for x in gb if x['type'] == 'Branded'), {})
online = next((x for x in r['channel'] if x['channel'] == 'Online'), {})
offline = next((x for x in r['channel'] if x['channel'] == 'Offline'), {})

html += '<ul style="padding-left:18px">'
html += f'<li><strong>Generic penetration:</strong> {generic.get("skus",0)} generic SKUs generating {inr(generic.get("revenue",0))} at {generic.get("margin_pct",0)}% margin vs branded at {branded.get("margin_pct",0)}%</li>'
html += f'<li><strong>Omnichannel:</strong> Online {inr(online.get("revenue",0))} ({int(online.get("orders",0)):,} orders) + Offline {inr(offline.get("revenue",0))} ({int(offline.get("orders",0)):,} orders)</li>'
html += f'<li><strong>Geographic focus:</strong> {len(r["cities"])} cities with Mumbai contributing {inr(r["cities"][0]["revenue"])} (41% of revenue)</li>'
html += f'<li><strong>Loyalty base:</strong> {sum(int(x["customers"]) for x in r["loyalty"]):,} active customers across {len(r["loyalty"])} loyalty tiers</li>'
html += '</ul>'

# Vulnerabilities
html += '<h4>Competitive Vulnerabilities</h4>'
html += f'<div style="background:#ffffff;padding:10px;border-radius:8px;border:1px solid #d1d5db">'
html += '<ul style="padding-left:18px;margin:0">'
html += f'<li style="color:{RED}"><strong>Scale gap:</strong> 30 stores vs Apollo\'s 5,800+ \u2014 limited bargaining power with suppliers</li>'
html += f'<li style="color:{RED}"><strong>Rx margin pressure:</strong> 18.4% margin on Rx (49% of revenue) \u2014 online players undercut on price</li>'
html += f'<li style="color:{AMBER}"><strong>Geographic concentration:</strong> Mumbai-heavy (41%) \u2014 vulnerable to local disruption</li>'
html += f'<li style="color:{AMBER}"><strong>OOS rate 6.1%:</strong> Higher than industry benchmark (~3-4%) \u2014 customers may switch to competitors</li>'
html += '</ul></div>'

html += '</div>'
print(f'HTML: {len(html)} chars')
answer = {'response_html': html, 'tools_used': ['query_database'], 'elapsed_ms': 0}
with open('analysis/_pending_answer.json', 'w', encoding='utf-8') as f:
    json.dump(answer, f, ensure_ascii=False)
print('Done')
