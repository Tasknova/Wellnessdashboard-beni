# Tasknova — Product Dataset Research

> Research conducted: April 2026
> Purpose: Identify what data is needed to build Tasknova and find publicly available datasets for each category

---

## 1. Data Categories Needed (Mapped from TN Bible Index)

Based on the 4-layer intelligence stack, 22 core intelligence objects, and the technical architecture (Sections 1–3A of the Bible), Tasknova requires data across **8 major categories**:

| # | Data Category | Bible Reference | Why It's Needed |
|---|---|---|---|
| 1 | **Speech/ASR (Hindi-English, Indian accents)** | Sec 2, Q17–Q19 | Whisper fine-tuning for code-switched Indian English, WER <18% target |
| 2 | **Sales Call Transcripts** | Sec 3, Q26 (Sales Diagnostic KPIs) | Talk-listen ratio, objection handling, discovery quality, sentiment scoring |
| 3 | **CRM / Deal Pipeline Data** | Sec 2 Q13, Sec 3A Q26R–W | Forecast confidence, stage progression, win/loss, deal momentum |
| 4 | **Sentiment & NLP Intent Data** | Sec 2 Q17, Sec 3A (A3) | 3-level sentiment model, intent detection, objection identification |
| 5 | **Contact Center / BPO Data** | Sec 3 (CX/Support KPIs), Sec 10 | AHT, FCR, CSAT, escalation markers, agent performance |
| 6 | **Churn / Renewal / Expansion Data** | Sec 3A Q26R (Revenue Intelligence) | Renewal risk, expansion readiness, revenue leakage prediction |
| 7 | **Email & Chat Communication Data** | Sec 2 Q13, Q20 | Email response delay, template performance, chat escalation markers |
| 8 | **Speaker Diarization Data** | Sec 3 (Talk-Listen Ratio) | "Who spoke when" — agent vs. customer segmentation in calls |

---

## 2. Datasets Found

### 2A. Speech / ASR — Hindi-English & Indian Accents

| Dataset | Source | Size | Details |
|---|---|---|---|
| **IndicVoices** | [Hugging Face — ai4bharat/IndicVoices](https://huggingface.co/datasets/ai4bharat/IndicVoices) | 12,000 hours, 22,563 speakers, 22 languages | Natural & spontaneous speech: read (8%), extempore (76%), conversational (15%). Covers 208 Indian districts. Powers IndicASR — first model for all 22 scheduled Indian languages. |
| **IndicVoices-R** | [Hugging Face — ai4bharat/indicvoices_r](https://huggingface.co/datasets/ai4bharat/indicvoices_r) | 1,704 hours, 10,496 speakers | High-quality TTS/ASR dataset derived from IndicVoices across 22 Indian languages. |
| **Hindi Speech Recognition Dataset** | [Hugging Face — ud-nlp/hindi-speech-recognition-dataset](https://huggingface.co/datasets/ud-nlp/hindi-speech-recognition-dataset) | 760 hours, 1,000+ speakers | Telephone dialogues with 95% sentence accuracy. Ideal for Hindi ASR training. |
| **Hindi-English Code-Switching Corpus** | [arXiv:1810.00662](https://arxiv.org/abs/1810.00662) | Research corpus | Specifically built for Hindi-English code-switching ASR research. |
| **VITB-HEBiC Corpus** | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0045790624009030) | 7.5 hours, 137 speakers, 27 Indian states | Bilingual Hindi-English corpus with natural noise, various accents, and code-switching patterns. |
| **Hindi-Marathi Code-Switched Dataset** | [ScienceDirect](https://www.sciencedirect.com/science/article/abs/pii/S0003682X24005590) | 450 hours annotated | Tag-switching, intra-sentential, and inter-sentential patterns. |
| **Indian Emotional Speech Corpus** | [Hugging Face — humyn-labs/Indian-Emotional-Speech-Corpus](https://huggingface.co/datasets/humyn-labs/Indian-Emotional-Speech-Corpus) | Emotional speech data | Useful for sentiment detection from voice in Indian accents. |
| **Indian English Spontaneous Speech** | [Hugging Face — Nexdata](https://huggingface.co/datasets/Nexdata/Indian_English_Spontaneous_Speech_Data) | Spontaneous speech | Indian-accented English for ASR training. |
| **BhasaAnuvaad** | [arXiv:2411.04699](https://arxiv.org/html/2411.04699v2) | 44,400+ hours, 13 languages | Largest Indic-language speech translation dataset. |
| **Whisper Hindi-English Fine-Tuning Research** | [ISCA Interspeech 2025](https://www.isca-archive.org/interspeech_2025/biswas25_interspeech.pdf) | Research paper | Achieved 14% and 28.1% WER reduction on Hindi-English code-mix with fine-tuned Whisper. Directly relevant to Tasknova's ASR pipeline. |

---

### 2B. Sales Call Transcripts & Conversation Intelligence

| Dataset | Source | Size | Details |
|---|---|---|---|
| **TeleSalesCorpus — CallCenterEN** | [EmergentMind](https://www.emergentmind.com/topics/telesalescorpus) | 91,706 transcripts (~10,448 hours) | Real call center transcripts. Inbound (91.3%) + outbound (8.7%). Indian, Filipino, American accents. Structured annotations and metadata. |
| **TeleSalesCorpus — LLM-Simulated** | Same source | 2,000 dialogues | High-fidelity multi-turn sales dialogues: Opening → Business_Analysis → Promotion → UI_Guidance → Objection_Handling → Closing. |
| **Sales Transcripts** | [Hugging Face — gwenshap/sales-transcripts](https://huggingface.co/datasets/gwenshap/sales-transcripts) | Open dataset | Simulated sales conversations for 5 fictional companies. |
| **Sales Conversations** | [Hugging Face — goendalf666/sales-conversations](https://huggingface.co/datasets/goendalf666/sales-conversations) | Open dataset | Sales conversation dataset for NLP analysis. |
| **Call Center Transcripts** | [Kaggle](https://www.kaggle.com/datasets/oleksiymaliovanyy/call-center-transcripts-dataset) | Open dataset | Real-world call center transcripts with PII redaction. |
| **Real-World Call Center Transcripts with PII Redaction** | [arXiv:2507.02958](https://arxiv.org/abs/2507.02958) | Largest open-source release | Inbound/outbound calls, Indian/Filipino/American accents. PII-redacted. |

---

### 2C. CRM / Deal Pipeline / Sales Forecasting

| Dataset | Source | Size | Details |
|---|---|---|---|
| **CRM Sales Predictive Analytics** | [Kaggle — agungpambudi](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics) | Open dataset | CRM performance data for predictive sales analytics. |
| **CRM Sales Opportunities** | [Kaggle — innocentmfa](https://www.kaggle.com/datasets/innocentmfa/crm-sales-opportunities) | Open dataset | Deal pipeline with opportunities, stages, and outcomes. |
| **Superstore Sales Dataset** | [Kaggle — rohitsahoo](https://www.kaggle.com/datasets/rohitsahoo/sales-forecasting) | Open dataset | Sales forecasting with time-series data. |
| **Predict Future Sales** | [Kaggle Competition](https://www.kaggle.com/c/competitive-data-science-predict-future-sales) | Open competition | Time-series daily sales data for revenue prediction. |

---

### 2D. Sentiment Analysis & NLP Intent Detection

| Dataset | Source | Details |
|---|---|---|
| **Stanford Sentiment Treebank (SST-5)** | Stanford NLP | Fine-grained 5-class sentiment on full sentences. Gold standard. |
| **Amazon Product Reviews** | Public / Kaggle | Customer satisfaction and product sentiment at scale. |
| **IMDb Reviews Dataset** | Public / Hugging Face | 50K movie reviews for binary sentiment classification. |
| **Banking Conversation Corpus** | [Hugging Face — talkmap](https://huggingface.co/datasets/talkmap/banking-conversation-corpus) | Banking domain conversations with intent labels. |
| **Email Intent Classification** | Research / Medium | NLP models classifying email intent (complaint, inquiry, request, etc.). |

---

### 2E. Contact Center / BPO / Customer Support

| Dataset | Source | Size | Details |
|---|---|---|---|
| **Multilingual Call Center Speech** | [Hugging Face — AxonData](https://huggingface.co/datasets/AxonData/multilingual-call-center-speech-dataset) | Multilingual | Call center speech across multiple languages. |
| **Call Center Data** | [Kaggle — satvicoder](https://www.kaggle.com/datasets/satvicoder/call-center-data) | Open dataset | Call center KPIs including AHT, resolution, satisfaction. |
| **Call Center Analysis** | [GitHub — globalsmile](https://github.com/globalsmile/Call-Center-Analysis) | Open source | Analysis of KPIs: CSAT, AHT, agent performance. |
| **NYC311 CSAT Surveys** | [Data.gov](https://catalog.data.gov/dataset/?tags=call-center) | Government data | Call taker performance and customer satisfaction scores. |
| **IBM Telco Customer Churn** | [Kaggle — yeanzc](https://www.kaggle.com/datasets/yeanzc/telco-customer-churn-ibm-dataset) | 7,043 customers, 21 columns | Gender, services, tenure, monthly charges, churn label. Industry standard. |
| **Telecom Churn Dataset** | [Kaggle — mnassrib](https://www.kaggle.com/datasets/mnassrib/telecom-churn-datasets) | Open dataset | Telecom-specific churn with 19 features. |

---

### 2F. Churn / Renewal / Expansion Revenue

| Dataset | Source | Details |
|---|---|---|
| **Telco Customer Churn (IBM)** | [Kaggle — blastchar](https://www.kaggle.com/datasets/blastchar/telco-customer-churn) | 7,043 customers. Features: tenure, contract type, payment method, monthly/total charges, churn label. |
| **Telecommunications Industry Churn** | [Kaggle — aadityabansalcodes](https://www.kaggle.com/datasets/aadityabansalcodes/telecommunications-industry-customer-churn-dataset) | Industry-specific churn data. |
| **SaaS Churn Research Data** | [PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0319998) | 1,000+ SaaS users. Key features: number of products, customers, marketplaces. Whale optimization algorithm for prediction. |
| **DataCamp Telecom Churn** | [DataCamp DataLab](https://www.datacamp.com/datalab/datasets/dataset-python-telecom-customer-churn) | Free dataset with interactive notebook environment. |

---

### 2G. Email & Chat Communication

| Dataset | Source | Details |
|---|---|---|
| **Enron Email Dataset** | Public (CMU) | ~500K emails from 150 users. The gold standard for email NLP research. |
| **Marketing Emails** | [Hugging Face — marketeam](https://huggingface.co/datasets/marketeam/Marketing-Emails) | Synthetic marketing emails with promotional framing, CTAs, persuasive rhetoric. |
| **Email Thread Summary** | [Hugging Face — sidhq](https://huggingface.co/datasets/sidhq/email-thread-summary) | Email threads with summaries — useful for account memory. |
| **Email Classification** | [Hugging Face — jason23322](https://huggingface.co/datasets/jason23322/high-accuracy-email-classifier) | High-accuracy email intent classifier data. |
| **WhatsApp Chat Data** | [Kaggle — mmuhammetcavus](https://www.kaggle.com/datasets/mmuhammetcavus/whatsapp-chat) | WhatsApp chat exports for NLP analysis. |

---

### 2H. Speaker Diarization (Talk-Listen Ratio)

| Dataset | Source | Details |
|---|---|---|
| **Speaker Diarization Datasets Collection** | [Hugging Face — diarizers-community](https://huggingface.co/collections/diarizers-community/speaker-diarization-datasets-66261b8d571552066e003788) | Curated collection of diarization datasets. |
| **CSSD (Conversational Short-phrase Speaker Diarization)** | [arXiv:2208.08042](https://arxiv.org/abs/2208.08042) | 20-hour conversational speech with verified speaker timestamps. |
| **MSDWILD (Multi-modal Speaker Diarization in the Wild)** | YouTube-sourced | 3,143 videos, 84 labelled hours. Multi-modal diarization. |
| **Awesome Diarization** | [GitHub — wq2012](https://github.com/wq2012/awesome-diarization) | Curated list of diarization papers, libraries, datasets, and resources. |

**Key benchmark from research:** Gong's 326K-call dataset shows won-deal average is 57% talk / 43% listen. Optimal discovery calls: 40–60% talk ratio. Optimal demos: 60–70%.

---

## 3. Data Gaps & Notes

| Gap | Impact on Tasknova | Mitigation |
|---|---|---|
| **No open B2B deal-stage dataset with evidence-backed progression** | Forecast Confidence Score and Stage Progression Integrity need labeled deal-stage data tied to conversation signals | Will need to generate synthetic data or collect from early customers |
| **No public stakeholder influence/org-chart dataset** | Stakeholder Influence Mapping (Intelligence Object #2) and Hidden Blocker Detection (#3) require relationship graphs | Must be built from CRM imports + conversation extraction; no public datasets exist |
| **Limited Indian-accent call center transcripts with annotations** | ASR + NLP pipeline for Indian market needs domain-specific fine-tuning data | TeleSalesCorpus has Indian accents; combine with IndicVoices for accent coverage |
| **No open "promise vs. delivery" tracking dataset** | Intelligence Objects #21 (Promise vs. Delivery Tracking) and #22 (Revenue Leakage) need labeled commitment data | Must be generated from customer conversation pipelines post-launch |
| **WhatsApp/Telegram business conversation data is scarce** | Day 1 connector integration but no training data for these channels | WhatsApp export format is documented; will need customer-contributed data with consent |
| **Coaching / improvement plan outcome data doesn't exist publicly** | Section 4 (Performance Improvement Engine) needs rep behavior change data over time | Must be collected longitudinally from Tasknova's own users |

---

## 4. Recommended Priority for Data Acquisition

### Tier 1 — Available Now (Download & Start Training)
1. **IndicVoices** (12K hours) → Hindi ASR fine-tuning
2. **TeleSalesCorpus** (91K transcripts) → Sales call analysis pipeline
3. **IBM Telco Churn** → Churn prediction model baseline
4. **Enron Email Dataset** → Email NLP pipeline
5. **Speaker Diarization Collection** → Talk-listen ratio engine

### Tier 2 — Available but Needs Augmentation
6. **CRM Sales Opportunities (Kaggle)** → Deal pipeline modeling (small, needs synthetic augmentation)
7. **Hindi-English Code-Switching Corpus** → Code-mix ASR (limited hours, combine with IndicVoices)
8. **Banking Conversation Corpus** → Intent detection baseline (domain transfer needed)
9. **Indian Emotional Speech Corpus** → Voice sentiment model

### Tier 3 — Must Build / Collect
10. Stakeholder influence mapping data → From early customer CRM imports
11. Promise vs. delivery tracking data → From conversation pipeline
12. WhatsApp/Telegram business conversations → From consented customer data
13. Rep coaching outcome data → Longitudinal collection post-launch
14. Industry-specific benchmarks (BPO, Real Estate, EdTech) → From pilot customers

---

## Sources

- [IndicVoices — AI4Bharat](https://huggingface.co/datasets/ai4bharat/IndicVoices)
- [IndicVoices-R — AI4Bharat](https://huggingface.co/datasets/ai4bharat/indicvoices_r)
- [Hindi Speech Recognition Dataset](https://huggingface.co/datasets/ud-nlp/hindi-speech-recognition-dataset)
- [Hindi-English Code-Switching Corpus](https://arxiv.org/abs/1810.00662)
- [Hindi-Marathi Code-Switched Dataset](https://www.sciencedirect.com/science/article/abs/pii/S0003682X24005590)
- [Indian Emotional Speech Corpus](https://huggingface.co/datasets/humyn-labs/Indian-Emotional-Speech-Corpus)
- [BhasaAnuvaad Speech Translation](https://arxiv.org/html/2411.04699v2)
- [Whisper Hindi-English Fine-Tuning](https://www.isca-archive.org/interspeech_2025/biswas25_interspeech.pdf)
- [TeleSalesCorpus](https://www.emergentmind.com/topics/telesalescorpus)
- [Sales Transcripts — Hugging Face](https://huggingface.co/datasets/gwenshap/sales-transcripts)
- [Sales Conversations — Hugging Face](https://huggingface.co/datasets/goendalf666/sales-conversations)
- [Call Center Transcripts — Kaggle](https://www.kaggle.com/datasets/oleksiymaliovanyy/call-center-transcripts-dataset)
- [Real-World Call Center Transcripts](https://arxiv.org/abs/2507.02958)
- [CRM Sales Predictive Analytics — Kaggle](https://www.kaggle.com/datasets/agungpambudi/crm-sales-predictive-analytics)
- [CRM Sales Opportunities — Kaggle](https://www.kaggle.com/datasets/innocentmfa/crm-sales-opportunities)
- [Superstore Sales Dataset — Kaggle](https://www.kaggle.com/datasets/rohitsahoo/sales-forecasting)
- [Banking Conversation Corpus — Hugging Face](https://huggingface.co/datasets/talkmap/banking-conversation-corpus)
- [Multilingual Call Center Speech — Hugging Face](https://huggingface.co/datasets/AxonData/multilingual-call-center-speech-dataset)
- [Call Center Data — Kaggle](https://www.kaggle.com/datasets/satvicoder/call-center-data)
- [IBM Telco Customer Churn — Kaggle](https://www.kaggle.com/datasets/yeanzc/telco-customer-churn-ibm-dataset)
- [Telco Customer Churn — Kaggle](https://www.kaggle.com/datasets/blastchar/telco-customer-churn)
- [SaaS Churn Prediction — PLOS ONE](https://journals.plos.org/plosone/article?id=10.1371/journal.pone.0319998)
- [Marketing Emails — Hugging Face](https://huggingface.co/datasets/marketeam/Marketing-Emails)
- [Email Thread Summary — Hugging Face](https://huggingface.co/datasets/sidhq/email-thread-summary)
- [WhatsApp Chat — Kaggle](https://www.kaggle.com/datasets/mmuhammetcavus/whatsapp-chat)
- [Speaker Diarization Datasets — Hugging Face](https://huggingface.co/collections/diarizers-community/speaker-diarization-datasets-66261b8d571552066e003788)
- [CSSD Diarization Dataset](https://arxiv.org/abs/2208.08042)
- [Awesome Diarization — GitHub](https://github.com/wq2012/awesome-diarization)
- [13 Best Free Datasets for Call Centers — Iguazio](https://www.iguazio.com/blog/13-best-free-datasets-for-call-centers-and-telcos/)
- [AI4Bharat ASR](https://ai4bharat.iitm.ac.in/areas/asr)
- [Gladia Code-Switching Guide](https://www.gladia.io/blog/what-is-code-switching-in-speech-recognition)
- [Talk-Listen Ratio Research — Demodesk](https://demodesk.com/resources-guides/talk-ratio-research)
