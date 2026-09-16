from fastapi import FastAPI
from pydantic import BaseModel
from google import genai

app = FastAPI()
client = genai.Client(api_key="AQ.Ab8RN6IDMZa-Yswenrcgtz2gCsHPRZoQbxGqqsrlbA2-aYcIsg")

crop_facts = {
    "rice": "Rice needs high nitrogen, pH 5.5-6.5, and heavy rainfall (200mm+). Best grown in Kharif season.",
    "wheat": "Wheat needs moderate nitrogen, pH 6.0-7.5, and grows well in Rabi season with less rainfall.",
    "cotton": "Cotton needs high potassium, pH 6.0-8.0, and warm climate with moderate rainfall."
}

class ChatInput(BaseModel):
    question: str
    crop_name: str = ""

@app.get("/")
def home():
    return {"message": "KrishiMitra Chatbot API is running"}

@app.post("/chatbot-query")
def chatbot_query(data: ChatInput):
    fact = crop_facts.get(data.crop_name.lower(), "No specific data available.")

    prompt = f"""You are a helpful farming assistant. Answer using ONLY this fact.
Fact: {fact}
Question: {data.question}
Give a short, simple answer in the same language as the question."""

    response = client.models.generate_content(
        model="gemini-3.6-flash",
        contents=prompt
    )
    return {"answer": response.text}
