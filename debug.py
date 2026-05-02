# debug_groq.py
from groq import Groq
from config import GROQ_API_KEY, GROQ_MODEL

client = Groq(api_key=GROQ_API_KEY)

print("Key:", GROQ_API_KEY[:8] if GROQ_API_KEY else "NONE ← PROBLEM")

try:
    response = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[{"role": "user", "content": "Dis bonjour en une phrase."}],
        max_tokens=50,
    )

    print("✅ Groq works:", response.choices[0].message.content)
    print("\n📊 Token usage for this call:")
    print(f"   Prompt tokens    : {response.usage.prompt_tokens}")
    print(f"   Completion tokens: {response.usage.completion_tokens}")
    print(f"   Total tokens     : {response.usage.total_tokens}")

except Exception as e:
    print("❌ Error:", e)