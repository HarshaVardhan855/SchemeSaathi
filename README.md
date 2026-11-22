# 🌾 SchemeSaathi — Voice-First Scheme Eligibility Agent

**🎯 Track 1: Civic Pulse, Digital Governance & Public Information**

Helps citizens discover and apply for government welfare schemes through voice conversation in Telugu, Hindi, or English. No app install, no literacy required.

## 🚨 Problem

60% of eligible citizens don't claim welfare schemes (PM-KISAN, Ayushman, pensions, scholarships) because forms are complex, English-only, and require documents they don't know how to get.

## 💡 Solution

1. 🗣️ **Voice Q&A** in Telugu/Hindi/English → extracts structured profile
2. 🧠 **RAG over curated scheme rules** (15 schemes: 5 Central + 5 AP + 5 Telangana) → computes eligibility + missing docs
3. 📝 **Auto-fills application** on government portals (Playwright) or generates filled PDF + checklist
4. 📱 **Delivers via WhatsApp/IVR** — works on feature phones

## 🏗️ Architecture

```text
Voice Input → Whisper.cpp (STT) → Groq/Llama (Structured Extraction)
                    ↓
            State Detection (AP/TS/Other)
                    ↓
            RAG Eligibility Engine (sentence-transformers + Llama)
                    ↓
            Piper TTS → Voice Response (same language)
                    ↓
            Playwright Form-Fill / PDF Generation
                    ↓
            WhatsApp Cloud API / Twilio Sandbox
```

## 🚀 Quick Start

### 📋 Prerequisites

- Python 3.10+
- Docker (optional, for local stack)
- Groq API key (free tier: https://console.groq.com)

### 💻 Local Development

```bash
cd SchemeSaathi
cp .env.example .env
# Edit .env with your Groq API key
docker-compose up -d
# OR
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

### 🎙️ Voice Pipeline Test

```bash
# Record a test audio file (Telugu/Hindi/English)
python voice_pipeline.py --input test_audio.wav --lang te
```

## 📁 Project Structure

```text
SchemeSaathi/
├── schemes/                    # Curated scheme knowledge base (15 markdown files)
│   ├── central/
│   │   ├── pm_kisan.md
│   │   ├── ayushman_bharat.md
│   │   ├── nsap_old_age_pension.md
│   │   ├── nsap_widow_pension.md
│   │   └── pm_svanidhi.md
│   ├── andhra_pradesh/
│   │   ├── annadata_sukhibhava.md
│   │   ├── shg_loan_waiver.md
│   │   ├── mahila_samriddhi.md
│   │   ├── ntr_bharosa_pension.md
│   │   └── talliki_vandanam.md
│   └── telangana/
│       ├── rythu_bandhu.md
│       ├── rythu_bima.md
│       ├── aasara_pension.md
│       ├── kalyana_lakshmi.md
│       └── dalit_empowerment.md
├── voice_pipeline.py           # Whisper → Groq extraction → Piper TTS
├── state_detector.py           # Language + state inference
├── eligibility_rag.py          # Embeddings + LLM reasoning
├── playwright_fill.py          # PM-KISAN form automation
├── pdf_generator.py            # Filled PDF + checklist generation
├── whatsapp_sender.py          # WhatsApp Cloud API / Twilio
├── streamlit_app.py            # Demo UI
├── requirements.txt
├── docker-compose.yml
├── .env.example
└── README.md
```

## 🌐 Languages Supported

- 🇮🇳 **Telugu (te)** — Andhra Pradesh, Telangana
- 🇮🇳 **Hindi (hi)** — National, North India
- 🇬🇧 **English (en)** — Urban, officials, fallback

## 📚 Schemes Covered (15 Total)

### 🇮🇳 Central (5)

1. 🌾 PM-KISAN — Farmer income support (₹6,000/yr)
2. 🏥 Ayushman Bharat (PM-JAY) — Health insurance (₹5L)
3. 👴 NSAP Old Age Pension — Senior citizens (₹200–500/mo)
4. 👩 NSAP Widow Pension — Widows 40–79 (₹300–500/mo)
5. 🛒 PM-SVANidhi — Street vendor loans (₹10k–50k)

### 🌅 Andhra Pradesh (5)

1. 🌾 **Annadata Sukhibhava** — Farmer support (₹13,500/yr incl. PM-KISAN)
2. 🤝 **SHG Loan Waiver & Vaddileni Runalu** — Women SHG loan waiver + 4% interest subsidy
3. 👩 **Mahila Samriddhi** — BC/SC/ST/Minority women 45–60 (₹75k/4yr)
4. 👴 **NTR Bharosa Pension** — Enhanced pension (₹3,000/mo)
5. 🎓 **Talliki Vandanam** — Mothers of school children (₹15,000/yr)

### 🌇 Telangana (5)

1. 🌾 **Rythu Bandhu** — Farmer investment support (₹10k/acre/yr)
2. 🛡️ **Rythu Bima** — Farmer life insurance (₹5L)
3. 👵 **Aasara Pension** — Old age/widow/disabled (₹2,016–3,016/mo)
4. 💍 **Kalyana Lakshmi / Shaadi Mubarak** — Marriage grant (₹1,00,116)
5. 🤝 **Dalit Empowerment Scheme** — Dalit family grant (₹10L unit cost)

## 🧪 Demo Flow

1. 👤 User selects language (Telugu/Hindi/English)
2. 🗣️ User speaks: "నా పేరు రమేష్. 2 ఎకర్ భూమి. ఆధార్ ఉంది."
3. 🔍 System extracts profile and detects state (AP)
4. 🧠 RAG checks applicable schemes
5. 🔊 Voice response delivers likely eligible schemes
6. 🖱️ Click "Auto-fill PM-KISAN" → Playwright fills the form
7. 📄 Download filled PDF and missing-document checklist
8. 📲 Send the result to WhatsApp

## 🆓 Free Tier Services

| Service | Free Limit |
|---------|------------|
| Groq (Llama-3.1-8B-instant) | 14,400 req/day |
| Whisper.cpp | Local, unlimited |
| Piper TTS | Local, unlimited |
| WhatsApp Cloud API | 1,000 conversations/mo |
| Twilio WhatsApp Sandbox | Unlimited testing |
| Streamlit Cloud | Free hosting |
| Render/Railway | 750 hrs/mo |

## ⚖️ License

MIT — Built for hackathon demonstration.
