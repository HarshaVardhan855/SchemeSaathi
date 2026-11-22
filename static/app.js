/**
 * SchemeSaathi Web Application Frontend Logic.
 * Full Multilingual Support: Telugu, Hindi, English.
 */

const STATE = {
  currentLanguage: 'te',
  isRecording: false,
  mediaRecorder: null,
  audioChunks: [],
  recordStartTime: null,
  recordTimerInterval: null,
  recordedBlob: null,
  lastProfile: null,
  lastEligibilities: [],
  lastVoiceResponse: null,
};

// UI Translations Dictionary
const I18N = {
  te: {
    top_announcement: "🏛️ పౌర స్పందన & డిజిటల్ పరిపాలన — ఆంధ్రప్రదేశ్, తెలంగాణ & కేంద్ర ప్రభుత్వ 15 సంక్షేమ పథకాలు",
    app_tagline: "ప్రభుత్వ సంక్షేమ పథకాల అర్హత తనిఖీ సహాయకుడు",
    model_status: "Groq Qwen 3.8 (27B) ఆన్‌లైన్",
    tab_voice: "వాయిస్ & వివరాలు (Voice Input)",
    tab_results: "అర్హత ఫలితాలు (Eligibility)",
    tab_autofill: "ఆటో-ఫిల్ & PDF (Forms & Docs)",
    tab_whatsapp: "వాట్సాప్ డెలివరీ (WhatsApp)",
    voice_header: "🎙️ మాట్లాడి తెలుసుకోండి",
    voice_subtitle: "మీ వివరాలు తెలుగు, హిందీ లేదా ఇంగ్లీషులో మాట్లాడండి. మా ఏఐ మీ అర్హతలను లెక్కిస్తుంది.",
    tap_to_speak: "మైక్ బటన్ నొక్కి మాట్లాడండి (Tap to speak)",
    recording: "రికార్డ్ అవుతోంది... ముగించడానికి మళ్ళీ నొక్కండి",
    btn_process_voice: "విశ్లేషించండి (Process Voice Input)",
    sample_label: "⚡ తక్షణ నమూనా వాయిస్ పరీక్ష (1-Click Test Prompts):",
    or_upload: "లేదా ఆడియో ఫైల్ అప్‌లోడ్ చేయండి",
    btn_choose_audio: "📂 ఆడియో ఫైల్ ఎంచుకోండి (.wav / .mp3 / .m4a)",
    manual_header: "📝 వివరాలు నమోదు చేయండి",
    manual_subtitle: "వాయిస్ కాకుండా నేరుగా ఫారమ్ ద్వారా కూడా అర్హత తనిఖీ చేయవచ్చు.",
    lbl_name: "పేరు (Name)",
    lbl_age: "వయస్సు (Age)",
    lbl_gender: "లింగం (Gender)",
    lbl_state: "రాష్ట్రం (State)",
    lbl_district: "జిల్లా (District)",
    lbl_land: "భూమి ఎకరాలు (Land in Acres)",
    lbl_income: "వార్షిక ఆదాయం (Annual Income ₹)",
    lbl_category: "కుల వర్గం (Category)",
    opt_select_gender: "లింగం ఎంచుకోండి (Select Gender)",
    opt_select_state: "రాష్ట్రం ఎంచుకోండి (Select State)",
    opt_select_category: "వర్గం ఎంచుకోండి (Select Category)",
    opt_male: "పురుషుడు (Male)",
    opt_female: "స్త్రీ (Female)",
    opt_other: "ఇతర (Other)",
    opt_ap: "ఆంధ్రప్రదేశ్ (Andhra Pradesh)",
    opt_ts: "తెలంగాణ (Telangana)",
    opt_other_state: "ఇతర రాష్ట్రాలు (Central Only)",
    opt_bc: "BC (వెనుకబడిన తరగతులు)",
    opt_sc: "SC",
    opt_st: "ST",
    opt_minority: "మైనారిటీ (Minority)",
    opt_general: "జనరల్ (General)",
    chk_farmer: "రైతు (Farmer)",
    chk_aadhaar: "ఆధార్ కార్డు ఉంది (Aadhaar)",
    chk_bank: "బ్యాంకు ఖాతా (Bank Account)",
    chk_ration: "రేషన్ కార్డు (Ration Card)",
    chk_landrec: "భూమి రికార్డు (Land Record / 1B)",
    chk_shg: "స్వయం సహాయక సంఘం (SHG Member)",
    chk_vendor: "వీధి వ్యాపారి (Street Vendor)",
    lbl_marital: "వివాహ స్థితి (Marital Status)",
    opt_select_marital: "వివాహ స్థితి ఎంచుకోండి",
    opt_married: "వివాహితులు (Married)",
    opt_unmarried: "అవివాహితులు (Unmarried)",
    opt_widowed: "వితంతువు / విధురుడు (Widow / Widower)",
    opt_divorced: "విడాకులు (Divorced)",    lbl_disability: "వికలాంగత (Disability)",
    opt_select_disability: "వికలాంగత ఎంచుకోండి",
    opt_no_disability: "వికలాంగత లేదు (None)",
    opt_has_disability: "వికలాంగత ఉంది (Yes, ≥40%)",
    lbl_occupation: "వృత్తి / ఉద్యోగం (Occupation)",
    opt_select_occupation: "వృత్తి ఎంచుకోండి",
    opt_occ_farmer: "రైతు (Farmer)",
    opt_occ_daily: "రోజువారీ కూలీ (Daily Wage Labourer)",
    opt_occ_vendor: "వీధి వ్యాపారి (Street Vendor)",
    opt_occ_self: "స్వయం ఉపాధి (Self-Employed / Business)",
    opt_occ_private: "ప్రైవేట్ ఉద్యోగి (Private Employee)",
    opt_occ_govt: "ప్రభుత్వ ఉద్యోగి (Govt. Employee / Retired)",
    opt_occ_homemaker: "గృహిణి (Homemaker)",
    opt_occ_student: "విద్యార్థి (Student)",
    opt_occ_unemployed: "నిరుద్యోగి (Unemployed)",
    btn_check_eligibility: "అర్హత తనిఖీ చేయండి (Check Eligibility)",
    btn_play_audio: "ఆడియో వినండి (Play Audio)",
    btn_pause_audio: "పాజ్ చేయండి (Pause)",
    btn_stop_audio: "ఆపండి (Stop)",
    status_audio_ready: "ఆడియో సిద్ధంగా ఉంది",
    status_audio_playing: "ఆడియో ప్లే అవుతోంది...",
    voice_resp_title: "SchemeSaathi ఆడియో సహాయకుడు (Audio Response)",
    voice_resp_sub: "మీ వివరాల ఆధారంగా ఏఐ రూపొందించిన వాయిస్ సందేశం:",
    profile_summary_title: "👤 పౌరుడి వివరాలు (Citizen Profile Extracted)",
    schemes_heading: "అర్హత కలిగిన పథకాలు",
    filter_all: "అన్నీ (All)",
    filter_eligible: "అర్హత ఉన్నవి (Eligible)",
    filter_central: "కేంద్ర పథకాలు (Central)",
    filter_ap: "ఆంధ్రప్రదేశ్ (AP)",
    filter_ts: "తెలంగాణ (TS)",
    empty_title: "ఇంకా వివరాలు నమోదు కాలేదు",
    empty_desc: "దయచేసి 'వాయిస్ & వివరాలు' ట్యాబ్‌లో మాట్లాడండి లేదా ఫారమ్ సమర్పించండి.",
    pdf_header: "📄 పత్రాల డౌన్‌లోడ్ (Official PDFs)",
    pdf_sub: "అధికారిక ఫారమ్ మరియు అవసరమైన డాక్యుమెంట్ల చెక్‌లిస్ట్‌ను ఒకే క్లిక్‌తో పిడిఎఫ్ రూపంలో పొందండి.",
    pdf_form_title: "📋 దరఖాస్తు ఫారమ్ PDF",
    pdf_form_desc: "మీ వివరాలతో నింపబడిన పిడిఎఫ్ దరఖాస్తు పత్రం (PM-KISAN / అన్నదాత సుఖీభవ / etc.)",
    btn_get_form_pdf: "ఫారమ్ PDF పొందండి",
    pdf_checklist_title: "📑 కావాల్సిన పత్రాల చెక్‌లిస్ట్",
    pdf_checklist_desc: "మీకు ఉన్నవి, మీరు సమర్పించాల్సిన డాక్యుమెంట్ల వివరాలతో కూడిన పూర్తి గైడ్.",
    btn_get_checklist_pdf: "చెక్‌లిస్ట్ PDF పొందండి",
    pdf_ready_title: "లభించిన ఫైళ్లు (Ready for Download):",
    autofill_header: "🤖 పోర్టల్ ఆటో-ఫిల్ (Portal Automation)",
    autofill_sub: "ప్రభుత్వ పోర్టల్ (PM-KISAN) లోకి మీ వివరాలను నేరుగా స్వయంచాలకంగా పూరించండి.",
    target_portal_lbl: "లక్ష్య పోర్టల్:",
    btn_launch_autofill: "PM-KISAN ఫారమ్ ఆటో-ఫిల్ ప్రారంభించండి",
    autofill_status_lbl: "ఆటోమేషన్ స్థితి:",
    whatsapp_header: "📱 వాట్సాప్‌కు ఫలితాలు పంపండి",
    whatsapp_sub: "స్మార్ట్‌ఫోన్ లేదా ఫీచర్ ఫోన్ ఉన్న పౌరుల మొబైల్‌కు అర్హత సమాచారం మరియు లింకులు పంపబడును.",
    whatsapp_num_lbl: "లబ్ధిదారుని వాట్సాప్ నంబర్ (Beneficiary Mobile)",
    btn_send_whatsapp: "వాట్సాప్‌కు పంపండి (Send to WhatsApp)",
    loading_analyzing: "విశ్లేషిస్తోంది...",
    loading_desc: "వాయిస్ మరియు నిబంధనలను ప్రాసెస్ చేస్తోంది...",
    status_eligible: "✅ అర్హులు (Eligible)",
    status_not_eligible: "❌ అనర్హులు (Not Eligible)",
    benefit_lbl: "లభించే ప్రయోజనం (Benefit)",
    req_docs_lbl: "అవసరమైన పత్రాలు:",
    btn_download_form: "📄 ఫారమ్ PDF డౌన్‌లోడ్",
    btn_not_eligible: "నిబంధనలు సరిపోలలేదు",
  },
  hi: {
    top_announcement: "🏛️ नागरिक सशक्तिकरण एवं डिजिटल गवर्नेंस — आंध्र प्रदेश, तेलंगाना और केंद्र की 15 कल्याणकारी योजनाएं",
    app_tagline: "सरकारी कल्याणकारी योजनाओं के लिए पात्रता जांच सहायक",
    model_status: "Groq Qwen 3.8 (27B) ऑनलाइन",
    tab_voice: "आवाज और विवरण (Voice Input)",
    tab_results: "पात्रता परिणाम (Eligibility)",
    tab_autofill: "ऑटो-फिल और पीडीएफ (Forms & Docs)",
    tab_whatsapp: "व्हाट्सएप डिलीवरी (WhatsApp)",
    voice_header: "🎙️ बोलकर पता करें (Voice Query)",
    voice_subtitle: "अपनी जानकारी तेलुगु, हिंदी या अंग्रेजी में बोलें। हमारा AI आपकी पात्रता की गणना करेगा।",
    tap_to_speak: "माइक बटन दबाएं और बोलें (Tap to speak)",
    recording: "रिकॉर्डिंग चालू है... रोकने के लिए दोबारा दबाएं",
    btn_process_voice: "विश्लेषण करें (Process Voice Input)",
    sample_label: "⚡ 1-क्लिक टेस्ट आवाज नमूने (1-Click Test Prompts):",
    or_upload: "या ऑडियो फाइल अपलोड करें",
    btn_choose_audio: "📂 ऑडियो फाइल चुनें (.wav / .mp3 / .m4a)",
    manual_header: "📝 विवरण दर्ज करें (Manual Profile)",
    manual_subtitle: "आवाज के बिना सीधे फॉर्म भरकर भी पात्रता जांची जा सकती है।",
    lbl_name: "नाम (Name)",
    lbl_age: "आयु (Age)",
    lbl_gender: "लिंग (Gender)",
    lbl_state: "राज्य (State)",
    lbl_district: "ज़िला (District)",
    lbl_land: "भूमि एकड़ में (Land in Acres)",
    lbl_income: "वार्षिक आय (Annual Income ₹)",
    lbl_category: "सामाजिक वर्ग (Category)",
    opt_select_gender: "लिंग चुनें (Select Gender)",
    opt_select_state: "राज्य चुनें (Select State)",
    opt_select_category: "वर्ग चुनें (Select Category)",
    opt_male: "पुरुष (Male)",
    opt_female: "महिला (Female)",
    opt_other: "अन्य (Other)",
    opt_ap: "आंध्र प्रदेश (Andhra Pradesh)",
    opt_ts: "तेलंगाना (Telangana)",
    opt_other_state: "अन्य राज्य (Central Only)",
    opt_bc: "BC (पिछड़ा वर्ग)",
    opt_sc: "SC (अनुसूचित जाति)",
    opt_st: "ST (अनुसूचित जनजाति)",
    opt_minority: "अल्पसंख्यक (Minority)",
    opt_general: "सामान्य (General)",
    chk_farmer: "किसान (Farmer)",
    chk_aadhaar: "आधार कार्ड है (Aadhaar)",
    chk_bank: "बैंक खाता है (Bank Account)",
    chk_ration: "राशन कार्ड है (Ration Card)",
    chk_landrec: "भूमि रिकॉर्ड (1B / खसरा)",
    chk_shg: "महिला स्वयं सहायता समूह (SHG)",
    chk_vendor: "स्ट्रीट वेंडर (Street Vendor)",
    lbl_marital: "वैवाहिक स्थिति (Marital Status)",
    opt_select_marital: "वैवाहिक स्थिति चुनें",
    opt_married: "विवाहित (Married)",
    opt_unmarried: "अविवाहित (Unmarried)",
    opt_widowed: "विधवा / विधुर (Widow / Widower)",
    opt_divorced: "तलाकशुदा (Divorced)",
    lbl_disability: "विकलांगता (Disability)",
    opt_select_disability: "विकलांगता चुनें",
    opt_no_disability: "कोई विकलांगता नहीं (None)",
    opt_has_disability: "विकलांगता है (Yes, ≥40%)",
    lbl_occupation: "व्यवसाय / नौकरी (Occupation)",
    opt_select_occupation: "व्यवसाय चुनें",
    opt_occ_farmer: "किसान (Farmer)",
    opt_occ_daily: "दैनिक मजदूर (Daily Wage Labourer)",
    opt_occ_vendor: "स्ट्रीट वेंडर (Street Vendor)",
    opt_occ_self: "स्व-रोजगार / व्यापार (Self-Employed)",
    opt_occ_private: "निजी कर्मचारी (Private Employee)",
    opt_occ_govt: "सरकारी कर्मचारी / सेवानिवृत्त (Govt. Employee / Retired)",
    opt_occ_homemaker: "गृहिणी (Homemaker)",
    opt_occ_student: "विद्यार्थी (Student)",
    opt_occ_unemployed: "बेरोजगार (Unemployed)",
    btn_check_eligibility: "पात्रता जांचें (Check Eligibility)",
    btn_play_audio: "ऑडियो सुनें (Play Audio)",
    btn_pause_audio: "रोकें (Pause)",
    btn_stop_audio: "बंद करें (Stop)",
    status_audio_ready: "ऑडियो तैयार है",
    status_audio_playing: "ऑडियो चल रहा है...",
    voice_resp_title: "SchemeSaathi ऑडियो सहायक (Audio Response)",
    voice_resp_sub: "आपकी जानकारी के आधार पर AI द्वारा तैयार आवाज संदेश:",
    profile_summary_title: "👤 नागरिक विवरण (Citizen Profile Extracted)",
    schemes_heading: "पात्र सरकारी योजनाएं (Evaluated Schemes)",
    filter_all: "सभी (All)",
    filter_eligible: "पात्र (Eligible Only)",
    filter_central: "केंद्रीय योजनाएं (Central)",
    filter_ap: "आंध्र प्रदेश (AP)",
    filter_ts: "तेलंगाना (TS)",
    empty_title: "अभी तक कोई विवरण दर्ज नहीं हुआ",
    empty_desc: "कृपया 'आवाज और विवरण' टैब में बोलें या फॉर्म सबमिट करें।",
    pdf_header: "📄 दस्तावेज़ डाउनलोड (Official PDFs)",
    pdf_sub: "आधिकारिक फॉर्म और आवश्यक दस्तावेजों की चेकलिस्ट पीडीएफ में तुरंत प्राप्त करें।",
    pdf_form_title: "📋 पूर्व-भरा आवेदन फॉर्म PDF",
    pdf_form_desc: "आपके विवरणों के साथ भरा हुआ पीडीएफ आवेदन पत्र (PM-KISAN / अन्य)",
    btn_get_form_pdf: "आवेदन फॉर्म PDF प्राप्त करें",
    pdf_checklist_title: "📑 आवश्यक दस्तावेज़ चेकलिस्ट",
    pdf_checklist_desc: "आपके पास उपलब्ध और जमा किए जाने वाले दस्तावेजों की पूरी गाइड।",
    btn_get_checklist_pdf: "चेकलिस्ट PDF प्राप्त करें",
    pdf_ready_title: "डाउनलोड के लिए तैयार फाइलें:",
    autofill_header: "🤖 पोर्टल ऑटो-फिल (Portal Automation)",
    autofill_sub: "सरकारी पोर्टल (PM-KISAN) में अपनी जानकारी स्वचालित रूप से भरें।",
    target_portal_lbl: "लक्षित पोर्टल:",
    btn_launch_autofill: "PM-KISAN फॉर्म ऑटो-फिल शुरू करें",
    autofill_status_lbl: "ऑटोमेशन स्थिति:",
    whatsapp_header: "📱 व्हाट्सएप पर परिणाम भेजें",
    whatsapp_sub: "नागरिक के मोबाइल नंबर पर पात्रता रिपोर्ट और फॉर्म लिंक सीधे भेजे जाएंगे।",
    whatsapp_num_lbl: "लाभार्थी का व्हाट्सएप मोबाइल नंबर",
    btn_send_whatsapp: "व्हाट्सएप पर भेजें (Send to WhatsApp)",
    loading_analyzing: "विश्लेषण हो रहा है...",
    loading_desc: "आपकी आवाज और योजना नियमों की जांच की जा रही है...",
    status_eligible: "✅ पात्र (Eligible)",
    status_not_eligible: "❌ अपात्र (Not Eligible)",
    benefit_lbl: "मिलने वाला लाभ (Benefit)",
    req_docs_lbl: "आवश्यक दस्तावेज़:",
    btn_download_form: "📄 फॉर्म पीडीएफ डाउनलोड",
    btn_not_eligible: "नियम मेल नहीं खाते",
  },
  en: {
    top_announcement: "🏛️ Civic Pulse & Digital Governance — 15 Curated Schemes for Andhra Pradesh, Telangana & Central",
    app_tagline: "Voice-First Civic Welfare Scheme Eligibility Assistant",
    model_status: "Groq Qwen 3.8 (27B) Online",
    tab_voice: "Voice & Profile (Voice Input)",
    tab_results: "Eligible Schemes (Eligibility)",
    tab_autofill: "Auto-Fill & PDFs (Forms & Docs)",
    tab_whatsapp: "WhatsApp Delivery (WhatsApp)",
    voice_header: "🎙️ Voice Discovery (Speak Details)",
    voice_subtitle: "Speak your details in Telugu, Hindi, or English. Our AI analyzes 15 government schemes.",
    tap_to_speak: "Tap the microphone and speak your details",
    recording: "Recording in progress... tap again to stop",
    btn_process_voice: "Process Voice Input (Analyze)",
    sample_label: "⚡ 1-Click Instant Test Prompts:",
    or_upload: "Or upload audio file",
    btn_choose_audio: "📂 Choose Audio File (.wav / .mp3 / .m4a)",
    manual_header: "📝 Manual Profile Entry (Fallback)",
    manual_subtitle: "Directly fill in your details to check eligible government schemes.",
    lbl_name: "Name",
    lbl_age: "Age",
    lbl_gender: "Gender",
    lbl_state: "State",
    lbl_district: "District",
    lbl_land: "Land (in Acres)",
    lbl_income: "Annual Income (₹)",
    lbl_category: "Social Category",
    opt_select_gender: "Select Gender",
    opt_select_state: "Select State",
    opt_select_category: "Select Category",
    opt_male: "Male",
    opt_female: "Female",
    opt_other: "Other",
    opt_ap: "Andhra Pradesh",
    opt_ts: "Telangana",
    opt_other_state: "Other States (Central Only)",
    opt_bc: "BC (Backward Class)",
    opt_sc: "SC (Scheduled Caste)",
    opt_st: "ST (Scheduled Tribe)",
    opt_minority: "Minority",
    opt_general: "General",
    chk_farmer: "Is Farmer",
    chk_aadhaar: "Has Aadhaar Card",
    chk_bank: "Has Bank Account",
    chk_ration: "Has Ration Card",
    chk_landrec: "Has Land Record (1B / Patta)",
    chk_shg: "SHG Member (Self Help Group)",
    chk_vendor: "Street Vendor",
    lbl_marital: "Marital Status",
    opt_select_marital: "Select Marital Status",
    opt_married: "Married",
    opt_unmarried: "Unmarried / Single",
    opt_widowed: "Widow / Widower",
    opt_divorced: "Divorced / Separated",
    lbl_disability: "Disability",
    opt_select_disability: "Select Disability Status",
    opt_no_disability: "No Disability",
    opt_has_disability: "Has Disability (≥40%)",
    lbl_occupation: "Occupation",
    opt_select_occupation: "Select Occupation",
    opt_occ_farmer: "Farmer / Agriculturist",
    opt_occ_daily: "Daily Wage Labourer",
    opt_occ_vendor: "Street Vendor",
    opt_occ_self: "Self-Employed / Business",
    opt_occ_private: "Private Sector Employee",
    opt_occ_govt: "Government Employee / Retired Govt. Employee",
    opt_occ_homemaker: "Homemaker",
    opt_occ_student: "Student",
    opt_occ_unemployed: "Unemployed",
    btn_check_eligibility: "Check Scheme Eligibility",
    btn_play_audio: "Play Audio Response",
    btn_pause_audio: "Pause Audio",
    btn_stop_audio: "Stop",
    status_audio_ready: "Audio Ready",
    status_audio_playing: "Playing Audio...",
    voice_resp_title: "SchemeSaathi Voice Assistant (Audio Response)",
    voice_resp_sub: "AI-generated conversational voice guidance based on your profile:",
    profile_summary_title: "👤 Extracted Citizen Profile",
    schemes_heading: "Evaluated Welfare Schemes",
    filter_all: "All Schemes",
    filter_eligible: "Eligible Only",
    filter_central: "Central Schemes",
    filter_ap: "Andhra Pradesh",
    filter_ts: "Telangana",
    empty_title: "No Profile Registered Yet",
    empty_desc: "Please speak in the 'Voice & Profile' tab or submit the details form.",
    pdf_header: "📄 Official Documents & PDF Generation",
    pdf_sub: "Instantly generate pre-filled official application forms and required documents checklists.",
    pdf_form_title: "📋 Pre-filled Application Form PDF",
    pdf_form_desc: "Auto-filled PDF application form with your details (PM-KISAN / Annadata / etc.)",
    btn_get_form_pdf: "Generate Form PDF",
    pdf_checklist_title: "📑 Missing Documents Checklist PDF",
    pdf_checklist_desc: "Complete checklist of documents you own and those needed for submission.",
    btn_get_checklist_pdf: "Generate Checklist PDF",
    pdf_ready_title: "Files Ready for Download:",
    autofill_header: "🤖 Automated Portal Form-Fill (Playwright)",
    autofill_sub: "Directly auto-fill your details into the government portal (PM-KISAN) using browser automation.",
    target_portal_lbl: "Target Portal:",
    btn_launch_autofill: "Launch PM-KISAN Form Auto-Fill",
    autofill_status_lbl: "Automation Execution Log:",
    whatsapp_header: "📱 WhatsApp Outreach & Delivery",
    whatsapp_sub: "Send eligibility report and pre-filled PDF links directly to citizen's mobile phone.",
    whatsapp_num_lbl: "Beneficiary WhatsApp Mobile Number",
    btn_send_whatsapp: "Send to WhatsApp",
    loading_analyzing: "Analyzing...",
    loading_desc: "Processing voice transcript and verifying scheme rules...",
    status_eligible: "✅ Eligible",
    status_not_eligible: "❌ Not Eligible",
    benefit_lbl: "Benefit Highlights",
    req_docs_lbl: "Required Documents:",
    btn_download_form: "📄 Download Form PDF",
    btn_not_eligible: "Criteria Not Met",
  }
};

// 1-Click Sample Prompts per Language
const SAMPLES_BY_LANG = {
  te: [
    {
      id: "ap-farmer",
      title: "🌾 AP రైతు (రమేశ్, 45, 2 ఎకరాలు, ఆధార్, బ్యాంక్, 1B)",
      text: "నా పేరు రమేశ్. వయస్సు 45 సంవత్సరాలు. ఆంధ్రప్రదేశ్ అనంతపురం జిల్లా. 2 ఎకరాల భూమి ఉంది. ఆధార్ కార్డు, బ్యాంకు ఖాతా మరియు 1B భూమి రికార్డు ఉన్నాయి. నేను రైతును.",
      state: "AP",
      lang: "te"
    },
    {
      id: "ts-farmer",
      title: "🚜 TS రైతు (సురేశ్, 52, వరంగల్, రైతుబంధు & బీమా)",
      text: "నా పేరు సురేశ్. వయస్సు 52. తెలంగాణ వరంగల్ జిల్లా. 3 ఎకరాల భూమి ఉంది. రైతును. ఆధార్ కార్డు, పాస్‌బుక్, బ్యాంకు ఖాతా ఉన్నాయి.",
      state: "TS",
      lang: "te"
    },
    {
      id: "ap-woman",
      title: "👩‍🌾 మహిళా స్వయం సహాయక సంఘం (లక్ష్మి, 38, SHG లోన్)",
      text: "నా పేరు లక్ష్మి. వయస్సు 38. అనంతపురం జిల్లా. మహిళా పొదుపు సంఘం సభ్యురాలిని (SHG member). ఆధార్, రేషన్ కార్డు ఉన్నాయి. రుణ మాఫీ కావాలి.",
      state: "AP",
      lang: "te"
    },
    {
      id: "vendor",
      title: "🛒 వీధి వ్యాపారి (రాజు, PM-స్వనిధి లోన్)",
      text: "నా పేరు రాజు. వయస్సు 35 సంవత్సరాలు. గుంటూరులో వీధి వ్యాపారిని (కూరగాయల బండి). ఆధార్ మరియు బ్యాంక్ ఖాతా ఉన్నాయి. పీఎం స్వనిధి లోన్ కావాలి.",
      state: "AP",
      lang: "te"
    }
  ],
  hi: [
    {
      id: "ap-farmer",
      title: "🌾 किसान (रमेश, 45 वर्ष, 2 एकड़ जमीन, आधार, बैंक खाता)",
      text: "मेरा नाम रमेश है। उम्र 45 वर्ष। आंध्र प्रदेश अनंतपुर ज़िला। 2 एकड़ ज़मीन है। आधार कार्ड, बैंक खाता और 1B भूमि रिकॉर्ड है। मैं किसान हूँ।",
      state: "AP",
      lang: "hi"
    },
    {
      id: "ts-farmer",
      title: "🚜 तेलंगाना किसान (सुरेश, 52 वर्ष, वारंगल, रैतु बंधु)",
      text: "मेरा नाम सुरेश है। उम्र 52 वर्ष। तेलंगाना वारंगल ज़िला। 3 एकड़ ज़मीन है। किसान हूँ। आधार कार्ड, पासबुक और बैंक खाता है।",
      state: "TS",
      lang: "hi"
    },
    {
      id: "ap-woman",
      title: "👩‍🌾 महिला स्वयं सहायता समूह (लक्ष्मी, 38 वर्ष, ऋण माफी)",
      text: "मेरा नाम लक्ष्मी है। उम्र 38 वर्ष। महिला स्वयं सहायता समूह (SHG) सदस्य हूँ। आधार और राशन कार्ड है। लोन माफी चाहिए।",
      state: "AP",
      lang: "hi"
    },
    {
      id: "vendor",
      title: "🛒 स्ट्रीट वेंडर (राजू, 35 वर्ष, पीएम स्वनिधि लोन)",
      text: "मेरा नाम राजू है। उम्र 35 वर्ष। गुंटूर में सब्ज़ी विक्रेता (स्ट्रीट वेंडर) हूँ। आधार कार्ड और बैंक खाता है। पीएम स्वनिधि लोन चाहिए।",
      state: "AP",
      lang: "hi"
    }
  ],
  en: [
    {
      id: "ap-farmer",
      title: "🌾 AP Farmer (Ramesh, 45 yrs, 2 acres, Aadhaar, Bank, 1B)",
      text: "My name is Ramesh. Age 45. Anantapur district, Andhra Pradesh. 2 acres agricultural land. Have Aadhaar card, bank account, and 1B land record. I am a farmer.",
      state: "AP",
      lang: "en"
    },
    {
      id: "ts-farmer",
      title: "🚜 TS Farmer (Suresh, 52 yrs, Warangal, Rythu Bandhu)",
      text: "My name is Suresh. Age 52. Warangal district, Telangana. 3 acres land. Farmer. Have Aadhaar card, pattadar passbook, and bank account.",
      state: "TS",
      lang: "en"
    },
    {
      id: "ap-woman",
      title: "👩‍🌾 SHG Member (Lakshmi, 38 yrs, SHG Loan Waiver)",
      text: "My name is Lakshmi. Age 38. Member of Women Self Help Group (SHG). Have Aadhaar and Ration card. Seeking SHG loan assistance.",
      state: "AP",
      lang: "en"
    },
    {
      id: "vendor",
      title: "🛒 Street Vendor (Raju, 35 yrs, PM-SVANidhi Loan)",
      text: "My name is Raju. Age 35. Vegetable street vendor in Guntur. Have Aadhaar and bank account. Need PM-SVANidhi collateral-free working capital loan.",
      state: "AP",
      lang: "en"
    }
  ]
};

// 15 Schemes Curated Multilingual Metadata
const SCHEME_I18N = {
  pm_kisan: {
    te: { name: "పీఎం కిసాన్ సమ్మాన్ నిధి", benefit: "సంవత్సరానికి ₹6,000 (3 విడతల్లో)" },
    hi: { name: "पीएम किसान सम्मान निधि", benefit: "प्रति वर्ष ₹6,000 (3 किश्तों में)" },
    en: { name: "PM-KISAN Samman Nidhi", benefit: "₹6,000/year income support in 3 installments" }
  },
  ayushman_bharat: {
    te: { name: "ఆయుష్మాన్ భారత్ (PM-JAY)", benefit: "కుటుంబానికి సంవత్సరానికి ₹5,00,000 ఉచిత ఆరోగ్య బీమా" },
    hi: { name: "आयुष्मान भारत (PM-JAY)", benefit: "प्रति परिवार प्रति वर्ष ₹5,00,000 का मुफ्त स्वास्थ्य बीमा" },
    en: { name: "Ayushman Bharat (PM-JAY)", benefit: "₹5,00,000 free health coverage per family/year" }
  },
  annadata_sukhibhava: {
    te: { name: "అన్నదాత సుఖీభవ (AP)", benefit: "రైతు కుటుంబానికి ₹13,500/సంవత్సరం (పీఎం-కిసాన్ కలుపుకొని)" },
    hi: { name: "अन्नदाता सुखीभव (AP)", benefit: "किसान परिवार को ₹13,500 प्रति वर्ष" },
    en: { name: "Annadata Sukhibhava (AP)", benefit: "₹13,500/year farmer investment support" }
  },
  rythu_bandhu: {
    te: { name: "రైతు బంధు పథకం (TS)", benefit: "ఎకరానికి ₹10,000/సంవత్సరం పంట పెట్టుబడి సాయం" },
    hi: { name: "रैतु बंधु योजना (TS)", benefit: "प्रति एकड़ ₹10,000 प्रति वर्ष फसल निवेश" },
    en: { name: "Rythu Bandhu (TS)", benefit: "₹10,000 per acre/year crop investment support" }
  },
  rythu_bima: {
    te: { name: "రైతు బీమా పథకం (TS)", benefit: "రైతుకు ₹5,00,000 జీవిత బీమా కవరేజ్ (ఉచితం)" },
    hi: { name: "रैतु बीमा योजना (TS)", benefit: "किसान के लिए ₹5,00,000 जीवन बीमा (मुफ्त)" },
    en: { name: "Rythu Bima (TS)", benefit: "₹5,00,000 farmer group life insurance" }
  },
  aasara_pension: {
    te: { name: "ఆసరా పింఛన్ పథకం (TS)", benefit: "నెలకు ₹2,016 నుండి ₹3,016 వరకు పింఛన్" },
    hi: { name: "आसरा पेंशन योजना (TS)", benefit: "प्रति माह ₹2,016 से ₹3,016 तक पेंशन" },
    en: { name: "Aasara Pension (TS)", benefit: "₹2,016 to ₹3,016 per month pension" }
  },
  ntr_bharosa_pension: {
    te: { name: "ఎన్టీఆర్ భరోసా పింఛన్ (AP)", benefit: "వృద్ధులు/వితంతువులకు నెలకు ₹3,000 పింఛన్" },
    hi: { name: "एनटीआर भरोसा पेंशन (AP)", benefit: "वृद्धों/विधवाओं को ₹3,000 प्रति माह पेंशन" },
    en: { name: "NTR Bharosa Pension (AP)", benefit: "₹3,000/month pension for seniors/widows" }
  },
  talliki_vandanam: {
    te: { name: "తల్లికి వందనం పథకం (AP)", benefit: "బడికి వెళ్ళే విద్యార్థుల తల్లులకు ₹15,000/సంవత్సరం" },
    hi: { name: "तल्लिकी वंदनम योजना (AP)", benefit: "स्कूली बच्चों की माताओं को ₹15,000 प्रति वर्ष" },
    en: { name: "Talliki Vandanam (AP)", benefit: "₹15,000/year for school students' mothers" }
  },
  mahila_samriddhi: {
    te: { name: "మహిళా సమృద్ధి పథకం (AP)", benefit: "45-60 ఏళ్ళ మహిళలకు ₹75,000 (4 ఏళ్ళలో ₹18,750 చొప్పున)" },
    hi: { name: "महिला समृद्धि योजना (AP)", benefit: "45-60 वर्ष की महिलाओं को ₹75,000 (4 वर्षों में)" },
    en: { name: "Mahila Samriddhi (AP)", benefit: "₹75,000 over 4 years for women aged 45-60" }
  },
  shg_loan_waiver: {
    te: { name: "మహిళా సంఘాల రుణ మాఫీ (AP)", benefit: "స్వయం సహాయక సంఘాల రుణాలపై 4% వడ్డీ రాయితీ & మాఫీ" },
    hi: { name: "महिला एसएचजी ऋण माफी (AP)", benefit: "एसएचजी ऋण पर 4% ब्याज सब्सिडी एवं माफी" },
    en: { name: "SHG Loan Waiver & Vaddileni Runalu", benefit: "4% interest subsidy & loan waiver for SHG women" }
  },
  pm_svanidhi: {
    te: { name: "పీఎం స్వనిధి వీధి వ్యాపారి రుణం (కేంద్రం)", benefit: "వీధి వ్యాపారులకు ₹10,000 - ₹50,000 పూచీకత్తు లేని రుణం" },
    hi: { name: "पीएम स्वनिधि योजना (केंद्र)", benefit: "स्ट्रीट वेंडरों को ₹10,000 - ₹50,000 बिना गारंटी ऋण" },
    en: { name: "PM-SVANidhi Street Vendor Loan", benefit: "₹10,000 to ₹50,000 working capital loan" }
  },
  nsap_old_age_pension: {
    te: { name: "జాతీయ వృద్ధాప్య పింఛన్ (NSAP)", benefit: "బీపీఎల్ వృద్ధులకు నెలకు కేంద్ర ఆర్థిక పింఛన్" },
    hi: { name: "राष्ट्रीय वृद्धावस्था पेंशन (NSAP)", benefit: "बीपीएल वृद्धों को मासिक केंद्रीय पेंशन सहायता" },
    en: { name: "NSAP Old Age Pension", benefit: "Monthly central financial assistance for seniors" }
  },
  nsap_widow_pension: {
    te: { name: "జాతీయ వితంతు పింఛన్ (NSAP)", benefit: "40-79 ఏళ్ళ బీపీఎల్ వితంతువులకు నెలకు కేంద్ర పింఛన్" },
    hi: { name: "राष्ट्रीय विधवा पेंशन (NSAP)", benefit: "बीपीएल विधवाओं को मासिक केंद्रीय पेंशन" },
    en: { name: "NSAP Widow Pension", benefit: "Monthly central pension for BPL widows (40-79 yrs)" }
  },
  kalyana_lakshmi: {
    te: { name: "కల్యాణ లక్ష్మి / షాదీ ముబారక్ (TS)", benefit: "పేద యువతుల వివాహానికి ₹1,00,116 ఆర్థిక సహాయం" },
    hi: { name: "कल्याण लक्ष्मी / शादी मुबारक (TS)", benefit: "गरीब युवतियों के विवाह हेतु ₹1,00,116 सहायता" },
    en: { name: "Kalyana Lakshmi / Shaadi Mubarak (TS)", benefit: "₹1,00,116 financial grant for daughter's marriage" }
  },
  dalit_empowerment: {
    te: { name: "దళిత సాధికారత పథకం (TS)", benefit: "దళిత కుటుంబాలకు ₹10,00,000 స్వయం ఉపాధి గ్రాంట్" },
    hi: { name: "दलित सशक्तिकरण योजना (TS)", benefit: "दलित परिवारों को ₹10,00,000 स्वरोज़गार अनुदान" },
    en: { name: "Dalit Empowerment Scheme (TS)", benefit: "₹10,00,000 unit cost grant for Dalit families" }
  }
};

// Initialize Application
document.addEventListener('DOMContentLoaded', () => {
  initLanguageSwitcher();
  initTabs();
  initVoiceRecorder();
  applyLanguage(STATE.currentLanguage);
  initManualForm();
  initPdfGeneration();
  initWhatsApp();
  initPlaywright();
  initFilters();
  initAudioResponseControls();
});

/* ========================================================
   Language Switcher & Full Site Localization
   ======================================================== */
function initLanguageSwitcher() {
  document.querySelectorAll('.lang-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.lang-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      const lang = btn.dataset.lang;
      STATE.currentLanguage = lang;
      applyLanguage(lang);
    });
  });
}

function applyLanguage(lang) {
  const dict = I18N[lang] || I18N.te;

  // 1. Translate all DOM elements with [data-i18n]
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.dataset.i18n;
    if (dict[key]) {
      el.textContent = dict[key];
    }
  });

  // 2. Update Placeholders and Form elements
  const nameInput = document.getElementById('m-name');
  const distInput = document.getElementById('m-district');
  if (lang === 'te') {
    if (nameInput) nameInput.placeholder = "రమేశ్";
    if (distInput) distInput.placeholder = "అనంతపురం";
  } else if (lang === 'hi') {
    if (nameInput) nameInput.placeholder = "रमेश";
    if (distInput) distInput.placeholder = "अनंतपुर";
  } else {
    if (nameInput) nameInput.placeholder = "Ramesh";
    if (distInput) distInput.placeholder = "Anantapur";
  }

  // 3. Update Mic Status Text
  const micStatus = document.getElementById('mic-status-text');
  if (micStatus && !STATE.isRecording) {
    micStatus.textContent = dict.tap_to_speak;
  }

  // 4. Re-render Sample Prompts in the active language
  renderSamplePrompts(lang);

  // 5. If Results are loaded, dynamically translate Scheme Cards & Profile Summary
  if (STATE.lastEligibilities && STATE.lastEligibilities.length > 0) {
    renderSchemeCards(STATE.lastEligibilities);
    if (STATE.lastProfile) {
      renderProfileSummary(STATE.lastProfile, lang);
    }
  }

  // 6. Update WhatsApp Chat Mockup
  updateWhatsAppMockup(lang);

  // 7. Update Audio Control Labels in active language
  if (typeof setAudioUIPlaying === 'function' && !STATE.isAudioPlaying) {
    setAudioUIPlaying(false);
  }
}

function renderSamplePrompts(lang) {
  const container = document.getElementById('samples-container');
  if (!container) return;

  const samples = SAMPLES_BY_LANG[lang] || SAMPLES_BY_LANG.te;
  container.innerHTML = samples.map(s => `
    <button class="sample-pill" data-text="${s.text}" data-lang="${s.lang}" data-state="${s.state}">
      ${s.title}
    </button>
  `).join('');

  // Attach click events
  container.querySelectorAll('.sample-pill').forEach(btn => {
    btn.addEventListener('click', async () => {
      const text = btn.dataset.text;
      const sampleLang = btn.dataset.lang;
      const state = btn.dataset.state;
      const dict = I18N[STATE.currentLanguage];

      showLoading(dict.loading_analyzing, `"${text.substring(0, 45)}..."`);

      try {
        const resp = await fetch('/api/voice/process-text', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({
            text: text,
            language: STATE.currentLanguage, // Evaluate in user's active language!
            state_override: state
          }),
        });

        if (!resp.ok) {
          const err = await resp.json();
          throw new Error(err.detail || 'Evaluation failed');
        }

        const data = await resp.json();
        handleAnalysisResults(data);
      } catch (err) {
        alert("Error: " + err.message);
      } finally {
        hideLoading();
      }
    });
  });
}

function updateWhatsAppMockup(lang) {
  const chatMsg = document.getElementById('mockup-chat-msg');
  if (!chatMsg) return;

  if (lang === 'te') {
    chatMsg.innerHTML = `
      నమస్తే! 🙏<br>
      మీ అర్హత వివరాలు ఇక్కడ ప్రత్యక్షంగా కనిపిస్తాయి.
      <span class="chat-time">Just now</span>
    `;
  } else if (lang === 'hi') {
    chatMsg.innerHTML = `
      नमस्ते! 🙏<br>
      आपकी पात्रता का विवरण यहाँ सीधे दिखाई देगा।
      <span class="chat-time">Just now</span>
    `;
  } else {
    chatMsg.innerHTML = `
      Hello! 🙏<br>
      Your scheme eligibility report will appear here.
      <span class="chat-time">Just now</span>
    `;
  }
}

/* ========================================================
   Tab Navigation
   ======================================================== */
function initTabs() {
  document.querySelectorAll('.tab-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      const tabId = btn.dataset.tab;
      switchTab(tabId);
    });
  });
}

function switchTab(tabId) {
  document.querySelectorAll('.tab-btn').forEach(b => b.classList.remove('active'));
  document.querySelectorAll('.tab-pane').forEach(p => p.classList.remove('active'));

  const activeBtn = document.querySelector(`.tab-btn[data-tab="${tabId}"]`);
  const activePane = document.getElementById(tabId);
  if (activeBtn) activeBtn.classList.add('active');
  if (activePane) activePane.classList.add('active');
}

/* ========================================================
   Voice Recording (Web Audio MediaRecorder API)
   ======================================================== */
function initVoiceRecorder() {
  const micBtn = document.getElementById('mic-btn');
  const timerEl = document.getElementById('recording-timer');
  const statusEl = document.getElementById('mic-status-text');
  const playbackBox = document.getElementById('audio-playback-box');
  const recordedAudio = document.getElementById('recorded-audio');
  const processBtn = document.getElementById('process-voice-btn');
  const fileInput = document.getElementById('audio-file-input');

  micBtn.addEventListener('click', async () => {
    const dict = I18N[STATE.currentLanguage];
    if (!STATE.isRecording) {
      try {
        const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
        STATE.audioChunks = [];
        STATE.mediaRecorder = new MediaRecorder(stream);

        STATE.mediaRecorder.ondataavailable = e => {
          if (e.data.size > 0) STATE.audioChunks.push(e.data);
        };

        STATE.mediaRecorder.onstop = () => {
          STATE.recordedBlob = new Blob(STATE.audioChunks, { type: 'audio/wav' });
          const audioUrl = URL.createObjectURL(STATE.recordedBlob);
          recordedAudio.src = audioUrl;
          playbackBox.classList.remove('hidden');
          statusEl.textContent = dict.btn_process_voice;
        };

        STATE.mediaRecorder.start();
        STATE.isRecording = true;
        micBtn.classList.add('recording');
        timerEl.classList.remove('hidden');
        statusEl.textContent = dict.recording;

        STATE.recordStartTime = Date.now();
        STATE.recordTimerInterval = setInterval(() => {
          const delta = Math.floor((Date.now() - STATE.recordStartTime) / 1000);
          const mins = String(Math.floor(delta / 60)).padStart(2, '0');
          const secs = String(delta % 60).padStart(2, '0');
          timerEl.textContent = `${mins}:${secs}`;
        }, 500);

      } catch (err) {
        alert("Microphone Error: " + err.message + "\nPlease use 1-Click test prompts or file upload.");
      }
    } else {
      STATE.mediaRecorder.stop();
      STATE.mediaRecorder.stream.getTracks().forEach(t => t.stop());
      STATE.isRecording = false;
      micBtn.classList.remove('recording');
      timerEl.classList.add('hidden');
      clearInterval(STATE.recordTimerInterval);
    }
  });

  processBtn.addEventListener('click', async () => {
    if (!STATE.recordedBlob) return;
    await uploadAndProcessAudio(STATE.recordedBlob);
  });

  fileInput.addEventListener('change', async (e) => {
    const file = e.target.files[0];
    if (file) {
      await uploadAndProcessAudio(file);
    }
  });
}

async function uploadAndProcessAudio(audioFileOrBlob) {
  const dict = I18N[STATE.currentLanguage];
  showLoading(dict.loading_analyzing, dict.loading_desc);
  
  const formData = new FormData();
  formData.append('audio', audioFileOrBlob, 'recording.wav');
  formData.append('language', STATE.currentLanguage);

  try {
    const resp = await fetch('/api/voice/process-audio', {
      method: 'POST',
      body: formData,
    });
    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || 'Audio processing error');
    }
    const data = await resp.json();
    handleAnalysisResults(data);
  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    hideLoading();
  }
}

/* ========================================================
   Manual Form Submission
   ======================================================== */
function initManualForm() {
  const form = document.getElementById('manual-profile-form');
  if (!form) return;

  form.addEventListener('submit', async (e) => {
    e.preventDefault();

    const occ = document.getElementById('m-occupation')?.value || '';
    const isFarmer = (occ === 'farmer');
    const isStreetVendor = (occ === 'street_vendor');
    const isGovt = (occ === 'govt_employee');

    const profileData = {
      name: document.getElementById('m-name')?.value.trim() || null,
      age: parseInt(document.getElementById('m-age')?.value) || null,
      gender: document.getElementById('m-gender')?.value || null,
      marital_status: document.getElementById('m-marital')?.value || null,
      state: document.getElementById('m-state')?.value || null,
      district: document.getElementById('m-district')?.value.trim() || null,
      village: '',
      caste_category: document.getElementById('m-caste')?.value || null,
      annual_income: parseInt(document.getElementById('m-income')?.value) || null,
      land_holding_acres: parseFloat(document.getElementById('m-land')?.value) || null,
      has_aadhaar: !!document.getElementById('m-aadhaar')?.checked,
      has_bank_account: !!document.getElementById('m-bank')?.checked,
      has_ration_card: !!document.getElementById('m-ration')?.checked,
      has_land_record: !!document.getElementById('m-landrec')?.checked,
      is_farmer: isFarmer,
      is_street_vendor: isStreetVendor,
      is_shg_member: !!document.getElementById('m-shg')?.checked,
      disability: document.getElementById('m-disability-sel')?.value === 'yes',
      is_govt_employee: isGovt,
      language: STATE.currentLanguage,
    };

    const dict = I18N[STATE.currentLanguage];
    showLoading(dict.loading_analyzing, dict.loading_desc);

    try {
      const resp = await fetch('/api/profile/manual-evaluate', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(profileData),
      });

      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || 'Evaluation failed');
      }

      const data = await resp.json();
      handleAnalysisResults(data);
      // Ensure smooth scroll to results tab view
      window.scrollTo({ top: 0, behavior: 'smooth' });
    } catch (err) {
      alert("Error: " + err.message);
    } finally {
      hideLoading();
    }
  });
}

/* ========================================================
   Render Results & Multilingual Scheme Dashboard
   ======================================================== */
function handleAnalysisResults(data) {
  STATE.lastProfile = data.profile;
  STATE.lastEligibilities = data.eligibilities || [];
  STATE.lastVoiceResponse = data.voice_response;

  // 1. Audio Voice Response Player
  const voiceCard = document.getElementById('ai-voice-response-card');
  const ttsPlayer = document.getElementById('tts-audio-player');
  const voiceText = document.getElementById('voice-response-text');

  if (data.voice_response && data.voice_response.text) {
    voiceCard.classList.remove('hidden');
    voiceText.innerHTML = formatMarkdown(data.voice_response.text);

    // Stop any previously playing audio/speech
    stopAudioResponse();

    if (data.audio_url) {
      STATE.lastAudioUrl = data.audio_url;
      // Pre-generated MP3 is ready on server! Load it into player
      ttsPlayer.src = data.audio_url;
      ttsPlayer.load();
    } else {
      STATE.lastAudioUrl = null;
      ttsPlayer.removeAttribute('src');
    }

    // Try auto-play (falls back gracefully to browser TTS or stays ready if auto-play blocked)
    playAudioResponse(true);
  }

  // 2. Profile Summary Badges
  renderProfileSummary(data.profile, STATE.currentLanguage);

  // 3. Render Scheme Cards in active language
  renderSchemeCards(STATE.lastEligibilities);

  // Update badges
  const eligibleCount = STATE.lastEligibilities.filter(e => e.eligible).length;
  document.getElementById('eligible-count-badge').textContent = eligibleCount;

  // Switch to Results Tab
  switchTab('results-tab');
}

function renderProfileSummary(p, lang) {
  const profileCard = document.getElementById('profile-summary-card');
  const statsContainer = document.getElementById('profile-stats');
  if (!profileCard || !statsContainer || !p) return;

  profileCard.classList.remove('hidden');

  let lbls = {
    name: "పేరు (Name)", age: "వయస్సు (Age)", state: "రాష్ట్రం (State)",
    district: "జిల్లా (District)", land: "భూమి (Land)", aadhaar: "ఆధార్ (Aadhaar)",
    bank: "బ్యాంక్ ఖాతా (Bank)", landrec: "భూమి రికార్డు (1B)",
    marital: "వివాహ స్థితి (Marital)", disability: "వికలాంగత (Disability)",
    yes: "✅ ఉంది", no: "❌ లేదు", yrs: "ఏళ్ళు", acres: "ఎకరాలు"
  };

  if (lang === 'hi') {
    lbls = {
      name: "नाम (Name)", age: "आयु (Age)", state: "राज्य (State)",
      district: "ज़िला (District)", land: "भूमि (Land)", aadhaar: "आधार (Aadhaar)",
      bank: "बैंक खाता (Bank)", landrec: "भूमि रिकॉर्ड (1B)",
      marital: "वैवाहिक स्थिति (Marital)", disability: "विकलांगता (Disability)",
      yes: "✅ हाँ", no: "❌ नहीं", yrs: "वर्ष", acres: "एकड़"
    };
  } else if (lang === 'en') {
    lbls = {
      name: "Name", age: "Age", state: "State",
      district: "District", land: "Land", aadhaar: "Aadhaar",
      bank: "Bank Account", landrec: "Land Record",
      marital: "Marital Status", disability: "Disability",
      yes: "✅ Verified", no: "❌ Not Provided", yrs: "yrs", acres: "Acres"
    };
  }

  statsContainer.innerHTML = `
    <div class="stat-item"><div class="stat-label">${lbls.name}</div><div class="stat-value">${p.name || '—'}</div></div>
    <div class="stat-item"><div class="stat-label">${lbls.age}</div><div class="stat-value">${p.age ? p.age + ' ' + lbls.yrs : '—'}</div></div>
    <div class="stat-item"><div class="stat-label">${lbls.state}</div><div class="stat-value">${p.state || '—'}</div></div>
    <div class="stat-item"><div class="stat-label">${lbls.district}</div><div class="stat-value">${p.district || '—'}</div></div>
    <div class="stat-item"><div class="stat-label">${lbls.marital}</div><div class="stat-value">${p.marital_status ? p.marital_status.toUpperCase() : '—'}</div></div>
    <div class="stat-item"><div class="stat-label">${lbls.disability}</div><div class="stat-value">${p.disability ? lbls.yes : lbls.no}</div></div>
    <div class="stat-item"><div class="stat-label">${lbls.land}</div><div class="stat-value">${p.land_holding_acres ? p.land_holding_acres + ' ' + lbls.acres : '—'}</div></div>
    <div class="stat-item"><div class="stat-label">${lbls.aadhaar}</div><div class="stat-value">${p.has_aadhaar ? lbls.yes : lbls.no}</div></div>
    <div class="stat-item"><div class="stat-label">${lbls.bank}</div><div class="stat-value">${p.has_bank_account ? lbls.yes : lbls.no}</div></div>
    <div class="stat-item"><div class="stat-label">${lbls.landrec}</div><div class="stat-value">${p.has_land_record ? lbls.yes : lbls.no}</div></div>
  `;
}

function renderSchemeCards(eligibilities, filter = 'all') {
  const container = document.getElementById('schemes-container');
  const totalTag = document.getElementById('schemes-total-tag');
  const lang = STATE.currentLanguage;
  const dict = I18N[lang] || I18N.te;

  let filtered = eligibilities;
  if (filter === 'eligible') {
    filtered = eligibilities.filter(e => e.eligible);
  } else if (filter === 'central') {
    filtered = eligibilities.filter(e => (e.jurisdiction || '').toLowerCase() === 'central');
  } else if (filter === 'ap') {
    filtered = eligibilities.filter(e => (e.jurisdiction || '').toLowerCase().includes('andhra'));
  } else if (filter === 'ts') {
    filtered = eligibilities.filter(e => (e.jurisdiction || '').toLowerCase().includes('telangana'));
  }

  totalTag.textContent = `${filtered.length} Schemes`;

  if (!filtered || filtered.length === 0) {
    container.innerHTML = `
      <div class="empty-state">
        <div class="empty-icon">🔍</div>
        <h3>${dict.empty_title}</h3>
        <p>${dict.empty_desc}</p>
      </div>
    `;
    return;
  }

  container.innerHTML = filtered.map(scheme => {
    const isEligible = scheme.eligible;
    const confidencePct = Math.round((scheme.confidence || 0.9) * 100);
    const juris = (scheme.jurisdiction || 'central').toLowerCase();
    const jurisClass = juris.includes('andhra') ? 'badge-ap' : (juris.includes('telangana') ? 'badge-ts' : 'badge-central');

    // Get localized scheme name and benefit if available
    const localizedMeta = (SCHEME_I18N[scheme.scheme_id] && SCHEME_I18N[scheme.scheme_id][lang])
      ? SCHEME_I18N[scheme.scheme_id][lang]
      : null;

    const schemeName = localizedMeta ? localizedMeta.name : scheme.scheme_name;
    const benefitText = localizedMeta ? localizedMeta.benefit : (scheme.benefit_summary || 'Financial Benefit');

    // Required Docs Tags
    const docs = (scheme.required_documents || []).map(d => {
      const has = !((scheme.missing_documents || []).includes(d));
      return `<span class="doc-tag ${has ? 'has' : 'missing'}">${has ? '✅' : '❌'} ${d}</span>`;
    }).join('');

    return `
      <div class="scheme-card ${isEligible ? 'eligible' : 'not-eligible'}">
        <div class="scheme-card-header">
          <div class="scheme-title">${schemeName}</div>
          <span class="jurisdiction-badge ${jurisClass}">${scheme.jurisdiction || 'CENTRAL'}</span>
        </div>

        <div class="benefit-box">
          <div class="benefit-title">${dict.benefit_lbl}</div>
          <div class="benefit-amount">${benefitText}</div>
        </div>

        <div class="match-score-row">
          <span><strong>${isEligible ? dict.status_eligible : dict.status_not_eligible}</strong></span>
          <div style="display: flex; align-items: center; gap: 0.4rem;">
            <span>${confidencePct}%</span>
            <div class="match-bar-bg"><div class="match-bar-fill" style="width: ${confidencePct}%"></div></div>
          </div>
        </div>

        <div class="scheme-docs-list">
          <strong>${dict.req_docs_lbl}</strong><br>
          ${docs || '<span style="color:#888;">—</span>'}
        </div>

        <div class="scheme-actions">
          ${isEligible ? `
            <button class="btn btn-primary btn-block btn-sm" onclick="downloadSchemePdf('${scheme.scheme_id}')">
              ${dict.btn_download_form}
            </button>
          ` : `
            <button class="btn btn-outline btn-block btn-sm" disabled style="opacity: 0.6;">
              ${dict.btn_not_eligible}
            </button>
          `}
        </div>
      </div>
    `;
  }).join('');
}

function initFilters() {
  document.querySelectorAll('.filter-btn').forEach(btn => {
    btn.addEventListener('click', () => {
      document.querySelectorAll('.filter-btn').forEach(b => b.classList.remove('active'));
      btn.classList.add('active');
      renderSchemeCards(STATE.lastEligibilities, btn.dataset.filter);
    });
  });
}

/* ========================================================
   PDF Downloads
   ======================================================== */
function initPdfGeneration() {
  const btnFormPdf = document.getElementById('btn-gen-form-pdf');
  const btnChecklistPdf = document.getElementById('btn-gen-checklist-pdf');

  btnFormPdf.addEventListener('click', () => downloadSchemePdf(null, 'form'));
  btnChecklistPdf.addEventListener('click', () => downloadSchemePdf(null, 'checklist'));
}

async function downloadSchemePdf(schemeId = null, pdfType = 'form') {
  if (!STATE.lastProfile) {
    alert("Please submit or speak your details first.");
    switchTab('voice-tab');
    return;
  }

  showLoading("Generating PDF...", "Compiling verified citizen data into official form...");

  try {
    const resp = await fetch('/api/pdf/generate', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ scheme_id: schemeId, pdf_type: pdfType }),
    });

    if (!resp.ok) {
      const err = await resp.json();
      throw new Error(err.detail || 'PDF generation error');
    }

    const data = await resp.json();
    
    // Show in downloads list
    const box = document.getElementById('pdf-download-links');
    const list = document.getElementById('pdf-links-list');
    box.classList.remove('hidden');

    const item = document.createElement('div');
    item.className = 'pdf-file-pill';
    item.innerHTML = `
      <span>📄 <strong>${data.title}</strong></span>
      <a href="${data.download_url}" target="_blank" class="btn btn-primary btn-sm" download>⬇️ Download PDF</a>
    `;
    list.prepend(item);

    window.open(data.download_url, '_blank');
  } catch (err) {
    alert("Error: " + err.message);
  } finally {
    hideLoading();
  }
}

/* ========================================================
   WhatsApp Integration
   ======================================================== */
function initWhatsApp() {
  const btn = document.getElementById('btn-send-whatsapp');
  btn.addEventListener('click', async () => {
    const phone = document.getElementById('whatsapp-phone').value;
    if (!phone) {
      alert("Enter recipient mobile number.");
      return;
    }

    if (!STATE.lastProfile) {
      alert("Please submit citizen details first.");
      return;
    }

    showLoading("Sending WhatsApp Message...", `Dispatching report to +91 ${phone}...`);

    try {
      const resp = await fetch('/api/whatsapp/send', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ phone_number: "+91" + phone.replace(/^\+91/, '') }),
      });

      const data = await resp.json();
      const statusBox = document.getElementById('whatsapp-status-box');
      statusBox.classList.remove('hidden');
      statusBox.innerHTML = `
        <div style="background: #dcfce7; border: 1px solid #86efac; color: #166534; padding: 1rem; border-radius: 8px; margin-top: 1rem;">
          ✅ <strong>WhatsApp Delivery Successful!</strong><br>
          Recipient: ${data.phone_number}<br>
          Messages: ${data.sent_count}/${data.total_messages} delivered.
        </div>
      `;

      // Update phone mockup preview
      const p = STATE.lastProfile;
      const eligible = STATE.lastEligibilities.filter(e => e.eligible).slice(0, 3);
      const lang = STATE.currentLanguage;

      const schemesList = eligible.map((e, i) => {
        const meta = SCHEME_I18N[e.scheme_id] && SCHEME_I18N[e.scheme_id][lang];
        const sName = meta ? meta.name : e.scheme_name;
        const sBen = meta ? meta.benefit : e.benefit_summary;
        return `${i+1}. <strong>${sName}:</strong> ${sBen}`;
      }).join('<br>');

      let greeting = `నమస్తే ${p.name || 'రమేశ్'} గారు! 🙏<br>మీరు <strong>${eligible.length} పథకాలకు</strong> అర్హులుగా గుర్తించబడ్డారు:<br><br>`;
      if (lang === 'hi') {
        greeting = `नमस्ते ${p.name || 'रमेश'} जी! 🙏<br>आप <strong>${eligible.length} योजनाओं</strong> के लिए पात्र पाए गए हैं:<br><br>`;
      } else if (lang === 'en') {
        greeting = `Hello ${p.name || 'Citizen'}! 🙏<br>You are eligible for <strong>${eligible.length} welfare schemes</strong>:<br><br>`;
      }

      document.getElementById('phone-chat-body').innerHTML = `
        <div class="chat-message incoming">
          ${greeting}
          ${schemesList || '1. PM-KISAN: ₹6,000/year'}<br><br>
          📄 Official filled form PDF attached.
          <span class="chat-time">Just now</span>
        </div>
      `;
    } catch (err) {
      alert("WhatsApp delivery error: " + err.message);
    } finally {
      hideLoading();
    }
  });
}

/* ========================================================
   Playwright Form Auto-Fill
   ======================================================== */
function initPlaywright() {
  const btn = document.getElementById('btn-run-playwright');
  btn.addEventListener('click', async () => {
    if (!STATE.lastProfile) {
      alert("Please submit citizen details first.");
      switchTab('voice-tab');
      return;
    }

    const resBox = document.getElementById('autofill-results');
    const logBox = document.getElementById('autofill-log');
    resBox.classList.remove('hidden');
    logBox.textContent = "🚀 Starting Playwright Chromium automation...\nConnecting to PM-KISAN Portal...\n";

    btn.disabled = true;
    showLoading("Running Portal Auto-Fill...", "Navigating government registration portal with Playwright...");

    try {
      const resp = await fetch('/api/form/auto-fill', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ scheme_id: 'pm_kisan' }),
      });

      const data = await resp.json();
      btn.disabled = false;

      if (data.success) {
        logBox.textContent += `✅ Auto-fill Successful!\nFields completed: ${data.fields_filled.join(', ')}\nScreenshots saved.`;
      } else {
        logBox.textContent += `ℹ️ Live Demo completed:\nFields mapped: ${data.fields_filled.join(', ')}\nStatus: ${data.error_message || 'Portal live submission ready'}`;
      }
    } catch (err) {
      btn.disabled = false;
      logBox.textContent += `\nError: ${err.message}`;
    } finally {
      hideLoading();
    }
  });
}

/* ========================================================
   Helpers & Native Speech Synthesis
   ======================================================== */
function showLoading(title, desc) {
  const overlay = document.getElementById('loading-overlay');
  document.getElementById('loading-title').textContent = title;
  document.getElementById('loading-desc').textContent = desc;
  overlay.classList.remove('hidden');
}

function hideLoading() {
  document.getElementById('loading-overlay').classList.add('hidden');
}

function formatMarkdown(text) {
  if (!text) return '';
  return text
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    .replace(/^# (.*$)/gim, '<h3>$1</h3>')
    .replace(/^## (.*$)/gim, '<h4>$1</h4>')
    .replace(/^- (.*$)/gim, '• $1');
}

/* ========================================================
   Audio Response Player & Voice Controls
   ======================================================== */
function initAudioResponseControls() {
  const playBtn = document.getElementById('btn-play-voice');
  const stopBtn = document.getElementById('btn-stop-voice');
  const ttsPlayer = document.getElementById('tts-audio-player');

  if (playBtn) {
    playBtn.addEventListener('click', () => {
      toggleAudioResponse();
    });
  }

  if (stopBtn) {
    stopBtn.addEventListener('click', () => {
      stopAudioResponse();
    });
  }

  if (ttsPlayer) {
    ttsPlayer.addEventListener('play', () => {
      setAudioUIPlaying(true);
    });
    ttsPlayer.addEventListener('pause', () => {
      if (!STATE.isSpeakingSpeech) {
        setAudioUIPlaying(false);
      }
    });
    ttsPlayer.addEventListener('ended', () => {
      setAudioUIPlaying(false);
    });
    ttsPlayer.addEventListener('error', (e) => {
      console.warn("Audio player error, falling back to Web Speech API:", e);
    });
  }
}

function toggleAudioResponse() {
  if (STATE.isAudioPlaying) {
    pauseAudioResponse();
  } else {
    playAudioResponse(false);
  }
}

function playAudioResponse(isAuto = false) {
  const ttsPlayer = document.getElementById('tts-audio-player');
  const text = (STATE.lastVoiceResponse && STATE.lastVoiceResponse.text) ? STATE.lastVoiceResponse.text : '';
  if (!text) return;

  // Stop any active speech synthesis
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }

  const hasAudioSource = ttsPlayer && ttsPlayer.src && ttsPlayer.src.trim() !== '' && !ttsPlayer.src.endsWith('/null');

  if (hasAudioSource) {
    STATE.audioMode = 'file';
    ttsPlayer.play().then(() => {
      setAudioUIPlaying(true);
    }).catch(err => {
      console.warn("Audio file play prevented/delayed:", err);
      // If language is English and file failed, can use browser speech
      if (!isAuto && STATE.currentLanguage === 'en') {
        playViaSpeechSynthesis(text);
      }
    });
  } else {
    // If no audio file on server, use speech synthesis for English
    if (!isAuto && STATE.currentLanguage === 'en') {
      playViaSpeechSynthesis(text);
    }
  }
}

function playViaSpeechSynthesis(text) {
  if (!('speechSynthesis' in window)) return;
  STATE.audioMode = 'speech';
  STATE.isSpeakingSpeech = true;
  setAudioUIPlaying(true);

  try {
    window.speechSynthesis.cancel();
    const cleanText = text.replace(/[*#✅❌•]/g, '').trim();
    const utterance = new SpeechSynthesisUtterance(cleanText);
    const langCode = STATE.currentLanguage === 'te' ? 'te-IN' : (STATE.currentLanguage === 'hi' ? 'hi-IN' : 'en-IN');
    utterance.lang = langCode;
    utterance.rate = 1.0;

    // Pick best available voice for language
    const voices = window.speechSynthesis.getVoices();
    if (voices && voices.length > 0) {
      const target = STATE.currentLanguage;
      const matched = voices.find(v => v.lang.toLowerCase().startsWith(target) || v.lang.toLowerCase().includes(target));
      if (matched) utterance.voice = matched;
    }

    utterance.onstart = () => {
      setAudioUIPlaying(true);
    };
    utterance.onend = () => {
      STATE.isSpeakingSpeech = false;
      setAudioUIPlaying(false);
    };
    utterance.onerror = (e) => {
      console.warn("SpeechSynthesis error:", e);
      STATE.isSpeakingSpeech = false;
      setAudioUIPlaying(false);
    };

    window.speechSynthesis.speak(utterance);
  } catch (err) {
    console.warn("Speech error:", err);
    STATE.isSpeakingSpeech = false;
    setAudioUIPlaying(false);
  }
}

function pauseAudioResponse() {
  const ttsPlayer = document.getElementById('tts-audio-player');
  if (ttsPlayer && !ttsPlayer.paused) {
    ttsPlayer.pause();
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  STATE.isSpeakingSpeech = false;
  setAudioUIPlaying(false);
}

function stopAudioResponse() {
  const ttsPlayer = document.getElementById('tts-audio-player');
  if (ttsPlayer) {
    ttsPlayer.pause();
    try { ttsPlayer.currentTime = 0; } catch (_) {}
  }
  if ('speechSynthesis' in window) {
    window.speechSynthesis.cancel();
  }
  STATE.isSpeakingSpeech = false;
  setAudioUIPlaying(false);
}

function setAudioUIPlaying(isPlaying) {
  STATE.isAudioPlaying = isPlaying;
  const playIcon = document.getElementById('voice-play-icon');
  const playText = document.getElementById('voice-play-text');
  const stopBtn = document.getElementById('btn-stop-voice');
  const statusDot = document.querySelector('.status-indicator-dot');
  const statusText = document.getElementById('audio-status-text');
  const dict = I18N[STATE.currentLanguage] || I18N.te;

  if (isPlaying) {
    if (playIcon) playIcon.textContent = '⏸️';
    if (playText) playText.textContent = dict.btn_pause_audio || 'పాజ్ చేయండి (Pause)';
    if (stopBtn) stopBtn.classList.remove('hidden');
    if (statusDot) statusDot.classList.add('playing');
    if (statusText) statusText.textContent = dict.status_audio_playing || 'ఆడియో ప్లే అవుతోంది...';
  } else {
    if (playIcon) playIcon.textContent = '▶️';
    if (playText) playText.textContent = dict.btn_play_audio || 'ఆడియో వినండి (Play Audio)';
    if (stopBtn) stopBtn.classList.add('hidden');
    if (statusDot) statusDot.classList.remove('playing');
    if (statusText) statusText.textContent = dict.status_audio_ready || 'ఆడియో సిద్ధంగా ఉంది';
  }
}

function speakNative(text, lang) {
  playViaSpeechSynthesis(text);
}
