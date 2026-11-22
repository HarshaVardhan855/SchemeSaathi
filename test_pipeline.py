#!/usr/bin/env python3
"""
Test script to verify SchemeSaathi pipeline components work.
Run after installing dependencies and setting GROQ_API_KEY.
"""
import os
import sys
import asyncio
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from models import UserProfile, Language, State, SchemeJurisdiction
from voice_pipeline import process_voice_input, generate_voice_response, detect_language, detect_state
from state_detector import detect_state_from_text, get_applicable_jurisdictions
from eligibility_rag import initialize_rag, get_rag
from pdf_generator import generate_filled_form_pdf, generate_checklist_pdf
from pdf_generator import SimplePDFGenerator


def test_language_detection():
    """Test language detection from text."""
    print("🧪 Testing Language Detection...")

    test_cases = [
        ("నా పేరు రమేశ్. 2 ఎకర్ భూమి.", Language.TELUGU),
        ("मेरा नाम रमेश है। 2 एकड़ जमीन।", Language.HINDI),
        ("My name is Ramesh. 2 acres land.", Language.ENGLISH),
    ]

    for text, expected in test_cases:
        detected = detect_language(text)
        status = "✅" if detected == expected else "❌"
        print(f"  {status} '{text[:30]}...' → {detected.value} (expected {expected.value})")


def test_state_detection():
    """Test state detection from text."""
    print("\n🧪 Testing State Detection...")

    test_cases = [
        ("నా గ్రామం అనంతపురం జిల్లా లో ఉంది", Language.TELUGU, State.ANDHRA_PRADESH),
        ("I live in Hyderabad, Telangana", Language.ENGLISH, State.TELANGANA),
        ("मेरा गांव वारंगल जिले में है", Language.HINDI, State.TELANGANA),
        ("I am from Bangalore, Karnataka", Language.ENGLISH, State.OTHER),
    ]

    for text, lang, expected in test_cases:
        result = detect_state_from_text(text, lang)
        status = "✅" if result.state == expected else "❌"
        print(f"  {status} '{text[:40]}...' → {result.state.value} (conf: {result.confidence:.1f}) (expected {expected.value})")


def test_rag_initialization():
    """Test RAG engine initialization."""
    print("\n🧪 Testing RAG Initialization...")
    try:
        rag = initialize_rag()
        print(f"  ✅ Loaded {len(rag.scheme_rules)} schemes")
        for sid, rule in rag.scheme_rules.items():
            print(f"    - {sid} ({rule.jurisdiction.value})")
        return rag
    except Exception as e:
        print(f"  ❌ RAG init failed: {e}")
        return None


def test_eligibility_evaluation(rag):
    """Test eligibility evaluation with sample profiles."""
    print("\n🧪 Testing Eligibility Evaluation...")

    test_profiles = [
        UserProfile(
            name="Ramesh",
            age=45,
            gender="male",
            state=State.ANDHRA_PRADESH,
            district="Anantapur",
            village="Kuderu",
            caste_category="bc",
            annual_income=80000,
            land_holding_acres=2.0,
            has_aadhaar=True,
            has_bank_account=True,
            has_ration_card=True,
            has_land_record=True,
            is_farmer=True,
            language=Language.TELUGU,
        ),
        UserProfile(
            name="Lakshmi",
            age=50,
            gender="female",
            marital_status="widowed",
            state=State.TELANGANA,
            district="Warangal",
            caste_category="sc",
            annual_income=60000,
            has_aadhaar=True,
            has_bank_account=True,
            has_ration_card=True,
            language=Language.TELUGU,
        ),
        UserProfile(
            name="Rajesh",
            age=28,
            gender="male",
            state=State.TELANGANA,
            district="Hyderabad",
            caste_category="bc",
            annual_income=120000,
            is_street_vendor=True,
            has_aadhaar=True,
            has_bank_account=True,
            language=Language.HINDI,
        ),
    ]

    for i, profile in enumerate(test_profiles, 1):
        print(f"\n  Profile {i}: {profile.name} ({profile.state.value})")
        try:
            eligibilities = rag.evaluate_all(profile)
            eligible = [e for e in eligibilities if e.eligible]
            print(f"    Eligible for {len(eligible)}/{len(eligibilities)} schemes:")
            for e in eligible:
                print(f"      ✅ {e.scheme_name} — {e.benefit_summary}")
            for e in eligibilities:
                if not e.eligible and e.exclusion_reasons:
                    print(f"      ❌ {e.scheme_name} — {e.exclusion_reasons[0]}")
        except Exception as e:
            print(f"    ❌ Evaluation failed: {e}")


def test_voice_response_generation(rag):
    """Test voice response generation."""
    print("\n🧪 Testing Voice Response Generation...")

    profile = UserProfile(
        name="Ramesh",
        age=45,
        state=State.ANDHRA_PRADESH,
        language=Language.TELUGU,
    )

    try:
        # Create mock eligibilities
        from models import SchemeEligibility
        mock_elig = [
            SchemeEligibility(
                scheme_id="pm_kisan",
                scheme_name="PM-KISAN",
                jurisdiction=SchemeJurisdiction.CENTRAL,
                eligible=True,
                confidence=0.95,
                benefit_summary="₹6,000 per year in 3 installments",
                missing_documents=["Land record (1B)", "Bank passbook"],
                next_actions=["Get 1B from MeeSeva", "Link Aadhaar to bank"],
            ),
            SchemeEligibility(
                scheme_id="ysr_rythu_bharosa",
                scheme_name="YSR Rythu Bharosa",
                jurisdiction=SchemeJurisdiction.ANDHRA_PRADESH,
                eligible=True,
                confidence=0.90,
                benefit_summary="₹13,500 per year (incl. PM-KISAN)",
                missing_documents=["Webland seeding"],
                next_actions=["Verify Webland linkage"],
            ),
        ]

        response = rag.generate_voice_response(profile, mock_elig)
        print(f"  ✅ Generated response ({len(response.text)} chars)")
        print(f"  Language: {response.language.value}")
        print(f"  Preview: {response.text[:100]}...")

        # Test TTS
        tts_path = os.path.join(tempfile.gettempdir(), "test_response.wav")
        generate_voice_response(response.text, Language.TELUGU, tts_path)
        if os.path.exists(tts_path):
            print(f"  ✅ TTS audio generated: {tts_path}")
        else:
            print(f"  ⚠️ TTS audio not found (Piper may need first-run download)")

    except Exception as e:
        print(f"  ❌ Voice response failed: {e}")


def test_pdf_generation():
    """Test PDF generation."""
    print("\n🧪 Testing PDF Generation...")

    profile = UserProfile(
        name="Ramesh",
        age=45,
        gender="male",
        state=State.ANDHRA_PRADESH,
        district="Anantapur",
        village="Kuderu",
        caste_category="bc",
        land_holding_acres=2.0,
        has_aadhaar=True,
        has_bank_account=True,
        language=Language.TELUGU,
    )

    from models import SchemeEligibility
    elig = SchemeEligibility(
        scheme_id="pm_kisan",
        scheme_name="PM-KISAN",
        jurisdiction=SchemeJurisdiction.CENTRAL,
        eligible=True,
        confidence=0.95,
        benefit_summary="₹6,000 per year in 3 installments",
        missing_documents=["Land record (1B)", "Bank passbook copy"],
        next_actions=["Get 1B from MeeSeva", "Link Aadhaar to bank"],
    )

    try:
        tmp_dir = tempfile.gettempdir()
        # Test simple PDF generator (fpdf2)
        gen = SimplePDFGenerator(Language.TELUGU)
        fpdf_path = os.path.join(tmp_dir, "test_form.pdf")
        gen.generate_simple_form(profile, elig, fpdf_path)
        if os.path.exists(fpdf_path):
            print("  ✅ Simple PDF (fpdf2) generated")
        else:
            print("  ❌ Simple PDF failed")

        # Test reportlab version if available
        try:
            from pdf_generator import SchemePDFGenerator
            gen2 = SchemePDFGenerator(Language.TELUGU)
            rl_path = os.path.join(tmp_dir, "test_form_rl.pdf")
            gen2.generate_filled_form(profile, elig, rl_path)
            if os.path.exists(rl_path):
                print("  ✅ ReportLab PDF generated")
        except ImportError:
            print("  ⚠️ ReportLab not available, skipped")

    except Exception as e:
        print(f"  ❌ PDF generation failed: {e}")


def test_whatsapp_sender():
    """Test mock WhatsApp sender."""
    print("\n🧪 Testing WhatsApp Sender (Mock)...")

    from whatsapp_sender import MockWhatsAppSender
    from models import UserProfile, SchemeEligibility, SchemeJurisdiction, Language

    sender = MockWhatsAppSender()
    profile = UserProfile(name="Ramesh", state=State.ANDHRA_PRADESH, language=Language.TELUGU)

    elig = SchemeEligibility(
        scheme_id="pm_kisan",
        scheme_name="PM-KISAN",
        jurisdiction=SchemeJurisdiction.CENTRAL,
        eligible=True,
        confidence=0.95,
        benefit_summary="₹6,000 per year",
        missing_documents=["Land record"],
        next_actions=["Get 1B from MeeSeva"],
    )

    results = sender.send_eligibility_results(
        to_number="+919876543210",
        profile=profile,
        eligibilities=[elig],
        language=Language.TELUGU,
    )
    print(f"  ✅ Mock WhatsApp sent: {len(results)} messages")


def main():
    print("=" * 60)
    print("  SchemeSaathi Pipeline Test")
    print("=" * 60)

    # Check API key
    if not os.getenv("GROQ_API_KEY"):
        print("\n⚠️  GROQ_API_KEY not set. Some tests will be skipped.")
        print("   Get free key at: https://console.groq.com")
        print("   Export: export GROQ_API_KEY='your_key'")
        print()

    # Run tests
    test_language_detection()
    test_state_detection()

    rag = test_rag_initialization()
    if rag:
        test_eligibility_evaluation(rag)
        test_voice_response_generation(rag)

    test_pdf_generation()
    test_whatsapp_sender()

    print("\n" + "=" * 60)
    print("  Test Complete")
    print("=" * 60)
    print("\nNext steps:")
    print("  1. Set GROQ_API_KEY in .env")
    print("  2. Run: python run_demo.py --full")
    print("  3. Open http://localhost:8501")


if __name__ == "__main__":
    main()