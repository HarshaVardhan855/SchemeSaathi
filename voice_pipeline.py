"""
Voice Pipeline: Whisper.cpp (STT) → Groq/Llama (Structured Extraction) → Piper TTS
Supports Telugu, Hindi, English
"""
import os
import json
import subprocess
import tempfile
import asyncio
from pathlib import Path
from typing import Optional, Dict, Any, List
from dataclasses import dataclass

from groq import Groq
from pydantic import BaseModel

from models import UserProfile, Language, State, VoiceResponse


# ===========================================
# Configuration
# ===========================================
from dotenv import load_dotenv
load_dotenv()

WHISPER_MODEL = os.getenv("WHISPER_MODEL", "base")
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")  # Fast, free tier

# Piper TTS voice mapping
PIPER_VOICES = {
    Language.TELUGU: "te_IN-tts",
    Language.HINDI: "hi_IN-tts",
    Language.ENGLISH: "en_US-lessac",
}

# Language detection keywords
LANGUAGE_KEYWORDS = {
    Language.TELUGU: ["నా", "నేను", "ఉన్నది", "కావాలి", "ఎలా", "ఎప్పుడు", "ఎక్కడ"],
    Language.HINDI: ["मेरा", "मैं", "है", "चाहिए", "कैसे", "कब", "कहाँ"],
    Language.ENGLISH: ["my", "i am", "have", "want", "how", "when", "where"],
}

STATE_KEYWORDS = {
    State.ANDHRA_PRADESH: ["ఆంధ్ర", "అనంతపురం", "కడప", "చిత్తూరు", "గుంటూరు", "కృష్ణ", "ప్రకాశం", "శ్రీకాకుళం", "విశాఖపట్నం", "విజయవాడ", "తిరుపతి", "వరంగల్", "నెల్లూరు", "కాకినాడ", "రాజమండ్రి", "ఎలూరు", "మచిలీపట్నం", "ఆంద్ర", "ఆంధ్రప్రదేశ్"],
    State.TELANGANA: ["తెలంగాణ", "హైదరాబాద్", "వరంగల్", "నిజామాబాద్", "కరీంనగర్", "ఖమ్మం", "నల్గొండ", "మహబూబ్‌నగర్", "అదిలాబాద్", "మెదక్", "రంగారెడ్డి", "మహబూబ్ాబాద్", "జorrido", "భో팔్", "జగ أقرب", "తెలంగాణ", "TS"],
}


# ===========================================
# Data Classes
# ===========================================
@dataclass
class ExtractionResult:
    profile: UserProfile
    raw_text: str
    language: Language
    detected_state: Optional[State]


# ===========================================
# Speech-to-Text (STT) Engine
# ===========================================
class WhisperSTT:
    """Speech-to-text using Groq Whisper API (whisper-large-v3) with local CLI fallback."""

    def __init__(self, model: str = WHISPER_MODEL):
        self.model = model
        self.binary = self._find_whisper_binary()

    def _find_whisper_binary(self) -> Optional[str]:
        """Find local whisper binary if available on system."""
        candidates = [
            "whisper-cli",
            "whisper",
            "./whisper.cpp/main",
            "./whisper.cpp/build/bin/whisper-cli",
        ]
        cmd = "where" if os.name == "nt" else "which"
        for c in candidates:
            try:
                if subprocess.run([cmd, c], capture_output=True).returncode == 0:
                    return c
            except Exception:
                pass
        return None

    def transcribe(self, audio_path: str, language: Optional[str] = None) -> str:
        """Transcribe audio file to text using Groq Whisper API or local binary."""
        # Primary: Groq Whisper API (whisper-large-v3: high accuracy for Telugu/Hindi/English)
        groq_key = os.getenv("GROQ_API_KEY")
        groq_error = None
        if groq_key:
            try:
                client = Groq(api_key=groq_key)
                with open(audio_path, "rb") as file:
                    transcription = client.audio.transcriptions.create(
                        file=(Path(audio_path).name, file.read()),
                        model="whisper-large-v3",
                        language=language if language and language != "auto" else None,
                        response_format="text"
                    )
                if isinstance(transcription, str):
                    return transcription.strip()
                return getattr(transcription, "text", str(transcription)).strip()
            except Exception as e:
                groq_error = e
                print(f"Groq Whisper transcription notice: {e}")

        # Secondary fallback: local whisper binary if installed on system host
        if self.binary:
            try:
                cmd = [self.binary, "-m", f"models/ggml-{self.model}.bin", "-f", audio_path]
                if language and language != "auto":
                    cmd.extend(["-l", language])
                cmd.extend(["-oj", "--no-timestamps"])  # JSON output

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                if result.returncode == 0:
                    try:
                        output = json.loads(result.stdout)
                        return output.get("text", "").strip()
                    except json.JSONDecodeError:
                        return result.stdout.strip()
                else:
                    print(f"Local whisper binary returned code {result.returncode}: {result.stderr}")
            except Exception as e:
                print(f"Local whisper fallback execution failed: {e}")

        if groq_error:
            raise RuntimeError(f"Audio transcription failed via Groq Whisper API: {groq_error}")
        raise RuntimeError("Audio transcription failed: GROQ_API_KEY is not configured and no local whisper binary was found.")

    async def transcribe_async(self, audio_path: str, language: Optional[str] = None) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.transcribe, audio_path, language)


# ===========================================
# Language Detection
# ===========================================
def detect_language(text: str) -> Language:
    """Detect language from transcribed text."""
    text_lower = text.lower()
    scores = {lang: 0 for lang in Language}

    for lang, keywords in LANGUAGE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                scores[lang] += 1

    # Default to Telugu for our target region
    detected = max(scores, key=scores.get)
    return detected if scores[detected] > 0 else Language.TELUGU


def detect_state(text: str, language: Language) -> Optional[State]:
    """Detect state from transcribed text."""
    text_lower = text.lower()

    for state, keywords in STATE_KEYWORDS.items():
        for kw in keywords:
            if kw in text_lower:
                return state

    return None


# ===========================================
# Groq Structured Extraction
# ===========================================
EXTRACTION_PROMPT = """You are an expert at extracting structured citizen profile information from voice transcripts in Indian languages (Telugu, Hindi, English).

Extract the following fields from the user's speech. Return ONLY valid JSON.

Fields to extract (all optional - use null if not mentioned):
- name: string
- age: integer
- gender: "male" | "female" | "other"
- marital_status: "married" | "unmarried" | "widowed" | "divorced"
- state: "AP" | "TS" | "OTHER" (Andhra Pradesh, Telangana, Other)
- district: string
- village: string
- caste_category: "general" | "sc" | "st" | "obc" | "bc" | "minority"
- annual_income: integer (in rupees)
- land_holding_ha: float (hectares)
- land_holding_acres: float (acres)
- has_aadhaar: boolean
- has_bank_account: boolean
- has_ration_card: boolean
- has_land_record: boolean
- occupation: string
- is_farmer: boolean
- is_street_vendor: boolean
- is_shg_member: boolean
- disability: boolean
- minority: boolean

Rules:
- If user says "2 acres" → land_holding_acres: 2, land_holding_ha: 0.81
- If user says "2 eker" / "2 ఎకర్" → same
- If user says "Aadhaar undi" / "आधार है" / "have Aadhaar" → has_aadhaar: true
- If user says "bank khata" / "బ్యాంకు ఖాతా" / "bank account" → has_bank_account: true
- If user says "ration card" / "రేషనీ కార్డు" → has_ration_card: true
- If user says "land record" / "1B" / "పహాని" / "webland" → has_land_record: true
- If user says "farmer" / "రైతు" / "किसान" → is_farmer: true
- If user says "street vendor" / "వేడీ వ్యాపారి" / "स्ट्रीट वेंडर" → is_street_vendor: true
- If user says "SHG" / "self help group" / "దాల్" / "समूह" → is_shg_member: true
- If user says "widow" / "విధవ" / "विधवा" → marital_status: "widowed"
- If user says "disabled" / "దివ్యాంగ" / "दिव्यांग" → disability: true

User speech: "{transcript}"

Return JSON only:"""


class GroqExtractor:
    """Extracts structured profile using Groq LLM."""

    def __init__(self, api_key: str = GROQ_API_KEY, model: str = GROQ_MODEL):
        self.client = Groq(api_key=api_key)
        self.model = model

    def extract(self, transcript: str, language: Language) -> UserProfile:
        prompt = EXTRACTION_PROMPT.format(transcript=transcript)

        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You output ONLY valid JSON. No markdown, no explanation."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=500,
            response_format={"type": "json_object"},
        )

        data = json.loads(response.choices[0].message.content)
        data["language"] = language.value
        return UserProfile(**data)

    async def extract_async(self, transcript: str, language: Language) -> UserProfile:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.extract, transcript, language)


# ===========================================
# Piper TTS
# ===========================================
class PiperTTS:
    """Text-to-speech using Piper (local, free)."""

    def __init__(self):
        self.voices_dir = Path.home() / ".local" / "share" / "piper" / "voices"
        self._ensure_voices()

    def _ensure_voices(self):
        """Download voice models if not present."""
        self.voices_dir.mkdir(parents=True, exist_ok=True)
        # Piper downloads automatically on first use

    def synthesize(self, text: str, language: Language, output_path: str) -> str:
        """Generate speech audio file."""
        voice = PIPER_VOICES.get(language, PIPER_VOICES[Language.ENGLISH])

        cmd = [
            "piper",
            "--model", voice,
            "--output_file", output_path,
        ]

        try:
            # Write text to stdin
            result = subprocess.run(cmd, input=text.encode(), capture_output=True, timeout=30)
            if result.returncode == 0:
                return output_path
        except Exception:
            pass

        # Fallback to gTTS (already installed)
        try:
            from gtts import gTTS
            lang_code = "te" if language == Language.TELUGU else ("hi" if language == Language.HINDI else "en")
            tts = gTTS(text=text, lang=lang_code)
            tts.save(output_path)
            return output_path
        except Exception as e:
            print(f"TTS synthesis fallback failed: {e}")
            if os.path.exists(output_path) and os.path.getsize(output_path) == 0:
                try:
                    os.remove(output_path)
                except Exception:
                    pass
            return output_path

    async def synthesize_async(self, text: str, language: Language, output_path: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.synthesize, text, language, output_path)


# ===========================================
# Main Voice Pipeline
# ===========================================
class VoicePipeline:
    """Complete voice pipeline: STT → Extract → TTS."""

    def __init__(self):
        self.stt = WhisperSTT()
        self.extractor = GroqExtractor()
        self.tts = PiperTTS()

    def process_audio(self, audio_path: str, language_hint: Optional[Language] = None) -> ExtractionResult:
        """Process audio file → structured profile."""
        # Step 1: Transcribe
        whisper_lang = language_hint.value if language_hint else "auto"
        transcript = self.stt.transcribe(audio_path, whisper_lang)

        if not transcript:
            raise ValueError("No speech detected in audio")

        # Step 2: Detect language
        language = detect_language(transcript)

        # Step 3: Detect state
        state = detect_state(transcript, language)

        # Step 4: Extract structured profile
        profile = self.extractor.extract(transcript, language)

        # Override state if detected from speech
        if state:
            profile.state = state

        return ExtractionResult(
            profile=profile,
            raw_text=transcript,
            language=language,
            detected_state=state,
        )

    async def process_audio_async(self, audio_path: str, language_hint: Optional[Language] = None) -> ExtractionResult:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.process_audio, audio_path, language_hint)

    def generate_response_audio(self, text: str, language: Language, output_path: str) -> str:
        """Generate TTS audio for response."""
        return self.tts.synthesize(text, language, output_path)

    async def generate_response_audio_async(self, text: str, language: Language, output_path: str) -> str:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self.generate_response_audio, text, language, output_path)


# ===========================================
# Convenience Functions
# ===========================================
def process_voice_input(audio_path: str, language_hint: Optional[Language] = None) -> ExtractionResult:
    """One-shot voice processing."""
    pipeline = VoicePipeline()
    return pipeline.process_audio(audio_path, language_hint)


def generate_voice_response(text: str, language: Language, output_path: str) -> str:
    """One-shot TTS generation."""
    pipeline = VoicePipeline()
    return pipeline.generate_response_audio(text, language, output_path)


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python voice_pipeline.py <audio_file> [--lang te|hi|en]")
        sys.exit(1)

    audio_file = sys.argv[1]
    lang_hint = None
    if "--lang" in sys.argv:
        idx = sys.argv.index("--lang")
        lang_hint = Language(sys.argv[idx + 1])

    result = process_voice_input(audio_file, lang_hint)
    print(json.dumps(result.profile.model_dump(), indent=2, ensure_ascii=False))