%%writefile main.py
from fastapi import FastAPI
from pydantic import BaseModel
from google import genai

app = FastAPI()
client = genai.Client(api_key="AQ.Ab8RN6IDMZa-Yswenrcgtz2gCsHPRZoQbxGqqsrlbA2-aYcIsg")

crop_facts = {
    "rice": "Needs high nitrogen, pH 5.5-6.5, heavy rainfall (200mm+), grown in Kharif season.",
    "maize": "Needs moderate nitrogen, pH 5.5-7.0, moderate rainfall, warm climate.",
    "chickpea": "Needs low nitrogen (fixes its own), pH 6.0-7.5, low rainfall, cool season crop.",
    "kidneybeans": "Needs moderate nitrogen, pH 5.5-6.5, moderate rainfall, cool climate.",
    "pigeonpeas": "Needs low nitrogen, pH 5.0-7.0, moderate rainfall, warm climate.",
    "mothbeans": "Needs low water, pH 6.0-7.5, drought-tolerant, grown in dry regions.",
    "mungbean": "Needs low nitrogen, pH 6.2-7.2, moderate rainfall, warm season.",
    "blackgram": "Needs low nitrogen, pH 6.0-7.5, moderate rainfall, warm climate.",
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
    "coconut": "Needs high potassium, pH 5.5-7.5, coastal humid climate, high rainfall.",
    "cotton": "Needs high potassium, pH 6.0-8.0, warm climate, moderate rainfall.",
    "jute": "Needs high nitrogen, pH 6.0-7.5, high humidity, heavy rainfall.",
    "coffee": "Needs moderate nitrogen, pH 6.0-6.5, shaded, cool humid climate.",
}

class ChatInput(BaseModel):
    question: str
    crop_name: str = ""

@app.get("/")
def home():
    return {"message": "KrishiMitra Chatbot API is running"}

@app.post("/chatbot-query")
def chatbot_query(data: ChatInput):
    fact = crop_facts.get(data.crop_name.lower().strip())

    if fact:
        prompt = f"""You are a helpful farming assistant for Indian farmers.
Use this verified fact as your main source: {fact}
Question: {data.question}
Answer in simple, easy words (avoid technical jargon). Keep it short.
Reply in the same language the farmer used (Hindi/Hinglish/English)."""
    else:
        prompt = f"""You are a helpful farming assistant for Indian farmers.
We don't have specific verified data for this crop/topic in our system.
Start your answer by saying (in the farmer's language) that this is general knowledge, not from our verified database.
Then answer this question simply and helpfully: {data.question}
Keep it short and in simple, easy words. Reply in the same language the farmer used."""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return {"answer": response.text}
