"""
Streamlit Demo App for SchemeSaathi.
Voice-first scheme eligibility checker with form filling and PDF generation.
"""
import os
import tempfile
import base64
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv
load_dotenv()

import streamlit as st

from models import UserProfile, Language, State, SchemeEligibility
from voice_pipeline import VoicePipeline, process_voice_input, generate_voice_response
from state_detector import detect_state_from_text, get_applicable_jurisdictions
from eligibility_rag import get_rag, initialize_rag
from playwright_fill import fill_pm_kisan_form, SchemeFormFiller
from pdf_generator import generate_filled_form_pdf, generate_checklist_pdf
from whatsapp_sender import get_sender, MockWhatsAppSender


# ===========================================
# Page Configuration
# ===========================================
st.set_page_config(
    page_title="SchemeSaathi — Scheme Eligibility Assistant",
    page_icon="🌾",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        background: linear-gradient(90deg, #1B5E20 0%, #2E7D32 100%);
        padding: 1.5rem;
        border-radius: 10px;
        color: white;
        margin-bottom: 2rem;
    }
    .scheme-card {
        border: 1px solid #e0e0e0;
        border-radius: 8px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: #fafafa;
    }
    .eligible { border-left: 4px solid #4CAF50; }
    .not-eligible { border-left: 4px solid #f44336; }
    .stAudio { margin: 1rem 0; }
    .voice-button {
        background: #1B5E20;
        color: white;
        border: none;
        padding: 0.5rem 1rem;
        border-radius: 5px;
        cursor: pointer;
    }
</style>
""", unsafe_allow_html=True)


# ===========================================
# Session State Initialization
# ===========================================
if "profile" not in st.session_state:
    st.session_state.profile = None
if "eligibilities" not in st.session_state:
    st.session_state.eligibilities = []
if "voice_response" not in st.session_state:
    st.session_state.voice_response = None
if "audio_path" not in st.session_state:
    st.session_state.audio_path = None
if "form_result" not in st.session_state:
    st.session_state.form_result = None
if "pdf_paths" not in st.session_state:
    st.session_state.pdf_paths = []


# ===========================================
# Helper Functions
# ===========================================
@st.cache_resource
def load_rag():
    """Load and initialize RAG engine."""
    rag = get_rag()
    rag.initialize()
    return rag


def save_audio_file(audio_data, suffix: str = ".wav") -> str:
    """Save audio bytes or UploadedFile to temp file."""
    if hasattr(audio_data, "getvalue"):
        data = audio_data.getvalue()
    elif hasattr(audio_data, "read"):
        if hasattr(audio_data, "seek"):
            audio_data.seek(0)
        data = audio_data.read()
    elif isinstance(audio_data, (bytes, bytearray)):
        data = audio_data
    else:
        data = bytes(audio_data)

    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as f:
        f.write(data)
        return f.name


def get_audio_base64(audio_path: str) -> str:
    """Convert audio file to base64 for HTML audio player."""
    with open(audio_path, "rb") as f:
        return base64.b64encode(f.read()).decode()


def display_scheme_card(eligibility: SchemeEligibility, language: Language):
    """Display a scheme eligibility card."""
    eligible_class = "eligible" if eligibility.eligible else "not-eligible"
    status_icon = "✅" if eligibility.eligible else "❌"
    status_text = "Eligible" if eligibility.eligible else "Not Eligible"

    with st.container():
        st.markdown(f"""
        <div class="scheme-card {eligible_class}">
            <h4>{status_icon} {eligibility.scheme_name} ({eligibility.jurisdiction.value})</h4>
            <p><strong>Status:</strong> {status_text} ({int(eligibility.confidence * 100)}% confidence)</p>
            <p><strong>Benefit:</strong> {eligibility.benefit_summary}</p>
        </div>
        """, unsafe_allow_html=True)

        if eligibility.eligible:
            col1, col2 = st.columns(2)
            with col1:
                if eligibility.missing_documents:
                    st.write("**📄 Missing Documents:**")
                    for doc in eligibility.missing_documents:
                        st.write(f"• {doc}")
            with col2:
                if eligibility.next_actions:
                    st.write("**➡️ Next Steps:**")
                    for action in eligibility.next_actions:
                        st.write(f"• {action}")

            if eligibility.application_url:
                st.link_button("🌐 Apply Online", eligibility.application_url)

            # Form fill button for supported schemes
            if eligibility.scheme_id in ["pm_kisan"]:
                if st.button(f"🤖 Auto-fill {eligibility.scheme_name} Form", key=f"fill_{eligibility.scheme_id}"):
                    with st.spinner("Filling form..."):
                        import asyncio
                        result = asyncio.run(fill_pm_kisan_form(st.session_state.profile))
                        st.session_state.form_result = result
                        if result.success:
                            st.success(f"Form filled! Fields completed: {', '.join(result.fields_filled)}")
                            if result.screenshots:
                                st.image(result.screenshots[0], caption="Form Screenshot")
                        else:
                            st.error(f"Form fill failed: {result.error_message}")

        if eligibility.exclusion_reasons:
            st.write("**❌ Reasons:**")
            for reason in eligibility.exclusion_reasons:
                st.write(f"• {reason}")

        st.divider()


# ===========================================
# Main App
# ===========================================
def main():
    # Header
    st.markdown("""
    <div class="main-header">
        <h1>🌾 SchemeSaathi</h1>
        <p>Voice-First Government Scheme Eligibility Assistant</p>
        <p><small>Speak in Telugu, Hindi, or English → Get eligible schemes → Auto-fill forms → Receive on WhatsApp</small></p>
    </div>
    """, unsafe_allow_html=True)

    # Sidebar: Language & State Selection
    with st.sidebar:
        st.header("⚙️ Settings")

        # Language selection
        lang_options = {
            "Telugu (తెలుగు)": Language.TELUGU,
            "Hindi (हिंदी)": Language.HINDI,
            "English": Language.ENGLISH,
        }
        selected_lang_label = st.selectbox(
            "Language / భాష / भाषा",
            list(lang_options.keys()),
            index=0,
        )
        language = lang_options[selected_lang_label]

        # State selection (optional override)
        state_options = {
            "Auto-detect from speech": None,
            "Andhra Pradesh": State.ANDHRA_PRADESH,
            "Telangana": State.TELANGANA,
            "Other / Central Only": State.OTHER,
        }
        selected_state_label = st.selectbox(
            "State / రాష్ట్ర / राज्य",
            list(state_options.keys()),
            index=0,
        )
        manual_state = state_options[selected_state_label]

        st.divider()

        # WhatsApp Settings
        st.subheader("📱 WhatsApp Delivery")
        whatsapp_number = st.text_input("Phone Number (with country code)", placeholder="+919876543210")
        use_mock_whatsapp = st.checkbox("Use Mock Sender (for demo)", value=True)

        st.divider()

        # System Status
        st.subheader("🔧 System Status")
        if st.button("Initialize RAG Engine"):
            with st.spinner("Loading schemes..."):
                rag = load_rag()
                st.success(f"Loaded {len(rag.scheme_rules)} schemes")

        if st.button("Clear Session"):
            for key in ["profile", "eligibilities", "voice_response", "audio_path", "form_result", "pdf_paths"]:
                st.session_state[key] = None if key != "pdf_paths" else []
            st.rerun()

    # Main Content Tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "🎤 Voice Input",
        "📋 Eligibility Results",
        "🤖 Form Filling",
        "📄 Download & Share"
    ])

    # ===========================================
    # Tab 1: Voice Input
    # ===========================================
    with tab1:
        st.header("Speak Your Details")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("""
            **Instructions:**
            1. Click "Record Audio" below
            2. Speak clearly in your selected language
            3. Include: Name, Age, State, Land size, Aadhaar/Bank status
            4. Click "Process" to analyze

            **Example (Telugu):**
            > "నా పేరు రమేశ్. వయస్సు 45. అనంతపురం జిల్లా. 2 ఎకర్ భూమి. ఆధార్ ఉంది. బంకు ఖాతా ఉంది."

            **Example (Hindi):**
            > "मेरा नाम रमेश है। उम्र 45। अनंतपुर जिला। 2 एकड़ जमीन। आधार है। बैंक खाता है।"

            **Example (English):**
            > "My name is Ramesh. Age 45. Anantapur district. 2 acres land. Have Aadhaar and bank account."
            """)

            # Audio recorder
            audio_bytes = st.audio_input("🎤 Record your details", key="audio_recorder")

            if audio_bytes:
                st.audio(audio_bytes, format="audio/wav")

                if st.button("🔍 Process Voice Input", type="primary", use_container_width=True):
                    with st.spinner("Processing voice..."):
                        # Save audio to temp file
                        audio_path = save_audio_file(audio_bytes)

                        try:
                            # Process through voice pipeline
                            lang_hint = language if language != Language.ENGLISH else None
                            result = process_voice_input(audio_path, lang_hint)

                            # Override state if manually selected
                            if manual_state:
                                result.profile.state = manual_state

                            # Store in session
                            st.session_state.profile = result.profile
                            st.session_state.voice_response = result

                            # Run eligibility check
                            rag = load_rag()
                            eligibilities = rag.evaluate_all(result.profile)
                            st.session_state.eligibilities = eligibilities

                            # Generate voice response
                            voice_resp = rag.generate_voice_response(result.profile, eligibilities)
                            st.session_state.voice_response = voice_resp

                            # Generate TTS audio
                            tts_path = tempfile.mktemp(suffix=".wav")
                            generate_voice_response(voice_resp.text, language, tts_path)
                            st.session_state.audio_path = tts_path

                            st.success("✅ Analysis complete! Check the Eligibility Results tab.")
                            st.rerun()

                        except Exception as e:
                            st.error(f"Error processing audio: {e}")
                        finally:
                            # Cleanup temp audio
                            try:
                                os.unlink(audio_path)
                            except:
                                pass

        with col2:
            st.subheader("📝 Manual Entry (Fallback)")
            st.caption("If voice doesn't work, enter details manually:")

            with st.form("manual_entry"):
                m_name = st.text_input("Name")
                m_age = st.number_input("Age", 18, 100, 45)
                m_gender = st.selectbox("Gender", ["male", "female", "other"])
                m_state = st.selectbox("State", ["AP", "TS", "OTHER"])
                m_district = st.text_input("District")
                m_village = st.text_input("Village")
                m_caste = st.selectbox("Caste", ["general", "sc", "st", "obc", "bc", "minority"])
                m_income = st.number_input("Annual Income (₹)", 0, 10000000, 80000)
                m_land = st.number_input("Land (acres)", 0.0, 100.0, 2.0)
                m_aadhaar = st.checkbox("Has Aadhaar")
                m_bank = st.checkbox("Has Bank Account")
                m_ration = st.checkbox("Has Ration Card")
                m_land_rec = st.checkbox("Has Land Record")
                m_farmer = st.checkbox("Is Farmer")
                m_vendor = st.checkbox("Is Street Vendor")
                m_shg = st.checkbox("Is SHG Member")

                if st.form_submit_button("Check Eligibility"):
                    profile = UserProfile(
                        name=m_name,
                        age=m_age,
                        gender=m_gender,
                        state=State(m_state),
                        district=m_district or None,
                        village=m_village or None,
                        caste_category=m_caste,
                        annual_income=m_income,
                        land_holding_acres=m_land,
                        has_aadhaar=m_aadhaar,
                        has_bank_account=m_bank,
                        has_ration_card=m_ration,
                        has_land_record=m_land_rec,
                        is_farmer=m_farmer,
                        is_street_vendor=m_vendor,
                        is_shg_member=m_shg,
                        language=language,
                    )
                    st.session_state.profile = profile

                    rag = load_rag()
                    eligibilities = rag.evaluate_all(profile)
                    st.session_state.eligibilities = eligibilities

                    voice_resp = rag.generate_voice_response(profile, eligibilities)
                    st.session_state.voice_response = voice_resp

                    tts_path = tempfile.mktemp(suffix=".wav")
                    generate_voice_response(voice_resp.text, language, tts_path)
                    st.session_state.audio_path = tts_path

                    st.success("✅ Eligibility checked!")
                    st.rerun()

    # ===========================================
    # Tab 2: Eligibility Results
    # ===========================================
    with tab2:
        st.header("Your Eligible Schemes")

        if st.session_state.profile is None:
            st.info("👈 Go to **Voice Input** tab and speak your details first.")
        else:
            profile = st.session_state.profile

            # Profile Summary
            with st.expander("👤 Your Profile", expanded=True):
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.write(f"**Name:** {profile.name or '—'}")
                    st.write(f"**Age:** {profile.age or '—'}")
                    st.write(f"**Gender:** {profile.gender or '—'}")
                with col2:
                    st.write(f"**State:** {profile.state.value if profile.state else '—'}")
                    st.write(f"**District:** {profile.district or '—'}")
                    st.write(f"**Village:** {profile.village or '—'}")
                with col3:
                    st.write(f"**Caste:** {profile.caste_category or '—'}")
                    st.write(f"**Income:** ₹{profile.annual_income:,}" if profile.annual_income else "**Income:** —")
                    st.write(f"**Land:** {profile.land_holding_acres} acres" if profile.land_holding_acres else "**Land:** —")

                st.write(f"**Aadhaar:** {'✅' if profile.has_aadhaar else '❌' if profile.has_aadhaar is not None else '—'}")
                st.write(f"**Bank Account:** {'✅' if profile.has_bank_account else '❌' if profile.has_bank_account is not None else '—'}")
                st.write(f"**Ration Card:** {'✅' if profile.has_ration_card else '❌' if profile.has_ration_card is not None else '—'}")
                st.write(f"**Land Record:** {'✅' if profile.has_land_record else '❌' if profile.has_land_record is not None else '—'}")

            # Voice Response
            if st.session_state.voice_response and st.session_state.voice_response.text:
                st.subheader("🔊 Voice Response")
                st.markdown(st.session_state.voice_response.text)

                if st.session_state.audio_path and os.path.exists(st.session_state.audio_path):
                    audio_b64 = get_audio_base64(st.session_state.audio_path)
                    st.audio(st.session_state.audio_path, format="audio/wav")

            # Scheme Cards
            st.subheader("📋 Scheme Eligibility")
            if st.session_state.eligibilities:
                for elig in st.session_state.eligibilities:
                    display_scheme_card(elig, language)
            else:
                st.warning("No schemes evaluated yet.")

    # ===========================================
    # Tab 3: Form Filling
    # ===========================================
    with tab3:
        st.header("🤖 Auto-fill Application Forms")

        if st.session_state.profile is None:
            st.info("Complete voice input first to enable form filling.")
        else:
            eligible_schemes = [e for e in st.session_state.eligibilities if e.eligible]

            if not eligible_schemes:
                st.warning("No eligible schemes to fill forms for.")
            else:
                st.write("Select a scheme to auto-fill its application form:")

                for elig in eligible_schemes:
                    with st.container():
                        col1, col2 = st.columns([3, 1])
                        with col1:
                            st.write(f"**{elig.scheme_name}** ({elig.jurisdiction.value})")
                            st.caption(f"Benefit: {elig.benefit_summary}")
                        with col2:
                            if elig.scheme_id == "pm_kisan":
                                if st.button("Fill PM-KISAN Form", key=f"fill_btn_{elig.scheme_id}"):
                                    with st.spinner("Filling PM-KISAN form..."):
                                        import asyncio
                                        result = asyncio.run(fill_pm_kisan_form(st.session_state.profile))
                                        st.session_state.form_result = result

                                        if result.success:
                                            st.success(f"✅ Form filled! Fields: {', '.join(result.fields_filled)}")
                                            if result.screenshots:
                                                for i, screenshot in enumerate(result.screenshots):
                                                    st.image(screenshot, caption=f"Step {i+1}")
                                        else:
                                            st.error(f"Failed: {result.error_message}")
                            else:
                                st.button("Form filler not yet implemented", disabled=True)

                        st.divider()

                # Show last form fill result
                if st.session_state.form_result:
                    st.subheader("Last Form Fill Result")
                    result = st.session_state.form_result
                    if result.success:
                        st.success("Form filled successfully!")
                        st.write(f"**Fields completed:** {', '.join(result.fields_filled)}")
                        if result.filled_pdf_path:
                            st.write(f"**Filled PDF:** {result.filled_pdf_path}")
                    else:
                        st.error(f"Failed: {result.error_message}")

    # ===========================================
    # Tab 4: Download & Share
    # ===========================================
    with tab4:
        st.header("📄 Download & Share Results")

        if st.session_state.profile is None:
            st.info("Complete voice input first to generate documents.")
        else:
            profile = st.session_state.profile
            eligibilities = st.session_state.eligibilities

            col1, col2 = st.columns(2)

            with col1:
                st.subheader("📥 Generate PDFs")

                if st.button("Generate Filled Forms (All Eligible)", use_container_width=True):
                    with st.spinner("Generating PDFs..."):
                        pdf_paths = []
                        for elig in eligibilities:
                            if elig.eligible:
                                output_path = f"output_{elig.scheme_id}_{profile.name or 'user'}.pdf"
                                try:
                                    generate_filled_form_pdf(profile, elig, output_path, language)
                                    pdf_paths.append(output_path)
                                except Exception as e:
                                    st.error(f"Failed to generate {elig.scheme_name}: {e}")

                        if pdf_paths:
                            st.session_state.pdf_paths = pdf_paths
                            st.success(f"Generated {len(pdf_paths)} PDF(s)")

                if st.button("Generate Document Checklist", use_container_width=True):
                    with st.spinner("Generating checklist..."):
                        output_path = f"checklist_{profile.name or 'user'}.pdf"
                        try:
                            generate_checklist_pdf(profile, eligibilities, output_path, language)
                            st.session_state.pdf_paths.append(output_path)
                            st.success("Checklist generated!")
                        except Exception as e:
                            st.error(f"Failed: {e}")

            with col2:
                st.subheader("📱 Send via WhatsApp")

                whatsapp_num = st.text_input("Recipient WhatsApp Number", value=whatsapp_number, placeholder="+919876543210")

                if st.button("Send Results to WhatsApp", use_container_width=True):
                    if not whatsapp_num:
                        st.error("Enter a WhatsApp number")
                    else:
                        with st.spinner("Sending..."):
                            sender = get_sender(use_mock=True)
                            results = sender.send_eligibility_results(
                                to_number=whatsapp_num,
                                profile=profile,
                                eligibilities=eligibilities,
                                language=language,
                            )
                            success_count = sum(1 for r in results if r.success)
                            st.success(f"Sent {success_count}/{len(results)} messages (mock mode)")

            # Download Links
            if st.session_state.pdf_paths:
                st.subheader("📥 Download Generated Files")
                for pdf_path in st.session_state.pdf_paths:
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            st.download_button(
                                label=f"⬇️ {os.path.basename(pdf_path)}",
                                data=f.read(),
                                file_name=os.path.basename(pdf_path),
                                mime="application/pdf",
                            )

            # Raw JSON Export
            st.subheader("🔧 Developer Export")
            if st.button("Export Full Session as JSON"):
                export_data = {
                    "profile": st.session_state.profile.model_dump() if st.session_state.profile else None,
                    "eligibilities": [e.model_dump() for e in st.session_state.eligibilities],
                    "voice_response": st.session_state.voice_response.model_dump() if st.session_state.voice_response else None,
                    "form_result": st.session_state.form_result.model_dump() if st.session_state.form_result else None,
                }
                st.download_button(
                    label="Download JSON",
                    data=json.dumps(export_data, indent=2, ensure_ascii=False, default=str),
                    file_name="schemesaathi_session.json",
                    mime="application/json",
                )


if __name__ == "__main__":
    main()