"""
PDF Generator: Creates filled application forms and missing document checklists.
Used as fallback when Playwright automation fails or for offline use.
"""
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime
from fpdf import FPDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

from models import UserProfile, SchemeEligibility, SchemeJurisdiction, Language


# ===========================================
# Language-specific labels
# ===========================================
LABELS = {
    Language.TELUGU: {
        "application_form": "అ 풀 Tirసamma רीलెజీస్ట్రేషన్ ఫార్మ్",
        "personal_details": "వ్యక్తిగత వివరాలు",
        "scheme_details": "స్కీమ్ వివరాలు",
        "documents_required": "అవసరమైన పత్రాలు",
        "checklist": "చెక్లిస్ట్",
        "checklist_title": "పత్రాలు చեկ్లిస్ట్",
        "checklist_obtained": "లಭించినవి",
        "checklist_pending": "లేద Jagu",
        "next_steps": "తరువాత దశలు",
        "declaration": "ఘోషణ",
        "signature": "కையொప్పు",
        "date": "తేదీ",
        "generated_on": "జనరేటెడ్ ఆన్",
        "farmer_name": "రైతు పేరు",
        "aadhaar": "ఆధార్ నంబర్",
        "age": "వయస్సు",
        "gender": "లింగం",
        "state": "రాష్ట్రం",
        "district": "జిల్లా",
        "village": "గ్రామం",
        "caste": "జాతి",
        "land_area": "భూమి విస్తీర్ణం",
        "bank_account": "బ్యాంకు ఖాతా నంబర్",
        "ifsc": "IFSC కోడ్",
        "mobile": "మోబైల్ నంబర్",
        "eligible": "అర్హత-Darలు",
        "not_eligible": "అర్హత లేవు",
        "benefit": "లാഭం",
        "missing_docs": "లిప్త పత్రాలు",
    },
    Language.HINDI: {
        "application_form": "आवेदन पत्र",
        "personal_details": "व्यक्तिगत विवरण",
        "scheme_details": "योजना विवरण",
        "documents_required": "आवश्यक दस्तावेज",
        "checklist": "चेकलिस्ट",
        "checklist_title": "दस्तावेज चेकलिस्ट",
        "checklist_obtained": "प्राप्त",
        "checklist_pending": "लंबित",
        "next_steps": "अगले कदम",
        "declaration": "घोषणा",
        "signature": "हस्ताक्षर",
        "date": "तारीख",
        "generated_on": "जनरेटेड ऑन",
        "farmer_name": "किसान का नाम",
        "aadhaar": "आधार नंबर",
        "age": "उम्र",
        "gender": "लिंग",
        "state": "राज्य",
        "district": "जिला",
        "village": "गांव",
        "caste": "जाति",
        "land_area": "भूमि क्षेत्र",
        "bank_account": "बैंक खाता नंबर",
        "ifsc": "IFSC कोड",
        "mobile": "मोबाइल नंबर",
        "eligible": "पात्र",
        "not_eligible": "अपात्र",
        "benefit": "लाभ",
        "missing_docs": "छूटे दस्तावेज",
    },
    Language.ENGLISH: {
        "application_form": "Application Form",
        "personal_details": "Personal Details",
        "scheme_details": "Scheme Details",
        "documents_required": "Required Documents",
        "checklist": "Checklist",
        "checklist_title": "Documents Checklist",
        "checklist_obtained": "Obtained",
        "checklist_pending": "Pending",
        "next_steps": "Next Steps",
        "declaration": "Declaration",
        "signature": "Signature",
        "date": "Date",
        "generated_on": "Generated On",
        "farmer_name": "Farmer Name",
        "aadhaar": "Aadhaar Number",
        "age": "Age",
        "gender": "Gender",
        "state": "State",
        "district": "District",
        "village": "Village",
        "caste": "Caste Category",
        "land_area": "Land Area",
        "bank_account": "Bank Account Number",
        "ifsc": "IFSC Code",
        "mobile": "Mobile Number",
        "eligible": "Eligible",
        "not_eligible": "Not Eligible",
        "benefit": "Benefit",
        "missing_docs": "Missing Documents",
    },
}

JURISDICTION_LABELS = {
    SchemeJurisdiction.CENTRAL: {"te": "కేంద్ర సർക്കార్", "hi": "केंद्र सरकार", "en": "Central Government"},
    SchemeJurisdiction.ANDHRA_PRADESH: {"te": "ఆంధ్రప్రదేశ్ సರ್ಕార్", "hi": "आंध्र प्रदेश सरकार", "en": "Andhra Pradesh Government"},
    SchemeJurisdiction.TELANGANA: {"te": "తెలంగాణ సർക്കార్", "hi": "तेलंगाना सरकार", "en": "Telangana Government"},
}


def state_to_jurisdiction(state: Any) -> SchemeJurisdiction:
    """Convert State enum or string to SchemeJurisdiction."""
    if not state:
        return SchemeJurisdiction.CENTRAL
    val = state.value if hasattr(state, 'value') else str(state)
    val_upper = str(val).upper().strip()
    if val_upper in ["AP", "ANDHRA_PRADESH", "ANDHRA PRADESH"]:
        return SchemeJurisdiction.ANDHRA_PRADESH
    elif val_upper in ["TS", "TELANGANA"]:
        return SchemeJurisdiction.TELANGANA
    return SchemeJurisdiction.CENTRAL


def get_label(key: str, language: Language) -> str:
    """Get label in specified language."""
    return LABELS.get(language, LABELS[Language.ENGLISH]).get(key, key)


def get_jurisdiction_label(jurisdiction: SchemeJurisdiction, language: Language) -> str:
    return JURISDICTION_LABELS.get(jurisdiction, {}).get(language.value, jurisdiction.value)


# ===========================================
# PDF Generator using ReportLab (better Unicode support)
# ===========================================
class SchemePDFGenerator:
    """Generates filled application forms and checklists as PDF."""

    def __init__(self, language: Language = Language.TELUGU):
        self.language = language
        self.styles = getSampleStyleSheet()
        self._setup_custom_styles()

    def _setup_custom_styles(self):
        """Setup custom styles for PDF."""
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Title'],
            fontSize=18,
            spaceAfter=12,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold',
        ))
        self.styles.add(ParagraphStyle(
            name='SectionHeader',
            parent=self.styles['Heading2'],
            fontSize=14,
            spaceBefore=12,
            spaceAfter=6,
            fontName='Helvetica-Bold',
            textColor=colors.darkblue,
        ))
        self.styles.add(ParagraphStyle(
            name='FieldLabel',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica-Bold',
        ))
        self.styles.add(ParagraphStyle(
            name='FieldValue',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
        ))
        self.styles.add(ParagraphStyle(
            name='ChecklistItem',
            parent=self.styles['Normal'],
            fontSize=10,
            fontName='Helvetica',
            leftIndent=20,
        ))
        self.styles.add(ParagraphStyle(
            name='Footer',
            parent=self.styles['Normal'],
            fontSize=8,
            fontName='Helvetica-Oblique',
            textColor=colors.grey,
            alignment=TA_CENTER,
        ))

    def _format_value(self, value: Any) -> str:
        """Format value for display."""
        if value is None:
            return "—"
        if isinstance(value, bool):
            return get_label("eligible", self.language) if value else get_label("not_eligible", self.language)
        if isinstance(value, (list, tuple)):
            return ", ".join(str(v) for v in value)
        return str(value)

    def generate_filled_form(self, profile: UserProfile, eligibility: SchemeEligibility, output_path: str) -> str:
        """Generate a filled application form PDF."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm,
        )

        story = []

        # Title
        title = f"{get_label('application_form', self.language)} — {eligibility.scheme_name}"
        story.append(Paragraph(title, self.styles['CustomTitle']))

        # Scheme info
        story.append(Paragraph(get_label("scheme_details", self.language), self.styles['SectionHeader']))
        scheme_data = [
            [get_label("farmer_name", self.language), self._format_value(profile.name)],
            [get_label("aadhaar", self.language), self._format_value(getattr(profile, 'aadhaar', None))],
            [get_label("age", self.language), self._format_value(profile.age)],
            [get_label("gender", self.language), self._format_value(profile.gender)],
            [get_label("state", self.language), get_jurisdiction_label(state_to_jurisdiction(profile.state), self.language)],
            [get_label("district", self.language), self._format_value(profile.district)],
            [get_label("village", self.language), self._format_value(profile.village)],
            [get_label("caste", self.language), self._format_value(profile.caste_category)],
            [get_label("land_area", self.language), f"{self._format_value(profile.land_holding_acres)} acres" if profile.land_holding_acres else "—"],
            [get_label("bank_account", self.language), self._format_value(getattr(profile, 'bank_account', None))],
            [get_label("ifsc", self.language), self._format_value(getattr(profile, 'ifsc', None))],
            [get_label("mobile", self.language), self._format_value(getattr(profile, 'mobile', None))],
            ["Scheme", eligibility.scheme_name],
            ["Jurisdiction", get_jurisdiction_label(eligibility.jurisdiction, self.language)],
            [get_label("benefit", self.language), eligibility.benefit_summary],
            ["Eligible", get_label("eligible", self.language) if eligibility.eligible else get_label("not_eligible", self.language)],
        ]

        table = Table(scheme_data, colWidths=[60*mm, 120*mm])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.whitesmoke]),
        ]))
        story.append(table)
        story.append(Spacer(1, 12))

        # Required Documents
        story.append(Paragraph(get_label("documents_required", self.language), self.styles['SectionHeader']))
        docs_data = [[get_label("checklist_obtained", self.language), get_label("checklist_pending", self.language), "Document"]]
        for req_doc in (eligibility.required_documents if hasattr(eligibility, 'required_documents') else []):
            pass

        # Use missing_documents from eligibility
        for missing_doc in eligibility.missing_documents:
            docs_data.append([get_label("checklist_pending", self.language), "☐", missing_doc])

        if docs_data:
            docs_table = Table(docs_data, colWidths=[30*mm, 15*mm, 135*mm])
            docs_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('BACKGROUND', (0, 0), (-1, 0), colors.lightblue),
            ]))
            story.append(docs_table)

        story.append(Spacer(1, 20))

        # Next Steps
        if eligibility.next_actions:
            story.append(Paragraph(get_label("next_steps", self.language), self.styles['SectionHeader']))
            for i, action in enumerate(eligibility.next_actions, 1):
                story.append(Paragraph(f"{i}. {action}", self.styles['ChecklistItem']))

        story.append(Spacer(1, 30))

        # Declaration
        story.append(Paragraph(get_label("declaration", self.language), self.styles['SectionHeader']))
        decl_text = (
            "I hereby declare that the information provided above is true and correct to the best of my knowledge. "
            "I understand that false information may lead to rejection of my application and legal action."
        )
        story.append(Paragraph(decl_text, self.styles['Normal']))
        story.append(Spacer(1, 20))

        # Signature line
        sig_data = [
            [get_label("signature", self.language), "________________________", get_label("date", self.language), "________________________"],
            [get_label("farmer_name", self.language), self._format_value(profile.name), "", datetime.now().strftime("%d-%m-%Y")],
        ]
        sig_table = Table(sig_data, colWidths=[40*mm, 70*mm, 30*mm, 50*mm])
        sig_table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('LINEBELOW', (1, 0), (1, 0), 1, colors.black),
            ('LINEBELOW', (3, 0), (3, 0), 1, colors.black),
        ]))
        story.append(sig_table)

        # Footer
        story.append(Spacer(1, 30))
        footer_text = f"{get_label('generated_on', self.language)}: {datetime.now().strftime('%d-%m-%Y %H:%M')} | SchemeSaathi"
        story.append(Paragraph(footer_text, self.styles['Footer']))

        doc.build(story)
        return output_path

    def generate_checklist(self, profile: UserProfile, eligibilities: List[SchemeEligibility], output_path: str) -> str:
        """Generate a comprehensive document checklist PDF."""
        doc = SimpleDocTemplate(
            output_path,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm,
        )

        story = []

        # Title
        story.append(Paragraph(f"{get_label('checklist_title', self.language)} — {profile.name or 'Citizen'}", self.styles['CustomTitle']))
        story.append(Spacer(1, 6))
        story.append(Paragraph(f"{get_label('generated_on', self.language)}: {datetime.now().strftime('%d-%m-%Y %H:%M')}", self.styles['Footer']))
        story.append(Spacer(1, 12))

        # Personal info summary
        story.append(Paragraph(get_label("personal_details", self.language), self.styles['SectionHeader']))
        personal_data = [
            [get_label("farmer_name", self.language), self._format_value(profile.name)],
            [get_label("aadhaar", self.language), "Available" if profile.has_aadhaar else "Not Available"],
            [get_label("age", self.language), self._format_value(profile.age)],
            [get_label("state", self.language), get_jurisdiction_label(state_to_jurisdiction(profile.state), self.language)],
            [get_label("district", self.language), self._format_value(profile.district)],
        ]
        ptable = Table(personal_data, colWidths=[60*mm, 120*mm])
        ptable.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ]))
        story.append(ptable)
        story.append(Spacer(1, 12))

        # For each eligible scheme, create a section
        for elig in eligibilities:
            if not elig.eligible:
                continue

            story.append(Paragraph(f"{elig.scheme_name} ({get_jurisdiction_label(elig.jurisdiction, self.language)})", self.styles['SectionHeader']))
            story.append(Paragraph(f"{get_label('benefit', self.language)}: {elig.benefit_summary}", self.styles['Normal']))
            story.append(Spacer(1, 6))

            # Documents table
            all_docs = elig.missing_documents  # In real implementation, merge with scheme.required_documents
            if all_docs:
                docs_data = [["✓" if False else "☐", doc_name] for doc_name in all_docs]  # All pending for demo
                docs_table = Table(docs_data, colWidths=[15*mm, 165*mm])
                docs_table.setStyle(TableStyle([
                    ('FONTNAME', (0, 0), (-1, -1), 'Helvetica'),
                    ('FONTSIZE', (0, 0), (-1, -1), 10),
                    ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                    ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.whitesmoke]),
                ]))
                story.append(docs_table)

            # Next steps
            if elig.next_actions:
                story.append(Paragraph(get_label("next_steps", self.language), self.styles['Normal']))
                for action in elig.next_actions:
                    story.append(Paragraph(f"• {action}", self.styles['ChecklistItem']))

            story.append(Spacer(1, 10))

        # Ineligible schemes summary
        ineligible = [e for e in eligibilities if not e.eligible]
        if ineligible:
            story.append(PageBreak())
            story.append(Paragraph("Not Eligible Schemes", self.styles['SectionHeader']))
            for elig in ineligible:
                reason = elig.exclusion_reasons[0] if elig.exclusion_reasons else "Does not meet criteria"
                story.append(Paragraph(f"❌ {elig.scheme_name} — {reason}", self.styles['Normal']))

        doc.build(story)
        return output_path


# ===========================================
# Simple FPDF Version (for environments without reportlab)
# ===========================================
class SimplePDFGenerator:
    """Lightweight PDF generator using fpdf2."""

    def __init__(self, language: Language = Language.TELUGU):
        self.language = language
        self.pdf = FPDF()
        self.pdf.add_font('DejaVu', '', 'DejaVuSans.ttf', uni=True)
        self.pdf.add_font('DejaVu', 'B', 'DejaVuSans-Bold.ttf', uni=True)

    def _t(self, key: str) -> str:
        return get_label(key, self.language)

    def generate_simple_form(self, profile: UserProfile, eligibility: SchemeEligibility, output_path: str) -> str:
        self.pdf.add_page()
        self.pdf.set_font('DejaVu', 'B', 16)
        self.pdf.cell(0, 10, f"{self._t('application_form')} - {eligibility.scheme_name}", ln=True, align='C')
        self.pdf.ln(5)

        # Personal details
        self.pdf.set_font('DejaVu', 'B', 12)
        self.pdf.cell(0, 8, self._t('personal_details'), ln=True)
        self.pdf.set_font('DejaVu', '', 10)

        fields = [
            (self._t('farmer_name'), profile.name),
            (self._t('aadhaar'), getattr(profile, 'aadhaar', None)),
            (self._t('age'), profile.age),
            (self._t('gender'), profile.gender),
            (self._t('state'), get_jurisdiction_label(state_to_jurisdiction(profile.state), self.language)),
            (self._t('district'), profile.district),
            (self._t('village'), profile.village),
            (self._t('caste'), profile.caste_category),
            (self._t('land_area'), f"{profile.land_holding_acres} acres" if profile.land_holding_acres else "—"),
            ("Scheme", eligibility.scheme_name),
            ("Benefit", eligibility.benefit_summary),
            ("Eligible", self._t('eligible') if eligibility.eligible else self._t('not_eligible')),
        ]

        for label, value in fields:
            self.pdf.set_font('DejaVu', 'B', 10)
            self.pdf.cell(50, 7, f"{label}:", ln=False)
            self.pdf.set_font('DejaVu', '', 10)
            self.pdf.cell(0, 7, str(value) if value else "—", ln=True)

        self.pdf.ln(5)

        # Missing documents
        if eligibility.missing_documents:
            self.pdf.set_font('DejaVu', 'B', 12)
            self.pdf.cell(0, 8, self._t('missing_docs'), ln=True)
            self.pdf.set_font('DejaVu', '', 10)
            for doc in eligibility.missing_documents:
                self.pdf.cell(10, 7, "", ln=False)
                self.pdf.cell(0, 7, f"☐ {doc}", ln=True)

        self.pdf.ln(5)

        # Next steps
        if eligibility.next_actions:
            self.pdf.set_font('DejaVu', 'B', 12)
            self.pdf.cell(0, 8, self._t('next_steps'), ln=True)
            self.pdf.set_font('DejaVu', '', 10)
            for i, action in enumerate(eligibility.next_actions, 1):
                self.pdf.cell(10, 7, "", ln=False)
                self.pdf.cell(0, 7, f"{i}. {action}", ln=True)

        self.pdf.output(output_path)
        return output_path


# ===========================================
# Main Generator Factory
# ===========================================
def create_pdf_generator(language: Language = Language.TELUGU, use_reportlab: bool = True):
    """Factory to create appropriate PDF generator."""
    if use_reportlab:
        try:
            return SchemePDFGenerator(language)
        except ImportError:
            pass
    return SimplePDFGenerator(language)


def generate_filled_form_pdf(profile: UserProfile, eligibility: SchemeEligibility, output_path: str, language: Language = Language.TELUGU) -> str:
    """Generate filled form PDF."""
    generator = create_pdf_generator(language)
    if isinstance(generator, SchemePDFGenerator):
        return generator.generate_filled_form(profile, eligibility, output_path)
    else:
        return generator.generate_simple_form(profile, eligibility, output_path)


def generate_checklist_pdf(profile: UserProfile, eligibilities: List[SchemeEligibility], output_path: str, language: Language = Language.TELUGU) -> str:
    """Generate checklist PDF."""
    generator = create_pdf_generator(language)
    if isinstance(generator, SchemePDFGenerator):
        return generator.generate_checklist(profile, eligibilities, output_path)
    else:
        # Simple version - just first eligible scheme
        eligible = [e for e in eligibilities if e.eligible]
        if eligible:
            return generator.generate_simple_form(profile, eligible[0], output_path)
        return generator.generate_simple_form(profile, eligibilities[0] if eligibilities else None, output_path)


if __name__ == "__main__":
    # Test
    from models import UserProfile, SchemeEligibility, SchemeJurisdiction, Language

    test_profile = UserProfile(
        name="Ramesh",
        age=45,
        gender="male",
        state="AP",
        district="Anantapur",
        village="Kuderu",
        caste_category="bc",
        land_holding_acres=2.0,
        has_aadhaar=True,
        has_bank_account=True,
        language=Language.TELUGU,
    )

    test_eligibility = SchemeEligibility(
        scheme_id="pm_kisan",
        scheme_name="PM-KISAN",
        jurisdiction=SchemeJurisdiction.CENTRAL,
        eligible=True,
        confidence=0.95,
        annual_amount="₹6,000/year",
        benefit_summary="₹6,000 per year in 3 installments",
        missing_documents=["Land record (1B/Webland)", "Bank passbook copy"],
        next_actions=["Get 1B copy from MeeSeva", "Link Aadhaar to bank account"],
        application_url="https://pmkisan.gov.in/RegistrationForm.aspx",
    )

    # Test reportlab version
    try:
        gen = SchemePDFGenerator(Language.TELUGU)
        gen.generate_filled_form(test_profile, test_eligibility, "test_form.pdf")
        gen.generate_checklist(test_profile, [test_eligibility], "test_checklist.pdf")
        print("ReportLab PDFs generated successfully")
    except Exception as e:
        print(f"ReportLab failed: {e}")
        # Try fpdf2
        gen2 = SimplePDFGenerator(Language.TELUGU)
        gen2.generate_simple_form(test_profile, test_eligibility, "test_form_simple.pdf")
        print("Simple PDF generated successfully")