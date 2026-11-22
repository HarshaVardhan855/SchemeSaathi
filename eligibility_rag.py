"""
Eligibility RAG Engine: Loads scheme markdowns, embeds them, and uses LLM reasoning
to determine user eligibility for each applicable scheme.
"""
import os
import re
import json
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

from sentence_transformers import SentenceTransformer
import chromadb
from groq import Groq

from models import (
    UserProfile, SchemeEligibility, SchemeRule, SchemeJurisdiction,
    Language, State, VoiceResponse
)
from state_detector import get_applicable_jurisdictions


# ===========================================
# Configuration
# ===========================================
from dotenv import load_dotenv
load_dotenv()

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
GROQ_MODEL = os.getenv("GROQ_MODEL", "qwen/qwen3.8-27b")
EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
CHROMA_PERSIST_DIR = os.getenv("CHROMA_PERSIST_DIR", "./chroma_db")
SCHEMES_DIR = Path(os.getenv("SCHEMES_DIR", "./schemes"))

# Collection names
COLLECTION_NAME = "scheme_rules"


# ===========================================
# Scheme Markdown Parser
# ===========================================
def parse_scheme_markdown(filepath: Path) -> SchemeRule:
    """Parse a scheme markdown file into SchemeRule object."""
    content = filepath.read_text(encoding="utf-8")

    # Extract jurisdiction from path
    jurisdiction_str = filepath.parent.name
    jurisdiction = SchemeJurisdiction(jurisdiction_str)

    # Parse sections using regex
    def extract_section(header: str) -> str:
        pattern = rf"## {re.escape(header)}\n(.*?)(?=\n## |\Z)"
        match = re.search(pattern, content, re.DOTALL)
        return match.group(1).strip() if match else ""

    def extract_list(section: str) -> List[str]:
        """Extract bullet points from a section."""
        items = []
        for line in section.split("\n"):
            line = line.strip()
            if line.startswith("- [ ]") or line.startswith("- [x]") or line.startswith("- "):
                # Remove checkbox syntax
                item = re.sub(r"^- \[[ x]\]\s*", "", line)
                item = re.sub(r"^-\s*", "", item)
                items.append(item.strip())
        return items

    def extract_dict_list(section: str) -> List[Dict[str, str]]:
        """Extract Q&A pairs from FAQ section."""
        items = []
        current_q = None
        for line in section.split("\n"):
            line = line.strip()
            if line.startswith("**Q:**") or line.startswith("Q:"):
                current_q = line.replace("**Q:**", "").replace("Q:", "").strip()
            elif line.startswith("**A:**") or line.startswith("A:"):
                if current_q:
                    items.append({"question": current_q, "answer": line.replace("**A:**", "").replace("A:", "").strip()})
                    current_q = None
        return items

    # Parse basic info
    basic_info = extract_section("Basic Info")
    official_portal = ""
    guidelines_pdf = ""
    myscheme_url = ""
    for line in basic_info.split("\n"):
        if "Official Portal:" in line:
            official_portal = line.split(":", 1)[1].strip()
        elif "Guidelines PDF:" in line:
            guidelines_pdf = line.split(":", 1)[1].strip()
        elif "MyScheme" in line:
            myscheme_url = line.split(":", 1)[1].strip()

    # Parse eligibility rules
    eligibility_section = extract_section("Eligibility Rules")
    must_have_all = extract_list(extract_section("Must Have (ALL required)"))
    must_not_have_any = extract_list(extract_section("Must NOT Have (ANY disqualifies)"))
    conditional_rules = extract_list(extract_section("Conditional / State-Specific"))

    # Parse documents
    docs_section = extract_section("Required Documents")
    required_documents = extract_list(docs_section)

    # Parse application
    app_section = extract_section("Application Process")
    online_url = ""
    offline = ""
    for line in app_section.split("\n"):
        if "Online URL:" in line:
            online_url = line.split(":", 1)[1].strip()
        elif "Offline:" in line:
            offline = line.split(":", 1)[1].strip()

    form_fields = extract_list(extract_section("Key Form Fields"))

    # Parse benefits
    benefit_section = extract_section("Benefit Details")
    benefit_amount = ""
    benefit_frequency = ""
    benefit_mode = ""
    for line in benefit_section.split("\n"):
        if "Amount:" in line:
            benefit_amount = line.split(":", 1)[1].strip()
        elif "Frequency:" in line:
            benefit_frequency = line.split(":", 1)[1].strip()
        elif "Mode:" in line:
            benefit_mode = line.split(":", 1)[1].strip()

    # Parse FAQ
    faq = extract_dict_list(extract_section("FAQ / Edge Cases"))

    # Parse source citations
    citations = extract_list(extract_section("Source Citations"))

    # Parse auto-fill feasible
    auto_fill = False
    if "auto_fill_feasible" in content.lower() or "Auto-fill feasible" in content:
        auto_fill = True

    # Scheme ID from filename
    scheme_id = filepath.stem

    return SchemeRule(
        scheme_id=scheme_id,
        scheme_name=scheme_id.replace("_", " ").title(),
        jurisdiction=jurisdiction,
        department="",  # Could parse from basic info
        official_portal=official_portal,
        guidelines_pdf=guidelines_pdf,
        myscheme_url=myscheme_url,
        must_have_all=must_have_all,
        must_not_have_any=must_not_have_any,
        conditional_rules=conditional_rules,
        required_documents=required_documents,
        online_application_url=online_url,
        offline_application=offline,
        key_form_fields=form_fields,
        benefit_amount=benefit_amount,
        benefit_frequency=benefit_frequency,
        benefit_mode=benefit_mode,
        faq=faq,
        source_citations=citations,
        last_verified="",
        auto_fill_feasible=auto_fill,
    )


# ===========================================
# RAG Engine
# ===========================================
class EligibilityRAG:
    """RAG engine for scheme eligibility determination."""

    def __init__(self):
        try:
            self.embedder = SentenceTransformer(EMBEDDING_MODEL)
        except Exception as e:
            print(f"SentenceTransformer embedding note: {e}")
            self.embedder = None
        self.client = chromadb.PersistentClient(path=CHROMA_PERSIST_DIR)
        self.collection = self._get_or_create_collection()
        self.groq_client = Groq(api_key=GROQ_API_KEY)
        self.scheme_rules: Dict[str, SchemeRule] = {}
        self._initialized = False

    def _get_or_create_collection(self):
        try:
            return self.client.get_collection(COLLECTION_NAME)
        except:
            return self.client.create_collection(
                name=COLLECTION_NAME,
                metadata={"hnsw:space": "cosine"}
            )

    def initialize(self, force_reload: bool = False):
        """Load all scheme markdowns and build vector index."""
        if self._initialized and not force_reload:
            return

        self.scheme_rules.clear()
        try:
            self.client.delete_collection(COLLECTION_NAME)
        except Exception:
            pass
        self.collection = self.client.create_collection(
            name=COLLECTION_NAME,
            metadata={"hnsw:space": "cosine"}
        )

        # Load all scheme files
        scheme_files = list(SCHEMES_DIR.rglob("*.md"))
        print(f"Loading {len(scheme_files)} scheme files...")

        documents = []
        metadatas = []
        ids = []

        for filepath in scheme_files:
            try:
                rule = parse_scheme_markdown(filepath)
                self.scheme_rules[rule.scheme_id] = rule

                # Create document for embedding: combine key sections
                doc_text = self._rule_to_document(rule)
                documents.append(doc_text)
                metadatas.append({
                    "scheme_id": rule.scheme_id,
                    "jurisdiction": rule.jurisdiction.value,
                    "scheme_name": rule.scheme_name,
                })
                ids.append(rule.scheme_id)
            except Exception as e:
                print(f"Error loading {filepath}: {e}")

        if documents:
            if self.embedder:
                embeddings = self.embedder.encode(documents).tolist()
                self.collection.add(
                    documents=documents,
                    embeddings=embeddings,
                    metadatas=metadatas,
                    ids=ids,
                )
            else:
                self.collection.add(
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids,
                )

        self._initialized = True
        print(f"Initialized RAG with {len(self.scheme_rules)} schemes")

    def _rule_to_document(self, rule: SchemeRule) -> str:
        """Convert scheme rule to document for embedding."""
        parts = [
            f"Scheme: {rule.scheme_name}",
            f"Jurisdiction: {rule.jurisdiction.value}",
            f"Eligibility: {'; '.join(rule.must_have_all)}",
            f"Exclusions: {'; '.join(rule.must_not_have_any)}",
            f"Conditions: {'; '.join(rule.conditional_rules)}",
            f"Documents: {'; '.join(rule.required_documents)}",
            f"Benefits: {rule.benefit_amount} ({rule.benefit_frequency}) via {rule.benefit_mode}",
        ]
        return "\n".join(parts)

    def get_applicable_schemes(self, user_profile: UserProfile) -> List[SchemeRule]:
        """Get schemes applicable to user's state."""
        jurisdictions = get_applicable_jurisdictions(user_profile.state or State.OTHER)
        return [
            rule for rule in self.scheme_rules.values()
            if rule.jurisdiction.value in jurisdictions
        ]

    def check_eligibility(self, user_profile: UserProfile, scheme: SchemeRule) -> SchemeEligibility:
        """Use LLM to determine eligibility for a specific scheme."""
        # Build context for LLM
        profile_dict = user_profile.to_dict()

        prompt = f"""You are a government scheme eligibility officer. Determine if this citizen is eligible for the scheme.

CITIZEN PROFILE:
{json.dumps(profile_dict, indent=2, ensure_ascii=False)}

SCHEME RULES:
Scheme: {scheme.scheme_name}
Jurisdiction: {scheme.jurisdiction.value}
Must Have (ALL required): {scheme.must_have_all}
Must NOT Have (ANY disqualifies): {scheme.must_not_have_any}
Conditional Rules: {scheme.conditional_rules}
Required Documents: {scheme.required_documents}
Benefits: {scheme.benefit_amount} ({scheme.benefit_frequency}) via {scheme.benefit_mode}
Application URL: {scheme.online_application_url}
Key Form Fields: {scheme.key_form_fields}

FAQ:
{json.dumps(scheme.faq, ensure_ascii=False)}

TASK: Analyze the citizen's profile against the scheme rules.
Return ONLY valid JSON with these fields:
- eligible: boolean
- confidence: float (0.0 to 1.0)
- monthly_amount: string or null
- annual_amount: string or null
- one_time_amount: string or null
- missing_documents: array of strings
- next_actions: array of strings
- application_url: string or null
- form_fields: array of strings
- benefit_summary: string
- exclusion_reasons: array of strings

Rules:
- If citizen meets ALL must_have and NONE of must_not_have → eligible: true
- If missing any must_have → eligible: false, list in missing_documents/next_actions
- If has any must_not_have → eligible: false, list in exclusion_reasons
- Confidence: 0.9+ if clear match, 0.5-0.8 if ambiguous, <0.5 if unclear
- Benefit summary: concise human-readable (e.g., "₹6,000 per year in 3 installments")
- Next actions: specific steps (e.g., "Get 1B land record from MeeSeva", "Link Aadhaar to bank account")
"""

        response = self.groq_client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise eligibility officer. Output ONLY valid JSON."},
                {"role": "user", "content": prompt},
            ],
            temperature=0.1,
            max_tokens=800,
            response_format={"type": "json_object"},
        )

        result = json.loads(response.choices[0].message.content)
        result["scheme_id"] = scheme.scheme_id
        result["scheme_name"] = scheme.scheme_name
        result["jurisdiction"] = scheme.jurisdiction.value
        return SchemeEligibility(**result)

    def evaluate_all(self, user_profile: UserProfile) -> List[SchemeEligibility]:
        """Fast batch evaluation for all applicable schemes in a single LLM call."""
        if not self._initialized:
            self.initialize()

        applicable = self.get_applicable_schemes(user_profile)
        if not applicable:
            return []

        schemes_summary = []
        for s in applicable:
            schemes_summary.append({
                "scheme_id": s.scheme_id,
                "scheme_name": s.scheme_name,
                "jurisdiction": s.jurisdiction.value,
                "must_have": s.must_have_all,
                "must_not_have": s.must_not_have_any,
                "required_documents": s.required_documents,
                "benefit_amount": s.benefit_amount
            })

        lang_name = "Telugu" if user_profile.language == Language.TELUGU else ("Hindi" if user_profile.language == Language.HINDI else "English")

        prompt = f"""You are an expert government scheme eligibility officer.
Evaluate this citizen profile against ALL the schemes listed below.

CITIZEN PROFILE:
{json.dumps(user_profile.to_dict(), ensure_ascii=False)}

SCHEMES TO EVALUATE:
{json.dumps(schemes_summary, ensure_ascii=False)}

TASK:
1. Determine eligibility for EACH scheme.
2. Provide a clear, complete conversational voice summary in {lang_name} addressing the citizen directly by name (explain which schemes they are eligible for, the financial benefits they get, and the documents they need to apply).

Return ONLY valid JSON with this exact structure:
{{
  "voice_summary": "Complete conversational response in {lang_name} addressing citizen by name, explaining all eligible schemes, benefits, and required documents",
  "evaluations": [
    {{
      "scheme_id": "string",
      "scheme_name": "string",
      "jurisdiction": "string",
      "eligible": boolean,
      "confidence": 0.95,
      "benefit_summary": "string",
      "missing_documents": ["string"],
      "exclusion_reasons": ["string"],
      "next_actions": ["string"]
    }}
  ]
}}
"""
        try:
            response = self.groq_client.chat.completions.create(
                model=GROQ_MODEL,
                messages=[
                    {"role": "system", "content": "You are a precise government scheme eligibility officer. Output ONLY valid JSON."},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.1,
                max_tokens=800,
                response_format={"type": "json_object"},
            )
            data = json.loads(response.choices[0].message.content)
            self._last_voice_summary = data.get("voice_summary")

            results = []
            for item in data.get("evaluations", []):
                orig = self.scheme_rules.get(item.get("scheme_id", ""))
                juris_val = item.get("jurisdiction", "central").lower()
                juris_enum = SchemeJurisdiction.ANDHRA_PRADESH if "andhra" in juris_val else (
                    SchemeJurisdiction.TELANGANA if "telangana" in juris_val else SchemeJurisdiction.CENTRAL
                )

                results.append(SchemeEligibility(
                    scheme_id=item.get("scheme_id", ""),
                    scheme_name=item.get("scheme_name", orig.scheme_name if orig else ""),
                    jurisdiction=juris_enum,
                    eligible=bool(item.get("eligible", False)),
                    confidence=float(item.get("confidence", 0.9)),
                    benefit_summary=item.get("benefit_summary", ""),
                    missing_documents=item.get("missing_documents", []),
                    exclusion_reasons=item.get("exclusion_reasons", []),
                    next_actions=item.get("next_actions", []),
                    application_url=orig.online_application_url if orig else None,
                    form_fields=orig.key_form_fields if orig else []
                ))

            results.sort(key=lambda x: (not x.eligible, -x.confidence))
            return results

        except Exception as e:
            print(f"Batch evaluation error, falling back to sequential: {e}")
            results = []
            for scheme in applicable:
                try:
                    results.append(self.check_eligibility(user_profile, scheme))
                except Exception as inner_e:
                    print(f"Error evaluating {scheme.scheme_id}: {inner_e}")
            results.sort(key=lambda x: (not x.eligible, -x.confidence))
            return results

    def generate_voice_response(self, user_profile: UserProfile, eligibilities: List[SchemeEligibility]) -> VoiceResponse:
        """Generate natural language voice response in user's language."""
        language = user_profile.language

        eligible_schemes = [e for e in eligibilities if e.eligible]
        ineligible_schemes = [e for e in eligibilities if not e.eligible]

        # ─── Priority 1: Use the AI-generated summary from the batch LLM call ───
        # This is already in the correct language (te/hi/en) because we told the
        # LLM which language to use in the batch evaluation prompt.
        if self._last_voice_summary and len(self._last_voice_summary.strip()) > 10:
            response_text = self._last_voice_summary.strip()
            self._last_voice_summary = None   # consume it once used
        else:
            # ─── Priority 2: Build from language-specific templates (fallback) ───
            templates = {
                Language.TELUGU: {
                    "greeting_eligible": "నమస్తే {name}! మీ వివరాల ఆధారంగా {count} పథకాలలో మీకు అర్హత ఉంది:",
                    "greeting_none":     "నమస్తే {name}! మీ ప్రస్తుత వివరాలతో ఏ పథకంలోనూ పూర్తి అర్హత లభించలేదు.",
                    "eligible_intro":    "✅ అర్హత గల పథకాలు:",
                    "docs_needed":       "కావలసిన పత్రాలు:",
                    "next":              "తదుపరి చర్య:",
                },
                Language.HINDI: {
                    "greeting_eligible": "नमस्ते {name}! आपके विवरण के अनुसार {count} योजनाओं में आप पात्र हैं:",
                    "greeting_none":     "नमस्ते {name}! वर्तमान जानकारी के आधार पर किसी भी योजना में पूर्ण पात्रता नहीं मिली।",
                    "eligible_intro":    "✅ पात्र योजनाएं:",
                    "docs_needed":       "आवश्यक दस्तावेज़:",
                    "next":              "अगला कदम:",
                },
                Language.ENGLISH: {
                    "greeting_eligible": "Hello {name}! Based on your profile, you are eligible for {count} scheme(s):",
                    "greeting_none":     "Hello {name}! Based on your current details, no scheme fully matched your profile.",
                    "eligible_intro":    "✅ Eligible schemes:",
                    "docs_needed":       "Documents needed:",
                    "next":              "Next step:",
                },
            }

            t = templates.get(language, templates[Language.ENGLISH])
            name = user_profile.name or ("మీరు" if language == Language.TELUGU else ("आप" if language == Language.HINDI else "you"))

            parts = []
            if eligible_schemes:
                parts.append(t["greeting_eligible"].format(name=name, count=len(eligible_schemes)))
                parts.append(t["eligible_intro"])
                for e in eligible_schemes[:3]:
                    parts.append(f"  • {e.scheme_name} — {e.benefit_summary}")
                    if e.missing_documents:
                        parts.append(f"    {t['docs_needed']} {', '.join(e.missing_documents[:2])}")
                    if e.next_actions:
                        parts.append(f"    {t['next']} {e.next_actions[0]}")
            else:
                parts.append(t["greeting_none"].format(name=name))

            response_text = "\n".join(parts)

        # Suggested actions
        suggested_actions = []
        for e in eligible_schemes[:3]:
            if e.next_actions:
                suggested_actions.extend(e.next_actions[:2])

        return VoiceResponse(
            language=language,
            text=response_text,
            eligibility_results=eligibilities,
            suggested_actions=suggested_actions[:5],
            session_state={"profile": user_profile.to_dict()},
        )


# ===========================================
# Singleton Instance
# ===========================================
_rag_instance: Optional[EligibilityRAG] = None


def get_rag() -> EligibilityRAG:
    global _rag_instance
    if _rag_instance is None:
        _rag_instance = EligibilityRAG()
    return _rag_instance


def initialize_rag(force_reload: bool = False):
    """Initialize the RAG engine."""
    rag = get_rag()
    rag.initialize(force_reload=force_reload)
    return rag


if __name__ == "__main__":
    # Test initialization
    rag = initialize_rag()
    print(f"Loaded schemes: {list(rag.scheme_rules.keys())}")