# PM-KISAN (Pradhan Mantri Kisan Samman Nidhi)

## Basic Info
- **Jurisdiction:** Central
- **Department:** Ministry of Agriculture & Farmers Welfare
- **Official Portal:** https://pmkisan.gov.in/
- **Guidelines PDF:** https://pmkisan.gov.in/Documents/PM-KISAN_Guidelines.pdf
- **MyScheme/State Portal Page:** https://www.myscheme.gov.in/schemes/pmkisan

## Eligibility Rules (Structured)

### Must Have (ALL required)
- [ ] Farmer with cultivable land in revenue records
- [ ] Landholder (owner or tenant with legal rights)
- [ ] Indian citizen

### Must NOT Have (ANY disqualifies)
- [ ] Institutional landholders (trusts, societies, companies)
- [ ] Income tax payee in last assessment year
- [ ] Serving/retired officers (Group A/B), PSU employees
- [ ] Professionals (doctors, engineers, lawyers, CAs) registered with professional bodies
- [ ] Pensioners receiving >₹10,000/month (except MTS/Class IV/Group D)
- [ ] Constitutional post holders (MPs, MLAs, Mayors, etc.)

### Conditional / State-Specific
- [ ] Land must be linked in state land records (AP: Webland, TS: Dharani, KA: Bhoomi)
- [ ] Aadhaar mandatory for registration
- [ ] Bank account must be Aadhaar-linked for DBT

## Required Documents (Exact Names)
1. Aadhaar Card (mandatory)
2. Land Record (1B / Pahani / Khata extract / Webland print / Dharani passbook)
3. Bank Passbook (first page with IFSC, account holder name)
4. Mobile Number (linked to Aadhaar for OTP)

## Application Process
- **Online URL:** https://pmkisan.gov.in/RegistrationForm.aspx
- **Offline:** CSC (Common Service Center) / Agriculture Office / Tahsildar Office
- **Key Form Fields:**
  - Aadhaar Number
  - Name (as per Aadhaar)
  - Gender
  - Category (General/SC/ST/OBC)
  - State, District, Sub-district, Village
  - Land Details: Survey Number, Extent (acres), Ownership Type
  - Bank: Account Number, IFSC, Bank Name
  - Mobile Number
  - Declaration Checkboxes

## Benefit Details
- **Amount:** ₹6,000 per year
- **Frequency:** Annual (3 installments of ₹2,000 each)
- **Mode:** Direct Benefit Transfer (DBT) to bank account

## FAQ / Edge Cases (for RAG)
- **Q: Tenant farmer eligible?** → A: Yes, if cultivating land with legal tenancy rights and name in revenue records
- **Q: Joint land holding?** → A: One installment per family (husband, wife, minor children)
- **Q: Aadhaar not linked to bank?** → A: Payment fails, must link Aadhaar to bank account via NPCI mapper
- **Q: Dead farmer?** → A: Legal heir can claim with succession certificate and death certificate
- **Q: Land in multiple districts?** → A: Register once, all land parcels included
- **Q: Farmer already registered but not getting payment?** → A: Check PM-KISAN portal for "Beneficiary Status" - usually Aadhaar-bank linking or land seeding issue
- **Q: Woman farmer without land in name?** → A: If cultivating family land, can register with husband's consent and family declaration

## Source Citations
- [PM-KISAN Guidelines PDF, Page 3-4] Eligibility criteria
- [PM-KISAN Guidelines PDF, Page 5-6] Exclusion categories
- [pmkisan.gov.in FAQ] Registration process
- [MyScheme PM-KISAN page] Document requirements

## Auto-fill Feasible
- **Portal:** pmkisan.gov.in
- **Status:** Yes - New Farmer Registration form has consistent selectors
- **CAPTCHA:** Yes (image-based, requires manual entry)
- **Submission:** Requires real OTP on registered mobile

*Last Verified: 2024-11-20*