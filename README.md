# 🌾 SchemeSaathi — Voice-First Scheme Eligibility Agent

**🎯 Track 1: Civic Pulse, Digital Governance & Public Information**

SchemeSaathi helps Indian citizens discover, check eligibility for, and apply for government welfare schemes through conversational voice in **Telugu**, **Hindi**, or **English**. It eliminates bureaucratic friction by translating spoken voice into structured citizen profiles, evaluating eligibility across 15+ central and state schemes via RAG, generating application PDFs, and enabling one-click auto-fill.

---

## 💡 Key Features

1. 🗣️ **Voice Q&A**: Real-time voice interaction with multilingual transcription (Groq Whisper-large-v3) and natural audio generation (gTTS in Telugu, Hindi, English).
2. 🧠 **Dynamic RAG Eligibility Engine**: Evaluates rule logic for 15 schemes (5 Central, 5 Andhra Pradesh, 5 Telangana) with exact match criteria, age bounds, landholdings, caste, and income ceilings.
3. 📄 **Application & Checklist PDF Generator**: Generates clean, ready-to-print official scheme application forms and missing document checklists in PDF format.
4. 📲 **WhatsApp Dispatch**: Sends application documents and eligibility summaries directly to citizen WhatsApp numbers via Twilio.
5. 🤖 **Portal Automation**: Playwright-powered background form filling for portals like PM-KISAN.
6. 🚀 **Production Ready for Render**: Fast, lightweight FastAPI server designed for zero-fuss deployment to cloud platforms like Render.

---

## 🏗️ System Architecture

```text
Voice / Form Input (Telugu / Hindi / English)
                     │
                     ▼
       Groq Whisper Speech-to-Text
                     │
                     ▼
       State Detection (AP / TS / Other)
                     │
                     ▼
       RAG Eligibility Engine (Groq Llama / Qwen)
       ├─ Central Schemes (PM-KISAN, Ayushman Bharat, etc.)
       ├─ Andhra Pradesh (Annadata Sukhibhava, NTR Bharosa, etc.)
       └─ Telangana (Rythu Bandhu, Rythu Bima, Aasara, etc.)
                     │
      ┌──────────────┴──────────────┐
      ▼                             ▼
 gTTS Multilingual Audio     ReportLab PDF Generator
 (Instant Voice Reply)       (Filled Forms & Checklists)
      │                             │
      └──────────────┬──────────────┘
                     ▼
         WhatsApp & Playwright Dispatch
```

---

## 🚀 Deploying to Render

SchemeSaathi is optimized for instant deployment on [Render](https://render.com).

### Option 1: Render Blueprint (Automatic & Recommended)
This repository includes a `render.yaml` blueprint file:

1. Push this repository to your GitHub account (`https://github.com/HarshaVardhan855/SchemeSaathi`).
2. Log in to [Render Dashboard](https://dashboard.render.com).
3. Click **New +** → **Blueprint**.
4. Connect your GitHub repository (`SchemeSaathi`).
5. Render will detect `render.yaml` automatically.
6. Enter your `GROQ_API_KEY` under Environment Variables.
7. Click **Apply**. Render will build and deploy the web service.

---

### Option 2: Manual Web Service Setup on Render

1. Log in to [Render Dashboard](https://dashboard.render.com) and click **New +** → **Web Service**.
2. Connect your GitHub repository: `https://github.com/HarshaVardhan855/SchemeSaathi`.
3. Configure the settings:
   - **Name**: `schemesaathi`
   - **Region**: Choose closest to your users (e.g., `Singapore` or `Oregon`)
   - **Branch**: `main`
   - **Runtime**: `Python 3`
   - **Build Command**:
     ```bash
     pip install -r requirements.txt
     ```
   - **Start Command**:
     ```bash
     uvicorn server:app --host 0.0.0.0 --port $PORT
     ```
   - **Plan**: `Free`

4. Add **Environment Variables** in Render:
   | Variable | Value | Description |
   |---|---|---|
   | `PYTHON_VERSION` | `3.11.9` | Recommended Python version |
   | `GROQ_API_KEY` | `gsk_...` | Your Groq API key ([Get one free](https://console.groq.com)) |
   | `GROQ_MODEL` | `qwen/qwen3.8-27b` | High-speed LLM model |
   | `SCHEMES_DIR` | `./schemes` | Path to scheme knowledge base |
   | `TWILIO_ACCOUNT_SID` | *(Optional)* | Twilio WhatsApp Account SID |
   | `TWILIO_AUTH_TOKEN` | *(Optional)* | Twilio WhatsApp Auth Token |
   | `TWILIO_WHATSAPP_NUMBER` | *(Optional)* | Twilio WhatsApp sandbox number |

5. Click **Create Web Service**. Once deployed, Render gives you a public URL (e.g. `https://schemesaathi.onrender.com`).

---

## 💻 Local Development Setup

### 1. Prerequisites
- Python 3.10 or 3.11
- A free Groq API key from [Groq Console](https://console.groq.com)

### 2. Installation
```bash
git clone https://github.com/HarshaVardhan855/SchemeSaathi.git
cd SchemeSaathi

# Create and activate virtual environment
python -m venv venv
# On Windows:
.\venv\Scripts\activate
# On Linux/macOS:
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### 3. Configure Environment Variables
Copy `.env.example` to `.env` and fill in your Groq API key:
```bash
cp .env.example .env
```
Inside `.env`:
```env
GROQ_API_KEY=your_actual_groq_api_key_here
GROQ_MODEL=qwen/qwen3.8-27b
SCHEMES_DIR=./schemes
```

### 4. Run the Web Application
```bash
python server.py
# Or with uvicorn:
uvicorn server:app --reload --host 0.0.0.0 --port 8000
```
Open [http://localhost:8000](http://localhost:8000) in your browser.

---

## 📁 Clean Production Project Structure

```text
schemesaathi/
├── render.yaml                 # Render infrastructure blueprint
├── requirements.txt            # Production dependencies
├── server.py                   # FastAPI application & REST endpoints
├── models.py                   # Pydantic schemas (profiles, recommendations)
├── eligibility_rag.py          # Vector RAG & scheme rules engine
├── state_detector.py           # Language, district, and state detector
├── voice_pipeline.py           # Speech-to-text & TTS pipeline
├── pdf_generator.py            # Application & checklist PDF builder
├── playwright_fill.py          # Portal automation scripts
├── whatsapp_sender.py          # Twilio WhatsApp messaging integration
├── schemes/                    # 15 Curated markdown knowledge base files
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
├── static/                     # Frontend client
│   ├── index.html              # Single-page interface
│   ├── style.css               # Design system & styles
│   ├── app.js                  # Audio recorder & reactive UI controller
│   └── generated/              # Output directory for PDFs and audio (.gitkeep)
├── .env.example                # Sample environment configuration
├── .gitignore                  # Git ignore rules
└── README.md                   # Documentation
```

---

## 📚 Schemes Covered (15 Schemes)

### 🇮🇳 Central Schemes (All States)
1. 🌾 **PM-KISAN** — Farmer income support (₹6,000/year in 3 installments)
2. 🏥 **Ayushman Bharat (PM-JAY)** — Health insurance coverage up to ₹5 Lakh/family
3. 👴 **NSAP Old Age Pension** — Monthly pension for citizens aged 60+
4. 👩 **NSAP Widow Pension** — Monthly pension for eligible widows aged 40–79
5. 🛒 **PM-SVANidhi** — Micro-credit working capital loans for street vendors (₹10,000–₹50,000)

### 🌅 Andhra Pradesh
1. 🌾 **Annadata Sukhibhava** — Financial assistance for farmers (₹20,000/year including PM-KISAN)
2. 🤝 **SHG Loan Waiver & Vaddileni Runalu** — Self-Help Group women loan waiver and interest subsidy
3. 👩 **Mahila Samriddhi** — Financial support for BC/SC/ST/Minority women
4. 👴 **NTR Bharosa Pension** — Enhanced social security pension (₹4,000/month)
5. 🎓 **Talliki Vandanam** — Annual educational financial assistance for mothers (₹15,000/year)

### 🌇 Telangana
1. 🌾 **Rythu Bandhu** — Investment support for agriculture (₹10,000/acre/year)
2. 🛡️ **Rythu Bima** — Life insurance for farmers (₹5 Lakh coverage)
3. 👵 **Aasara Pension** — Social security pension for senior citizens, widows, and disabled
4. 💍 **Kalyana Lakshmi / Shaadi Mubarak** — Financial marriage assistance for brides (₹1,00,116)
5. 🤝 **Dalit Empowerment Scheme** — Financial grant for Dalit family entrepreneurship

---

## 🌐 Supported Languages

| Language | Code | Region / Usage |
|---|---|---|
| **Telugu** | `te` | Andhra Pradesh & Telangana |
| **Hindi** | `hi` | National & North India |
| **English** | `en` | Urban & Official fallback |

---

## ⚖️ License

MIT License — Built for civic governance and digital inclusion.
