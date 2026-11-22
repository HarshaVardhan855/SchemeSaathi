# SchemeSaathi — Voice-First Scheme Eligibility Agent

**Track 1: Civic Pulse, Digital Governance & Public Information**

Helps citizens discover and apply for government welfare schemes through voice conversation in Telugu, Hindi, or English. No app install, no literacy required.

## Problem
60% of eligible citizens don't claim welfare schemes (PM-KISAN, Ayushman, pensions, scholarships) because forms are complex, English-only, and require documents they don't know how to get.

## Solution
1. **Voice Q&A** in Telugu/Hindi/English → extracts structured profile
2. **RAG over curated scheme rules** (15 schemes: 5 Central + 5 AP + 5 Telangana) → computes eligibility + missing docs
3. **Auto-fills application** on government portals (Playwright) or generates filled PDF + checklist
4. **Delivers via WhatsApp/IVR** — works on feature phones

## Architecture
```
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

## Quick Start

### Prerequisites
- Python 3.10+
- Docker (optional, for local stack)
- Groq API key (free tier: `https://console.groq.com`)

### Local Development
```bash
cd schemesaathi
cp .env.example .env
# Edit .env with your Groq API key
docker-compose up -d
# OR
pip install -r requirements.txt
python -m streamlit run streamlit_app.py
```

### Voice Pipeline Test
```bash
# Record a test audio file (Telugu/Hindi/English)
python voice_pipeline.py --input test_audio.wav --lang te
```

## Project Structure
```
schemesaathi/
├── schemes/                    # Curated scheme knowledge base (15 markdown files)
│   ├── central/
│   │   ├── pm_kisan.md
│   │   ├── ayushman_bharat.md
│   │   ├── nsap_old_age_pension.md
│   │   ├── nsap_widow_pension.md
│   │   └── pm_svanidhi.md
│   ├── andhra_pradesh/
│   │   ├── annadata_sukhibhava.md       # Replaces YSR Rythu Bharosa
│   │   ├── shg_loan_waiver.md           # Replaces YSR Aasara
│   │   ├── mahila_samriddhi.md          # Replaces YSR Cheyutha
│   │   ├── ntr_bharosa_pension.md       # CONTINUED
│   │   └── talliki_vandanam.md          # Replaces Amma Vodi
│   └── telangana/
│       ├── rythu_bandhu.md              # CONTINUED
│       ├── rythu_bima.md                # CONTINUED
│       ├── aasara_pension.md            # CONTINUED & ENHANCED
│       ├── kalyana_lakshmi.md           # CONTINUED
│       └── dalit_empowerment.md         # Restructured from Dalit Bandhu
├── voice_pipeline.py           # Whisper → Groq extraction → Piper TTS
├── state_detector.py           # Language + state inference
├── eligibility_rag.py          # Embeddings + LLM reasoning
├── playwright_fill.py          # PM-KISAN form automation
├   pdf_generator.py            # Filled PDF + checklist generation
├── whatsapp_sender.py          # WhatsApp Cloud API / Twilio
├   streamlit_app.py            # Demo UI
├   requirements.txt
├   docker-compose.yml
├   .env.example
└── README.md
```

## Languages Supported
- **Telugu (te)** — Andhra Pradesh, Telangana
- **Hindi (hi)** — National, North India
- **English (en)** — Urban, officials, fallback

## Schemes Covered (15 Total) — **Updated for Current Governments (Late 2024)**

### Central (5) — All States (BJP/NDA Government)
1. PM-KISAN — Farmer income support (₹6,000/yr)
2. Ayushman Bharat (PM-JAY) — Health insurance (₹5L)
3. NSAP Old Age Pension — Senior citizens (₹200-500/mo)
4. NSAP Widow Pension — Widows 40-79 (₹300-500/mo)
5. PM-SVANidhi — Street vendor loans (₹10k-50k)

### Andhra Pradesh (5) — **TDP+JSP+BJP Government (since June 2024)**
1. **Annadata Sukhibhava** — Farmer support (₹13,500/yr incl. PM-KISAN) *[Replaces YSR Rythu Bharosa]*
2. **SHG Loan Waiver & Vaddileni Runalu** — Women SHG loan waiver + 4% interest subsidy *[Replaces YSR Aasara]*
3. **Mahila Samriddhi** — BC/SC/ST/Minority women 45-60 (₹75k/4yr) *[Replaces YSR Cheyutha]*
4. **NTR Bharosa Pension** — Enhanced pension (₹3,000/mo) **[CONTINUED]**
5. **Talliki Vandanam** — Mothers of school children (₹15,000/yr) *[Replaces Amma Vodi]*

### Telangana (5) — **Congress Government (since Dec 2023)**
1. **Rythu Bandhu** — Farmer investment support (₹10k/acre/yr) **[CONTINUED]**
2. **Rythu Bima** — Farmer life insurance (₹5L) **[CONTINUED]**
3. **Aasara Pension** — Old age/widow/disabled (₹2,016-3,016/mo) **[CONTINUED & ENHANCED]**
4. **Kalyana Lakshmi / Shaadi Mubarak** — Marriage grant (₹1,00,116) **[CONTINUED]**
5. **Dalit Empowerment Scheme** — Dalit family grant (₹10L unit cost) *[Restructured from Dalit Bandhu]*

## Demo Flow
1. User selects language (Telugu/Hindi/English)
2. User speaks: "నా పేరు రమేష్. 2 ఎకర్ భూమి. ఆధార్ ఉంది."
3. System extracts profile + detects state (AP)
4. RAG checks 10 applicable schemes (5 Central + 5 AP)
5. Voice response: "మీరు 3 స్కీమ్స్ కు అర్హతदार రు..."
6. Click "Auto-fill PM-KISAN" → Playwright fills form
7. Download filled PDF + missing docs checklist
8. Send to WhatsApp

## Free Tier Services
| Service | Free Limit |
|---------|------------|
| Groq (Llama-3.1-8B-instant) | 14,400 req/day |
| Whisper.cpp | Local, unlimited |
| Piper TTS | Local, unlimited |
| WhatsApp Cloud API | 1,000 conversations/mo |
| Twilio WhatsApp Sandbox | Unlimited testing |
| Streamlit Cloud | Free hosting |
| Render/Railway | 750 hrs/mo |

## License
MIT — Built for hackathon demonstration.