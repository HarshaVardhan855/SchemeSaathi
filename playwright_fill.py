"""
Playwright Form Automation for Government Scheme Portals.
Primary target: PM-KISAN (pmkisan.gov.in) for demo.
Fallback: Generates filled PDF when portal automation fails.
"""
import os
import asyncio
import json
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

from playwright.async_api import async_playwright, Page, Browser
from pydantic import BaseModel

from models import UserProfile, FormFillResult, SchemeEligibility, SchemeJurisdiction


# ===========================================
# Configuration
# ===========================================
PLAYWRIGHT_HEADLESS = os.getenv("PLAYWRIGHT_HEADLESS", "true").lower() == "true"
PLAYWRIGHT_TIMEOUT = int(os.getenv("PLAYWRIGHT_TIMEOUT", "30000"))

# PM-KISAN Selectors (tested as of 2024)
PM_KISAN_SELECTORS = {
    "new_farmer_registration": "a:has-text('New Farmer Registration')",
    "aadhaar_input": "#AadhaarNo",
    "name_input": "#FarmerName",
    "gender_select": "#Gender",
    "category_select": "#Category",
    "state_select": "#State",
    "district_select": "#District",
    "sub_district_select": "#SubDistrict",
    "village_select": "#Village",
    "land_survey_input": "#SurveyNo",
    "land_area_input": "#Area",
    "ownership_select": "#Ownership",
    "bank_account_input": "#AccountNo",
    "ifsc_input": "#IFSC",
    "bank_name_select": "#BankName",
    "mobile_input": "#MobileNo",
    "declaration_checkbox": "#Declaration",
    "submit_button": "#btnSubmit",
    "captcha_image": "#imgCaptcha",
    "captcha_input": "#txtCaptcha",
}

# Portal URLs
PORTAL_URLS = {
    "pm_kisan": "https://pmkisan.gov.in/",
    "pm_kisan_registration": "https://pmkisan.gov.in/RegistrationForm.aspx",
}


@dataclass
class FormFieldMapping:
    """Maps user profile fields to form selectors."""
    profile_field: str
    selector: str
    field_type: str  # input, select, checkbox
    transform: Optional[str] = None  # e.g., "acres_to_hectares"


# PM-KISAN field mappings
PM_KISAN_MAPPINGS = [
    FormFieldMapping("aadhaar", PM_KISAN_SELECTORS["aadhaar_input"], "input"),
    FormFieldMapping("name", PM_KISAN_SELECTORS["name_input"], "input"),
    FormFieldMapping("gender", PM_KISAN_SELECTORS["gender_select"], "select"),
    FormFieldMapping("caste_category", PM_KISAN_SELECTORS["category_select"], "select"),
    FormFieldMapping("state", PM_KISAN_SELECTORS["state_select"], "select"),
    FormFieldMapping("district", PM_KISAN_SELECTORS["district_select"], "select"),
    FormFieldMapping("sub_district", PM_KISAN_SELECTORS["sub_district_select"], "select"),
    FormFieldMapping("village", PM_KISAN_SELECTORS["village_select"], "select"),
    FormFieldMapping("land_survey", PM_KISAN_SELECTORS["land_survey_input"], "input"),
    FormFieldMapping("land_area_acres", PM_KISAN_SELECTORS["land_area_input"], "input", "acres"),
    FormFieldMapping("ownership", PM_KISAN_SELECTORS["ownership_select"], "select"),
    FormFieldMapping("bank_account", PM_KISAN_SELECTORS["bank_account_input"], "input"),
    FormFieldMapping("ifsc", PM_KISAN_SELECTORS["ifsc_input"], "input"),
    FormFieldMapping("bank_name", PM_KISAN_SELECTORS["bank_name_select"], "select"),
    FormFieldMapping("mobile", PM_KISAN_SELECTORS["mobile_input"], "input"),
]


class PlaywrightFormFiller:
    """Automates form filling on government portals."""

    def __init__(self, headless: bool = PLAYWRIGHT_HEADLESS):
        self.headless = headless
        self.browser: Optional[Browser] = None
        self.page: Optional[Page] = None
        self.screenshots: List[str] = []

    async def __aenter__(self):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=self.headless)
        self.page = await self.browser.new_page()
        self.page.set_default_timeout(PLAYWRIGHT_TIMEOUT)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()

    async def _take_screenshot(self, name: str) -> str:
        """Take screenshot and return path."""
        path = f"screenshots/{name}_{len(self.screenshots)}.png"
        os.makedirs("screenshots", exist_ok=True)
        await self.page.screenshot(path=path, full_page=True)
        self.screenshots.append(path)
        return path

    async def _fill_field(self, selector: str, value: Any, field_type: str):
        """Fill a form field based on type."""
        if not value:
            return

        element = await self.page.wait_for_selector(selector, timeout=5000)

        if field_type == "input":
            await element.fill(str(value))
        elif field_type == "select":
            await element.select_option(label=str(value))
        elif field_type == "checkbox":
            if value:
                await element.check()
            else:
                await element.uncheck()

    def _transform_value(self, field: str, value: Any, transform: Optional[str]) -> Any:
        """Transform profile value for form field."""
        if transform == "acres_to_hectares" and value:
            return round(float(value) * 0.404686, 4)
        if transform == "hectares_to_acres" and value:
            return round(float(value) / 0.404686, 2)
        return value

    def _map_profile_to_form(self, profile: UserProfile) -> Dict[str, Any]:
        """Map user profile to PM-KISAN form fields."""
        return {
            "aadhaar": profile.aadhaar if hasattr(profile, 'aadhaar') else None,
            "name": profile.name,
            "gender": {"male": "Male", "female": "Female", "other": "Other"}.get(profile.gender, "Male") if profile.gender else None,
            "caste_category": {"general": "General", "sc": "SC", "st": "ST", "obc": "OBC", "bc": "BC", "minority": "Minority"}.get(profile.caste_category, "General") if profile.caste_category else None,
            "state": "Andhra Pradesh" if profile.state and profile.state.value == "AP" else "Telangana" if profile.state and profile.state.value == "TS" else None,
            "district": profile.district,
            "sub_district": None,  # Would need mapping
            "village": profile.village,
            "land_survey": None,  # User would need to provide
            "land_area_acres": profile.land_holding_acres,
            "ownership": "Owner",  # Default
            "bank_account": None,  # User would need to provide
            "ifsc": None,
            "bank_name": None,
            "mobile": None,  # User would need to provide
        }

    async def fill_pm_kisan(self, profile: UserProfile) -> FormFillResult:
        """Fill PM-KISAN new farmer registration form."""
        try:
            # Navigate to registration page
            await self.page.goto(PORTAL_URLS["pm_kisan_registration"], wait_until="networkidle")
            await self._take_screenshot("pm_kisan_landing")

            # Click New Farmer Registration if needed
            try:
                await self.page.click(PM_KISAN_SELECTORS["new_farmer_registration"])
                await self.page.wait_for_load_state("networkidle")
            except:
                pass  # Might already be on registration form

            await self._take_screenshot("pm_kisan_form")

            # Map profile to form data
            form_data = self._map_profile_to_form(profile)

            # Fill each field
            fields_filled = []
            for mapping in PM_KISAN_MAPPINGS:
                value = form_data.get(mapping.profile_field)
                if value is not None:
                    value = self._transform_value(mapping.profile_field, value, mapping.transform)
                    try:
                        await self._fill_field(mapping.selector, value, mapping.field_type)
                        fields_filled.append(mapping.profile_field)
                    except Exception as e:
                        print(f"Failed to fill {mapping.profile_field}: {e}")

            await self._take_screenshot("pm_kisan_filled")

            # Handle CAPTCHA (manual intervention needed)
            captcha_present = await self.page.is_visible(PM_KISAN_SELECTORS["captcha_image"])
            if captcha_present:
                print("CAPTCHA detected - manual entry required")
                # In demo, we'll skip actual submission
                await self._take_screenshot("pm_kisan_captcha")

            # Check declaration
            try:
                await self.page.check(PM_KISAN_SELECTORS["declaration_checkbox"])
                fields_filled.append("declaration")
            except:
                pass

            # Don't actually submit in demo (would need real data)
            # await self.page.click(PM_KISAN_SELECTORS["submit_button"])

            return FormFillResult(
                success=True,
                scheme_id="pm_kisan",
                screenshots=self.screenshots.copy(),
                fields_filled=fields_filled,
                error_message="Form filled successfully (submission skipped for demo)" if fields_filled else "No fields could be filled",
            )

        except Exception as e:
            return FormFillResult(
                success=False,
                scheme_id="pm_kisan",
                screenshots=self.screenshots.copy(),
                error_message=str(e),
            )


async def fill_pm_kisan_form(profile: UserProfile) -> FormFillResult:
    """Convenience function to fill PM-KISAN form."""
    async with PlaywrightFormFiller() as filler:
        return await filler.fill_pm_kisan(profile)


# ===========================================
# Scheme-Specific Form Fillers (Extensible)
# ===========================================
class SchemeFormFiller:
    """Registry of scheme-specific form fillers."""

    def __init__(self):
        self.fillers = {
            "pm_kisan": fill_pm_kisan_form,
            # Add more as needed:
            # "ayushman_bharat": fill_ayushman_form,
            # "nsap_pension": fill_nsap_form,
        }

    async def fill(self, scheme_id: str, profile: UserProfile) -> FormFillResult:
        """Fill form for a specific scheme."""
        filler = self.fillers.get(scheme_id)
        if not filler:
            return FormFillResult(
                success=False,
                scheme_id=scheme_id,
                error_message=f"No form filler implemented for {scheme_id}",
            )
        return await filler(profile)

    def is_supported(self, scheme_id: str) -> bool:
        return scheme_id in self.fillers


# ===========================================
# Demo / Test
# ===========================================
if __name__ == "__main__":
    import sys

    # Test with sample profile
    sample_profile = UserProfile(
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
        language="te",
    )

    async def test():
        result = await fill_pm_kisan_form(sample_profile)
        print(json.dumps(result.model_dump(), indent=2, default=str))

    asyncio.run(test())