import google.generativeai as genai
from config import GEMINI_API_KEY

genai.configure(api_key=GEMINI_API_KEY)

for m in genai.list_models():
    print(m.name)  # remove the filter to see ALL models