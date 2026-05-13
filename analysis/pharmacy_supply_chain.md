# Indian Pharmacy Chain — Supply Chain & Inventory Management

> Knowledge base for Tasknova chatbot. Sources: AIOCD, IPA, BioPharm International, PMC/NCBI, industry reports.

---

## 1. Supply Chain Structure

### Multi-Tier Distribution Chain

```
Manufacturer → C&F Agent (3-5%) → Stockist/Distributor (8-12%) → Sub-Stockist → Retailer (16-22% on MRP) → Consumer
```

| Role | Count in India | Function |
|---|---|---|
| C&F Agents | 25–35 per company | Storage + forwarding to stockists |
| Stockists/Distributors | ~60,000–65,000 total | Regional distribution, handles 5–15 companies each |
| Retailers | ~850,000 pharmacies | Point of sale to consumers |

- **Organized chains:** ~8.5% of total pharmacies
- **Unorganized (standalone):** ~88.7%
- **Online pharmacies:** ~2.8%

---

## 2. Stockout Problem

### Stockout Rates
- Traditional pharmacies: **5–10%+ stockout rate**
- E-pharmacies achieve ~95% fill rates
- Over **75% of retailers** experience frequent stockouts
- Revenue losses: **3–10% annually** from stockouts

### Cost of Stockouts
- **30–40%** of customers who experience a stockout buy from a competitor
- **40%** will take their entire basket elsewhere (not just the missing item)
- Each stockout **reduces return visit probability by ~9%**
- **Basket loss:** Customer came for 1 item but would buy 3–4 more; stockout loses the entire basket
- A Tamil Nadu chain calculated recurring stockouts on 12 medicines cost ~**INR 1.8 L/month** in direct lost sales

### Root Causes
- Manual tracking errors and lack of real-time visibility
- Vendors dumping near-expiry goods
- Rural location and communication hurdles
- No demand forecasting (most pharmacies use intuition)
- Limited SKU capacity: offline pharmacy holds 6,000–8,000 SKUs vs 50,000+ online

---

## 3. Demand Forecasting

### Seasonal Patterns in India

| Season | Category Spike | Key Products |
|---|---|---|
| **Monsoon** (Jun–Sep) | Respiratory, anti-infectives | Antivirals, decongestants, cough syrups, anti-malarials |
| **Summer** (Mar–Jun) | Gastrointestinal | ORS, antidiarrheals, electrolytes |
| **Winter** (Nov–Feb) | Cardiac, respiratory | Cold/flu remedies, cardiac drugs |
| **Poor AQI periods** | Respiratory | Inhalers, respiratory aids |
| **Festive/Wedding** | General wellness | Vitamins, supplements, dermatological |

### Current State
- Apollo Pharmacy reportedly does **not use** formal demand forecasting models — relies on experience-based ordering
- Most unorganized pharmacies rely on **intuition and experience**
- Winter's Exponential Smoothing (WES) achieved best accuracy: **MAPE = 27.5%** for seasonal products

### Top Therapeutic Segments (FY25 by turnover)
Cardiac > Gastrointestinal > Anti-diabetic (volume growth 9%, 8.7%, 8.4% respectively)

---

## 4. Inventory Management

### Days of Inventory on Hand (DOH)

| Context | DOH |
|---|---|
| General retail optimal | 30–45 days |
| Pharma (safety-focused) | 100–180 days |
| Best-in-class pharmacy | 30–45 days |
| Underperforming | 60+ days |

### ABC-VED Analysis

**ABC (by expenditure):**
- **A:** 14.4% of drugs consume **70% of budget** — strict control
- **B:** 22.5% of drugs consume **20%** — moderate control
- **C:** 63.7% of drugs consume **10%** — routine control

**VED (by criticality):**
- **Vital:** 7.3% — cannot function without (insulin, cardiac emergency drugs)
- **Essential:** 49.3% — service quality affected if unavailable
- **Desirable:** 43.3% — unavailability doesn't interfere

**Combined Matrix Priority:**
- Category I (AV, BV, CV, AE, AD) — highest priority, strict monitoring
- Category II (BE, CE, BD) — moderate
- Category III (CD) — routine

### Expiry & Dead Stock
- Indian pharmacies lose **INR 20,000–50,000/month** per store from expired stock
- Industry benchmark: **3% of inventory value** for expired stock
- Common causes: unpredictable demand, near-expiry supplier dumps, manual tracking, lack of FEFO discipline

---

## 5. Cold Chain Logistics

### Market Size
- India cold chain market: **USD 4.7 Bn (2024)**, projected USD 12.2 Bn by 2030 at **17% CAGR**

### Infrastructure Gaps
- Over **90%** of cold chain logistics is fragmented and privately owned
- Gaps especially visible in **Tier II/III** markets
- India's Drugs & Cosmetics Act lacks specific temperature classifications
- Single temperature excursion can compromise entire batches

### Vaccine Wastage (Proxy for Cold Chain Failure)
- BCG wastage: **38.9–60.4%** (over 50% permissible limit)
- OPV wastage: 33.6%
- Government planning overhaul of pharmaceutical storage rules

---

## 6. Distributor Dynamics

### Margin Structure

| Role | Margin Range |
|---|---|
| Retailer | 16–25% of MRP |
| Distributor/Stockist (Branded) | 8–12% |
| Distributor/Stockist (Generic) | 10–20% |
| C&F Agent | 3–5% |

### Credit Periods

| Relationship | Credit Period |
|---|---|
| Manufacturer to Distributor | 30–45 days |
| Generic companies to Distributor | 45–70 days |
| Distributor to Retailer | 7–30 days (up to 90 for large chains) |

### Counterfeit Drug Problem
- Estimated **13–25%** of Indian pharmacy stock is counterfeit
- In major cities, **1 in 5 medicines** may be fraudulent
- **75% of global counterfeit cases** originate from India
- ASSOCHAM estimate: fake drugs = **USD 4.25 Bn** of domestic market

---

## 7. Warehousing Models

| Chain | Approach |
|---|---|
| **Wellness Forever** | Zero Error Distribution Center (ZEDC) — integrated with central planogramming, POS, ERP, OMS |
| **Apollo** | Microsoft Dynamics ERP + Nutanix Cloud (1.7x speed improvement); micro-warehousing at store level |
| **MedPlus** | Automated warehouses in multiple cities; 1.2M+ online Rx orders/month |

### Common Models
- **Central Warehouse:** Single large DC serving a region
- **Hub-and-Spoke:** Central hub → satellite warehouses near stores
- **Micro-warehousing:** Converting store back-of-house into mini fulfillment centers
- **Cross-docking:** Emerging in organized chains

---

## 8. Regulatory Requirements

### Drug License
- All pharmacies require license under Drugs and Cosmetics Act, 1940
- Registered pharmacist must be on premises during operating hours

### Schedule H/H1 Tracking

**Schedule H:** Records must include manufacturer name, batch number, expiry date

**Schedule H1:** Separate register with:
- Prescriber name and address
- Patient name and phone
- Drug name and quantity
- Records maintained **3 years**, open for Drug Inspector audit

### DAVA System (Drug Authentication & Verification)
- Track-and-trace at primary, secondary, tertiary levels
- Replaced by **iVEDA** (April 2020) for export drug serialization
- QR codes/barcodes mandated on top 300 medicine brands (Aug 2023)

---

## 9. Technology in Supply Chain

### ERP Systems

| Chain | System |
|---|---|
| Apollo | Microsoft Dynamics + Nutanix Cloud |
| Wellness Forever | Custom ERP + ZEDC + OMS |
| MedPlus | Proprietary IT + automated warehousing |

### India-Specific Pharmacy Software
LOGIC ERP, EvitalRx, Gofrugal, RxERP, Pharma247 — offering billing, GST compliance, batch tracking, expiry management.

### RFID Adoption
- Adoption areas: Distribution (72.4%), Warehousing (53.4%), Reverse Logistics (48.3%)
- RFID delivers **98–99% inventory accuracy**
- Main barriers: high device cost (60.3%), limited understanding (58.6%)

### Automated Replenishment
- RFID-detected depletion triggers auto replenishment to WMS
- AI predicts demand, detects anomalies, optimizes storage
- Most unorganized pharmacies still rely on **manual stock counts** and phone ordering

---

## Key Summary Statistics

| Metric | Value |
|---|---|
| Total pharmacies in India | ~850,000 |
| Organized chain share | ~8.5% |
| Total stockists/distributors | 60,000–65,000 |
| Retail pharmacy market size | USD 24 Bn (2024) |
| Market CAGR | ~10% (to 2030) |
| Typical stockout revenue loss | 3–10% annually |
| Customer switching on stockout | 30–40% |
| Monthly expiry loss per store | INR 20K–50K |
| Expired stock benchmark | 3% of inventory |
| Cold chain market | USD 4.7 Bn (2024) |
| Counterfeit drug estimate | 13–25% of market |
| RFID inventory accuracy | 98–99% |
