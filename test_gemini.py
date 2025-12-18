from google.ai.generativelanguage_v1 import GenerativeServiceClient
from google.ai.generativelanguage_v1.types import Content, Part, GenerateContentRequest
from google.api_core.client_options import ClientOptions
import os
from dotenv import load_dotenv

load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

client = GenerativeServiceClient(
    client_options=ClientOptions(
        api_key=api_key,
        api_endpoint="https://generativelanguage.googleapis.com"
    )
)

prompt = Content(parts=[Part(text="What is sustainability in product manufacturing?")])

response = client.generate_content(
    request=GenerateContentRequest(
        model="models/gemini-pro",
        contents=[prompt]
    ),
    timeout=20
)

print(response.candidates[0].content.parts[0].text)
