# Tasknova Bible — Summary: Overall Model, Strengths & Weaknesses

> Source document: `Tn Bible 2026 v3.pdf` (300 pages, 11 sections, ~87 numbered questions)
> Updated: April 2026 (v3)

---

## What Tasknova Is — The Core Model

Tasknova is a **Revenue Intelligence Platform** that ingests every customer-facing interaction (calls, demos, emails, chat, WhatsApp, Telegram, Discord) and converts them into a layered intelligence stack that gives sales reps, managers, and executives visibility into account health, deal risk, execution quality, and revenue outcomes.

### The One-Sentence Position
> CRM captures stage. Tasknova captures reality.

### The Central Problem It Solves
Companies lose revenue not because they don't talk to customers — but because every customer conversation is fragmented across channels, people, and teams, with no shared memory, no execution feedback loop, and no link between what was said and what happened to revenue.

---

## The Intelligence Architecture (The Full Model)

Tasknova is built as a **4-layer intelligence stack**, each layer feeding the next:

```
Layer 1 — CUSTOMER INTELLIGENCE
  What the account/buyer is actually signaling
  How each stakeholder prefers to be handled
  ↓
Layer 2 — SALES INTELLIGENCE
  How well the team is executing
  What behaviors are creating or destroying pipeline quality
  ↓
Layer 3 — REVENUE INTELLIGENCE
  What the business consequences are
  Forecast confidence, deal risk, renewal health, lifecycle leakage
  ↓
Layer 4 — STRATEGIC INTELLIGENCE (Phase 3)
  What may happen next under changing conditions
  Scenario simulation, predictive models, Miro Fish / swarm agent logic
```

### The 4 Product Intelligence Object Layers

| Layer | Key Objects |
|---|---|
| **Core Intelligence** | Composite Account Memory, Stakeholder Influence Mapping, Hidden Blocker Detection, Relationship Fragility, Commitment Credibility, Deal Momentum, Expectation Mismatch |
| **Revenue Intelligence** | Forecast Confidence Score, Stage Progression Integrity, Revenue at Risk, Deal Slippage Prediction, Expansion Readiness, Renewal Risk |
| **Action Layer** | Next Best Action Engine, Stakeholder Targeting Recommendation, Intervention Priority Ranking, Scenario-Based Response Suggestions, Auto-Generated Account Briefs |
| **Full Journey Layer** | Sales → Implementation Continuity, Handoff Quality Analysis, Promise vs. Delivery Tracking, Revenue Leakage Across Lifecycle |

### The 3 Evolution Stages (Product Maturity Model)

1. **Interaction Intelligence** — Recording and summarizing what was said *(entry point)*
2. **Execution Intelligence** — Interpreting how well the team performed *(diagnostic)*
3. **Business Intelligence** — Converting signals into revenue truth *(strategic destination)*

### Target Users

| Role | Primary Intelligence Consumed | The Truth They Seek |
|---|---|---|
| Founders / CROs | Revenue & Strategic | Is our revenue predictable? Is strategy working in the field? |
| RevOps / COOs | Revenue & Journey | Where is lifecycle leakage? Are forecast stages a lie? |
| Managers | Sales & Action | Who do I coach today? Which deal needs intervention now? |
| Reps / Frontline | Action & Interaction | What's my next move? What did I miss in that last call? |
| QA / Enablement | Sales Intelligence | Which interactions fail? How do we standardize? |
| CS / Onboarding / Support | Customer & Journey | What was promised? Where is continuity breaking? |

### Target Market
- **Geography**: India-first (BPO, Real Estate, EdTech, SaaS, BFSI, Healthcare), then SEA + GCC + Global
- **Company size**: SMB to Mid-Market first (10–200 reps), Enterprise later
- **Stage**: Series A → Enterprise
- **Vertical fit**: Any company with high-volume human customer interactions (B2B SaaS, Real Estate, EdTech, BPO, Financial Services, HealthTech, D2C, Logistics, Hospitality, IT Services/Consulting)

---

## MVP Module Stack

### Ships in MVP (Phase 1) — 15 Features
- Multi-Channel Interaction Capture (calls, demos, chat, email, WhatsApp, Telegram, Discord)
- Account Memory & Lead Timeline
- Company Interaction Profile
- Stakeholder Interaction Profile
- Customer Intelligence Layer
- Sales Intelligence Layer
- Revenue & Customer Journey Reports
- Manager Intervention Dashboard
- Executive & RevOps Intelligence Dashboard
- Rep Action Layer
- Weekly Improvement Engine
- Account & Stakeholder Intelligence Layer
- Role-Based Access
- Redaction & Governance Controls
- Basic Trust / Communication Quality Signals

### Phase 2
- Forecast Confidence Engine
- Account Risk Scoring
- Expansion & Churn Signal Layer
- Dynamic LMS
- Cross-Team Shared Learning
- Manager Coaching AI
- Advanced Trust Engine
- Handoff & Continuity Intelligence
- Promise vs. Delivery Tracking
- CRM API sync (HubSpot, Zoho, Salesforce)
- Slack, Teams, Intercom, Zendesk integrations

### Phase 3
- Customer Journey Intelligence Across Departments
- Real-Time Next Best Action Engine
- Predictive Win/Churn/Expansion Models
- Strategic Intelligence / Simulation Layer
- Company-Wide Knowledge Graph
- Competency Maps & Workflow Automation

---

## Strengths

### 1. Full Customer Lifecycle Coverage
Most competitors (Gong, Outreach) are pre-sale focused. Tasknova explicitly covers the full journey from lead qualification → demo → negotiation → onboarding → support → renewal → expansion. The Promise vs. Delivery Tracking, Handoff Quality Analysis, and Renewal Risk Intelligence objects make this credible — not just a marketing claim.

### 2. Multi-Channel Depth from Day 1
MVP ingests: calls (Exotel, Twilio), Zoom/Meet demos, Gmail/Outlook emails, WhatsApp Business, Telegram, Discord. Most Western RI tools are call-and-email only. This is a direct fit for India and SEA markets where WhatsApp is a primary sales channel.

### 3. Deep India Market Fit
- Whisper large-v3 with Hindi-English code-switching optimization (WER < 18%)
- Exotel/Twilio Day 1 integrations
- TRAI, DLT, and WhatsApp Business API compliance baked in
- Industry verticals calibrated for India: Real Estate, EdTech, BPO, BFSI, healthcare
- Awareness of spam/DLT trust score issues specific to Indian telecalling

### 4. Behavioral Memory Layer (Structural Moat)
The Company Interaction Profile + Stakeholder Interaction Profile is conceptually the strongest differentiator. It captures not just what happened, but *how this account and its people should be handled* — preferred channels, tone preferences, what builds trust, what creates friction, how Roger from Acme reacts under pressure. This compounds in value over time and is extremely hard to replicate.

### 5. Actionable, Not Just Analytical
Every layer terminates in actions: weekly rep improvement plans (3 focus areas, 3 actions, evidence clips), manager coaching agendas, intervention priority queues, next best action recommendations. The document explicitly distinguishes between **insights** (describe) and **improvement plans** (prescribe) — an important product philosophy.

### 6. Industry-Adaptive Discovery Framework
The system automatically detects industry type and switches between BANT (Real Estate, Education, Finance, B2C high-ticket), SPIN (SaaS, enterprise software, consulting), or Hybrid — giving rep-specific discovery scoring adapted to context. This is more sophisticated than fixed scoring templates.

### 7. Cross-Team Shared Learning / Dynamic LMS
The Best Practice Library aggregates real interaction patterns, not theory, and routes personalized examples to reps based on their specific gap patterns (not random). This creates compounding organizational intelligence and is described as the "most defensible long-term moat."

### 8. Revenue-Layer KPIs Give Executive-Level Value
The KPI hierarchy moves from diagnostic (talk-listen ratio, sentiment) up through account intelligence (stakeholder coverage, commitment credibility) to revenue business KPIs (forecast confidence, stage integrity, revenue at risk). This positioning makes Tasknova relevant to CROs and boards, not just sales managers.

### 9. Coaching-First Positioning
Explicitly designed to avoid "surveillance system" perception. The product positions as "Grammarly for sales, not CCTV for calls." Reps see their own transcripts; managers see flagged clips. Positive reinforcement is a design requirement. This is important for adoption in high-turnover environments.

### 10. Well-Sequenced Build Roadmap
The module dependency tree, phased ship plan, and clear MVP boundary are well-thought-out. The document distinguishes what can ship independently (call analysis, email analysis, manager dashboard) from what requires foundational layers first (dynamic LMS, predictive models) — preventing over-engineering at launch.

### 11. Deep Post-Sale & Continuity Value Story (New in v3)
v3 adds dedicated anecdotes proving continuity, retention, account reassignment, and revenue truth value (NorthBridge ERP, CarePulse Health, Axis Prime Realty, FinCore Advisory). This makes the full-lifecycle value proposition concrete rather than aspirational, with specific company stories showing handoff quality analysis, renewal risk detection, and account memory across rep changes.

### 12. Comprehensive ROI & Business Value Framework (New in v3)
Section 11 expanded from 8 to 14 questions with detailed sub-sections. Now covers: rep value (4 categories), manager value (7 mechanisms + 7 decision types), CS/onboarding/support value (6 areas), RevOps value (6 areas), revenue uplift by category, cost savings (6 types), continuity value (5 areas), cultural impact (6 transformations), leadership visibility (5 categories), forecasting improvement (5 mechanisms), strategy de-risking (6 mechanisms), and long-term strategic value (5 assets). This makes Tasknova sellable at multiple organizational levels.

### 13. Derived Intelligence Governance (New in v3)
Section 7 now explicitly addresses governance of derived intelligence (account memory, stakeholder profiles, risk scores, continuity summaries) — not just raw recordings. This is a meaningful compliance maturity step that most competitors haven't addressed.

---

## Weaknesses

### 1. Heavy Module Dependency Chain
Many of the most valuable modules (Forecast Confidence Engine, Account Risk Scoring, Renewal Risk Intelligence, Dynamic LMS) cannot ship meaningfully until foundational layers — especially Account Memory, Revenue Signal Engine, and Full Journey Continuity — are stable and populated. This creates a cold-start problem: the platform's full value isn't immediately visible to new customers.

### 2. Post-Sale CS Intelligence is Phase 2, Not MVP
The strongest differentiator (full lifecycle vs. Gong's pre-sale focus) is largely Phase 2+. The MVP may look similar to existing call analytics tools until the post-sale intelligence layers arrive.

### 3. CRM Integration is CSV-First in MVP
Phase 1 CRM integration is manual CSV imports (leads, accounts, pipeline stages, lifecycle mapping). Real API sync with HubSpot, Zoho, Salesforce is Phase 2. For customers with active CRMs, this means manual data maintenance during the critical early adoption period, which reduces stickiness.

### 4. ASR Accuracy Targets Are Ambitious
WER < 18% for Hindi-English code-switching, < 12% for pure English (Indian accent), < 15% for pure Hindi are good targets — but real-world background noise, overlapping speech, and regional accent variance in Indian BPO environments will frequently miss these thresholds. The mitigations (WER threshold acceptance, human QA sampling) are correct but add operational overhead.

### 5. Non-Hindi Indian Language Support Deferred
Hindi-English is Phase 1. Marathi, Gujarati, and other regional language fine-tuning is Phase 2. Indian SMBs in Gujarat or Maharashtra may have significant Marathi/Gujarati code-switching not adequately handled at launch.

### 6. Sections 5 & 6 Removed — UX/UI and GTM Gaps
v3 removes Section 5 (UX/UI, Sprint Planning & Engineering) and Section 6 (GTM & Pricing) entirely. The 12-screen MVP spec, route map, design rules, and product surfaces from v1 are no longer in the Bible. There is still no pricing tier structure, competitive pricing comparison, or GTM playbook. These are meaningful gaps for engineering and commercial teams.

### 7. Strategic Intelligence Layer is Highly Aspirational
Phase 3 features — "Miro Fish and swarmagent simulation logic," scenario simulation, Company-Wide Knowledge Graph, predictive churn models — are described at a concept level with no technical grounding. The gap between MVP and Phase 3 is large enough to represent a separate product requiring fundamentally different engineering.

### 8. Adoption / Change Management Risk is a Real Barrier
The document explicitly acknowledges manager resistance (feel threatened), rep fear (surveillance), and the need for a coaching-first narrative. These are implementation failure modes that the technology alone cannot solve. This is especially acute in BPO environments where agents are measured harshly and managers are accustomed to manual QA.

### 9. Third-Party Platform Dependency Risk
Exotel/Twilio downtime impacts ingestion. The mitigation (fallback queue + status alerts) is sensible but any outage means data gaps in the account memory — degrading the platform's core value proposition. A fallback recording mechanism is not mentioned.

### 10. No CRM — Integration-Only Model
Tasknova explicitly says it is "NOT a CRM" and integrates rather than replaces. This is the right positioning, but it means Tasknova's intelligence quality is permanently dependent on the client's CRM data quality. The document acknowledges "tools break down when underlying CRM data is poor" as an industry gap — but doesn't fully resolve how Tasknova compensates for this in practice.

### 11. No UX/Screen Specification in v3
The removal of Section 5 means the Bible no longer contains MVP screen definitions, route maps, or UX design rules. Engineering teams will need a separate UX specification document. This could create misalignment between product vision and implementation.

---

## Competitive Positioning (Implied)

| Dimension | Tasknova Claim | Key Gap vs. Incumbents |
|---|---|---|
| Full lifecycle | Pre-sale + post-sale (Phase 2) | Gong/Outreach are pre-sale only |
| Multi-channel | 9+ channels Day 1 | Most tools are call-only |
| India fit | Hindi/Hinglish ASR, Exotel, TRAI | Western tools have poor India accuracy |
| Price point | SMB accessible (pricing not specified in v3) | Gong = $50K platform fee + $250+/user |
| Intelligence depth | Account memory + behavioral handling | Gong scores calls; doesn't learn how to handle the account |
| Action orientation | Weekly improvement plans, next best action | Analytics-first tools don't close the action loop |
| Derived intelligence governance | Explicit governance for account memory, profiles, risk scores | Most tools only govern raw recordings |
| Post-sale continuity | Handoff quality, promise vs delivery, renewal risk | Competitors don't track the full journey |

---

## Summary Verdict

**The model is architecturally well-designed and meaningfully differentiated**, particularly in full-journey coverage, behavioral memory, India market depth, and the link from interaction signals to revenue intelligence. The four-layer intelligence architecture is coherent and defensible.

v3 significantly strengthens the value articulation with comprehensive ROI framing (Q74–Q87), four new real-world stories proving continuity/retention/account-reassignment/revenue-truth value, complete 10-industry fit profiles, expanded coaching workflows, and derived intelligence governance. The business case is now much more concrete and multi-level.

The core risks remain **execution sequence** (most differentiated features are Phase 2+), **CRM dependency** (CSV-only in MVP), and the **removal of UX/GTM sections** which leaves engineering and commercial gaps unaddressed in the Bible. The cold-start problem — where the platform looks like basic call analytics until foundational layers are populated — will be the main sales/adoption challenge in early months.

If the team executes Phases 1 and 2 cleanly, Tasknova can occupy a genuine white space: a full-lifecycle revenue intelligence platform built natively for India and SMB/mid-market pricing, at a time when the market leaders are consolidating at the enterprise end and pricing out smaller companies.

---

## What Changed: v1 (260 pages) → v3 (300 pages)

| Area | v1 | v3 |
|---|---|---|
| Total pages | 260 | 300 |
| Total questions | ~81 | ~87 |
| Section 4 (Coaching) | Q35–Q42 | Q35–Q45 (added Q43 evidence, Q44 manager workflow, Q45 rep workflow) |
| Sections 5 & 6 | Present (UX/UI, GTM/Pricing) | Removed entirely |
| Section 7 | p.194–203 | p.139–171 (expanded, added derived intelligence governance) |
| Section 8 | p.204–217, 8.1–8.5 | p.171–196, 8.1–8.8 (added USPs, user love, company-size impact) |
| Section 9 | 3 stories | 7 stories (added NorthBridge, CarePulse, Axis Prime, FinCore) |
| Section 10 | Partially documented | All 10 industries fully documented |
| Section 11 | Q74–Q81 | Q74–Q87 with A–G sub-sections per question |
| MVP features | 12 | 15 (added Company/Stakeholder Profiles, Role-Based Access, Redaction, Trust Signals) |
