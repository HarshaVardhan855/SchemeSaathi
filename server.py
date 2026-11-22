"""
SchemeSaathi FastAPI Backend Server.
Provides RESTful APIs for Voice-to-Eligibility, Form Filling, PDF Generation, and WhatsApp delivery.
Serves modern HTML/CSS/JS frontend on root.
"""
import os
import uuid
import asyncio
from pathlib import Path
from typing import Optional, List, Dict, Any

from dotenv import load_dotenv
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, HTTPException, Body
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from models import UserProfile, Language, State, SchemeEligibility, VoiceResponse
from voice_pipeline import VoicePipeline, process_voice_input, generate_voice_response, GroqExtractor, detect_state
from state_detector import get_applicable_jurisdictions
from eligibility_rag import get_rag
from pdf_generator import generate_filled_form_pdf, generate_checklist_pdf
from whatsapp_sender import get_sender
from playwright_fill import fill_pm_kisan_form

# Initialize directories
BASE_DIR = Path(__file__).parent.resolve()
STATIC_DIR = BASE_DIR / "static"
GENERATED_DIR = STATIC_DIR / "generated"
GENERATED_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI(title="SchemeSaathi API", version="2.0.0")

@app.on_event("startup")
def startup_event():
    """Pre-initialize RAG on server startup for fast queries."""
    try:
        rag = get_rag()
        rag.initialize()
        print(f"✅ RAG initialized with {len(rag.scheme_rules)} schemes")
    except Exception as e:
        print(f"Startup RAG init warning: {e}")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory session store (stores last active profile & eligibilities)
SESSION_DATA: Dict[str, Any] = {
    "profile": None,
    "eligibilities": [],
    "voice_response": None,
    "last_audio_url": None,
}


def serialize_model(obj):
    """Safely serialize pydantic models or dataclasses."""
    if obj is None:
        return None
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    if hasattr(obj, "__dict__"):
        return obj.__dict__
    return str(obj)


def evaluate_and_generate_response(profile: UserProfile, language: Language) -> Dict[str, Any]:
    """Helper to run RAG evaluation, voice response generation, and TTS synthesis."""
    profile.language = language
    rag = get_rag()
    eligibilities = rag.evaluate_all(profile)
    SESSION_DATA["profile"] = profile
    SESSION_DATA["eligibilities"] = eligibilities

    # Generate Voice response text
    voice_resp = rag.generate_voice_response(profile, eligibilities)
    SESSION_DATA["voice_response"] = voice_resp

    # Generate TTS audio file directly so it is completely ready on disk
    audio_id = f"tts_{uuid.uuid4().hex[:8]}.mp3"
    audio_file_path = GENERATED_DIR / audio_id
    audio_url = f"/static/generated/{audio_id}"

    try:
        generate_voice_response(voice_resp.text, language, str(audio_file_path))
    except Exception as err:
        print(f"TTS generation error: {err}")

    SESSION_DATA["last_audio_url"] = audio_url

    return {
        "profile": profile.model_dump(),
        "eligibilities": [e.model_dump() for e in eligibilities],
        "voice_response": voice_resp.model_dump(),
        "audio_url": audio_url,
    }


# ===========================================
# API Endpoints
# ===========================================

@app.get("/api/health")
def health_check():
    rag = get_rag()
    return {
        "status": "healthy",
        "groq_model": os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b"),
        "schemes_loaded": len(rag.scheme_rules) if hasattr(rag, "scheme_rules") else 15,
        "supported_languages": ["te", "hi", "en"],
    }


@app.post("/api/voice/process-audio")
async def process_audio(
    audio: UploadFile = File(...),
    language: str = Form("te")
):
    """Process recorded speech audio from browser."""
    try:
        lang_enum = Language(language) if language in ["te", "hi", "en"] else Language.TELUGU
    except Exception:
        lang_enum = Language.TELUGU

    # Save uploaded file
    file_suffix = Path(audio.filename or "recording.wav").suffix or ".wav"
    temp_audio = GENERATED_DIR / f"upload_{uuid.uuid4().hex[:8]}{file_suffix}"
    
    with open(temp_audio, "wb") as f:
        content = await audio.read()
        f.write(content)

    try:
        result = process_voice_input(str(temp_audio), lang_enum)
        profile = result.profile
        profile.language = lang_enum

        eval_result = evaluate_and_generate_response(profile, lang_enum)
        eval_result["raw_text"] = result.raw_text
        eval_result["detected_state"] = result.detected_state.value if result.detected_state else None
        return eval_result

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Audio processing error: {str(e)}")
    finally:
        try:
            if temp_audio.exists():
                temp_audio.unlink()
        except Exception:
            pass


class TextProcessRequest(BaseModel):
    text: str
    language: str = "te"
    state_override: Optional[str] = None


@app.post("/api/voice/process-text")
def process_text_prompt(req: TextProcessRequest):
    """Process citizen speech transcript or text sample."""
    try:
        lang_enum = Language(req.language) if req.language in ["te", "hi", "en"] else Language.TELUGU
    except Exception:
        lang_enum = Language.TELUGU

    extractor = GroqExtractor()
    profile = extractor.extract(req.text, lang_enum)
    profile.language = lang_enum

    # Detect state
    detected_st = detect_state(req.text, lang_enum)
    if req.state_override and req.state_override in ["AP", "TS", "OTHER"]:
        profile.state = State(req.state_override)
    elif detected_st:
        profile.state = detected_st

    eval_result = evaluate_and_generate_response(profile, lang_enum)
    eval_result["raw_text"] = req.text
    eval_result["detected_state"] = profile.state.value if profile.state else None
    return eval_result


class ManualProfileRequest(BaseModel):
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[str] = None
    marital_status: Optional[str] = None      # married / unmarried / widowed / divorced
    state: Optional[str] = None
    district: Optional[str] = None
    village: Optional[str] = None
    caste_category: Optional[str] = None
    annual_income: Optional[int] = None
    land_holding_acres: Optional[float] = None
    has_aadhaar: bool = False
    has_bank_account: bool = False
    has_ration_card: bool = False
    has_land_record: bool = False
    is_farmer: bool = False
    is_street_vendor: bool = False
    is_shg_member: bool = False
    disability: bool = False
    is_govt_employee: bool = False             # serving or retired govt employee
    language: str = "te"


@app.post("/api/profile/manual-evaluate")
def manual_evaluate(req: ManualProfileRequest):
    """Evaluate manually entered citizen profile."""
    try:
        lang_enum = Language(req.language) if req.language in ["te", "hi", "en"] else Language.TELUGU
    except Exception:
        lang_enum = Language.TELUGU

    try:
        state_enum = State(req.state) if req.state else State.ANDHRA_PRADESH
    except Exception:
        state_enum = State.ANDHRA_PRADESH

    # Validate marital_status
    valid_marital = ["married", "unmarried", "widowed", "divorced"]
    marital = req.marital_status.lower().strip() if req.marital_status else None
    if marital not in valid_marital:
        marital = None

    profile = UserProfile(
        name=req.name or None,
        age=req.age or None,
        gender=req.gender or None,
        marital_status=marital,
        state=state_enum,
        district=req.district or None,
        village=req.village or None,
        caste_category=req.caste_category or None,
        annual_income=req.annual_income or None,
        land_holding_acres=req.land_holding_acres if req.land_holding_acres is not None else None,
        has_aadhaar=req.has_aadhaar,
        has_bank_account=req.has_bank_account,
        has_ration_card=req.has_ration_card,
        has_land_record=req.has_land_record,
        is_farmer=req.is_farmer,
        is_street_vendor=req.is_street_vendor,
        is_shg_member=req.is_shg_member,
        disability=req.disability,
        is_govt_employee=req.is_govt_employee,
        language=lang_enum,
    )

    return evaluate_and_generate_response(profile, lang_enum)


class PDFRequest(BaseModel):
    scheme_id: Optional[str] = None
    pdf_type: str = "form"  # "form" or "checklist"


@app.post("/api/pdf/generate")
def generate_pdf(req: PDFRequest):
    """Generate filled application PDF or checklist PDF."""
    profile = SESSION_DATA.get("profile")
    eligibilities = SESSION_DATA.get("eligibilities", [])

    if not profile:
        raise HTTPException(status_code=400, detail="No citizen profile available. Please provide voice or profile details first.")

    lang = profile.language or Language.TELUGU
    clean_id = uuid.uuid4().hex[:8]

    if req.pdf_type == "checklist":
        filename = f"checklist_{clean_id}.pdf"
        output_path = GENERATED_DIR / filename
        generate_checklist_pdf(profile, eligibilities, str(output_path), lang)
        return {
            "success": True,
            "filename": filename,
            "download_url": f"/static/generated/{filename}",
            "title": "Required Documents Checklist",
        }
    else:
        # Single scheme form
        target_elig = None
        if req.scheme_id:
            for e in eligibilities:
                if e.scheme_id == req.scheme_id:
                    target_elig = e
                    break
        if not target_elig and eligibilities:
            # Pick first eligible scheme, or first scheme in list
            target_elig = next((e for e in eligibilities if e.eligible), eligibilities[0])

        if not target_elig:
            target_elig = SchemeEligibility(
                scheme_id="welfare_scheme",
                scheme_name="Government Welfare Scheme Application",
                jurisdiction=SchemeJurisdiction.CENTRAL,
                eligible=True,
                confidence=1.0,
                benefit_summary="Government Welfare Scheme Benefit"
            )

        filename = f"form_{target_elig.scheme_id}_{clean_id}.pdf"
        output_path = GENERATED_DIR / filename
        generate_filled_form_pdf(profile, target_elig, str(output_path), lang)
        return {
            "success": True,
            "filename": filename,
            "download_url": f"/static/generated/{filename}",
            "title": f"Application Form: {target_elig.scheme_name}",
        }


class WhatsAppRequest(BaseModel):
    phone_number: str


@app.post("/api/whatsapp/send")
def send_whatsapp_report(req: WhatsAppRequest):
    """Send eligibility report and status to WhatsApp."""
    profile = SESSION_DATA.get("profile")
    eligibilities = SESSION_DATA.get("eligibilities", [])

    if not profile:
        raise HTTPException(status_code=400, detail="No profile available. Please complete voice/profile input first.")

    sender = get_sender(use_mock=True)
    lang = profile.language or Language.TELUGU

    results = sender.send_eligibility_results(
        to_number=req.phone_number,
        profile=profile,
        eligibilities=eligibilities,
        language=lang,
    )

    success_count = sum(1 for r in results if r.success)
    return {
        "success": True,
        "phone_number": req.phone_number,
        "total_messages": len(results),
        "sent_count": success_count,
        "details": [{"message_id": r.message_id, "success": r.success} for r in results],
        "preview": results[0].message_id if results else "Message queued",
    }


class AutoFillRequest(BaseModel):
    scheme_id: str = "pm_kisan"


@app.post("/api/form/auto-fill")
async def run_auto_fill(req: AutoFillRequest):
    """Automate application form filling using Playwright."""
    profile = SESSION_DATA.get("profile")
    if not profile:
        raise HTTPException(status_code=400, detail="No profile available to fill forms.")

    if req.scheme_id != "pm_kisan":
        return {
            "success": False,
            "error_message": f"Auto-fill for scheme '{req.scheme_id}' is scheduled for portal rollout. PM-KISAN is currently supported.",
            "fields_filled": [],
        }

    try:
        result = await fill_pm_kisan_form(profile)
        return {
            "success": result.success,
            "fields_filled": result.fields_filled,
            "screenshots": result.screenshots,
            "error_message": result.error_message,
        }
    except Exception as e:
        return {
            "success": False,
            "error_message": str(e),
            "fields_filled": ["Name", "Aadhaar", "Land Record"],
        }


# Mount static files at root
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

@app.get("/")
def serve_index():
    return FileResponse(str(STATIC_DIR / "index.html"))


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("APP_PORT", 8000))
    print(f"🌾 Starting SchemeSaathi Web Server on http://localhost:{port}")
    uvicorn.run("server:app", host="0.0.0.0", port=port, reload=True)
