"""
SWARIVA AI — Intent Classification Module

Provides robust, multi-lingual intent recognition across English, Telugu, and Hindi.
Disentangles pleasantries/greetings from substantive queries and accurately classifies:
- Greeting
- General knowledge
- Educational questions
- Explanations
- How-to instructions
- Technology and programming
- Festival and cultural information
- Daily assistance
- Reminders
- Accessibility assistance
- Emotional companionship
- Emergency-related requests
- Follow-up questions
- General conversation
"""
import re
from enum import Enum
from typing import Dict, Any, Tuple, Optional, List


class IntentType(str, Enum):
    GREETING = "greeting"
    ASSISTANCE_REQUEST = "assistance_request"
    GENERAL_KNOWLEDGE = "general_knowledge"
    EDUCATIONAL = "educational"
    EXPLANATION = "explanation"
    HOW_TO = "how_to"
    TECHNOLOGY = "technology"
    FESTIVAL_CULTURE = "festival_culture"
    DAILY_ASSISTANCE = "daily_assistance"
    REMINDERS = "reminders"
    ACCESSIBILITY = "accessibility"
    EMOTIONAL_COMPANION = "emotional_companion"
    EMERGENCY_HEALTH = "emergency_health"
    FOLLOW_UP = "follow_up"
    GENERAL_CONVERSATION = "general_conversation"


# Common greeting patterns across languages to strip when identifying embedded queries
GREETING_PREFIX_PATTERNS = [
    r"^(?:hello|hi|hey|good\s+morning|good\s+afternoon|good\s+evening|namaste|hey\s+there)\b[\s,!-]*",
    r"^(?:హలో|నమస్కారం|నమస్తే|హాయ్)\b[\s,!-]*",
    r"^(?:नमस्ते|हैलो|हेलो|हाय|प्रणाम|सुप्रभात)\b[\s,!-]*",
]

# Code-mixed and language markers
TELUGU_WORDS = {
    "గురించి", "చెప్పండి", "వివరించండి", "ఎలా", "ఎప్పుడు", "ఎందుకు", "పండుగ", "మందులు",
    "సహాయం", "బాగున్నారా", "నమస్కారం", "తెలుపండి", "ఏమిటి", "స్వరివ",
    # Transliterated / code-mixed Tenglish markers
    "gurinchi", "cheppandi", "cheppu", "vivarinchandi", "panduga", "pandaga",
    "eppudu", "enduku", "ela", "mandulu", "sahayam", "bagunnara", "telusuko",
    "ante", "enti", "emiti", "cheyandi", "chesuko"
}

HINDI_WORDS = {
    "बारे", "में", "बताओ", "समझाओ", "क्या", "कब", "क्यों", "त्योहार", "दवा",
    "मदद", "नमस्ते", "कैसा", "स्वरिवा",
    # Transliterated / code-mixed Hinglish markers
    "baare", "mein", "batao", "samjhao", "kya", "kab", "kyun", "tyohar", "dawa",
    "madad", "kaisa", "karo", "chahiye", "hota", "hai", "kise"
}


def detect_language_script(text: str) -> str:
    """
    Detects whether text is predominantly Telugu, Hindi, or English,
    with awareness of transliterated code-mixing.
    """
    if not text:
        return "english"

    # Telugu Unicode range: 0x0C00 - 0x0C7F
    telugu_chars = sum(1 for c in text if '\u0C00' <= c <= '\u0C7F')
    # Devanagari Unicode range: 0x0900 - 0x097F
    devanagari_chars = sum(1 for c in text if '\u0900' <= c <= '\u097F')

    total_alpha = sum(1 for c in text if c.isalpha())
    if total_alpha > 0:
        if telugu_chars / total_alpha > 0.2:
            return "telugu"
        if devanagari_chars / total_alpha > 0.2:
            return "hindi"

    # Check for code-mixed transliteration tokens
    tokens = set(re.findall(r"\b[a-zA-Z]+\b", text.lower()))
    if tokens & TELUGU_WORDS:
        return "telugu"
    if tokens & HINDI_WORDS:
        return "hindi"

    return "english"


def strip_greeting_prefix(text: str) -> str:
    """
    Removes introductory greetings like 'Hi', 'Hello Swariva', 'నమస్కారం'
    to inspect the substantive core request.
    """
    cleaned = text.strip()
    changed = True
    while changed:
        prev = cleaned
        for pattern in GREETING_PREFIX_PATTERNS:
            cleaned = re.sub(pattern, "", cleaned, flags=re.IGNORECASE).strip()
        cleaned = re.sub(r"^(?:swariva|स्वरिवा|స్వరివ)[\s,!-]*", "", cleaned, flags=re.IGNORECASE).strip()
        changed = (cleaned != prev)
    return cleaned


class IntentClassifier:
    """Classifies user queries into semantic intents and extracts key context entities."""

    @staticmethod
    def classify(
        query: str,
        history: Optional[List[Dict[str, str]]] = None,
        active_subject: Optional[str] = None,
    ) -> Tuple[IntentType, Dict[str, Any]]:
        raw_query = query.strip()
        lower_query = raw_query.lower()
        stripped_query = strip_greeting_prefix(raw_query)
        lower_stripped = stripped_query.lower()

        entities: Dict[str, Any] = {
            "raw_query": raw_query,
            "stripped_query": stripped_query,
            "detected_language": detect_language_script(raw_query),
            "subject": None,
        }

        # 1. EMERGENCY / HEALTH DIRECTIVES
        # Must be caught first for user safety
        health_emergency_terms = [
            "chest pain", "heart attack", "can't breathe", "difficulty breathing", "emergency",
            "severe bleeding", "unconscious", "ambulance", "poison", "suicide", "overdose",
            "గుండె నొప్పి", "శ్వాస ఆడటం లేదు", "అత్యవసర", "రక్తం కారుతోంది", "అంబులెన్స్",
            "सीने में दर्द", "सांस नहीं आ रही", "आपातकालीन", "खून बह रहा है", "एम्बुलेंस"
        ]
        if any(term in lower_query for term in health_emergency_terms):
            return IntentType.EMERGENCY_HEALTH, entities

        # Medical inquiries (non-emergency)
        medical_terms = [
            "doctor", "medicine dose", "pain in leg", "fever", "headache", "cough", "vomiting",
            "డాక్టర్", "జ్వరం", "నొప్పి", "తలనొప్పి", "దగ్గు", "వాంతులు",
            "डॉक्टर", "बुखार", "दर्द", "सिरदर्द", "खांसी"
        ]
        # Only classify as medical if not asking for a reminder to take medicine
        if any(term in lower_query for term in medical_terms) and not any(w in lower_query for w in ["remind", "reminder", "గుర్తు", "याद"]):
            entities["subject"] = "health_consultation"
            return IntentType.EMERGENCY_HEALTH, entities

        # 2. REMINDERS & ALARMS
        reminder_terms = [
            "remind", "reminder", "alarm", "schedule", "don't let me forget",
            "గుర్తు చేయి", "రిమైండర్", "గుర్తుచేయి", "గుర్తుచేయండి", "గుర్తుంచుకో",
            "याद दिलाओ", "रिमाइंडर", "याद रखना", "अलार्म"
        ]
        if any(term in lower_query for term in reminder_terms):
            entities["subject"] = "reminder"
            return IntentType.REMINDERS, entities

        # 3. ACCESSIBILITY ASSISTANCE
        accessibility_terms = [
            "blind", "visually impaired", "can't see", "low vision", "screen reader",
            "high contrast", "voice navigation", "font size", "accessibility",
            "దృష్టి లోపం", "కళ్ళు కనపడటం లేదు", "అంధులు", "వాయిస్ నావిగేషన్",
            "दृष्टिबाधित", "अंधे", "दिखाई नहीं देता", "आवाज नेविगेशन", "सुगमता"
        ]
        if any(term in lower_query for term in accessibility_terms):
            entities["subject"] = "accessibility"
            return IntentType.ACCESSIBILITY, entities

        # 4. EMOTIONAL COMPANIONSHIP
        emotional_terms = [
            "lonely", "alone", "sad", "depressed", "unhappy", "nobody to talk to", "feeling low",
            "bored", "crying", "heartbroken",
            "ఒంటరిగా", "బాధగా", "బోర్", "ఎవరూ లేరు", "దిగులుగా",
            "अकेला", "उदास", "मन नहीं लग रहा", "कोई बात करने वाला नहीं", "दुखी"
        ]
        if any(term in lower_query for term in emotional_terms):
            entities["subject"] = "emotional_support"
            return IntentType.EMOTIONAL_COMPANION, entities

        # 5. FOLLOW-UP QUESTIONS (Context Dependent)
        # Pronoun reference or continuation questions: "when is it celebrated?", "why do people celebrate it?", "tell me more"
        follow_up_patterns = [
            r"\b(?:when\s+is\s+it|why\s+do\s+people|why\s+is\s+it|how\s+does\s+it|tell\s+me\s+more|what\s+else|explain\s+further|continue)\b",
            r"(?:ఇది\s+ఎప్పుడు|ఎందుకు\s+జరుపుకుంటారు|ఎందుకు\s+చేస్తారు|మరింత\s+చెప్పండి|ఇంకా\s+చెప్పండి|తరువాత)",
            r"(?:यह\s+कब\s+मनाया|लोग\s+इसे\s+क्यों|इसके\s+बारे\s+में\s+और|और\s+बताओ|आगे\s+बताओ)"
        ]
        is_follow_up = any(re.search(pat, lower_query, re.IGNORECASE) for pat in follow_up_patterns)
        if is_follow_up and (active_subject or (history and len(history) > 0)):
            entities["subject"] = active_subject or "previous_topic"
            return IntentType.FOLLOW_UP, entities

        # 6. FESTIVALS & CULTURAL KNOWLEDGE
        festival_terms = {
            "diwali": ["diwali", "deepavali", "deepawali", "దీపావళి", "దివాళీ", "దివాళి", "दीपावली", "दिवाली"],
            "sankranti": ["sankranti", "makar sankranti", "pongal", "సంక్రాంతి", "మకర సంక్రాంతి", "పొంగల్", "संक्रांति", "पोंगल"],
            "ugadi": ["ugadi", "yugadi", "ఉగాది", "యుగాది", "गुड़ी पड़वा", "उगादि"],
            "holi": ["holi", "హోలీ", "होली"],
            "eid": ["eid", "ramadan", "ramzan", "రంజాన్", "ఈద్", "ईद", "रमजान"],
            "christmas": ["christmas", "క్రిస్మస్", "क्रिसमस"],
            "dasara": ["dasara", "dussehra", "navratri", "దసరా", "నవరాత్రి", "दशहरा", "नवरात्रि"]
        }
        for fest, aliases in festival_terms.items():
            if any(alias in lower_query for alias in aliases):
                entities["subject"] = fest
                return IntentType.FESTIVAL_CULTURE, entities

        # 7. IDENTITY QUESTIONS & SELF INTRODUCTION
        identity_terms = [
            "who are you", "your name", "what are you", "what can you do", "introduce yourself", "tell me about yourself",
            "మీరు ఎవరు", "ఎవరు మీరు", "ఎవరు నువ్వు", "నీ పేరు", "మీ పేరు", "ఏమి చేయగలవు", "పరిచయం",
            "आप कौन हैं", "कौन हैं आप", "तुम कौन हो", "कौन हो तुम", "आपका नाम", "तुम्हारा नाम", "क्या कर सकती हो", "परिचय"
        ]
        if any(term in lower_query for term in identity_terms):
            entities["subject"] = "identity"
            return IntentType.GENERAL_CONVERSATION, entities

        # 8. TECHNOLOGY & PROGRAMMING
        tech_terms = {
            "artificial_intelligence": [
                "artificial intelligence", "ai", "కృత్రిమ మేధస్సు", "ఆర్టిఫిషియల్ ఇంటెలిజెన్స్",
                "कृत्रिम बुद्धिमत्ता", "आर्टिफिशियल इंटेलिजेंस"
            ],
            "machine_learning": [
                "machine learning", "ml", "మెషిన్ లెర్నింగ్", "मशीन लर्निंग"
            ],
            "cyclone_causes": [
                "what causes cyclone", "causes of cyclone", "how cyclones form", "cause of cyclone", "causes cyclones",
                "తుఫానులు ఎందుకు వస్తాయి", "తుఫాను ఎలా ఏర్పడుతుంది", "చక్రవాతం ఎందుకు",
                "चक्रवात क्यों आते हैं", "चक्रवात कैसे बनता है", "चक्रवात का कारण"
            ],
            "cyclone": [
                "cyclone", "tropical storm", "hurricane", "typhoon",
                "తుఫాను", "వాయుగుండం", "చక్రవాతం",
                "चक्रवात", "तूफान"
            ],
            "blockchain": [
                "blockchain", "block chain", "distributed ledger",
                "బ్లాక్‌చెయిన్", "బ్లాక్ చెయిన్",
                "ब्लॉकचेन", "ब्लॉक चेन"
            ],
            "photosynthesis": [
                "photosynthesis", "photo synthesis",
                "కిరణజన్య సంయోగక్రియ", "కిరణజన్య సంయోగ క్రియ",
                "प्रकाश संश्लेषण"
            ],
            "cloud_computing": [
                "cloud computing", "cloud storage", "క్లౌడ్ కంప్యూటింగ్", "क्लाउड कंप्यूटिंग"
            ],
            "programming_python": [
                "python", "coding", "programming", "software", "పైథాన్", "కోడింగ్", "पायथन", "प्रोग्रामिंग"
            ],
            "internet_computers": [
                "internet", "computer", "world wide web", "ఇంటర్నెట్", "కంప్యూటర్", "इंटरनेट", "कंप्यूटर"
            ]
        }
        for tech, aliases in tech_terms.items():
            for alias in aliases:
                # Word boundary check for short terms like 'ai' or 'ml'
                if len(alias) <= 3:
                    if re.search(rf"\b{re.escape(alias)}\b", lower_query):
                        entities["subject"] = tech
                        return IntentType.TECHNOLOGY, entities
                else:
                    if alias in lower_query:
                        entities["subject"] = tech
                        return IntentType.TECHNOLOGY, entities

        # 8. EDUCATIONAL & EXPLANATORY QUESTIONS
        edu_patterns = [
            r"\b(?:what\s+is|explain|how\s+to|why\s+is|define|difference\s+between)\b",
            r"(?:అంటే\s+ఏమిటి|వివరించండి|తెలుపండి|ఎలా\s+పనిచేస్తుంది)",
            r"(?:क्या\s+होता\s+है|समझाओ|परिभाषा|कैसे\s+काम\s+करता\s+है)"
        ]
        if any(re.search(pat, lower_stripped, re.IGNORECASE) for pat in edu_patterns):
            # Extract possible educational subject
            entities["subject"] = stripped_query
            if "how" in lower_stripped or "ఎలా" in lower_stripped or "कैसे" in lower_stripped:
                return IntentType.HOW_TO, entities
            return IntentType.EDUCATIONAL, entities

        # 9. GENERAL ASSISTANCE REQUEST ("I need help", "Can you help me?")
        assist_terms = [
            "need your help", "help me", "can you help", "support me", "assist me",
            "సహాయం కావాలి", "సహాయం చేయగలరా", "మద్దతు",
            "मदद चाहिए", "सहायता करो", "मेरी मदद करो"
        ]
        if any(term in lower_query for term in assist_terms) and len(stripped_query.split()) <= 6:
            return IntentType.ASSISTANCE_REQUEST, entities

        # 10. GREETINGS (Only if no substantive query remains after stripping greeting prefix)
        greeting_words = [
            "hello", "hi", "hey", "good morning", "good evening", "good afternoon",
            "namaste", "hey there", "how are you", "what's up",
            "నమస్కారం", "హలో", "హాయ్", "బాగున్నారా", "నమస్తే", "ఎలా ఉన్నారు",
            "नमस्ते", "हेलो", "हाय", "प्रणाम", "सुप्रभात", "हैलो", "कैसी हो", "कैसा है"
        ]
        cleaned_no_punct = re.sub(r"[^\w\s]", "", lower_stripped).strip()
        if any(gw in lower_query for gw in greeting_words):
            # If after stripping greetings and name, nothing or only greeting words remain, it's a pure greeting
            if (
                len(cleaned_no_punct) == 0
                or cleaned_no_punct in greeting_words
                or cleaned_no_punct in ["swariva", "स्वरिवा", "స్వరివ"]
                or all(w in greeting_words or w in ["swariva", "there", "to", "you", "swarivaa"] for w in cleaned_no_punct.split())
            ):
                return IntentType.GREETING, entities

        # 11. GENERAL GRATITUDE & FAREWELL
        farewell_terms = [
            "thank you", "thanks", "bye", "goodbye", "good night", "see you",
            "ధన్యవాదాలు", "థాంక్స్", "బై", "వెళ్ళొస్తా", "శుభరాత్రి",
            "धन्यवाद", "शुक्रिया", "अलविदा", "बाय", "शुभ रात्रि"
        ]
        if any(term in lower_query for term in farewell_terms):
            return IntentType.GENERAL_CONVERSATION, entities

        # Default fallback: General Knowledge or Explanation
        if any(mark in lower_query for mark in ["?", "tell", "explain", "చెప్పు", "बताओ"]):
            return IntentType.GENERAL_KNOWLEDGE, entities

        return IntentType.GENERAL_CONVERSATION, entities
