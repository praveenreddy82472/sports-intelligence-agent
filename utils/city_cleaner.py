import re

def extract_city_from_text(text: str) -> str:
    text = text.lower()

    # Remove filler phrases
    drop_phrases = [
        "tell me about",
        "tell me the",
        "tell me",
        "city of",
        "city in",
        "city",
        "information",
        "info",
        "tourist places in",
        "tourist places",
        "places in",
        "travel plan for",
        "travel plan",
        "about",
        "the",
    ]
    for p in drop_phrases:
        text = text.replace(p, "")

    # Keep only letters and spaces
    text = re.sub(r"[^a-z\s]", "", text).strip()

    if len(text.split()) > 3:
        return ""  # Too long → not a real city

    return text.title()


from openai import AzureOpenAI
from core.config import settings

client = AzureOpenAI(
    api_key=settings.openai_api_key,
    azure_endpoint=settings.azure_openai_endpoint,
    api_version="2024-12-01-preview"
)

def correct_city_spelling(city: str) -> str:
    prompt = f"Correct this to a valid city name: '{city}'. Only return the corrected city name."

    res = client.chat.completions.create(
        model="gpt-4.1-mini",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.0,
        max_tokens=10
    )

    return res.choices[0].message.content.strip()
