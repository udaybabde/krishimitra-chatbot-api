from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from google import genai
from typing import List, Optional
import os

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

crop_facts = {
    "rice": "Needs high nitrogen, pH 5.5-6.5, heavy rainfall (200mm+), grown in Kharif season. MSP for 2026-27: Rs 2,441 per quintal.",
    "maize": "Needs moderate nitrogen, pH 5.5-7.0, moderate rainfall, warm climate. MSP for 2026-27: Rs 2,410 per quintal.",
    "pigeonpeas": "Needs low nitrogen, pH 5.0-7.0, moderate rainfall, warm climate. MSP for 2026-27: Rs 8,450 per quintal.",
    "mungbean": "Needs low nitrogen, pH 6.2-7.2, moderate rainfall, warm season. MSP for 2026-27: Rs 8,780 per quintal.",
    "blackgram": "Needs low nitrogen, pH 6.0-7.5, moderate rainfall, warm climate. MSP for 2026-27: Rs 8,200 per quintal.",
    "cotton": "Needs high potassium, pH 6.0-8.0, warm climate, moderate rainfall. MSP for 2026-27: Rs 8,267/quintal (medium staple), Rs 8,667 (long staple).",
    "coconut": "Needs high potassium, pH 5.5-7.5, coastal humid climate, high rainfall. MSP (as Copra) for 2026-27: Rs 12,500 per quintal.",
    "soybean": "Needs moderate nitrogen, pH 6.0-7.5, moderate rainfall, warm climate. MSP for 2026-27: Rs 5,708 per quintal.",
    "chickpea": "Needs low nitrogen (fixes its own), pH 6.0-7.5, low rainfall, cool season crop. MSP for 2026-27: Rs 5,875 per quintal.",
    "lentil": "Needs low nitrogen, pH 6.0-7.5, low rainfall, cool season crop. MSP for 2026-27: Rs 7,000 per quintal.",
    "jute": "Needs high nitrogen, pH 6.0-7.5, high humidity, heavy rainfall. MSP for 2026-27: Rs 5,925 per quintal.",
    "kidneybeans": "Needs moderate nitrogen, pH 5.5-6.5, moderate rainfall, cool climate.",
    "mothbeans": "Needs low water, pH 6.0-7.5, drought-tolerant, grown in dry regions.",
    "pomegranate": "Needs low water once established, pH 5.5-7.5, dry to semi-arid climate.",
    "banana": "Needs high potassium, pH 5.5-7.0, high rainfall, warm humid climate.",
    "mango": "Needs moderate nutrients, pH 5.5-7.5, distinct dry and wet seasons.",
    "grapes": "Needs moderate potassium, pH 6.0-7.0, low humidity, warm dry climate.",
    "watermelon": "Needs high potassium, pH 6.0-6.8, warm climate, moderate water.",
    "muskmelon": "Needs moderate nitrogen, pH 6.0-6.8, warm dry climate.",
    "apple": "Needs moderate nutrients, pH 5.5-6.5, cold climate, chilling hours required.",
    "orange": "Needs moderate nitrogen, pH 5.5-7.5, subtropical climate, moderate rainfall.",
    "papaya": "Needs high nitrogen, pH 6.0-6.5, warm climate, well-drained soil.",
    "coffee": "Needs moderate nitrogen, pH 6.0-6.5, shaded, cool humid climate.",
}

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
    crop_input = data.crop_name.lower().strip()

    # Agar crop_name khaali hai, to question ke text mein se khud dhoondo
    if not crop_input:
        question_lower = data.question.lower()
        for crop in crop_facts.keys():
            if crop in question_lower:
                crop_input = crop
                break

    fact = crop_facts.get(crop_input)

    # purani conversation ko text mein convert karo
    history_text = ""
    for msg in data.history[-5:]:
        history_text += f"Farmer asked: {msg.question}\nYou answered: {msg.answer}\n\n"

    if fact:
        base_instruction = f"Use this verified fact as your main source: {fact}"
    else:
        base_instruction = (
            "Answer using your own general agricultural knowledge. "
            "Start your reply with the symbol \u2139\ufe0f (info symbol) followed by a space, "
            "then go straight into the answer. Do not write any sentence about data sources."
        )

    prompt = f"""You are a helpful farming assistant for Indian farmers.
{base_instruction}

Previous conversation (for context):
{history_text if history_text else "No previous conversation."}

New question: {data.question}

Answer in simple, easy words (avoid technical jargon). Keep it short.
Reply in the same language the farmer used (Hindi/Hinglish/English).
Use the previous conversation to understand follow-up questions if relevant."""

        import time
    last_error = None
    for attempt in range(3):
        try:
            response = client.models.generate_content(
                model="gemini-3.6-flash",
                contents=prompt
            )
            return {"answer": response.text}
        except Exception as e:
            last_error = str(e)
            print(f"Attempt {attempt+1} failed: {last_error}")
            time.sleep(3)

    return {"answer": "The AI service is currently busy. Please try again in a moment.", "debug_error": last_error}
