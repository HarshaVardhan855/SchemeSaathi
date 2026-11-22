"""
Pydantic models for SchemeSaathi data structures.
"""
from typing import Optional, List, Literal, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class Language(str, Enum):
    TELUGU = "te"
    HINDI = "hi"
    ENGLISH = "en"


class State(str, Enum):
    ANDHRA_PRADESH = "AP"
    TELANGANA = "TS"
    OTHER = "OTHER"


class SchemeJurisdiction(str, Enum):
    CENTRAL = "central"
    ANDHRA_PRADESH = "andhra_pradesh"
    TELANGANA = "telangana"


class UserProfile(BaseModel):
    """Extracted user profile from voice conversation."""
    name: Optional[str] = None
    age: Optional[int] = None
    gender: Optional[Literal["male", "female", "other"]] = None
    marital_status: Optional[Literal["married", "unmarried", "widowed", "divorced"]] = None
    state: Optional[State] = None
    district: Optional[str] = None
    village: Optional[str] = None
    caste_category: Optional[Literal["general", "sc", "st", "obc", "bc", "minority"]] = None
    annual_income: Optional[int] = None
    land_holding_ha: Optional[float] = None  # in hectares
    land_holding_acres: Optional[float] = None
    has_aadhaar: Optional[bool] = None
    has_bank_account: Optional[bool] = None
    has_ration_card: Optional[bool] = None
    has_land_record: Optional[bool] = None
    occupation: Optional[str] = None
    is_farmer: Optional[bool] = None
    is_street_vendor: Optional[bool] = None
    is_shg_member: Optional[bool] = None
    disability: Optional[bool] = None
    minority: Optional[bool] = None
    is_govt_employee: Optional[bool] = None   # disqualifies many pension/welfare schemes
    language: Language = Language.TELUGU

    def to_dict(self) -> Dict[str, Any]:
        return {k: v for k, v in self.model_dump().items() if v is not None}


class SchemeEligibility(BaseModel):
    """Eligibility result for a single scheme."""
    scheme_id: str
    scheme_name: str
    jurisdiction: SchemeJurisdiction
    eligible: bool
    confidence: float = Field(ge=0.0, le=1.0)
    monthly_amount: Optional[str] = None  # e.g., "₹3,000/month"
    annual_amount: Optional[str] = None   # e.g., "₹6,000/year"
    one_time_amount: Optional[str] = None
    missing_documents: List[str] = Field(default_factory=list)
    next_actions: List[str] = Field(default_factory=list)
    application_url: Optional[str] = None
    form_fields: List[str] = Field(default_factory=list)
    benefit_summary: str = ""
    exclusion_reasons: List[str] = Field(default_factory=list)

    def to_display_dict(self, language: Language) -> Dict[str, Any]:
        """Format for display in user's language."""
        return {
            "scheme_name": self.scheme_name,
            "eligible": "YES" if self.eligible else "NO",
            "confidence": f"{int(self.confidence * 100)}%",
            "benefit": self.benefit_summary,
            "missing_docs": self.missing_documents,
            "next_steps": self.next_actions,
            "apply_url": self.application_url,
        }


class SchemeRule(BaseModel):
    """Structured scheme rules for RAG."""
    scheme_id: str
    scheme_name: str
    jurisdiction: SchemeJurisdiction
    department: str
    official_portal: str
    guidelines_pdf: Optional[str] = None
    myscheme_url: Optional[str] = None

    # Eligibility rules as structured lists
    must_have_all: List[str] = Field(default_factory=list)
    must_not_have_any: List[str] = Field(default_factory=list)
    conditional_rules: List[str] = Field(default_factory=list)

    # Documents
    required_documents: List[str] = Field(default_factory=list)

    # Application
    online_application_url: Optional[str] = None
    offline_application: Optional[str] = None
    key_form_fields: List[str] = Field(default_factory=list)

    # Benefits
    benefit_amount: Optional[str] = None
    benefit_frequency: Optional[str] = None  # monthly, quarterly, annual, one-time
    benefit_mode: Optional[str] = None  # DBT, cheque, direct

    # FAQ
    faq: List[Dict[str, str]] = Field(default_factory=list)

    # Metadata
    source_citations: List[str] = Field(default_factory=list)
    last_verified: Optional[str] = None
    auto_fill_feasible: bool = False


class VoiceResponse(BaseModel):
    """Structured voice response to user."""
    language: Language
    text: str
    audio_path: Optional[str] = None
    eligibility_results: List[SchemeEligibility] = Field(default_factory=list)
    suggested_actions: List[str] = Field(default_factory=list)
    session_state: Dict[str, Any] = Field(default_factory=dict)


class FormFillResult(BaseModel):
    """Result of Playwright form automation."""
    success: bool
    scheme_id: str
    screenshots: List[str] = Field(default_factory=list)
    filled_pdf_path: Optional[str] = None
    error_message: Optional[str] = None
    fields_filled: List[str] = Field(default_factory=list)