import os
import re
import time
from typing import List, Optional

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from google import genai
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.8-flash"

# ---------------------------------------------------------------
# Crop knowledge base (single source of truth)
# nutrient / rainfall / climate / msp can be None if data is not available
# ---------------------------------------------------------------
CROPS = {
    "rice": {"nutrient": "High nitrogen", "ph": "5.5-6.5", "rainfall": "Heavy rainfall (200mm+)", "climate": "Grown in Kharif season", "msp": "Rs 2,441 per quintal"},
    "maize": {"nutrient": "Moderate nitrogen", "ph": "5.5-7.0", "rainfall": "Moderate rainfall", "climate": "Warm climate", "msp": "Rs 2,410 per quintal"},
    "pigeonpeas": {"nutrient": "Low nitrogen", "ph": "5.0-7.0", "rainfall": "Moderate rainfall", "climate": "Warm climate", "msp": "Rs 8,450 per quintal"},
    "mungbean": {"nutrient": "Low nitrogen", "ph": "6.2-7.2", "rainfall": "Moderate rainfall", "climate": "Warm season", "msp": "Rs 8,780 per quintal"},
    "blackgram": {"nutrient": "Low nitrogen", "ph": "6.0-7.5", "rainfall": "Moderate rainfall", "climate": "Warm climate", "msp": "Rs 8,200 per quintal"},
    "cotton": {"nutrient": "High potassium", "ph": "6.0-8.0", "rainfall": "Moderate rainfall", "climate": "Warm climate", "msp": "Rs 8,267 per quintal (medium staple), Rs 8,667 per quintal (long staple)"},
    "coconut": {"nutrient": "High potassium", "ph": "5.5-7.5", "rainfall": "High rainfall", "climate": "Coastal humid climate", "msp": "Rs 12,500 per quintal (as copra)"},
    "soybean": {"nutrient": "Moderate nitrogen", "ph": "6.0-7.5", "rainfall": "Moderate rainfall", "climate": "Warm climate", "msp": "Rs 5,708 per quintal"},
    "chickpea": {"nutrient": "Low nitrogen (fixes its own)", "ph": "6.0-7.5", "rainfall": "Low rainfall", "climate": "Cool season crop", "msp": "Rs 5,875 per quintal"},
    "lentil": {"nutrient": "Low nitrogen", "ph": "6.0-7.5", "rainfall": "Low rainfall", "climate": "Cool season crop", "msp": "Rs 7,000 per quintal"},
    "jute": {"nutrient": "High nitrogen", "ph": "6.0-7.5", "rainfall": "Heavy rainfall and high humidity", "climate": "Humid climate", "msp": "Rs 5,925 per quintal"},
    "kidneybeans": {"nutrient": "Moderate nitrogen", "ph": "5.5-6.5", "rainfall": "Moderate rainfall", "climate": "Cool climate", "msp": None},
    "mothbeans": {"nutrient": None, "ph": "6.0-7.5", "rainfall": "Low water need, drought-tolerant", "climate": "Grown in dry regions", "msp": None},
    "pomegranate": {"nutrient": None, "ph": "5.5-7.5", "rainfall": "Low water need once established", "climate": "Dry to semi-arid climate", "msp": None},
    "banana": {"nutrient": "High potassium", "ph": "5.5-7.0", "rainfall": "High rainfall", "climate": "Warm humid climate", "msp": None},
    "mango": {"nutrient": "Moderate nutrients", "ph": "5.5-7.5", "rainfall": None, "climate": "Distinct dry and wet seasons", "msp": None},
    "grapes": {"nutrient": "Moderate potassium", "ph": "6.0-7.0", "rainfall": None, "climate": "Low humidity, warm dry climate", "msp": None},
    "watermelon": {"nutrient": "High potassium", "ph": "6.0-6.8", "rainfall": "Moderate water", "climate": "Warm climate", "msp": None},
    "muskmelon": {"nutrient": "Moderate nitrogen", "ph": "6.0-6.8", "rainfall": None, "climate": "Warm dry climate", "msp": None},
    "apple": {"nutrient": "Moderate nutrients", "ph": "5.5-6.5", "rainfall": None, "climate": "Cold climate, chilling hours required", "msp": None},
    "orange": {"nutrient": "Moderate nitrogen", "ph": "5.5-7.5", "rainfall": "Moderate rainfall", "climate": "Subtropical climate", "msp": None},
    "papaya": {"nutrient": "High nitrogen", "ph": "6.0-6.5", "rainfall": None, "climate": "Warm climate, well-drained soil", "msp": None},
    "coffee": {"nutrient": "Moderate nitrogen", "ph": "6.0-6.5", "rainfall": None, "climate": "Shaded, cool humid climate", "msp": None},
}

# Different names (English / Hinglish / Hindi) farmers may use for each crop
ALIASES = {
    "rice": ["rice", "paddy", "chawal", "dhan", "चावल", "धान"],
    "maize": ["maize", "corn", "makka", "makkai", "मक्का", "मक्की"],
    "pigeonpeas": ["pigeonpea", "pigeon pea", "tur", "toor", "arhar", "तुर", "तूर", "अरहर"],
    "mungbean": ["mungbean", "mung bean", "moong", "green gram", "मूंग", "मूँग"],
    "blackgram": ["blackgram", "black gram", "urad", "उड़द"],
    "cotton": ["cotton", "kapas", "कपास"],
    "coconut": ["coconut", "nariyal", "नारियल"],
    "soybean": ["soybean", "soyabean", "soya", "सोयाबीन"],
    "chickpea": ["chickpea", "chana", "चना"],
    "lentil": ["lentil", "masoor", "masur", "मसूर"],
    "jute": ["jute", "जूट", "पटसन"],
    "kidneybeans": ["kidneybean", "kidney bean", "rajma", "राजमा"],
    "mothbeans": ["mothbean", "moth bean", "matki", "मटकी"],
    "pomegranate": ["pomegranate", "anar", "अनार"],
    "banana": ["banana", "kela", "केला"],
    "mango": ["mango"],
    "grapes": ["grape", "angur", "अंगूर"],
    "watermelon": ["watermelon", "tarbooz", "तरबूज"],
    "muskmelon": ["muskmelon", "kharbuja", "खरबूजा"],
    "apple": ["apple", "seb", "सेब"],
    "orange": ["orange", "santra", "संतरा"],
    "papaya": ["papaya", "papita", "पपीता"],
    "coffee": ["coffee", "कॉफी"],
}


def _build_matchers():
    matchers = []
    for crop, words in ALIASES.items():
        ascii_words = [w for w in words if w.isascii()]
        other_words = [w for w in words if not w.isascii()]
        pattern = None
        if ascii_words:
            alt = "|".join(re.escape(w) for w in ascii_words)
            pattern = re.compile(rf"\b(?:{alt})(?:s|es)?\b", re.I)
        matchers.append((crop, pattern, other_words))
    return matchers


MATCHERS = _build_matchers()


def crops_in_text(text):
    text = text or ""
    low = text.lower()
    found = []
    for crop, pattern, other_words in MATCHERS:
        if (pattern and pattern.search(low)) or any(w in text for w in other_words):
            found.append(crop)
    return found


# What is the farmer asking about?
INTENTS = {
    "ph": re.compile(r"\bph\b|पीएच", re.I),
    "rainfall": re.compile(r"rainfall|\brain\b|\bbaarish\b|\bbarish\b|\bpaani\b|\bpani\b|\bwater\b|बारिश|पानी|वर्षा", re.I),
    "msp": re.compile(r"\bmsp\b|minimum support|support price|एमएसपी", re.I),
    "nutrient": re.compile(r"nitrogen|potassium|nutrient|\bnpk\b|नाइट्रोजन|पोटैशियम|पोषक", re.I),
    "climate": re.compile(r"season|climate|mausam|temperature|\bkab\b|\bwhen\b|मौसम|जलवायु|तापमान|कब", re.I),
}

# Questions with these words need real reasoning -> send to Gemini
COMPLEX = re.compile(
    r"\bhow\b|\bwhy\b|\bwhat to do\b|\bsolution\b|\bproblem\b|\btips?\b|\bexplain\b|\bbest\b|\bwhich\b|\bcompare\b"
    r"|\bdisease\b|\bpest\b|fertili[sz]er|kaise|kyun|\bkyu\b|upay|samjha|\bkhad\b|bimari|\bkeet\b|konsa|kaunsa|\bkya kar"
    r"|कैसे|क्यों|उपाय|खाद|बीमारी|कीट|रोग|सबसे|कौन|समझा",
    re.I,
)


def is_simple(question):
    q = re.sub(r"how (?:much|many|high|low)", "", question.lower())
    return len(q.split()) <= 14 and not COMPLEX.search(q)


def detect_language(question):
    if re.search(r"[\u0900-\u097F]", question):
        return "hi"
    if re.search(r"\b(?:ke liye|kitna|kitni|kya|hai|chahiye|mein|kab|batao|ka|ki|ke)\b", question.lower()):
        return "hinglish"
    return "en"


LABELS = {
    "en": {
        "ph": "Soil pH for {c}: {v}",
        "rainfall": "Rainfall/water for {c}: {v}",
        "nutrient": "Nutrient need for {c}: {v}",
        "climate": "Climate/season for {c}: {v}",
        "msp": "MSP of {c} (2026-27): {v}",
        "nomsp": "No MSP is declared for {c}.",
    },
    "hinglish": {
        "ph": "{c} ke liye mitti ka pH: {v}",
        "rainfall": "{c} ke liye barish/paani: {v}",
        "nutrient": "{c} ke liye poshak tatva: {v}",
        "climate": "{c} ke liye mausam/season: {v}",
        "msp": "{c} ka MSP (2026-27): {v}",
        "nomsp": "{c} ke liye MSP declare nahi hai.",
    },
    "hi": {
        "ph": "{c} के लिए मिट्टी का pH: {v}",
        "rainfall": "{c} के लिए बारिश/पानी: {v}",
        "nutrient": "{c} के लिए पोषक तत्व: {v}",
        "climate": "{c} के लिए मौसम/जलवायु: {v}",
        "msp": "{c} का MSP (2026-27): {v}",
        "nomsp": "{c} के लिए MSP घोषित नहीं है।",
    },
}


def fact_text(crop):
    d = CROPS[crop]
    parts = []
    if d.get("nutrient"):
        parts.append(d["nutrient"])
    parts.append(f"soil pH {d['ph']}")
    if d.get("rainfall"):
        parts.append(d["rainfall"])
    if d.get("climate"):
        parts.append(d["climate"])
    text = f"{crop.capitalize()}: " + ", ".join(parts) + "."
    if d.get("msp"):
        text += f" MSP for 2026-27: {d['msp']}."
    return text


def direct_answer(crop, intents, lang):
    """Answer straight from our own data. Returns None if data is missing."""
    d = CROPS[crop]
    name = crop.capitalize()
    lines = []
    for intent in intents:
        if intent == "msp":
            key = "msp" if d.get("msp") else "nomsp"
            lines.append(LABELS[lang][key].format(c=name, v=d.get("msp")))
        else:
            value = d.get(intent)
            if not value:
                return None
            lines.append(LABELS[lang][intent].format(c=name, v=value))
    return "\n".join(lines)


def crops_from_history(history):
    """For follow-up questions like 'uske liye rainfall kitni chahiye?'"""
    for msg in reversed(history[-5:]):
        for text in (msg.question, msg.answer):
            found = crops_in_text(text)
            if len(found) == 1:
                return found
    return []


ANSWER_CACHE = {}
MAX_CACHE = 300


def ask_gemini(prompt):
    """Returns (text, error_type). error_type is None on success."""
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model=MODEL_NAME, contents=prompt
            )
            text = (response.text or "").strip()
            if text:
                return text, None
            print(f"Attempt {attempt + 1}: empty response")
        except Exception as e:
            err = str(e)
            print(f"Attempt {attempt + 1} failed: {err}")
            if "429" in err or "RESOURCE_EXHAUSTED" in err:
                return None, "quota"  # no point retrying a daily limit
        time.sleep(3)
    return None, "busy"


class Message(BaseModel):
    question: str
    answer: str


class ChatInput(BaseModel):
    question: str
    crop_name: str = ""
    history: Optional[List[Message]] = []


@app.get("/")
def home():
    return {"message": "KrishiMitra Chatbot API is running"}


@app.post("/chatbot-query")
def chatbot_query(data: ChatInput):
    question = data.question.strip()
    history = data.history or []

    crops = crops_in_text(data.crop_name) or crops_in_text(question)
    intents = [name for name, rx in INTENTS.items() if rx.search(question)]

    # 1) Simple factual question -> answer from our own data, NO Gemini call
    if intents and is_simple(question):
        target = crops if crops else crops_from_history(history)
        if len(target) == 1:
            reply = direct_answer(target[0], intents, detect_language(question))
            if reply:
                return {"answer": reply}

    # 2) Same question asked before -> reuse the saved answer, NO Gemini call
    cache_key = None
    if not history:
        cache_key = (" ".join(question.lower().split()), tuple(crops))
        if cache_key in ANSWER_CACHE:
            return {"answer": ANSWER_CACHE[cache_key]}

    # 3) Everything else -> Gemini (with our verified facts as context if available)
    history_text = ""
    for msg in history[-5:]:
        history_text += f"Farmer asked: {msg.question}\nYou answered: {msg.answer}\n\n"

    if crops:
        facts = " ".join(fact_text(c) for c in crops)
        base_instruction = f"Use these verified facts as your main source: {facts}"
    else:
        base_instruction = (
            "Answer using your own general agricultural knowledge. "
            "Start your reply with the symbol \u2139\ufe0f followed by a space, "
            "then go straight into the answer. Do not write any sentence about data sources."
        )

    prompt = f"""You are a helpful farming assistant for Indian farmers.
{base_instruction}

Previous conversation (for context):
{history_text if history_text else "No previous conversation."}

New question: {question}

Answer in simple, easy words (avoid technical jargon). Keep it short.
Reply in the same language the farmer used (Hindi/Hinglish/English).
Use the previous conversation to understand follow-up questions if relevant."""

    text, error_type = ask_gemini(prompt)

    if text:
        if cache_key is not None:
            if len(ANSWER_CACHE) >= MAX_CACHE:
                ANSWER_CACHE.clear()
            ANSWER_CACHE[cache_key] = text
        return {"answer": text}

    # 4) Gemini failed -> still give something useful
    if crops:
        return {"answer": "\n".join(fact_text(c) for c in crops)}
    if error_type == "quota":
        return {
            "answer": (
                "The AI assistant has reached its daily limit. Questions about crop pH, "
                "rainfall, season, nutrients or MSP still work - please try those, or ask again later."
            )
        }
    return {"answer": "The AI service is currently busy. Please try again in a moment."}
