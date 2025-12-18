import os
import logging
from dotenv import load_dotenv
import google.generativeai as genai

# Setup
load_dotenv()
logging.basicConfig(level=logging.DEBUG)

api_key = os.getenv("GEMINI_API_KEY")
if not api_key:
    raise ValueError("❌ API Key not found in .env!")

genai.configure(api_key=api_key)

# Use the best available model
model = genai.GenerativeModel("gemini-1.5-pro-latest")

# Constructing context prompt from your graph data
user_query = "Is this perfume good for someone with sensitive skin?"
product_data = """
📦 Name: Eco Warrior Perfume for Men
💬 Description: An eco-friendly, long-lasting perfume made from natural ingredients suitable for sensitive skin.
💰 Price: ₹399
⭐ Rating: 4.6 out of 5
📝 Top Reviews:
- Smells amazing and doesn't irritate my skin!
- Love the natural scent — it's subtle but lasts long.
- Good value for an eco product.
"""

prompt = f"User query: {user_query}\n\nRelevant Product Info:\n{product_data}"

try:
    print("⏳ Querying Gemini...")
    response = model.generate_content(prompt)
    print("\n🌟 Gemini's Response:\n", response.text)
except Exception as e:
    logging.exception("❌ Failed to generate response from Gemini.")
