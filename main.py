from fastapi import FastAPI
from pydantic import BaseModel
from google import genai
from typing import List, Optional

app = FastAPI()

from fastapi.middleware.cors import CORSMiddleware

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

client = genai.Client(api_key="AQ.Ab8RN6IDMZa-Yswenrcgtz2gCsHPRZoQbxGqqsrlbA2-aYcIsg")

crop_facts = {
    "rice": "Needs high nitrogen, pH 5.5-6.5, heavy rainfall (200mm+), grown in Kharif season. MSP for 2026-27: Rs 2,441 per quintal.",
    "maize": "Needs moderate nitrogen, pH 5.5-7.0, moderate rainfall, warm climate. MSP for 2026-27: Rs 2,410 per quintal.",
    "pigeonpeas": "Needs low nitrogen, pH 5.0-7.0, moderate rainfall, warm climate. MSP for 2026-27: Rs 8,450 per quintal.",
    "mungbean": "Needs low nitrogen, pH 6.2-7.2, moderate rainfall, warm season. MSP for 2026-27: Rs 8,780 per quintal.",
    "blackgram": "Needs low nitrogen, pH 6.0-7.5, moderate rainfall, warm climate. MSP for 2026-27: Rs 8,200 per quintal.",
    "cotton": "Needs high potassium, pH 6.0-8.0, warm climate, moderate rainfall. MSP for 2026-27: Rs 8,267/quintal (medium staple), Rs 8,667 (long staple).",
    "coconut": "Needs high potassium, pH 5.5-7.5, coastal humid climate, high rainfall. MSP (as Copra) for 2026-27: Rs 12,500 per quintal.",
    "chickpea": "Needs low nitrogen (fixes its own), pH 6.0-7.5, low rainfall, cool season crop.",
    "kidneybeans": "Needs moderate nitrogen, pH 5.5-6.5, moderate rainfall, cool climate.",
    "mothbeans": "Needs low water, pH 6.0-7.5, drought-tolerant, grown in dry regions.",
    "lentil": "Needs low nitrogen, pH 6.0-7.5, low rainfall, cool season crop.",
    "pomegranate": "Needs low water once established, pH 5.5-7.5, dry to semi-arid climate.",
    "banana": "Needs high potassium, pH 5.5-7.0, high rainfall, warm humid climate.",
    "mango": "Needs moderate nutrients, pH 5.5-7.5, distinct dry and wet seasons.",
    "grapes": "Needs moderate potassium, pH 6.0-7.0, low humidity, warm dry climate.",
    "watermelon": "Needs high potassium, pH 6.0-6.8, warm climate, moderate water.",
    "muskmelon": "Needs moderate nitrogen, pH 6.0-6.8, warm dry climate.",
    "apple": "Needs moderate nutrients, pH 5.5-6.5, cold climate, chilling hours required.",
    "orange": "Needs moderate nitrogen, pH 5.5-7.5, subtropical climate, moderate rainfall.",
    "papaya": "Needs high nitrogen, pH 6.0-6.5, warm climate, well-drained soil.",
    "jute": "Needs high nitrogen, pH 6.0-7.5, high humidity, heavy rainfall.",
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
    fact = crop_facts.get(data.crop_name.lower().strip())

    # purani conversation ko text mein convert karo
    history_text = ""
    for msg in data.history[-5:]:  # sirf last 5 messages yaad rakhega
        history_text += f"Farmer asked: {msg.question}\nYou answered: {msg.answer}\n\n"

    if fact:
        base_instruction = f"Use this verified fact as your main source: {fact}"
    else:
        base_instruction = (
            "We don't have specific verified data for this crop/topic. "
            "Start by saying (in farmer's language) this is general knowledge, not from our verified database."
        )

    prompt = f"""You are a helpful farming assistant for Indian farmers.
{base_instruction}

Previous conversation (for context):
{history_text if history_text else "No previous conversation."}

New question: {data.question}

Answer in simple, easy words (avoid technical jargon). Keep it short.
Reply in the same language the farmer used (Hindi/Hinglish/English).
Use the previous conversation to understand follow-up questions if relevant."""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return {"answer": response.text}
