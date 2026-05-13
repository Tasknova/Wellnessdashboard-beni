# Tasknova MVP — Public Dataset Catalog for Revenue Intelligence

> Research date: April 2026
> Purpose: Map publicly available datasets to the 5 core MVP capabilities for a B2B SaaS Revenue Intelligence platform

---

## Overview: MVP Capabilities vs. Dataset Coverage

| # | MVP Capability | Datasets Found | Coverage Quality |
|---|---|---|---|
| 1 | Sales call/conversation analysis | 5 datasets | Strong — real + synthetic transcripts available |
| 2 | Deal/pipeline intelligence | 4 datasets | Moderate — CRM pipeline data exists but small |
| 3 | Customer sentiment & churn signals | 4 datasets | Strong — multiple SaaS-relevant churn datasets |
| 4 | Email/messaging analysis | 4 datasets | Moderate — mostly synthetic or repurposed |
| 5 | Account health & lifecycle | 2 datasets | Moderate — SaaS subscription lifecycle available |

---

## Capability 1: Sales Call / Conversation Analysis

**KPIs demonstrated:** Rep performance scoring, talk-listen ratio, discovery quality, objection handling, next-step clarity

---

### 1A. DeepMostInnovations/saas-sales-conversations

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/DeepMostInnovations/saas-sales-conversations) |
| **License** | MIT (commercially usable) |
| **Size** | Train split (exact row count varies; ~1K+ conversations with 468-dim embeddings) |
| **Format** | Parquet |

**Schema / Key Fields:**
- `company_id`, `company_name` — Company identifiers
- `product_name`, `product_type` — SaaS product metadata
- `conversation_id` — Unique conversation ID
- `scenario` — Sales scenario type
- `conversation` — Full conversation transcript
- `full_text` — Complete text
- `outcome` (Int64) — Binary sale outcome (0/1)
- `conversation_length` (Int64) — Length of conversation
- `customer_engagement` (Float64) — Engagement metric
- `sales_effectiveness` (Float64) — Effectiveness score
- `probability_trajectory` — How deal probability changed during the call
- `conversation_style` — Style classification
- `conversation_flow` — Flow pattern
- `communication_channel` — Channel used
- `embedding_0` through `embedding_467` — 468-dim pre-computed embeddings

**Tasknova Capabilities Proven:**
- Rep performance scoring (via `sales_effectiveness`)
- Discovery quality (via `conversation_flow`, `conversation_style`)
- Win/loss outcome prediction (via `outcome`, `probability_trajectory`)
- Customer engagement scoring (via `customer_engagement`)

**Limitations:**
- Synthetic data (generated from RL agent research paper)
- SaaS-specific but not real conversations
- No speaker-level turn annotations (can't directly compute talk-listen ratio)
- No explicit objection-handling labels

---

### 1B. AIxBlock/92k-real-world-call-center-scripts-english (CallCenterEN)

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english) |
| **License** | CC-BY-NC-4.0 (non-commercial only) |
| **Size** | 91,706 transcripts (~10,448 audio hours), 1.4 GB |
| **Format** | JSON files in ZIP archives |

**Schema / Key Fields:**
- Full transcript text (redacted for 42+ PII types)
- Word-level timestamps
- ASR confidence scores (WER: 96.1%)
- Domain/industry categorization
- Call type (inbound vs outbound, 91.3% inbound / 8.7% outbound)
- Accent labels (Indian, American, Filipino English)

**Tasknova Capabilities Proven:**
- Talk-listen ratio (word-level timestamps enable agent vs. customer time computation)
- Call structure analysis (turn patterns, call length distribution)
- Rep performance patterns (across domains and accent types)
- Intent detection and objection handling (from transcript text)

**Limitations:**
- **Non-commercial license** — cannot be used directly in a commercial product; research/prototyping only
- Primarily customer service, not pure sales conversations
- No explicit labels for objection handling, discovery quality, or next steps
- Requires NLP pipeline to extract sales-relevant features

---

### 1C. goendalf666/sales-conversations

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/goendalf666/sales-conversations) |
| **License** | Not explicitly stated (check before commercial use) |
| **Size** | 3,410 conversations |
| **Format** | Parquet (20 columns) |

**Schema / Key Fields:**
- Columns 0-15: Alternating customer and salesman conversation turns (text)
- Column 16-17: Category fields (16 unique values each)
- Column 18-19: Category fields (3 unique values each)

**Tasknova Capabilities Proven:**
- Multi-turn conversation analysis
- Customer-salesman dialogue pattern recognition
- Talk ratio (turn-level, not time-level)
- Sales technique classification via category labels

**Limitations:**
- Relatively small (3.4K conversations)
- License unclear — may not be commercially usable
- No outcome labels (won/lost)
- No engagement or effectiveness metrics
- Turn-based structure without timing information

---

### 1D. gwenshap/sales-transcripts

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/gwenshap/sales-transcripts) |
| **License** | Not specified |
| **Size** | Small (simulated conversations for 5 companies) |
| **Format** | Chunked and embedded (OpenAI text-embedding-3-small) |

**Schema / Key Fields:**
- Sales conversation text chunks
- Pre-computed embeddings (OpenAI text-embedding-3-small)
- Company identifiers (5 fictional companies)

**Tasknova Capabilities Proven:**
- Vector similarity search over sales conversations
- Conversation retrieval and semantic search
- RAG-ready format for building sales assistants

**Limitations:**
- Very small dataset (5 companies)
- Synthetic/simulated data
- No labels, outcomes, or performance metrics
- Primarily designed for RAG demos, not ML training

---

### 1E. CyberAgentAILab/salestalk-dataset

| Field | Detail |
|---|---|
| **Source** | [GitHub](https://github.com/CyberAgentAILab/salestalk-dataset) |
| **License** | Research use |
| **Size** | Multi-turn dialogues with utterance-level annotations |
| **Format** | JSON Lines |

**Schema / Key Fields:**
- Dialogue-level evaluation labels
- Utterance-level willingness annotations
- Sales dialogue success indicators
- Fine-grained temporal willingness tracking

**Tasknova Capabilities Proven:**
- Objection handling analysis (willingness evolution)
- Discovery quality (dialogue structure)
- Sales technique effectiveness (dialogue-level outcomes)

**Limitations:**
- **All utterances are in Japanese** — requires translation for English MVP
- Research license — commercial use may be restricted
- Domain-specific to Japanese retail sales context

---

## Capability 2: Deal / Pipeline Intelligence

**KPIs demonstrated:** Deal stage progression, win/loss prediction, forecast confidence, time-to-close

---

### 2A. CRM Sales Predictive Analytics (agungpambudi)

| Field | Detail |
|---|---|
| **Source** | [Kaggle](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics) |
| **License** | CC0 Public Domain (fully commercially usable) |
| **Size** | ~146 KB (4 CSV files) |
| **Format** | CSV |

**Schema / Key Fields:**

**accounts.csv:**
- `account` — Company name
- `sector` — Industry
- `year_established` — Year established
- `revenue` — Annual revenue (millions USD)
- `employees` — Number of employees
- `office_location` — Headquarters
- `subsidiary_of` — Parent company

**products.csv:**
- `product` — Product name
- `series` — Product series
- `sales_price` — Suggested retail price

**sales_teams.csv:**
- `sales_agent` — Sales agent name
- `manager` — Sales manager
- `regional_office` — Regional office

**sales_pipeline.csv:**
- `opportunity_id` — Unique deal identifier
- `sales_agent` — Sales agent name
- `product` — Product name
- `account` — Company name
- `deal_stage` — Pipeline stage (Prospecting > Engaging > Won / Lost)
- `engage_date` — Date "Engaging" stage started
- `close_date` — Date deal was Won or Lost
- `close_value` — Revenue from the deal

**Tasknova Capabilities Proven:**
- Deal stage progression (Prospecting > Engaging > Won/Lost)
- Win/loss prediction (outcome labels + deal features)
- Time-to-close analysis (engage_date to close_date)
- Rep performance comparison (sales_agent + outcomes)
- Revenue forecasting (close_value + time series)
- Account intelligence (firmographic data in accounts.csv)

**Limitations:**
- Computer hardware company, not SaaS (no recurring revenue)
- Small dataset — will need augmentation for robust ML
- Simple 3-stage pipeline (real SaaS pipelines have 5-8 stages)
- No conversation or engagement signals tied to deals

---

### 2B. Sales Pipeline Conversion at a SaaS Startup (soumyadipmondal)

| Field | Detail |
|---|---|
| **Source** | [Kaggle](https://www.kaggle.com/datasets/soumyadipmondal/sales-pipeline-conversion-at-a-saas-startup) |
| **License** | Unknown |
| **Size** | ~78,000 rows, ~986 KB |
| **Format** | CSV in ZIP |

**Schema / Key Fields:**
- Client city
- Opportunity size
- Client revenue
- Sales medium
- Sales velocity (target variable = time-to-close)

**Tasknova Capabilities Proven:**
- Time-to-close prediction (sales velocity)
- Deal sizing / opportunity scoring
- Sales channel effectiveness (sales medium)
- Pipeline conversion modeling

**Limitations:**
- License unknown — commercial viability uncertain
- Limited schema information publicly available
- No deal stage progression data
- No win/loss labels (focused on velocity/time-to-close)

---

### 2C. CRM + Sales + Opportunities (innocentmfa)

| Field | Detail |
|---|---|
| **Source** | [Kaggle](https://www.kaggle.com/datasets/innocentmfa/crm-sales-opportunities) |
| **License** | Apache 2.0 (commercially usable) |
| **Size** | ~146 KB |
| **Format** | CSV in ZIP |

**Schema / Key Fields:**
- Customer demographics and firmographics
- Sales activities
- Opportunity data (deal size, stage, probability)
- Product/service information
- Sales team performance metrics
- Time-series sales data

**Tasknova Capabilities Proven:**
- Deal stage tracking with probability
- Win/loss analysis
- Rep/team performance comparison
- Revenue forecasting

**Limitations:**
- Small dataset
- Exact column names require download to inspect
- Not SaaS-specific

---

### 2D. Amazon AWS SaaS Sales Dataset (nnthanh101)

| Field | Detail |
|---|---|
| **Source** | [Kaggle](https://www.kaggle.com/datasets/nnthanh101/aws-saas-sales) |
| **License** | GNU Free Documentation License 1.3 |
| **Size** | 9,994 transactions |
| **Format** | CSV |

**Schema / Key Fields:**
- `Row ID` — Unique transaction identifier
- `Order ID` — Order identifier
- `Order Date` — Order placement date
- `Contact Name` — Person who placed the order
- `Country`, `City`, `Region`, `Subregion` — Geographic data
- `Customer` — Company name
- `Customer ID` — Customer identifier
- `Industry` — Customer industry
- `Segment` — Customer segment (SMB, Strategic, Enterprise)
- `Product` — SaaS product ordered
- `License` — License key
- `Sales` — Total sales amount
- `Quantity` — Items in transaction
- `Discount` — Discount applied
- `Profit` — Profit from transaction

**Tasknova Capabilities Proven:**
- B2B SaaS revenue analysis by segment (SMB/Strategic/Enterprise)
- Customer segmentation and deal sizing
- Discount impact on profitability
- Geographic pipeline distribution
- Industry vertical analysis

**Limitations:**
- Fictitious data (not real transactions)
- No deal stages or pipeline progression
- No time-to-close or win/loss labels
- Transaction-level, not opportunity-level
- GNU FDL license is unusual for datasets — may have copyleft implications

---

## Capability 3: Customer Sentiment & Churn Signals

**KPIs demonstrated:** Sentiment from interactions, renewal risk, expansion readiness, churn prediction

---

### 3A. SaaS Subscription & Churn Analytics Dataset (rivalytics)

| Field | Detail |
|---|---|
| **Source** | [Kaggle](https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset) |
| **License** | MIT (commercially usable) |
| **Size** | ~600 KB (5 CSV files) |
| **Format** | CSV |

**Schema / Key Files:**

**accounts.csv** — Customer metadata (company info, creation dates, industry)

**subscriptions.csv** — Subscription lifecycles and revenue (plan types, start/end dates, MRR, pricing tiers)

**feature_usage.csv** — Daily product interaction logs (feature names, usage dates, interaction counts)

**support_tickets.csv** — Support activity and satisfaction scores (ticket IDs, resolution dates, CSAT ratings)

**churn_events.csv** — Churn dates, reasons, and refund behaviors (churn reasons, refund amounts, reactivation flags)

**Tasknova Capabilities Proven:**
- Churn prediction (churn_events with reasons and timing)
- Renewal risk scoring (subscription lifecycle + support patterns)
- Expansion readiness (feature adoption + MRR growth patterns)
- Customer health scoring (multi-signal: usage + support + revenue)
- Trial-to-paid conversion analysis
- MRR trends and cohort analysis

**Limitations:**
- Simulated data (fictional company "RavenStack")
- Exact column names require download to verify
- No conversation or sentiment text data
- No NPS or qualitative feedback fields

---

### 3B. IBM Telco Customer Churn (blastchar)

| Field | Detail |
|---|---|
| **Source** | [Kaggle](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) |
| **License** | Community Data License Agreement (CDLA) |
| **Size** | 7,043 customers, 21 columns |
| **Format** | CSV |

**Schema / Key Fields:**
- `customerID` — Unique customer ID
- `gender`, `SeniorCitizen`, `Partner`, `Dependents` — Demographics
- `tenure` — Months as customer
- `PhoneService`, `MultipleLines` — Phone services
- `InternetService`, `OnlineSecurity`, `OnlineBackup`, `DeviceProtection`, `TechSupport` — Internet services
- `StreamingTV`, `StreamingMovies` — Streaming services
- `Contract` — Contract type (month-to-month, one year, two year)
- `PaperlessBilling` — Billing preference
- `PaymentMethod` — Payment method
- `MonthlyCharges`, `TotalCharges` — Billing amounts
- `Churn` — Target label (Yes/No)

**Tasknova Capabilities Proven:**
- Churn prediction baseline model
- Contract type impact on retention
- Service adoption vs. churn correlation
- Tenure-based renewal risk modeling
- Payment behavior as churn signal

**Limitations:**
- Telecom, not SaaS (no MRR/ARR, no feature usage)
- No text/sentiment data
- No interaction history or engagement signals
- Single-point-in-time snapshot (no temporal progression)

---

### 3C. Predictive Analytics for Customer Churn (safrin03)

| Field | Detail |
|---|---|
| **Source** | [Kaggle](https://www.kaggle.com/datasets/safrin03/predictive-analytics-for-customer-churn-dataset) |
| **License** | CC0 Public Domain |
| **Size** | Subscription service case study |
| **Format** | CSV |

**Schema / Key Fields:**
- Subscription type
- Payment method
- Customer support interactions
- Viewing/usage preferences
- Churn label
- Demographic attributes

**Tasknova Capabilities Proven:**
- Churn prediction with support interaction features
- Subscription-based renewal modeling
- Support ticket volume as churn signal

**Limitations:**
- Generic subscription service, not B2B SaaS
- Limited schema detail publicly available
- No revenue or MRR data

---

### 3D. syncora/customer_support_conversations_dataset

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/syncora/customer_support_conversations_dataset) |
| **License** | Check HuggingFace page |
| **Size** | Synthetic conversations |
| **Format** | Parquet |

**Schema / Key Fields:**
- Customer support conversation text
- Sentiment classification labels
- Emotion and intent annotations
- Empathy/tone metrics
- Turnaround time indicators

**Tasknova Capabilities Proven:**
- Sentiment classification from support interactions
- Intent detection (complaint, inquiry, request)
- Tone analysis (empathy, frustration)
- Support quality as churn signal proxy

**Limitations:**
- Synthetic data
- Support-focused, not sales-focused
- Limited schema documentation

---

## Capability 4: Email / Messaging Analysis

**KPIs demonstrated:** Sales email effectiveness, follow-up patterns, response rates, email intent

---

### 4A. Enron Email Dataset

| Field | Detail |
|---|---|
| **Source** | [Kaggle](https://www.kaggle.com/datasets/wcukierski/enron-email-dataset), [CMU](https://www.cs.cmu.edu/~enron/), [Library of Congress](https://www.loc.gov/item/2018487913/) |
| **License** | Public domain (released by FERC during investigation) |
| **Size** | ~500,000 emails from 158 employees |
| **Format** | TXT / CSV |

**Schema / Key Fields:**
- Full email headers (From, To, CC, BCC, Date, Subject)
- Email body text
- Thread/reply chains
- Timestamps
- Organizational roles of senders/recipients

**Tasknova Capabilities Proven:**
- Email communication pattern analysis
- Response time and follow-up cadence
- Thread depth and engagement tracking
- Email intent classification (NLP)
- Network/relationship mapping between contacts
- Email volume and timing patterns

**Limitations:**
- Energy company (2001), not SaaS — domain vocabulary differs
- No labels for email effectiveness or conversion
- Some PII concerns (though publicly released)
- No open/click/reply rate metrics
- Dated communication patterns (pre-modern sales tools)

---

### 4B. marketeam/Marketing-Emails

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/marketeam/Marketing-Emails) |
| **License** | MIT (commercially usable) |
| **Size** | 16,440 emails, 32.7 MB |
| **Format** | Parquet (CSV auto-converted) |

**Schema / Key Fields:**
- `split` — Data partition (train)
- `0` — Full email content (subject + body, 1.1K-3.26K chars each)

**Content Characteristics:**
- Marketing emails with Subject lines and bodies
- Promotional framing, CTAs, persuasive rhetoric
- B2B marketing communication patterns
- 10K+ artificial personas
- Campaign performance discussions, audience engagement, strategic recommendations

**Tasknova Capabilities Proven:**
- Sales email template analysis
- CTA structure and persuasive rhetoric patterns
- Email tone and style classification
- Marketing email effectiveness benchmarking
- Email content generation training

**Limitations:**
- Fully synthetic (generative model output)
- Marketing emails, not sales prospecting emails
- No response/effectiveness metrics (open rates, reply rates)
- Only 2 columns — no metadata or labels
- No threading or follow-up sequences

---

### 4C. sidhq/email-thread-summary (EmailSum)

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/sidhq/email-thread-summary) |
| **License** | Partially restricted (Avocado corpus requires LDC license) |
| **Size** | 2,549 labeled email threads + 8,594 unlabeled threads |
| **Format** | JSON |

**Schema / Key Fields:**
- Email threads (3-10 emails per thread)
- Short summaries (<30 words)
- Long summaries (<100 words)
- Topic classifications

**Tasknova Capabilities Proven:**
- Email thread summarization (account memory feature)
- Multi-turn email conversation understanding
- Topic extraction from email sequences
- Follow-up pattern analysis

**Limitations:**
- Requires separate access to Avocado corpus (LDC license, paid)
- Not sales-specific email threads
- Summaries only — no effectiveness labels
- Small labeled set (2.5K threads)

---

### 4D. emailmarketingdataset/open-email-marketing-dataset

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/emailmarketingdataset/open-email-marketing-dataset) |
| **License** | MIT / CC BY 4.0 (commercially usable) |
| **Size** | 1,000 Q&A pairs |
| **Format** | JSONL |

**Schema / Key Fields:**
- `question` — Question about email marketing, lead gen, or related topic
- `answer` — Detailed B2B answer
- `keywords` — LSI keyword list
- `source_url` — Canonical source URL

**Tasknova Capabilities Proven:**
- Email marketing best practices knowledge base
- Lead generation strategy reference
- Cold email compliance guidance (GDPR, CAN-SPAM)
- RAG knowledge source for email coaching

**Limitations:**
- Q&A format, not actual emails
- Not training data for email analysis models
- Small (1K pairs)
- Better suited for RAG/knowledge base than ML training

---

## Capability 5: Account Health & Lifecycle

**KPIs demonstrated:** Lead-to-close journey, onboarding success, renewal tracking, expansion signals

---

### 5A. SaaS Subscription & Churn Analytics Dataset (rivalytics)

*(Same as 3A above — dual-use dataset)*

| Field | Detail |
|---|---|
| **Source** | [Kaggle](https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset) |
| **License** | MIT (commercially usable) |
| **Size** | 5 CSV files, ~600 KB |

**Lifecycle Coverage:**
- `accounts.csv` — Account creation and metadata (onboarding start)
- `subscriptions.csv` — Subscription lifecycle (trial > paid > upgrade > downgrade > churn)
- `feature_usage.csv` — Daily product engagement (adoption and stickiness)
- `support_tickets.csv` — Support health (resolution quality, satisfaction)
- `churn_events.csv` — End-of-lifecycle (churn reasons, reactivation)

**Tasknova Capabilities Proven:**
- Full account lifecycle tracking (creation > subscription > usage > support > churn/renewal)
- Health score computation (multi-signal: usage + support + revenue)
- Expansion readiness (feature adoption patterns)
- Onboarding success metrics (time-to-first-value via feature_usage)
- Cohort-based lifecycle analysis

**Limitations:**
- No lead/prospect stage (starts at account creation)
- Simulated data
- No sales conversation or email data tied to accounts
- Missing NPS/CSAT survey data

---

### 5B. Lead Scoring Dataset (amritachatterjee09)

| Field | Detail |
|---|---|
| **Source** | [Kaggle](https://www.kaggle.com/datasets/amritachatterjee09/lead-scoring-dataset) |
| **License** | Unknown |
| **Size** | ~420 KB |
| **Format** | CSV |

**Schema / Key Fields:**
- `Prospect ID` — Unique customer identifier
- `Lead Number` — Lead identifier
- `Lead Origin` — How lead was identified (API, Landing Page, etc.)
- `Lead Source` — Source (Google, Organic, Olark Chat, etc.)
- `Do Not Email`, `Do Not Call` — Contact preferences
- `Converted` — Target variable (binary conversion)
- `TotalVisits` — Website visits
- `Total Time Spent on Website` — Session duration
- `Page Views Per Visit` — Engagement depth
- `Last Activity` — Last action (Email Opened, Chat, etc.)
- `Country`, `City` — Geographic data
- `Specialization` — Industry/domain
- `Current Occupation` — Employment status
- `Tags` — Lead status tags
- `Lead Quality` — Quality assessment
- `Lead Profile` — Profile-based lead level
- `Asymmetric Activity Index` — Activity-based score
- Various marketing channel indicators (Search, Magazine, Digital Ad, Recommendations)

**Tasknova Capabilities Proven:**
- Lead scoring and qualification
- Lead source attribution
- Website engagement as buying signal
- Lead-to-conversion funnel analysis
- Multi-channel marketing attribution

**Limitations:**
- Education company context (not B2B SaaS)
- License unknown
- No post-conversion lifecycle data (no onboarding, renewal, expansion)
- No revenue or deal value data
- Focused on top-of-funnel only

---

## Supplementary Datasets (Cross-Capability)

### S1. stanfordnlp/craigslist_bargains (Negotiation Dialogues)

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/stanfordnlp/craigslist_bargains) |
| **License** | Unknown |
| **Size** | 6,682 dialogues (5,247 train / 597 val / 838 test) |
| **Capability** | Objection handling, negotiation pattern analysis |
| **Limitation** | Consumer negotiation (not B2B sales); license unclear |

### S2. Samsung/samsum (Dialogue Summarization)

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/Samsung/samsum) |
| **License** | CC BY-NC-ND 4.0 (non-commercial) |
| **Size** | 16,369 conversations |
| **Capability** | Conversation summarization for meeting/call notes |
| **Limitation** | Non-commercial license; general conversations, not sales |

### S3. knkarthick/AMI (Meeting Summarization)

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/knkarthick/AMI) |
| **License** | CC BY 4.0 (commercially usable) |
| **Size** | 279 meeting dialogues |
| **Capability** | Meeting transcript summarization, action item extraction |
| **Limitation** | Small dataset; general meetings, not sales calls |

### S4. Salesforce/dialogstudio (Dialogue Collection)

| Field | Detail |
|---|---|
| **Source** | [HuggingFace](https://huggingface.co/datasets/Salesforce/dialogstudio) |
| **License** | Mixed (per sub-dataset) |
| **Size** | Large collection across multiple dialogue categories |
| **Capability** | Task-oriented dialogue, conversational recommendation, NLU |
| **Limitation** | Not sales-specific; requires sub-dataset license checking |

### S5. SQL CRM Example Data (mexwell)

| Field | Detail |
|---|---|
| **Source** | [Kaggle](https://www.kaggle.com/datasets/mexwell/sql-crm-example-data) |
| **License** | Other (check dataset) |
| **Size** | ~415 KB |
| **Capability** | CRM data modeling practice (accounts, contacts, deals) |
| **Limitation** | Fake data for SQL practice; very small |

---

## Recommended MVP Dataset Stack

Based on license compatibility, relevance to B2B SaaS, and data quality:

### Tier 1 — Immediate Use (Download & Build)

| Priority | Dataset | License | Capability | Action |
|---|---|---|---|---|
| 1 | **CRM Sales Predictive Analytics** (Kaggle/agungpambudi) | CC0 Public Domain | Deal pipeline, win/loss, rep performance | Build deal stage progression and forecast confidence models |
| 2 | **DeepMostInnovations/saas-sales-conversations** | MIT | Sales call scoring, engagement, outcomes | Train conversation effectiveness and win prediction models |
| 3 | **SaaS Subscription & Churn Analytics** (Kaggle/rivalytics) | MIT | Churn, renewal, account health, lifecycle | Build customer health score and churn prediction |
| 4 | **marketeam/Marketing-Emails** | MIT | Email template analysis, CTA patterns | Train email effectiveness classifier |
| 5 | **Enron Email Dataset** | Public Domain | Email patterns, threading, follow-ups | Build email cadence and response analysis pipeline |
| 6 | **IBM Telco Customer Churn** | CDLA | Churn baseline model | Train baseline churn prediction (transfer to SaaS) |

### Tier 2 — Use with Caution (License Restrictions)

| Dataset | License Issue | Use Case |
|---|---|---|
| **CallCenterEN (92K transcripts)** | CC-BY-NC-4.0 | Prototype-only: call analysis pipeline, talk-listen ratio |
| **Sales Pipeline Conversion (SaaS Startup)** | Unknown | Prototype-only: time-to-close prediction |
| **Lead Scoring Dataset** | Unknown | Prototype-only: lead qualification models |

### Tier 3 — Augment with Synthetic Data

| Gap | Mitigation |
|---|---|
| No labeled objection-handling dataset in English | Use LLM to label objection segments in CallCenterEN or SaaS sales conversations |
| No multi-stage SaaS pipeline with 5-8 stages | Generate synthetic pipeline data using CRM Predictive Analytics as template |
| No email open/reply/conversion metrics | Simulate email engagement metrics on top of Marketing-Emails |
| No NPS/CSAT survey data tied to accounts | Add synthetic NPS scores to SaaS Subscription & Churn dataset |
| No conversation-to-deal linking | Create synthetic join keys between sales conversations and pipeline datasets |

---

## Key Gaps — No Public Dataset Exists

| Gap | Why It Matters | Workaround |
|---|---|---|
| **Real B2B SaaS deal pipeline with evidence-backed stage progression** | Core to forecast confidence and deal momentum scoring | Synthetic generation or collect from early customers |
| **Sales emails with open/reply/conversion metrics** | Required for email effectiveness scoring | Simulate metrics; collect from customer integrations |
| **Conversation-to-CRM-deal linked data** | Needed to correlate call quality with deal outcomes | Build linkage in Tasknova's own data model |
| **Stakeholder/org-chart data** | Required for multi-threading and champion tracking | Must come from customer CRM imports |
| **Rep coaching outcome data over time** | Needed for Performance Improvement Engine | Must be collected longitudinally from users |
| **Real SaaS renewal/expansion revenue with interaction history** | Full lifecycle intelligence requires linked data | Use SaaS Subscription dataset as structure; enrich with synthetic interaction data |

---

## Sources

- [DeepMostInnovations/saas-sales-conversations](https://huggingface.co/datasets/DeepMostInnovations/saas-sales-conversations)
- [AIxBlock/92k-real-world-call-center-scripts-english](https://huggingface.co/datasets/AIxBlock/92k-real-world-call-center-scripts-english)
- [goendalf666/sales-conversations](https://huggingface.co/datasets/goendalf666/sales-conversations)
- [gwenshap/sales-transcripts](https://huggingface.co/datasets/gwenshap/sales-transcripts)
- [CyberAgentAILab/salestalk-dataset](https://github.com/CyberAgentAILab/salestalk-dataset)
- [CRM Sales Predictive Analytics — Kaggle](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics)
- [Sales Pipeline Conversion at a SaaS Startup — Kaggle](https://www.kaggle.com/datasets/soumyadipmondal/sales-pipeline-conversion-at-a-saas-startup)
- [CRM + Sales + Opportunities — Kaggle](https://www.kaggle.com/datasets/innocentmfa/crm-sales-opportunities)
- [Amazon AWS SaaS Sales — Kaggle](https://www.kaggle.com/datasets/nnthanh101/aws-saas-sales)
- [SaaS Subscription & Churn Analytics — Kaggle](https://www.kaggle.com/datasets/rivalytics/saas-subscription-and-churn-analytics-dataset)
- [IBM Telco Customer Churn — Kaggle](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
- [Predictive Analytics for Customer Churn — Kaggle](https://www.kaggle.com/datasets/safrin03/predictive-analytics-for-customer-churn-dataset)
- [syncora/customer_support_conversations_dataset](https://huggingface.co/datasets/syncora/customer_support_conversations_dataset)
- [Enron Email Dataset — Kaggle](https://www.kaggle.com/datasets/wcukierski/enron-email-dataset)
- [marketeam/Marketing-Emails](https://huggingface.co/datasets/marketeam/Marketing-Emails)
- [sidhq/email-thread-summary](https://huggingface.co/datasets/sidhq/email-thread-summary)
- [emailmarketingdataset/open-email-marketing-dataset](https://huggingface.co/datasets/emailmarketingdataset/open-email-marketing-dataset)
- [Lead Scoring Dataset — Kaggle](https://www.kaggle.com/datasets/amritachatterjee09/lead-scoring-dataset)
- [stanfordnlp/craigslist_bargains](https://huggingface.co/datasets/stanfordnlp/craigslist_bargains)
- [Samsung/samsum](https://huggingface.co/datasets/Samsung/samsum)
- [knkarthick/AMI Corpus](https://huggingface.co/datasets/knkarthick/AMI)
- [Salesforce/dialogstudio](https://huggingface.co/datasets/Salesforce/dialogstudio)
- [SQL CRM Example Data — Kaggle](https://www.kaggle.com/datasets/mexwell/sql-crm-example-data)
- [Customer Satisfaction Scores and Behavior Data — Kaggle](https://www.kaggle.com/datasets/salahuddinahmedshuvo/customer-satisfaction-scores-and-behavior-data)
