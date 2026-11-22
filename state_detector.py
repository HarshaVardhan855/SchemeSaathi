"""
State and Language Detection for SchemeSaathi.
Infers user's state (AP/TS/Other) from voice transcript and language.
"""
from typing import Optional, Dict, List
from dataclasses import dataclass

from models import Language, State


# ===========================================
# State Keywords (Telugu script + transliteration)
# ===========================================
AP_KEYWORDS = [
    # Telugu script
    "ఆంధ్ర", "ఆంధ్రప్రదేశ్", "అనంతపురం", "కడప", "చిత్తూరు", "గుంటూరు",
    "కృష్ణ", "ప్రకాశం", "శ్రీకాకుళం", "విశాఖపట్నం", "విజయవాడ",
    "తిరుపతి", "నెల్లూరు", "కాకినాడ", "రాజమండ్రి", "ఎలూరు",
    "మచిలీపట్నం", "ఎస్‌పీఎస్", "వైజాగ్",
    # Transliteration
    "andhra", "andhra pradesh", "anantapur", "kadapa", "chittoor", "guntur",
    "krishna", "prakasam", "srikakulam", "visakhapatnam", "vijayawada",
    "tirupati", "nellore", "kakinada", "rajahmundry", "eluru",
    "machilipatnam", "ap",
]

TS_KEYWORDS = [
    # Telugu script
    "తెలంగాణ", "హైదరాబాద్", "వరంగల్", "నిజామాబాద్", "కరీంనగర్",
    "ఖమ్మం", "నల్గొండ", "మహబూబ్‌నగర్", "అదిలాబాద్", "మెదక్",
    "రంగారెడ్డి", "జగ الألماني", "భూపాల్", "మధిరి", "సిద్దిపేట",
    "జయశంకర్", "ముళుగు", "నారాయణపేట", "కమారెడ్డి", "సంగారెడ్డి",
    # Transliteration
    "telangana", "hyderabad", "warangal", "nizamabad", "karimnagar",
    "khammam", "nalgonda", "mahbubnagar", "adilabad", "medak",
    "rangareddy", "jagitial", "bhupalpally", "siddipet",
    "jayashankar", "mulugu", "narayanpet", "kamareddy", "sangareddy",
    "ts", "tg",
]

# Central government / other states
OTHER_KEYWORDS = [
    "కర్నాటక", "కర్నాటక", "తమిళనాడు", "తమిళనాడు", "మహారాష్ట్ర",
    "కర్ణాటక", "karnataka", "tamil nadu", "maharashtra", "gujarat",
    "rajasthan", "madhya pradesh", "uttar pradesh", "bihar", "west bengal",
    "odisha", "kerala", "punjab", "haryana", "delhi", "central",
]


@dataclass
class DetectionResult:
    state: State
    confidence: float
    matched_keywords: List[str]
    language: Language


# ===========================================
# Detection Functions
# ===========================================
def detect_state_from_text(text: str, language: Language) -> DetectionResult:
    """
    Detect state from transcribed text.
    Returns DetectionResult with state, confidence, and matched keywords.
    """
    text_lower = text.lower()
    ap_matches = []
    ts_matches = []
    other_matches = []

    # Check AP keywords
    for kw in AP_KEYWORDS:
        if kw.lower() in text_lower:
            ap_matches.append(kw)

    # Check TS keywords
    for kw in TS_KEYWORDS:
        if kw.lower() in text_lower:
            ts_matches.append(kw)

    # Check other state keywords
    for kw in OTHER_KEYWORDS:
        if kw.lower() in text_lower:
            other_matches.append(kw)

    # Determine state
    if ap_matches and not ts_matches:
        return DetectionResult(
            state=State.ANDHRA_PRADESH,
            confidence=min(0.9, 0.5 + 0.1 * len(ap_matches)),
            matched_keywords=ap_matches,
            language=language,
        )
    elif ts_matches and not ap_matches:
        return DetectionResult(
            state=State.TELANGANA,
            confidence=min(0.9, 0.5 + 0.1 * len(ts_matches)),
            matched_keywords=ts_matches,
            language=language,
        )
    elif ap_matches and ts_matches:
        # Both mentioned - check which appears first
        ap_pos = min(text_lower.find(kw.lower()) for kw in ap_matches)
        ts_pos = min(text_lower.find(kw.lower()) for kw in ts_matches)
        if ap_pos < ts_pos:
            return DetectionResult(
                state=State.ANDHRA_PRADESH,
                confidence=0.7,
                matched_keywords=ap_matches,
                language=language,
            )
        else:
            return DetectionResult(
                state=State.TELANGANA,
                confidence=0.7,
                matched_keywords=ts_matches,
                language=language,
            )
    elif other_matches:
        return DetectionResult(
            state=State.OTHER,
            confidence=0.6,
            matched_keywords=other_matches,
            language=language,
        )
    else:
        # Default based on language
        if language == Language.TELUGU:
            # Telugu speaker - could be AP or TS, default to AP
            return DetectionResult(
                state=State.ANDHRA_PRADESH,
                confidence=0.3,
                matched_keywords=[],
                language=language,
            )
        else:
            return DetectionResult(
                state=State.OTHER,
                confidence=0.3,
                matched_keywords=[],
                language=language,
            )


def detect_state_from_language(language: Language) -> State:
    """Fallback state detection based on language alone."""
    if language == Language.TELUGU:
        return State.ANDHRA_PRADESH  # Default for Telugu
    elif language == Language.HINDI:
        return State.OTHER
    else:
        return State.OTHER


def get_applicable_jurisdictions(state: State) -> List[str]:
    """Get list of scheme jurisdictions applicable for a state."""
    jurisdictions = ["central"]  # Always include central

    if state == State.ANDHRA_PRADESH:
        jurisdictions.append("andhra_pradesh")
    elif state == State.TELANGANA:
        jurisdictions.append("telangana")
    # For OTHER, only central schemes

    return jurisdictions


def format_state_prompt(state: State, language: Language) -> str:
    """Format state confirmation prompt in user's language."""
    state_names = {
        Language.TELUGU: {
            State.ANDHRA_PRADESH: "ఆంధ్రప్రదేశ్",
            State.TELANGANA: "తెలంగాణ",
            State.OTHER: "ఇతర రాష్ట్రము",
        },
        Language.HINDI: {
            State.ANDHRA_PRADESH: "आंध्र प्रदेश",
            State.TELANGANA: "तेलंगाना",
            State.OTHER: "अन्य राज्य",
        },
        Language.ENGLISH: {
            State.ANDHRA_PRADESH: "Andhra Pradesh",
            State.TELANGANA: "Telangana",
            State.OTHER: "Other State",
        },
    }
    return state_names.get(language, state_names[Language.ENGLISH]).get(state, "Unknown")


if __name__ == "__main__":
    # Test
    test_cases = [
        ("నా గ్రామం అనంతపురం జిల్లా లో ఉంది", Language.TELUGU),
        ("I live in Hyderabad, Telangana", Language.ENGLISH),
        ("मेरा गांव वारंगल जिले में है", Language.HINDI),
        ("నా పేరు రమేష్. 2 ఎకర్ భూమి.", Language.TELUGU),
        ("I am a farmer from Karnataka", Language.ENGLISH),
    ]

    for text, lang in test_cases:
        result = detect_state_from_text(text, lang)
        print(f"Text: {text}")
        print(f"  Language: {lang.value}")
        print(f"  State: {result.state.value} (confidence: {result.confidence:.1f})")
        print(f"  Keywords: {result.matched_keywords}")
        print(f"  Jurisdictions: {get_applicable_jurisdictions(result.state)}")
        print()