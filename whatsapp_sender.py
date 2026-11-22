"""
WhatsApp Sender: Sends eligibility results, PDFs, and voice notes via WhatsApp.
Supports both WhatsApp Cloud API (Meta) and Twilio Sandbox for testing.
"""
import os
import json
import requests
from pathlib import Path
from typing import Optional, List, Dict, Any
from dataclasses import dataclass

from models import UserProfile, SchemeEligibility, VoiceResponse, Language


# ===========================================
# Configuration
# ===========================================
# WhatsApp Cloud API (Meta)
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN")
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID")
WHATSAPP_VERIFY_TOKEN = os.getenv("WHATSAPP_VERIFY_TOKEN")
WHATSAPP_APP_SECRET = os.getenv("WHATSAPP_APP_SECRET")
WHATSAPP_API_VERSION = "v20.0"
WHATSAPP_BASE_URL = f"https://graph.facebook.com/{WHATSAPP_API_VERSION}"

# Twilio WhatsApp Sandbox (Alternative)
TWILIO_ACCOUNT_SID = os.getenv("TWILIO_ACCOUNT_SID")
TWILIO_AUTH_TOKEN = os.getenv("TWILIO_AUTH_TOKEN")
TWILIO_WHATSAPP_FROM = os.getenv("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")


# ===========================================
# Message Templates
# ===========================================
TEMPLATES = {
    Language.TELUGU: {
        "greeting": "నమస్తే {name}! మీకు ఈ స్కీమ్స్ అర్హత ఉన్నాయి:",
        "eligible_item": "✅ {scheme} — {benefit}",
        "missing_docs": "   📄 కావలసిన పత్రాలు: {docs}",
        "next_step": "   ➡️ {action}",
        "ineligible_item": "❌ {scheme} — {reason}",
        "footer": "వివరాలు ఇక్కడ: {url}\n\n— SchemeSaathi",
    },
    Language.HINDI: {
        "greeting": "नमस्ते {name}! आपको ये स्कीम्स मिल सकती हैं:",
        "eligible_item": "✅ {scheme} — {benefit}",
        "missing_docs": "   📄 आवश्यक दस्तावेज: {docs}",
        "next_step": "   ➡️ {action}",
        "ineligible_item": "❌ {scheme} — {reason}",
        "footer": "विवरण यहाँ: {url}\n\n— SchemeSaathi",
    },
    Language.ENGLISH: {
        "greeting": "Hello {name}! You're eligible for these schemes:",
        "eligible_item": "✅ {scheme} — {benefit}",
        "missing_docs": "   📄 Missing documents: {docs}",
        "next_step": "   ➡️ {action}",
        "ineligible_item": "❌ {scheme} — {reason}",
        "footer": "Details here: {url}\n\n— SchemeSaathi",
    },
}


@dataclass
class SendResult:
    success: bool
    message_id: Optional[str] = None
    error: Optional[str] = None


class WhatsAppSender:
    """Sends messages via WhatsApp Cloud API or Twilio."""

    def __init__(self, use_twilio: bool = False):
        self.use_twilio = use_twilio
        self.session = requests.Session()

        if use_twilio:
            if not TWILIO_ACCOUNT_SID or not TWILIO_AUTH_TOKEN:
                raise ValueError("Twilio credentials not configured")
            self.session.auth = (TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)
            self.base_url = f"https://api.twilio.com/2010-04-01/Accounts/{TWILIO_ACCOUNT_SID}/Messages.json"
            self.from_number = TWILIO_WHATSAPP_FROM
        else:
            if not WHATSAPP_ACCESS_TOKEN or not WHATSAPP_PHONE_NUMBER_ID:
                raise ValueError("WhatsApp Cloud API credentials not configured")
            self.session.headers.update({
                "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
                "Content-Type": "application/json",
            })
            self.base_url = f"{WHATSAPP_BASE_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
            self.from_number = WHATSAPP_PHONE_NUMBER_ID

    def _get_template(self, language: Language) -> Dict[str, str]:
        return TEMPLATES.get(language, TEMPLATES[Language.ENGLISH])

    def format_eligibility_message(
        self,
        profile: UserProfile,
        eligibilities: List[SchemeEligibility],
        language: Language,
        detail_url: str = ""
    ) -> str:
        """Format eligibility results as WhatsApp message."""
        t = self._get_template(language)
        name = profile.name or "వాడుకు" if language == Language.TELUGU else "आप" if language == Language.HINDI else "there"

        parts = [t["greeting"].format(name=name)]

        eligible = [e for e in eligibilities if e.eligible]
        ineligible = [e for e in eligibilities if not e.eligible]

        if eligible:
            for e in eligible[:3]:  # Top 3
                parts.append(t["eligible_item"].format(
                    scheme=e.scheme_name,
                    benefit=e.benefit_summary
                ))
                if e.missing_documents:
                    docs = ", ".join(e.missing_documents[:3])
                    parts.append(t["missing_docs"].format(docs=docs))
                if e.next_actions:
                    parts.append(t["next_step"].format(action=e.next_actions[0]))

        if ineligible:
            parts.append("\nNot eligible:")
            for e in ineligible[:2]:
                reason = e.exclusion_reasons[0] if e.exclusion_reasons else "Does not meet criteria"
                parts.append(t["ineligible_item"].format(scheme=e.scheme_name, reason=reason))

        if detail_url:
            parts.append(t["footer"].format(url=detail_url))

        return "\n".join(parts)

    def send_text(self, to_number: str, message: str) -> SendResult:
        """Send a text message."""
        to_number = self._normalize_number(to_number)

        if self.use_twilio:
            data = {
                "From": self.from_number,
                "To": f"whatsapp:{to_number}",
                "Body": message,
            }
            response = self.session.post(self.base_url, data=data)
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "text",
                "text": {"body": message},
            }
            response = self.session.post(self.base_url, json=payload)

        return self._handle_response(response)

    def send_document(self, to_number: str, document_url: str, caption: str = "", filename: str = "document.pdf") -> SendResult:
        """Send a document (PDF)."""
        to_number = self._normalize_number(to_number)

        if self.use_twilio:
            data = {
                "From": self.from_number,
                "To": f"whatsapp:{to_number}",
                "Body": caption,
                "MediaUrl": document_url,
            }
            response = self.session.post(self.base_url, data=data)
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "document",
                "document": {
                    "link": document_url,
                    "caption": caption,
                    "filename": filename,
                },
            }
            response = self.session.post(self.base_url, json=payload)

        return self._handle_response(response)

    def send_audio(self, to_number: str, audio_url: str) -> SendResult:
        """Send an audio file (voice note)."""
        to_number = self._normalize_number(to_number)

        if self.use_twilio:
            data = {
                "From": self.from_number,
                "To": f"whatsapp:{to_number}",
                "MediaUrl": audio_url,
            }
            response = self.session.post(self.base_url, data=data)
        else:
            payload = {
                "messaging_product": "whatsapp",
                "to": to_number,
                "type": "audio",
                "audio": {"link": audio_url},
            }
            response = self.session.post(self.base_url, json=payload)

        return self._handle_response(response)

    def send_eligibility_results(
        self,
        to_number: str,
        profile: UserProfile,
        eligibilities: List[SchemeEligibility],
        language: Language,
        detail_url: str = "",
        pdf_urls: Optional[List[str]] = None,
        audio_url: Optional[str] = None,
    ) -> List[SendResult]:
        """Send complete eligibility results: text + PDFs + audio."""
        results = []

        # 1. Send text message
        message = self.format_eligibility_message(profile, eligibilities, language, detail_url)
        results.append(self.send_text(to_number, message))

        # 2. Send PDFs if provided
        if pdf_urls:
            for pdf_url in pdf_urls:
                results.append(self.send_document(
                    to_number,
                    pdf_url,
                    caption="Your scheme application form / checklist",
                    filename="scheme_form.pdf"
                ))

        # 3. Send audio if provided
        if audio_url:
            results.append(self.send_audio(to_number, audio_url))

        return results

    def _normalize_number(self, number: str) -> str:
        """Normalize phone number to international format."""
        # Remove whatsapp: prefix if present
        number = number.replace("whatsapp:", "")
        # Remove spaces, dashes, parentheses
        number = "".join(c for c in number if c.isdigit() or c == "+")
        # Add + if missing
        if not number.startswith("+"):
            # Assume India if 10 digits
            if len(number) == 10:
                number = "+91" + number
            else:
                number = "+" + number
        return number

    def _handle_response(self, response: requests.Response) -> SendResult:
        """Handle API response."""
        try:
            data = response.json()
            if response.status_code == 200:
                # Extract message ID
                msg_id = None
                if self.use_twilio:
                    msg_id = data.get("sid")
                else:
                    msg_id = data.get("messages", [{}])[0].get("id")
                return SendResult(success=True, message_id=msg_id)
            else:
                error = data.get("error", {}).get("message", str(data))
                return SendResult(success=False, error=error)
        except Exception as e:
            return SendResult(success=False, error=str(e))


class MockWhatsAppSender(WhatsAppSender):
    """Mock sender for testing without API credentials."""

    def __init__(self):
        self.sent_messages = []

    def send_text(self, to_number: str, message: str) -> SendResult:
        self.sent_messages.append({"to": to_number, "type": "text", "content": message})
        print(f"[MOCK WHATSAPP] To: {to_number}\n{message}\n---")
        return SendResult(success=True, message_id="mock_msg_id")

    def send_document(self, to_number: str, document_url: str, caption: str = "", filename: str = "document.pdf") -> SendResult:
        self.sent_messages.append({"to": to_number, "type": "document", "url": document_url, "caption": caption})
        print(f"[MOCK WHATSAPP] Document to {to_number}: {filename} ({document_url})")
        return SendResult(success=True, message_id="mock_doc_id")

    def send_audio(self, to_number: str, audio_url: str) -> SendResult:
        self.sent_messages.append({"to": to_number, "type": "audio", "url": audio_url})
        print(f"[MOCK WHATSAPP] Audio to {to_number}: {audio_url}")
        return SendResult(success=True, message_id="mock_audio_id")


def get_sender(use_mock: bool = False, use_twilio: bool = False) -> WhatsAppSender:
    """Factory to get appropriate sender."""
    if use_mock or (not WHATSAPP_ACCESS_TOKEN and not TWILIO_ACCOUNT_SID):
        return MockWhatsAppSender()
    if use_twilio:
        return WhatsAppSender(use_twilio=True)
    return WhatsAppSender(use_twilio=False)


# ===========================================
# Webhook Handler (for incoming messages)
# ===========================================
def verify_webhook(request_args: Dict[str, str]) -> Optional[str]:
    """Verify WhatsApp webhook subscription."""
    mode = request_args.get("hub.mode")
    token = request_args.get("hub.verify_token")
    challenge = request_args.get("hub.challenge")

    if mode == "subscribe" and token == WHATSAPP_VERIFY_TOKEN:
        return challenge
    return None


def parse_webhook_payload(payload: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Parse incoming WhatsApp webhook payload."""
    messages = []

    try:
        for entry in payload.get("entry", []):
            for change in entry.get("changes", []):
                value = change.get("value", {})
                for message in value.get("messages", []):
                    msg = {
                        "from": message.get("from"),
                        "id": message.get("id"),
                        "timestamp": message.get("timestamp"),
                        "type": message.get("type"),
                    }
                    if message.get("type") == "text":
                        msg["text"] = message.get("text", {}).get("body")
                    elif message.get("type") == "audio":
                        msg["audio_id"] = message.get("audio", {}).get("id")
                        msg["mime_type"] = message.get("audio", {}).get("mime_type")
                    messages.append(msg)
    except Exception as e:
        print(f"Error parsing webhook: {e}")

    return messages


if __name__ == "__main__":
    # Test mock sender
    sender = MockWhatsAppSender()

    from models import UserProfile, SchemeEligibility, SchemeJurisdiction, Language

    profile = UserProfile(name="Ramesh", state="AP", language=Language.TELUGU)
    eligibility = SchemeEligibility(
        scheme_id="pm_kisan",
        scheme_name="PM-KISAN",
        jurisdiction=SchemeJurisdiction.CENTRAL,
        eligible=True,
        confidence=0.95,
        benefit_summary="₹6,000 per year",
        missing_documents=["Land record", "Bank passbook"],
        next_actions=["Get 1B copy from MeeSeva"],
    )

    sender.send_eligibility_results(
        to_number="+919876543210",
        profile=profile,
        eligibilities=[eligibility],
        language=Language.TELUGU,
    )